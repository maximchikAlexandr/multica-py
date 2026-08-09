from __future__ import annotations

import msgspec

from multica_py.sentinels import Unset, UnsetType


class ProjectCreateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    description: str | None = None


class ProjectUpdateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str | UnsetType = Unset
    description: str | None | UnsetType = Unset

    def __post_init__(self) -> None:
        if self.name is None:
            raise TypeError("name must be non-null")
