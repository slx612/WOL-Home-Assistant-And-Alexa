"""System tray companion app for PC Power Free."""

from __future__ import annotations

import argparse
import ctypes
import json
import locale
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from PIL import Image, ImageDraw
import pystray

APP_NAME = "PC Power Free"
APP_TITLE = "PC Power Free Tray"
APP_DIR_NAME = "PC Power Free"
APP_VERSION = "0.2.0-beta.4"
DEFAULT_AGENT_PORT = 8777
CONFIG_FILENAME = "config.json"
COMMAND_GUARD_ALLOW = "allow"
COMMAND_GUARD_IGNORE_MANUAL = "ignore_manual"
COMMAND_GUARD_IGNORE_UNTIL = "ignore_until"
LOCAL_GUARD_ENDPOINT = "/v1/local/guard"
MUTEX_NAME = "Local\\PCPowerFreeTraySingleton"

TRANSLATIONS = {
    "en": {
        "status_not_configured": "PC Power Free is not configured yet",
        "status_error": "Tray status: {error}",
        "status_waiting": "Tray status: waiting for the local agent",
        "status_allow": "Protection is off. Home Assistant requests are allowed.",
        "status_manual": "Protection is on until you allow requests again.",
        "status_until": "Protection is on until {time_text}.",
        "status_generic": "Protection is on.",
        "menu_allow": "Allow Home Assistant requests",
        "menu_ignore_15": "Ignore for 15 minutes",
        "menu_ignore_60": "Ignore for 1 hour",
        "menu_ignore_manual": "Ignore until I re-enable it",
        "menu_refresh": "Refresh status",
        "menu_open_setup": "Open configurator",
        "menu_exit": "Exit tray icon",
        "notify_refresh_failed": "Could not refresh status: {error}",
        "notify_change_failed": "Could not change protection: {error}",
        "notify_allow": "Home Assistant requests are allowed again.",
        "notify_ignore_15": "Home Assistant requests will be ignored for 15 minutes.",
        "notify_ignore_60": "Home Assistant requests will be ignored for 1 hour.",
        "notify_ignore_manual": "Home Assistant requests will be ignored until you re-enable them.",
        "notify_open_setup_failed": "Could not open the configurator: {error}",
    },
    "es": {
        "status_not_configured": "PC Power Free todavia no esta configurado",
        "status_error": "Estado de la bandeja: {error}",
        "status_waiting": "Estado de la bandeja: esperando al agente local",
        "status_allow": "La proteccion esta desactivada. Home Assistant puede enviar ordenes.",
        "status_manual": "La proteccion esta activada hasta que vuelvas a permitir las ordenes.",
        "status_until": "La proteccion esta activada hasta las {time_text}.",
        "status_generic": "La proteccion esta activada.",
        "menu_allow": "Permitir ordenes de Home Assistant",
        "menu_ignore_15": "Ignorar durante 15 minutos",
        "menu_ignore_60": "Ignorar durante 1 hora",
        "menu_ignore_manual": "Ignorar hasta que yo lo reactive",
        "menu_refresh": "Actualizar estado",
        "menu_open_setup": "Abrir configurador",
        "menu_exit": "Salir del icono de bandeja",
        "notify_refresh_failed": "No se pudo actualizar el estado: {error}",
        "notify_change_failed": "No se pudo cambiar la proteccion: {error}",
        "notify_allow": "Las ordenes de Home Assistant vuelven a estar permitidas.",
        "notify_ignore_15": "Las ordenes de Home Assistant se ignoraran durante 15 minutos.",
        "notify_ignore_60": "Las ordenes de Home Assistant se ignoraran durante 1 hora.",
        "notify_ignore_manual": "Las ordenes de Home Assistant se ignoraran hasta que lo reactives.",
        "notify_open_setup_failed": "No se pudo abrir el configurador: {error}",
    },
}


