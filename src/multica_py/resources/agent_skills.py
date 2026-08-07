from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py.models.agents import AgentSkill
from multica_py.resources._base import BaseResource


class AgentSkillResource(BaseResource):
    def list_command(self, agent_id: str) -> Command[tuple[AgentSkill, ...]]:
        return self._decoded_list_command(("agent", "skills", "list", agent_id), AgentSkill)

    def list(self, agent_id: str) -> tuple[AgentSkill, ...]:
        return self.list_command(agent_id).run()

    def set_command(self, agent_id: str, skill_ids: tuple[str, ...]) -> Command[None]:
        args = ["agent", "skills", "set", agent_id]
        for sid in skill_ids:
            args.extend(["--skill-id", sid])
        return self._none_command(tuple(args))

    def set(self, agent_id: str, skill_ids: tuple[str, ...]) -> None:
        self.set_command(agent_id, skill_ids).run()
