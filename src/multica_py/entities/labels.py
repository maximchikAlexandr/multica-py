from __future__ import annotations

from multica_py.entities._base import _BoundEntity


class Label(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    color: str | None = None

    _PUBLIC_FIELDS = ("id", "name", "color")
