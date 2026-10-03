"""Linux desktop setup must not replace existing Home Assistant credentials."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "linux_agent" / "setup_cli.py"


class LinuxInstallerTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("dpkg-deb"), "Debian packaging tools are unavailable")
    def test_deb_has_safe_directory_modes_and_no_private_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            subprocess.run(["sh", str(ROOT / "linux_package/build-deb.sh"), temporary],
                           check=True, capture_output=True, text=True, timeout=30)
            package = next(Path(temporary).glob("WakeLink-Ubuntu-*.deb"))
            listing = subprocess.run(["dpkg-deb", "--contents", str(package)],
                                     check=True, capture_output=True, text=True).stdout
            self.assertTrue(listing.splitlines()[0].startswith("drwxr-xr-x"))
            self.assertNotIn("config.json", listing)
            self.assertNotIn("agent-key.pem", listing)
            self.assertIn("wakelink.desktop", listing)

    def test_desktop_package_has_gui_launcher_and_keeps_config_on_upgrade(self):
        package = ROOT / "linux_package"
        desktop = (package / "wakelink.desktop").read_text(encoding="utf-8")
        postinst = (package / "postinst").read_text(encoding="utf-8")
        service = (package / "pcpowerfree-agent.service").read_text(encoding="utf-8")
        self.assertIn("Terminal=false", desktop)
        self.assertIn("linux_agent/desktop_ui.py", desktop)
        self.assertIn("WakeLink", desktop)
        self.assertNotIn("setup_cli.py", postinst)
        self.assertIn("ExecStart=/usr/bin/python3", service)
        self.assertTrue((package / "build-deb.sh").exists())
        self.assertTrue((package / "setup-helper.sh").exists())

    def test_new_pairing_code_keeps_existing_identity_and_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            config = directory / "config.json"
            original = json.loads((ROOT / "tests/fixtures/beta6-config.json").read_text())
            config.write_text(json.dumps(original), encoding="utf-8")
            certificate = directory / "agent-cert.pem"
            key = directory / "agent-key.pem"
            certificate.write_bytes(b"existing certificate")
            key.write_bytes(b"existing private key")

            result = subprocess.run(
                [sys.executable, str(SETUP), "--config", str(config), "--pairing-only"],
                capture_output=True, text=True, timeout=10,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertRegex(result.stdout, r"Pairing code: [0-9]{6}")
            updated = json.loads(config.read_text(encoding="utf-8"))
            for field in ("pairing_code_hash", "pairing_code_expires_at", "pairing_code_failed_attempts"):
                original.pop(field, None)
                updated.pop(field, None)
            self.assertEqual(updated, original)
            self.assertEqual(certificate.read_bytes(), b"existing certificate")
            self.assertEqual(key.read_bytes(), b"existing private key")

    def test_pairing_only_refuses_missing_or_broken_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / "config.json"
            for content in (None, "{broken"):
                if content is not None:
                    config.write_text(content, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(SETUP), "--config", str(config), "--pairing-only"],
                    capture_output=True, text=True, timeout=10,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(config.read_text(encoding="utf-8") if config.exists() else None, content)


if __name__ == "__main__":
    unittest.main()
