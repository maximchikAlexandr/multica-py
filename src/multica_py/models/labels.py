from __future__ import annotations

import msgspec


class LabelData(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    color: str | None = None
