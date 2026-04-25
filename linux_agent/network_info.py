"""Helpers to detect the primary Linux network adapter."""

from __future__ import annotations

from dataclasses import dataclass
import ipaddress
from pathlib import Path
import socket
import sys
import uuid

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_core.common import AdapterInfo

import ifaddr


@dataclass(slots=True)
class _AdapterCandidate:
    adapter_info: AdapterInfo
    has_default_route: bool
    is_link_local: bool
    is_virtual: bool
    matches_primary_ip: bool


def normalize_mac(value: str) -> str:
    cleaned = "".join(character for character in value if character.isalnum())
    if len(cleaned) != 12:
        raise ValueError("The detected MAC address is invalid")
    return ":".join(cleaned[index : index + 2] for index in range(0, 12, 2)).upper()


def _detect_primary_ipv4_address() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.connect(("8.8.8.8", 80))
            ip_address = udp_socket.getsockname()[0]
    except OSError:
        return None

    try:
        parsed = ipaddress.ip_address(ip_address)
    except ValueError:
        return None
    return str(parsed) if isinstance(parsed, ipaddress.IPv4Address) else None


def _load_default_route_interfaces() -> set[str]:
    route_file = Path("/proc/net/route")
    if not route_file.exists():
        return set()

    interfaces: set[str] = set()
    for line in route_file.read_text(encoding="utf-8", errors="ignore").splitlines()[1:]:
        fields = line.split()
        if len(fields) < 4:
            continue
        interface_name, destination, flags_hex = fields[0], fields[1], fields[3]
        try:
            flags = int(flags_hex, 16)
        except ValueError:
            continue
        if destination == "00000000" and flags & 0x1:
            interfaces.add(interface_name)
    return interfaces


def _read_interface_mac(interface_name: str) -> str | None:
    address_path = Path("/sys/class/net") / interface_name / "address"
    try:
        raw = address_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not raw or raw == "00:00:00:00:00:00":
        return None
    try:
        return normalize_mac(raw)
    except ValueError:
        return None


def _looks_virtual_interface(*values: str) -> bool:
    combined = " ".join(value.lower() for value in values if value)
    virtual_keywords = (
        "docker",
        "veth",
        "virbr",
        "virtual",
        "vmware",
        "hyper-v",
        "bridge",
        "loopback",
        "tailscale",
        "wireguard",
        "zerotier",
        "tun",
        "tap",
    )
    return any(keyword in combined for keyword in virtual_keywords)


def detect_primary_adapter() -> AdapterInfo:
    hostname = socket.gethostname() or "PC Linux"
    primary_ip = _detect_primary_ipv4_address()
    default_route_interfaces = _load_default_route_interfaces()

    candidates: list[_AdapterCandidate] = []
    for adapter in ifaddr.get_adapters():
        interface_name = adapter.name
        mac_address = _read_interface_mac(interface_name)
        if not mac_address:
            continue

        for ip_info in adapter.ips:
            if not ip_info.is_IPv4:
                continue
            if not isinstance(ip_info.ip, str):
                continue

            ipv4_address = ip_info.ip.strip()
            if not ipv4_address:
                continue

            network = ipaddress.ip_network(
                f"{ipv4_address}/{int(ip_info.network_prefix)}",
                strict=False,
            )
            parsed_ip = ipaddress.ip_address(ipv4_address)
            interface_alias = adapter.nice_name or interface_name
            adapter_info = AdapterInfo(
                hostname=hostname,
                interface_alias=interface_alias,
                ipv4_address=ipv4_address,
                prefix_length=network.prefixlen,
                mac_address=mac_address,
                subnet_cidr=f"{network.network_address}/{network.prefixlen}",
                broadcast_address=str(network.broadcast_address),
            )
            candidates.append(
                _AdapterCandidate(
                    adapter_info=adapter_info,
                    has_default_route=interface_name in default_route_interfaces,
                    is_link_local=parsed_ip.is_link_local,
                    is_virtual=_looks_virtual_interface(interface_name, interface_alias),
                    matches_primary_ip=bool(primary_ip and ipv4_address == primary_ip),
                )
            )
            break

    if not candidates:
        raise RuntimeError("No valid IPv4 adapter was found")

    ranked_candidates = sorted(
        candidates,
        key=lambda candidate: (
            candidate.matches_primary_ip,
            candidate.has_default_route,
            not candidate.is_link_local,
            not candidate.is_virtual,
        ),
        reverse=True,
    )
    return ranked_candidates[0].adapter_info


def get_local_mac_addresses() -> list[str]:
    mac_addresses: list[str] = []
    interfaces_dir = Path("/sys/class/net")
    if interfaces_dir.exists():
        for interface_dir in interfaces_dir.iterdir():
            if interface_dir.name == "lo":
                continue
            mac_address = _read_interface_mac(interface_dir.name)
            if mac_address and mac_address not in mac_addresses:
                mac_addresses.append(mac_address)

    if not mac_addresses:
        fallback = _format_mac_int(uuid.getnode())
        if fallback:
            mac_addresses.append(fallback)

    return mac_addresses


def _format_mac_int(value: int) -> str | None:
    if value <= 0 or value >= 1 << 48:
        return None
    raw = f"{value:012x}"
    return ":".join(raw[index : index + 2] for index in range(0, 12, 2)).upper()
