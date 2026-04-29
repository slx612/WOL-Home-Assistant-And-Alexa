"""Shared platform metadata helpers for PC Power Free."""

from __future__ import annotations

from collections.abc import Iterable

DEFAULT_PLATFORM_LABEL = "Device"
DEFAULT_PLATFORM_MODEL = "Network device"
PLATFORM_LABELS = {
    "windows": "Windows",
    "linux": "Linux",
    "dsm": "DSM",
}
PLATFORM_MODELS = {
    "windows": "Windows PC",
    "linux": "Linux host",
    "dsm": "Synology DSM",
}


def normalize_agent_platform(value: object) -> str | None:
    """Normalize an agent platform string."""
    if not isinstance(value, str):
        return None
    platform = value.strip().lower()
    return platform or None


def normalize_agent_capabilities(value: object) -> tuple[str, ...]:
    """Normalize an agent capabilities payload."""
    raw_values: Iterable[object]
    if isinstance(value, str):
        raw_values = [value]
    elif isinstance(value, (list, tuple, set)):
        raw_values = value
    else:
        raw_values = ()

    normalized: list[str] = []
    for item in raw_values:
        if not isinstance(item, str):
            continue
        capability = item.strip().lower()
        if capability and capability not in normalized:
            normalized.append(capability)
    return tuple(normalized)


def platform_label(platform: str | None) -> str:
    """Return a short display label for the platform."""
    return PLATFORM_LABELS.get(platform or "", DEFAULT_PLATFORM_LABEL)


def platform_model(platform: str | None) -> str:
    """Return a device-model label for the platform."""
    return PLATFORM_MODELS.get(platform or "", DEFAULT_PLATFORM_MODEL)
