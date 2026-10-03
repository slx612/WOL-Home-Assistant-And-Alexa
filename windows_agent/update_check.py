"""Compatibility imports for existing Windows installers and callers."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_core.update_check import (
    GITHUB_REPO_URL, GITHUB_RELEASES_API_URL, WINDOWS_INSTALLER_NAME,
    MAX_RELEASE_PAGES, VERSION_REGEX, GitHubRelease, fetch_latest_github_release,
    format_update_error, is_newer_version, normalize_version_text, parse_version_key,
    urllib_request,
)
