from __future__ import annotations

import datetime

import msgspec

from multica_py.models.issue_activity import TaskCancellationActor


class AgentSkill(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    enabled: bool


class AgentTask(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    status: str
    issue_id: str
    issue_title: str | None = None
    issue_description: str | None = None
    issue_status: str | None = None
    issue_assignee_type: str | None = None
    issue_assignee_id: str | None = None
    issue_changed_fields: tuple[str, ...] = ()
    issue_state_delta_known: bool | None = None
    failure_reason: str | None = None
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    cancelled_by: TaskCancellationActor | None = None
    _wire_presence: tuple[tuple[str, str], ...] = msgspec.field(default_factory=tuple)


class AgentConversationStarter(msgspec.Struct, frozen=True, kw_only=True):
    label: str
    prompt: str
