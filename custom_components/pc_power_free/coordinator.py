"""Data coordinator for PC Power Free."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PCPowerAuthError, PCPowerClient, PCPowerCommandError
from .const import CONF_MACHINE_ID, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class PCPowerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate the local state updates for the PC."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: PCPowerClient) -> None:
        """Initialize the coordinator."""
        self._client = client

        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{entry.data.get(CONF_MACHINE_ID, entry.data[CONF_HOST])}",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest device data."""
        try:
            return await self._client.async_get_status()
        except PCPowerAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except PCPowerCommandError as err:
            raise UpdateFailed(str(err)) from err
