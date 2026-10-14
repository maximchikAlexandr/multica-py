from __future__ import annotations

import datetime

import msgspec

from multica_py.types import MetadataValue

PropertyListValue = tuple[str, ...]
PropertyValueType = MetadataValue | PropertyListValue

__all__ = [
    "PropertyDefinition",
    "PropertyListValue",
    "PropertyOption",
    "PropertyValue",
    "PropertyValueType",
]


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
