"""Switch platform for PC Power Free."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PCPowerRuntimeData
from .device_info import build_device_info
from .const import (
    DOMAIN,
    STATUS_AGENT_VERSION,
    STATUS_BOOTED_AT,
    STATUS_CAPABILITIES,
    STATUS_COMMAND_GUARD_ACTIVE,
    STATUS_COMMAND_GUARD_MODE,
    STATUS_COMMAND_GUARD_UNTIL_TS,
    STATUS_HOST,
    STATUS_HOSTNAME,
    STATUS_LAST_COMMAND,
    STATUS_LAST_COMMAND_AT,
    STATUS_MAC_ADDRESSES,
    STATUS_ONLINE,
    STATUS_PLATFORM,
    STATUS_REACHABLE,
    STATUS_UPTIME_SECONDS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch from a config entry."""
    runtime_data: PCPowerRuntimeData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PCPowerSwitch(entry, runtime_data)])


class PCPowerSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the PC power switch."""

    _attr_has_entity_name = True
    _attr_name = "Power"
    _attr_icon = "mdi:desktop-tower-monitor"

    def __init__(self, entry: ConfigEntry, runtime_data: PCPowerRuntimeData) -> None:
        """Initialize the entity."""
        super().__init__(runtime_data.coordinator)
        self._entry = entry
        self._client = runtime_data.client
        self._attr_unique_id = f"{entry.entry_id}_power"
        self._attr_device_info = build_device_info(entry)

    @property
    def is_on(self) -> bool:
        """Return whether the PC is on."""
        data = self.coordinator.data or {}
        return bool(data.get(STATUS_ONLINE, False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose diagnostic attributes."""
        data = self.coordinator.data or {}
        return {
            STATUS_HOST: data.get(STATUS_HOST, self._client.host or None),
            STATUS_HOSTNAME: data.get(STATUS_HOSTNAME),
            STATUS_AGENT_VERSION: data.get(STATUS_AGENT_VERSION),
            STATUS_BOOTED_AT: data.get(STATUS_BOOTED_AT),
            STATUS_CAPABILITIES: ", ".join(data.get(STATUS_CAPABILITIES, [])),
            STATUS_COMMAND_GUARD_ACTIVE: data.get(STATUS_COMMAND_GUARD_ACTIVE, False),
            STATUS_COMMAND_GUARD_MODE: data.get(STATUS_COMMAND_GUARD_MODE),
            STATUS_COMMAND_GUARD_UNTIL_TS: data.get(STATUS_COMMAND_GUARD_UNTIL_TS),
            STATUS_REACHABLE: data.get(STATUS_REACHABLE, False),
            STATUS_LAST_COMMAND: data.get(STATUS_LAST_COMMAND),
            STATUS_LAST_COMMAND_AT: data.get(STATUS_LAST_COMMAND_AT),
            STATUS_MAC_ADDRESSES: ", ".join(data.get(STATUS_MAC_ADDRESSES, [])),
            STATUS_PLATFORM: data.get(STATUS_PLATFORM),
            STATUS_UPTIME_SECONDS: data.get(STATUS_UPTIME_SECONDS),
        }

    async def async_turn_on(self, **kwargs) -> None:
        """Wake the PC using Wake-on-LAN."""
        await self._client.async_wake()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Shut the PC down through the local agent."""
        await self._client.async_shutdown()
        data = self.coordinator.data or {}
        self.coordinator.async_set_updated_data(
            {**data, STATUS_ONLINE: False, STATUS_LAST_COMMAND: "shutdown"}
        )
