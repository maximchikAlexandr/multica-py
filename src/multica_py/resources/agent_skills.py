from __future__ import annotations

from multica_py.models.skills import Skill
from multica_py.resources._base import BaseResource


class AgentSkillResource(BaseResource):
    def list(self, agent_id: str) -> tuple[Skill, ...]:
        return self._run_json_decode_list(("agent", "skill", "list", agent_id), Skill)

    def set(self, agent_id: str, skill_ids: tuple[str, ...]) -> None:
        args = ["agent", "skill", "set", agent_id]
        for sid in skill_ids:
            args.extend(["--skill-id", sid])
        self._transport.run_text(tuple(args))
