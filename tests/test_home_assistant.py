"""Lifecycle contract tests with HA doubles, not a substitute for a real HA run."""
import ast
import importlib
from datetime import timedelta
from pathlib import Path
import types
import unittest
from unittest.mock import AsyncMock, Mock
from test_api import TOKEN, MAC, api
import voluptuous as vol

ROOT = Path(__file__).resolve().parents[1]


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        source = ROOT / "custom_components/pc_power_free/__init__.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        selected = [node for node in tree.body if (
            isinstance(node, ast.ImportFrom) and node.module == "__future__"
        ) or isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef))]
        self.env = dict(vars(importlib.import_module("test_integration.const")))
        self.env.update(CONF_HOST="host", CONF_MAC="mac", PLATFORMS=(),
            PCPowerRuntimeData=types.SimpleNamespace, async_get_clientsession=lambda hass: None,
            PCPowerClient=Mock(), ConfigEntryAuthFailed=RuntimeError)
        coordinator = types.SimpleNamespace(data={}, async_config_entry_first_refresh=AsyncMock())
        self.env["PCPowerCoordinator"] = Mock(return_value=coordinator)
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), "exec"), self.env)
        self.entry = types.SimpleNamespace(entry_id="test-entry", version=1,
            data={"host": "192.0.2.2", "agent_port": 58477, "api_token": TOKEN,
                "mac": MAC, "broadcast_address": "192.0.2.255", "broadcast_port": 9,
                "certificate_fingerprint": "11" * 32}, options={},
            async_on_unload=Mock(), add_update_listener=Mock())
        def update(entry, **kwargs):
            for key, value in kwargs.items():
                setattr(entry, key, value)
        self.hass = types.SimpleNamespace(data={"pc_power_free": {}},
            config_entries=types.SimpleNamespace(async_update_entry=Mock(side_effect=update),
                async_forward_entry_setups=AsyncMock(), async_reload=AsyncMock(),
                async_unload_platforms=AsyncMock(return_value=False)))

    async def test_reload_delegates_to_manager_and_does_not_run_local_setup(self):
        await self.env["async_reload_entry"](self.hass, self.entry)
        self.hass.config_entries.async_reload.assert_awaited_once_with("test-entry")
        self.hass.config_entries.async_forward_entry_setups.assert_not_awaited()

    async def test_new_discovered_address_wins_over_stale_options(self):
        self.entry.options = {"host": "192.0.2.1"}
        await self.env["async_setup_entry"](self.hass, self.entry)
        self.assertEqual(self.env["PCPowerClient"].call_args.kwargs["host"], "192.0.2.2")

    async def test_migration_keeps_entities_and_loads_without_pairing(self):
        self.assertIn("async_migrate_entry", self.env)
        self.entry.data.pop("certificate_fingerprint")
        old_data = dict(self.entry.data)
        self.assertTrue(await self.env["async_migrate_entry"](self.hass, self.entry))
        self.assertEqual(self.entry.version, 3)
        self.assertEqual(self.entry.data["mac"], old_data["mac"])
        self.assertEqual(self.entry.data["api_token"], old_data["api_token"])
        self.assertEqual(self.entry.entry_id, "test-entry")
        self.assertTrue(await self.env["async_setup_entry"](self.hass, self.entry))
        self.assertIsNone(self.env["PCPowerClient"].call_args.kwargs["certificate_fingerprint"])

    async def test_beta6_migration_keeps_effective_options_and_unique_id(self):
        self.entry.version = 2
        self.entry.unique_id = "original-machine"
        self.entry.options = {"agent_port": 58478, "host": "192.0.2.55", "scan_interval": 60}
        self.assertTrue(await self.env["async_migrate_entry"](self.hass, self.entry))
        self.assertEqual(self.entry.unique_id, "original-machine")
        self.assertEqual(self.entry.data["agent_port"], 58478)
        self.assertEqual(self.entry.data["host"], "192.0.2.55")
        self.assertEqual(self.entry.data["scan_interval"], 60)
        self.assertEqual(self.entry.options, {})

    async def test_failed_unload_preserves_runtime(self):
        self.hass.data["pc_power_free"]["test-entry"] = "runtime"
        self.assertFalse(await self.env["async_unload_entry"](self.hass, self.entry))
        self.assertEqual(self.hass.data["pc_power_free"]["test-entry"], "runtime")


class FlowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        class FlowBase:
            def __init_subclass__(cls, **kwargs):
                pass

            def async_abort(self, **kwargs):
                return {"type": "abort", **kwargs}

            def async_show_form(self, **kwargs):
                return {"type": "form", **kwargs}

            def async_create_entry(self, **kwargs):
                return {"type": "create_entry", **kwargs}

            def _async_current_entries(self):
                return self.hass.config_entries.async_entries()

            async def async_set_unique_id(self, value):
                self.unique_id = value

            def _abort_if_unique_id_configured(self, **kwargs):
                pass

        source = ROOT / "custom_components/pc_power_free/config_flow.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        selected = [node for node in tree.body if (
            isinstance(node, ast.ImportFrom) and node.module == "__future__"
        ) or isinstance(node, (ast.ClassDef, ast.FunctionDef))]
        self.env = dict(vars(importlib.import_module("test_integration.const")))
        self.env.update(vars(api))
        self.env.update(CONF_HOST="host", CONF_MAC="mac", CONF_NAME="name", vol=vol,
            cv=types.SimpleNamespace(string=str), callback=lambda fn: fn,
            ConfigEntryState=types.SimpleNamespace(LOADED="loaded"),
            config_entries=types.SimpleNamespace(ConfigFlow=FlowBase, OptionsFlow=FlowBase),
            async_get_clientsession=lambda hass: None, platform_label=lambda value: value or "PC")
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), "exec"), self.env)
        self.entry = types.SimpleNamespace(entry_id="keep-me", unique_id="test-machine",
            data={"machine_id": "test-machine", "host": "192.0.2.1", "mac": MAC,
                  "certificate_fingerprint": "11" * 32}, options={}, state="error")
        def update(entry, **kwargs):
            for key, value in kwargs.items():
                setattr(entry, key, value)
        self.hass = types.SimpleNamespace(data={}, config_entries=types.SimpleNamespace(
            async_get_entry=lambda _: self.entry, async_entries=lambda: [self.entry],
            async_update_entry=Mock(side_effect=update), async_reload=AsyncMock()))
        self.flow = self.env["PCPowerFreeConfigFlow"]()
        self.flow.hass = self.hass
        self.flow.context = {"entry_id": "keep-me"}
        self.discovery = api._normalize_discovery_payload({"machine_id": "test-machine",
            "mac_addresses": [MAC], "pairing_code_active": True},
            fallback_host="192.0.2.2", fallback_port=58477)
        self.discovery.certificate_fingerprint = "22" * 32

    async def test_unsolicited_discovery_cannot_replace_trusted_address(self):
        result = await self.flow._async_prepare_discovery(self.discovery)
        self.assertEqual(result["reason"], "invalid_response")
        self.hass.config_entries.async_update_entry.assert_not_called()

    async def test_discovery_upgrades_existing_entry_only_after_secret_proof(self):
        self.entry.data.pop("certificate_fingerprint")
        self.entry.data["api_token"] = TOKEN
        self.entry.options = {"scan_interval": 60}
        self.env["async_verify_upgrade"] = AsyncMock(return_value=False)
        result = await self.flow._async_prepare_discovery(self.discovery)
        self.assertEqual(result["reason"], "invalid_response")
        self.hass.config_entries.async_update_entry.assert_not_called()
        self.env["async_verify_upgrade"].return_value = True
        result = await self.flow._async_prepare_discovery(self.discovery)
        self.assertEqual(result["reason"], "already_configured")
        self.assertEqual(self.entry.entry_id, "keep-me")
        self.assertEqual(self.entry.unique_id, "test-machine")
        self.assertEqual(self.entry.data["api_token"], TOKEN)
        self.assertEqual(self.entry.data["certificate_fingerprint"], "22" * 32)
        self.assertEqual(self.entry.data["host"], "192.0.2.2")
        self.assertEqual(self.entry.data["scan_interval"], 60)
        self.assertEqual(self.entry.options, {})

    async def test_reauth_repairs_existing_entry_without_losing_entities(self):
        result = await self.flow.async_step_reauth(self.entry.data)
        self.assertEqual(result["step_id"], "manual")
        self.assertIsNone(await self.flow._async_prepare_discovery(self.discovery, allow_repair=True))
        self.env["async_exchange_pairing_code"] = AsyncMock(return_value=api.PCPowerPairingResult(
            discovery=self.discovery, api_token=TOKEN, broadcast_port=9))
        result = await self.flow.async_step_pair({"name": "PC", "pairing_code": "123456", "scan_interval": 30})
        self.assertEqual(result["reason"], "repair_successful")
        self.assertEqual(self.entry.entry_id, "keep-me")
        self.assertEqual(self.entry.data["certificate_fingerprint"], "22" * 32)
        self.assertEqual(self.entry.data["host"], "192.0.2.2")
        self.hass.config_entries.async_reload.assert_awaited_once_with("keep-me")

    async def test_reauth_does_not_pair_a_different_machine(self):
        await self.flow.async_step_reauth(self.entry.data)
        self.discovery.machine_id = "somebody-else"
        result = await self.flow._async_prepare_discovery(self.discovery, allow_repair=True)
        self.assertEqual(result["reason"], "invalid_response")

    async def test_options_do_not_create_stale_connection_overrides(self):
        flow = self.env["PCPowerOptionsFlow"](self.entry)
        flow.hass = self.hass
        result = await flow.async_step_init({"host": "192.0.2.3", "scan_interval": 20})
        self.assertEqual(result["data"], {})
        self.assertEqual(self.entry.data["host"], "192.0.2.3")


class CoordinatorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        class CoordinatorBase:
            def __class_getitem__(cls, _):
                return cls

            def __init__(self, hass, **kwargs):
                self.hass = hass

        source = ROOT / "custom_components/pc_power_free/coordinator.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        nodes = [node for node in tree.body if isinstance(node, ast.ClassDef) or (
            isinstance(node, ast.ImportFrom) and node.module == "__future__")]
        env = {**vars(importlib.import_module("test_integration.const")), **vars(api),
               "DataUpdateCoordinator": CoordinatorBase, "timedelta": timedelta,
               "_LOGGER": Mock(), "CONF_HOST": "host", "ConfigEntryAuthFailed": RuntimeError,
               "UpdateFailed": RuntimeError}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), env)
        self.entry = types.SimpleNamespace(data={"host": "192.0.2.1", "api_token": TOKEN,
            "machine_id": "test-machine", "name": "My PC"}, options={}, entry_id="keep-me")
        def update(entry, **kwargs):
            for key, value in kwargs.items():
                setattr(entry, key, value)
        self.hass = types.SimpleNamespace(config_entries=types.SimpleNamespace(
            async_update_entry=Mock(side_effect=update)))
        self.client = types.SimpleNamespace(certificate_fingerprint=None, host="192.0.2.2",
            async_get_status=AsyncMock(return_value={"online": False, "reachable": False,
                                                   "upgrade_pending": True}))
        self.coordinator = env["PCPowerCoordinator"](self.hass, self.entry, self.client)

    async def test_pending_upgrade_retries_and_persists_trust_once_without_new_entry(self):
        status = await self.coordinator._async_update_data()
        self.assertTrue(status["upgrade_pending"])
        self.hass.config_entries.async_update_entry.assert_not_called()
        self.client.certificate_fingerprint = "11" * 32
        self.client.async_get_status.return_value = {"online": True, "reachable": True}
        await self.coordinator._async_update_data()
        self.assertEqual(self.entry.data["certificate_fingerprint"], "11" * 32)
        self.assertEqual(self.entry.data["host"], "192.0.2.2")
        self.assertEqual(self.entry.entry_id, "keep-me")
        self.assertEqual(self.entry.data["api_token"], TOKEN)
        self.assertEqual(self.entry.data["name"], "My PC")
        await self.coordinator._async_update_data()
        self.hass.config_entries.async_update_entry.assert_called_once()

    async def test_preexisting_pin_is_never_overwritten_by_upgrade(self):
        self.entry.data["certificate_fingerprint"] = "22" * 32
        self.client.certificate_fingerprint = "11" * 32
        self.client.async_get_status.return_value = {"online": True, "reachable": True}
        await self.coordinator._async_update_data()
        self.hass.config_entries.async_update_entry.assert_not_called()
