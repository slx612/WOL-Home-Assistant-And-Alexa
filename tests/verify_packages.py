"""Verify built archives/Windows code without installing or executing power actions."""
import io
import json
import marshal
from pathlib import Path
import re
import tarfile
import types
import zipfile

from PyInstaller.archive.readers import CArchiveReader
import pefile

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {"config.json", "agent-key.pem", "agent-cert.pem", "guard_state.json"}


def signature(code):
    fields = ("co_code", "co_names", "co_varnames", "co_freevars", "co_cellvars",
              "co_argcount", "co_kwonlyargcount", "co_posonlyargcount", "co_flags")
    return tuple(getattr(code, field) for field in fields) + (tuple(
        signature(value) if isinstance(value, types.CodeType) else value
        for value in code.co_consts),)


def source_signature(path):
    return signature(compile(path.read_bytes(), str(path), "exec"))


def verify_sources(archive, prefix=""):
    checked = set()
    for member in archive.getmembers():
        name = member.name.removeprefix("./").removeprefix(prefix)
        assert Path(name).name not in FORBIDDEN, f"Private state included: {name}"
        if not member.isfile() or not name.startswith(("agent_core/", "linux_agent/")):
            continue
        path = ROOT / name
        assert archive.extractfile(member).read() == path.read_bytes(), name
        checked.add(name)
    assert "agent_core/tls.py" in checked
    return len(checked)


def main():
    results = {}
    with zipfile.ZipFile(ROOT / "release_assets/pcpowerfree-home-assistant-integration.zip") as archive:
        expected = {path.relative_to(ROOT).as_posix() for path in
                    (ROOT / "custom_components/pc_power_free").rglob("*")
                    if path.is_file() and "__pycache__" not in path.parts}
        found = set()
        for stored in archive.namelist():
            if stored.endswith("/"):
                continue
            name = stored.replace("\\", "/")
            assert name in expected, name
            assert archive.read(stored) == (ROOT / name).read_bytes(), name
            found.add(name)
        assert found == expected, sorted(expected - found)
        results["ha_files"] = len(found)

    with tarfile.open(ROOT / "release_assets/pcpowerfree-linux-agent.tar.gz") as archive:
        results["linux_files"] = verify_sources(archive)

    version = json.loads((ROOT / "custom_components/pc_power_free/manifest.json").read_text())["version"]
    base, beta = version.split("-beta.")
    spk = ROOT / f"dsm_package/dist/pcpowerfree-dsm-noarch-{base}-{int(beta):04}.spk"
    with tarfile.open(spk) as archive:
        payload = archive.extractfile("package.tgz").read()
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as inner:
            results["dsm_files"] = verify_sources(inner, "app/")
            for script in (ROOT / "dsm_package/payload/dsm_runtime").glob("*"):
                if script.is_file():
                    assert inner.extractfile(f"./app/dsm_runtime/{script.name}").read() == script.read_bytes()

    for exe, module in [("PCPowerAgent", "pc_power_agent"), ("PCPowerSetup", "setup_wizard_gui"),
                        ("PCPowerTray", "pc_power_tray")]:
        path = ROOT / f"windows_agent/dist/{exe}.exe"
        archive = CArchiveReader(str(path))
        assert signature(marshal.loads(archive.extract(module))) == source_signature(ROOT / f"windows_agent/{module}.py"), exe
        embedded = archive.open_embedded_archive("PYZ.pyz")
        for shared in ("common", "tls"):
            assert signature(embedded.extract(f"agent_core.{shared}")) == source_signature(ROOT / f"agent_core/{shared}.py"), (exe, shared)
        assert any("cryptography" in name and name.endswith(".pyd") for name in archive.toc), exe
        if exe == "PCPowerSetup":
            assert archive.extract("install-task.ps1") == (ROOT / "windows_agent/install-task.ps1").read_bytes()
        levels = []
        with pefile.PE(str(path)) as pe:
            for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
                if resource_type.id != 24:
                    continue
                for resource in resource_type.directory.entries:
                    for language in resource.directory.entries:
                        data = language.data.struct
                        xml = pe.get_data(data.OffsetToData, data.Size).decode("utf-8")
                        levels.extend(re.findall(r'requestedExecutionLevel[^>]*level="([^"]+)"', xml))
        assert levels == ["requireAdministrator" if exe == "PCPowerSetup" else "asInvoker"]
        results[exe] = "source/core/TLS match; crypto bundled; manifest checked"
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
