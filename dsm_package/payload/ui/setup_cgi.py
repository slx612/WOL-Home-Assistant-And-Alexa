"""DSM same-origin CGI bridge to the local WakeLink agent."""

from __future__ import annotations

from http import HTTPStatus
import json
import os
from pathlib import Path
import ssl
import sys
from typing import Mapping, TextIO
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener
from urllib.parse import urlsplit


AGENT_PORT = 58477


def call_agent(method: str, path: str, headers: dict[str, str]) -> tuple[int, dict]:
    """Forward one allowed request to the pinned local TLS identity."""
    certificate = Path(__file__).with_name("agent-cert.pem")
    context = ssl.create_default_context(cafile=str(certificate))
    context.check_hostname = False
    opener = build_opener(ProxyHandler({}), HTTPSHandler(context=context))
    request = Request(
        f"https://127.0.0.1:{AGENT_PORT}{path}",
        data=b"" if method == "POST" else None,
        headers=headers,
        method=method,
    )
    try:
        response = opener.open(request, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read(4097)
        if len(raw) > 4096:
            raise ValueError("Agent response too large")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("Invalid agent response")
        return response.status, payload


def handle_request(environ: Mapping[str, str]) -> tuple[int, dict]:
    """Accept only setup status and code creation, never power actions."""
    action = environ.get("QUERY_STRING", "")
    method = environ.get("REQUEST_METHOD", "")
    if action == "action=status":
        if method != "GET":
            return 405, {"error": "Method not allowed"}
        path = "/v1/dsm/setup"
    elif action == "action=pair":
        if method != "POST":
            return 405, {"error": "Method not allowed"}
        if environ.get("HTTP_X_WAKELINK_ACTION") != "pair":
            return 403, {"error": "Setup action not allowed"}
        path = "/v1/dsm/pairing-code"
    else:
        return 404, {"error": "Not found"}

    origin = environ.get("HTTP_ORIGIN", "")
    if origin and urlsplit(origin).netloc.lower() != environ.get("HTTP_HOST", "").lower():
        return 403, {"error": "Origin not allowed"}

    headers = {
        "Cookie": environ.get("HTTP_COOKIE", ""),
        "X-WakeLink-Remote-Addr": environ.get("REMOTE_ADDR", ""),
        "X-WakeLink-Server-Addr": environ.get("SERVER_ADDR", ""),
        "X-SYNO-TOKEN": environ.get("HTTP_X_SYNO_TOKEN", ""),
        "X-SYNO-HASH": environ.get("HTTP_X_SYNO_HASH", ""),
    }
    if action == "action=pair":
        headers["X-WakeLink-Action"] = "pair"
    try:
        status, payload = call_agent(method, path, headers)
    except (OSError, ValueError, URLError, ssl.SSLError):
        return 503, {"error": "WakeLink agent unavailable"}

    if status == 200 and action == "action=status":
        return status, {key: payload.get(key) for key in (
            "online", "hostname", "ip_address", "mac_address", "agent_version", "power_permission_enabled",
        )}
    if status == 200 and action == "action=pair":
        return status, {key: payload.get(key) for key in ("pairing_code", "expires_in")}
    return status, {"error": str(payload.get("error", "Setup request failed"))}


def main(environ: Mapping[str, str] | None = None, output: TextIO | None = None) -> None:
    status, payload = handle_request(os.environ if environ is None else environ)
    output = sys.stdout if output is None else output
    reason = HTTPStatus(status).phrase
    output.write(f"Status: {status} {reason}\r\n")
    output.write("Content-Type: application/json; charset=utf-8\r\n")
    output.write("Cache-Control: no-store\r\n")
    output.write("X-Content-Type-Options: nosniff\r\n\r\n")
    output.write(json.dumps(payload))


if __name__ == "__main__":
    main()
