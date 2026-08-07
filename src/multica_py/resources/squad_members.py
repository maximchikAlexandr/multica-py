from __future__ import annotations

from typing import cast

from multica_py._generated.approved_sdk import (
    SQUAD_MEMBERS_ADD_BINDING,
    SQUAD_MEMBERS_LIST_BINDING,
    SQUAD_MEMBERS_REMOVE_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command
from multica_py.models.common import Page
from multica_py.models.system import SquadMember
from multica_py.resources._base import BaseResource


class SquadMemberResource(BaseResource):
    def list_command(self, squad_id: str) -> Command[Page[SquadMember]]:
        _ = cast("object", SQUAD_MEMBERS_LIST_BINDING)
        validate_nonblank(squad_id)
        return self._decoded_page_command(("squad", "member", "list", squad_id), SquadMember)

    def list(self, squad_id: str) -> Page[SquadMember]:
        return self.list_command(squad_id).run()

    def add_command(self, squad_id: str, member_id: str) -> Command[None]:
        _ = cast("object", SQUAD_MEMBERS_ADD_BINDING)
        validate_nonblank(squad_id)
        validate_nonblank(member_id)
        return self._none_command(("squad", "member", "add", squad_id, member_id))

    def add(self, squad_id: str, member_id: str) -> None:
        self.add_command(squad_id, member_id).run()

    def remove_command(self, squad_id: str, member_id: str) -> Command[None]:
        _ = cast("object", SQUAD_MEMBERS_REMOVE_BINDING)
        validate_nonblank(squad_id)
        validate_nonblank(member_id)
        return self._none_command(("squad", "member", "remove", squad_id, member_id))

    def remove(self, squad_id: str, member_id: str) -> None:
        self.remove_command(squad_id, member_id).run()
