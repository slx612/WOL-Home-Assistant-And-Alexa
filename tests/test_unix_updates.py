"""Ubuntu updates must be explicit, official and preserve existing pairing."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import queue
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import Mock, patch

from agent_core import update_check
from linux_agent import update_install
from dsm_package.build_repository import build_catalog

ROOT = Path(__file__).resolve().parents[1]


def download(content, url="https://release-assets.githubusercontent.com/package.deb"):
    response = io.BytesIO(content)
    response.url = url
    return response


class UbuntuUpdatesTests(unittest.TestCase):
    def setUp(self):
        version = patch.object(update_install, "AGENT_VERSION", "0.2.0-beta.12")
        version.start()
        self.addCleanup(version.stop)

    def test_selects_only_the_official_uploaded_ubuntu_asset(self):
        tag = "v0.2.0-beta.13"
        name = "WakeLink-Ubuntu-0.2.0-beta.13.deb"
        url = f"{update_check.GITHUB_REPO_URL}/releases/download/{tag}/{name}"
        response = io.BytesIO(json.dumps([{
            "tag_name": tag, "html_url": f"{update_check.GITHUB_REPO_URL}/releases/tag/{tag}",
            "assets": [{"name": name, "state": "uploaded", "size": 50,
                        "digest": "sha256:" + "a" * 64, "browser_download_url": url}],
        }]).encode())
        response.headers = {}
        with patch.object(update_check.urllib_request, "urlopen", return_value=response):
            release = update_check.fetch_latest_github_release(platform="ubuntu")
        self.assertEqual((release.version, release.installer_url, release.installer_sha256),
                         ("0.2.0-beta.13", url, "a" * 64))

    def test_stable_ubuntu_installations_do_not_offer_betas_or_unverifiable_assets(self):
        def entry(version, digest="sha256:" + "a" * 64):
            tag = "v" + version
            name = f"WakeLink-Ubuntu-{version}.deb"
            return {"tag_name": tag, "html_url": f"{update_check.GITHUB_REPO_URL}/releases/tag/{tag}",
                    "assets": [{"name": name, "state": "uploaded", "size": 50, "digest": digest,
                                "browser_download_url": f"{update_check.GITHUB_REPO_URL}/releases/download/{tag}/{name}"}]}
        response = io.BytesIO(json.dumps([entry("1.1.0-beta.1"), entry("1.0.1", ""), entry("1.0.0")]).encode())
        response.headers = {}
        with patch.object(update_check.urllib_request, "urlopen", return_value=response):
            result = update_check.fetch_latest_github_release(platform="ubuntu", include_prereleases=False)
        self.assertEqual(result.version, "1.0.0")

    def test_verified_package_uses_native_apt_without_touching_configuration(self):
        content = b"test deb contents"
        release = update_check.GitHubRelease(
            "0.2.0-beta.13", "", "", "https://github.com/package.deb", len(content),
            hashlib.sha256(content).hexdigest(),
        )
        metadata = "Package: wakelink\nVersion: 0.2.0~beta13\nArchitecture: all\n"
        with patch.object(update_install.os, "geteuid", return_value=0, create=True), \
                patch.object(update_install, "fetch_latest_github_release", return_value=release), \
                patch.object(update_install.request, "urlopen", return_value=download(content)), \
                patch.object(update_install.subprocess, "run", return_value=Mock(stdout=metadata)) as run:
            update_install.install_update()
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args.args[0][:3], ["/usr/bin/apt-get", "-y", "install"])
        self.assertNotIn("--allow-downgrades", run.call_args.args[0])

    def test_rejects_corruption_wrong_package_and_untrusted_download_before_apt(self):
        content = b"test deb contents"
        release = update_check.GitHubRelease("0.2.0-beta.13", "", "", "", len(content),
                                           hashlib.sha256(content).hexdigest())
        for body, url, metadata in (
            (b"wrong", "https://github.com/file", ""),
            (content, "http://github.com/file", ""),
            (content, "https://evil.example/file", ""),
            (content, "https://github.com/file", "Package: unrelated\nVersion: 1\nArchitecture: all\n"),
        ):
            with self.subTest(url=url, metadata=metadata), \
                    patch.object(update_install.os, "geteuid", return_value=0, create=True), \
                    patch.object(update_install, "fetch_latest_github_release", return_value=release), \
                    patch.object(update_install.request, "urlopen", return_value=download(body, url)), \
                    patch.object(update_install.subprocess, "run", return_value=Mock(stdout=metadata)) as run:
                with self.assertRaises(RuntimeError):
                    update_install.install_update()
                self.assertLessEqual(run.call_count, 1)

    def test_requires_authorization_and_refuses_missing_digest_or_downgrade(self):
        with patch.object(update_install.os, "geteuid", return_value=1000, create=True):
            with self.assertRaises(PermissionError):
                update_install.install_update()
        for release in (update_check.GitHubRelease("0.1.0", "", ""),
                        update_check.GitHubRelease("0.2.0-beta.13", "", "", "", 100)):
            with patch.object(update_install.os, "geteuid", return_value=0, create=True), \
                    patch.object(update_install, "fetch_latest_github_release", return_value=release):
                with self.assertRaises(RuntimeError):
                    update_install.install_update()

    def test_window_reports_network_failure_and_does_not_clear_pairing_code(self):
        spec = importlib.util.spec_from_file_location("linux_desktop_update_test", ROOT / "linux_agent/desktop_ui.py")
        ui = importlib.util.module_from_spec(spec)
        with patch.dict("sys.modules", {"network_info": Mock()}):
            spec.loader.exec_module(ui)
        ui.AGENT_VERSION = "0.2.0-beta.12"
        window = ui.WakeLinkWindow.__new__(ui.WakeLinkWindow)
        window.root = Mock()
        window.draw = Mock()
        window.results = queue.Queue()
        window.code = "123456"
        window.busy = False
        window.results.put(("check_updates", TimeoutError("offline")))
        window.poll()
        self.assertEqual(window.update_state, "update_error")
        self.assertFalse(window.checking_updates)
        self.assertEqual(window.code, "123456")
        window.results.put(("check_updates", update_check.GitHubRelease("0.2.0-beta.13", "", "")))
        window.poll()
        self.assertEqual(window.update_state, "available")
        window.results.put(("update", subprocess.CompletedProcess([], 1, "", "canceled")))
        window.language = "en"
        with patch.object(ui.messagebox, "showerror"):
            window.poll()
        self.assertEqual(window.code, "123456")
        window.root.destroy.assert_not_called()

    def test_stopped_agent_window_offers_translated_activation(self):
        spec = importlib.util.spec_from_file_location("linux_desktop_activation_test", ROOT / "linux_agent/desktop_ui.py")
        ui = importlib.util.module_from_spec(spec)
        with patch.dict("sys.modules", {"network_info": Mock()}):
            spec.loader.exec_module(ui)
        for language in ("en", "es"):
            window = ui.WakeLinkWindow.__new__(ui.WakeLinkWindow)
            window.root = Mock()
            window.root.winfo_children.return_value = []
            window.language = language
            window.latest_release = None
            window.update_state = "current"
            window.update_error = ""
            window.checking_updates = window.busy = False
            window.code = None
            window.network_summary = Mock(return_value="test network")
            window.start = Mock()
            with self.subTest(language=language), patch.object(ui, "agent_running", return_value=False), \
                    patch.multiple(ui.tk, Frame=Mock(), Label=Mock(), Canvas=Mock(), Scrollbar=Mock()), \
                    patch.object(ui.tk, "Button") as button:
                window.draw()
                activation = next(call.kwargs for call in button.call_args_list
                                  if call.kwargs.get("text") == ui.TEXT[language]["activate"])
                activation["command"]()
                window.start.assert_called_once_with("enable")


class DsmRepositoryTests(unittest.TestCase):
    def test_catalog_matches_spk_identity_and_rejects_unofficial_download(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "pcpowerfree-dsm-noarch-0.2.0-0023.spk"
            info = (ROOT / "dsm_package/template/INFO.in").read_text().replace(
                "@@DSM_PACKAGE_VERSION@@", "0.2.0-0023").replace("@@APP_VERSION@@", "0.2.0-beta.12").encode()
            with tarfile.open(package, "w") as archive:
                member = tarfile.TarInfo("INFO")
                member.size = len(info)
                archive.addfile(member, io.BytesIO(info))
            official = update_check.GITHUB_REPO_URL + "/releases/download/v0.2.0-beta.13/" + package.name
            entry = build_catalog(package, official)["packages"][0]
            self.assertEqual((entry["package"], entry["version"], entry["dname"]),
                             ("pcpowerfree", "0.2.0-0023", "WakeLink"))
            self.assertEqual(entry["md5"], hashlib.md5(package.read_bytes()).hexdigest())
            self.assertEqual(entry["size"], package.stat().st_size)
            self.assertFalse(entry["qupgrade"])
            for bad in ("http://example.com/file.spk", official + "?other=1", official.replace("0023", "0022")):
                with self.assertRaises(ValueError):
                    build_catalog(package, bad)


if __name__ == "__main__":
    unittest.main()
