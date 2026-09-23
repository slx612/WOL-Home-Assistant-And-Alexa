"""Updater regressions: fake HTTP and native dialogs, temporary cache only."""
from contextlib import ExitStack
import importlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "windows_agent"))
# Import without a display server, Pillow, or Windows shell integration in CI.
with patch.dict(sys.modules, {
    "PIL": types.SimpleNamespace(Image=Mock(), ImageDraw=Mock()),
    "pystray": Mock(),
}):
    tray = importlib.import_module("pc_power_tray")

REPO_URL = "https://github.com/slx612/WOL-Home-Assistant-And-Alexa"
INSTALLER = "pcpowerfree-windows-x64-setup.exe"


def release(version="0.2.0-beta.7", **changes):
    tag = "v" + version
    result = {
        "tag_name": tag, "name": "WakeLink " + version,
        "html_url": f"{REPO_URL}/releases/tag/{tag}",
        "draft": False, "prerelease": "-" in version,
        "assets": [{
            "name": INSTALLER, "state": "uploaded", "size": 55756339,
            "browser_download_url": f"{REPO_URL}/releases/download/{tag}/{INSTALLER}",
        }],
    }
    result.update(changes)
    return result


def response(payload, *, more=False):
    result = io.BytesIO(json.dumps(payload).encode("utf-8"))
    result.headers = {"Link": '<https://api.github.com/releases?page=2>; rel="next"'} if more else {}
    return result


class ReleaseSelectionTests(unittest.TestCase):
    def fetch(self, payload):
        with patch.object(tray.urllib_request, "urlopen", return_value=response(payload)):
            return tray.fetch_latest_github_release()

    def test_beta7_is_newer_than_beta5_and_numeric_prereleases_sort_correctly(self):
        for candidate, current, expected in [
            ("v0.2.0-beta.7", "0.2.0-beta.5", True),
            ("0.2.0-beta.10", "0.2.0-beta.9", True),
            ("0.2.0-beta.7", "v0.2.0-beta.7", False),
            ("0.2.0-beta.6", "0.2.0-beta.7", False),
            ("0.2.0", "0.2.0-rc.9", True),
            ("0.2.0-beta.9", "0.2.0", False),
        ]:
            with self.subTest(candidate=candidate, current=current):
                self.assertEqual(tray.is_newer_version(candidate, current), expected)

    def test_invalid_versions_are_not_guessed_to_be_updates(self):
        for candidate, current in [("nightly", "0.2.0"), ("0.2.0", "unknown")]:
            with self.subTest(candidate=candidate, current=current):
                with self.assertRaisesRegex(ValueError, "version"):
                    tray.is_newer_version(candidate, current)

    def test_highest_version_wins_not_github_order_and_prereleases_are_included(self):
        result = self.fetch([
            release("0.2.0-beta.5"), release("0.2.0-beta.10"),
            release("0.2.0-beta.7"), release("0.3.0", draft=True),
            release("nightly"), None,
        ])
        self.assertEqual(result.version, "0.2.0-beta.10")

    def test_release_without_installer_is_skipped_for_latest_installable_release(self):
        result = self.fetch([release("0.3.0", assets=[]), release()])
        self.assertEqual(result.version, "0.2.0-beta.7")

    def test_incomplete_or_untrusted_installer_is_not_offered(self):
        for changes in [
            {"name": "PCPowerAgent.exe"}, {"name": "PCPowerSetup.exe"},
            {"state": "new"}, {"size": 0}, {"size": "large"},
            {"browser_download_url": ""},
            {"browser_download_url": "http://github.com/file.exe"},
            {"browser_download_url": "https://example.com/file.exe"},
        ]:
            with self.subTest(changes=changes):
                bad = release("0.3.0")
                bad["assets"][0].update(changes)
                self.assertEqual(self.fetch([bad, release()]).version, "0.2.0-beta.7")

    def test_invalid_release_page_is_not_offered(self):
        for url in ["", "file:///C:/bad.exe", "https://example.com/release"]:
            with self.subTest(url=url):
                self.assertEqual(self.fetch([release("0.3.0", html_url=url), release()]).version,
                                 "0.2.0-beta.7")

    def test_no_usable_installer_is_an_error_not_up_to_date(self):
        for payload in [[], [release(assets=[])], [release(assets=None)]]:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(RuntimeError, "Windows installer"):
                    self.fetch(payload)

    def test_result_exposes_validated_installer_url_to_both_windows_interfaces(self):
        result = self.fetch([release()])
        self.assertEqual(getattr(result, "installer_url", None),
                         f"{REPO_URL}/releases/download/v0.2.0-beta.7/{INSTALLER}")

    def test_next_page_is_checked_before_choosing_latest(self):
        with patch.object(tray.urllib_request, "urlopen", side_effect=[
            response([release("0.2.0-beta.5")], more=True), response([release()]),
        ]) as fetch:
            self.assertEqual(tray.fetch_latest_github_release(timeout=3).version, "0.2.0-beta.7")
        self.assertEqual(fetch.call_count, 2)
        for call in fetch.call_args_list:
            self.assertEqual(call.kwargs["timeout"], 3)
            self.assertIn("api.github.com/repos/slx612/", call.args[0].full_url)

    def test_network_request_has_timeout_and_identifies_client(self):
        with patch.object(tray.urllib_request, "urlopen", return_value=response([release()])) as fetch:
            tray.fetch_latest_github_release(timeout=3)
        self.assertEqual(fetch.call_args.kwargs["timeout"], 3)
        self.assertTrue(fetch.call_args.args[0].get_header("User-agent"))

    def test_pagination_is_bounded_and_incomplete_results_are_not_reported_as_latest(self):
        def endless_pages(*args, **kwargs):
            return response([release()], more=True)
        with patch.object(tray.urllib_request, "urlopen", side_effect=endless_pages) as fetch:
            with self.assertRaisesRegex(RuntimeError, "too many release pages"):
                tray.fetch_latest_github_release()
        self.assertLessEqual(fetch.call_count, 5)

    def test_malformed_response_is_reported_clearly(self):
        with self.assertRaisesRegex(RuntimeError, "invalid response"):
            self.fetch({"message": "Unexpected API response"})
        with patch.object(tray.urllib_request, "urlopen", return_value=io.BytesIO(b"<html>oops")):
            with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
                tray.fetch_latest_github_release()

    def test_rate_limit_and_timeout_errors_are_actionable(self):
        err = HTTPError("https://api.github.com", 403, "Forbidden", {"X-RateLimit-Remaining": "0"}, None)
        self.assertIn("rate limit", tray.format_update_error(err).lower())
        for err in [TimeoutError(), URLError(TimeoutError())]:
            with self.subTest(error=err):
                self.assertIn("timed out", tray.format_update_error(err).lower())
                self.assertIn("try again", tray.format_update_error(err).lower())

    def test_connection_error_explains_what_to_check(self):
        self.assertIn("connection", tray.format_update_error(URLError("offline")).lower())


