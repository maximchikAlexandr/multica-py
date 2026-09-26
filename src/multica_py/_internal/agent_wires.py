from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import msgspec

from multica_py._internal.wire_presence import presence as _presence_seed
from multica_py.exceptions import OutputShapeError
from multica_py.models.agents import AgentConversationStarter, AgentSkill, AgentTask
from multica_py.models.issue_activity import TaskCancellationActor

if TYPE_CHECKING:
    from multica_py.entities.agents import Agent


class _AgentConversationStarterWire(msgspec.Struct, frozen=True, kw_only=True):
    label: str
    prompt: str


class _TaskCancellationActorWire(msgspec.Struct, frozen=True, kw_only=True):
    type: str
    id: str | None | msgspec.UnsetType = msgspec.UNSET
    name: str | None | msgspec.UnsetType = msgspec.UNSET


def _task_cancellation_actor_from_wire(
    wire: _TaskCancellationActorWire,
) -> TaskCancellationActor:
    if not wire.type.strip():
        raise OutputShapeError("cancelled_by.type must be nonblank")
    return TaskCancellationActor(
        type=wire.type,
        id=None if wire.id is msgspec.UNSET else wire.id,
        name=None if wire.name is msgspec.UNSET else wire.name,
    )


class _AgentTaskWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    status: str
    issue_id: str
    wakeup_id: str | None | msgspec.UnsetType = msgspec.UNSET
    supplement_capability: str | None | msgspec.UnsetType = msgspec.UNSET
    supplement_comment_ids: tuple[str, ...] | msgspec.UnsetType = msgspec.UNSET
    can_supplement: bool | None | msgspec.UnsetType = msgspec.UNSET
    issue_title: str | None | msgspec.UnsetType = msgspec.UNSET
    issue_description: str | None | msgspec.UnsetType = msgspec.UNSET
    issue_status: str | None | msgspec.UnsetType = msgspec.UNSET
    issue_assignee_type: str | None | msgspec.UnsetType = msgspec.UNSET
    issue_assignee_id: str | None | msgspec.UnsetType = msgspec.UNSET
    issue_changed_fields: tuple[str, ...] | None | msgspec.UnsetType = msgspec.UNSET
    issue_state_delta_known: bool | None | msgspec.UnsetType = msgspec.UNSET
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    cancelled_by: _TaskCancellationActorWire | msgspec.UnsetType = msgspec.UNSET
    failure_reason: str | None = None


def _agent_task_from_wire(wire: _AgentTaskWire) -> AgentTask:
    return AgentTask(
        id=wire.id,
        status=wire.status,
        issue_id=wire.issue_id,
        wakeup_id=None if wire.wakeup_id is msgspec.UNSET else wire.wakeup_id,
        supplement_capability=(
            None if wire.supplement_capability is msgspec.UNSET else wire.supplement_capability
        ),
        supplement_comment_ids=(
            () if wire.supplement_comment_ids is msgspec.UNSET else wire.supplement_comment_ids
        ),
        can_supplement=(None if wire.can_supplement is msgspec.UNSET else wire.can_supplement),
        issue_title=None if wire.issue_title is msgspec.UNSET else wire.issue_title,
        issue_description=(
            None if wire.issue_description is msgspec.UNSET else wire.issue_description
        ),
        issue_status=None if wire.issue_status is msgspec.UNSET else wire.issue_status,
        issue_assignee_type=(
            None if wire.issue_assignee_type is msgspec.UNSET else wire.issue_assignee_type
        ),
        issue_assignee_id=(
            None if wire.issue_assignee_id is msgspec.UNSET else wire.issue_assignee_id
        ),
        issue_changed_fields=(
            () if wire.issue_changed_fields in (msgspec.UNSET, None) else wire.issue_changed_fields
        ),
        issue_state_delta_known=(
            None if wire.issue_state_delta_known is msgspec.UNSET else wire.issue_state_delta_known
        ),
        failure_reason=wire.failure_reason,
        started_at=wire.started_at,
        completed_at=wire.completed_at,
        cancelled_by=(
            None
            if wire.cancelled_by is msgspec.UNSET
            else _task_cancellation_actor_from_wire(wire.cancelled_by)
        ),
        _wire_presence=(
            ("wakeup_id", _presence_seed(wire.wakeup_id)),
            ("supplement_capability", _presence_seed(wire.supplement_capability)),
            ("supplement_comment_ids", _presence_seed(wire.supplement_comment_ids)),
            ("can_supplement", _presence_seed(wire.can_supplement)),
            ("issue_title", _presence_seed(wire.issue_title)),
            ("issue_description", _presence_seed(wire.issue_description)),
            ("issue_status", _presence_seed(wire.issue_status)),
            ("issue_assignee_type", _presence_seed(wire.issue_assignee_type)),
            ("issue_assignee_id", _presence_seed(wire.issue_assignee_id)),
            ("issue_changed_fields", _presence_seed(wire.issue_changed_fields)),
            ("issue_state_delta_known", _presence_seed(wire.issue_state_delta_known)),
        ),
    )


class _AgentWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    description: str | None = None
    skills: tuple[AgentSkill, ...] | msgspec.UnsetType = msgspec.UNSET
    archived_at: datetime.datetime | None = None
    conversation_starters: tuple[_AgentConversationStarterWire, ...] | msgspec.UnsetType = (
        msgspec.UNSET
    )
    runtime_availability: str | None | msgspec.UnsetType = msgspec.UNSET
    runtime_id: str | None | msgspec.UnsetType = msgspec.UNSET
    model: str | None | msgspec.UnsetType = msgspec.UNSET
    thinking_level: str | None | msgspec.UnsetType = msgspec.UNSET


def _agent_from_wire(wire: _AgentWire) -> Agent:
    from multica_py.entities.agents import Agent

    starters = () if wire.conversation_starters is msgspec.UNSET else wire.conversation_starters
    return Agent(
        id=wire.id,
        name=wire.name,
        description=wire.description,
        skill_refs=() if wire.skills is msgspec.UNSET else wire.skills,
        archived_at=wire.archived_at,
        conversation_starters=tuple(
            AgentConversationStarter(label=item.label, prompt=item.prompt) for item in starters
        ),
        runtime_availability=(
            None if wire.runtime_availability is msgspec.UNSET else wire.runtime_availability
        ),
        runtime_id=None if wire.runtime_id is msgspec.UNSET else wire.runtime_id,
        model=None if wire.model is msgspec.UNSET else wire.model,
        thinking_level=None if wire.thinking_level is msgspec.UNSET else wire.thinking_level,
        _wire_presence=(
            ("runtime_id", _presence_seed(wire.runtime_id)),
            ("model", _presence_seed(wire.model)),
            ("thinking_level", _presence_seed(wire.thinking_level)),
        ),
    )
