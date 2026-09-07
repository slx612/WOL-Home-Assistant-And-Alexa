"""API client and discovery helpers for PC Power Free."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
import hashlib
import hmac
import ipaddress
from itertools import islice
import re
import secrets
import socket
import ssl
import time
from typing import Any

from aiohttp import ClientError, ClientSession, Fingerprint, ServerFingerprintMismatch

from .const import (
    DEFAULT_AGENT_PORT,
    DEFAULT_BROADCAST_ADDRESS,
    DEFAULT_BROADCAST_PORT,
    STATUS_BOOTED_AT,
    STATUS_CAPABILITIES,
    STATUS_COMMAND_GUARD_ACTIVE,
    STATUS_COMMAND_GUARD_MODE,
    STATUS_COMMAND_GUARD_UNTIL_TS,
    STATUS_LAST_COMMAND_AT,
    STATUS_MACHINE_ID,
    STATUS_PLATFORM,
    STATUS_UPTIME_SECONDS,
)
from .platforms import normalize_agent_capabilities, normalize_agent_platform

MAC_REGEX = re.compile(r"^[0-9a-fA-F]{12}$")
DISCOVERY_TIMEOUT_SECONDS = 0.75
DISCOVERY_COOLDOWN_SECONDS = 300
DISCOVERY_CONCURRENCY = 32
DISCOVERY_MAX_ADDRESSES = 4096
DISCOVERY_DEADLINE_SECONDS = 12


class PCPowerError(Exception):
    """Base exception for the integration."""


class PCPowerAuthError(PCPowerError):
    """Raised when the agent rejects the token."""


class PCPowerCommandError(PCPowerError):
    """Raised when an action cannot be completed."""


class PCPowerDiscoveryError(PCPowerError):
    """Raised when discovery data cannot be retrieved or validated."""

    def __init__(self, reason: str) -> None:
        """Store the machine-readable reason."""
        super().__init__(reason)
        self.reason = reason


class PCPowerPairingError(PCPowerError):
    """Raised when the pairing flow fails."""

    def __init__(self, reason: str) -> None:
        """Store the machine-readable reason."""
        super().__init__(reason)
        self.reason = reason


@dataclass(slots=True)
class PCPowerDiscoveryInfo:
    """Normalized discovery data returned by the local agent."""

    machine_id: str
    host: str
    agent_port: int
    hostname: str
    name: str
    primary_mac: str
    mac_addresses: tuple[str, ...]
    broadcast_address: str
    discovery_subnets: tuple[str, ...]
    agent_version: str | None
    platform: str | None
    capabilities: tuple[str, ...]
    pairing_code_active: bool
    certificate_fingerprint: str = ""

    @property
    def discovery_subnets_text(self) -> str:
        """Return discovery subnets as a comma-separated string."""
        return ",".join(self.discovery_subnets)


@dataclass(slots=True)
class PCPowerPairingResult:
    """Pairing response returned by the local agent."""

    discovery: PCPowerDiscoveryInfo
    api_token: str
    broadcast_port: int


def normalize_mac(mac_address: str) -> str:
    """Normalize a MAC address to 12 hexadecimal characters."""
    cleaned = re.sub(r"[:.\-]", "", mac_address.strip())
    if not MAC_REGEX.fullmatch(cleaned):
        raise PCPowerError("Invalid MAC address")
    return cleaned.lower()


def format_mac(mac_address: str) -> str:
    """Format a normalized MAC address using colons."""
    normalized = normalize_mac(mac_address)
    return ":".join(normalized[index : index + 2] for index in range(0, 12, 2)).upper()


def send_magic_packet(mac_address: str, broadcast_address: str, broadcast_port: int) -> None:
    """Send a Wake-on-LAN magic packet."""
    normalized = normalize_mac(mac_address)
    payload = b"\xff" * 6 + bytes.fromhex(normalized) * 16

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.sendto(payload, (broadcast_address, broadcast_port))


def parse_discovery_subnets(value: str | Iterable[str] | None) -> tuple[ipaddress.IPv4Network, ...]:
    """Parse discovery subnets from a text field or an iterable."""
    if value is None:
        return ()

    if isinstance(value, str):
        raw_entries = re.split(r"[\s,;]+", value.strip())
    else:
        raw_entries = [str(item).strip() for item in value]

    networks: list[ipaddress.IPv4Network] = []
    for entry in raw_entries:
        if not entry:
            continue
        network = ipaddress.ip_network(entry, strict=False)
        if not isinstance(network, ipaddress.IPv4Network):
            raise PCPowerError("Only IPv4 discovery subnets are supported")
        networks.append(network)
    return tuple(networks)


def _normalize_discovery_payload(
    payload: dict[str, Any],
    *,
    fallback_host: str,
    fallback_port: int,
) -> PCPowerDiscoveryInfo:
    """Validate and normalize discovery data."""
    if not isinstance(payload, dict):
        raise PCPowerDiscoveryError("invalid_response")
    machine_id = str(payload.get("machine_id", "")).strip().lower()
    if not machine_id:
        raise PCPowerDiscoveryError("invalid_response")

    host = fallback_host.strip()
    if not host:
        raise PCPowerDiscoveryError("invalid_response")

    try:
        agent_port = int(fallback_port)
        if not 1 <= agent_port <= 65535:
            raise ValueError("Invalid port")
    except (TypeError, ValueError) as err:
        raise PCPowerDiscoveryError("invalid_response") from err

    hostname = str(payload.get("hostname") or payload.get("name") or host).strip()
    name = str(payload.get("name") or hostname or host).strip()

    raw_mac_entries = payload.get("mac_addresses", [])
    if not isinstance(raw_mac_entries, list):
        raw_mac_entries = []

    normalized_macs: list[str] = []
    for raw_value in [payload.get("primary_mac"), *raw_mac_entries]:
        if not isinstance(raw_value, str):
            continue
        try:
            mac_value = format_mac(raw_value)
        except PCPowerError:
            continue
        if mac_value not in normalized_macs:
            normalized_macs.append(mac_value)

    if not normalized_macs:
        raise PCPowerDiscoveryError("invalid_response")

    raw_discovery_subnets = payload.get("discovery_subnets", [])
    if isinstance(raw_discovery_subnets, str):
        raw_discovery_subnets = [raw_discovery_subnets]
    if not isinstance(raw_discovery_subnets, list):
        raw_discovery_subnets = []

    try:
        discovery_subnets = tuple(
            str(network) for network in parse_discovery_subnets(raw_discovery_subnets)
        )
    except (PCPowerError, ValueError) as err:
        raise PCPowerDiscoveryError("invalid_response") from err

    broadcast_address = str(
        payload.get("broadcast_address") or DEFAULT_BROADCAST_ADDRESS
    ).strip()

    return PCPowerDiscoveryInfo(
        machine_id=machine_id,
        host=host,
        agent_port=agent_port,
        hostname=hostname,
        name=name,
        primary_mac=normalized_macs[0],
        mac_addresses=tuple(normalized_macs),
        broadcast_address=broadcast_address,
        discovery_subnets=discovery_subnets,
        agent_version=str(payload.get("agent_version") or "").strip() or None,
        platform=normalize_agent_platform(payload.get(STATUS_PLATFORM)),
        capabilities=normalize_agent_capabilities(payload.get(STATUS_CAPABILITIES)),
        pairing_code_active=bool(payload.get("pairing_code_active")),
    )


def _pin(fingerprint: str | None) -> Fingerprint:
    """Never send credentials until the stored TLS identity has been checked."""
    try:
        value = bytes.fromhex(fingerprint or "")
        if len(value) != 32:
            raise ValueError("Missing SHA-256 identity")
        return Fingerprint(value)
    except ValueError as err:
        raise PCPowerAuthError("Pair again to establish a secure connection") from err


async def _enrollment_fingerprint(host: str, port: int) -> str:
    """Read an untrusted identity; enrollment or an existing secret must verify it."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    _, writer = await asyncio.open_connection(host, port, ssl=context)
    try:
        certificate = writer.get_extra_info("ssl_object").getpeercert(binary_form=True)
        return hashlib.sha256(certificate).hexdigest()
    finally:
        writer.close()
        await writer.wait_closed()


