from __future__ import annotations

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.system import Squad
from multica_py.resources._base import BaseResource
from multica_py.resources.squad_members import SquadMemberResource


class SquadResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.members = SquadMemberResource(transport, config)

    def list(self) -> tuple[Squad, ...]:
        return self._run_json_decode_list(("squad", "list"), Squad)

    def get(self, squad_id: str) -> Squad:
        return self._run_json_decode(("squad", "get", squad_id), Squad)
