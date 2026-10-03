"""Native DSM lifecycle scripts must stop on backup/restore failures."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == "posix" and shutil.which("sh"), "POSIX shell required")
class DsmUpgradeFailureTests(unittest.TestCase):
    def test_failed_backup_restore_and_initialization_are_not_success(self):
        for stage in ("preupgrade", "postupgrade", "initialization"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                state = root / "state"
                backup = root / "upgrade/pcpowerfree-state"
                scripts = root / "package/scripts"
                binary = root / "bin"
                for path in (state, backup, scripts, binary):
                    path.mkdir(parents=True)
                original = b'original pairing and TLS state'
                (state / "config.json").write_bytes(original)
                (backup / "config.json").write_bytes(original)
                init = root / "package/target/app/dsm_runtime/init.sh"
                init.parent.mkdir(parents=True)
                init.write_text("#!/bin/sh\nexit 7\n" if stage == "initialization" else "#!/bin/sh\nexit 0\n")
                init.chmod(0o755)
                if stage != "initialization":
                    cp = binary / "cp"
                    cp.write_text('#!/bin/sh\nprintf partial > "$2"\nexit 1\n')
                    cp.chmod(0o755)
                script_name = "preupgrade" if stage == "preupgrade" else "postupgrade"
                script = scripts / script_name
                script.write_bytes((ROOT / "dsm_package/template/scripts" / script_name).read_bytes())
                result = subprocess.run(["sh", str(script)], capture_output=True, env={
                    **os.environ, "PATH": str(binary) + os.pathsep + os.environ["PATH"],
                    "SYNOPKG_PKGVAR": str(state), "SYNOPKG_TEMP_UPGRADE_FOLDER": str(root / "upgrade"),
                    "SYNOPKG_TEMP_LOGFILE": str(root / "install.log"),
                })
                self.assertNotEqual(result.returncode, 0, "Failed lifecycle stage reported success")
                self.assertEqual((state / "config.json").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
