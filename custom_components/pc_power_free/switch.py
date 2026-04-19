"""Switch platform for PC Power Free."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PCPowerRuntimeData
from .const import (
    CONF_MACHINE_ID,
    DOMAIN,
    STATUS_AGENT_VERSION,
    STATUS_HOST,
    STATUS_HOSTNAME,
    STATUS_LAST_COMMAND,
    STATUS_MAC_ADDRESSES,
    STATUS_ONLINE,
    STATUS_REACHABLE,
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

    @property
    def is_on(self) -> bool:
        """Return whether the PC is on."""
        data = self.coordinator.data or {}
        return bool(data.get(STATUS_ONLINE, False))

    @property
    def extra_state_attributes(self) -> dict[str, str | bool | None]:
        """Expose diagnostic attributes."""
        data = self.coordinator.data or {}
        return {
            STATUS_HOST: data.get(STATUS_HOST, self._client.host or None),
            STATUS_HOSTNAME: data.get(STATUS_HOSTNAME),
            STATUS_AGENT_VERSION: data.get(STATUS_AGENT_VERSION),
            STATUS_REACHABLE: data.get(STATUS_REACHABLE, False),
            STATUS_LAST_COMMAND: data.get(STATUS_LAST_COMMAND),
            STATUS_MAC_ADDRESSES: ", ".join(data.get(STATUS_MAC_ADDRESSES, [])),
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
