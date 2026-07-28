from __future__ import annotations

from multica_py.models.system import SquadMember
from multica_py.resources._base import BaseResource


class SquadMemberResource(BaseResource):
    def list(self, squad_id: str) -> tuple[SquadMember, ...]:
        return self._run_json_decode_list(("squad", "member", "list", squad_id), SquadMember)
