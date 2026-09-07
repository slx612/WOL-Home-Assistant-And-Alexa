"""Windows API calls are mocked; DSM failure test runs a harmless shell fragment."""
import ctypes
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "windows_agent"))


@unittest.skipUnless(sys.platform == "win32", "Windows wrapper")
class WindowsTests(unittest.TestCase):
    def test_upgrade_entry_point_reuses_published_data_location_without_gui(self):
        import setup_wizard_gui as setup
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            config = directory / "config.json"
            shutil.copyfile(ROOT / "tests/fixtures/beta6-config.json", config)
            args = types.SimpleNamespace(upgrade_existing=True, config=None, lang=None)
            with patch.object(setup, "parse_args", return_value=args), \
                 patch.object(setup, "resolve_data_dir", return_value=directory), \
                 patch.object(setup, "upgrade_existing_installation") as upgrade, \
                 patch.object(setup.tk, "Tk") as gui:
                self.assertEqual(setup.main(), 0)
            self.assertEqual(upgrade.call_args.args[1], config)
            gui.assert_not_called()

    def test_first_install_probe_leaves_configuration_for_the_wizard(self):
        import setup_wizard_gui as setup
        with tempfile.TemporaryDirectory() as temporary:
            args = types.SimpleNamespace(upgrade_existing=True, config=None, lang=None)
            with patch.object(setup, "parse_args", return_value=args), \
                 patch.object(setup, "resolve_data_dir", return_value=Path(temporary)), \
                 patch.object(setup, "upgrade_existing_installation") as upgrade, \
                 patch.object(setup.tk, "Tk") as gui:
                self.assertEqual(setup.main(), 3)
            upgrade.assert_not_called()
            gui.assert_not_called()

    def test_published_installation_upgrade_keeps_config_guard_and_tls_identity(self):
        import setup_wizard_gui as setup
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            config = directory / "config.json"
            shutil.copyfile(ROOT / "tests/fixtures/beta6-config.json", config)
            guard = directory / "guard_state.json"
            guard.write_text('{"mode":"ignore_manual"}', encoding="utf-8")
            original_config, original_guard = config.read_bytes(), guard.read_bytes()
            with patch.object(setup, "run_task_script", return_value=True) as task, \
                 patch.object(setup, "wait_for_agent") as wait, \
                 patch.object(setup, "resolve_agent_command", return_value=("fake.exe", "")):
                setup.upgrade_existing_installation(directory, config)
                cert, key = (directory / "agent-cert.pem").read_bytes(), (directory / "agent-key.pem").read_bytes()
                setup.upgrade_existing_installation(directory, config)
            self.assertEqual(config.read_bytes(), original_config)
            self.assertEqual(guard.read_bytes(), original_guard)
            self.assertEqual((directory / "agent-cert.pem").read_bytes(), cert)
            self.assertEqual((directory / "agent-key.pem").read_bytes(), key)
            self.assertEqual(task.call_args.args[1], "Upgrade")
            self.assertEqual(wait.call_count, 2)

    def test_corrupt_upgrade_config_is_not_replaced_or_repaired_with_new_credentials(self):
        import setup_wizard_gui as setup
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            config = directory / "config.json"
            config.write_text('{"broken"', encoding="utf-8")
            original = config.read_bytes()
            with patch.object(setup, "run_task_script") as task:
                with self.assertRaises(ValueError):
                    setup.upgrade_existing_installation(directory, config)
            self.assertEqual(config.read_bytes(), original)
            task.assert_not_called()
            self.assertFalse((directory / "agent-key.pem").exists())

    def test_upgrade_does_not_enable_previously_disabled_startup(self):
        import setup_wizard_gui as setup
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            config = directory / "config.json"
            shutil.copyfile(ROOT / "tests/fixtures/beta6-config.json", config)
            with patch.object(setup, "run_task_script", return_value=False), \
                 patch.object(setup, "wait_for_agent") as wait, \
                 patch.object(setup, "resolve_agent_command", return_value=("fake.exe", "")):
                setup.upgrade_existing_installation(directory, config)
            wait.assert_not_called()

    def test_uptime_uses_unsigned_64_bit_return(self):
        import pc_power_agent as windows
        windows.get_system_uptime_seconds()
        self.assertEqual(ctypes.sizeof(ctypes.windll.kernel32.GetTickCount64.restype), 8)

    def test_invalid_mac_is_rejected(self):
        import pc_power_agent as windows
        self.assertIsNone(windows._normalize_mac_string("GG:GG:GG:GG:GG:GG"))

    def test_task_failure_is_reported(self):
        import setup_wizard_gui as setup
        failed = types.SimpleNamespace(returncode=1, stdout="", stderr="Task failed")
        with patch.object(setup.subprocess, "run", return_value=failed):
            with self.assertRaisesRegex(RuntimeError, "Task failed"):
                setup.install_startup_task("Test not installed", command_exe="fake.exe",
                    command_prefix="", config_path=Path("fake-config.json"))

    def test_configurator_uses_shared_task_script(self):
        import setup_wizard_gui as setup
        ok = types.SimpleNamespace(returncode=0, stdout="", stderr="")
        with patch.object(setup.subprocess, "run", return_value=ok) as run:
            setup.install_startup_task("Test not installed", command_exe="fake.exe",
                command_prefix="", config_path=Path("fake-config.json"))
        command = run.call_args.args[0]
        self.assertTrue(any(str(arg).endswith("install-task.ps1") for arg in command))

    def test_setup_launch_uses_windows_elevation(self):
        import pc_power_tray as tray
        with patch.object(tray.ctypes.windll.shell32, "ShellExecuteW", return_value=42) as launch:
            tray.launch_configurator(Path("fake.exe"))
        self.assertEqual(launch.call_args.args[1], "runas")

    def test_standalone_setup_uses_its_bundled_task_script(self):
        import setup_wizard_gui as setup
        ok = types.SimpleNamespace(returncode=0, stdout="", stderr="")
        with patch.object(setup.sys, "frozen", True, create=True), \
             patch.object(setup.sys, "_MEIPASS", "C:/isolated-test-bundle", create=True), \
             patch.object(setup.subprocess, "run", return_value=ok) as run:
            setup.run_task_script("Never created", "Stop")
        self.assertIn(str(Path("C:/isolated-test-bundle/install-task.ps1")), run.call_args.args[0])


