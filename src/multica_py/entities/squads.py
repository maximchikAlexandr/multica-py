from __future__ import annotations

import datetime

import msgspec

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command
from multica_py.config import OperationOptions
from multica_py.entities._base import _BoundEntity
from multica_py.entities.issues import Issue
from multica_py.models.common import ActionResult
from multica_py.models.relations import LazyCollection, OffsetLazyCollection, OffsetPage
from multica_py.models.system import SquadMember


class Squad(_BoundEntity):  # type: ignore[misc]
    id: str
    name: str
    member_count: int = 0
    leader_id: str | None = None
    archived_at: datetime.datetime | None = None

    _members: LazyCollection[SquadMember] | None = msgspec.field(default=None, name="_members")
    _issues: OffsetLazyCollection[Issue] | None = msgspec.field(default=None, name="_issues")

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
                    lambda: members.list(sid).items,
                    command_loader=lambda: client.squads._members_relation_command(sid),
                ),
            )
        return self._members  # type: ignore[return-value]

    @property
    def issues(self) -> OffsetLazyCollection[Issue]:
        if self._issues is None:
            client = self._require_client(
                entity_type="Squad", entity_id=self.id, relation_name="issues"
            )
            sid = self.id

            def page_loader(*, limit: int | None, offset: int) -> OffsetPage[Issue]:
                return client.squads._issues_page(sid, limit, offset)

            def page_command_loader(limit: int | None, offset: int) -> Command[OffsetPage[Issue]]:
                return client.squads._issues_page_command(sid, limit, offset)

            self._set_runtime(
                "_issues",
                OffsetLazyCollection(
                    page_loader,
                    default_limit=50,
                    page_command_loader=page_command_loader,
                ),
            )
        return self._issues  # type: ignore[return-value]

    def _invalidate_members(self) -> None:
        if self._members is not None:
            self._members.invalidate()

    def add_member(
        self, member_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.add_member_command(member_id, options=options).run()

    def add_member_command(
        self, member_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        validate_nonblank(member_id)
        client = self._require_client(
            entity_type="Squad", entity_id=self.id, relation_name="add_member"
        )

        def invalidate(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                self._invalidate_members()
            return result

        return client.squads._add_member_command(
            self.id, member_id, invalidate=invalidate, options=options
        )

    def remove_member(
        self, member_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.remove_member_command(member_id, options=options).run()

    def remove_member_command(
        self, member_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        validate_nonblank(member_id)
        client = self._require_client(
            entity_type="Squad", entity_id=self.id, relation_name="remove_member"
        )

        def invalidate(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                self._invalidate_members()
            return result

        return client.squads._remove_member_command(
            self.id, member_id, invalidate=invalidate, options=options
        )