class TrayUpdateTests(unittest.TestCase):
    def setUp(self):
        self.stack = self.enterContext(ExitStack())
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.stack.enter_context(patch.dict(os.environ, {
            "LOCALAPPDATA": str(self.directory / "user"), "APPDATA": str(self.directory / "roaming"),
        }))
        self.stack.enter_context(patch.object(tray, "resolve_language", return_value="en"))
        self.stack.enter_context(patch.object(tray.pystray, "Icon", return_value=Mock()))
        self.app = tray.TrayApp(self.directory / "machine" / "config.json")
        self.stack.enter_context(patch.object(tray, "APP_VERSION", "0.2.0-beta.5"))
        self.stack.enter_context(patch.object(tray, "UPDATE_CHECK_STARTUP_DELAY_SECONDS", 0))
        self.dialog = self.stack.enter_context(patch.object(
            tray.ctypes, "windll", types.SimpleNamespace(user32=Mock()), create=True,
        )).user32.MessageBoxW
        self.dialog.return_value = 7  # No, never launch the actual browser.
        self.browser = self.stack.enter_context(patch.object(tray.webbrowser, "open", return_value=True))
        self.fetch = self.stack.enter_context(patch.object(
            tray.urllib_request, "urlopen", return_value=response([release("0.2.0-beta.5")]),
        ))

    def assert_dialog_contains(self, *texts):
        self.assertTrue(self.dialog.called, "Manual results must use a visible native dialog")
        message = self.dialog.call_args.args[1]
        for text in texts:
            self.assertIn(text.lower(), message.lower())

    def test_manual_up_to_date_result_is_a_dialog_not_a_notification(self):
        self.app._update_check_worker(manual=True)
        self.assert_dialog_contains("WakeLink", "0.2.0-beta.5")
        self.assertFalse(self.app._update_check_in_progress)

    def test_manual_network_error_is_visible_and_releases_busy_state(self):
        self.fetch.side_effect = URLError("offline")
        self.app._update_check_in_progress = True
        self.app._update_check_worker(manual=True)
        self.assert_dialog_contains("offline")
        self.assertFalse(self.app._update_check_in_progress)

    def test_beta5_to_beta7_prompts_even_if_cache_write_is_denied(self):
        self.fetch.return_value = response([release()])
        with patch.object(Path, "write_text", side_effect=PermissionError("Access denied")):
            self.app._update_check_worker(manual=True)
        self.assert_dialog_contains("0.2.0-beta.5", "0.2.0-beta.7")

    def test_unwritable_cache_does_not_turn_up_to_date_into_failure(self):
        with patch.object(Path, "write_text", side_effect=PermissionError("Access denied")):
            self.app._update_check_worker(manual=True)
        self.assert_dialog_contains("0.2.0-beta.5")
        self.assertNotIn("Access denied", self.dialog.call_args.args[1])

    def test_cache_is_per_user_not_next_to_machine_config(self):
        self.assertEqual(self.app._update_state_path,
                         self.directory / "user" / "PC Power Free" / "update_state.json")

    def test_automatic_same_version_never_displays_dialog_or_notification(self):
        self.app._update_check_worker(manual=False)
        self.dialog.assert_not_called()
        self.app._icon.notify.assert_not_called()

    def test_automatic_errors_are_quiet(self):
        self.fetch.side_effect = TimeoutError()
        self.app._update_check_worker(manual=False)
        self.dialog.assert_not_called()
        self.app._icon.notify.assert_not_called()

    def test_automatic_new_release_prompts_once_and_manual_bypasses_cache(self):
        self.fetch.side_effect = [response([release()]) for _ in range(3)]
        self.app._update_check_worker(manual=False)
        self.dialog.assert_called_once()
        with patch.object(self.app, "_should_auto_check_updates", return_value=True):
            self.app._update_check_worker(manual=False)
        self.dialog.assert_called_once()
        self.app._update_check_worker(manual=True)
        self.assertEqual(self.dialog.call_count, 2)

    def test_manual_busy_check_is_visibly_acknowledged(self):
        self.app._update_check_in_progress = True
        self.app._start_update_check(manual=True)
        self.assert_dialog_contains("progress")

    def test_manual_click_during_automatic_fetch_gets_visible_final_result(self):
        def during_fetch(*args, **kwargs):
            self.app._update_check_in_progress = True
            self.app._start_update_check(manual=True)
            self.dialog.reset_mock()
            return response([release("0.2.0-beta.5")])
        self.fetch.side_effect = during_fetch
        self.app._update_check_worker(manual=False)
        self.assert_dialog_contains("0.2.0-beta.5")

    def test_manual_click_during_throttle_lookup_is_not_discarded(self):
        def during_cache_read():
            self.app._update_check_in_progress = True
            self.app._start_update_check(manual=True)
            self.dialog.reset_mock()
            return False
        with patch.object(self.app, "_should_auto_check_updates", side_effect=during_cache_read):
            self.app._update_check_worker(manual=False)
        self.assert_dialog_contains("0.2.0-beta.5")

    def test_manual_click_during_result_comparison_is_not_discarded(self):
        def during_comparison(candidate, current):
            self.app._update_check_in_progress = True
            self.app._start_update_check(manual=True)
            self.dialog.reset_mock()
            return False
        with patch.object(tray, "is_newer_version", side_effect=during_comparison):
            self.app._update_check_worker(manual=False)
        self.assert_dialog_contains("0.2.0-beta.5")

    def test_browser_launch_failure_is_visible_after_accepting_update(self):
        self.fetch.return_value = response([release()])
        self.dialog.return_value = 6
        self.browser.return_value = False
        self.app._update_check_worker(manual=True)
        self.assertEqual(self.dialog.call_count, 2)
        self.assert_dialog_contains("browser", REPO_URL)

    def test_accepting_update_opens_validated_installer_download(self):
        self.fetch.return_value = response([release()])
        self.dialog.return_value = 6
        self.app._update_check_worker(manual=True)
        self.browser.assert_called_once_with(
            f"{REPO_URL}/releases/download/v0.2.0-beta.7/{INSTALLER}")

    def test_thread_start_failure_is_visible_and_allows_retry(self):
        with patch.object(tray.threading.Thread, "start", side_effect=RuntimeError("worker unavailable")):
            try:
                self.app._start_update_check(manual=True)
            except RuntimeError:
                self.fail("Worker startup errors must not escape the tray callback")
        self.assert_dialog_contains("worker unavailable")
        self.assertFalse(self.app._update_check_in_progress)

    def test_shared_language_change_is_used_by_existing_tray(self):
        import ui_preferences
        # Keep the shared preference helper real, but all storage temporary.
        with patch.dict(os.environ, {"PC_POWER_FREE_PREFERENCES_DIR": str(self.directory)}), \
             patch.object(tray, "resolve_language", wraps=ui_preferences.load_language):
            ui_preferences.save_language("es")
            self.app._update_check_worker(manual=True)
        self.assert_dialog_contains("WakeLink", "version", "0.2.0-beta.5")
        self.assertNotIn("up to date", self.dialog.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
