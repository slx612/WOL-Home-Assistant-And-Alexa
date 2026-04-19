"""Helpers to detect the primary Windows network adapter."""

from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import json
import socket
import subprocess


@dataclass(slots=True)
class AdapterInfo:
    """Detected network adapter settings."""

    hostname: str
    interface_alias: str
    ipv4_address: str
    prefix_length: int
    mac_address: str
    subnet_cidr: str
    broadcast_address: str


def normalize_mac(value: str) -> str:
    """Normalize a MAC address into AA:BB:CC:DD:EE:FF."""
    cleaned = "".join(character for character in value if character.isalnum())
    if len(cleaned) != 12:
        raise ValueError("La MAC detectada no es valida")
    return ":".join(cleaned[index : index + 2] for index in range(0, 12, 2)).upper()


def detect_primary_adapter() -> AdapterInfo:
    """Detect the active adapter to use for Wake-on-LAN."""
    command = r"""
$items = Get-NetIPConfiguration |
  Where-Object { $_.NetAdapter.Status -eq 'Up' -and $_.IPv4Address -and $_.NetAdapter.HardwareInterface } |
  ForEach-Object {
    [PSCustomObject]@{
      InterfaceAlias = $_.InterfaceAlias
      MacAddress = $_.NetAdapter.MacAddress
      IPv4Address = $_.IPv4Address.IPAddress
      PrefixLength = [int]$_.IPv4Address.PrefixLength
      InterfaceMetric = if ($_.NetIPv4Interface) { [int]$_.NetIPv4Interface.InterfaceMetric } else { 9999 }
    }
  } |
  Sort-Object InterfaceMetric, InterfaceAlias |
  ConvertTo-Json -Compress
"""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if isinstance(payload, dict):
        items = [payload]
    else:
        items = payload

    if not items:
        raise RuntimeError("No se ha encontrado un adaptador IPv4 activo")

    selected = items[0]
    ip_address = str(selected["IPv4Address"])
    prefix_length = int(selected["PrefixLength"])
    subnet = ipaddress.ip_network(f"{ip_address}/{prefix_length}", strict=False)
    return AdapterInfo(
        hostname=socket.gethostname() or "PC Windows",
        interface_alias=str(selected["InterfaceAlias"]),
        ipv4_address=ip_address,
        prefix_length=prefix_length,
        mac_address=normalize_mac(str(selected["MacAddress"])),
        subnet_cidr=f"{subnet.network_address}/{prefix_length}",
        broadcast_address=str(subnet.broadcast_address),
    )
