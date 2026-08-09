from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models._bound import _BoundEntity
from multica_py.models.common import ActionResult, Page
from multica_py.models.issues import IssueListFilter, IssueSummary
from multica_py.models.relations import (
    LazyCollection,
    OffsetLazyCollection,
    OffsetPage,
)
from multica_py.models.system import SquadMember
from multica_py.resources._base import BaseResource, _page_items
from multica_py.resources.issues import (
    _issue_summary_offset_page,
    _issue_summary_offset_page_command,
)
from multica_py.resources.squad_members import SquadMemberResource

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


def _page_squad_issues(
    client: MulticaClient, squad_id: str, limit: int | None, offset: int
) -> OffsetPage[IssueSummary]:

    flt = IssueListFilter(
        assignee_id=squad_id,
        limit=limit,
        offset=offset,
    )
    return _issue_summary_offset_page(client.issues, flt)


def _squad_members_command(
    client: MulticaClient, squad_id: str
) -> Command[tuple[SquadMember, ...]]:
    validate_nonblank(squad_id)
    return client.squads.members.list_command(squad_id)._map(_page_items)


def _squad_issues_page_command(
    client: MulticaClient, squad_id: str, limit: int | None, offset: int
) -> Command[OffsetPage[IssueSummary]]:
    return _issue_summary_offset_page_command(
        client.issues,
        IssueListFilter(assignee_id=squad_id, limit=limit, offset=offset),
    )


class Squad(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    member_count: int = 0
    leader_id: str | None = None
    archived_at: datetime.datetime | None = None

    _members: LazyCollection[SquadMember] | None = msgspec.field(default=None, name="_members")
    _issues: OffsetLazyCollection[IssueSummary] | None = msgspec.field(default=None, name="_issues")

    _PUBLIC_FIELDS = ("id", "name", "member_count", "leader_id", "archived_at")

    @property
    def members(self) -> LazyCollection[SquadMember]:
        if self._members is None:
            client = self._require_client(
                entity_type="Squad", entity_id=self.id, relation_name="members"
            )
            sid = self.id
            members = client.squads.members
            self._set_runtime(
                "_members",
                LazyCollection(
                    lambda: _page_items(members.list(sid)),
                    command_loader=lambda: _squad_members_command(client, sid),
                ),
            )
        return self._members  # type: ignore[return-value]

    @property
    def issues(self) -> OffsetLazyCollection[IssueSummary]:
        if self._issues is None:
            client = self._require_client(
                entity_type="Squad", entity_id=self.id, relation_name="issues"
            )
            sid = self.id

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[IssueSummary]:
                return _page_squad_issues(client, sid, limit, offset)

            self._set_runtime(
                "_issues",
                OffsetLazyCollection(
                    page_loader,
                    default_limit=50,
                    page_command_loader=lambda limit, offset: _squad_issues_page_command(
                        client, sid, limit, offset
                    ),
                ),
            )
        return self._issues  # type: ignore[return-value]

    def _invalidate_members(self) -> None:
        if self._members is not None:
            self._members.invalidate()

    def add_member(self, member_id: str) -> ActionResult[None]:
        return self.add_member_command(member_id).run()

    def add_member_command(self, member_id: str) -> Command[ActionResult[None]]:
        validate_nonblank(member_id)
        client = self._require_client(
            entity_type="Squad", entity_id=self.id, relation_name="add_member"
        )

        def invalidate(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                self._invalidate_members()
            return result

        return client.squads.members.add_command(self.id, member_id)._map(invalidate)

    def remove_member(self, member_id: str) -> ActionResult[None]:
        return self.remove_member_command(member_id).run()

    def remove_member_command(self, member_id: str) -> Command[ActionResult[None]]:
        validate_nonblank(member_id)
        client = self._require_client(
            entity_type="Squad", entity_id=self.id, relation_name="remove_member"
        )

        def invalidate(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                self._invalidate_members()
            return result

        return client.squads.members.remove_command(self.id, member_id)._map(invalidate)


class SquadResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.members = SquadMemberResource(transport, config)

    def list_command(self) -> Command[Page[Squad]]:
        return self._decoded_list_command(("squad", "list"), Squad)._map(
            lambda items: Page(
                items=tuple(squad._with_client(self._client) for squad in items),
                total=len(items),
            )
        )

    def list(self) -> Page[Squad]:
        return self.list_command().run()

    def get_command(self, squad_id: str) -> Command[Squad]:
        validate_nonblank(squad_id)
        return self._decoded_command(("squad", "get", squad_id), Squad)._map(
            lambda squad: squad._with_client(self._client)
        )

    def get(self, squad_id: str) -> Squad:
        return self.get_command(squad_id).run()
