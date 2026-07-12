from __future__ import annotations

import datetime
import pathlib
from collections.abc import Mapping

import msgspec

from multica_py.enums import CompatibilityPolicy


def _to_env_tuple(env: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(env.items()))


class ClientConfig(msgspec.Struct, frozen=True, kw_only=True):
    executable: pathlib.Path | str = "multica"
    server_url: str | None = None
    workspace_id: str | None = None
    profile: str | None = None
    cwd: pathlib.Path | None = None
    environment: tuple[tuple[str, str], ...] = ()
    timeout: datetime.timedelta | None = None
    compatibility: CompatibilityPolicy = CompatibilityPolicy.ignore
    debug: bool = False
    encoding: str = "utf-8"
    max_processes: int = 4

    def __post_init__(self) -> None:
        if isinstance(self.environment, Mapping):
            object.__setattr__(self, "environment", _to_env_tuple(self.environment))
