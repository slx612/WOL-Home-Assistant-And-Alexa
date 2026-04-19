"""Button platform for PC Power Free."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PCPowerRuntimeData
from .const import CONF_MACHINE_ID, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities for the entry."""
    runtime_data: PCPowerRuntimeData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PCPowerRestartButton(entry, runtime_data)])


class PCPowerRestartButton(CoordinatorEntity, ButtonEntity):
    """Button entity that restarts the PC."""

    _attr_has_entity_name = True
    _attr_name = "Restart"
    _attr_icon = "mdi:restart"

    def __init__(self, entry: ConfigEntry, runtime_data: PCPowerRuntimeData) -> None:
        """Initialize the restart button."""
        super().__init__(runtime_data.coordinator)
        self._client = runtime_data.client
        self._attr_unique_id = f"{entry.entry_id}_restart"
        device_name = entry.options.get(CONF_NAME, entry.data.get(CONF_NAME, entry.title))
        device_identifier = entry.data.get(CONF_MACHINE_ID, entry.unique_id or entry.entry_id)
        connections = set()
        if mac_address := entry.data.get(CONF_MAC):
            connections.add((CONNECTION_NETWORK_MAC, mac_address))
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_identifier)},
            connections=connections,
            name=device_name,
            manufacturer="PC Power Free",
            model="Windows PC",
        )

    async def async_press(self) -> None:
        """Restart the PC through the local agent."""
        await self._client.async_restart()
