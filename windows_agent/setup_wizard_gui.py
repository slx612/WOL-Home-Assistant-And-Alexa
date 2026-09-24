"""Windows GUI installer for PC Power Free."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import ipaddress
import json
import logging
import os
from pathlib import Path
import secrets
import shutil
import ssl
import subprocess
import sys
import time
from urllib import request as urllib_request
import uuid
import winreg
import tkinter as tk
from tkinter import messagebox
from typing import Any

from network_info import AdapterInfo, detect_primary_adapter, normalize_mac
from update_check import fetch_latest_github_release, format_update_error, is_newer_version

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from agent_core.common import atomic_write_json, load_config
from agent_core.tls import create_server_context

APP_TITLE = "WakeLink"
APP_DIR_NAME = "PC Power Free"
APP_VERSION = "0.2.0-beta.12"
DEFAULT_AGENT_PORT = 58477
DEFAULT_TASK_NAME = "PC Power Agent"
DEFAULT_RULE_NAME = "PC Power Agent"
TRAY_RUN_VALUE_NAME = "PC Power Free Tray"
PAIRING_CODE_DIGITS = 6
PAIRING_CODE_TTL_SECONDS = 600

def is_admin() -> bool:
    """Return whether the current process is elevated."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def generate_token() -> str:
    """Return a URL-safe random token."""
    return secrets.token_urlsafe(32)


def generate_pairing_code() -> str:
    """Return a short numeric pairing code."""
    return "".join(secrets.choice("0123456789") for _ in range(PAIRING_CODE_DIGITS))


def hash_pairing_code(pairing_code: str) -> str:
    """Hash the pairing code before storing it."""
    return hashlib.sha256(pairing_code.strip().encode("utf-8")).hexdigest()


def resolve_python_or_executable_command(
    agent_dir: Path,
    *,
    executable_name: str,
    script_name: str,
) -> tuple[str, str]:
    """Return either the packaged executable or the Python command line."""
    packaged_executable = agent_dir / executable_name
    if packaged_executable.exists():
        return str(packaged_executable), ""

    python_exe = shutil.which("python") or shutil.which("py")
    if not python_exe:
        raise RuntimeError(f"{executable_name} or Python/py.exe was not found on the system")

    script_path = agent_dir / script_name
    if not script_path.exists():
        raise RuntimeError(f"{script_name} was not found")

    executable_name = Path(python_exe).name.lower()
    if executable_name in {"py", "py.exe"}:
        return python_exe, f'-3 "{script_path}"'
    return python_exe, f'"{script_path}"'


def resolve_agent_command(agent_dir: Path) -> tuple[str, str]:
    """Return the executable and arguments used to run the agent."""
    return resolve_python_or_executable_command(
        agent_dir,
        executable_name="PCPowerAgent.exe",
        script_name="pc_power_agent.py",
    )


def resolve_tray_command(agent_dir: Path) -> tuple[str, str]:
    """Return the executable and arguments used to run the tray app."""
    return resolve_python_or_executable_command(
        agent_dir,
        executable_name="PCPowerTray.exe",
        script_name="pc_power_tray.py",
    )


def build_command_line(command_exe: str, command_prefix: str, config_path: Path) -> str:
    """Build a quoted command line used for startup registration."""
    if command_prefix:
        return f'"{command_exe}" {command_prefix} --config "{config_path}"'
    return f'"{command_exe}" --config "{config_path}"'


def build_allowed_subnets(home_assistant_ip: str, subnet_cidr: str) -> tuple[list[str], list[str]]:
    """Return API and firewall restrictions."""
    if home_assistant_ip:
        return [f"{home_assistant_ip}/32", "127.0.0.1/32"], [home_assistant_ip]
    return [subnet_cidr, "127.0.0.1/32"], [subnet_cidr]


