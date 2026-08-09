from __future__ import annotations

import msgspec

from multica_py.sentinels import Unset, UnsetType


class SkillFile(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    path: str
    content: str | None = None


class SkillCreateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    description: str | None = None


class SkillUpdateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str | UnsetType = Unset
    description: str | None | UnsetType = Unset

    def __post_init__(self) -> None:
        if self.name is None:
            raise TypeError("name must be non-null")
