from __future__ import annotations

import datetime

import msgspec


class AgentSkill(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    enabled: bool


class AgentCreateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    description: str | None = None
    runtime_id: str | None = None
    model: str | None = None


class AgentUpdateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str | None = None
    description: str | None = None


class AgentTask(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    status: str
    issue_id: str
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None


class AgentData(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    description: str | None = None
    skill_refs: tuple[AgentSkill, ...] = ()
    archived_at: datetime.datetime | None = None
