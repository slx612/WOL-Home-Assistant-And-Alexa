"""One-time administrator grant for DSM's two normal power actions."""

import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

RULE_PATH = Path("/etc/sudoers.d/wakelink-power")
POWER_COMMAND = "/usr/syno/sbin/synoshutdown"
RULE = (
    "# WakeLink: normal NAS shutdown/restart only; no shell or arbitrary arguments.\n"
    "pcpowerfree ALL=(root) NOPASSWD: /usr/syno/sbin/synoshutdown --shutdown, "
    "/usr/syno/sbin/synoshutdown --reboot\n"
)


def configure(*, remove=False):
    if os.geteuid() != 0:
        raise RuntimeError("Run this one-time setup as a DSM administrator using sudo")
    if RULE_PATH.is_symlink():
        raise RuntimeError("Refusing to replace a symbolic link in sudoers.d")
    if RULE_PATH.exists() and RULE_PATH.read_text() != RULE:
        raise RuntimeError("An unfamiliar permission rule already exists; refusing to replace it")
    if remove:
        RULE_PATH.unlink(missing_ok=True)
        return
    if not Path("/var/packages/pcpowerfree/target").is_dir():
        raise RuntimeError("Install the WakeLink DSM package before granting power permission")
    binary = Path(POWER_COMMAND).stat()
    directory = RULE_PATH.parent.stat()
    if binary.st_uid != 0 or binary.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise RuntimeError("DSM's power command must be root-owned and not writable by other users")
    if directory.st_uid != 0 or directory.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise RuntimeError("sudoers.d must be root-owned and not writable by other users")
    existed = RULE_PATH.exists()
    fd, temporary = tempfile.mkstemp(prefix=".wakelink-", dir=RULE_PATH.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            os.fchmod(stream.fileno(), 0o440)
            stream.write(RULE)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, RULE_PATH)
        try:
            for flag in ("--shutdown", "--reboot"):
                subprocess.run(
                    ["/usr/bin/sudo", "-n", "-l", "-U", "pcpowerfree", POWER_COMMAND, flag],
                    check=True, capture_output=True, text=True, timeout=10,
                )
        except (OSError, subprocess.SubprocessError):
            if not existed:
                RULE_PATH.unlink()
            raise RuntimeError("DSM did not accept the restricted power permission") from None
    finally:
        Path(temporary).unlink(missing_ok=True)


if __name__ == "__main__":
    if sys.argv[1:] not in ([], ["--remove"]):
        sys.exit("Usage: power_permissions.py [--remove]")
    try:
        for path in (Path(__file__), Path(__file__).parent):
            metadata = path.stat()
            if metadata.st_uid != 0 or metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
                raise RuntimeError("Use the root-protected WakeLink helper in /var/packages/pcpowerfree/conf")
        configure(remove=bool(sys.argv[1:]))
    except (OSError, KeyError, RuntimeError) as error:
        sys.exit(str(error))
    print("WakeLink DSM power permission removed." if sys.argv[1:] else
          "WakeLink DSM power permission enabled. No power command was executed.")
