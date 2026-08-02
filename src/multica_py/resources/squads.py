from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models import ResourceEntity
from multica_py.models.issues import IssueListFilter, IssueSummary
from multica_py.models.relations import (
    LazyCollection,
    OffsetLazyCollection,
    OffsetPage,
)
from multica_py.models.system import Squad, SquadData, SquadMember
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


class SquadEntity(ResourceEntity[SquadData]):
    def __init__(self, data: SquadData, client: MulticaClient | None = None) -> None:
        super().__init__(data, client=client)
        self._members: LazyCollection[SquadMember] | None = None
        self._issues: OffsetLazyCollection[IssueSummary] | None = None

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def name(self) -> str:
        return self._data.name

    @property
    def member_count(self) -> int:
        return self._data.member_count

    @property
    def leader_id(self) -> str | None:
        return self._data.leader_id

    @property
    def archived_at(self) -> datetime.datetime | None:
        return self._data.archived_at

    def _check_client(self, relation_name: str) -> MulticaClient:
        return self._require_client(
            entity_type="SquadEntity", entity_id=self._data.id, relation_name=relation_name
        )

    @property
    def members(self) -> LazyCollection[SquadMember]:
        if self._members is None:
            client = self._check_client("members")
            sid = self._data.id

            members = client.squads.members
            self._members = LazyCollection(lambda: members.list(sid))
        return self._members

    @property
    def issues(self) -> OffsetLazyCollection[IssueSummary]:
        if self._issues is None:
            client = self._check_client("issues")
            sid = self._data.id

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[IssueSummary]:
                return _page_squad_issues(client, sid, limit, offset)

            self._issues = OffsetLazyCollection(page_loader)
        return self._issues

    def _invalidate_members(self) -> None:
        if self._members is not None:
            self._members.invalidate()

    def add_member(self, member_id: str) -> None:
        validate_nonblank(member_id)
        client = self._check_client("add_member")
        client.squads.members.add(self.id, member_id)
        self._invalidate_members()

    def remove_member(self, member_id: str) -> None:
        validate_nonblank(member_id)
        client = self._check_client("remove_member")
        client.squads.members.remove(self.id, member_id)
        self._invalidate_members()


class SquadResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.members = SquadMemberResource(transport, config)

    def list(self) -> tuple[SquadEntity, ...]:
        items = self._run_json_decode_list(("squad", "list"), Squad)
        return tuple(self._bind_squad(s) for s in items)

    def get(self, squad_id: str) -> SquadEntity:
        validate_nonblank(squad_id)
        s = self._run_json_decode(("squad", "get", squad_id), Squad)
        return self._bind_squad(s)

    def _bind_squad(self, s: Squad) -> SquadEntity:
        data = SquadData(
            id=s.id,
            name=s.name,
            member_count=s.member_count,
            leader_id=s.leader_id,
            archived_at=s.archived_at,
        )
        return SquadEntity(data, client=self._client)
