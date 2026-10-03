"""Install only a verified Ubuntu package from WakeLink's official releases."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib import request
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_core.common import AGENT_VERSION
from agent_core.update_check import fetch_latest_github_release, is_newer_version


def install_update() -> None:
    if os.geteuid() != 0:
        raise PermissionError("Ubuntu administrator authorization is required.")
    release = fetch_latest_github_release(platform="ubuntu", include_prereleases="-" in AGENT_VERSION)
    if not is_newer_version(release.version, AGENT_VERSION):
        raise RuntimeError("No newer Ubuntu installer is available.")
    if not release.installer_sha256 or not 0 < release.installer_size <= 200_000_000:
        raise RuntimeError("The Ubuntu installer has no valid GitHub checksum or size.")
    with tempfile.TemporaryDirectory(prefix="wakelink-update-") as temporary:
        package = Path(temporary) / "wakelink.deb"
        digest = hashlib.sha256()
        size = 0
        with request.urlopen(release.installer_url, timeout=30) as response, package.open("wb") as output:
            location = urlsplit(response.url)
            if location.scheme != "https" or location.hostname not in (
                "github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com",
            ):
                raise RuntimeError("The installer download left GitHub's secure download hosts.")
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > release.installer_size:
                    raise RuntimeError("The installer exceeds its published size.")
                output.write(chunk)
                digest.update(chunk)
        if size != release.installer_size or digest.hexdigest() != release.installer_sha256:
            raise RuntimeError("The downloaded installer failed checksum verification.")
        metadata = subprocess.run(
            ["/usr/bin/dpkg-deb", "--field", str(package), "Package", "Version", "Architecture"],
            check=True, capture_output=True, text=True, timeout=30,
        ).stdout.splitlines()
        expected_version = release.version.replace("-beta.", "~beta")
        if metadata != ["Package: wakelink", f"Version: {expected_version}", "Architecture: all"]:
            raise RuntimeError("The installer is not the expected WakeLink Ubuntu package.")
        # apt's unprivileged download user needs to traverse this temporary directory.
        os.chmod(temporary, 0o755)
        # Never kill APT/dpkg mid-transaction; Ubuntu owns the installation lifecycle.
        subprocess.run(["/usr/bin/apt-get", "-y", "install", str(package)], check=True)


if __name__ == "__main__":
    try:
        install_update()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
