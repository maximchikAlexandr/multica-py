from __future__ import annotations

import msgspec

__all__ = ["SkillFile", "SkillSearchResult"]


class SkillFile(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    path: str
    content: str | None = None


class SkillSearchResult(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    url: str
    source: str
    install_count: int
    description: str = ""
