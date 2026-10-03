"""DSM setup authorization and package UI tests."""

import importlib
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import tarfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agent_core import common as core
from agent_core.tls import create_server_context
from tests.test_runtime import FakePlatform, TOKEN, config_in

ROOT = Path(__file__).resolve().parents[1]


class DsmAuthenticationTests(unittest.TestCase):
    def auth(self, cookie="id=valid", remote_addr="192.168.100.10", server_addr="192.168.100.167", **headers):
        module = importlib.import_module("dsm_package.payload.dsm_runtime.setup_auth")
        return module.authenticate_admin(cookie, remote_addr, server_addr, **headers)

    def test_missing_cookie_is_rejected_without_subprocess(self):
        with patch("subprocess.run") as run:
            self.assertFalse(self.auth(cookie=""))
        run.assert_not_called()

    def test_expired_session_is_rejected(self):
        with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, "", "")) as run:
            self.assertFalse(self.auth())
        self.assertEqual(run.call_count, 1)

    def test_non_admin_is_rejected(self):
        calls = [
            subprocess.CompletedProcess([], 0, "sergio\n", ""),
            subprocess.CompletedProcess([], 0, "users\n", ""),
        ]
        with patch("subprocess.run", side_effect=calls):
            self.assertFalse(self.auth())

    def test_admin_is_accepted(self):
        calls = [
            subprocess.CompletedProcess([], 0, "sergio\n", ""),
            subprocess.CompletedProcess([], 0, "users administrators\n", ""),
        ]
        with patch("subprocess.run", side_effect=calls) as run:
            self.assertTrue(self.auth())
        self.assertEqual(run.call_args_list[0].args[0], ["/usr/syno/synoman/webman/modules/authenticate.cgi"])
        self.assertEqual(run.call_args_list[0].kwargs["env"]["HTTP_COOKIE"], "id=valid")
        self.assertEqual(run.call_args_list[1].args[0], ["id", "-nG", "sergio"])

    def test_subprocess_failure_fails_closed(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("authenticate.cgi", 3)):
            self.assertFalse(self.auth())

    def test_signed_desktop_session_reaches_native_authentication(self):
        calls = [
            subprocess.CompletedProcess([], 0, "sergio\n", ""),
            subprocess.CompletedProcess([], 0, "users administrators\n", ""),
        ]
        with patch("subprocess.run", side_effect=calls) as run:
            self.assertTrue(self.auth(cookie="_SSID=desktop", syno_token="csrf-token", syno_hash="signed-request.1"))
        environment = run.call_args_list[0].kwargs["env"]
        self.assertEqual(environment["HTTP_COOKIE"], "_SSID=desktop")
        self.assertEqual(environment["HTTP_X_SYNO_TOKEN"], "csrf-token")
        self.assertEqual(environment["HTTP_X_SYNO_HASH"], "signed-request.1")

    def test_malformed_native_headers_fail_closed(self):
        for headers in (
            {"syno_token": "token\r\nInjected: yes"},
            {"syno_hash": "hash\0"},
            {"syno_hash": "x" * 513},
        ):
            with self.subTest(headers=headers), patch("subprocess.run") as run:
                self.assertFalse(self.auth(**headers))
                run.assert_not_called()

    def test_dsm_adapter_delegates_authentication(self):
        root = Path(__file__).resolve().parents[1]
        paths = [str(root / "linux_agent"), str(root / "dsm_package" / "payload"), *sys.path]
        with patch.object(sys, "path", paths):
            from linux_agent.pc_power_agent import DsmPlatformAdapter

            with patch("dsm_runtime.setup_auth.authenticate_admin", return_value=True) as auth:
                self.assertTrue(DsmPlatformAdapter().authenticate_setup_request(
                    "_SSID=desktop", "192.168.100.10", "192.168.100.167",
                    syno_token="csrf-token", syno_hash="signed-request.1",
                ))
        auth.assert_called_once_with(
            "_SSID=desktop", "192.168.100.10", "192.168.100.167",
            syno_token="csrf-token", syno_hash="signed-request.1",
        )


