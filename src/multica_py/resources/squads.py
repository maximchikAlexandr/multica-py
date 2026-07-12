from __future__ import annotations

from multica_py.models.system import Squad
from multica_py.resources._base import BaseResource


class SquadResource(BaseResource):
    def list(self) -> tuple[Squad, ...]:
        return self._run_json_decode_list(("squad", "list"), Squad)

    def get(self, squad_id: str) -> Squad:
        return self._run_json_decode(("squad", "get", squad_id), Squad)