def resolve_data_dir(app_dir: Path) -> Path:
    """Return the directory used for config, logs and generated files."""
    override = os.environ.get("PC_POWER_FREE_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()

    app_dir_str = str(app_dir).lower()
    if "\\program files" in app_dir_str:
        return Path(os.environ.get("ProgramData", r"C:\ProgramData")) / APP_DIR_NAME

    return app_dir


def resolve_default_config_path() -> Path:
    """Return the default config path for the tray app."""
    if getattr(sys, "frozen", False):
        app_dir = Path(sys.executable).resolve().parent
    else:
        app_dir = Path(__file__).resolve().parent
    return resolve_data_dir(app_dir) / CONFIG_FILENAME


def resolve_language() -> str:
    """Return the preferred UI language for the tray app."""
    system_locale = locale.getlocale()[0] or ""
    if system_locale.lower().startswith("es"):
        return "es"
    return "en"


def load_runtime_config(config_path: Path) -> dict[str, Any]:
    """Load the agent config that contains token and port."""
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError("config.json does not contain a JSON object")
    return raw


def build_local_api_request(
    *,
    config: dict[str, Any],
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 5,
) -> dict[str, Any]:
    """Call a localhost-only agent endpoint using the configured token."""
    agent_port = int(config.get("port", DEFAULT_AGENT_PORT))
    token = str(config.get("token", "")).strip()
    body: bytes | None = None
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": f"PCPowerFreeTray/{APP_VERSION}",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib_request.Request(
        f"http://127.0.0.1:{agent_port}{path}",
        data=body,
        method=method,
        headers=headers,
    )
    with urllib_request.urlopen(request, timeout=timeout) as response:
        raw = json.loads(response.read().decode("utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError("The agent returned an invalid JSON payload")
    return raw


def build_tray_image(*, mode: str | None, available: bool) -> Image.Image:
    """Return the tray icon image for the current protection state."""
    background = "#3b82f6" if available else "#6b7280"
    accent = "#f59e0b" if mode and mode != COMMAND_GUARD_ALLOW else "#34d399"

    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((6, 6, 58, 58), radius=16, fill=background)
    draw.rounded_rectangle((16, 14, 48, 38), radius=6, outline="white", width=3)
    draw.rectangle((24, 42, 40, 47), fill="white")
    draw.ellipse((41, 39, 56, 54), fill=accent)
    draw.line((48, 43, 48, 49), fill="white", width=2)
    draw.arc((44, 39, 52, 47), start=200, end=340, fill="white", width=2)
    return image


def acquire_single_instance_mutex() -> int | None:
    """Prevent duplicate tray instances in the same session."""
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not mutex:
        return None
    if kernel32.GetLastError() == 183:
        kernel32.CloseHandle(mutex)
        return None
    return mutex


class TrayApp:
    """Tray controller for temporary protection against HA power commands."""

    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path
        self._language_code = resolve_language()
        self._cached_state: dict[str, Any] | None = None
        self._last_error: str | None = None
        self._icon = pystray.Icon(APP_NAME)
        self._icon.icon = build_tray_image(mode=None, available=False)
        self._icon.title = APP_TITLE
        self._icon.menu = pystray.Menu(
            pystray.MenuItem(lambda item: self._status_text(), self._noop, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: self._t("menu_allow"), self._allow_requests),
            pystray.MenuItem(lambda item: self._t("menu_ignore_15"), self._ignore_for_15_minutes),
            pystray.MenuItem(lambda item: self._t("menu_ignore_60"), self._ignore_for_1_hour),
            pystray.MenuItem(lambda item: self._t("menu_ignore_manual"), self._ignore_manually),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: self._t("menu_refresh"), self._refresh_from_menu),
            pystray.MenuItem(lambda item: self._t("menu_open_setup"), self._open_setup),
            pystray.MenuItem(lambda item: self._t("menu_exit"), self._quit),
        )

    def _t(self, key: str, **kwargs: Any) -> str:
        """Translate a tray string."""
        return TRANSLATIONS[self._language_code][key].format(**kwargs)

    def run(self) -> None:
        """Run the tray application."""
        self._refresh_state(notify=False)
        self._icon.run()

    def _noop(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Do nothing for disabled status rows."""

    def _status_text(self) -> str:
        """Return the current menu status line."""
        if not self._config_path.exists():
            return self._t("status_not_configured")
        if self._last_error:
            return self._t("status_error", error=self._last_error)
        if not self._cached_state:
            return self._t("status_waiting")

        mode = str(self._cached_state.get("mode") or COMMAND_GUARD_ALLOW)
        if not self._cached_state.get("active"):
            return self._t("status_allow")
        if mode == COMMAND_GUARD_IGNORE_MANUAL:
            return self._t("status_manual")
        if mode == COMMAND_GUARD_IGNORE_UNTIL:
            until_ts = self._cached_state.get("until_ts")
            if until_ts:
                until_text = time.strftime("%H:%M", time.localtime(float(until_ts)))
                return self._t("status_until", time_text=until_text)
        return self._t("status_generic")

    def _refresh_state(self, *, notify: bool) -> None:
        """Reload the command guard state from the local agent."""
        try:
            config = load_runtime_config(self._config_path)
            state = build_local_api_request(
                config=config,
                method="GET",
                path=LOCAL_GUARD_ENDPOINT,
            )
        except FileNotFoundError:
            self._cached_state = None
            self._last_error = "config.json not found"
            self._icon.icon = build_tray_image(mode=None, available=False)
        except Exception as err:  # pragma: no cover - depends on local Windows runtime
            self._cached_state = None
            self._last_error = str(err)
            self._icon.icon = build_tray_image(mode=None, available=False)
            if notify:
                self._notify(self._t("notify_refresh_failed", error=self._last_error))
        else:
            self._cached_state = state
            self._last_error = None
            self._icon.icon = build_tray_image(
                mode=str(state.get("mode") or COMMAND_GUARD_ALLOW),
                available=True,
            )
            if notify:
                self._notify(self._status_text())

        self._icon.title = self._status_text()
        self._icon.update_menu()

    def _set_guard_mode(self, payload: dict[str, Any], *, notification: str) -> None:
        """Apply a new protection mode through the local agent."""
        try:
            config = load_runtime_config(self._config_path)
            state = build_local_api_request(
                config=config,
                method="POST",
                path=LOCAL_GUARD_ENDPOINT,
                payload=payload,
            )
        except Exception as err:  # pragma: no cover - depends on local Windows runtime
            self._last_error = str(err)
            self._icon.icon = build_tray_image(mode=None, available=False)
            self._icon.title = self._status_text()
            self._icon.update_menu()
            self._notify(self._t("notify_change_failed", error=self._last_error))
            return

        self._cached_state = state
        self._last_error = None
        self._icon.icon = build_tray_image(
            mode=str(state.get("mode") or COMMAND_GUARD_ALLOW),
            available=True,
        )
        self._icon.title = self._status_text()
        self._icon.update_menu()
        self._notify(notification)

    def _allow_requests(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Allow power commands again."""
        self._set_guard_mode(
            {"mode": COMMAND_GUARD_ALLOW},
            notification=self._t("notify_allow"),
        )

    def _ignore_for_15_minutes(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Ignore power requests for 15 minutes."""
        self._set_guard_mode(
            {"mode": COMMAND_GUARD_IGNORE_UNTIL, "duration_minutes": 15},
            notification=self._t("notify_ignore_15"),
        )

    def _ignore_for_1_hour(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Ignore power requests for one hour."""
        self._set_guard_mode(
            {"mode": COMMAND_GUARD_IGNORE_UNTIL, "duration_minutes": 60},
            notification=self._t("notify_ignore_60"),
        )

    def _ignore_manually(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Ignore power requests until the user re-enables them."""
        self._set_guard_mode(
            {"mode": COMMAND_GUARD_IGNORE_MANUAL},
            notification=self._t("notify_ignore_manual"),
        )

    def _refresh_from_menu(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Refresh the displayed protection state."""
        self._refresh_state(notify=True)

    def _open_setup(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Open the desktop configurator."""
        if getattr(sys, "frozen", False):
            agent_dir = Path(sys.executable).resolve().parent
        else:
            agent_dir = Path(__file__).resolve().parent

        setup_exe = agent_dir / "PCPowerSetup.exe"
        setup_script = agent_dir / "setup_wizard_gui.py"
        try:
            if setup_exe.exists():
                subprocess.Popen([str(setup_exe)])
                return
            subprocess.Popen([sys.executable, str(setup_script)])
        except Exception as err:  # pragma: no cover - depends on local Windows runtime
            self._notify(self._t("notify_open_setup_failed", error=err))

    def _quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Stop the tray icon."""
        self._icon.stop()

    def _notify(self, message: str) -> None:
        """Show a best-effort tray notification."""
        try:
            self._icon.notify(message, APP_TITLE)
        except Exception:
            pass


def parse_args() -> argparse.Namespace:
    """Parse tray CLI arguments."""
    parser = argparse.ArgumentParser(description="Run the PC Power Free system tray app")
    parser.add_argument("--config", help="Path to config.json")
    return parser.parse_args()


def main() -> int:
    """Start the tray application."""
    mutex = acquire_single_instance_mutex()
    if mutex is None:
        return 0

    args = parse_args()
    config_path = (
        Path(args.config).expanduser().resolve()
        if args.config
        else resolve_default_config_path()
    )

    tray_app = TrayApp(config_path)
    try:
        tray_app.run()
    finally:
        ctypes.windll.kernel32.CloseHandle(mutex)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
