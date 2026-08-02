from __future__ import annotations

from multica_py._generated.approved_sdk import (
    SQUAD_MEMBERS_ADD_BINDING,
    SQUAD_MEMBERS_LIST_BINDING,
    SQUAD_MEMBERS_REMOVE_BINDING,
    validate_nonblank,
)
from multica_py.models.system import SquadMember
from multica_py.resources._base import BaseResource


class SquadMemberResource(BaseResource):
    def list(self, squad_id: str) -> tuple[SquadMember, ...]:
        _ = SQUAD_MEMBERS_LIST_BINDING
        validate_nonblank(squad_id)
        return self._run_json_decode_list(("squad", "member", "list", squad_id), SquadMember)

    def add(self, squad_id: str, member_id: str) -> None:
        _ = SQUAD_MEMBERS_ADD_BINDING
        validate_nonblank(squad_id)
        validate_nonblank(member_id)
        self._transport.run_text(("squad", "member", "add", squad_id, member_id))

    def remove(self, squad_id: str, member_id: str) -> None:
        _ = SQUAD_MEMBERS_REMOVE_BINDING
        validate_nonblank(squad_id)
        validate_nonblank(member_id)
        self._transport.run_text(("squad", "member", "remove", squad_id, member_id))
