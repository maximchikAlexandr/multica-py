from __future__ import annotations

from multica_py.models.agents import AgentSkill
from multica_py.resources._base import BaseResource


class AgentSkillResource(BaseResource):
    def list(self, agent_id: str) -> tuple[AgentSkill, ...]:
        return self._run_json_decode_list(("agent", "skills", "list", agent_id), AgentSkill)

    def set(self, agent_id: str, skill_ids: tuple[str, ...]) -> None:
        args = ["agent", "skills", "set", agent_id]
        for sid in skill_ids:
            args.extend(["--skill-id", sid])
        self._transport.run_text(tuple(args))
