"""Simple Linux setup flow for PC Power Free."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
import uuid

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_core.common import (
    DEFAULT_PORT,
    PAIRING_CODE_TTL_SECONDS,
    generate_pairing_code,
    generate_token,
    hash_pairing_code,
)
from network_info import detect_primary_adapter


def build_allowed_subnets(home_assistant_ip: str, subnet_cidr: str) -> list[str]:
    """Return API restrictions for the Linux agent."""
    if home_assistant_ip:
        return [f"{home_assistant_ip}/32", "127.0.0.1/32"]
    return [subnet_cidr, "127.0.0.1/32"]


def load_existing_config(config_path: Path) -> dict[str, object]:
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
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure the PC Power Free Linux agent")
    parser.add_argument(
        "--config",
        default=str(CURRENT_DIR / "config.json"),
        help="Path to the output config.json",
    )
    parser.add_argument(
        "--home-assistant-ip",
        default="",
        help="Restrict access to a specific Home Assistant IP",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Agent port",
    )
    parser.add_argument(
        "--token",
        default="",
        help="Use an explicit API token instead of generating a new one",
    )
    parser.add_argument(
        "--pairing-code",
        default="",
        help="Use an explicit 6-digit pairing code instead of generating a new one",
    )
    parser.add_argument(
        "--force-shutdown",
        action="store_true",
        help="Store shutdown_force=true in the config",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    existing_config = load_existing_config(config_path)
    adapter = detect_primary_adapter()

    token = str(args.token or existing_config.get("token") or generate_token()).strip()
    if len(token) < 16:
        raise SystemExit("The token must be at least 16 characters long.")

    pairing_code = str(args.pairing_code or generate_pairing_code()).strip()
    if len(pairing_code) != 6 or not pairing_code.isdigit():
        raise SystemExit("The pairing code must be exactly 6 digits.")

    machine_id = str(existing_config.get("machine_id") or uuid.uuid4().hex).strip().lower()
    allowed_subnets = build_allowed_subnets(args.home_assistant_ip.strip(), adapter.subnet_cidr)

    write_config(
        config_path,
        port=args.port,
        token=token,
        allowed_subnets=allowed_subnets,
        force=bool(args.force_shutdown or existing_config.get("shutdown_force", False)),
        machine_id=machine_id,
        pairing_code_hash=hash_pairing_code(pairing_code),
        pairing_code_expires_at=time.time() + PAIRING_CODE_TTL_SECONDS,
    )

    print("PC Power Free Linux setup completed.")
    print()
    print(f"Computer: {adapter.hostname}")
    print(f"Adapter: {adapter.interface_alias}")
    print(f"Current IP: {adapter.ipv4_address}")
    print(f"MAC: {adapter.mac_address}")
    print(f"Discovery subnet: {adapter.subnet_cidr}")
    print(f"Wake-on-LAN broadcast: {adapter.broadcast_address}")
    print(f"Agent port: {args.port}")
    print(f"Machine ID: {machine_id}")
    print(f"Pairing code: {pairing_code}")
    print(f"Config written to: {config_path}")
    print()
    print("Next steps:")
    print("1. Start the Linux agent with the generated config.")
    print("2. Add or open PC Power Free in Home Assistant.")
    print("3. Enter the pairing code before it expires.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
