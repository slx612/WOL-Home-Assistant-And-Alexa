"""Per-user UI preferences, separate from the agent's credentials."""
import json
import locale
import os
from pathlib import Path
import tempfile


def preferences_path() -> Path:
    override = os.environ.get("PC_POWER_FREE_PREFERENCES_DIR")
    directory = Path(override) if override else Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "WakeLink"
    return directory / "preferences.json"


def load_language() -> str:
    try:
        saved = json.loads(preferences_path().read_text(encoding="utf-8"))
        if isinstance(saved, dict) and saved.get("language") in ("en", "es"):
            return saved["language"]
    except (OSError, ValueError):
        pass
    return "es" if (locale.getlocale()[0] or "").lower().startswith("es") else "en"


def save_language(language: str) -> None:
    if language not in ("en", "es"):
        raise ValueError("Unsupported language")
    path = preferences_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"language": language}, stream)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
