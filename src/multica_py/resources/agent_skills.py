from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py.models.agents import AgentSkill
from multica_py.models.common import ActionResult, Page
from multica_py.resources._base import BaseResource


class AgentSkillResource(BaseResource):
    def list_command(self, agent_id: str) -> Command[Page[AgentSkill]]:
        return self._decoded_page_command(("agent", "skills", "list", agent_id), AgentSkill)

    def list(self, agent_id: str) -> Page[AgentSkill]:
        return self.list_command(agent_id).run()

    def set_command(self, agent_id: str, skill_ids: tuple[str, ...]) -> Command[ActionResult[None]]:
        args = ["agent", "skills", "set", agent_id]
        for sid in skill_ids:
            args.extend(["--skill-id", sid])
        return self._action_command(tuple(args))

    def set(self, agent_id: str, skill_ids: tuple[str, ...]) -> ActionResult[None]:
        return self.set_command(agent_id, skill_ids).run()
