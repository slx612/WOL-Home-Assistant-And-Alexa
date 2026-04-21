"""Authenticated local agent to control Windows shutdown and restart."""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass
import hashlib
import ipaddress
import json
import logging
from logging.handlers import RotatingFileHandler
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import socket
import subprocess
import time
import uuid
from typing import Any

from network_info import AdapterInfo, detect_primary_adapter

try:
    from zeroconf import IPVersion, ServiceInfo, Zeroconf
except ImportError:  # pragma: no cover - optional during source-only use
    IPVersion = None
    ServiceInfo = None
    Zeroconf = None

AGENT_VERSION = "0.2.0-beta.3"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8777
DEFAULT_ALLOWED_SUBNETS = ("127.0.0.1/32",)
DEFAULT_SHUTDOWN_DELAY = 0
DEFAULT_SHUTDOWN_FORCE = False
DEFAULT_BROADCAST_PORT = 9
DEFAULT_GUARD_STATE_FILE = "guard_state.json"
PAIRING_CODE_TTL_SECONDS = 600
PAIRING_CODE_MIN_LENGTH = 6
ZEROCONF_SERVICE_TYPE = "_pcpowerfree._tcp.local."
COMMAND_GUARD_ALLOW = "allow"
COMMAND_GUARD_IGNORE_MANUAL = "ignore_manual"
COMMAND_GUARD_IGNORE_UNTIL = "ignore_until"

AllowedNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network


class AgentConfigError(ValueError):
    """Raised when the agent configuration is invalid."""


