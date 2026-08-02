from __future__ import annotations

import msgspec


class Workspace(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    description: str | None = None


class WorkspaceData(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    description: str | None = None


class WorkspaceMember(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    role: str | None = None
    user_id: str | None = None
    email: str | None = None