async def async_fetch_discovery_info(
    session: ClientSession,
    *,
    host: str,
    agent_port: int = DEFAULT_AGENT_PORT,
    timeout: int = 5,
    certificate_fingerprint: str | None = None,
) -> PCPowerDiscoveryInfo:
    """Fetch pre-pairing discovery data from the local agent."""
    try:
        async with asyncio.timeout(timeout):
            fingerprint = certificate_fingerprint or await _enrollment_fingerprint(host, agent_port)
            async with session.get(
                f"https://{host}:{agent_port}/v1/discovery",
                headers={"Accept": "application/json"},
                ssl=_pin(fingerprint), allow_redirects=False,
            ) as response:
                if response.status == 403:
                    raise PCPowerDiscoveryError("network_not_allowed")
                response.raise_for_status()
                payload = await response.json()
    except PCPowerDiscoveryError:
        raise
    except TimeoutError as err:
        raise PCPowerDiscoveryError("cannot_connect") from err
    except (ClientError, OSError) as err:
        raise PCPowerDiscoveryError("cannot_connect") from err
    except ValueError as err:
        raise PCPowerDiscoveryError("invalid_response") from err

    discovery = _normalize_discovery_payload(payload, fallback_host=host, fallback_port=agent_port)
    discovery.certificate_fingerprint = fingerprint
    return discovery


