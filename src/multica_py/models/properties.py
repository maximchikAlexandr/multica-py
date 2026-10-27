from __future__ import annotations

import datetime
import json
from collections.abc import Sequence
from typing import Literal, cast
from urllib.parse import urlsplit

import msgspec

from multica_py.exceptions import OutputShapeError
from multica_py.types import MetadataValue

PropertyListValue = tuple[str, ...]
PropertyListType = Literal["multi_text", "multi_url"]
PropertyValueType = MetadataValue | PropertyListValue
PropertyInputValue = str | Sequence[str]

__all__ = [
    "PropertyDefinition",
    "PropertyInputValue",
    "PropertyListType",
    "PropertyListValue",
    "PropertyOption",
    "PropertyValue",
    "PropertyValueType",
    "decode_property_value",
    "normalize_property_input",
]


def normalize_property_input(value: object, property_type: PropertyListType | None) -> str:
    """Validate and canonicalize a discriminated list-property input."""
    if property_type is None:
        if type(value) is str:
            return value
        if isinstance(value, Sequence) and not isinstance(value, str):
            raise TypeError("property_type is required for sequence values")
        raise TypeError("value must be a string")
    if property_type not in {"multi_text", "multi_url"}:
        raise ValueError("property_type must be multi_text or multi_url")
    if value is None:
        raise TypeError("value cannot be null")
    if type(value) is str:
        items = _parse_property_list_string(value)
    elif isinstance(value, Sequence):
        items = tuple(value)
    else:
        raise TypeError("discriminated value must be a string or sequence of strings")
    if not items:
        raise ValueError("value must contain at least one string")
    if any(type(item) is not str for item in items):
        raise TypeError("value tuple must contain only strings")
    unique: list[str] = []
    for item in items:
        if item not in unique:
            unique.append(item)
    if len(unique) > 20:
        raise ValueError("value cannot contain more than 20 unique strings")
    if property_type == "multi_text":
        if any(not item.strip() for item in unique):
            raise ValueError("multi_text values cannot contain blank strings")
        if any(len(item) > 2000 for item in unique):
            raise ValueError("multi_text values cannot exceed 2000 characters")
    else:
        for item in unique:
            if len(item) > 2048:
                raise ValueError("multi_url values cannot exceed 2048 characters")
            parsed = urlsplit(item)
            if (
                parsed.scheme.lower() not in {"http", "https"}
                or not parsed.netloc
                or any(char.isspace() for char in item)
            ):
                raise ValueError("multi_url values must be HTTP(S) URLs")
    return json.dumps(unique, ensure_ascii=False, separators=(",", ":"))


def decode_property_value(property_type: str, value: object) -> PropertyValueType:
    """Decode one wire property value into the typed public representation."""
    if property_type in {"multi_text", "multi_url"}:
        if not isinstance(value, (list, tuple)) or any(type(item) is not str for item in value):
            raise OutputShapeError("list property value must be an array of strings")
        return tuple(cast("str", item) for item in value)
    if value is None or type(value) in {str, int, float, bool}:
        return cast("MetadataValue", value)
    raise OutputShapeError("scalar property value must be a scalar")


def _parse_property_list_string(value: str) -> tuple[str, ...]:
    if value.startswith("["):
        try:
            parsed = cast("object", json.loads(value))
        except json.JSONDecodeError as error:
            raise ValueError("list property JSON value is invalid") from error
        if type(parsed) is not list:
            raise TypeError("list property JSON value must be an array")
        if any(type(item) is not str for item in parsed):
            raise TypeError("list property JSON value must contain strings")
        return cast("tuple[str, ...]", tuple(parsed))
    return tuple(value.split(","))


class PropertyOption(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    color: str = ""


class PropertyDefinition(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    type: str
    description: str = ""
    icon: str = ""
    options: tuple[PropertyOption, ...] = ()
    position: float = 0.0
    archived: bool = False
    usage_count: int = 0
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


class PropertyValue(msgspec.Struct, frozen=True, kw_only=True):
    property_id: str
    name: str
    type: str
    value: PropertyValueType
    display: str = ""
    archived: bool = False
