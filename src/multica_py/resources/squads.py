from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import cast

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.entities.issues import Issue
from multica_py.entities.squads import Squad
from multica_py.models.common import ActionResult, Page
from multica_py.models.issues import IssueListFilter
from multica_py.models.relations import (
    OffsetPage,
)
from multica_py.models.system import SquadMember, SquadMemberRemoval
from multica_py.resources._base import BaseResource
from multica_py.resources.squad_members import SquadMemberResource

__all__ = ["Squad", "SquadResource"]


class SquadResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.members = SquadMemberResource(transport, config)

    def _members_relation_command(self, squad_id: str) -> Command[tuple[SquadMember, ...]]:
        validate_nonblank(squad_id)
        return self.members.list_command(squad_id)._map(lambda page: tuple(page.items))

    def _issues_page(self, squad_id: str, limit: int | None, offset: int) -> OffsetPage[Issue]:
        return self._bound_client().issues._offset_page(
            IssueListFilter(assignee_id=squad_id, limit=limit, offset=offset),
        )

    def _issues_page_command(
        self, squad_id: str, limit: int | None, offset: int
    ) -> Command[OffsetPage[Issue]]:
        return self._bound_client().issues._offset_page_command(
            IssueListFilter(assignee_id=squad_id, limit=limit, offset=offset),
        )

    def _add_member_command(
        self,
        squad_id: str,
        *,
        member_id: str,
        member_type: str,
        role: str = "",
        invalidate: Callable[[SquadMember], SquadMember],
        options: OperationOptions | None,
    ) -> Command[SquadMember]:
        return self.members.add_command(
            squad_id,
            member_id=member_id,
            member_type=member_type,
            role=role,
            options=options,
        )._map(invalidate)

    def _remove_member_command(
        self,
        squad_id: str,
        *,
        member_id: str,
        member_type: str,
        invalidate: Callable[[SquadMemberRemoval], SquadMemberRemoval],
        options: OperationOptions | None,
    ) -> Command[SquadMemberRemoval]:
        return self.members.remove_command(
            squad_id, member_id=member_id, member_type=member_type, options=options
        )._map(invalidate)

    def list_command(self, *, options: OperationOptions | None = None) -> Command[Page[Squad]]:
        return self._decoded_list_command(("squad", "list"), Squad, options=options)._map(
            lambda items: Page(
                items=tuple(squad._with_client(self._client) for squad in items),
                total=len(items),
            )
        )

    def list(self, *, options: OperationOptions | None = None) -> Page[Squad]:
        return self.list_command(options=options).run()

    def get_command(
        self, squad_id: str, *, options: OperationOptions | None = None
    ) -> Command[Squad]:
        validate_nonblank(squad_id)
        return self._decoded_command(("squad", "get", squad_id), Squad, options=options)._map(
            lambda squad: squad._with_client(self._client)
        )

    def get(self, squad_id: str, *, options: OperationOptions | None = None) -> Squad:
        return self.get_command(squad_id, options=options).run()

    def create_command(
        self,
        *,
        name: str,
        leader: str,
        description: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Squad]:
        validate_nonblank(name)
        validate_nonblank(leader)
        args = ["squad", "create", "--name", name, "--leader", leader]
        if description is not None:
            args.extend(("--description", description))
        return self._decoded_command(tuple(args), Squad, options=options)._map(
            lambda squad: squad._with_client(self._client)
        )

    def create(
        self,
        *,
        name: str,
        leader: str,
        description: str | None = None,
        options: OperationOptions | None = None,
    ) -> Squad:
        return self.create_command(
            name=name, leader=leader, description=description, options=options
        ).run()

    def update_command(
        self,
        squad_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        leader: str | None = None,
        avatar_url: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Squad]:
        validate_nonblank(squad_id)
        args = ["squad", "update", squad_id]
        for flag, value in (
            ("--name", name),
            ("--description", description),
            ("--instructions", instructions),
            ("--leader", leader),
            ("--avatar-url", avatar_url),
        ):
            if value is not None:
                args.extend((flag, value))
        return self._decoded_command(tuple(args), Squad, options=options)._map(
            lambda squad: squad._with_client(self._client)
        )

    def update(
        self,
        squad_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        instructions: str | None = None,
        leader: str | None = None,
        avatar_url: str | None = None,
        options: OperationOptions | None = None,
    ) -> Squad:
        return self.update_command(
            squad_id,
            name=name,
            description=description,
            instructions=instructions,
            leader=leader,
            avatar_url=avatar_url,
            options=options,
        ).run()

    def delete_command(
        self, squad_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        validate_nonblank(squad_id)

        def decode(stdout: bytes, command: str) -> object:
            return decode_json(stdout, dict[str, object], command=command)

        return self._plan(
            steps=(
                _Step(
                    ("squad", "delete", squad_id, "--output", "json"), "run_bytes", decode=decode
                ),
            ),
            finalize=lambda _results: ActionResult(value=None),
            options=options,
        )

    def delete(
        self, squad_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_command(squad_id, options=options).run()

    def activity_command(
        self,
        issue_id: str,
        outcome: str,
        *,
        reason: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Mapping[str, object]]:
        validate_nonblank(issue_id)
        validate_nonblank(outcome)
        args = ["squad", "activity", issue_id, outcome]
        if reason is not None:
            args.extend(("--reason", reason))

        def decode(stdout: bytes, command: str) -> object:
            return decode_json(stdout, dict[str, object], command=command)

        return self._plan(
            steps=(_Step((*args, "--output", "json"), "run_bytes", decode=decode),),
            finalize=lambda results: cast("Mapping[str, object]", results[0]),
            options=options,
        )

    def activity(
        self,
        issue_id: str,
        outcome: str,
        *,
        reason: str | None = None,
        options: OperationOptions | None = None,
    ) -> Mapping[str, object]:
        return self.activity_command(issue_id, outcome, reason=reason, options=options).run()

    def member_set_role_command(
        self,
        squad_id: str,
        member_id: str,
        *,
        member_type: str = "agent",
        role: str,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[None]]:
        return self.members.set_role_command(
            squad_id,
            member_id,
            member_type=member_type,
            role=role,
            options=options,
        )

    def member_set_role(
        self,
        squad_id: str,
        member_id: str,
        *,
        member_type: str = "agent",
        role: str,
        options: OperationOptions | None = None,
    ) -> ActionResult[None]:
        return self.member_set_role_command(
            squad_id,
            member_id,
            member_type=member_type,
            role=role,
            options=options,
        ).run()
