from __future__ import annotations

JsonScalar = str | int | float | bool | None
# msgspec resolves concrete unions at decoder construction time; recursive
# aliases are not supported there. These are the JSON shapes accepted by the
# governed CLI payload fields.
JsonValue = JsonScalar | tuple[JsonScalar, ...] | dict[str, JsonScalar]
MetadataValue = str | int | float | bool | None
