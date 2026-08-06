from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models._bound import _BoundEntity
from multica_py.models.issues import IssueListFilter, IssueSummary
from multica_py.models.relations import (
    LazyCollection,
    OffsetLazyCollection,
    OffsetPage,
)
from multica_py.models.system import SquadMember
from multica_py.resources._base import BaseResource
from multica_py.resources.issues import _issue_summary_offset_page
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
            self._set_runtime("_members", LazyCollection(lambda: members.list(sid)))
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

            self._set_runtime("_issues", OffsetLazyCollection(page_loader))
        return self._issues  # type: ignore[return-value]

    def _invalidate_members(self) -> None:
        if self._members is not None:
            self._members.invalidate()

    def add_member(self, member_id: str) -> None:
        validate_nonblank(member_id)
        client = self._require_client(
            entity_type="Squad", entity_id=self.id, relation_name="add_member"
        )
        client.squads.members.add(self.id, member_id)
        self._invalidate_members()

    def remove_member(self, member_id: str) -> None:
        validate_nonblank(member_id)
        client = self._require_client(
            entity_type="Squad", entity_id=self.id, relation_name="remove_member"
        )
        client.squads.members.remove(self.id, member_id)
        self._invalidate_members()


class SquadResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.members = SquadMemberResource(transport, config)

    def list(self) -> tuple[Squad, ...]:
        items = self._run_json_decode_list(("squad", "list"), Squad)
        return tuple(s._with_client(self._client) for s in items)

    def get(self, squad_id: str) -> Squad:
        validate_nonblank(squad_id)
        s = self._run_json_decode(("squad", "get", squad_id), Squad)
        return s._with_client(self._client)