class DsmPowerTests(unittest.TestCase):
    def setUp(self):
        with patch.object(sys, "path", [str(ROOT / "linux_agent"), *sys.path]):
            from linux_agent.pc_power_agent import DsmPlatformAdapter
        self.adapter = DsmPlatformAdapter()

    def test_status_queries_only_permissions_and_fails_closed(self):
        for results, allowed, count in (
            ([subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 0)], True, 2),
            ([subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 1)], False, 2),
            ([subprocess.CompletedProcess([], 1)], False, 1),
            ([subprocess.TimeoutExpired("sudo", 2)], False, 1),
        ):
            with self.subTest(allowed=allowed, count=count), patch("subprocess.run", side_effect=results) as run:
                self.assertEqual(self.adapter.power_permission_enabled(), allowed)
                self.assertEqual(run.call_count, count)
                for call in run.call_args_list:
                    self.assertEqual(call.args[0][:4], ["/usr/bin/sudo", "-n", "-l", "/usr/syno/sbin/synoshutdown"])

    def test_only_native_normal_commands_are_executed_after_permission_check(self):
        for action, flag in (("shutdown", "--shutdown"), ("restart", "--reboot")):
            with self.subTest(action=action), patch("subprocess.run", return_value=
                    subprocess.CompletedProcess([], 0, "", "")) as run:
                self.adapter.execute_power_action(action, delay_seconds=0, force=False)
                command = ["/usr/syno/sbin/synoshutdown", flag]
                self.assertEqual(run.call_args_list[0].args[0], ["/usr/bin/sudo", "-n", "-l", *command])
                self.assertEqual(run.call_args_list[1].args[0], ["/usr/bin/sudo", "-n", *command])
                self.assertTrue(run.call_args_list[1].kwargs["check"])

    def test_missing_permission_never_attempts_shutdown(self):
        with patch("subprocess.run", return_value=
                subprocess.CompletedProcess([], 1, "", "not allowed")) as run:
            with self.assertRaisesRegex(core.PowerActionError, "DSM power permission is not enabled"):
                self.adapter.execute_power_action("shutdown", delay_seconds=0, force=False)
        self.assertEqual(run.call_count, 1)

    def test_unsupported_actions_never_reach_sudo(self):
        for action, delay, force in (("shutdown", 0, True), ("shutdown", 60, False),
                                     ("restart", -1, False), ("invalid", 0, False)):
            with self.subTest(action=action, delay=delay, force=force), patch("subprocess.run") as run:
                with self.assertRaises(core.PowerActionError):
                    self.adapter.execute_power_action(action, delay_seconds=delay, force=force)
                run.assert_not_called()

    def test_native_failure_is_reported_and_never_retried(self):
        for error, message in (
            (subprocess.CalledProcessError(1, "test", stderr="critical operation in progress"),
             "DSM rejected the power action: critical operation in progress"),
            (subprocess.TimeoutExpired("test", 10), "DSM power command timed out"),
        ):
            with self.subTest(message=message), patch("subprocess.run", side_effect=[
                subprocess.CompletedProcess([], 0, "", ""), error,
            ]) as run:
                with self.assertRaisesRegex(core.PowerActionError, message):
                    self.adapter.execute_power_action("shutdown", delay_seconds=0, force=False)
                self.assertEqual(run.call_count, 2)

    def test_permission_setup_is_root_only_and_refuses_unfamiliar_rules(self):
        module = importlib.import_module("dsm_package.payload.dsm_runtime.power_permissions")
        self.assertEqual(module.RULE.splitlines()[1],
            "pcpowerfree ALL=(root) NOPASSWD: /usr/syno/sbin/synoshutdown --shutdown, "
            "/usr/syno/sbin/synoshutdown --reboot")
        with patch.object(os, "geteuid", return_value=1000, create=True), patch("subprocess.run") as run:
            with self.assertRaisesRegex(RuntimeError, "administrator"):
                module.configure()
            run.assert_not_called()
        with tempfile.TemporaryDirectory() as temporary:
            rule = Path(temporary) / "wakelink-power"
            rule.write_text("another administrator's rule")
            with patch.object(module, "RULE_PATH", rule), \
                    patch.object(os, "geteuid", return_value=0, create=True):
                for remove in (False, True):
                    with self.assertRaisesRegex(RuntimeError, "unfamiliar"):
                        module.configure(remove=remove)
            self.assertEqual(rule.read_text(), "another administrator's rule")


