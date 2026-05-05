"""The PC Power Free integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .api import PCPowerClient
from .const import (
    CONF_AGENT_PORT,
    CONF_API_TOKEN,
    CONF_BROADCAST_ADDRESS,
    CONF_BROADCAST_PORT,
    CONF_CAPABILITIES,
    CONF_DISCOVERY_SUBNETS,
    CONF_MACHINE_ID,
    CONF_PLATFORM,
    DISCOVERY_CACHE,
    DOMAIN,
)
from .coordinator import PCPowerCoordinator

PLATFORMS: tuple[Platform, ...] = (Platform.SWITCH, Platform.BUTTON, Platform.SENSOR)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


@dataclass(slots=True)
class PCPowerRuntimeData:
    """Runtime objects stored for each config entry."""

    client: PCPowerClient
    coordinator: PCPowerCoordinator


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the domain."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DISCOVERY_CACHE, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PC Power Free from a config entry."""
    session = async_get_clientsession(hass)
    config = {**entry.data, **entry.options}

    client = PCPowerClient(
        session,
        host=config[CONF_HOST],
        agent_port=config[CONF_AGENT_PORT],
        api_token=config[CONF_API_TOKEN],
        mac_address=config[CONF_MAC],
        broadcast_address=config[CONF_BROADCAST_ADDRESS],
        broadcast_port=config[CONF_BROADCAST_PORT],
        discovery_subnets=config.get(CONF_DISCOVERY_SUBNETS, ""),
        machine_id=config.get(CONF_MACHINE_ID),
    )

    coordinator = PCPowerCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    metadata_changed = _sync_entry_metadata_from_status(hass, entry, coordinator.data)

    hass.data[DOMAIN][entry.entry_id] = PCPowerRuntimeData(client=client, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    if metadata_changed:
        hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def _sync_entry_metadata_from_status(
    hass: HomeAssistant,
    entry: ConfigEntry,
    status_data: dict[str, object] | None,
) -> bool:
    """Persist platform metadata learned from the live agent status."""
    if not status_data:
        return False

    updates = dict(entry.data)
    changed = False

    platform = status_data.get(CONF_PLATFORM)
    if isinstance(platform, str) and platform and updates.get(CONF_PLATFORM) != platform:
        updates[CONF_PLATFORM] = platform
        changed = True

    capabilities = status_data.get(CONF_CAPABILITIES)
    if isinstance(capabilities, tuple):
        capabilities = list(capabilities)
    if isinstance(capabilities, list) and capabilities and updates.get(CONF_CAPABILITIES) != capabilities:
        updates[CONF_CAPABILITIES] = capabilities
        changed = True

    if changed:
        hass.config_entries.async_update_entry(entry, data=updates)
    return changed
