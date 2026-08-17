from __future__ import annotations

import datetime
import math
import os
import pathlib
from collections.abc import Mapping
from typing import cast
from urllib.parse import urlparse

import msgspec

from multica_py.enums import CompatibilityPolicy
from multica_py.sentinels import Unset, UnsetType


def _to_env_tuple(
    env: Mapping[str, str] | tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    items = tuple(env.items()) if isinstance(env, Mapping) else env
    normalized: list[tuple[str, str]] = []
    for item in items:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError("environment entries must be (name, value) pairs")
        name, value = item
        if not isinstance(name, str) or not isinstance(value, str):
            raise TypeError("environment names and values must be strings")
        normalized.append((name, value))
    return tuple(sorted(normalized))


_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _validate_origin_url(url: str, field_name: str, *, normalize_trailing_slash: bool) -> str:
    if not isinstance(url, str):
        raise TypeError(f"{field_name} must be a string or None")
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    if not parsed.netloc or not host:
        raise ValueError(f"{field_name} must be an absolute URL; got {url!r}")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(f"{field_name} must not contain username or password userinfo")
    if parsed.query or parsed.fragment:
        raise ValueError(f"{field_name} must not contain query or fragment")
    if scheme != "https" and not (scheme == "http" and host in _LOCAL_HOSTS):
        raise ValueError(
            f"{field_name} must use https (or http for localhost/127.0.0.1/[::1]); got {url!r}"
        )
    if normalize_trailing_slash:
        return url.rstrip("/")
    return url


def _validate_server_url(url: str) -> str:
    return _validate_origin_url(url, "server_url", normalize_trailing_slash=False)


def _normalize_identifier(value: str | None | UnsetType, field_name: str) -> str | None | UnsetType:
    if value is Unset or value is None:
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    if not value.strip():
        raise ValueError(f"{field_name} must be nonblank when provided")
    return value


def _normalize_timeout(
    value: datetime.timedelta | float | None | UnsetType,
    field_name: str = "timeout",
) -> datetime.timedelta | None | UnsetType:
    if value is Unset or value is None:
        return value
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be a finite nonnegative number or timedelta")
    if isinstance(value, datetime.timedelta):
        seconds = value.total_seconds()
    elif isinstance(value, (int, float)):
        seconds = float(value)
    else:
        raise TypeError(f"{field_name} must be a finite nonnegative number or timedelta")
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError(f"{field_name} must be finite and nonnegative")
    try:
        return datetime.timedelta(seconds=seconds)
    except OverflowError as error:
        raise ValueError(f"{field_name} must be finite and nonnegative") from error


def _normalize_cwd(
    value: str | os.PathLike[str] | None | UnsetType,
) -> pathlib.Path | None | UnsetType:
    if value is Unset or value is None:
        return value
    if not isinstance(value, (str, os.PathLike)):
        raise TypeError("cwd must be a string, path-like value, or None")
    return pathlib.Path(value)


def _normalize_executable(value: str | os.PathLike[str]) -> str:
    if not isinstance(value, (str, os.PathLike)):
        raise TypeError("executable must be a string or path-like value")
    return os.fspath(value)


def _normalize_environment(
    value: Mapping[str, str] | tuple[tuple[str, str], ...] | UnsetType,
) -> tuple[tuple[str, str], ...] | UnsetType:
    if value is Unset:
        return value
    if not isinstance(value, (Mapping, tuple)):
        raise TypeError("environment must be a mapping or tuple of pairs")
    return _to_env_tuple(value)


def _validate_workspace_slug(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("workspace_slug must be a string or None")
    if not value.strip() or "/" in value or "\\" in value:
        raise ValueError("workspace_slug must be one nonblank URL path segment")
    return value


class OperationOptions(msgspec.Struct, frozen=True, kw_only=True):
    profile: str | None | UnsetType = Unset
    workspace_id: str | None | UnsetType = Unset
    timeout: datetime.timedelta | float | None | UnsetType = Unset
    cwd: str | os.PathLike[str] | None | UnsetType = Unset
    environment: Mapping[str, str] | tuple[tuple[str, str], ...] | UnsetType = Unset

    def __post_init__(self) -> None:
        msgspec.structs.force_setattr(
            self, "profile", _normalize_identifier(self.profile, "profile")
        )
        msgspec.structs.force_setattr(
            self,
            "workspace_id",
            _normalize_identifier(self.workspace_id, "workspace_id"),
        )
        msgspec.structs.force_setattr(self, "timeout", _normalize_timeout(self.timeout))
        msgspec.structs.force_setattr(self, "cwd", _normalize_cwd(self.cwd))
        msgspec.structs.force_setattr(self, "environment", _normalize_environment(self.environment))


class ClientConfig(msgspec.Struct, frozen=True, kw_only=True):
    """CLI settings for the execution target.

    ``executable`` and ``cwd`` name paths on that target. ``environment`` contains
    explicit target-process overrides; it does not replace the executor's own
    environment policy.
    """

    executable: str | os.PathLike[str] = "multica"
    server_url: str | None = None
    app_url: str | None = None
    workspace_slug: str | None = None
    workspace_id: str | None = None
    profile: str | None = None
    cwd: str | os.PathLike[str] | None = None
    environment: tuple[tuple[str, str], ...] = ()
    timeout: datetime.timedelta | None = None
    compatibility: CompatibilityPolicy = CompatibilityPolicy.ignore
    min_cli_version: str | None = None
    max_cli_version: str | None = None
    debug: bool = False
    encoding: str = "utf-8"
    max_processes: int = 4

    def __post_init__(self) -> None:
        msgspec.structs.force_setattr(self, "executable", _normalize_executable(self.executable))
        msgspec.structs.force_setattr(self, "cwd", _normalize_cwd(self.cwd))
        if isinstance(self.environment, Mapping):
            msgspec.structs.force_setattr(self, "environment", _to_env_tuple(self.environment))
        if self.server_url is not None:
            normalized_server_url = _validate_server_url(self.server_url)
            if normalized_server_url is not None:
                msgspec.structs.force_setattr(self, "server_url", normalized_server_url)
        if self.app_url is not None:
            msgspec.structs.force_setattr(
                self,
                "app_url",
                _validate_origin_url(self.app_url, "app_url", normalize_trailing_slash=True),
            )
        msgspec.structs.force_setattr(
            self, "workspace_slug", _validate_workspace_slug(self.workspace_slug)
        )


def _apply_operation_options(
    config: ClientConfig,
    options: OperationOptions | None,
) -> ClientConfig:
    """Return an immutable config snapshot with present operation overrides."""
    if options is None:
        return msgspec.structs.replace(config)
    changes: dict[str, object] = {}
    for field in msgspec.structs.fields(OperationOptions):
        field_name = field.name
        value = cast("object", getattr(options, field_name))
        if value is not Unset:
            changes[field_name] = value
    return msgspec.structs.replace(config, **changes)
