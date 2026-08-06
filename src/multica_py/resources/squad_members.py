from __future__ import annotations

from typing import cast

from multica_py._generated.approved_sdk import (
    SQUAD_MEMBERS_ADD_BINDING,
    SQUAD_MEMBERS_LIST_BINDING,
    SQUAD_MEMBERS_REMOVE_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command, _Step
from multica_py.models.system import SquadMember
from multica_py.resources._base import BaseResource


class SquadMemberResource(BaseResource):
    def list_command(self, squad_id: str) -> Command[tuple[SquadMember, ...]]:
        _ = cast("object", SQUAD_MEMBERS_LIST_BINDING)
        validate_nonblank(squad_id)
        args, decode = self._plan_decode_list(("squad", "member", "list", squad_id), SquadMember)

        def finalize(results: tuple[object, ...]) -> tuple[SquadMember, ...]:
            return cast("tuple[SquadMember, ...]", results[0])

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def list(self, squad_id: str) -> tuple[SquadMember, ...]:
        return self.list_command(squad_id).run()

    def add_command(self, squad_id: str, member_id: str) -> Command[None]:
        _ = cast("object", SQUAD_MEMBERS_ADD_BINDING)
        validate_nonblank(squad_id)
        validate_nonblank(member_id)
        return self._plan(
            steps=(_Step(("squad", "member", "add", squad_id, member_id), "run_text"),),
            finalize=lambda results: None,
        )

    def add(self, squad_id: str, member_id: str) -> None:
        self.add_command(squad_id, member_id).run()

    def remove_command(self, squad_id: str, member_id: str) -> Command[None]:
        _ = cast("object", SQUAD_MEMBERS_REMOVE_BINDING)
        validate_nonblank(squad_id)
        validate_nonblank(member_id)
        return self._plan(
            steps=(_Step(("squad", "member", "remove", squad_id, member_id), "run_text"),),
            finalize=lambda results: None,
        )

    def remove(self, squad_id: str, member_id: str) -> None:
        self.remove_command(squad_id, member_id).run()
