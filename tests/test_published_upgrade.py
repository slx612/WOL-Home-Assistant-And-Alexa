"""Exercise BOTH upgrade orders against the actual published beta.6 Python code.

Requires the local v0.2.0-beta.6 Git tag. No old installer, LAN, or OS power action
is executed. Old/new agents run on loopback with FakePlatform and temporary data.
"""
import asyncio
import importlib.util
import logging
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import aiohttp
from test_api import api, client
from test_runtime import core, FakePlatform, TOKEN
from agent_core.tls import create_server_context

ROOT = Path(__file__).resolve().parents[1]


def published_module(name, source_path):
    repository = ROOT if (ROOT / ".git/HEAD").exists() else ROOT / ".repo_push_beta6"
    result = subprocess.run(["git", "-C", str(repository), "show",
        f"v0.2.0-beta.6:{source_path}"], capture_output=True, timeout=20)
    if result.returncode:
        raise unittest.SkipTest("Fetch Git tag v0.2.0-beta.6 to test the published code")
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader=None))
    sys.modules[name] = module
    exec(compile(result.stdout, f"v0.2.0-beta.6/{source_path}", "exec"), module.__dict__)
    return module


class PublishedUpgradeTests(unittest.IsolatedAsyncioTestCase):
    # Match HA's selector loop, including intentional HTTP-to-TLS disconnects.
    loop_factory = asyncio.SelectorEventLoop

    @classmethod
    def setUpClass(cls):
        cls.old_core = published_module("published_beta6_core", "agent_core/common.py")
        cls.old_api = published_module("test_integration.published_beta6_api",
                                       "custom_components/pc_power_free/api.py")

    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.config_path = self.directory / "config.json"
        shutil.copyfile(ROOT / "tests/fixtures/beta6-config.json", self.config_path)
        self.original_config = self.config_path.read_bytes()
        self.session = aiohttp.ClientSession()
        self.server = None
        self.platform = FakePlatform()

    async def stop_server(self):
        if self.server is not None:
            await asyncio.to_thread(self.server.shutdown)
            self.server.server_close()
            self.thread.join(2)
            self.server = None

    async def start_server(self, *, upgraded, port=0):
        module = core if upgraded else self.old_core
        config, _ = module.load_config(self.config_path)
        settings = {}
        if upgraded:
            settings["tls_context"] = await asyncio.to_thread(create_server_context, self.directory)
        logger = logging.getLogger("published-upgrade-test")
        logger.addHandler(logging.NullHandler())
        logger.propagate = False
        self.server = module.PCPowerHTTPServer(("127.0.0.1", port), module.PCPowerRequestHandler,
            config, self.config_path, logger, self.platform, **settings)
        self.thread = threading.Thread(target=self.server.serve_forever,
            kwargs={"poll_interval": .01}, daemon=True)
        self.thread.start()
        return self.server.server_address[1]

    def old_client(self, port):
        return self.old_api.PCPowerClient(self.session, host="127.0.0.1", agent_port=port,
            api_token=TOKEN, mac_address="02:00:00:00:00:01", machine_id="test-machine",
            broadcast_address="127.0.0.1", broadcast_port=9,
            discovery_subnets="127.0.0.1/32", timeout=1)

    async def asyncTearDown(self):
        await self.session.close()
        await self.stop_server()
        self.temp.cleanup()

    async def test_ha_first_then_windows_recovers_on_next_poll_without_pairing(self):
        port = await self.start_server(upgraded=False)
        self.assertTrue((await self.old_client(port).async_get_status())["online"])
        upgraded_ha = client(self.session, agent_port=port, timeout=1)
        with patch.object(self.old_core.PCPowerRequestHandler, "_authorize") as authorize:
            self.assertTrue((await upgraded_ha.async_get_status())["upgrade_pending"])
        authorize.assert_not_called()
        await self.stop_server()
        await self.start_server(upgraded=True, port=port)
        self.assertTrue((await upgraded_ha.async_get_status())["online"])
        self.assertEqual(self.config_path.read_bytes(), self.original_config)
        self.assertEqual(self.platform.commands, [])

    async def test_windows_first_then_ha_recovers_using_the_published_token(self):
        port = await self.start_server(upgraded=False)
        old_ha = self.old_client(port)
        self.assertTrue((await old_ha.async_get_status())["online"])
        await self.stop_server()
        await self.start_server(upgraded=True, port=port)
        self.assertFalse((await old_ha.async_get_status())["online"])
        upgraded_ha = client(self.session, agent_port=port)
        self.assertTrue((await upgraded_ha.async_get_status())["online"])
        self.assertEqual(upgraded_ha._api_token, TOKEN)
        self.assertEqual(self.config_path.read_bytes(), self.original_config)
        self.assertEqual(self.platform.commands, [])

    async def test_multiple_previously_paired_clients_can_upgrade_independently(self):
        port = await self.start_server(upgraded=True)
        first, second = client(self.session, agent_port=port), client(self.session, agent_port=port)
        results = await asyncio.gather(first.async_get_status(), second.async_get_status())
        self.assertTrue(all(result["online"] for result in results))
        self.assertEqual(first.certificate_fingerprint, second.certificate_fingerprint)
        self.assertEqual(self.config_path.read_bytes(), self.original_config)
