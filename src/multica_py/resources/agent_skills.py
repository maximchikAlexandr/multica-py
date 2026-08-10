from __future__ import annotations

from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.models.agents import AgentSkill
from multica_py.models.common import ActionResult, Page
from multica_py.resources._base import BaseResource


class AgentSkillResource(BaseResource):
    def list_command(
        self, agent_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[AgentSkill]]:
        return self._decoded_page_command(
            ("agent", "skills", "list", agent_id), AgentSkill, options=options
        )

    def list(self, agent_id: str, *, options: OperationOptions | None = None) -> Page[AgentSkill]:
        return self.list_command(agent_id, options=options).run()

    def set_command(
        self,
        agent_id: str,
        skill_ids: tuple[str, ...],
        *,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[None]]:
        args = ["agent", "skills", "set", agent_id]
        for sid in skill_ids:
            args.extend(["--skill-id", sid])
        return self._action_command(tuple(args), options=options)

    def set(
        self,
        agent_id: str,
        skill_ids: tuple[str, ...],
        *,
        options: OperationOptions | None = None,
    ) -> ActionResult[None]:
        return self.set_command(agent_id, skill_ids, options=options).run()