class DsmPlatform(FakePlatform):
    platform_id = "dsm"

    def authenticate_setup_request(self, cookie, remote_addr, server_addr, *, syno_token="", syno_hash=""):
        return cookie == "id=admin" and remote_addr == "192.168.100.10" and server_addr == "192.168.100.167"


class DsmSetupRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.config_path = self.directory / "config.json"
        self.config = config_in(self.directory)
        core.save_config(self.config_path, self.config)
        context = create_server_context(self.directory)
        self.cert_hash = hashlib.sha256((self.directory / "agent-cert.pem").read_bytes()).hexdigest()
        self.key_hash = hashlib.sha256((self.directory / "agent-key.pem").read_bytes()).hexdigest()
        self.platform = DsmPlatform()
        self.server = core.PCPowerHTTPServer(
            ("127.0.0.1", 0), core.PCPowerRequestHandler, self.config,
            self.config_path, logging.getLogger("dsm-test"), self.platform, tls_context=context,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.temp.cleanup()

    def request(self, path, *, method="GET", headers=None):
        request = Request(
            f"https://127.0.0.1:{self.server.server_address[1]}{path}",
            headers=headers or {}, method=method,
        )
        context = ssl.create_default_context(cafile=str(self.directory / "agent-cert.pem"))
        context.check_hostname = False
        try:
            response = urlopen(request, context=context, timeout=3)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response), response.headers

    def headers(self, *, cookie="id=admin", action=None):
        result = {
            "Cookie": cookie,
            "X-WakeLink-Remote-Addr": "192.168.100.10",
            "X-WakeLink-Server-Addr": "192.168.100.167",
        }
        if action:
            result["X-WakeLink-Action"] = action
        return result

    def test_non_dsm_platform_has_no_setup_route(self):
        self.server.platform = FakePlatform()
        status, _, _ = self.request("/v1/dsm/setup", headers=self.headers())
        self.assertEqual(status, 404)

    def test_non_loopback_source_is_rejected(self):
        self.server.platform = DsmPlatform()
        with patch.object(core.ipaddress, "ip_address", return_value=core.ipaddress.ip_address("192.0.2.1")):
            status, _, _ = self.request("/v1/dsm/setup", headers=self.headers())
        self.assertEqual(status, 403)

    def test_missing_or_invalid_session_is_rejected(self):
        for cookie in ("", "id=nonadmin"):
            with self.subTest(cookie=cookie):
                status, _, _ = self.request("/v1/dsm/setup", headers=self.headers(cookie=cookie))
                self.assertEqual(status, 403)

    def test_pairing_requires_custom_header(self):
        status, _, _ = self.request("/v1/dsm/pairing-code", method="POST", headers=self.headers())
        self.assertEqual(status, 403)

    def test_status_exposes_no_secret(self):
        status, payload, headers = self.request("/v1/dsm/setup", headers=self.headers())
        self.assertEqual(status, 200)
        self.assertTrue(payload["online"])
        self.assertEqual(payload["hostname"], self.server.hostname)
        self.assertNotIn(TOKEN, json.dumps(payload))
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_status_reports_power_permission_without_power_action(self):
        with patch.object(self.platform, "power_permission_enabled", return_value=True, create=True) as check:
            status, payload, _ = self.request("/v1/dsm/setup", headers=self.headers())
        self.assertEqual(status, 200)
        self.assertTrue(payload["power_permission_enabled"])
        check.assert_called_once_with()
        self.assertEqual(self.platform.commands, [])

    def test_route_preserves_native_signature_without_exposing_it(self):
        headers = {**self.headers(), "X-SYNO-TOKEN": "csrf-token", "X-SYNO-HASH": "signed-request.1"}
        with patch.object(self.platform, "authenticate_setup_request", wraps=self.platform.authenticate_setup_request) as auth:
            status, payload, _ = self.request("/v1/dsm/setup", headers=headers)
        self.assertEqual(status, 200)
        auth.assert_called_once_with(
            "id=admin", "192.168.100.10", "192.168.100.167",
            syno_token="csrf-token", syno_hash="signed-request.1",
        )
        self.assertNotIn("csrf-token", json.dumps(payload))
        self.assertNotIn("signed-request.1", json.dumps(payload))

    def test_pairing_preserves_identity_and_existing_connection(self):
        status, payload, headers = self.request(
            "/v1/dsm/pairing-code", method="POST", headers=self.headers(action="pair"),
        )
        self.assertEqual(status, 200)
        self.assertRegex(payload["pairing_code"], r"^[0-9]{6}$")
        self.assertEqual(headers["Cache-Control"], "no-store")
        saved = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["token"], TOKEN)
        self.assertEqual(saved["machine_id"], "test-machine")
        self.assertEqual(saved["pairing_code_hash"], core.hash_pairing_code(payload["pairing_code"]))
        self.assertGreater(saved["pairing_code_expires_at"], time.time() + 590)
        self.assertEqual(hashlib.sha256((self.directory / "agent-cert.pem").read_bytes()).hexdigest(), self.cert_hash)
        self.assertEqual(hashlib.sha256((self.directory / "agent-key.pem").read_bytes()).hexdigest(), self.key_hash)
        self.assertEqual(self.platform.commands, [])


