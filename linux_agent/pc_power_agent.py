"""Linux runtime wrapper for the shared PC Power Free agent."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import subprocess
import sys

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_core.common import PowerActionError, run_agent
from network_info import AdapterInfo, detect_primary_adapter, get_local_mac_addresses


def build_linux_command(action: str, *, delay_seconds: int, force: bool) -> list[str]:
    """Return the Linux command for a power action."""
    if delay_seconds <= 0:
        if force:
            if action == "shutdown":
                return ["poweroff", "-f"]
            if action == "restart":
                return ["reboot", "-f"]
        if action == "shutdown":
            return ["shutdown", "-P", "now"]
        if action == "restart":
            return ["shutdown", "-r", "now"]
        raise PowerActionError(f"Unsupported action: {action}")

    delay_minutes = max(1, math.ceil(delay_seconds / 60))
    if action == "shutdown":
        return ["shutdown", "-P", f"+{delay_minutes}"]
    if action == "restart":
        return ["shutdown", "-r", f"+{delay_minutes}"]
    raise PowerActionError(f"Unsupported action: {action}")


def get_system_uptime_seconds() -> int | None:
    """Return the Linux uptime in whole seconds."""
    uptime_path = Path("/proc/uptime")
    try:
        raw_value = uptime_path.read_text(encoding="utf-8").split()[0]
        return int(float(raw_value))
    except (OSError, ValueError, IndexError):
        return None


class LinuxPlatformAdapter:
    """Linux-specific hooks consumed by the shared agent runtime."""

    platform_id = "linux"
    capabilities = ("shutdown", "restart", "guard", "pairing", "discovery")

    def detect_primary_adapter(self) -> AdapterInfo:
        return detect_primary_adapter()

    def get_mac_addresses(self) -> list[str]:
        return get_local_mac_addresses()

    def get_system_uptime_seconds(self) -> int | None:
        return get_system_uptime_seconds()

    def execute_power_action(self, action: str, *, delay_seconds: int, force: bool) -> None:
        command = build_linux_command(action, delay_seconds=delay_seconds, force=force)
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError as err:
            raise PowerActionError(
                "Linux power command not found",
                details=str(err),
            ) from err
        except subprocess.CalledProcessError as err:
            raise PowerActionError(
                "Linux power command failed",
                details=err.stderr.strip() or err.stdout.strip(),
            ) from err


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PC Power Free Linux agent")
    parser.add_argument("--config", required=True, help="Path to config.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    return run_agent(
        config_path=config_path,
        platform=LinuxPlatformAdapter(),
        logger_name="pc_power_agent.linux",
    )


if __name__ == "__main__":
    raise SystemExit(main())
