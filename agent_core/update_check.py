"""Stdlib-only release checking shared by the desktop agents."""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
import ssl
from urllib import error as urllib_error
from urllib import request as urllib_request

GITHUB_REPO_URL = "https://github.com/slx612/WOL-Home-Assistant-And-Alexa"
GITHUB_RELEASES_API_URL = (
    "https://api.github.com/repos/slx612/WOL-Home-Assistant-And-Alexa/releases?per_page=100"
)
WINDOWS_INSTALLER_NAME = "pcpowerfree-windows-x64-setup.exe"
MAX_RELEASE_PAGES = 5
VERSION_REGEX = re.compile(
    r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:[-.]?(?P<stage>alpha|beta|rc)(?:[.-]?(?P<stage_number>\d+))?)?$",
    re.IGNORECASE,
)


@dataclass(slots=True)
class GitHubRelease:
    """A published version with a complete platform installer asset."""

    version: str
    html_url: str
    name: str
    installer_url: str = ""
    installer_size: int = 0
    installer_sha256: str = ""


def normalize_version_text(version: str) -> str:
    return version.strip().lower().removeprefix("v")


def parse_version_key(version: str) -> tuple[int, int, int, int, int] | None:
    """Order alpha < beta < rc < stable, with numeric prerelease suffixes."""
    match = VERSION_REGEX.fullmatch(normalize_version_text(version))
    if match is None:
        return None
    stage = match.group("stage")
    return (
        int(match.group("major")), int(match.group("minor")), int(match.group("patch")),
        {"alpha": 0, "beta": 1, "rc": 2, None: 3}[stage.lower() if stage else None],
        int(match.group("stage_number") or 0),
    )


def is_newer_version(candidate: str, current: str) -> bool:
    """Compare supported versions; never guess an upgrade for unknown versions."""
    candidate_key, current_key = parse_version_key(candidate), parse_version_key(current)
    if candidate_key is None or current_key is None:
        raise ValueError(f"Cannot compare version {candidate!r} with installed version {current!r}")
    return candidate_key > current_key


def format_update_error(err: Exception) -> str:
    """Describe network failures without hiding their cause or suggesting insecure TLS."""
    if isinstance(err, urllib_error.HTTPError):
        headers = err.headers or {}
        if err.code == 429 or (err.code == 403 and headers.get("X-RateLimit-Remaining") == "0"):
            return f"GitHub rate limit reached (HTTP {err.code}). Please try again later."
        if err.code == 403:
            return "GitHub refused the request (HTTP 403). Check network restrictions or try again later."
        if err.code == 404:
            return "GitHub releases could not be found (HTTP 404). Please try again later."
        return f"GitHub HTTP {err.code}. Please try again later."
    reason = err.reason if isinstance(err, urllib_error.URLError) else err
    if isinstance(reason, TimeoutError):
        return "The update request timed out. Check your internet connection and try again."
    if isinstance(reason, ssl.SSLError):
        return f"Could not verify the secure GitHub connection. Check your clock or network: {reason}"
    if isinstance(err, urllib_error.URLError):
        return f"Could not connect to GitHub. Check your internet connection: {reason}"
    return str(err) or err.__class__.__name__


def fetch_latest_github_release(timeout: float = 5, *, platform: str = "windows",
                               include_prereleases: bool = True) -> GitHubRelease:
    """Return the highest installable version, including prereleases.

    Each HTTP operation has a timeout. Scan at most five pages (500 releases),
    failing explicitly rather than calling an incomplete result 'latest'.
    Installer availability is checked from GitHub's uploaded-asset metadata;
    this function never downloads or executes an installer.
    """
    if platform not in ("windows", "ubuntu"):
        raise ValueError("Unsupported installer platform")
    ranked: list[tuple[tuple[int, int, int, int, int], GitHubRelease]] = []
    for page in range(1, MAX_RELEASE_PAGES + 1):
        request = urllib_request.Request(
            f"{GITHUB_RELEASES_API_URL}&page={page}",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "WakeLink-Updater"},
        )
        with urllib_request.urlopen(request, timeout=timeout) as response:
            try:
                payload = json.loads(response.read().decode("utf-8"))
            except (ValueError, UnicodeError) as err:
                raise RuntimeError("GitHub returned invalid JSON. Please try again later.") from err
            more = 'rel="next"' in response.headers.get("Link", "")
        if not isinstance(payload, list):
            raise RuntimeError("GitHub returned an invalid response")

        for item in payload:
            if not isinstance(item, dict) or item.get("draft"):
                continue
            tag = item.get("tag_name") or item.get("name") or ""
            if not isinstance(tag, str):
                continue
            version_key = parse_version_key(tag)
            if version_key is None:
                continue
            if not include_prereleases and (version_key[3] < 3 or item.get("prerelease")):
                continue
            html_url = f"{GITHUB_REPO_URL}/releases/tag/{tag}"
            if item.get("html_url") != html_url:
                continue
            assets = item.get("assets")
            if not isinstance(assets, list):
                continue
            installer_name = (WINDOWS_INSTALLER_NAME if platform == "windows"
                              else f"WakeLink-Ubuntu-{normalize_version_text(tag)}.deb")
            installer_url = f"{GITHUB_REPO_URL}/releases/download/{tag}/{installer_name}"
            for asset in assets:
                if (isinstance(asset, dict)
                        and asset.get("name") == installer_name
                        and asset.get("state") == "uploaded"
                        and type(asset.get("size")) is int and asset["size"] > 0
                        and asset.get("browser_download_url") == installer_url):
                    digest = asset.get("digest", "")
                    checksum = (digest[7:] if isinstance(digest, str)
                                and re.fullmatch(r"sha256:[0-9a-f]{64}", digest) else "")
                    if platform == "ubuntu" and (not checksum or asset["size"] > 200_000_000):
                        continue
                    ranked.append((version_key, GitHubRelease(
                        normalize_version_text(tag), html_url,
                        str(item.get("name") or tag), installer_url, asset["size"], checksum,
                    )))
                    break
        if not more:
            break
    else:
        raise RuntimeError("GitHub returned too many release pages. Open the releases page to check manually.")

    if not ranked:
        label = "Windows" if platform == "windows" else "Ubuntu"
        raise RuntimeError(f"No published release with an uploaded {label} installer was found. Try again later.")
    return max(ranked, key=lambda entry: entry[0])[1]
