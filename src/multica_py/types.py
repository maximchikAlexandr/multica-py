from __future__ import annotations

from collections.abc import Mapping

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | tuple["JsonValue", ...] | Mapping[str, "JsonValue"]
MetadataValue = str | int | float | bool | None
