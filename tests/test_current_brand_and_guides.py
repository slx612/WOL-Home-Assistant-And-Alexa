"""Current branding and beginner documentation stay aligned."""

from pathlib import Path
import re
import sys
import unittest

from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class CurrentBrandAndGuideTests(unittest.TestCase):
    def test_home_assistant_icon_uses_windows_symbol(self):
        if sys.platform != "win32":
            self.skipTest("Pillow is installed only for Windows desktop tests")
        from PIL import Image
        with Image.open(ROOT / "windows_agent/assets/wakelink.ico") as source:
            expected = source.convert("RGBA").resize((256, 256))
        with Image.open(ROOT / "custom_components/pc_power_free/brand/icon.png") as actual:
            self.assertEqual(actual.convert("RGBA").tobytes(), expected.tobytes())

    def test_tray_reuses_bundled_windows_icon(self):
        source = (ROOT / "windows_agent/pc_power_tray.py").read_text(encoding="utf-8")
        build = (ROOT / "windows_agent/build-exe.ps1").read_text(encoding="utf-8")
        self.assertIn("wakelink.ico", source)
        self.assertIn('"assets/wakelink.ico;assets"', build)

    def test_tray_only_adds_a_status_dot_to_the_shared_symbol(self):
        if sys.platform != "win32":
            self.skipTest("Pillow and pystray are installed only for Windows desktop tests")
        from PIL import Image, ImageDraw
        sys.path.insert(0, str(ROOT / "windows_agent"))
        from pc_power_tray import build_tray_image
        import pc_power_tray
        with Image.open(ROOT / "windows_agent/assets/wakelink.ico") as source:
            base = source.convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
        with patch.object(pc_power_tray, "Image", Image), patch.object(pc_power_tray, "ImageDraw", ImageDraw):
            normal = build_tray_image(mode="allow", available=True)
            protected = build_tray_image(mode="ignore_manual", available=True)
        self.assertEqual(normal.crop((0, 0, 40, 40)).tobytes(), base.crop((0, 0, 40, 40)).tobytes())
        self.assertNotEqual(normal.getpixel((52, 52)), protected.getpixel((52, 52)))

    def test_current_english_and_spanish_guides_are_linked(self):
        for page in ("README.md", "docs/README.es.md"):
            text = (ROOT / page).read_text(encoding="utf-8")
            self.assertIn("GETTING_STARTED", text)
            self.assertIn("ALEXA", text)
            self.assertIn("WakeLink-Windows-x64-Setup.exe", text)
            self.assertNotIn("install PC Power Free from HACS", text)
        for page in ("GETTING_STARTED.en.md", "GETTING_STARTED.es.md",
                     "ALEXA.en.md", "ALEXA.es.md"):
            self.assertTrue((ROOT / "docs" / page).exists(), page)

    def test_windows_pairing_copy_uses_wakelink(self):
        text = (ROOT / "windows_agent/desktop_ui.py").read_text(encoding="utf-8")
        self.assertNotIn("install PC Power Free from HACS", text)
        self.assertNotIn("instala PC Power Free desde HACS", text)

    def test_both_alexa_guides_disclose_external_dependency_and_untested_status(self):
        for language in ("en", "es"):
            text = (ROOT / "docs" / f"ALEXA.{language}.md").read_text(encoding="utf-8")
            with self.subTest(language=language):
                self.assertIn("matterbridge-hass", text)
                self.assertIn("Matterbridge", text)
                self.assertIn("Echo", text)
                self.assertIn("Whitelist", text)
                self.assertIn("token", text.lower())

    def test_current_local_documentation_links_resolve(self):
        pages = [ROOT / "README.md", *(ROOT / "docs" / name for name in (
            "README.md", "README.es.md", "GETTING_STARTED.en.md", "GETTING_STARTED.es.md",
            "ALEXA.en.md", "ALEXA.es.md"))]
        for page in pages:
            for target in re.findall(r"\]\(([^)]+)\)", page.read_text(encoding="utf-8")):
                if target.startswith(("https://", "http://", "#")):
                    continue
                path = target.split("#", 1)[0]
                with self.subTest(page=page.name, target=target):
                    self.assertTrue((page.parent / path).exists())


if __name__ == "__main__":
    unittest.main()
