"""Current branding and beginner documentation stay aligned."""

from pathlib import Path
import json
import re
import struct
import sys
import unittest
from urllib.parse import parse_qs, unquote, urlsplit

from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
CURRENT_GUIDES = [ROOT / "README.md", ROOT / "linux_agent/README.md",
                  ROOT / "dsm_package/README.md", *(ROOT / "docs" / name for name in (
    "README.md", "README.es.md", "HISTORY.md", "HACS_PUBLISHING.md", "KNOWN_ISSUES.md",
    *(f"{name}.{language}.md" for name in (
        "GETTING_STARTED", "INSTALL_UBUNTU", "INSTALL_DSM", "ALEXA", "HELP")
      for language in ("en", "es"))))]


def markdown_text(page):
    return re.sub(r"(?ms)^```[^\n]*\n.*?^```[ \t]*$", "", page.read_text(encoding="utf-8"))


def anchors(text):
    result = set(re.findall(r'<a\s+id="([^"]+)"', text))
    counts = {}
    for heading in re.findall(r"(?m)^#{1,6} (.+)$", text):
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        result.add(f"{slug}-{count}" if count else slug)
        counts[slug] = count + 1
    return result


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

    def test_covers_show_logo_and_install_guides_link_to_the_correct_hacs_repository(self):
        covers = [ROOT / "README.md", ROOT / "docs/README.es.md"]
        for page in covers:
            self.assertIn("/main/custom_components/pc_power_free/brand/logo.png", markdown_text(page))
        for page in covers + [ROOT / "docs" / f"{guide}.{language}.md"
                              for guide in ("GETTING_STARTED", "INSTALL_UBUNTU", "INSTALL_DSM")
                              for language in ("en", "es")]:
            links = re.findall(r"\]\((https://my\.home-assistant\.io/redirect/hacs_repository/\?[^)]+)\)",
                               markdown_text(page))
            with self.subTest(page=page.name):
                self.assertEqual(len(links), 1)
                self.assertEqual(parse_qs(urlsplit(links[0]).query), {
                    "owner": ["slx612"], "repository": ["WOL-Home-Assistant-And-Alexa"],
                    "category": ["integration"]})
                self.assertIn("https://my.home-assistant.io/badges/hacs_repository.svg", markdown_text(page))

    def test_both_alexa_guides_disclose_external_dependency_and_untested_status(self):
        for language in ("en", "es"):
            text = (ROOT / "docs" / f"ALEXA.{language}.md").read_text(encoding="utf-8")
            with self.subTest(language=language):
                self.assertIn("matterbridge-hass", text)
                self.assertIn("Matterbridge", text)
                self.assertIn("Echo", text)
                self.assertIn("Whitelist", text)
                self.assertIn("token", text.lower())

    def test_alexa_wizard_uses_the_same_label_filter_as_current_guides(self):
        for name in ("strings.json", "translations/en.json", "translations/es.json"):
            source = ROOT / "custom_components/pc_power_free" / name
            steps = json.loads(source.read_text(encoding="utf-8"))["options"]["step"]
            with self.subTest(source=name):
                self.assertIn("Filter By Label", steps["alexa_filter"]["description"])
                self.assertNotIn("Split Entities", steps["alexa_filter"]["description"])

    def test_current_local_documentation_links_resolve(self):
        for page in CURRENT_GUIDES:
            for target in re.findall(r"\]\(([^)]+)\)", markdown_text(page)):
                if target.startswith(("https://", "http://")):
                    continue
                path, _, fragment = unquote(target).partition("#")
                destination = page.parent / path if path else page
                with self.subTest(page=page.name, target=target):
                    self.assertTrue(destination.exists())
                    if destination.is_file() and fragment:
                        self.assertIn(fragment, anchors(markdown_text(destination)))

    def test_documentation_inventory_is_current_or_explicitly_historical(self):
        current = set(CURRENT_GUIDES)
        history = markdown_text(ROOT / "docs/HISTORY.md")
        for page in (ROOT / "docs").rglob("*.md"):
            if page in current:
                continue
            with self.subTest(page=page.name):
                self.assertIn("Historical record / Registro", page.read_text(encoding="utf-8")[:600])
                self.assertIn(page.relative_to(ROOT / "docs").as_posix(), history)

    def test_screenshot_languages_match_each_user_guide(self):
        for language in ("en", "es"):
            for guide in ("ALEXA", "INSTALL_DSM"):
                page = ROOT / "docs" / f"{guide}.{language}.md"
                images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown_text(page))
                self.assertTrue(images, page.name)
                for target in images:
                    name = Path(target).name
                    with self.subTest(page=page.name, image=name):
                        if name.startswith(("ha-", "entity-")):
                            self.assertEqual(name.endswith("-en.png"), language == "en")
                        if "images/dsm/" in target:
                            self.assertTrue(name.endswith(f".{language}.jpg"))

    def test_bundled_brand_pngs_have_icon_and_logo_dimensions(self):
        brand = ROOT / "custom_components/pc_power_free/brand"
        icon = (brand / "icon.png").read_bytes()
        self.assertEqual(icon[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", icon[16:24]), (256, 256))
        logo = (brand / "logo.png").read_bytes()
        self.assertEqual(logo[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", logo[16:24]), (720, 256))


if __name__ == "__main__":
    unittest.main()
