from __future__ import annotations

import msgspec

from multica_py.sentinels import Unset, UnsetType


class LabelUpdateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str | UnsetType = Unset
    color: str | UnsetType = Unset

    def __post_init__(self) -> None:
        if self.name is None:
            raise TypeError("name must be non-null")
        if self.color is None:
            raise TypeError("color must be non-null")