@dataclass(slots=True)
class CommandGuardState:
    """Persistent state that can temporarily block power commands."""

    mode: str = COMMAND_GUARD_ALLOW
    until_ts: float | None = None
    updated_at: float | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "CommandGuardState":
        """Build the guard state from a JSON payload."""
        if not isinstance(payload, dict):
            return cls()

        mode = str(payload.get("mode", COMMAND_GUARD_ALLOW)).strip().lower()
        if mode not in {
            COMMAND_GUARD_ALLOW,
            COMMAND_GUARD_IGNORE_MANUAL,
            COMMAND_GUARD_IGNORE_UNTIL,
        }:
            mode = COMMAND_GUARD_ALLOW

        until_raw = payload.get("until_ts")
        try:
            until_ts = float(until_raw) if until_raw not in (None, "") else None
        except (TypeError, ValueError):
            until_ts = None

        updated_raw = payload.get("updated_at")
        try:
            updated_at = float(updated_raw) if updated_raw not in (None, "") else None
        except (TypeError, ValueError):
            updated_at = None

        return cls(mode=mode, until_ts=until_ts, updated_at=updated_at)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the guard state to JSON."""
        return {
            "mode": self.mode,
            "until_ts": self.until_ts,
            "updated_at": self.updated_at,
        }

    def effective(self, now: float | None = None) -> "CommandGuardState":
        """Return the effective current state, clearing expired windows."""
        current_time = time.time() if now is None else now
        if self.mode == COMMAND_GUARD_IGNORE_UNTIL:
            if self.until_ts is None or self.until_ts <= current_time:
                return CommandGuardState(
                    mode=COMMAND_GUARD_ALLOW,
                    until_ts=None,
                    updated_at=self.updated_at,
                )
        return self

    def is_blocking(self, now: float | None = None) -> bool:
        """Return whether commands should currently be blocked."""
        return self.effective(now).mode != COMMAND_GUARD_ALLOW


class AgentConfig:
    """Small container for runtime settings."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        token: str,
        allowed_subnets: tuple[AllowedNetwork, ...],
        shutdown_delay_seconds: int,
        shutdown_force: bool,
        log_file: Path,
        machine_id: str,
        pairing_code_hash: str | None,
        pairing_code_expires_at: float | None,
    ) -> None:
        self.host = host
        self.port = port
        self.token = token
        self.allowed_subnets = allowed_subnets
        self.shutdown_delay_seconds = shutdown_delay_seconds
        self.shutdown_force = shutdown_force
        self.log_file = log_file
        self.machine_id = machine_id
        self.pairing_code_hash = pairing_code_hash
        self.pairing_code_expires_at = pairing_code_expires_at

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
        *,
        config_dir: Path,
    ) -> tuple["AgentConfig", bool]:
        """Build the config object from JSON data."""
        changed = False

        token = str(payload.get("token", "")).strip()
        if len(token) < 16:
            raise AgentConfigError("The token must be at least 16 characters long")

        subnet_entries = payload.get("allowed_subnets", list(DEFAULT_ALLOWED_SUBNETS))
        if not isinstance(subnet_entries, list) or not subnet_entries:
            raise AgentConfigError("allowed_subnets must be a non-empty list")

        allowed_subnets = tuple(ipaddress.ip_network(entry, strict=False) for entry in subnet_entries)

        log_file_raw = payload.get("log_file", "pc_power_agent.log")
        log_file = Path(log_file_raw)
        if not log_file.is_absolute():
            log_file = config_dir / log_file

        machine_id = str(payload.get("machine_id", "")).strip().lower()
        if not machine_id:
            machine_id = uuid.uuid4().hex
            changed = True

        pairing_code_hash = payload.get("pairing_code_hash")
        if pairing_code_hash is not None:
            pairing_code_hash = str(pairing_code_hash).strip().lower() or None

        pairing_code_expires_at_raw = payload.get("pairing_code_expires_at")
        pairing_code_expires_at: float | None
        if pairing_code_expires_at_raw in (None, ""):
            pairing_code_expires_at = None
        else:
            pairing_code_expires_at = float(pairing_code_expires_at_raw)

        return (
            cls(
                host=str(payload.get("host", DEFAULT_HOST)),
                port=int(payload.get("port", DEFAULT_PORT)),
                token=token,
                allowed_subnets=allowed_subnets,
                shutdown_delay_seconds=max(
                    0,
                    int(payload.get("shutdown_delay_seconds", DEFAULT_SHUTDOWN_DELAY)),
                ),
                shutdown_force=bool(payload.get("shutdown_force", DEFAULT_SHUTDOWN_FORCE)),
                log_file=log_file,
                machine_id=machine_id,
                pairing_code_hash=pairing_code_hash,
                pairing_code_expires_at=pairing_code_expires_at,
            ),
            changed,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the config back to JSON."""
        return {
            "host": self.host,
            "port": self.port,
            "token": self.token,
            "allowed_subnets": [str(item) for item in self.allowed_subnets],
            "shutdown_delay_seconds": self.shutdown_delay_seconds,
            "shutdown_force": self.shutdown_force,
            "log_file": str(self.log_file),
            "machine_id": self.machine_id,
            "pairing_code_hash": self.pairing_code_hash,
            "pairing_code_expires_at": self.pairing_code_expires_at,
        }


class PCPowerHTTPServer(ThreadingHTTPServer):
    """HTTP server that stores the agent configuration."""

    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler_class: type[BaseHTTPRequestHandler],
        config: AgentConfig,
        config_path: Path,
        logger: logging.Logger,
    ) -> None:
        super().__init__(server_address, request_handler_class)
        self.config = config
        self.config_path = config_path
        self.config_mtime_ns = _get_config_mtime_ns(config_path)
        self.logger = logger
        self.hostname = socket.gethostname()
        self.last_command: str | None = None
        self.last_command_at: float | None = None
        self.guard_state_path = config_path.with_name(DEFAULT_GUARD_STATE_FILE)
        self.guard_state = load_guard_state(self.guard_state_path)
        self.guard_state_mtime_ns = _get_config_mtime_ns(self.guard_state_path)

    def refresh_config_if_needed(self) -> None:
        """Reload the config if it has changed on disk."""
        current_mtime = _get_config_mtime_ns(self.config_path)
        if current_mtime == self.config_mtime_ns:
            return

        new_config, _ = load_config(self.config_path)
        if new_config.port != self.server_address[1]:
            self.logger.warning(
                "Ignoring updated port %s while running on %s",
                new_config.port,
                self.server_address[1],
            )
            new_config.port = self.server_address[1]

        self.config = new_config
        self.config_mtime_ns = current_mtime
        self.logger.info("Reloaded config from disk")

    def persist_config(self) -> None:
        """Persist the current config to disk."""
        save_config(self.config_path, self.config)
        self.config_mtime_ns = _get_config_mtime_ns(self.config_path)

    def refresh_guard_state_if_needed(self) -> None:
        """Reload the command guard state if it changed on disk."""
        current_mtime = _get_config_mtime_ns(self.guard_state_path)
        if current_mtime == self.guard_state_mtime_ns:
            return

        self.guard_state = load_guard_state(self.guard_state_path)
        self.guard_state_mtime_ns = current_mtime
        self.logger.info("Reloaded command guard state from disk")

    def persist_guard_state(self) -> None:
        """Persist the current command guard state."""
        save_guard_state(self.guard_state_path, self.guard_state)
        self.guard_state_mtime_ns = _get_config_mtime_ns(self.guard_state_path)

    def get_effective_guard_state(self) -> CommandGuardState:
        """Return the effective command guard state, clearing expired windows."""
        effective_state = self.guard_state.effective()
        if effective_state.to_dict() != self.guard_state.to_dict():
            self.guard_state = effective_state
            self.persist_guard_state()
        return effective_state

    def build_guard_status_payload(self) -> dict[str, Any]:
        """Return the current command guard state as JSON."""
        state = self.get_effective_guard_state()
        return {
            "active": state.mode != COMMAND_GUARD_ALLOW,
            "mode": state.mode,
            "until_ts": state.until_ts,
            "updated_at": state.updated_at,
        }


class ServiceAdvertiser:
    """Advertise the agent on the local network using mDNS."""

    def __init__(self, server: PCPowerHTTPServer, logger: logging.Logger) -> None:
        self._server = server
        self._logger = logger
        self._zeroconf: Zeroconf | None = None
        self._service_info: ServiceInfo | None = None

    def start(self) -> None:
        """Register the mDNS service."""
        if Zeroconf is None or ServiceInfo is None or IPVersion is None:
            self._logger.warning("Zeroconf is not available; LAN discovery disabled")
            return

        try:
            adapter = detect_primary_adapter()
        except Exception as err:  # pragma: no cover - depends on host networking
            self._logger.warning("Unable to detect primary adapter for discovery: %s", err)
            return

        service_name = f"{self._server.hostname}-{self._server.config.machine_id[:8]}.{ZEROCONF_SERVICE_TYPE}"
        self._service_info = ServiceInfo(
            ZEROCONF_SERVICE_TYPE,
            service_name,
            addresses=[socket.inet_aton(adapter.ipv4_address)],
            port=self._server.server_address[1],
            properties={
                "id": self._server.config.machine_id,
                "hostname": self._server.hostname,
                "name": self._server.hostname,
                "version": AGENT_VERSION,
            },
            server=f"{self._server.hostname}.local.",
        )
        self._zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self._zeroconf.register_service(self._service_info, allow_name_change=True)
        self._logger.info(
            "Registered mDNS service %s on %s",
            ZEROCONF_SERVICE_TYPE,
            adapter.ipv4_address,
        )

    def stop(self) -> None:
        """Unregister the mDNS service."""
        if self._zeroconf is None:
            return

        if self._service_info is not None:
            try:
                self._zeroconf.unregister_service(self._service_info)
            except Exception:  # pragma: no cover - best effort on shutdown
                self._logger.exception("Failed to unregister mDNS service")
        self._zeroconf.close()
        self._zeroconf = None
        self._service_info = None


class PCPowerRequestHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests for the agent."""

    server: PCPowerHTTPServer
    server_version = f"PCPowerAgent/{AGENT_VERSION}"

    def do_GET(self) -> None:
        """Handle GET requests."""
        self.server.refresh_config_if_needed()
        self.server.refresh_guard_state_if_needed()

        if self.path == "/v1/status":
            if not self._authorize():
                return
            self._send_json(HTTPStatus.OK, self._build_status_payload())
            return

        if self.path == "/v1/discovery":
            if not self._authorize_network():
                return
            self._send_json(HTTPStatus.OK, self._build_discovery_payload())
            return

        if self.path == "/v1/local/guard":
            if not self._authorize_local():
                return
            self._send_json(HTTPStatus.OK, self.server.build_guard_status_payload())
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
        """Handle POST requests."""
        self.server.refresh_config_if_needed()
        self.server.refresh_guard_state_if_needed()

        if self.path == "/v1/pairing/exchange":
            if not self._authorize_network():
                return
            self._handle_pairing_exchange()
            return

        if self.path == "/v1/local/guard":
            if not self._authorize_local():
                return
            self._handle_guard_update()
            return

        if not self._authorize():
            return

        if self.path == "/v1/power/shutdown":
            self._handle_power_action("shutdown")
            return

        if self.path == "/v1/power/restart":
            self._handle_power_action("restart")
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def log_message(self, format: str, *args: Any) -> None:
        """Route HTTP logs through the agent logger."""
        self.server.logger.info("%s - %s", self.client_address[0], format % args)

    def _authorize_network(self) -> bool:
        """Authorize the client by source network only."""
        client_ip = ipaddress.ip_address(self.client_address[0])
        if not any(client_ip in subnet for subnet in self.server.config.allowed_subnets):
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Client IP is not allowed"})
            return False
        return True

    def _authorize(self) -> bool:
        """Authorize the request by source network and token."""
        if not self._authorize_network():
            return False

        header = self.headers.get("Authorization", "")
        token = header.removeprefix("Bearer ").strip()
        if not secrets.compare_digest(token, self.server.config.token):
            self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "Invalid token"})
            return False

        return True

    def _authorize_local(self) -> bool:
        """Authorize a loopback-only local control request."""
        if not self._authorize():
            return False

        client_ip = ipaddress.ip_address(self.client_address[0])
        if not client_ip.is_loopback:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Local control requires loopback"})
            return False
        return True

    def _handle_power_action(self, action: str) -> None:
        """Run a power action if the request is valid."""
        guard_state = self.server.get_effective_guard_state()
        if guard_state.is_blocking():
            self.server.logger.warning(
                "Ignored %s command from %s because the command guard is active (%s)",
                action,
                self.client_address[0],
                guard_state.mode,
            )
            self._send_json(
                HTTPStatus.LOCKED,
                {
                    "error": "Command guard is active",
                    "action": action,
                    **self.server.build_guard_status_payload(),
                },
            )
            return

        try:
            payload = self._read_json()
            delay_seconds = max(
                0,
                int(payload.get("delay_seconds", self.server.config.shutdown_delay_seconds)),
            )
            force = bool(payload.get("force", self.server.config.shutdown_force))
            command = build_windows_command(action, delay_seconds=delay_seconds, force=force)
            subprocess.run(command, check=True, capture_output=True, text=True)
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body"})
            return
        except subprocess.CalledProcessError as err:
            self.server.logger.exception("Windows command failed")
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "Windows command failed", "details": err.stderr.strip()},
            )
            return

        self.server.last_command = action
        self.server.last_command_at = time.time()
        self.server.logger.info("Accepted %s command", action)
        self._send_json(
            HTTPStatus.ACCEPTED,
            {"accepted": True, "action": action, "delay_seconds": delay_seconds, "force": force},
        )

    def _handle_guard_update(self) -> None:
        """Update the command guard mode from a local request."""
        try:
            payload = self._read_json()
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body"})
            return

        mode = str(payload.get("mode", "")).strip().lower()
        now = time.time()

        if mode == COMMAND_GUARD_ALLOW:
            self.server.guard_state = CommandGuardState(
                mode=COMMAND_GUARD_ALLOW,
                until_ts=None,
                updated_at=now,
            )
        elif mode == COMMAND_GUARD_IGNORE_MANUAL:
            self.server.guard_state = CommandGuardState(
                mode=COMMAND_GUARD_IGNORE_MANUAL,
                until_ts=None,
                updated_at=now,
            )
        elif mode == COMMAND_GUARD_IGNORE_UNTIL:
            try:
                duration_minutes = int(payload.get("duration_minutes", 0))
            except (TypeError, ValueError):
                duration_minutes = 0
            if duration_minutes <= 0:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "duration_minutes must be a positive integer"},
                )
                return
            self.server.guard_state = CommandGuardState(
                mode=COMMAND_GUARD_IGNORE_UNTIL,
                until_ts=now + duration_minutes * 60,
                updated_at=now,
            )
        else:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Unsupported guard mode"})
            return

        self.server.persist_guard_state()
        self.server.logger.info(
            "Updated command guard from %s to %s",
            self.client_address[0],
            self.server.guard_state.mode,
        )
        self._send_json(HTTPStatus.OK, self.server.build_guard_status_payload())

    def _handle_pairing_exchange(self) -> None:
        """Exchange a valid pairing code for the long-lived API token."""
        try:
            payload = self._read_json()
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body"})
            return

        pairing_code = str(payload.get("pairing_code", "")).strip()
        if len(pairing_code) < PAIRING_CODE_MIN_LENGTH:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid pairing code"})
            return

        expires_at = self.server.config.pairing_code_expires_at
        expected_hash = self.server.config.pairing_code_hash
        if expected_hash is None or expires_at is None:
            self._send_json(HTTPStatus.PRECONDITION_FAILED, {"error": "No active pairing code"})
            return

        if expires_at < time.time():
            self.server.config.pairing_code_hash = None
            self.server.config.pairing_code_expires_at = None
            self.server.persist_config()
            self._send_json(HTTPStatus.GONE, {"error": "Pairing code expired"})
            return

        if not secrets.compare_digest(expected_hash, hash_pairing_code(pairing_code)):
            self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "Invalid pairing code"})
            return

        discovery_payload = self._build_discovery_payload()
        self.server.config.pairing_code_hash = None
        self.server.config.pairing_code_expires_at = None
        self.server.persist_config()
        self.server.logger.info("Pairing completed for %s", self.client_address[0])
        self._send_json(
            HTTPStatus.OK,
            {
                **discovery_payload,
                "api_token": self.server.config.token,
                "broadcast_port": DEFAULT_BROADCAST_PORT,
            },
        )

    def _read_json(self) -> dict[str, Any]:
        """Parse the JSON request body."""
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length == 0:
            return {}

        raw_body = self.rfile.read(content_length).decode("utf-8")
        if not raw_body.strip():
            return {}

        payload = json.loads(raw_body)
        if not isinstance(payload, dict):
            raise ValueError("JSON payload must be an object")
        return payload

    def _send_json(self, status_code: HTTPStatus, payload: dict[str, Any]) -> None:
        """Send a JSON response."""
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _build_status_payload(self) -> dict[str, Any]:
        """Build the authenticated status payload."""
        guard_state = self.server.get_effective_guard_state()
        uptime_seconds = get_system_uptime_seconds()
        booted_at = (time.time() - uptime_seconds) if uptime_seconds is not None else None
        return {
            "online": True,
            "hostname": self.server.hostname,
            "agent_version": AGENT_VERSION,
            "last_command": self.server.last_command,
            "last_command_at": self.server.last_command_at,
            "mac_addresses": get_local_mac_addresses(),
            "machine_id": self.server.config.machine_id,
            "uptime_seconds": uptime_seconds,
            "booted_at": booted_at,
            "command_guard_active": guard_state.mode != COMMAND_GUARD_ALLOW,
            "command_guard_mode": guard_state.mode,
            "command_guard_until_ts": guard_state.until_ts,
        }

    def _build_discovery_payload(self) -> dict[str, Any]:
        """Build the discovery payload returned before pairing."""
        try:
            adapter = detect_primary_adapter()
        except Exception:
            adapter = None

        mac_addresses = get_local_mac_addresses()
        primary_mac = _pick_primary_mac(adapter, mac_addresses)
        discovery_subnets = [adapter.subnet_cidr] if adapter is not None else []
        return {
            "machine_id": self.server.config.machine_id,
            "hostname": self.server.hostname,
            "name": self.server.hostname,
            "agent_version": AGENT_VERSION,
            "agent_port": self.server.server_address[1],
            "host": (
                adapter.ipv4_address
                if adapter is not None
                else (
                    self.server.server_address[0]
                    if self.server.server_address[0] not in ("", "0.0.0.0")
                    else None
                )
            ),
            "primary_mac": primary_mac,
            "mac_addresses": mac_addresses,
            "broadcast_address": adapter.broadcast_address if adapter is not None else None,
            "discovery_subnets": discovery_subnets,
            "pairing_code_active": self._pairing_code_is_active(),
        }

    def _pairing_code_is_active(self) -> bool:
        """Return whether there is a valid pairing code configured."""
        return bool(
            self.server.config.pairing_code_hash
            and self.server.config.pairing_code_expires_at
            and self.server.config.pairing_code_expires_at >= time.time()
        )


