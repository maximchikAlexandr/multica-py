from __future__ import annotations

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | tuple["JsonValue", ...] | dict[str, "JsonValue"]
MetadataValue = str | int | float | bool | None
