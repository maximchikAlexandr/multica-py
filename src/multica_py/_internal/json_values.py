"""Shared recursive JSON value coercion used by wire decoders."""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import cast

import msgspec

from multica_py.entities._base import _is_mapping
from multica_py.types import JsonValue

__all__ = ["_coerce_json_value"]


_COERCE_MAX_DEPTH = 100


def _coerce_json_value(value: object, *, field_name: str, _depth: int = 0) -> JsonValue:
    if _depth > _COERCE_MAX_DEPTH:
        raise msgspec.ValidationError(f"{field_name} exceeds maximum nesting depth")
    if isinstance(value, float) and not math.isfinite(value):
        raise msgspec.ValidationError(f"{field_name} must contain only finite JSON numbers")
    if value is None or isinstance(value, (str, int, float, bool)):
        return cast("JsonValue", value)
    if isinstance(value, (list, tuple)):
        return tuple(
            _coerce_json_value(item, field_name=field_name, _depth=_depth + 1) for item in value
        )
    if _is_mapping(value):
        result: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise msgspec.ValidationError(f"{field_name} object keys must be strings")
            result[key] = _coerce_json_value(item, field_name=field_name, _depth=_depth + 1)
        return MappingProxyType(result)
    raise msgspec.ValidationError(f"{field_name} must contain only JSON values")
