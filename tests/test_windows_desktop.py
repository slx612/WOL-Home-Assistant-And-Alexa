"""Exercise the desktop flow with temporary data, never the installed agent."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "windows_agent"))


@unittest.skipUnless(sys.platform == "win32", "Windows desktop")
class DesktopDataTests(unittest.TestCase):
    def test_settings_save_preserves_existing_identity_and_unrelated_options(self):
        import setup_wizard_gui as setup
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            original = {"host": "192.0.2.5", "port": 8777, "token": "old-token-not-regenerated",
                        "machine_id": "already-paired", "shutdown_delay_seconds": 17,
                        "custom_setting": "keep", "pairing_code_hash": None}
            path.write_text(json.dumps(original), encoding="utf-8")
            setup.write_config(path, port=8777, token=original["token"],
                allowed_subnets=["192.0.2.1/32", "127.0.0.1/32"], force=False,
                machine_id="already-paired", pairing_code_hash="new-code", pairing_code_expires_at=100)
            saved = json.loads(path.read_text())
            for key in ("host", "port", "token", "machine_id", "shutdown_delay_seconds", "custom_setting"):
                self.assertEqual(saved[key], original[key], key)

    def test_firewall_setup_does_not_flash_console_windows(self):
        from types import SimpleNamespace
        import setup_wizard_gui as setup
        with patch.object(setup.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
            setup.configure_firewall("test-rule-not-created", port=8777, remote_addresses=["192.0.2.0/24"])
        for call in run.call_args_list:
            self.assertEqual(call.kwargs.get("creationflags"), setup.subprocess.CREATE_NO_WINDOW)

    def test_displayed_certificate_fingerprint_matches_the_agent_certificate(self):
        import hashlib
        import ssl
        import setup_wizard_gui as setup
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            setup.create_server_context(directory)
            certificate = (directory / "agent-cert.pem").read_text()
            expected = hashlib.sha256(ssl.PEM_cert_to_DER_cert(certificate)).hexdigest()
            self.assertEqual(setup.certificate_fingerprint(directory), expected)

    def test_windows_certificate_is_readable_by_users_but_private_key_is_not(self):
        from agent_core.tls import create_server_context
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            create_server_context(directory)
            certificate = directory / "agent-cert.pem"
            key = directory / "agent-key.pem"
            cert_bytes, key_bytes = certificate.read_bytes(), key.read_bytes()
            create_server_context(directory)
            self.assertEqual(certificate.read_bytes(), cert_bytes)
            self.assertEqual(key.read_bytes(), key_bytes)
            cert_acl = subprocess.run(["icacls.exe", str(certificate)], capture_output=True,
                text=True, check=True).stdout.upper()
            key_acl = subprocess.run(["icacls.exe", str(key)], capture_output=True,
                text=True, check=True).stdout.upper()
            self.assertRegex(cert_acl, r"BUILTIN\\(USERS|USUARIOS):\(R\)")
            self.assertNotRegex(key_acl, r"BUILTIN\\(USERS|USUARIOS):")

    def test_bad_existing_configuration_is_not_treated_as_a_new_install(self):
        import setup_wizard_gui as setup
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            path.write_text('{"broken":', encoding="utf-8")
            with self.assertRaises(ValueError):
                setup.load_existing_config(path)
            self.assertEqual(path.read_text(), '{"broken":')

    def test_language_is_persisted_independently_of_agent_credentials(self):
        import ui_preferences
        with tempfile.TemporaryDirectory() as temporary, \
             patch.dict(os.environ, {"PC_POWER_FREE_PREFERENCES_DIR": temporary}):
            ui_preferences.save_language("es")
            with patch.object(ui_preferences.locale, "getlocale", return_value=("en_US", "UTF-8")):
                self.assertEqual(ui_preferences.load_language(), "es")
            self.assertEqual(json.loads((Path(temporary) / "preferences.json").read_text()), {"language": "es"})
            with self.assertRaises(ValueError):
                ui_preferences.save_language("invalid")

    def test_generating_a_code_keeps_existing_pairing_and_network_restrictions(self):
        import setup_wizard_gui as setup
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "config.json"
            original = {"host": "0.0.0.0", "port": 8777, "token": "keep-existing-token-123456",
                        "machine_id": "existing-id", "allowed_subnets": ["192.0.2.7/32"],
                        "pairing_code_failed_attempts": 4}
            path.write_text(json.dumps(original), encoding="utf-8")
            code = setup.activate_pairing_code(path)
            self.assertEqual(len(code), 6)
            self.assertTrue(code.isascii() and code.isdigit())
            saved = json.loads(path.read_text())
            for key in ("host", "port", "token", "machine_id", "allowed_subnets"):
                self.assertEqual(saved[key], original[key])
            self.assertEqual(saved["pairing_code_failed_attempts"], 0)
            self.assertEqual(saved["pairing_code_hash"], setup.hash_pairing_code(code))


@unittest.skipUnless(sys.platform == "win32", "Windows desktop")
class DesktopViewTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        import desktop_ui
        self.ui = desktop_ui
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.environment = patch.dict(os.environ, {"PC_POWER_FREE_DATA_DIR": self.temp.name,
            "PC_POWER_FREE_PREFERENCES_DIR": self.temp.name})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        # No background network/OS jobs: only the real widgets and UI state are exercised.
        self.jobs = patch.object(desktop_ui.WakeLinkApplication, "_run_job")
        self.jobs.start()
        self.addCleanup(self.jobs.stop)

    def test_first_run_goes_to_setup_without_showing_a_fake_pairing_code(self):
        app = self.ui.WakeLinkApplication(self.root, initial_language="en")
        self.assertEqual(app.current_page, "setup")
        self.assertEqual(app.pairing_code_var.get(), "------")
        self.assertFalse((Path(self.temp.name) / "config.json").exists())

    def test_upgrade_opens_dashboard_without_rewriting_configuration(self):
        path = Path(self.temp.name) / "config.json"
        raw = '{"port":8777,"token":"existing-secret","machine_id":"existing-id","allowed_subnets":["192.0.2.7/32"]}'
        path.write_text(raw, encoding="utf-8")
        app = self.ui.WakeLinkApplication(self.root, initial_language="es")
        self.assertEqual(app.current_page, "home")
        self.assertEqual(app.port_var.get(), "8777")
        self.assertEqual(path.read_text(), raw)
        self.assertEqual(app.pairing_code_var.get(), "------")

    def test_certificate_permission_error_does_not_leave_a_blank_window(self):
        path = Path(self.temp.name) / "config.json"
        path.write_text('{"port":8777,"token":"existing","machine_id":"existing"}', encoding="utf-8")
        (Path(self.temp.name) / "agent-cert.pem").write_text("cert", encoding="ascii")
        with patch.object(self.ui.setup, "certificate_fingerprint", side_effect=PermissionError("certificate")):
            app = self.ui.WakeLinkApplication(self.root, initial_language="es")
        self.assertEqual(app.current_page, "home")
        self.assertIn("certificado", app.fingerprint_var.get().lower())
        self.assertIn("WakeLink", self.root.title())

    def test_settings_are_unlocked_before_editing_so_elevation_cannot_lose_input(self):
        import setup_wizard_gui as setup
        with patch.object(setup, "is_admin", return_value=False):
            app = self.ui.WakeLinkApplication(self.root, initial_language="en")
        self.assertTrue(app.port_entry.instate(["readonly"]))
        self.assertTrue(app.networks_entry.instate(["readonly"]))
        self.assertTrue(app.save_button.instate(["disabled"]))
        self.assertTrue(app.unlock_button.winfo_manager())

    def test_switching_language_preserves_inputs_and_current_page(self):
        app = self.ui.WakeLinkApplication(self.root, initial_language="en")
        app.show_page("settings")
        app.port_var.set("8777")
        app.language_var.set("Espa\u00f1ol")
        app._on_language_changed()
        self.assertEqual(app.language_code, "es")
        self.assertEqual(app.current_page, "settings")
        self.assertEqual(app.port_var.get(), "8777")
        import ui_preferences
        self.assertEqual(ui_preferences.load_language(), "es")

    def test_navigation_does_not_generate_pairing_credentials(self):
        app = self.ui.WakeLinkApplication(self.root, initial_language="en")
        for page in ("home", "pairing", "settings", "updates"):
            app.show_page(page)
            self.assertEqual(app.current_page, page)
        self.assertFalse((Path(self.temp.name) / "config.json").exists())

    def test_dashboard_status_and_protection_round_trip_over_real_tls(self):
        import logging
        import threading
        from test_runtime import core, config_in, FakePlatform
        from agent_core.tls import create_server_context
        directory = Path(self.temp.name)
        config = config_in(directory)
        path = directory / "config.json"
        core.save_config(path, config)
        platform = FakePlatform()
        server = core.PCPowerHTTPServer(("127.0.0.1", 0), core.PCPowerRequestHandler,
            config, path, logging.getLogger("desktop-test"), platform,
            tls_context=create_server_context(directory))
        server.logger.addHandler(logging.NullHandler())
        server.logger.propagate = False
        payload = json.loads(path.read_text())
        payload["port"] = server.server_port
        path.write_text(json.dumps(payload), encoding="utf-8")
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
        thread.start()
        try:
            app = self.ui.WakeLinkApplication(self.root, initial_language="en")
            app._status_received(app._local_request())
            self.assertTrue(app.online)
            self.assertFalse(app.guard_status["command_guard_active"])
            app._local_request("POST", "/v1/local/guard", {"mode": "ignore_until", "duration_minutes": 60})
            app._status_received(app._local_request())
            self.assertTrue(app.guard_status["command_guard_active"])
            self.assertIn("Protected until", app.guard_status_var.get())
            self.assertEqual(platform.commands, [])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(2)

    def test_hour_protection_uses_the_agent_minutes_contract(self):
        app = self.ui.WakeLinkApplication(self.root, initial_language="en")
        app.online = True
        app._busy_buttons()
        with patch.object(app, "set_guard") as guard:
            app.guard_buttons[0].invoke()
        self.assertEqual(guard.call_args.args[0], {"mode": "ignore_until", "duration_minutes": 60})

    def test_installer_language_is_kept_on_next_launch(self):
        self.ui.WakeLinkApplication(self.root, initial_language="es")
        import ui_preferences
        with patch.object(ui_preferences.locale, "getlocale", return_value=("en_US", "UTF-8")):
            self.assertEqual(ui_preferences.load_language(), "es")

    def test_changing_the_pairing_code_invalidates_the_copy_action_immediately(self):
        import time
        import setup_wizard_gui as setup
        path = Path(self.temp.name) / "config.json"
        path.write_text(json.dumps({"token": "existing", "machine_id": "existing", "port": 8777}), encoding="utf-8")
        app = self.ui.WakeLinkApplication(self.root, initial_language="en")
        app.pairing_code_var.set("123456")
        app.code_deadline = time.time() + 300
        setup.activate_pairing_code(path)
        with patch.object(self.root, "clipboard_append") as copy:
            app.copy_code()
        copy.assert_not_called()

    def test_repair_keeps_config_verbatim_without_new_pairing(self):
        path = Path(self.temp.name) / "config.json"
        original = '{"host":"0.0.0.0","port":8777,"token":"existing","machine_id":"existing","allowed_subnets":["192.0.2.7/32"],"shutdown_force":false}'
        path.write_text(original, encoding="utf-8")
        app = self.ui.WakeLinkApplication(self.root, initial_language="en")
        with patch.object(app, "_install_runtime") as install:
            app._repair_runtime()
        self.assertEqual(path.read_text(), original)
        self.assertEqual(install.call_args.args, (8777, ["192.0.2.7/32"]))
        self.assertEqual(install.call_args.kwargs, {"first_run": True})

    def test_settings_overview_fits_small_window_in_both_languages(self):
        app = self.ui.WakeLinkApplication(self.root, initial_language="en")
        from types import SimpleNamespace
        app.canvas.unbind("<Configure>")
        for language in ("English", "Espa\u00f1ol"):
            app.language_var.set(language)
            app._on_language_changed()
            for name in app.pages:
                app.show_page(name)
                app._resize(SimpleNamespace(width=520))
                self.root.update_idletasks()
                page = app.pages[name]
                self.assertLessEqual(page.winfo_reqwidth(), 465, (language, name))


if __name__ == "__main__":
    unittest.main()
