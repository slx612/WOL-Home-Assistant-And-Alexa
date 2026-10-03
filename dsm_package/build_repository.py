"""Generate a DSM Package Center catalog from the exact released SPK."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile
from urllib.parse import urlsplit

REPOSITORY = "https://github.com/slx612/WOL-Home-Assistant-And-Alexa"
ICON = "https://raw.githubusercontent.com/slx612/WOL-Home-Assistant-And-Alexa/main/custom_components/pc_power_free/brand/icon.png"


def build_catalog(package: Path, download_url: str) -> dict:
    location = urlsplit(download_url)
    if (location.scheme != "https" or location.netloc != "github.com"
            or not download_url.startswith(REPOSITORY + "/releases/download/")
            or location.query or location.fragment
            or location.path.rsplit("/", 1)[-1] != package.name):
        raise ValueError("Use this SPK's exact official GitHub release download URL")
    with tarfile.open(package, "r:*") as archive:
        info = archive.extractfile("INFO")
        if info is None:
            raise ValueError("The SPK has no INFO metadata")
        fields = dict(re.findall(r'^([a-z_]+)="([^"\n]*)"\s*$', info.read().decode(), re.M))
    if fields.get("package") != "pcpowerfree" or fields.get("arch") != "noarch":
        raise ValueError("Expected WakeLink's noarch DSM package")
    version = fields.get("version", "")
    if not re.fullmatch(r"\d+\.\d+\.\d+-\d{4}", version):
        raise ValueError("Unsupported DSM package version")
    if package.name != f"pcpowerfree-dsm-noarch-{version}.spk":
        raise ValueError("The SPK filename does not match its package version")
    content = package.read_bytes()
    return {"packages": [{
        "package": "pcpowerfree", "version": version, "dname": "WakeLink",
        "desc": fields["description"], "link": download_url,
        "thumbnail": [ICON, ICON], "thumbnail_retina": [ICON, ICON],
        # DSM must show its normal third-party/license confirmation, also on updates.
        "qinst": False, "qupgrade": False, "qstart": False, "startable": "yes",
        "deppkgs": None, "conflictpkgs": None, "snapshot": [],
        "download_count": 0, "recent_download_count": 0,
        "maintainer": fields["maintainer"], "maintainer_url": REPOSITORY,
        "distributor": "WakeLink", "distributor_url": REPOSITORY,
        "md5": hashlib.md5(content, usedforsecurity=False).hexdigest(),
        "size": len(content), "os_min_ver": fields["os_min_ver"],
        "changelog": "WakeLink update. Existing pairing and TLS identity are preserved.",
    }]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("download_url")
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    arguments.output.write_text(json.dumps(build_catalog(arguments.package, arguments.download_url),
                                          indent=2) + "\n", encoding="utf-8")
