"""Helpers to detect the primary Windows network adapter."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import ipaddress
from pathlib import Path
import socket
import sys

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_core.common import AdapterInfo

AF_UNSPEC = 0
AF_INET = socket.AF_INET
ERROR_BUFFER_OVERFLOW = 111
GAA_FLAG_INCLUDE_GATEWAYS = 0x0080
IF_OPER_STATUS_UP = 1
IF_TYPE_SOFTWARE_LOOPBACK = 24
IF_TYPE_TUNNEL = 131
MAX_ADAPTER_ADDRESS_LENGTH = 8


class SOCKADDR(ctypes.Structure):
    """Minimal sockaddr header used to inspect the address family."""

    _fields_ = [
        ("sa_family", wintypes.USHORT),
        ("sa_data", ctypes.c_char * 14),
    ]


class SOCKADDR_IN(ctypes.Structure):
    """IPv4 sockaddr layout."""

    _fields_ = [
        ("sin_family", wintypes.USHORT),
        ("sin_port", wintypes.USHORT),
        ("sin_addr", ctypes.c_ubyte * 4),
        ("sin_zero", ctypes.c_ubyte * 8),
    ]


class SOCKET_ADDRESS(ctypes.Structure):
    """Socket address wrapper used by IP Helper."""

    _fields_ = [
        ("lpSockaddr", ctypes.POINTER(SOCKADDR)),
        ("iSockaddrLength", ctypes.c_int),
    ]


class IP_ADAPTER_UNICAST_ADDRESS(ctypes.Structure):
    """Linked-list node containing a unicast IP address."""


IP_ADAPTER_UNICAST_ADDRESS_POINTER = ctypes.POINTER(IP_ADAPTER_UNICAST_ADDRESS)
IP_ADAPTER_UNICAST_ADDRESS._fields_ = [
    ("Length", wintypes.ULONG),
    ("Flags", wintypes.DWORD),
    ("Next", IP_ADAPTER_UNICAST_ADDRESS_POINTER),
    ("Address", SOCKET_ADDRESS),
    ("PrefixOrigin", wintypes.ULONG),
    ("SuffixOrigin", wintypes.ULONG),
    ("DadState", wintypes.ULONG),
    ("ValidLifetime", wintypes.ULONG),
    ("PreferredLifetime", wintypes.ULONG),
    ("LeaseLifetime", wintypes.ULONG),
    ("OnLinkPrefixLength", ctypes.c_ubyte),
]


class IP_ADAPTER_GATEWAY_ADDRESS(ctypes.Structure):
    """Linked-list node containing a gateway IP address."""


IP_ADAPTER_GATEWAY_ADDRESS_POINTER = ctypes.POINTER(IP_ADAPTER_GATEWAY_ADDRESS)
IP_ADAPTER_GATEWAY_ADDRESS._fields_ = [
    ("Length", wintypes.ULONG),
    ("Reserved", wintypes.DWORD),
    ("Next", IP_ADAPTER_GATEWAY_ADDRESS_POINTER),
    ("Address", SOCKET_ADDRESS),
]


class IP_ADAPTER_ADDRESSES(ctypes.Structure):
    """Truncated Windows adapter structure with the fields we use."""


IP_ADAPTER_ADDRESSES_POINTER = ctypes.POINTER(IP_ADAPTER_ADDRESSES)
IP_ADAPTER_ADDRESSES._fields_ = [
    ("Length", wintypes.ULONG),
    ("IfIndex", wintypes.DWORD),
    ("Next", IP_ADAPTER_ADDRESSES_POINTER),
    ("AdapterName", ctypes.c_char_p),
    ("FirstUnicastAddress", IP_ADAPTER_UNICAST_ADDRESS_POINTER),
    ("FirstAnycastAddress", ctypes.c_void_p),
    ("FirstMulticastAddress", ctypes.c_void_p),
    ("FirstDnsServerAddress", ctypes.c_void_p),
    ("DnsSuffix", ctypes.c_wchar_p),
    ("Description", ctypes.c_wchar_p),
    ("FriendlyName", ctypes.c_wchar_p),
    ("PhysicalAddress", ctypes.c_ubyte * MAX_ADAPTER_ADDRESS_LENGTH),
    ("PhysicalAddressLength", wintypes.DWORD),
    ("Flags", wintypes.DWORD),
    ("Mtu", wintypes.DWORD),
    ("IfType", wintypes.DWORD),
    ("OperStatus", wintypes.DWORD),
    ("Ipv6IfIndex", wintypes.DWORD),
    ("ZoneIndices", wintypes.DWORD * 16),
    ("FirstPrefix", ctypes.c_void_p),
    ("TransmitLinkSpeed", ctypes.c_ulonglong),
    ("ReceiveLinkSpeed", ctypes.c_ulonglong),
    ("FirstWinsServerAddress", ctypes.c_void_p),
    ("FirstGatewayAddress", IP_ADAPTER_GATEWAY_ADDRESS_POINTER),
]


@dataclass(slots=True)
class _AdapterCandidate:
    """Candidate adapter plus metadata used for ranking."""

    adapter_info: AdapterInfo
    has_gateway: bool
    is_link_local: bool
    is_virtual: bool
    matches_primary_ip: bool


def normalize_mac(value: str) -> str:
    """Normalize a MAC address into AA:BB:CC:DD:EE:FF."""
    cleaned = "".join(character for character in value if character.isalnum())
    if len(cleaned) != 12:
        raise ValueError("La MAC detectada no es valida")
    return ":".join(cleaned[index : index + 2] for index in range(0, 12, 2)).upper()


def _detect_primary_ipv4_address() -> str | None:
    """Return the IPv4 address Windows would currently use for outbound traffic."""
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


def _looks_virtual_adapter(*values: str) -> bool:
    """Best-effort detection for virtual-only adapters."""
    combined = " ".join(value.lower() for value in values if value)
    virtual_keywords = (
        "virtualbox",
        "hyper-v",
        "vmware",
        "loopback",
        "host-only",
        "default switch",
        "wireguard",
        "tailscale",
        "vpn",
    )
    return any(keyword in combined for keyword in virtual_keywords)


def _socket_address_to_ipv4(socket_address: SOCKET_ADDRESS) -> str | None:
    """Convert a Windows SOCKET_ADDRESS into an IPv4 string if possible."""
    if not socket_address.lpSockaddr or socket_address.iSockaddrLength < ctypes.sizeof(SOCKADDR_IN):
        return None

    sockaddr = socket_address.lpSockaddr.contents
    if sockaddr.sa_family != AF_INET:
        return None

    sockaddr_in = ctypes.cast(socket_address.lpSockaddr, ctypes.POINTER(SOCKADDR_IN)).contents
    return socket.inet_ntoa(bytes(sockaddr_in.sin_addr))


def _iter_linked_list(start_pointer: ctypes._Pointer) -> list[ctypes.Structure]:
    """Materialize a Windows linked list into Python objects."""
    items: list[ctypes.Structure] = []
    current = start_pointer
    while current:
        items.append(current.contents)
        current = current.contents.Next
    return items


def _get_adapter_addresses() -> list[IP_ADAPTER_ADDRESSES]:
    """Return the current adapter list using the Windows IP Helper API."""
    iphlpapi = ctypes.WinDLL("iphlpapi.dll")
    get_adapters_addresses = iphlpapi.GetAdaptersAddresses
    get_adapters_addresses.argtypes = [
        wintypes.ULONG,
        wintypes.ULONG,
        ctypes.c_void_p,
        IP_ADAPTER_ADDRESSES_POINTER,
        ctypes.POINTER(wintypes.ULONG),
    ]
    get_adapters_addresses.restype = wintypes.ULONG

    buffer_length = wintypes.ULONG(15_000)
    raw_buffer = ctypes.create_string_buffer(buffer_length.value)

    result = get_adapters_addresses(
        AF_UNSPEC,
        GAA_FLAG_INCLUDE_GATEWAYS,
        None,
        ctypes.cast(raw_buffer, IP_ADAPTER_ADDRESSES_POINTER),
        ctypes.byref(buffer_length),
    )
    if result == ERROR_BUFFER_OVERFLOW:
        raw_buffer = ctypes.create_string_buffer(buffer_length.value)
        result = get_adapters_addresses(
            AF_UNSPEC,
            GAA_FLAG_INCLUDE_GATEWAYS,
            None,
            ctypes.cast(raw_buffer, IP_ADAPTER_ADDRESSES_POINTER),
            ctypes.byref(buffer_length),
        )
    if result != 0:
        raise OSError(f"GetAdaptersAddresses devolvio el error {result}")

    adapter_pointer = ctypes.cast(raw_buffer, IP_ADAPTER_ADDRESSES_POINTER)
    adapters: list[IP_ADAPTER_ADDRESSES] = []
    current = adapter_pointer
    while current:
        adapters.append(current.contents)
        current = current.contents.Next
    return adapters


def _iter_adapter_candidates(*, hostname: str, primary_ip: str | None) -> list[_AdapterCandidate]:
    """Build ranked candidates from the current Windows adapter list."""
    candidates: list[_AdapterCandidate] = []

    for adapter in _get_adapter_addresses():
        if adapter.OperStatus != IF_OPER_STATUS_UP:
            continue
        if adapter.IfType == IF_TYPE_SOFTWARE_LOOPBACK:
            continue
        if adapter.PhysicalAddressLength <= 0:
            continue

        friendly_name = str(adapter.FriendlyName or adapter.Description or "Network adapter").strip()
        description = str(adapter.Description or friendly_name).strip()
        is_virtual = adapter.IfType == IF_TYPE_TUNNEL or _looks_virtual_adapter(
            friendly_name,
            description,
        )

        mac_bytes = bytes(adapter.PhysicalAddress[: adapter.PhysicalAddressLength])
        mac_address = normalize_mac(mac_bytes.hex())
        has_gateway = any(
            _socket_address_to_ipv4(gateway.Address)
            for gateway in _iter_linked_list(adapter.FirstGatewayAddress)
        )

        for unicast in _iter_linked_list(adapter.FirstUnicastAddress):
            ip_address = _socket_address_to_ipv4(unicast.Address)
            if not ip_address:
                continue

            prefix_length = int(unicast.OnLinkPrefixLength)
            if not 0 <= prefix_length <= 32:
                continue

            network = ipaddress.ip_network(f"{ip_address}/{prefix_length}", strict=False)
            parsed_ip = ipaddress.ip_address(ip_address)
            candidates.append(
                _AdapterCandidate(
                    adapter_info=AdapterInfo(
                        hostname=hostname or "PC Windows",
                        interface_alias=friendly_name,
                        ipv4_address=ip_address,
                        prefix_length=network.prefixlen,
                        mac_address=mac_address,
                        subnet_cidr=f"{network.network_address}/{network.prefixlen}",
                        broadcast_address=str(network.broadcast_address),
                    ),
                    has_gateway=has_gateway,
                    is_link_local=parsed_ip.is_link_local,
                    is_virtual=is_virtual,
                    matches_primary_ip=bool(primary_ip and ip_address == primary_ip),
                )
            )

    return candidates


def detect_primary_adapter() -> AdapterInfo:
    """Detect the active adapter to use for Wake-on-LAN."""
    hostname = socket.gethostname() or "PC Windows"
    primary_ip = _detect_primary_ipv4_address()

    try:
        candidates = _iter_adapter_candidates(hostname=hostname, primary_ip=primary_ip)
    except OSError as err:
        raise RuntimeError(f"No se pudo consultar la configuracion de red de Windows: {err}") from err

    if not candidates:
        raise RuntimeError("No se ha encontrado un adaptador IPv4 valido")

    ranked_candidates = sorted(
        candidates,
        key=lambda candidate: (
            candidate.matches_primary_ip,
            candidate.has_gateway,
            not candidate.is_link_local,
            not candidate.is_virtual,
        ),
        reverse=True,
    )
    return ranked_candidates[0].adapter_info