class DsmPageTests(unittest.TestCase):
    def ui(self):
        return importlib.import_module("dsm_package.payload.ui.setup_cgi")

    def test_package_launcher_opens_dsm_desktop_window(self):
        info = (ROOT / "dsm_package/template/INFO.in").read_text(encoding="utf-8")
        config = json.loads((ROOT / "dsm_package/payload/ui/config").read_text(encoding="utf-8"))
        self.assertIn('displayname="WakeLink"', info)
        self.assertIn('dsmuidir="ui"', info)
        self.assertIn('dsmappname="com.wakelink.Setup"', info)
        self.assertNotIn(".url", config)
        app = config["main.js"]["com.wakelink.Setup"]
        self.assertEqual(app["type"], "app")
        self.assertEqual(app["appWindow"], "SYNO.SDS.WakeLink.MainWindow")
        self.assertFalse(app["allowMultiInstance"])
        self.assertNotIn("allUsers", app)
        launcher = (ROOT / "dsm_package/payload/ui/main.js").read_text(encoding="utf-8")
        self.assertIn('Ext.define("com.wakelink.Setup"', launcher)
        self.assertIn('extend: "SYNO.SDS.AppWindow"', launcher)
        self.assertIn('/webman/3rdparty/pcpowerfree/index.html', launcher)
        self.assertNotIn("/v1/power/", launcher)

    def test_page_has_both_languages_and_no_power_button(self):
        html = (ROOT / "dsm_package/payload/ui/index.html").read_text(encoding="utf-8")
        script = (ROOT / "dsm_package/payload/ui/app.js").read_text(encoding="utf-8")
        self.assertIn('lang="en"', html)
        self.assertIn("Generar código", script)
        self.assertIn("Generate pairing code", script)
        self.assertNotIn("/v1/power/", html + script)
        self.assertNotIn("action=shutdown", html + script)

    def test_desktop_session_is_used_without_a_second_login_form(self):
        html = (ROOT / "dsm_package/payload/ui/index.html").read_text(encoding="utf-8")
        script = (ROOT / "dsm_package/payload/ui/app.js").read_text(encoding="utf-8")
        self.assertNotIn('type="password"', html)
        self.assertNotIn('id="login-form"', html)
        self.assertNotIn('SYNO.API.Auth', script)
        self.assertIn('id="desktop-link"', html)
        self.assertIn('api.env.getRequestHeaders()', script)
        self.assertIn('"X-SYNO-TOKEN", "X-SYNO-HASH"', script)

    def test_dsm_ui_assets_are_versioned_on_each_package_upgrade(self):
        html = (ROOT / "dsm_package/payload/ui/index.html").read_text(encoding="utf-8")
        launcher = (ROOT / "dsm_package/payload/ui/main.js").read_text(encoding="utf-8")
        builder = (ROOT / "dsm_package/build-dsm-package.ps1").read_text(encoding="utf-8")
        self.assertIn('app.js?revision=@@DSM_PACKAGE_VERSION@@', html)
        self.assertIn('style.css?revision=@@DSM_PACKAGE_VERSION@@', html)
        self.assertIn('index.html?revision=@@DSM_PACKAGE_VERSION@@', launcher)
        self.assertIn('Replace("@@DSM_PACKAGE_VERSION@@", $dsmPackageVersion)', builder)

    def test_cgi_rejects_unknown_action_without_proxying(self):
        module = self.ui()
        with patch.object(module, "call_agent") as call:
            status, _ = module.handle_request({"QUERY_STRING": "action=shutdown", "REQUEST_METHOD": "POST"})
        self.assertEqual(status, 404)
        call.assert_not_called()

    def test_cgi_pairing_requires_custom_header(self):
        module = self.ui()
        with patch.object(module, "call_agent") as call:
            status, _ = module.handle_request({"QUERY_STRING": "action=pair", "REQUEST_METHOD": "POST"})
        self.assertEqual(status, 403)
        call.assert_not_called()

    def test_cgi_rejects_cross_origin_post(self):
        module = self.ui()
        environment = {
            "QUERY_STRING": "action=pair", "REQUEST_METHOD": "POST",
            "HTTP_X_WAKELINK_ACTION": "pair", "HTTP_ORIGIN": "https://other.example",
            "HTTP_HOST": "nas.local:5001",
        }
        with patch.object(module, "call_agent") as call:
            status, _ = module.handle_request(environment)
        self.assertEqual(status, 403)
        call.assert_not_called()

    def test_cgi_reports_agent_unavailable(self):
        module = self.ui()
        with patch.object(module, "call_agent", side_effect=URLError("offline")):
            status, payload = module.handle_request({"QUERY_STRING": "action=status", "REQUEST_METHOD": "GET"})
        self.assertEqual(status, 503)
        self.assertEqual(payload["error"], "WakeLink agent unavailable")

    def test_cgi_forwards_admin_context_and_disables_caching(self):
        module = self.ui()
        environment = {
            "QUERY_STRING": "action=pair", "REQUEST_METHOD": "POST",
            "HTTP_X_WAKELINK_ACTION": "pair", "HTTP_COOKIE": "id=admin",
            "REMOTE_ADDR": "192.168.100.10", "SERVER_ADDR": "192.168.100.167",
            "HTTP_X_SYNO_TOKEN": "csrf-token", "HTTP_X_SYNO_HASH": "signed-request.1",
        }
        output = io.StringIO()
        with patch.object(module, "call_agent", return_value=(200, {"pairing_code": "123456", "expires_in": 600})) as call:
            module.main(environment, output)
        self.assertEqual(call.call_args.args[0], "POST")
        self.assertEqual(call.call_args.args[1], "/v1/dsm/pairing-code")
        self.assertEqual(call.call_args.args[2]["Cookie"], "id=admin")
        self.assertEqual(call.call_args.args[2]["X-SYNO-TOKEN"], "csrf-token")
        self.assertEqual(call.call_args.args[2]["X-SYNO-HASH"], "signed-request.1")
        self.assertIn("Cache-Control: no-store", output.getvalue())
        self.assertIn('"pairing_code": "123456"', output.getvalue())
        self.assertNotIn("id=admin", output.getvalue())
        self.assertNotIn("signed-request.1", output.getvalue())

    def test_cgi_uses_pinned_public_certificate(self):
        module = self.ui()
        source = (ROOT / "dsm_package/payload/ui/setup_cgi.py").read_text(encoding="utf-8")
        self.assertIn("agent-cert.pem", source)
        self.assertIn("ssl.create_default_context", source)
        self.assertNotIn("_create_unverified_context", source)

    def test_built_package_has_page_but_no_private_state(self):
        archive_path = ROOT / "dsm_package/build/package.tgz"
        if not archive_path.is_file():
            self.skipTest("Build the DSM package first")
        with tarfile.open(archive_path) as archive:
            names = {name.removeprefix("./") for name in archive.getnames()}
            self.assertIn("ui/index.html", names)
            self.assertIn("ui/main.js", names)
            self.assertIn("ui/setup.cgi", names)
            self.assertIn("ui/images/wakelink_64.png", names)
            for name in names:
                self.assertNotIn(Path(name).name, {"agent-key.pem", "agent-cert.pem", "config.json"})

    def test_built_package_contains_root_protected_setup_helper(self):
        archive_path = ROOT / "dsm_package/build/spk"
        if not archive_path.is_dir():
            self.skipTest("Build the DSM package first")
        self.assertEqual(
            (archive_path / "conf/power_permissions.py").read_bytes(),
            (ROOT / "dsm_package/payload/dsm_runtime/power_permissions.py").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