def resolve_data_dir(app_dir: Path) -> Path:
    """Return the directory used for config, logs and generated files."""
    override = os.environ.get("PC_POWER_FREE_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()

    app_dir_str = str(app_dir).lower()
    if "\\program files" in app_dir_str:
        return Path(os.environ.get("ProgramData", r"C:\ProgramData")) / APP_DIR_NAME

    return app_dir


def load_existing_config(config_path: Path) -> dict[str, Any]:
    """Load the existing config if present."""
    if not config_path.exists():
        return {}

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        raise ValueError("Cannot read existing config.json. Restore a backup; do not uninstall.") from err
    if not isinstance(payload, dict):
        raise ValueError("config.json must contain an object")
    return payload


def activate_pairing_code(config_path: Path) -> str:
    """The agent reloads this file; existing tokens and TLS identity stay unchanged."""
    config = load_existing_config(config_path)
    if not config.get("token") or not config.get("machine_id"):
        raise ValueError("Complete setup before generating a pairing code")
    code = generate_pairing_code()
    config.update(pairing_code_hash=hash_pairing_code(code),
                  pairing_code_expires_at=time.time() + PAIRING_CODE_TTL_SECONDS,
                  pairing_code_failed_attempts=0)
    atomic_write_json(config_path, config)
    return code


def write_config(
    config_path: Path,
    *,
    port: int,
    token: str,
    allowed_subnets: list[str],
    force: bool,
    machine_id: str,
    pairing_code_hash: str,
    pairing_code_expires_at: float,
) -> None:
    """Write the agent JSON config."""
    payload = load_existing_config(config_path)
    payload.setdefault("host", "0.0.0.0")
    payload.setdefault("shutdown_delay_seconds", 0)
    payload.setdefault("log_file", "pc_power_agent.log")
    payload.update({
        "port": port,
        "token": token,
        "allowed_subnets": allowed_subnets,
        "shutdown_force": force,
        "machine_id": machine_id,
        "pairing_code_hash": pairing_code_hash,
        "pairing_code_expires_at": pairing_code_expires_at,
        "pairing_code_failed_attempts": 0,
    })
    atomic_write_json(config_path, payload)


def configure_firewall(rule_name: str, *, port: int, remote_addresses: list[str]) -> None:
    """Create the Windows firewall rule for the agent."""
    subprocess.run(
        ["netsh", "advfirewall", "firewall", "delete", "rule", f'name={rule_name}'],
        check=False,
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    remote_ip_value = ",".join(remote_addresses)
    result = subprocess.run(
        [
            "netsh",
            "advfirewall",
            "firewall",
            "add",
            "rule",
            f'name={rule_name}',
            "dir=in",
            "action=allow",
            "enable=yes",
            "protocol=TCP",
            f"localport={port}",
            f"remoteip={remote_ip_value}",
        ],
        check=False,
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Unable to create the firewall rule")


def install_startup_task(task_name: str, *, command_exe: str, command_prefix: str, config_path: Path) -> None:
    """Install a scheduled task that starts the agent at boot."""
    arguments = ["-ExecutablePath", command_exe, "-ConfigPath", str(config_path)]
    if command_prefix:
        arguments.extend(["-CommandPrefix", command_prefix])
    run_task_script(task_name, "Install", *arguments)


def run_task_script(task_name: str, mode: str, *arguments: str) -> bool:
    """Keep GUI and manual installs on the same Task Scheduler settings."""
    app_dir = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    result = subprocess.run([
        "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-File", str(app_dir / "install-task.ps1"), "-TaskName", task_name,
        "-Mode", mode, *arguments,
    ], capture_output=True, text=True, timeout=45, creationflags=subprocess.CREATE_NO_WINDOW)
    if mode == "Upgrade" and result.returncode == 3:
        return False  # Keep disabled or absent automatic startup disabled.
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Task configuration failed")
    return True


def upgrade_existing_installation(agent_dir: Path, config_path: Path) -> None:
    """Reuse published settings verbatim; never replace credentials during an update."""
    _, changed = load_config(config_path)
    if changed:
        raise ValueError("Existing machine identity is missing. Restore the configuration backup.")
    create_server_context(config_path.parent)
    command_exe, command_prefix = resolve_agent_command(agent_dir)
    arguments = ["-ExecutablePath", command_exe, "-ConfigPath", str(config_path)]
    if command_prefix:
        arguments.extend(["-CommandPrefix", command_prefix])
    if run_task_script(DEFAULT_TASK_NAME, "Upgrade", *arguments):
        wait_for_agent(config_path)


def wait_for_agent(config_path: Path) -> None:
    """Report success only after the configured TLS endpoint actually responds."""
    config = load_existing_config(config_path)
    context = ssl.create_default_context(cafile=str(config_path.parent / "agent-cert.pem"))
    request = urllib_request.Request(f"https://127.0.0.1:{config['port']}/v1/status",
        headers={"Authorization": f"Bearer {config['token']}"})
    deadline = time.monotonic() + 15
    while True:
        try:
            with urllib_request.urlopen(request, context=context, timeout=2) as response:
                status = json.load(response)
                if status.get("machine_id") == config["machine_id"]:
                    return
        except (OSError, ValueError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError("The agent did not start on the configured port. Check pc_power_agent.log.")
        time.sleep(.5)


def certificate_fingerprint(data_dir: Path) -> str:
    certificate = (data_dir / "agent-cert.pem").read_text(encoding="ascii")
    return hashlib.sha256(ssl.PEM_cert_to_DER_cert(certificate)).hexdigest()


def configure_tray_startup(
    *,
    enabled: bool,
    command_exe: str,
    command_prefix: str,
    config_path: Path,
) -> None:
    """Register or remove the tray app from the current user's startup apps."""
    run_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    command_line = build_command_line(command_exe, command_prefix, config_path)

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, run_key_path) as run_key:
        if enabled:
            winreg.SetValueEx(run_key, TRAY_RUN_VALUE_NAME, 0, winreg.REG_SZ, command_line)
            return

        try:
            winreg.DeleteValue(run_key, TRAY_RUN_VALUE_NAME)
        except FileNotFoundError:
            pass


def start_tray_application(command_exe: str, command_prefix: str, config_path: Path) -> None:
    """Launch the tray app immediately after install."""
    if command_prefix:
        subprocess.Popen(
            build_command_line(command_exe, command_prefix, config_path),
            shell=True,
        )
        return

    subprocess.Popen(
        [command_exe, "--config", str(config_path)],
        shell=False,
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run the PC Power Free setup wizard")
    parser.add_argument("--lang", choices=("en", "es"), help="UI language")
    parser.add_argument("--page", choices=("home", "setup", "pairing", "settings", "updates"))
    parser.add_argument("--upgrade-existing", action="store_true",
                        help="Update existing settings without running the pairing wizard")
    parser.add_argument("--config", type=Path, help="Override the configuration path for --upgrade-existing")
    return parser.parse_args()


def main() -> int:
    """Run the Tkinter application."""
    args = parse_args()
    if args.upgrade_existing:
        agent_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
        config_path = args.config or resolve_data_dir(agent_dir) / "config.json"
        if not config_path.exists():
            return 3  # First install: let the installer offer the normal configurator.
        try:
            upgrade_existing_installation(agent_dir, config_path)
        except Exception as err:
            try:
                logging.basicConfig(filename=config_path.with_name("upgrade.log"), level=logging.ERROR)
                logging.error("Existing installation upgrade failed: %s", err)
            except OSError:
                pass
            return 1
        return 0
    from desktop_ui import WakeLinkApplication
    root = tk.Tk()
    try:
        WakeLinkApplication(root, initial_language=args.lang or "", initial_page=args.page)
    except Exception as err:
        messagebox.showerror(APP_TITLE, str(err), parent=root)
        root.destroy()
        return 1
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
