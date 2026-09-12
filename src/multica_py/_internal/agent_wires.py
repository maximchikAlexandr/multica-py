from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import msgspec

from multica_py.models.agents import AgentConversationStarter, AgentSkill

if TYPE_CHECKING:
    from multica_py.entities.agents import Agent


class _AgentConversationStarterWire(msgspec.Struct, frozen=True, kw_only=True):
    label: str
    prompt: str


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
