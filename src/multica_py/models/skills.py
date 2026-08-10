from __future__ import annotations

import msgspec


class SkillFile(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    path: str
    content: str | None = None
