"""Button platform for PC Power Free."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PCPowerRuntimeData
from .const import CONF_CAPABILITIES, DOMAIN, STATUS_CAPABILITIES
from .device_info import build_device_info
from .platforms import normalize_agent_capabilities


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities for the entry."""
    runtime_data: PCPowerRuntimeData = hass.data[DOMAIN][entry.entry_id]
    capabilities = normalize_agent_capabilities(
        runtime_data.coordinator.data.get(STATUS_CAPABILITIES)
        if runtime_data.coordinator.data
        else entry.data.get(CONF_CAPABILITIES)
    )
    if capabilities and "restart" not in capabilities:
        return
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
        self._attr_device_info = build_device_info(entry)

    async def async_press(self) -> None:
        """Restart the PC through the local agent."""
        await self._client.async_restart()
