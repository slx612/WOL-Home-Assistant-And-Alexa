"""Windows GUI installer for PC Power Free."""

from __future__ import annotations

import ctypes
import hashlib
import ipaddress
import json
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
        raise RuntimeError("No se ha encontrado PCPowerAgent.exe ni Python/py.exe en el sistema")

    script_path = agent_dir / "pc_power_agent.py"
    if not script_path.exists():
        raise RuntimeError("No se ha encontrado pc_power_agent.py")

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
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "No se pudo crear la regla de firewall")


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
        raise RuntimeError(create_result.stderr.strip() or create_result.stdout.strip() or "No se pudo crear la tarea programada")

    subprocess.run(
        ["schtasks", "/Run", "/TN", task_name],
        check=False,
        capture_output=True,
        text=True,
    )


class SetupApplication:
    """Tkinter GUI used to configure the Windows agent."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
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
        self.status_var = tk.StringVar(value="Listo")

        self._build_ui()
        self.refresh_network_data()

    def _build_ui(self) -> None:
        """Create the widgets."""
        main = ttk.Frame(self.root, padding=14)
        main.grid(row=0, column=0, sticky="nsew")

        row = 0
        ttk.Label(main, text="Datos detectados", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1

        fields = [
            ("Equipo", self.hostname_var, True),
            ("Adaptador", self.interface_var, True),
            ("IP actual", self.ip_var, True),
            ("MAC", self.mac_var, True),
            ("Subred descubrimiento", self.subnet_var, False),
            ("Broadcast WOL", self.broadcast_var, False),
            ("Puerto agente", self.port_var, False),
            ("Token interno", self.token_var, False),
            ("Codigo de vinculacion", self.pairing_code_var, True),
            ("IP Home Assistant", self.home_assistant_ip_var, False),
        ]

        for label_text, variable, readonly in fields:
            ttk.Label(main, text=label_text).grid(row=row, column=0, sticky="w", pady=3)
            entry = ttk.Entry(main, textvariable=variable, width=42)
            if readonly:
                entry.state(["readonly"])
            entry.grid(row=row, column=1, sticky="ew", pady=3)

            if variable is self.token_var:
                ttk.Button(main, text="Nuevo", command=self.regenerate_token).grid(row=row, column=2, sticky="ew", padx=(8, 0))
            elif variable is self.pairing_code_var:
                ttk.Button(main, text="Nuevo", command=self.regenerate_pairing_code).grid(row=row, column=2, sticky="ew", padx=(8, 0))
            else:
                ttk.Label(main, text="").grid(row=row, column=2)
            row += 1

        ttk.Label(
            main,
            text="El codigo de vinculacion se usa en Home Assistant y caduca 10 minutos despues de instalar.",
            wraplength=460,
            foreground="#4a4a4a",
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(2, 8))
        row += 1

        ttk.Checkbutton(main, text="Forzar cierre de apps al apagar", variable=self.force_shutdown_var).grid(row=row, column=0, columnspan=3, sticky="w", pady=(4, 2))
        row += 1
        ttk.Checkbutton(main, text="Crear regla de firewall", variable=self.firewall_var).grid(row=row, column=0, columnspan=3, sticky="w", pady=2)
        row += 1
        ttk.Checkbutton(main, text="Instalar al arranque", variable=self.install_task_var).grid(row=row, column=0, columnspan=3, sticky="w", pady=2)
        row += 1

        button_bar = ttk.Frame(main)
        button_bar.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(12, 6))
        ttk.Button(button_bar, text="Redetectar", command=self.refresh_network_data).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(button_bar, text="Instalar", command=self.install).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(button_bar, text="Cerrar", command=self.root.destroy).grid(row=0, column=2)
        row += 1

        ttk.Label(main, textvariable=self.status_var, foreground="#1f4d2c").grid(row=row, column=0, columnspan=3, sticky="w")

        for column in range(3):
            main.columnconfigure(column, weight=1 if column == 1 else 0)

    def regenerate_token(self) -> None:
        """Generate a fresh token."""
        self.token_var.set(generate_token())

    def regenerate_pairing_code(self) -> None:
        """Generate a fresh visible pairing code."""
        self.pairing_code_var.set(generate_pairing_code())
        self.status_var.set("Codigo de vinculacion actualizado")

    def refresh_network_data(self) -> None:
        """Refresh the adapter information shown in the UI."""
        try:
            adapter = detect_primary_adapter()
        except Exception as err:
            messagebox.showerror(APP_TITLE, f"No se pudo detectar la red activa:\n\n{err}")
            self.status_var.set("Error al detectar la red")
            return

        self.hostname_var.set(adapter.hostname)
        self.interface_var.set(adapter.interface_alias)
        self.ip_var.set(adapter.ipv4_address)
        self.mac_var.set(adapter.mac_address)
        self.subnet_var.set(adapter.subnet_cidr)
        self.broadcast_var.set(adapter.broadcast_address)
        self.status_var.set("Red detectada correctamente")

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
                raise ValueError("El puerto debe estar entre 1 y 65535")
            token = self.token_var.get().strip()
            if len(token) < 16:
                raise ValueError("El token debe tener al menos 16 caracteres")
            pairing_code = self.pairing_code_var.get().strip()
            if len(pairing_code) != PAIRING_CODE_DIGITS or not pairing_code.isdigit():
                raise ValueError("El codigo de vinculacion debe tener 6 digitos")
            home_assistant_ip = self.home_assistant_ip_var.get().strip()
            if home_assistant_ip:
                ipaddress.ip_address(home_assistant_ip)
            ipaddress.ip_network(adapter.subnet_cidr, strict=False)
        except Exception as err:
            messagebox.showerror(APP_TITLE, f"Revision de datos fallida:\n\n{err}")
            return

        privileged_action = self.firewall_var.get() or self.install_task_var.get()
        if privileged_action and not is_admin():
            messagebox.showerror(
                APP_TITLE,
                "Para crear la regla de firewall o instalar la tarea al arranque tienes que ejecutar este programa como administrador.",
            )
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
            messagebox.showerror(APP_TITLE, f"La instalacion no se pudo completar:\n\n{err}")
            self.status_var.set("Instalacion fallida")
            return

        self.status_var.set("Instalacion completada")
        messagebox.showinfo(
            APP_TITLE,
            "Instalacion completada.\n\n"
            f"Codigo de vinculacion: {pairing_code}\n\n"
            "Home Assistant deberia descubrir este PC automaticamente en la red local.\n"
            "Se ha generado home_assistant_values.txt y el resumen se ha copiado al portapapeles.",
        )

    def _build_summary(self, adapter: AdapterInfo, pairing_code: str, port: int) -> str:
        """Create the Home Assistant summary text."""
        return (
            "PC Power Free - Datos para Home Assistant\n\n"
            f"Nombre detectado: {adapter.hostname}\n"
            f"Host actual del PC: {adapter.ipv4_address}\n"
            f"MAC principal: {adapter.mac_address}\n"
            f"Machine ID: {self.machine_id}\n"
            f"Codigo de vinculacion: {pairing_code}\n"
            f"Puerto del agente: {port}\n"
            f"Broadcast WOL: {adapter.broadcast_address}\n"
            f"Subred de descubrimiento: {adapter.subnet_cidr}\n\n"
            "Flujo recomendado:\n"
            "- Instala o reinicia la integracion PC Power Free en Home Assistant.\n"
            "- Espera a que aparezca este PC descubierto en la red local.\n"
            "- Pulsa configurar e introduce el codigo de vinculacion.\n\n"
            "Notas:\n"
            "- El codigo caduca 10 minutos despues de pulsar Instalar.\n"
            "- Si caduca o quieres vincular otro Home Assistant, genera uno nuevo.\n"
        )


def main() -> int:
    """Run the Tkinter application."""
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    SetupApplication(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
