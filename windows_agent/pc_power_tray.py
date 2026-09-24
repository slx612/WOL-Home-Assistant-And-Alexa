"""WakeLink system tray companion; existing PC Power Free identities retained."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
import ssl
import subprocess
import sys
import threading
import time
from typing import Any
from urllib import request as urllib_request
import webbrowser

from PIL import Image, ImageDraw
import pystray

from ui_preferences import load_language
from update_check import (
    GitHubRelease,
    fetch_latest_github_release,
    format_update_error,
    is_newer_version,
    normalize_version_text,
    parse_version_key,
)

APP_NAME = "WakeLink"
APP_TITLE = "WakeLink"
APP_DIR_NAME = "PC Power Free"
APP_VERSION = "0.2.0-beta.12"
DEFAULT_AGENT_PORT = 58477
CONFIG_FILENAME = "config.json"
COMMAND_GUARD_ALLOW = "allow"
COMMAND_GUARD_IGNORE_MANUAL = "ignore_manual"
COMMAND_GUARD_IGNORE_UNTIL = "ignore_until"
LOCAL_GUARD_ENDPOINT = "/v1/local/guard"
MUTEX_NAME = "Local\\PCPowerFreeTraySingleton"
UPDATE_STATE_FILENAME = "update_state.json"
UPDATE_CHECK_INTERVAL_SECONDS = 6 * 60 * 60
UPDATE_CHECK_STARTUP_DELAY_SECONDS = 5

TRANSLATIONS = {
    "en": {
        "status_not_configured": "WakeLink is not configured yet",
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
        "menu_check_updates": "Check for updates",
        "menu_checking_updates": "Checking for updates...",
        "menu_refresh": "Refresh status",
        "menu_open_setup": "Open WakeLink",
        "menu_exit": "Exit tray icon",
        "notify_refresh_failed": "Could not refresh status: {error}",
        "notify_change_failed": "Could not change protection: {error}",
        "notify_update_check_running": "Update check already in progress.",
        "notify_update_check_failed": "Could not check updates: {error}",
        "notify_up_to_date": "No newer Windows installer is available for WakeLink.\n\nInstalled version: {version}",
        "update_browser_failed": "Could not open your browser. Download the installer manually:\n\n{url}",
        "notify_allow": "Home Assistant requests are allowed again.",
        "notify_ignore_15": "Home Assistant requests will be ignored for 15 minutes.",
        "notify_ignore_60": "Home Assistant requests will be ignored for 1 hour.",
        "notify_ignore_manual": "Home Assistant requests will be ignored until you re-enable them.",
        "notify_open_setup_failed": "Could not open the configurator: {error}",
        "update_available_title": "Update available",
        "update_available_message": (
            "A newer version of WakeLink with a Windows installer is available.\n\n"
            "Installed version: {current_version}\n"
            "Latest version: {latest_version}\n\n"
            "Download the installer now? Save your work before running it."
        ),
    },
    "es": {
        "status_not_configured": "WakeLink todavia no esta configurado",
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
        "menu_check_updates": "Buscar actualizaciones",
        "menu_checking_updates": "Buscando actualizaciones...",
        "menu_refresh": "Actualizar estado",
        "menu_open_setup": "Abrir WakeLink",
        "menu_exit": "Salir del icono de bandeja",
        "notify_refresh_failed": "No se pudo actualizar el estado: {error}",
        "notify_change_failed": "No se pudo cambiar la proteccion: {error}",
        "notify_update_check_running": "La comprobacion de actualizaciones ya esta en marcha.",
        "notify_update_check_failed": "No se pudieron comprobar las actualizaciones: {error}",
        "notify_up_to_date": "No hay un instalador de Windows mas nuevo para WakeLink.\n\nVersion instalada: {version}",
        "update_browser_failed": "No se pudo abrir el navegador. Descarga el instalador manualmente:\n\n{url}",
        "notify_allow": "Las ordenes de Home Assistant vuelven a estar permitidas.",
        "notify_ignore_15": "Las ordenes de Home Assistant se ignoraran durante 15 minutos.",
        "notify_ignore_60": "Las ordenes de Home Assistant se ignoraran durante 1 hora.",
        "notify_ignore_manual": "Las ordenes de Home Assistant se ignoraran hasta que lo reactives.",
        "notify_open_setup_failed": "No se pudo abrir el configurador: {error}",
        "update_available_title": "Actualizacion disponible",
        "update_available_message": (
            "Hay una version mas nueva de WakeLink con instalador de Windows.\n\n"
            "Version instalada: {current_version}\n"
            "Ultima version: {latest_version}\n\n"
            "Quieres descargar ahora el instalador? Guarda tu trabajo antes de ejecutarlo."
        ),
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
    return load_language()


def load_runtime_config(config_path: Path) -> dict[str, Any]:
    """Load the agent config that contains token and port."""
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError("config.json does not contain a JSON object")
    raw["_certificate_path"] = str(config_path.parent / "agent-cert.pem")
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
        f"https://127.0.0.1:{agent_port}{path}",
        data=body,
        method=method,
        headers=headers,
    )
    context = ssl.create_default_context(cafile=config["_certificate_path"])
    with urllib_request.urlopen(request, timeout=timeout, context=context) as response:
        raw = json.loads(response.read().decode("utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError("The agent returned an invalid JSON payload")
    return raw


def launch_configurator(path: Path) -> None:
    """Open the daily dashboard normally; it elevates only privileged actions."""
    launch = ctypes.windll.shell32.ShellExecuteW
    launch.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p,
                      ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_int]
    launch.restype = ctypes.c_void_p
    result = launch(None, "open", str(path), None, str(path.parent), 1)
    if not result or result <= 32:
        raise OSError(f"Windows did not open the configurator (code {result})")


def build_tray_image(*, mode: str | None, available: bool) -> Image.Image:
    """Return the tray icon image for the current protection state."""
    accent = "#6b7280" if not available else (
        "#f59e0b" if mode and mode != COMMAND_GUARD_ALLOW else "#34d399"
    )
    asset_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    icon = Image.open(asset_root / "assets" / "wakelink.ico")
    try:
        image = icon.convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
    finally:
        icon.close()
    draw = ImageDraw.Draw(image)
    draw.ellipse((43, 43, 62, 62), fill="#eef3df")
    draw.ellipse((46, 46, 59, 59), fill=accent)
    return image


def load_update_state(path: Path) -> dict[str, Any]:
    """Load the persisted updater state, if any."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def save_update_state(path: Path, payload: dict[str, Any]) -> None:
    """Cache update metadata without allowing storage failures to hide results."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass  # This cache is optional, unlike the agent's configuration.


def show_update_message(message: str, *, error: bool = False) -> None:
    """Show an explicit result even when Windows suppresses tray notifications."""
    ctypes.windll.user32.MessageBoxW(
        None, message, APP_TITLE,
        (0x00000010 if error else 0x00000040) | 0x00010000 | 0x00040000,
    )


def ask_yes_no(title: str, message: str) -> bool:
    """Show a native yes/no dialog and return True for Yes."""
    user32 = ctypes.windll.user32
    result = user32.MessageBoxW(
        None,
        message,
        title,
        0x00000004 | 0x00000020 | 0x00010000 | 0x00040000,
    )
    return result == 6


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
        cache_root = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        self._update_state_path = (
            Path(cache_root) / APP_DIR_NAME / UPDATE_STATE_FILENAME
            if cache_root else config_path.with_name(UPDATE_STATE_FILENAME)
        )
        self._language_code = resolve_language()
        self._cached_state: dict[str, Any] | None = None
        self._last_error: str | None = None
        self._update_check_in_progress = False
        self._manual_update_requested = threading.Event()
        self._icon = pystray.Icon(APP_DIR_NAME)
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
            pystray.MenuItem(
                lambda item: self._t("menu_checking_updates" if self._update_check_in_progress else "menu_check_updates"),
                self._check_updates_from_menu,
            ),
            pystray.MenuItem(lambda item: self._t("menu_refresh"), self._refresh_from_menu),
            pystray.MenuItem(lambda item: self._t("menu_open_setup"), self._open_setup, default=True),
            pystray.MenuItem(lambda item: self._t("menu_exit"), self._quit),
        )

    def _t(self, key: str, **kwargs: Any) -> str:
        """Translate a tray string."""
        self._language_code = resolve_language()
        return TRANSLATIONS[self._language_code][key].format(**kwargs)

    def run(self) -> None:
        """Run the tray application."""
        self._refresh_state(notify=False)
        self._start_update_check(manual=False)
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

    def _check_updates_from_menu(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Check GitHub for updates from the tray menu."""
        self._start_update_check(manual=True)

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
                launch_configurator(setup_exe)
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

    def _start_update_check(self, *, manual: bool) -> None:
        """Start an asynchronous GitHub update check."""
        if self._update_check_in_progress:
            if manual:
                self._manual_update_requested.set()
                show_update_message(self._t("notify_update_check_running"))
            return

        self._update_check_in_progress = True
        self._manual_update_requested.clear()
        self._icon.update_menu()
        try:
            worker = threading.Thread(
                target=self._update_check_worker,
                args=(manual,),
                daemon=True,
            )
            worker.start()
        except Exception as err:
            self._update_check_in_progress = False
            self._icon.update_menu()
            if manual:
                show_update_message(self._t("notify_update_check_failed", error=format_update_error(err)), error=True)

    def _update_check_worker(self, manual: bool) -> None:
        """Run the update check without blocking the tray UI."""
        try:
            if not manual:
                self._manual_update_requested.wait(UPDATE_CHECK_STARTUP_DELAY_SECONDS)
                if not self._should_auto_check_updates() and not self._manual_update_requested.is_set():
                    return

            latest_release = fetch_latest_github_release()
            self._record_update_check(latest_release.version)
            if is_newer_version(latest_release.version, APP_VERSION):
                if self._should_prompt_for_release(latest_release.version) or manual or self._manual_update_requested.is_set():
                    should_open = ask_yes_no(
                        self._t("update_available_title"),
                        self._t(
                            "update_available_message",
                            current_version=APP_VERSION,
                            latest_version=latest_release.version,
                        ),
                    )
                    self._record_prompted_release(latest_release.version)
                    if should_open:
                        try:
                            opened = webbrowser.open(latest_release.installer_url)
                        except Exception:
                            opened = False
                        if not opened:
                            show_update_message(self._t("update_browser_failed", url=latest_release.installer_url), error=True)
                return

            if manual or self._manual_update_requested.is_set():
                show_update_message(self._t("notify_up_to_date", version=APP_VERSION))
        except Exception as err:  # pragma: no cover - depends on local Windows runtime
            if manual or self._manual_update_requested.is_set():
                show_update_message(
                    self._t("notify_update_check_failed", error=format_update_error(err)), error=True,
                )
        finally:
            self._manual_update_requested.clear()
            self._update_check_in_progress = False
            self._icon.update_menu()

    def _should_auto_check_updates(self) -> bool:
        """Return whether the startup check should hit GitHub now."""
        state = load_update_state(self._update_state_path)
        last_checked_raw = state.get("last_checked_at")
        try:
            last_checked = float(last_checked_raw)
        except (TypeError, ValueError):
            last_checked = None

        if last_checked is None:
            return True
        return (time.time() - last_checked) >= UPDATE_CHECK_INTERVAL_SECONDS

    def _record_update_check(self, latest_version: str) -> None:
        """Persist when the last successful update check happened."""
        state = load_update_state(self._update_state_path)
        state["last_checked_at"] = time.time()
        state["last_seen_version"] = latest_version
        save_update_state(self._update_state_path, state)

    def _should_prompt_for_release(self, latest_version: str) -> bool:
        """Return whether this release has already been shown automatically."""
        state = load_update_state(self._update_state_path)
        prompted_version = str(state.get("last_prompted_version") or "").strip().lower()
        return prompted_version != normalize_version_text(latest_version)

    def _record_prompted_release(self, latest_version: str) -> None:
        """Persist the latest release version that was shown to the user."""
        state = load_update_state(self._update_state_path)
        state["last_prompted_version"] = normalize_version_text(latest_version)
        state["last_prompted_at"] = time.time()
        save_update_state(self._update_state_path, state)


def parse_args() -> argparse.Namespace:
    """Parse tray CLI arguments."""
    parser = argparse.ArgumentParser(description="Run the WakeLink system tray app")
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
