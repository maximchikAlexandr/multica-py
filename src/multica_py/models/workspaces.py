from __future__ import annotations

import msgspec


class WorkspaceData(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    description: str | None = None