def build_windows_command(action: str, *, delay_seconds: int, force: bool) -> list[str]:
    """Return the Windows command for a power action."""
    if action == "shutdown":
        command = ["shutdown", "/s", "/t", str(delay_seconds)]
    elif action == "restart":
        command = ["shutdown", "/r", "/t", str(delay_seconds)]
    else:
        raise AgentConfigError(f"Unsupported action: {action}")

    if force:
        command.append("/f")

    return command


def hash_pairing_code(pairing_code: str) -> str:
    """Hash a pairing code before storing or comparing it."""
    return hashlib.sha256(pairing_code.strip().encode("utf-8")).hexdigest()


def get_system_uptime_seconds() -> int | None:
    """Return the Windows uptime in whole seconds."""
    try:
        return int(ctypes.windll.kernel32.GetTickCount64() // 1000)
    except (AttributeError, OSError):
        return None


def get_local_mac_addresses() -> list[str]:
    """Return the MAC addresses that identify this Windows machine."""
    mac_addresses: list[str] = []
    try:
        result = subprocess.run(
            ["getmac", "/fo", "csv", "/nh"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        fallback_mac = _format_mac_int(uuid.getnode())
        return [fallback_mac] if fallback_mac else []

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip().strip('"')
        if not line:
            continue
        device_fields = [item.strip().strip('"') for item in raw_line.split(",")]
        if not device_fields:
            continue
        mac_value = device_fields[0]
        if mac_value and mac_value != "N/A":
            normalized = _normalize_mac_string(mac_value)
            if normalized and normalized not in mac_addresses:
                mac_addresses.append(normalized)

    if not mac_addresses:
        fallback_mac = _format_mac_int(uuid.getnode())
        if fallback_mac:
            mac_addresses.append(fallback_mac)

    return mac_addresses


def _normalize_mac_string(value: str) -> str | None:
    """Normalize a MAC string into AA:BB:CC:DD:EE:FF."""
    cleaned = "".join(character for character in value if character.isalnum())
    if len(cleaned) != 12:
        return None
    return ":".join(cleaned[index : index + 2] for index in range(0, 12, 2)).upper()


def _format_mac_int(value: int) -> str | None:
    """Format an integer MAC address."""
    if value <= 0 or value >= 1 << 48:
        return None
    raw = f"{value:012x}"
    return ":".join(raw[index : index + 2] for index in range(0, 12, 2)).upper()


def _pick_primary_mac(adapter: AdapterInfo | None, mac_addresses: list[str]) -> str | None:
    """Select the best MAC address to identify the PC."""
    if adapter is not None:
        return adapter.mac_address
    return mac_addresses[0] if mac_addresses else None


def _get_config_mtime_ns(config_path: Path) -> int:
    """Return the modification timestamp of the config file."""
    try:
        return config_path.stat().st_mtime_ns
    except FileNotFoundError:
        return 0


def load_config(config_path: Path) -> tuple[AgentConfig, bool]:
    """Load the JSON configuration from disk."""
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise AgentConfigError("Config file must contain a JSON object")
    return AgentConfig.from_dict(raw, config_dir=config_path.parent)


def save_config(config_path: Path, config: AgentConfig) -> None:
    """Persist the JSON configuration to disk."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")


def load_guard_state(state_path: Path) -> CommandGuardState:
    """Load the persisted command guard state from disk."""
    try:
        raw = json.loads(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return CommandGuardState()
    except (OSError, ValueError):
        return CommandGuardState()

    return CommandGuardState.from_dict(raw if isinstance(raw, dict) else None)


def save_guard_state(state_path: Path, guard_state: CommandGuardState) -> None:
    """Persist the command guard state to disk."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(guard_state.to_dict(), indent=2), encoding="utf-8")


def create_logger(log_file: Path) -> logging.Logger:
    """Create the rotating logger for the agent."""
    logger = logging.getLogger("pc_power_agent")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run the PC Power Free Windows agent")
    parser.add_argument("--config", required=True, help="Path to config.json")
    return parser.parse_args()


def main() -> int:
    """Start the HTTP server."""
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    config, changed = load_config(config_path)
    if changed:
        save_config(config_path, config)

    logger = create_logger(config.log_file)
    logger.info("Starting PC Power Agent %s", AGENT_VERSION)
    logger.info("Allowed subnets: %s", ", ".join(str(item) for item in config.allowed_subnets))
    logger.info("Machine ID: %s", config.machine_id)

    server = PCPowerHTTPServer(
        (config.host, config.port),
        PCPowerRequestHandler,
        config,
        config_path,
        logger,
    )
    advertiser = ServiceAdvertiser(server, logger)
    advertiser.start()

    try:
        logger.info("Listening on http://%s:%s", config.host, config.port)
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping agent")
    finally:
        advertiser.stop()
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
