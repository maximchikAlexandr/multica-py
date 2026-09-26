from __future__ import annotations

from typing import cast

import msgspec

from multica_py.sentinels import Unset, UnsetType


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


class DaemonLaunchOptions(msgspec.Struct, frozen=True, kw_only=True):
    """Presence-aware controls shared by daemon start and restart."""

    foreground: bool | UnsetType = Unset
    identity: str | UnsetType = Unset
    data_dir: str | UnsetType = Unset
    pid_file: str | UnsetType = Unset
    poll_interval: str | float | UnsetType = Unset
    heartbeat_interval: str | float | UnsetType = Unset
    watchdog_interval: str | float | UnsetType = Unset
    max_concurrent_tasks: int | UnsetType = Unset
    update: bool | UnsetType = Unset
    reload: bool | UnsetType = Unset

    def __post_init__(self) -> None:
        for name in ("foreground", "update", "reload"):
            value = cast("object", getattr(self, name))
            if value is not Unset and not isinstance(value, bool):
                raise TypeError(f"{name} must be a bool or Unset")
        for name in ("identity", "data_dir", "pid_file"):
            value = cast("object", getattr(self, name))
            if value is not Unset and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be nonblank when provided")
        for name in ("poll_interval", "heartbeat_interval", "watchdog_interval"):
            value = cast("object", getattr(self, name))
            if value is not Unset and (
                not isinstance(value, (str, float, int)) or isinstance(value, bool)
            ):
                raise TypeError(f"{name} must be a duration string or number")
        concurrency = cast("object", self.max_concurrent_tasks)
        if concurrency is not Unset and (
            not isinstance(concurrency, int) or isinstance(concurrency, bool) or concurrency < 1
        ):
            raise ValueError("max_concurrent_tasks must be a positive integer")

    def to_argv(self) -> tuple[str, ...]:
        """Render only present controls in the reviewed daemon flag order."""

        args: list[str] = []
        for name, flag in (
            ("foreground", "--foreground"),
            ("identity", "--identity"),
            ("data_dir", "--data-dir"),
            ("pid_file", "--pid-file"),
            ("poll_interval", "--poll-interval"),
            ("heartbeat_interval", "--heartbeat-interval"),
            ("watchdog_interval", "--watchdog-interval"),
            ("max_concurrent_tasks", "--max-concurrent-tasks"),
            ("update", "--update"),
            ("reload", "--reload"),
        ):
            value = cast("object", getattr(self, name))
            if value is Unset:
                continue
            if isinstance(value, bool):
                args.append(f"{flag}={'true' if value else 'false'}")
                continue
            args.extend((flag, str(value)))
        return tuple(args)


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


class SquadMember(msgspec.Struct, frozen=True, kw_only=True):
    member_id: str
    member_type: str
    role: str


class MaintenanceVersion(msgspec.Struct, frozen=True, kw_only=True):
    version: str
    commit: str | None = None
    build_date: str | None = None
