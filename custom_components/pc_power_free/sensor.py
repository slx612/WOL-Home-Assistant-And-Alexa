"""Sensor platform for PC Power Free."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import PCPowerRuntimeData
from .const import (
    CONF_MACHINE_ID,
    DOMAIN,
    STATUS_BOOTED_AT,
    STATUS_ONLINE,
    STATUS_REACHABLE,
    STATUS_UPTIME_SECONDS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities for the entry."""
    runtime_data: PCPowerRuntimeData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PCPowerUptimeSensor(entry, runtime_data),
            PCPowerBootTimeSensor(entry, runtime_data),
        ]
    )


class PCPowerSensorEntity(CoordinatorEntity, SensorEntity):
    """Base class for PC Power Free sensors."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: ConfigEntry,
        runtime_data: PCPowerRuntimeData,
        *,
        unique_suffix: str,
    ) -> None:
        """Initialize the shared sensor state."""
        super().__init__(runtime_data.coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
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
    def available(self) -> bool:
        """Return whether the PC is reachable and online."""
        data = self.coordinator.data or {}
        return (
            super().available
            and bool(data.get(STATUS_REACHABLE, False))
            and bool(data.get(STATUS_ONLINE, False))
        )


class PCPowerUptimeSensor(PCPowerSensorEntity):
    """Human-readable uptime sensor."""

    _attr_name = "Uptime"
    _attr_icon = "mdi:timer-outline"

    def __init__(self, entry: ConfigEntry, runtime_data: PCPowerRuntimeData) -> None:
        """Initialize the uptime sensor."""
        super().__init__(entry, runtime_data, unique_suffix="uptime")

    @property
    def native_value(self) -> str | None:
        """Return the formatted uptime."""
        data = self.coordinator.data or {}
        raw_value = data.get(STATUS_UPTIME_SECONDS)
        if raw_value in (None, ""):
            return None

        try:
            uptime_seconds = max(0, int(float(raw_value)))
        except (TypeError, ValueError):
            return None

        return _format_uptime(uptime_seconds)


class PCPowerBootTimeSensor(PCPowerSensorEntity):
    """Boot timestamp sensor."""

    _attr_name = "Boot time"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-start"

    def __init__(self, entry: ConfigEntry, runtime_data: PCPowerRuntimeData) -> None:
        """Initialize the boot time sensor."""
        super().__init__(entry, runtime_data, unique_suffix="boot_time")

    @property
    def native_value(self):
        """Return the last boot time in UTC."""
        data = self.coordinator.data or {}
        raw_value = data.get(STATUS_BOOTED_AT)
        if raw_value in (None, ""):
            return None

        try:
            return dt_util.utc_from_timestamp(float(raw_value))
        except (TypeError, ValueError, OverflowError):
            return None


def _format_uptime(total_seconds: int) -> str:
    """Return a compact uptime string."""
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m"
    return f"{seconds}s"
