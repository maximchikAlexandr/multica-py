from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import msgspec

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
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    cancelled_by: _TaskCancellationActorWire | msgspec.UnsetType = msgspec.UNSET


def _agent_task_from_wire(wire: _AgentTaskWire) -> AgentTask:
    return AgentTask(
        id=wire.id,
        status=wire.status,
        issue_id=wire.issue_id,
        started_at=wire.started_at,
        completed_at=wire.completed_at,
        cancelled_by=(
            None
            if wire.cancelled_by is msgspec.UNSET
            else _task_cancellation_actor_from_wire(wire.cancelled_by)
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
    )
