"""Guard the bilingual, read-only Matter onboarding copy."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components/pc_power_free"


class MatterGuideContentTests(unittest.TestCase):
    def test_guide_is_translated_and_uses_current_power_entity(self):
        for name in ("strings.json", "translations/en.json", "translations/es.json"):
            with self.subTest(name=name):
                data = json.loads((INTEGRATION / name).read_text(encoding="utf-8"))
                self.assertEqual(data["title"], "WakeLink")
                options = data["options"]
                self.assertEqual(set(options["step"]["init"]["menu_options"]), {"device", "alexa"})
                self.assertIn("{entity_id}", options["step"]["alexa_filter"]["description"])
                self.assertIn("guide_finished", options["abort"])
                self.assertIn("power_entity_missing", options["abort"])
                self.assertNotIn("{token}", json.dumps(options))
                plugin_text = options["step"]["alexa_plugin"]["description"]
                self.assertIn("wss://", plugin_text)
                self.assertIn("ws://", plugin_text)

    def test_hacs_installation_uses_new_visible_name(self):
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        spanish = (ROOT / "docs/README.es.md").read_text(encoding="utf-8")
        self.assertIn("search for `WakeLink`", english)
        self.assertIn("busca `WakeLink`", spanish)

    def test_ha_preview_does_not_change_integration_identity(self):
        manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
        hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["domain"], "pc_power_free")
        self.assertEqual(manifest["name"], "WakeLink")
        self.assertEqual(manifest["version"], "0.2.0-beta.11")
        self.assertEqual(hacs["name"], "WakeLink")


if __name__ == "__main__":
    unittest.main()
