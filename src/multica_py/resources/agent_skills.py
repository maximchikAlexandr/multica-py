from __future__ import annotations

from typing import cast

from multica_py._internal.commands import Command, _Step
from multica_py.models.agents import AgentSkill
from multica_py.resources._base import BaseResource


class AgentSkillResource(BaseResource):
    def list_command(self, agent_id: str) -> Command[tuple[AgentSkill, ...]]:
        args, decode = self._plan_decode_list(("agent", "skills", "list", agent_id), AgentSkill)

        def finalize(results: tuple[object, ...]) -> tuple[AgentSkill, ...]:
            return cast("tuple[AgentSkill, ...]", results[0])

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def list(self, agent_id: str) -> tuple[AgentSkill, ...]:
        return self.list_command(agent_id).run()

    def set_command(self, agent_id: str, skill_ids: tuple[str, ...]) -> Command[None]:
        args = ["agent", "skills", "set", agent_id]
        for sid in skill_ids:
            args.extend(["--skill-id", sid])
        return self._plan(
            steps=(_Step(tuple(args), "run_text"),),
            finalize=lambda results: None,
        )

    def set(self, agent_id: str, skill_ids: tuple[str, ...]) -> None:
        self.set_command(agent_id, skill_ids).run()
