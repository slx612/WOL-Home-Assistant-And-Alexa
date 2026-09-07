"""Safe regressions: fake power adapter and temporary loopback server only."""
import concurrent.futures
import io
import json
import logging
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_core import common as core

TOKEN = "test-only-token-not-a-real-credential"
MAC = "02:00:00:00:00:01"


class FakePlatform:
    platform_id = "windows"
    capabilities = ("shutdown", "restart", "guard", "pairing", "discovery")

    def __init__(self):
        self.commands = []

    def detect_primary_adapter(self):
        return core.AdapterInfo("test", "fake", "127.0.0.1", 32, MAC,
                                "127.0.0.1/32", "127.0.0.1")

    def get_mac_addresses(self):
        return [MAC]

    def get_system_uptime_seconds(self):
        return 100

    def execute_power_action(self, action, **kwargs):
        self.commands.append({"action": action, **kwargs})


def config_in(directory):
    return core.AgentConfig.from_dict({
        "token": TOKEN, "machine_id": "test-machine", "port": 58477,
        "allowed_subnets": ["127.0.0.1/32"], "shutdown_force": True,
        "pairing_code_hash": core.hash_pairing_code("123456"),
        "pairing_code_expires_at": time.time() + 600,
    }, config_dir=directory)[0]


class RuntimeTests(unittest.TestCase):
    def test_discovery_recovers_after_network_is_late(self):
        server = Mock()
        server.hostname = "test"
        server.config.machine_id = "test-machine"
        server.server_address = ("127.0.0.1", 58477)
        server.platform = FakePlatform()
        advertiser = core.ServiceAdvertiser(server, logging.getLogger("test"))
        self.assertTrue(hasattr(advertiser, "_refresh"), "Discovery must support repeated refresh")
        with patch.object(core, "Zeroconf") as zeroconf, patch.object(core, "ServiceInfo"), \
             patch.object(core, "IPVersion", Mock(V4Only=1)):
            with patch.object(server.platform, "detect_primary_adapter", side_effect=OSError("No network")):
                advertiser._refresh()
            advertiser._refresh()
            zeroconf.return_value.register_service.assert_called_once()
            advertiser._refresh()
            zeroconf.return_value.register_service.assert_called_once()
            advertiser.stop()

    def test_invalid_power_payload_does_not_execute(self):
        handler = object.__new__(core.PCPowerRequestHandler)
        handler.server = Mock()
        handler.server.get_effective_guard_state.return_value = core.CommandGuardState()
        handler.server.config.shutdown_delay_seconds = 0
        handler.server.config.shutdown_force = False
        handler._send_json = Mock()
        handler._execute_power_action("shutdown", {"force": "false"})
        handler.server.platform.execute_power_action.assert_not_called()
        self.assertEqual(handler._send_json.call_args.args[0], 400)

    def test_rejects_invalid_body_length_before_read(self):
        for length in ("-1", "1000000000", "invalid"):
            with self.subTest(length=length):
                handler = object.__new__(core.PCPowerRequestHandler)
                handler.headers = {"Content-Length": length}
                handler.rfile = Mock(return_value=io.BytesIO(b"{}"))
                handler.rfile.read.return_value = b"{}"
                with self.assertRaises(ValueError):
                    handler._read_json()
                handler.rfile.read.assert_not_called()

    def test_corrupt_guard_blocks_instead_of_allowing(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "guard.json"
            with path.open("w") as stream:
                stream.write("{")
            self.assertTrue(core.load_guard_state(path).is_blocking())

    def test_atomic_guard_preserves_previous_file_if_replace_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "guard.json"
            core.save_guard_state(path, core.CommandGuardState(mode="ignore_manual"))
            with patch("os.replace", side_effect=OSError("disk failure")):
                with self.assertRaises(OSError):
                    core.save_guard_state(path, core.CommandGuardState())
            self.assertTrue(core.load_guard_state(path).is_blocking())

    def test_pairing_is_consumed_once_under_concurrency(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            config = config_in(path.parent)
            core.save_config(path, config)
            server = core.PCPowerHTTPServer(("127.0.0.1", 0), core.PCPowerRequestHandler,
                config, path, logging.getLogger("test"), FakePlatform())
            self.addCleanup(server.server_close)
            barrier = threading.Barrier(2)
            def exchange():
                handler = object.__new__(core.PCPowerRequestHandler)
                handler.server = server
                handler.client_address = ("127.0.0.1", 1234)
                handler._read_json = lambda: {"pairing_code": "123456"}
                replies = []
                handler._send_json = lambda status, payload: replies.append(int(status))
                # Delay after validation in the old implementation to expose double use.
                handler._build_discovery_payload = lambda: (time.sleep(.05) or {})
                barrier.wait(timeout=2)
                handler._handle_pairing_exchange()
                return replies[0]
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: exchange(), range(2)))
            self.assertEqual(sorted(results), [200, 412])


if __name__ == "__main__":
    unittest.main()
