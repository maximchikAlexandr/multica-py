from __future__ import annotations

import datetime

import msgspec


class AgentSkill(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    enabled: bool


class AgentTask(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    status: str
    issue_id: str
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