class PackageScriptTests(unittest.TestCase):
    def test_installer_upgrades_existing_config_without_running_setup_wizard(self):
        script = (ROOT / "windows_agent/pcpowerfree-installer.nsi").read_text(encoding="utf-8")
        install = script.split('Section "Install"', 1)[1].split("SectionEnd", 1)[0]
        self.assertIn('--upgrade-existing', install)
        self.assertNotIn('Delete "$APPDATA', install)
        task = (ROOT / "windows_agent/install-task.ps1").read_text(encoding="utf-8")
        self.assertIn('$Mode -eq "Upgrade"', task)
        self.assertIn('$existing.State -eq "Disabled"', task)

    def test_task_is_unlimited_and_recovers(self):
        script = (ROOT / "windows_agent/install-task.ps1").read_text(encoding="utf-8")
        self.assertIn("-ExecutionTimeLimit ([TimeSpan]::Zero)", script)
        self.assertIn("-AllowStartIfOnBatteries", script)
        self.assertIn("-RestartCount 3", script)

    def test_uninstaller_stops_agent_before_deleting_task(self):
        script = (ROOT / "windows_agent/pcpowerfree-installer.nsi").read_text(encoding="utf-8")
        uninstall = script.split('Section "Uninstall"', 1)[1]
        self.assertIn('/End /TN "PC Power Agent"', uninstall)
        self.assertLess(uninstall.index('/End /TN'), uninstall.index('/Delete /TN'))
        self.assertIn('agent-key.pem', uninstall)

    def test_dsm_generation_error_propagates(self):
        shell = shutil.which("sh") or r"C:\Program Files\Git\usr\bin\sh.exe"
        if not Path(shell).exists():
            self.skipTest("POSIX shell not available")
        script = (ROOT / "dsm_package/payload/dsm_runtime/init.sh").read_text(encoding="utf-8")
        fragment = script[script.index("ensure_config() {"):]
        variables = ('fail() { exit 1; }; PYTHON_BIN=false; CONFIG_PATH=/nonexistent-test/config.json; '
                     'APP_ROOT=/nonexistent-test; SUMMARY_PATH=/dev/null;\n')
        result = subprocess.run([shell, "-c", variables + fragment], capture_output=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