async def async_verify_upgrade(
    session: ClientSession,
    *,
    discovery: PCPowerDiscoveryInfo,
    api_token: str,
    timeout: float = 5,
) -> bool:
    """Authenticate a legacy pairing's TLS identity without sending the old secret."""
    if not api_token:
        return False
    nonce = secrets.token_hex(32)
    try:
        async with asyncio.timeout(timeout):
            async with session.post(
                f"https://{discovery.host}:{discovery.agent_port}/v1/pairing/upgrade",
                headers={"Accept": "application/json"}, json={"nonce": nonce},
                ssl=_pin(discovery.certificate_fingerprint), allow_redirects=False,
            ) as response:
                if response.status != 200:
                    return False
                payload = await response.json()
        proof = payload.get("proof") if isinstance(payload, dict) else None
        if not isinstance(proof, str) or not re.fullmatch(r"[0-9a-f]{64}", proof):
            return False
        transcript = (b"pc-power-free/tls-upgrade/v1\0" + bytes.fromhex(nonce)
                      + bytes.fromhex(discovery.certificate_fingerprint))
        expected = hmac.digest(api_token.encode("utf-8"), transcript, "sha256").hex()
        return hmac.compare_digest(proof, expected)
    except (TimeoutError, ClientError, OSError, ValueError, PCPowerAuthError):
        return False


async def async_exchange_pairing_code(
    session: ClientSession,
    *,
    host: str,
    agent_port: int = DEFAULT_AGENT_PORT,
    pairing_code: str,
    certificate_fingerprint: str,
    timeout: int = 5,
) -> PCPowerPairingResult:
    """Exchange a temporary pairing code for the long-lived API token."""
    try:
        async with asyncio.timeout(timeout):
            async with session.post(
                f"https://{host}:{agent_port}/v1/pairing/exchange",
                headers={"Accept": "application/json"},
                ssl=_pin(certificate_fingerprint), allow_redirects=False,
                json={"pairing_code": pairing_code},
            ) as response:
                if response.status == 400:
                    raise PCPowerPairingError("invalid_pairing_code")
                if response.status == 401:
                    raise PCPowerPairingError("invalid_pairing_code")
                if response.status == 403:
                    raise PCPowerPairingError("network_not_allowed")
                if response.status == 410:
                    raise PCPowerPairingError("pairing_code_expired")
                if response.status == 429:
                    raise PCPowerPairingError("pairing_code_blocked")
                if response.status == 412:
                    raise PCPowerPairingError("no_pairing_code")
                response.raise_for_status()
                payload = await response.json()
    except PCPowerPairingError:
        raise
    except TimeoutError as err:
        raise PCPowerPairingError("cannot_connect") from err
    except ClientError as err:
        raise PCPowerPairingError("cannot_connect") from err
    except ValueError as err:
        raise PCPowerPairingError("invalid_response") from err

    if not isinstance(payload, dict):
        raise PCPowerPairingError("invalid_response")
    api_token = str(payload.get("api_token", "")).strip()
    if len(api_token) < 16:
        raise PCPowerPairingError("invalid_response")

    discovery = _normalize_discovery_payload(payload, fallback_host=host, fallback_port=agent_port)
    discovery.certificate_fingerprint = certificate_fingerprint
    try:
        broadcast_port = int(payload.get("broadcast_port", DEFAULT_BROADCAST_PORT))
    except (TypeError, ValueError) as err:
        raise PCPowerPairingError("invalid_response") from err

    return PCPowerPairingResult(
        discovery=discovery,
        api_token=api_token,
        broadcast_port=broadcast_port,
    )


