"""Authenticate a DSM administrator before local setup actions."""

from __future__ import annotations

import ipaddress
import os
import subprocess


AUTHENTICATE_CGI = "/usr/syno/synoman/webman/modules/authenticate.cgi"


def authenticate_admin(
    cookie: str, remote_addr: str, server_addr: str,
    *, syno_token: str = "", syno_hash: str = "",
) -> bool:
    """Fail closed unless DSM confirms the session belongs to an administrator."""
    if not cookie or len(cookie) > 8192 or any(char in cookie for char in "\r\n\0"):
        return False
    if any(len(value) > 512 or any(char in value for char in "\r\n\0") for value in (syno_token, syno_hash)):
        return False
    try:
        ipaddress.ip_address(remote_addr)
        ipaddress.ip_address(server_addr)
        environment = os.environ.copy()
        # DSM's signed desktop sessions use these headers instead of an id cookie.
        environment.update(
            HTTP_COOKIE=cookie, REMOTE_ADDR=remote_addr, SERVER_ADDR=server_addr,
            HTTP_X_SYNO_TOKEN=syno_token, HTTP_X_SYNO_HASH=syno_hash,
        )
        auth = subprocess.run(
            [AUTHENTICATE_CGI], env=environment, capture_output=True, text=True,
            timeout=3, check=False,
        )
        username = auth.stdout.strip()
        if auth.returncode or not username or "\n" in username or "\r" in username:
            return False
        groups = subprocess.run(
            ["id", "-nG", username], capture_output=True, text=True,
            timeout=3, check=False,
        )
        return groups.returncode == 0 and "administrators" in groups.stdout.split()
    except (OSError, ValueError, subprocess.SubprocessError):
        return False
