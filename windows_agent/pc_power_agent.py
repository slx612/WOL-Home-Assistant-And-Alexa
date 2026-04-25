"""Windows runtime wrapper for the shared PC Power Free agent."""

from __future__ import annotations

import argparse
import ctypes
from pathlib import Path
import subprocess
import sys
import uuid

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_core.common import AGENT_VERSION, PowerActionError, run_agent
from network_info import AdapterInfo, detect_primary_adapter


def build_windows_command(action: str, *, delay_seconds: int, force: bool) -> list[str]:
    """Return the Windows command for a power action."""
    if action == "shutdown":
        command = ["shutdown", "/s", "/t", str(delay_seconds)]
    elif action == "restart":
        command = ["shutdown", "/r", "/t", str(delay_seconds)]
    else:
        raise PowerActionError(f"Unsupported action: {action}")

    if force:
        command.append("/f")

    return command


def get_system_uptime_seconds() -> int | None:
    """Return the Windows uptime in whole seconds."""
    try:
        return int(ctypes.windll.kernel32.GetTickCount64() // 1000)
    except (AttributeError, OSError):
        return None


def get_local_mac_addresses() -> list[str]:
    """Return the MAC addresses that identify this Windows machine."""
    mac_addresses: list[str] = []
    try:
        result = subprocess.run(
            ["getmac", "/fo", "csv", "/nh"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        fallback_mac = _format_mac_int(uuid.getnode())
        return [fallback_mac] if fallback_mac else []

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip().strip('"')
        if not line:
            continue
        device_fields = [item.strip().strip('"') for item in raw_line.split(",")]
        if not device_fields:
            continue
        mac_value = device_fields[0]
        if mac_value and mac_value != "N/A":
            normalized = _normalize_mac_string(mac_value)
            if normalized and normalized not in mac_addresses:
                mac_addresses.append(normalized)

    if not mac_addresses:
        fallback_mac = _format_mac_int(uuid.getnode())
        if fallback_mac:
            mac_addresses.append(fallback_mac)

    return mac_addresses


def _normalize_mac_string(value: str) -> str | None:
    """Normalize a MAC string into AA:BB:CC:DD:EE:FF."""
    cleaned = "".join(character for character in value if character.isalnum())
    if len(cleaned) != 12:
        return None
    return ":".join(cleaned[index : index + 2] for index in range(0, 12, 2)).upper()


def _format_mac_int(value: int) -> str | None:
    """Format an integer MAC address."""
    if value <= 0 or value >= 1 << 48:
        return None
    raw = f"{value:012x}"
    return ":".join(raw[index : index + 2] for index in range(0, 12, 2)).upper()


class WindowsPlatformAdapter:
    """Windows-specific hooks consumed by the shared agent runtime."""

    platform_id = "windows"
    capabilities = ("shutdown", "restart", "guard", "pairing", "discovery")

    def detect_primary_adapter(self) -> AdapterInfo:
        """Return the adapter used for discovery and Wake-on-LAN."""
        return detect_primary_adapter()

    def get_mac_addresses(self) -> list[str]:
        """Return MAC addresses for the local Windows host."""
        return get_local_mac_addresses()

    def get_system_uptime_seconds(self) -> int | None:
        """Return the Windows uptime in seconds."""
        return get_system_uptime_seconds()

    def execute_power_action(self, action: str, *, delay_seconds: int, force: bool) -> None:
        """Run the local Windows shutdown or restart command."""
        command = build_windows_command(action, delay_seconds=delay_seconds, force=force)
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as err:
            raise PowerActionError("Windows command failed", details=err.stderr.strip()) from err


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run the PC Power Free Windows agent")
    parser.add_argument("--config", required=True, help="Path to config.json")
    return parser.parse_args()


def main() -> int:
    """Start the Windows agent runtime."""
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    return run_agent(
        config_path=config_path,
        platform=WindowsPlatformAdapter(),
        logger_name="pc_power_agent.windows",
    )


if __name__ == "__main__":
    raise SystemExit(main())
