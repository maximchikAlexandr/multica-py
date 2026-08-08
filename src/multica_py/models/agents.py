from __future__ import annotations

import datetime

import msgspec

from multica_py.sentinels import Unset, UnsetType


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
    name: str | UnsetType = Unset
    description: str | None | UnsetType = Unset

    def __post_init__(self) -> None:
        if self.name is None:
            raise TypeError("name must be non-null")


class AgentTask(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    status: str
    issue_id: str
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
