"""Integration API tested against the real agent on loopback, never the LAN."""
import asyncio
import hashlib
import hmac
import importlib
import logging
from pathlib import Path
import ssl
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
from test_runtime import core, config_in, FakePlatform, TOKEN, MAC

package = types.ModuleType("test_integration")
package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components/pc_power_free")]
sys.modules[package.__name__] = package
api = importlib.import_module("test_integration.api")


def client(session, **overrides):
    settings = dict(host="127.0.0.1", agent_port=58477, api_token=TOKEN,
        mac_address=MAC, machine_id="test-machine", broadcast_address="127.0.0.1",
        broadcast_port=9, discovery_subnets="127.0.0.1/32")
    settings.update(overrides)
    return api.PCPowerClient(session, **settings)


class ApiTests(unittest.IsolatedAsyncioTestCase):
    def test_wake_packet_has_standard_contents(self):
        with patch.object(api.socket, "socket") as factory:
            api.send_magic_packet(MAC, "192.0.2.255", 9)
        packet, address = factory.return_value.__enter__.return_value.sendto.call_args.args
        self.assertEqual(packet, b"\xff" * 6 + bytes.fromhex(MAC.replace(":", "")) * 16)
        self.assertEqual(address, ("192.0.2.255", 9))

    async def test_pending_upgrade_does_not_send_credentials_or_request_pairing(self):
        session = Mock()
        instance = client(session)
        with patch.object(api, "async_fetch_discovery_info", side_effect=api.PCPowerDiscoveryError("cannot_connect")):
            status = await instance.async_get_status()
        self.assertFalse(status["online"])
        self.assertTrue(status["upgrade_pending"])
        session.get.assert_not_called()
        session.post.assert_not_called()

    async def test_scan_has_fixed_workers_and_address_budget(self):
        asyncio.get_running_loop().set_debug(False)
        instance = client(None, discovery_subnets="192.0.0.0/16")
        probe = AsyncMock(return_value=None)
        instance._async_probe_candidate = probe
        create_task = asyncio.create_task
        with patch.object(asyncio, "create_task", wraps=create_task) as tasks:
            await instance.async_discover_host(force=True)
        self.assertLessEqual(tasks.call_count, 32)
        self.assertLessEqual(probe.await_count, 4096)

    async def test_agent_defaults_are_not_overridden(self):
        instance = client(None)
        instance._async_post = AsyncMock()
        await instance.async_shutdown()
        instance._async_post.assert_awaited_once_with("shutdown", {})

    async def test_discovery_rejects_array(self):
        with self.assertRaises(api.PCPowerDiscoveryError):
            api._normalize_discovery_payload([], fallback_host="127.0.0.1", fallback_port=58477)


class TlsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from agent_core.tls import create_server_context
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        context = await asyncio.to_thread(create_server_context, self.directory)
        cert = (self.directory / "agent-cert.pem").read_text(encoding="ascii")
        self.fingerprint = hashlib.sha256(ssl.PEM_cert_to_DER_cert(cert)).hexdigest()
        config = config_in(self.directory)
        path = self.directory / "config.json"
        core.save_config(path, config)
        self.platform = FakePlatform()
        self.server = core.PCPowerHTTPServer(("127.0.0.1", 0), core.PCPowerRequestHandler,
            config, path, logging.getLogger("test"), self.platform, tls_context=context)
        self.server.logger.addHandler(logging.NullHandler())
        self.server.logger.propagate = False
        self.thread = threading.Thread(target=self.server.serve_forever,
            kwargs={"poll_interval": .01}, daemon=True)
        self.thread.start()
        self.session = aiohttp.ClientSession()
        self.client = client(self.session, agent_port=self.server.server_address[1],
            certificate_fingerprint=self.fingerprint)

    async def asyncTearDown(self):
        await self.session.close()
        await asyncio.to_thread(self.server.shutdown)
        self.server.server_close()
        self.thread.join(2)
        self.temp.cleanup()

    async def test_enroll_status_power_and_guard(self):
        info = await api.async_fetch_discovery_info(self.session, host=self.client.host,
            agent_port=self.client.agent_port)
        self.assertEqual(info.certificate_fingerprint, self.fingerprint)
        pair = await api.async_exchange_pairing_code(self.session, host=self.client.host,
            agent_port=self.client.agent_port, pairing_code="123456",
            certificate_fingerprint=info.certificate_fingerprint)
        self.assertEqual(pair.api_token, TOKEN)
        self.assertTrue((await self.client.async_get_status())["online"])
        await self.client.async_shutdown()
        self.assertTrue(self.platform.commands[0]["force"])
        self.server.guard_state = core.CommandGuardState(mode="ignore_manual")
        with self.assertRaises(api.PCPowerCommandError):
            await self.client.async_restart()
        self.assertEqual(len(self.platform.commands), 1)

    async def test_local_certificate_trust_works_for_windows_tray(self):
        from urllib.request import Request, urlopen
        context = ssl.create_default_context(cafile=str(self.directory / "agent-cert.pem"))
        def fetch():
            request = Request(f"{self.client.base_url}/v1/status",
                              headers={"Authorization": f"Bearer {TOKEN}"})
            with urlopen(request, context=context, timeout=2) as response:
                return response.status
        self.assertEqual(await asyncio.to_thread(fetch), 200)

    async def test_relocated_agent_is_authenticated_and_found(self):
        self.client._host = "127.0.0.2"
        self.assertTrue((await self.client.async_get_status())["online"])
        self.assertEqual(self.client.host, "127.0.0.1")

    async def test_expired_code_is_rejected(self):
        self.server.config.pairing_code_expires_at = 1
        with self.assertRaisesRegex(api.PCPowerPairingError, "pairing_code_expired"):
            await api.async_exchange_pairing_code(self.session, host=self.client.host,
                agent_port=self.client.agent_port, pairing_code="123456",
                certificate_fingerprint=self.fingerprint)

    async def test_five_wrong_codes_invalidate_pairing(self):
        results = []
        for _ in range(6):
            async with self.session.post(f"{self.client.base_url}/v1/pairing/exchange",
                ssl=aiohttp.Fingerprint(bytes.fromhex(self.fingerprint)),
                json={"pairing_code": "999999"}) as response:
                results.append(response.status)
        self.assertEqual(results, [401, 401, 401, 401, 429, 412])

    async def test_same_public_identity_wrong_certificate_receives_no_token(self):
        self.client._certificate_fingerprint = "00" * 32
        with patch.object(core.PCPowerRequestHandler, "_authorize", side_effect=AssertionError("Token sent!")):
            with self.assertRaises(api.PCPowerAuthError):
                await self.client.async_get_status()

    async def test_os_failure_is_not_a_connection_failure(self):
        def fail(*args, **kwargs):
            raise core.PowerActionError("OS denied shutdown")
        self.platform.execute_power_action = fail
        self.client.async_discover_host = AsyncMock(return_value=None)
        with self.assertRaisesRegex(api.PCPowerCommandError, "OS denied shutdown"):
            await self.client.async_shutdown()
        self.client.async_discover_host.assert_not_awaited()

    async def test_existing_pairing_upgrades_without_code_or_token_rotation(self):
        self.client._certificate_fingerprint = None
        self.server.config.pairing_code_hash = None
        self.server.persist_config()
        before = self.server.config_path.read_bytes()
        upgrade_headers = []
        original_upgrade = core.PCPowerRequestHandler._handle_tls_upgrade
        def record_upgrade(handler):
            upgrade_headers.append(dict(handler.headers))
            original_upgrade(handler)
        with patch.object(core.PCPowerRequestHandler, "_handle_pairing_exchange",
                          side_effect=AssertionError("Must not pair again")), \
             patch.object(core.PCPowerRequestHandler, "_handle_tls_upgrade", record_upgrade):
            status = await self.client.async_get_status()
        self.assertTrue(status["online"])
        self.assertEqual(len(upgrade_headers), 1)
        self.assertNotIn("Authorization", upgrade_headers[0])
        self.assertEqual(self.client.certificate_fingerprint, self.fingerprint)
        self.assertEqual(self.server.config_path.read_bytes(), before)
        self.assertEqual(self.client._api_token, TOKEN)
        await self.client.async_shutdown()
        self.assertEqual(len(self.platform.commands), 1)

    async def test_existing_pairing_upgrades_after_ip_change(self):
        self.client._certificate_fingerprint = None
        self.client._host = "127.0.0.2"
        self.assertTrue((await self.client.async_get_status())["online"])
        self.assertEqual(self.client.host, "127.0.0.1")
        self.assertEqual(self.client.certificate_fingerprint, self.fingerprint)

    async def test_upgrade_wrong_secret_cannot_receive_credentials(self):
        self.client._certificate_fingerprint = None
        self.client._api_token = "different-test-only-token"
        with patch.object(core.PCPowerRequestHandler, "_authorize") as authorize:
            status = await self.client.async_get_status()
        authorize.assert_not_called()
        self.assertFalse(status["online"])
        self.assertIsNone(self.client.certificate_fingerprint)

    async def test_upgrade_wrong_machine_cannot_be_trusted(self):
        self.client._certificate_fingerprint = None
        self.client._machine_id = "a-different-machine"
        with patch.object(core.PCPowerRequestHandler, "_authorize") as authorize:
            self.assertFalse((await self.client.async_get_status())["online"])
        authorize.assert_not_called()
        self.assertIsNone(self.client.certificate_fingerprint)

    async def test_upgrade_proof_is_bound_to_server_certificate_not_client_input(self):
        nonce = "12" * 32
        async with self.session.post(f"{self.client.base_url}/v1/pairing/upgrade",
            ssl=api._pin(self.fingerprint),
            json={"nonce": nonce, "certificate_fingerprint": "99" * 32}) as response:
            self.assertEqual(response.status, 200)
            payload = await response.json()
        transcript = b"pc-power-free/tls-upgrade/v1\0" + bytes.fromhex(nonce + self.fingerprint)
        self.assertEqual(payload, {"proof": hmac.digest(TOKEN.encode(), transcript, "sha256").hex()})

    async def test_replayed_or_relayed_proof_does_not_establish_trust(self):
        for bad_transcript in (
            b"pc-power-free/tls-upgrade/v1\0" + bytes.fromhex("11" * 32 + self.fingerprint),
            b"pc-power-free/tls-upgrade/v1\0" + bytes.fromhex("22" * 32 + "99" * 32),
        ):
            self.client._certificate_fingerprint = None
            proof = hmac.digest(TOKEN.encode(), bad_transcript, "sha256").hex()
            def wrong_proof(handler):
                self.assertNotIn("Authorization", handler.headers)
                handler._read_json()
                handler._send_json(200, {"proof": proof})
            with patch.object(api.secrets, "token_hex", return_value="22" * 32), \
                 patch.object(core.PCPowerRequestHandler, "_handle_tls_upgrade", wrong_proof), \
                 patch.object(core.PCPowerRequestHandler, "_authorize") as authorize:
                self.assertFalse((await self.client.async_get_status())["online"])
            authorize.assert_not_called()
            self.assertIsNone(self.client.certificate_fingerprint)

    async def test_upgrade_rejects_invalid_nonce_without_mutating_pairing(self):
        before = self.server.config_path.read_bytes()
        for nonce in (None, 123, "", "ab", "G" * 64, "a " * 32, "a" * 4096):
            async with self.session.post(f"{self.client.base_url}/v1/pairing/upgrade",
                ssl=api._pin(self.fingerprint), json={"nonce": nonce}) as response:
                self.assertEqual(response.status, 400)
        self.assertEqual(self.server.config_path.read_bytes(), before)

    async def test_upgraded_pairing_does_not_bootstrap_again_on_restart(self):
        self.client._certificate_fingerprint = None
        self.assertTrue((await self.client.async_get_status())["online"])
        restarted = client(self.session, agent_port=self.client.agent_port,
                           certificate_fingerprint=self.client.certificate_fingerprint)
        with patch.object(core.PCPowerRequestHandler, "_handle_tls_upgrade",
                          side_effect=AssertionError("Already upgraded")):
            self.assertTrue((await restarted.async_get_status())["online"])
