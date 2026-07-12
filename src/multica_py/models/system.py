from __future__ import annotations

import msgspec


class Repository(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    url: str | None = None


class RepositoryCheckoutResult(msgspec.Struct, frozen=True, kw_only=True):
    path: str
    branch: str
    success: bool


class RuntimeDefinition(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    version: str | None = None


class AttachmentResult(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    filename: str
    url: str | None = None


class DaemonStatus(msgspec.Struct, frozen=True, kw_only=True):
    running: bool = False
    pid: int | None = None
    uptime: float | None = None


class DaemonDiskUsageEntry(msgspec.Struct, frozen=True, kw_only=True):
    path: str
    size_bytes: int = 0


class AuthenticationStatus(msgspec.Struct, frozen=True, kw_only=True):
    authenticated: bool = False
    user_id: str | None = None
    token_type: str | None = None


class User(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    email: str | None = None


class Squad(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    member_count: int = 0


class MaintenanceVersion(msgspec.Struct, frozen=True, kw_only=True):
    version: str
    commit: str | None = None
    build_date: str | None = None
