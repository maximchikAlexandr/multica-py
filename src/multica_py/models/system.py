from __future__ import annotations

import datetime

import msgspec


class RepositoryRecord(msgspec.Struct, frozen=True, kw_only=True):
    url: str
    description: str | None = None


class RepositoryMutationResult(msgspec.Struct, frozen=True, kw_only=True):
    workspace_id: str
    added: tuple[RepositoryRecord, ...] = ()
    updated: tuple[RepositoryRecord, ...] = ()
    removed: tuple[RepositoryRecord, ...] = ()
    repos: tuple[RepositoryRecord, ...] = ()


class RuntimeDefinition(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    version: str | None = None


class RuntimeUsage(msgspec.Struct, frozen=True, kw_only=True):
    date: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int


class RuntimeActivity(msgspec.Struct, frozen=True, kw_only=True):
    hour: int
    count: int


class RuntimeUpdate(msgspec.Struct, frozen=True, kw_only=True):
    target_version: str
    wait: bool = False


class RuntimeUpdateResult(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    status: str
    output: str | None = None
    error: str | None = None


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


class UserProfile(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    email: str | None = None
    profile_description: str = ""


class UserProfileUpdate(msgspec.Struct, frozen=True, kw_only=True):
    description: str | msgspec.UnsetType = msgspec.UNSET


class SquadData(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    member_count: int = 0
    leader_id: str | None = None
    archived_at: datetime.datetime | None = None


class WorkspaceMemberData(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    role: str | None = None
    user_id: str | None = None
    email: str | None = None


class SquadMember(msgspec.Struct, frozen=True, kw_only=True):
    member_id: str
    member_type: str
    role: str


class MaintenanceVersion(msgspec.Struct, frozen=True, kw_only=True):
    version: str
    commit: str | None = None
    build_date: str | None = None
