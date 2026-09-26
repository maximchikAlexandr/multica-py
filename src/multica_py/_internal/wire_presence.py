"""Small helpers for preserving omitted, null, and value wire states."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal

import msgspec

WirePresence = Literal["missing", "null", "value"]


def presence(value: object) -> WirePresence:
    """Classify a decoded msgspec value without collapsing falsey values."""

    if value is msgspec.UNSET:
        return "missing"
    if value is None:
        return "null"
    return "value"


def field_presence(payload: Mapping[str, object], name: str) -> WirePresence:
    """Classify a mapping field, including a key explicitly set to null."""

    return presence(payload.get(name, msgspec.UNSET))


def struct_presence(value: object, names: Sequence[str]) -> tuple[tuple[str, WirePresence], ...]:
    """Return presence for named struct attributes or mapping keys."""

    result: list[tuple[str, WirePresence]] = []
    for name in names:
        if isinstance(value, Mapping):
            result.append((name, field_presence(value, name)))
        else:
            result.append((name, presence(getattr(value, name, msgspec.UNSET))))
    return tuple(result)


__all__ = ["WirePresence", "field_presence", "presence", "struct_presence"]
