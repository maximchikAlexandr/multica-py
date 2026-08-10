from __future__ import annotations

from typing import cast

from multica_py._generated.approved_sdk import (
    SQUAD_MEMBERS_ADD_BINDING,
    SQUAD_MEMBERS_LIST_BINDING,
    SQUAD_MEMBERS_REMOVE_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.models.common import ActionResult, Page
from multica_py.models.system import SquadMember
from multica_py.resources._base import BaseResource


class SquadMemberResource(BaseResource):
    def list_command(
        self, squad_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[SquadMember]]:
        _ = cast("object", SQUAD_MEMBERS_LIST_BINDING)
        validate_nonblank(squad_id)
        return self._decoded_page_command(
            ("squad", "member", "list", squad_id), SquadMember, options=options
        )

    def list(self, squad_id: str, *, options: OperationOptions | None = None) -> Page[SquadMember]:
        return self.list_command(squad_id, options=options).run()

    def add_command(
        self, squad_id: str, member_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        _ = cast("object", SQUAD_MEMBERS_ADD_BINDING)
        validate_nonblank(squad_id)
        validate_nonblank(member_id)
        return self._action_command(
            ("squad", "member", "add", squad_id, member_id), options=options
        )

    def add(
        self, squad_id: str, member_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.add_command(squad_id, member_id, options=options).run()

    def remove_command(
        self, squad_id: str, member_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        _ = cast("object", SQUAD_MEMBERS_REMOVE_BINDING)
        validate_nonblank(squad_id)
        validate_nonblank(member_id)
        return self._action_command(
            ("squad", "member", "remove", squad_id, member_id), options=options
        )

    def remove(
        self, squad_id: str, member_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.remove_command(squad_id, member_id, options=options).run()
