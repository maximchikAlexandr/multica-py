from __future__ import annotations

import datetime
from collections.abc import Mapping

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
    wakeup_id: str | None = None
    supplement_capability: str | None = None
    supplement_comment_ids: tuple[str, ...] = ()
    can_supplement: bool | None = None
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


class SecretEnvironment(dict[str, str]):
    """Mapping returned by the audited agent-env operations.

    Values remain available through the approved mapping API, but accidental
    repr/logging of the result never exposes credential material.
    """

    def __init__(self, values: Mapping[str, str]) -> None:
        super().__init__(values)

    def __repr__(self) -> str:
        keys = ", ".join(f"{key!r}: '***'" for key in self)
        return f"SecretEnvironment({{{keys}}})"

    __str__ = __repr__