class PCPowerClient:
    """Local network client for the local agent."""

    def __init__(
        self,
        session: ClientSession,
        *,
        host: str,
        agent_port: int,
        api_token: str,
        mac_address: str,
        broadcast_address: str,
        broadcast_port: int,
        discovery_subnets: str | Iterable[str] | None = None,
        machine_id: str | None = None,
        certificate_fingerprint: str | None = None,
        timeout: int = 5,
    ) -> None:
        self._session = session
        self._host = host
        self._agent_port = agent_port
        self._api_token = api_token
        self._mac_address = format_mac(mac_address)
        self._normalized_mac_address = normalize_mac(mac_address)
        self._broadcast_address = broadcast_address
        self._broadcast_port = broadcast_port
        self._discovery_subnets = parse_discovery_subnets(discovery_subnets)
        self._machine_id = str(machine_id or "").strip().lower() or None
        self._certificate_fingerprint = certificate_fingerprint
        self._timeout = timeout
        self._next_discovery_at = 0.0

    @property
    def host(self) -> str:
        """Return the configured host."""
        return self._host

    @property
    def agent_port(self) -> int:
        """Return the configured agent port."""
        return self._agent_port

    @property
    def certificate_fingerprint(self) -> str | None:
        """Return the pinned or secret-authenticated TLS identity."""
        return self._certificate_fingerprint

    @property
    def base_url(self) -> str:
        """Return the base URL for the local agent."""
        return f"https://{self._host}:{self._agent_port}"

    async def async_wake(self) -> None:
        """Send the magic packet to the PC."""
        await asyncio.to_thread(
            send_magic_packet,
            self._mac_address,
            self._broadcast_address,
            self._broadcast_port,
        )
        self._next_discovery_at = 0.0

    async def async_shutdown(self, *, force: bool | None = None, delay_seconds: int | None = None) -> None:
        """Ask the agent to shut the PC down."""
        await self._async_post("shutdown", {key: value for key, value in
            {"force": force, "delay_seconds": delay_seconds}.items() if value is not None})

    async def async_restart(self, *, force: bool | None = None, delay_seconds: int | None = None) -> None:
        """Ask the agent to restart the PC."""
        await self._async_post("restart", {key: value for key, value in
            {"force": force, "delay_seconds": delay_seconds}.items() if value is not None})

    async def async_get_status(self) -> dict[str, Any]:
        """Return the latest online status.

        A network failure is treated as the PC being offline so the entity can
        still show an explicit off state instead of becoming unavailable.
        """
        payload = await self._async_get_status_payload()
        if payload is None:
            return {"online": False, "reachable": False,
                    "upgrade_pending": not bool(self._certificate_fingerprint)}
        return self._normalize_status_payload(payload)

    async def _async_post(self, action: str, payload: dict[str, Any]) -> None:
        """Send an authenticated POST action to the agent."""
        # Locate and authenticate before sending a non-idempotent power command.
        if await self._async_get_status_payload() is None:
            raise PCPowerCommandError("Unable to reach the local agent")
        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    f"{self.base_url}/v1/power/{action}",
                    headers=self._headers(),
                    json=payload,
                    ssl=_pin(self._certificate_fingerprint), allow_redirects=False,
                ) as response:
                    if response.status in (401, 403):
                        raise PCPowerAuthError("The agent rejected the token")
                    if response.status == 423:
                        raise PCPowerCommandError(
                            "Power commands are currently blocked by the local guard"
                        )

                    if response.status != 202:
                        try:
                            error = await response.json()
                        except (ValueError, ClientError):
                            error = {}
                        detail = error.get("error") if isinstance(error, dict) else None
                        raise PCPowerCommandError(detail or f"Agent rejected command (HTTP {response.status})")
                    return
        except PCPowerAuthError:
            raise
        except TimeoutError as err:
            raise PCPowerCommandError("Command response timed out; result unknown, not retried") from err
        except ServerFingerprintMismatch as err:
            raise PCPowerAuthError("The agent certificate changed; pair again") from err
        except ClientError as err:
            raise PCPowerCommandError("Connection lost; command result unknown, not retried") from err

    def _headers(self) -> dict[str, str]:
        """Build the auth headers for the agent."""
        headers = {"Accept": "application/json"}
        if self._api_token:
            headers["Authorization"] = f"Bearer {self._api_token}"
        return headers

    async def _async_get_status_payload(self) -> dict[str, Any] | None:
        """Fetch the status payload, retrying with discovery if needed."""
        auth_error = None
        try:
            payload = await self._async_fetch_status_from_host(self._host)
        except PCPowerAuthError as err:
            auth_error = err
            payload = None
        if payload is not None:
            return payload

        discovered_host = await self.async_discover_host()
        if not discovered_host:
            if auth_error:
                raise auth_error
            return None

        return await self._async_fetch_status_from_host(discovered_host)

    async def _async_fetch_status_from_host(self, host: str) -> dict[str, Any] | None:
        """Fetch the status from a specific host."""
        if not host:
            return None

        if not self._certificate_fingerprint and not await self._async_upgrade_identity(host, self._timeout):
            return None

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(
                    f"https://{host}:{self._agent_port}/v1/status",
                    headers=self._headers(),
                    ssl=_pin(self._certificate_fingerprint), allow_redirects=False,
                ) as response:
                    if response.status in (401, 403):
                        raise PCPowerAuthError("Token rejected" if response.status == 401 else "Client network is not allowed")

                    if response.status != 200:
                        raise PCPowerCommandError(f"Agent status failed (HTTP {response.status})")
                    payload = await response.json()
        except PCPowerAuthError:
            raise
        except ServerFingerprintMismatch as err:
            raise PCPowerAuthError("The agent certificate changed; pair again") from err
        except (TimeoutError, ClientError):
            return None
        except ValueError as err:
            raise PCPowerCommandError("The agent returned invalid JSON") from err

        if not isinstance(payload, dict):
            raise PCPowerCommandError("The agent returned a non-object status")
        if self._machine_id and payload.get(STATUS_MACHINE_ID) != self._machine_id:
            raise PCPowerAuthError("The agent identity changed; pair again")
        self._host = host
        return payload

    async def async_discover_host(self, *, force: bool = False) -> str | None:
        """Try to find the current host IP for the configured PC."""
        now = time.monotonic()
        if not force and now < self._next_discovery_at:
            return None

        self._next_discovery_at = now + DISCOVERY_COOLDOWN_SECONDS

        subnets = self._discovery_subnets or self._infer_discovery_subnets()
        if not subnets:
            return None

        semaphore = asyncio.Semaphore(DISCOVERY_CONCURRENCY)
        addresses = iter(islice((str(address) for subnet in subnets for address in subnet.hosts()),
                                DISCOVERY_MAX_ADDRESSES))
        async def worker():
            for host in addresses:
                result = await self._async_probe_candidate(host, semaphore)
                if result:
                    return result
            return None
        tasks = [asyncio.create_task(worker()) for _ in range(DISCOVERY_CONCURRENCY)]

        try:
            async with asyncio.timeout(DISCOVERY_DEADLINE_SECONDS):
                for completed_task in asyncio.as_completed(tasks):
                    result = await completed_task
                    if result is not None:
                        self._host = result
                        self._next_discovery_at = 0.0
                        return result
        except TimeoutError:
            return None
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

        return None

    async def _async_probe_candidate(
        self,
        host: str,
        semaphore: asyncio.Semaphore,
    ) -> str | None:
        """Probe a candidate host without exposing the API token."""
        if host == self._host:
            return None

        async with semaphore:
            if not self._certificate_fingerprint:
                return host if await self._async_upgrade_identity(host, DISCOVERY_TIMEOUT_SECONDS) else None
            try:
                async with asyncio.timeout(DISCOVERY_TIMEOUT_SECONDS):
                    async with self._session.get(
                        f"https://{host}:{self._agent_port}/v1/discovery",
                        headers={"Accept": "application/json"},
                        ssl=_pin(self._certificate_fingerprint), allow_redirects=False,
                    ) as response:
                        if response.status != 200:
                            return None
                        payload = await response.json()
            except (TimeoutError, ClientError, ValueError, PCPowerAuthError):
                return None

        if not isinstance(payload, dict):
            return None
        payload_machine_id = str(payload.get(STATUS_MACHINE_ID, "")).strip().lower()
        if self._machine_id and payload_machine_id:
            return host if payload_machine_id == self._machine_id else None

        candidate_macs: set[str] = set()
        raw_macs = payload.get("mac_addresses", [])
        if not isinstance(raw_macs, list):
            return None
        for item in raw_macs:
            if not isinstance(item, str):
                continue
            try:
                candidate_macs.add(normalize_mac(item))
            except PCPowerError:
                continue
        if self._normalized_mac_address in candidate_macs:
            return host
        return None

    async def _async_upgrade_identity(self, host: str, timeout: float) -> bool:
        """Upgrade without re-pairing; failure stays pending, never falls back to HTTP."""
        try:
            async with asyncio.timeout(timeout):
                discovery = await async_fetch_discovery_info(
                    self._session, host=host, agent_port=self._agent_port)
                if self._machine_id:
                    if discovery.machine_id != self._machine_id:
                        return False
                elif self._mac_address not in discovery.mac_addresses:
                    return False
                if not await async_verify_upgrade(self._session, discovery=discovery, api_token=self._api_token):
                    return False
        except (TimeoutError, PCPowerDiscoveryError, OSError):
            return False
        # A concurrent discovery must not replace an identity already established.
        if self._certificate_fingerprint and self._certificate_fingerprint != discovery.certificate_fingerprint:
            return False
        self._certificate_fingerprint = discovery.certificate_fingerprint
        return True

    def _infer_discovery_subnets(self) -> tuple[ipaddress.IPv4Network, ...]:
        """Infer discovery subnets from the current host when possible."""
        if self._host:
            try:
                host_ip = ipaddress.ip_address(self._host)
            except ValueError:
                return ()
            if isinstance(host_ip, ipaddress.IPv4Address):
                return (ipaddress.ip_network(f"{host_ip}/24", strict=False),)
        return ()

    def _normalize_status_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Normalize the status payload into entity data."""
        payload_machine_id = str(payload.get(STATUS_MACHINE_ID, "")).strip().lower()
        if payload_machine_id and not self._machine_id:
            self._machine_id = payload_machine_id

        return {
            "online": bool(payload.get("online", True)),
            "reachable": True,
            "host": self._host,
            "hostname": payload.get("hostname"),
            "agent_version": payload.get("agent_version"),
            "booted_at": payload.get(STATUS_BOOTED_AT),
            "capabilities": normalize_agent_capabilities(payload.get(STATUS_CAPABILITIES)),
            "command_guard_active": bool(payload.get("command_guard_active", False)),
            "command_guard_mode": payload.get("command_guard_mode"),
            "command_guard_until_ts": payload.get("command_guard_until_ts"),
            "last_command": payload.get("last_command"),
            "last_command_at": payload.get(STATUS_LAST_COMMAND_AT),
            "mac_addresses": payload.get("mac_addresses", []),
            "machine_id": payload_machine_id or self._machine_id,
            "platform": normalize_agent_platform(payload.get(STATUS_PLATFORM)),
            "uptime_seconds": payload.get(STATUS_UPTIME_SECONDS),
        }
