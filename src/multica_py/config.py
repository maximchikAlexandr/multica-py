from __future__ import annotations

import datetime
import pathlib
from collections.abc import Mapping
from urllib.parse import urlparse

import msgspec

from multica_py.enums import CompatibilityPolicy


def _to_env_tuple(env: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(env.items()))


_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _validate_server_url(url: str) -> None:
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    if scheme == "https":
        return
    if scheme == "http" and host in _LOCAL_HOSTS:
        return
    raise ValueError(
        f"server_url must use https (or http for localhost/127.0.0.1/[::1]); got {url!r}"
    )


class ClientConfig(msgspec.Struct, frozen=True, kw_only=True):
    executable: pathlib.Path | str = "multica"
    server_url: str | None = None
    workspace_id: str | None = None
    profile: str | None = None
    cwd: pathlib.Path | None = None
    environment: tuple[tuple[str, str], ...] = ()
    timeout: datetime.timedelta | None = None
    compatibility: CompatibilityPolicy = CompatibilityPolicy.ignore
    min_cli_version: str | None = None
    max_cli_version: str | None = None
    debug: bool = False
    encoding: str = "utf-8"
    max_processes: int = 4

    def __post_init__(self) -> None:
        if isinstance(self.environment, Mapping):
            object.__setattr__(self, "environment", _to_env_tuple(self.environment))
        if self.server_url is not None:
            _validate_server_url(self.server_url)
