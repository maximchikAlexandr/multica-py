from __future__ import annotations

from multica_py.entities._base import _BoundEntity


class Label(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    color: str | None = None
    description: str | None = None
    # Response values stay open so newer server scopes remain decodable.
    resource_type: str | None = None
