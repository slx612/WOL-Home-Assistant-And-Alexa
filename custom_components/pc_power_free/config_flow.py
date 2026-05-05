"""Config flow for PC Power Free."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .api import (
    PCPowerDiscoveryError,
    PCPowerDiscoveryInfo,
    PCPowerPairingError,
    async_exchange_pairing_code,
    async_fetch_discovery_info,
    normalize_mac,
    parse_discovery_subnets,
)
from .const import (
    CONF_AGENT_PORT,
    CONF_API_TOKEN,
    CONF_BROADCAST_ADDRESS,
    CONF_BROADCAST_PORT,
    CONF_CAPABILITIES,
    CONF_DISCOVERY_SUBNETS,
    CONF_MACHINE_ID,
    CONF_PLATFORM,
    CONF_SCAN_INTERVAL,
    DEFAULT_AGENT_PORT,
    DEFAULT_BROADCAST_ADDRESS,
    DEFAULT_BROADCAST_PORT,
    DEFAULT_DISCOVERY_SUBNETS,
    DEFAULT_SCAN_INTERVAL,
    DISCOVERY_CACHE,
    DOMAIN,
    MANUAL_DISCOVERY_OPTION,
)
from .platforms import platform_label


def _manual_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the manual discovery schema."""
    data = defaults or {}

    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=data.get(CONF_HOST, "")): cv.string,
            vol.Required(
                CONF_AGENT_PORT,
                default=data.get(CONF_AGENT_PORT, DEFAULT_AGENT_PORT),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
        }
    )


def _discovery_choice_label(discovery: PCPowerDiscoveryInfo) -> str:
    """Return the label shown for one discovered device."""
    return f"{discovery.name} ({discovery.host}, {platform_label(discovery.platform)})"


def _pair_schema(discovery: PCPowerDiscoveryInfo, defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the pairing schema for a discovered PC."""
    data = defaults or {}

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data.get(CONF_NAME, discovery.name)): cv.string,
            vol.Required("pairing_code", default=data.get("pairing_code", "")): cv.string,
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
        }
    )


def _options_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the options schema."""
    data = defaults or {}

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=data.get(CONF_NAME, "PC Power Device")): cv.string,
            vol.Required(CONF_HOST, default=data.get(CONF_HOST, "")): cv.string,
            vol.Required(
                CONF_AGENT_PORT,
                default=data.get(CONF_AGENT_PORT, DEFAULT_AGENT_PORT),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Optional(
                CONF_DISCOVERY_SUBNETS,
                default=data.get(CONF_DISCOVERY_SUBNETS, DEFAULT_DISCOVERY_SUBNETS),
            ): cv.string,
            vol.Required(
                CONF_BROADCAST_ADDRESS,
                default=data.get(CONF_BROADCAST_ADDRESS, DEFAULT_BROADCAST_ADDRESS),
            ): cv.string,
            vol.Required(
                CONF_BROADCAST_PORT,
                default=data.get(CONF_BROADCAST_PORT, DEFAULT_BROADCAST_PORT),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
        }
    )


def _extract_zeroconf_host(discovery_info: ZeroconfServiceInfo) -> str:
    """Return the discovered IPv4 address from a zeroconf payload."""
    host = getattr(discovery_info, "host", None)
    if host:
        return str(host)

    ip_address = getattr(discovery_info, "ip_address", None)
    if ip_address:
        return str(ip_address)

    ip_addresses = getattr(discovery_info, "ip_addresses", None)
    if ip_addresses:
        return str(ip_addresses[0])

    return ""


class PCPowerFreeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PC Power Free."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: PCPowerDiscoveryInfo | None = None
        self._repair_entry: ConfigEntry | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        discovered_items = self._discovered_items
        if not discovered_items:
            return await self.async_step_manual()

        if user_input is not None:
            selected_machine_id = user_input["discovered_device"]
            if selected_machine_id == MANUAL_DISCOVERY_OPTION:
                return await self.async_step_manual()

            discovery = discovered_items.get(selected_machine_id)
            if discovery is not None:
                result = await self._async_prepare_discovery(discovery, allow_repair=True)
                if result is not None:
                    return result
                self.context["title_placeholders"] = {"name": discovery.name}
                return await self.async_step_pair()

        options = {
            machine_id: _discovery_choice_label(discovery)
            for machine_id, discovery in discovered_items.items()
        }
        options[MANUAL_DISCOVERY_OPTION] = "Configurar por IP manualmente"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("discovered_device"): vol.In(options)}
            ),
        )

    async def async_step_manual(self, user_input: dict[str, Any] | None = None):
        """Handle manual discovery by host/IP."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                discovery = await async_fetch_discovery_info(
                    async_get_clientsession(self.hass),
                    host=user_input[CONF_HOST].strip(),
                    agent_port=user_input[CONF_AGENT_PORT],
                )
            except PCPowerDiscoveryError as err:
                errors["base"] = err.reason
            else:
                if not discovery.pairing_code_active:
                    errors["base"] = "no_pairing_code"
                else:
                    result = await self._async_prepare_discovery(discovery, allow_repair=True)
                    if result is not None:
                        return result
                    self.context["title_placeholders"] = {"name": discovery.name}
                    return await self.async_step_pair()

        return self.async_show_form(
            step_id="manual",
            data_schema=_manual_schema(user_input),
            errors=errors,
        )

    async def async_step_pair(self, user_input: dict[str, Any] | None = None):
        """Handle pairing with a discovered PC."""
        if self._discovery_info is None:
            return await self.async_step_user()

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                pairing_result = await async_exchange_pairing_code(
                    async_get_clientsession(self.hass),
                    host=self._discovery_info.host,
                    agent_port=self._discovery_info.agent_port,
                    pairing_code=user_input["pairing_code"],
                )
            except PCPowerPairingError as err:
                errors["base"] = err.reason
            else:
                discovery = pairing_result.discovery

                entry_data = {
                    CONF_NAME: user_input[CONF_NAME].strip() or discovery.name,
                    CONF_HOST: discovery.host,
                    CONF_MAC: discovery.primary_mac,
                    CONF_API_TOKEN: pairing_result.api_token,
                    CONF_AGENT_PORT: discovery.agent_port,
                    CONF_BROADCAST_ADDRESS: discovery.broadcast_address,
                    CONF_BROADCAST_PORT: pairing_result.broadcast_port,
                    CONF_DISCOVERY_SUBNETS: discovery.discovery_subnets_text,
                    CONF_MACHINE_ID: discovery.machine_id,
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                }
                if discovery.capabilities:
                    entry_data[CONF_CAPABILITIES] = list(discovery.capabilities)
                if discovery.platform:
                    entry_data[CONF_PLATFORM] = discovery.platform

                if self._repair_entry is not None:
                    repair_entry = self._repair_entry
                    self.hass.config_entries.async_update_entry(
                        repair_entry,
                        data={**repair_entry.data, **entry_data},
                        title=entry_data[CONF_NAME],
                        unique_id=discovery.machine_id,
                    )
                    return self.async_abort(reason="repair_successful")

                result = await self._async_prepare_discovery(discovery, allow_repair=True)
                if result is not None:
                    return result

                await self.async_set_unique_id(discovery.machine_id)
                self._abort_if_unique_id_configured(
                    updates=self._build_discovery_updates(discovery)
                )
                return self.async_create_entry(title=entry_data[CONF_NAME], data=entry_data)

        return self.async_show_form(
            step_id="pair",
            data_schema=_pair_schema(self._discovery_info, user_input),
            description_placeholders={
                "name": self._discovery_info.name,
                "host": self._discovery_info.host,
                "platform": platform_label(self._discovery_info.platform),
            },
            errors=errors,
        )

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo):
        """Handle zeroconf discovery."""
        host = _extract_zeroconf_host(discovery_info)
        if not host:
            return self.async_abort(reason="cannot_connect")

        try:
            discovery = await async_fetch_discovery_info(
                async_get_clientsession(self.hass),
                host=host,
                agent_port=int(getattr(discovery_info, "port", DEFAULT_AGENT_PORT)),
            )
        except PCPowerDiscoveryError as err:
            return self.async_abort(reason=err.reason)

        if not discovery.pairing_code_active:
            await self._async_prepare_discovery(discovery)
            return self.async_abort(reason="no_pairing_code")

        result = await self._async_prepare_discovery(discovery, allow_repair=True)
        if result is not None:
            return result

        self.context["title_placeholders"] = {"name": discovery.name}
        return await self.async_step_pair()

    @property
    def _discovered_items(self) -> dict[str, PCPowerDiscoveryInfo]:
        """Return the cached discovered devices."""
        domain_data = self.hass.data.setdefault(DOMAIN, {})
        return domain_data.setdefault(DISCOVERY_CACHE, {})

    async def _async_prepare_discovery(
        self,
        discovery: PCPowerDiscoveryInfo,
        *,
        allow_repair: bool = False,
    ):
        """Store discovery data and abort if the device already exists."""
        self._discovered_items[discovery.machine_id] = discovery
        self._discovery_info = discovery
        self._repair_entry = None

        if existing_entry := self._find_existing_entry_for_discovery(discovery):
            if allow_repair and discovery.pairing_code_active:
                self._repair_entry = existing_entry
                return None
            data = {**existing_entry.data, **self._build_discovery_updates(discovery)}
            self.hass.config_entries.async_update_entry(
                existing_entry,
                data=data,
                unique_id=discovery.machine_id,
            )
            return self.async_abort(reason="already_configured")

        await self.async_set_unique_id(discovery.machine_id)
        self._abort_if_unique_id_configured(updates=self._build_discovery_updates(discovery))
        return None

    def _find_existing_entry_for_discovery(
        self,
        discovery: PCPowerDiscoveryInfo,
    ) -> ConfigEntry | None:
        """Find an existing entry by machine ID first, then by MAC."""
        for entry in self._async_current_entries():
            entry_machine_id = str(
                entry.data.get(CONF_MACHINE_ID) or entry.unique_id or ""
            ).strip().lower()
            if entry_machine_id and entry_machine_id == discovery.machine_id:
                return entry

        return self._find_existing_entry_by_mac(discovery.mac_addresses)

    def _build_discovery_updates(self, discovery: PCPowerDiscoveryInfo) -> dict[str, Any]:
        """Build the config entry updates derived from discovery."""
        updates: dict[str, Any] = {
            CONF_HOST: discovery.host,
            CONF_AGENT_PORT: discovery.agent_port,
            CONF_MAC: discovery.primary_mac,
            CONF_MACHINE_ID: discovery.machine_id,
        }
        if discovery.capabilities:
            updates[CONF_CAPABILITIES] = list(discovery.capabilities)
        if discovery.platform:
            updates[CONF_PLATFORM] = discovery.platform
        if discovery.broadcast_address:
            updates[CONF_BROADCAST_ADDRESS] = discovery.broadcast_address
        if discovery.discovery_subnets:
            updates[CONF_DISCOVERY_SUBNETS] = discovery.discovery_subnets_text
        return updates

    def _find_existing_entry_by_mac(
        self,
        mac_addresses: tuple[str, ...],
    ) -> ConfigEntry | None:
        """Find an existing entry created by the previous MAC-based flow."""
        normalized_candidates = {
            normalize_mac(mac_address)
            for mac_address in mac_addresses
        }

        for entry in self._async_current_entries():
            entry_machine_id = entry.data.get(CONF_MACHINE_ID) or entry.unique_id
            if entry_machine_id in normalized_candidates:
                continue

            entry_mac = entry.data.get(CONF_MAC)
            if not entry_mac:
                continue
            try:
                normalized_entry_mac = normalize_mac(entry_mac)
            except Exception:
                continue
            if normalized_entry_mac in normalized_candidates:
                return entry

        return None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return PCPowerOptionsFlow(config_entry)


class PCPowerOptionsFlow(config_entries.OptionsFlow):
    """Handle the options flow."""

    def __init__(self, config_entry) -> None:
        """Store the config entry."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                parse_discovery_subnets(user_input.get(CONF_DISCOVERY_SUBNETS, ""))
            except PCPowerDiscoveryError:
                errors["base"] = "invalid_input"
            except Exception:
                errors["base"] = "invalid_input"
            else:
                return self.async_create_entry(title="", data=user_input)

        current_values = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(current_values),
            errors=errors,
        )
