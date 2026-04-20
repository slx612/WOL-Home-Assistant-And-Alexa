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
    CONF_DISCOVERY_SUBNETS,
    CONF_MACHINE_ID,
    DISCOVERY_CACHE,
    DOMAIN,
)
from .coordinator import PCPowerCoordinator

PLATFORMS: tuple[Platform, ...] = (Platform.SWITCH, Platform.BUTTON)
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

    hass.data[DOMAIN][entry.entry_id] = PCPowerRuntimeData(client=client, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
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
