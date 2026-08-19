from __future__ import annotations

import msgspec

__all__ = ["McpServer"]


class McpServer(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    transport: str
    enabled: bool | None = None
