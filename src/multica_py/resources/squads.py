from __future__ import annotations

from collections.abc import Callable

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig, OperationOptions
from multica_py.entities.issues import Issue
from multica_py.entities.squads import Squad
from multica_py.models.common import ActionResult, Page
from multica_py.models.issues import IssueListFilter
from multica_py.models.relations import (
    OffsetPage,
)
from multica_py.models.system import SquadMember
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
        member_id: str,
        *,
        invalidate: Callable[[ActionResult[None]], ActionResult[None]],
        options: OperationOptions | None,
    ) -> Command[ActionResult[None]]:
        return self.members.add_command(squad_id, member_id, options=options)._map(invalidate)

    def _remove_member_command(
        self,
        squad_id: str,
        member_id: str,
        *,
        invalidate: Callable[[ActionResult[None]], ActionResult[None]],
        options: OperationOptions | None,
    ) -> Command[ActionResult[None]]:
        return self.members.remove_command(squad_id, member_id, options=options)._map(invalidate)

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
