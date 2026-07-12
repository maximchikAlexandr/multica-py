from __future__ import annotations

import msgspec


class Skill(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    description: str | None = None
    file_count: int = 0


class SkillFile(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    path: str
    content: str | None = None


class SkillCreateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    description: str | None = None


class SkillUpdateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str | None = None
    description: str | None = None
