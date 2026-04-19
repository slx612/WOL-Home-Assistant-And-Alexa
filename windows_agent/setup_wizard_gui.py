"""Windows GUI installer for PC Power Free."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import ipaddress
import json
import locale
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
import uuid
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from network_info import AdapterInfo, detect_primary_adapter, normalize_mac

APP_TITLE = "PC Power Free Setup"
APP_DIR_NAME = "PC Power Free"
DEFAULT_AGENT_PORT = 8777
DEFAULT_TASK_NAME = "PC Power Agent"
DEFAULT_RULE_NAME = "PC Power Agent"
PAIRING_CODE_DIGITS = 6
PAIRING_CODE_TTL_SECONDS = 600
LANGUAGE_NAMES = {"en": "English", "es": "Español"}

TRANSLATIONS = {
    "en": {
        "window_title": "PC Power Free Setup",
        "language": "Language",
        "detected_data": "Detected data",
        "hostname": "Computer",
        "adapter": "Adapter",
        "current_ip": "Current IP",
        "mac": "MAC",
        "discovery_subnet": "Discovery subnet",
        "wol_broadcast": "Wake-on-LAN broadcast",
        "agent_port": "Agent port",
        "internal_token": "Internal token",
        "pairing_code": "Pairing code",
        "home_assistant_ip": "Home Assistant IP",
        "new": "New",
        "pairing_note": "The pairing code is used in Home Assistant and expires 10 minutes after installation.",
        "force_shutdown": "Force applications to close on shutdown",
        "create_firewall": "Create firewall rule",
        "install_startup": "Install at startup",
        "redetect": "Detect again",
        "install": "Install",
        "close": "Close",
        "ready": "Ready",
        "pairing_code_updated": "Pairing code updated",
        "network_detected": "Network detected successfully",
        "network_detection_error": "Unable to detect the active network:\n\n{error}",
        "network_detection_status_error": "Network detection error",
        "validation_failed": "Data validation failed:\n\n{error}",
        "port_range_error": "The port must be between 1 and 65535",
        "token_length_error": "The token must be at least 16 characters long",
        "pairing_length_error": "The pairing code must be 6 digits",
        "admin_required": "To create the firewall rule or install the startup task, you need to run this program as Administrator.",
        "install_failed": "Installation could not be completed:\n\n{error}",
        "install_failed_status": "Installation failed",
        "install_completed_status": "Installation completed",
        "install_completed_message": (
            "Installation completed.\n\n"
            "Pairing code: {pairing_code}\n\n"
            "Home Assistant should discover this PC automatically on the local network.\n"
            "home_assistant_values.txt has been generated and the summary has been copied to the clipboard."
        ),
        "summary_title": "PC Power Free - Home Assistant values",
        "summary_name": "Detected name",
        "summary_host": "Current PC host",
        "summary_mac": "Primary MAC",
        "summary_machine_id": "Machine ID",
        "summary_pairing": "Pairing code",
        "summary_port": "Agent port",
        "summary_broadcast": "Wake-on-LAN broadcast",
        "summary_subnet": "Discovery subnet",
        "summary_flow_title": "Recommended flow:",
        "summary_flow_step_1": "- Install or restart the PC Power Free integration in Home Assistant.",
        "summary_flow_step_2": "- Wait for this PC to appear automatically on the local network.",
        "summary_flow_step_3": "- Click configure and enter the pairing code.",
        "summary_notes_title": "Notes:",
        "summary_notes_1": "- The code expires 10 minutes after you click Install.",
        "summary_notes_2": "- If it expires or you want to link another Home Assistant instance, generate a new one.",
    },
    "es": {
        "window_title": "PC Power Free Setup",
        "language": "Idioma",
        "detected_data": "Datos detectados",
        "hostname": "Equipo",
        "adapter": "Adaptador",
        "current_ip": "IP actual",
        "mac": "MAC",
        "discovery_subnet": "Subred descubrimiento",
        "wol_broadcast": "Broadcast WOL",
        "agent_port": "Puerto agente",
        "internal_token": "Token interno",
        "pairing_code": "Codigo de vinculacion",
        "home_assistant_ip": "IP Home Assistant",
        "new": "Nuevo",
        "pairing_note": "El codigo de vinculacion se usa en Home Assistant y caduca 10 minutos despues de instalar.",
        "force_shutdown": "Forzar cierre de apps al apagar",
        "create_firewall": "Crear regla de firewall",
        "install_startup": "Instalar al arranque",
        "redetect": "Redetectar",
        "install": "Instalar",
        "close": "Cerrar",
        "ready": "Listo",
        "pairing_code_updated": "Codigo de vinculacion actualizado",
        "network_detected": "Red detectada correctamente",
        "network_detection_error": "No se pudo detectar la red activa:\n\n{error}",
        "network_detection_status_error": "Error al detectar la red",
        "validation_failed": "Revision de datos fallida:\n\n{error}",
        "port_range_error": "El puerto debe estar entre 1 y 65535",
        "token_length_error": "El token debe tener al menos 16 caracteres",
        "pairing_length_error": "El codigo de vinculacion debe tener 6 digitos",
        "admin_required": "Para crear la regla de firewall o instalar la tarea al arranque tienes que ejecutar este programa como administrador.",
        "install_failed": "La instalacion no se pudo completar:\n\n{error}",
        "install_failed_status": "Instalacion fallida",
        "install_completed_status": "Instalacion completada",
        "install_completed_message": (
            "Instalacion completada.\n\n"
            "Codigo de vinculacion: {pairing_code}\n\n"
            "Home Assistant deberia descubrir este PC automaticamente en la red local.\n"
            "Se ha generado home_assistant_values.txt y el resumen se ha copiado al portapapeles."
        ),
        "summary_title": "PC Power Free - Datos para Home Assistant",
        "summary_name": "Nombre detectado",
        "summary_host": "Host actual del PC",
        "summary_mac": "MAC principal",
        "summary_machine_id": "Machine ID",
        "summary_pairing": "Codigo de vinculacion",
        "summary_port": "Puerto del agente",
        "summary_broadcast": "Broadcast WOL",
        "summary_subnet": "Subred de descubrimiento",
        "summary_flow_title": "Flujo recomendado:",
        "summary_flow_step_1": "- Instala o reinicia la integracion PC Power Free en Home Assistant.",
        "summary_flow_step_2": "- Espera a que aparezca este PC descubierto en la red local.",
        "summary_flow_step_3": "- Pulsa configurar e introduce el codigo de vinculacion.",
        "summary_notes_title": "Notas:",
        "summary_notes_1": "- El codigo caduca 10 minutos despues de pulsar Instalar.",
        "summary_notes_2": "- Si caduca o quieres vincular otro Home Assistant, genera uno nuevo.",
    },
}


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


def resolve_agent_command(agent_dir: Path) -> tuple[str, str]:
    """Return the executable and arguments used to run the agent."""
    packaged_agent = agent_dir / "PCPowerAgent.exe"
    if packaged_agent.exists():
        return str(packaged_agent), ""

    python_exe = shutil.which("python") or shutil.which("py")
    if not python_exe:
        raise RuntimeError("PCPowerAgent.exe or Python/py.exe was not found on the system")

    script_path = agent_dir / "pc_power_agent.py"
    if not script_path.exists():
        raise RuntimeError("pc_power_agent.py was not found")

    executable_name = Path(python_exe).name.lower()
    if executable_name in {"py", "py.exe"}:
        return python_exe, f'-3 "{script_path}"'
    return python_exe, f'"{script_path}"'


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
    except (OSError, ValueError):
        return {}

    return payload if isinstance(payload, dict) else {}


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
    payload = {
        "host": "0.0.0.0",
        "port": port,
        "token": token,
        "allowed_subnets": allowed_subnets,
        "shutdown_delay_seconds": 0,
        "shutdown_force": force,
        "log_file": "pc_power_agent.log",
        "machine_id": machine_id,
        "pairing_code_hash": pairing_code_hash,
        "pairing_code_expires_at": pairing_code_expires_at,
    }
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def configure_firewall(rule_name: str, *, port: int, remote_addresses: list[str]) -> None:
    """Create the Windows firewall rule for the agent."""
    subprocess.run(
        ["netsh", "advfirewall", "firewall", "delete", "rule", f'name={rule_name}'],
        check=False,
        capture_output=True,
        text=True,
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
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Unable to create the firewall rule")


def install_startup_task(task_name: str, *, command_exe: str, command_prefix: str, config_path: Path) -> None:
    """Install a scheduled task that starts the agent at boot."""
    if command_prefix:
        task_command = f'"{command_exe}" {command_prefix} --config "{config_path}"'
    else:
        task_command = f'"{command_exe}" --config "{config_path}"'

    create_result = subprocess.run(
        [
            "schtasks",
            "/Create",
            "/TN",
            task_name,
            "/SC",
            "ONSTART",
            "/RL",
            "HIGHEST",
            "/RU",
            "SYSTEM",
            "/TR",
            task_command,
            "/F",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if create_result.returncode != 0:
        raise RuntimeError(create_result.stderr.strip() or create_result.stdout.strip() or "Unable to create the scheduled task")

    subprocess.run(
        ["schtasks", "/Run", "/TN", task_name],
        check=False,
        capture_output=True,
        text=True,
    )


def resolve_initial_language(preferred: str | None) -> str:
    """Resolve the initial UI language."""
    if preferred in TRANSLATIONS:
        return preferred

    system_locale = locale.getlocale()[0] or ""
    if system_locale.lower().startswith("es"):
        return "es"
    return "en"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run the PC Power Free setup wizard")
    parser.add_argument("--lang", choices=tuple(TRANSLATIONS), help="UI language")
    return parser.parse_args()


class SetupApplication:
    """Tkinter GUI used to configure the Windows agent."""

    def __init__(self, root: tk.Tk, *, initial_language: str) -> None:
        self.root = root
        self.root.resizable(False, False)

        if getattr(sys, "frozen", False):
            self.agent_dir = Path(sys.executable).resolve().parent
        else:
            self.agent_dir = Path(__file__).resolve().parent
        self.data_dir = resolve_data_dir(self.agent_dir)
        self.config_path = self.data_dir / "config.json"
        self.summary_path = self.data_dir / "home_assistant_values.txt"

        self.existing_config = load_existing_config(self.config_path)
        self.machine_id = str(self.existing_config.get("machine_id") or uuid.uuid4().hex).strip().lower()
        self.language_code = resolve_initial_language(initial_language)
        self._status_key = "ready"

        self.interface_var = tk.StringVar()
        self.hostname_var = tk.StringVar()
        self.ip_var = tk.StringVar()
        self.mac_var = tk.StringVar()
        self.subnet_var = tk.StringVar()
        self.broadcast_var = tk.StringVar()
        self.port_var = tk.StringVar(value=str(self.existing_config.get("port", DEFAULT_AGENT_PORT)))
        self.token_var = tk.StringVar(value=str(self.existing_config.get("token") or generate_token()))
        self.pairing_code_var = tk.StringVar(value=generate_pairing_code())
        self.home_assistant_ip_var = tk.StringVar()
        self.force_shutdown_var = tk.BooleanVar(value=bool(self.existing_config.get("shutdown_force", False)))
        self.install_task_var = tk.BooleanVar(value=True)
        self.firewall_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar()
        self.language_var = tk.StringVar(value=LANGUAGE_NAMES[self.language_code])

        self.field_widgets: dict[str, ttk.Label] = {}
        self.static_spacers: list[ttk.Label] = []

        self._build_ui()
        self._apply_texts()
        self.refresh_network_data()

    def _t(self, key: str, **kwargs: Any) -> str:
        """Translate a UI string."""
        value = TRANSLATIONS[self.language_code][key]
        return value.format(**kwargs)

    def _set_status(self, key: str) -> None:
        """Update the translated status text."""
        self._status_key = key
        self.status_var.set(self._t(key))

    def _build_ui(self) -> None:
        """Create the widgets."""
        self.root.title(self._t("window_title"))
        main = ttk.Frame(self.root, padding=14)
        main.grid(row=0, column=0, sticky="nsew")

        row = 0
        self.language_label = ttk.Label(main)
        self.language_label.grid(row=row, column=0, sticky="w", pady=(0, 6))
        self.language_combo = ttk.Combobox(
            main,
            state="readonly",
            values=[LANGUAGE_NAMES["en"], LANGUAGE_NAMES["es"]],
            textvariable=self.language_var,
            width=18,
        )
        self.language_combo.grid(row=row, column=1, sticky="w", pady=(0, 6))
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_changed)
        row += 1

        self.header_label = ttk.Label(main, font=("Segoe UI", 10, "bold"))
        self.header_label.grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1

        fields = [
            ("hostname", self.hostname_var, True),
            ("adapter", self.interface_var, True),
            ("current_ip", self.ip_var, True),
            ("mac", self.mac_var, True),
            ("discovery_subnet", self.subnet_var, False),
            ("wol_broadcast", self.broadcast_var, False),
            ("agent_port", self.port_var, False),
            ("internal_token", self.token_var, False),
            ("pairing_code", self.pairing_code_var, True),
            ("home_assistant_ip", self.home_assistant_ip_var, False),
        ]

        for key, variable, readonly in fields:
            label = ttk.Label(main)
            label.grid(row=row, column=0, sticky="w", pady=3)
            self.field_widgets[key] = label

            entry = ttk.Entry(main, textvariable=variable, width=42)
            if readonly:
                entry.state(["readonly"])
            entry.grid(row=row, column=1, sticky="ew", pady=3)

            if key == "internal_token":
                self.token_button = ttk.Button(main, command=self.regenerate_token)
                self.token_button.grid(row=row, column=2, sticky="ew", padx=(8, 0))
            elif key == "pairing_code":
                self.pairing_button = ttk.Button(main, command=self.regenerate_pairing_code)
                self.pairing_button.grid(row=row, column=2, sticky="ew", padx=(8, 0))
            else:
                spacer = ttk.Label(main, text="")
                spacer.grid(row=row, column=2)
                self.static_spacers.append(spacer)
            row += 1

        self.note_label = ttk.Label(main, wraplength=460, foreground="#4a4a4a")
        self.note_label.grid(row=row, column=0, columnspan=3, sticky="w", pady=(2, 8))
        row += 1

        self.force_shutdown_check = ttk.Checkbutton(main, variable=self.force_shutdown_var)
        self.force_shutdown_check.grid(row=row, column=0, columnspan=3, sticky="w", pady=(4, 2))
        row += 1
        self.firewall_check = ttk.Checkbutton(main, variable=self.firewall_var)
        self.firewall_check.grid(row=row, column=0, columnspan=3, sticky="w", pady=2)
        row += 1
        self.install_startup_check = ttk.Checkbutton(main, variable=self.install_task_var)
        self.install_startup_check.grid(row=row, column=0, columnspan=3, sticky="w", pady=2)
        row += 1

        button_bar = ttk.Frame(main)
        button_bar.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(12, 6))
        self.redetect_button = ttk.Button(button_bar, command=self.refresh_network_data)
        self.redetect_button.grid(row=0, column=0, padx=(0, 8))
        self.install_button = ttk.Button(button_bar, command=self.install)
        self.install_button.grid(row=0, column=1, padx=(0, 8))
        self.close_button = ttk.Button(button_bar, command=self.root.destroy)
        self.close_button.grid(row=0, column=2)
        row += 1

        self.status_label = ttk.Label(main, textvariable=self.status_var, foreground="#1f4d2c")
        self.status_label.grid(row=row, column=0, columnspan=3, sticky="w")

        for column in range(3):
            main.columnconfigure(column, weight=1 if column == 1 else 0)

    def _apply_texts(self) -> None:
        """Apply translated text to the UI."""
        self.root.title(self._t("window_title"))
        self.language_label.config(text=self._t("language"))
        self.header_label.config(text=self._t("detected_data"))

        for key, label in self.field_widgets.items():
            label.config(text=self._t(key))

        self.token_button.config(text=self._t("new"))
        self.pairing_button.config(text=self._t("new"))
        self.note_label.config(text=self._t("pairing_note"))
        self.force_shutdown_check.config(text=self._t("force_shutdown"))
        self.firewall_check.config(text=self._t("create_firewall"))
        self.install_startup_check.config(text=self._t("install_startup"))
        self.redetect_button.config(text=self._t("redetect"))
        self.install_button.config(text=self._t("install"))
        self.close_button.config(text=self._t("close"))
        self.status_var.set(self._t(self._status_key))

    def _on_language_changed(self, _event: tk.Event | None = None) -> None:
        """Handle language changes from the combo box."""
        display_value = self.language_var.get()
        for code, label in LANGUAGE_NAMES.items():
            if display_value == label:
                self.language_code = code
                break
        self._apply_texts()

    def regenerate_token(self) -> None:
        """Generate a fresh token."""
        self.token_var.set(generate_token())

    def regenerate_pairing_code(self) -> None:
        """Generate a fresh visible pairing code."""
        self.pairing_code_var.set(generate_pairing_code())
        self._set_status("pairing_code_updated")

    def refresh_network_data(self) -> None:
        """Refresh the adapter information shown in the UI."""
        try:
            adapter = detect_primary_adapter()
        except Exception as err:
            messagebox.showerror(APP_TITLE, self._t("network_detection_error", error=err))
            self._set_status("network_detection_status_error")
            return

        self.hostname_var.set(adapter.hostname)
        self.interface_var.set(adapter.interface_alias)
        self.ip_var.set(adapter.ipv4_address)
        self.mac_var.set(adapter.mac_address)
        self.subnet_var.set(adapter.subnet_cidr)
        self.broadcast_var.set(adapter.broadcast_address)
        self._set_status("network_detected")

    def install(self) -> None:
        """Write config, optionally configure firewall and install the task."""
        try:
            adapter = AdapterInfo(
                hostname=self.hostname_var.get().strip(),
                interface_alias=self.interface_var.get().strip(),
                ipv4_address=self.ip_var.get().strip(),
                prefix_length=int(self.subnet_var.get().split("/", 1)[1]),
                mac_address=normalize_mac(self.mac_var.get().strip()),
                subnet_cidr=self.subnet_var.get().strip(),
                broadcast_address=str(ipaddress.ip_address(self.broadcast_var.get().strip())),
            )
            port = int(self.port_var.get().strip())
            if not 1 <= port <= 65535:
                raise ValueError(self._t("port_range_error"))
            token = self.token_var.get().strip()
            if len(token) < 16:
                raise ValueError(self._t("token_length_error"))
            pairing_code = self.pairing_code_var.get().strip()
            if len(pairing_code) != PAIRING_CODE_DIGITS or not pairing_code.isdigit():
                raise ValueError(self._t("pairing_length_error"))
            home_assistant_ip = self.home_assistant_ip_var.get().strip()
            if home_assistant_ip:
                ipaddress.ip_address(home_assistant_ip)
            ipaddress.ip_network(adapter.subnet_cidr, strict=False)
        except Exception as err:
            messagebox.showerror(APP_TITLE, self._t("validation_failed", error=err))
            return

        privileged_action = self.firewall_var.get() or self.install_task_var.get()
        if privileged_action and not is_admin():
            messagebox.showerror(APP_TITLE, self._t("admin_required"))
            return

        allowed_subnets, firewall_addresses = build_allowed_subnets(home_assistant_ip, adapter.subnet_cidr)

        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            write_config(
                self.config_path,
                port=port,
                token=token,
                allowed_subnets=allowed_subnets,
                force=self.force_shutdown_var.get(),
                machine_id=self.machine_id,
                pairing_code_hash=hash_pairing_code(pairing_code),
                pairing_code_expires_at=time.time() + PAIRING_CODE_TTL_SECONDS,
            )

            command_exe, command_prefix = resolve_agent_command(self.agent_dir)

            if self.firewall_var.get():
                configure_firewall(DEFAULT_RULE_NAME, port=port, remote_addresses=firewall_addresses)

            if self.install_task_var.get():
                install_startup_task(
                    DEFAULT_TASK_NAME,
                    command_exe=command_exe,
                    command_prefix=command_prefix,
                    config_path=self.config_path,
                )

            summary = self._build_summary(adapter, pairing_code, port)
            self.summary_path.write_text(summary, encoding="utf-8")
            self.root.clipboard_clear()
            self.root.clipboard_append(summary)
        except Exception as err:
            messagebox.showerror(APP_TITLE, self._t("install_failed", error=err))
            self._set_status("install_failed_status")
            return

        self._set_status("install_completed_status")
        messagebox.showinfo(
            APP_TITLE,
            self._t("install_completed_message", pairing_code=pairing_code),
        )

    def _build_summary(self, adapter: AdapterInfo, pairing_code: str, port: int) -> str:
        """Create the Home Assistant summary text."""
        return (
            f"{self._t('summary_title')}\n\n"
            f"{self._t('summary_name')}: {adapter.hostname}\n"
            f"{self._t('summary_host')}: {adapter.ipv4_address}\n"
            f"{self._t('summary_mac')}: {adapter.mac_address}\n"
            f"{self._t('summary_machine_id')}: {self.machine_id}\n"
            f"{self._t('summary_pairing')}: {pairing_code}\n"
            f"{self._t('summary_port')}: {port}\n"
            f"{self._t('summary_broadcast')}: {adapter.broadcast_address}\n"
            f"{self._t('summary_subnet')}: {adapter.subnet_cidr}\n\n"
            f"{self._t('summary_flow_title')}\n"
            f"{self._t('summary_flow_step_1')}\n"
            f"{self._t('summary_flow_step_2')}\n"
            f"{self._t('summary_flow_step_3')}\n\n"
            f"{self._t('summary_notes_title')}\n"
            f"{self._t('summary_notes_1')}\n"
            f"{self._t('summary_notes_2')}\n"
        )


def main() -> int:
    """Run the Tkinter application."""
    args = parse_args()
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    SetupApplication(root, initial_language=args.lang or "")
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
