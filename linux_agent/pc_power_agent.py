"""Linux runtime wrapper for the shared PC Power Free agent."""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import subprocess
import sys

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_core.common import PowerActionError, run_agent
from network_info import AdapterInfo, detect_primary_adapter, get_local_mac_addresses

DEFAULT_PLATFORM_ID = "linux"
SUPPORTED_PLATFORM_IDS = {"linux", "dsm"}


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

    capabilities = ("shutdown", "restart", "guard", "pairing", "discovery")

    def __init__(self, platform_id: str = DEFAULT_PLATFORM_ID) -> None:
        """Store the effective platform ID exposed by this runtime."""
        self.platform_id = platform_id

    def detect_primary_adapter(self) -> AdapterInfo:
        """Return the adapter used for discovery and Wake-on-LAN."""
        return detect_primary_adapter()

    def get_mac_addresses(self) -> list[str]:
        """Return MAC addresses for the local Linux host."""
        return get_local_mac_addresses()

    def get_system_uptime_seconds(self) -> int | None:
        """Return the Linux uptime in seconds."""
        return get_system_uptime_seconds()

    def execute_power_action(self, action: str, *, delay_seconds: int, force: bool) -> None:
        """Run the local Linux shutdown or restart command."""
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


class DsmPlatformAdapter(LinuxPlatformAdapter):
    """DSM's agent adds authenticated access to local setup actions."""

    def __init__(self) -> None:
        super().__init__(platform_id="dsm")

    def power_permission_enabled(self) -> bool:
        """Query both fixed permissions without executing a power action."""
        try:
            return all(subprocess.run(
                ["/usr/bin/sudo", "-n", "-l", "/usr/syno/sbin/synoshutdown", flag],
                capture_output=True, text=True, timeout=2,
            ).returncode == 0 for flag in ("--shutdown", "--reboot"))
        except (OSError, subprocess.SubprocessError):
            return False

    def execute_power_action(self, action: str, *, delay_seconds: int, force: bool) -> None:
        """Use DSM's normal shutdown checks with narrowly granted privileges."""
        flags = {"shutdown": "--shutdown", "restart": "--reboot"}
        if action not in flags:
            raise PowerActionError(f"Unsupported action: {action}")
        if force or delay_seconds != 0:
            raise PowerActionError("DSM supports normal, immediate power actions only")
        command = ["/usr/syno/sbin/synoshutdown", flags[action]]
        try:
            permission = subprocess.run(
                ["/usr/bin/sudo", "-n", "-l", *command],
                capture_output=True, text=True, timeout=10,
            )
            if permission.returncode != 0:
                raise PowerActionError(
                    "DSM power permission is not enabled; run WakeLink's one-time DSM power setup",
                    details=permission.stderr.strip() or permission.stdout.strip(),
                )
            subprocess.run(
                ["/usr/bin/sudo", "-n", *command],
                check=True, capture_output=True, text=True, timeout=10,
            )
        except FileNotFoundError as err:
            raise PowerActionError("DSM power command not found", details=str(err)) from err
        except subprocess.TimeoutExpired as err:
            # Do not retry: DSM might already have accepted the shutdown.
            raise PowerActionError("DSM power command timed out; check the NAS before retrying") from err
        except subprocess.CalledProcessError as err:
            details = (err.stderr or err.stdout or "").strip()
            raise PowerActionError(
                f"DSM rejected the power action: {details}" if details else "DSM power command failed",
                details=details,
            ) from err

    def authenticate_setup_request(
        self, cookie: str, remote_addr: str, server_addr: str,
        *, syno_token: str = "", syno_hash: str = "",
    ) -> bool:
        from dsm_runtime.setup_auth import authenticate_admin

        return authenticate_admin(
            cookie, remote_addr, server_addr, syno_token=syno_token, syno_hash=syno_hash,
        )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run the PC Power Free Linux agent")
    parser.add_argument("--config", required=True, help="Path to config.json")
    return parser.parse_args()


def main() -> int:
    """Start the Linux agent runtime."""
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    platform_id = os.environ.get("PC_POWER_PLATFORM_ID", DEFAULT_PLATFORM_ID).strip().lower()
    if platform_id not in SUPPORTED_PLATFORM_IDS:
        platform_id = DEFAULT_PLATFORM_ID
    return run_agent(
        config_path=config_path,
        platform=DsmPlatformAdapter() if platform_id == "dsm" else LinuxPlatformAdapter(),
        logger_name=f"pc_power_agent.{platform_id}",
    )


if __name__ == "__main__":
    raise SystemExit(main())
