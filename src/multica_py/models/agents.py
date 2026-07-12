from __future__ import annotations

import datetime

import msgspec


class Agent(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    description: str | None = None
    skills: tuple[str, ...] = ()


class AgentCreateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    description: str | None = None


class AgentUpdateRequest(msgspec.Struct, frozen=True, kw_only=True):
    name: str | None = None
    description: str | None = None


class AgentTask(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    status: str
    issue_id: str
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
