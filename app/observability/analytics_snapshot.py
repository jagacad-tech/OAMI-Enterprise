"""Serialization helpers for passive analytics snapshots."""

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from typing import Any


def json_safe(value: Any):
    """Return a recursively JSON-safe value without changing the source snapshot."""
    if is_dataclass(value):
        return json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def snapshot_to_dict(snapshot):
    """Copy every available MarketSnapshot field for historical analysis."""
    return json_safe(snapshot) if snapshot is not None else None
