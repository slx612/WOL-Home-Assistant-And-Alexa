"""Device metadata helpers for PC Power Free entities."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo

from .const import CONF_MACHINE_ID, CONF_PLATFORM, DOMAIN
from .platforms import normalize_agent_platform, platform_model


def build_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Build consistent device info for all entities of one entry."""
    device_name = entry.options.get(CONF_NAME, entry.data.get(CONF_NAME, entry.title))
    device_identifier = entry.data.get(CONF_MACHINE_ID, entry.unique_id or entry.entry_id)
    connections = set()
    if mac_address := entry.data.get(CONF_MAC):
        connections.add((CONNECTION_NETWORK_MAC, mac_address))

    platform = normalize_agent_platform(
        entry.options.get(CONF_PLATFORM, entry.data.get(CONF_PLATFORM))
    )
    return DeviceInfo(
        identifiers={(DOMAIN, device_identifier)},
        connections=connections,
        name=device_name,
        manufacturer="PC Power Free",
        model=platform_model(platform),
    )
