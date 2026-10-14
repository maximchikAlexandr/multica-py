from __future__ import annotations

import datetime
import json
from typing import Literal, cast
from urllib.parse import urlsplit

import msgspec

from multica_py.types import MetadataValue

PropertyListValue = tuple[str, ...]
PropertyListType = Literal["multi_text", "multi_url"]
PropertyValueType = MetadataValue | PropertyListValue

__all__ = [
    "PropertyDefinition",
    "PropertyListType",
    "PropertyListValue",
    "PropertyOption",
    "PropertyValue",
    "PropertyValueType",
    "normalize_property_input",
]


def normalize_property_input(value: object, property_type: PropertyListType | None) -> str:
    """Validate and canonicalize a discriminated list-property input."""
    if property_type is None:
        if type(value) is str:
            return value
        if type(value) is not tuple:
            raise TypeError("value must be a string")
        raise TypeError("property_type is required for sequence values")
    if property_type not in {"multi_text", "multi_url"}:
        raise ValueError("property_type must be multi_text or multi_url")
    if value is None:
        raise TypeError("value cannot be null")
    if type(value) is str:
        items = _parse_property_list_string(value)
    elif type(value) is tuple:
        items = value
    else:
        raise TypeError("discriminated value must be a string or tuple of strings")
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
