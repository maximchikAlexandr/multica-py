from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, cast

import msgspec

from multica_py.entities._base import _BoundEntity
from multica_py.exceptions import MissingRelationContextError
from multica_py.models.common import CommentCursor
from multica_py.models.relations import CursorLazyCollection, CursorPage

if TYPE_CHECKING:
    from multica_py._internal.commands import Command
    from multica_py.client import MulticaClient


class Comment(_BoundEntity):  # type: ignore[misc]
    id: str
    body: str
    thread_id: str | None = None
    author_id: str | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


class CommentThread(_BoundEntity):  # type: ignore[misc]
    id: str
    resolved: bool = False
    updated_at: datetime.datetime | None = None

    issue_id: str | None = msgspec.field(default=None, name="_issue_id")
    _comments: CursorLazyCollection[Comment] | None = msgspec.field(default=None, name="_comments")

    @property
    def comments(self) -> CursorLazyCollection[Comment]:
        if self._comments is None:
            client = self._require_client(
                entity_type="CommentThread", entity_id=self.id, relation_name="comments"
            )
            if self.issue_id is None:
                raise MissingRelationContextError("CommentThread", self.id, "comments", "issue_id")
            issue_id = self.issue_id
            thread_id = self.id

            def page_loader(cursor: CommentCursor | None = None) -> CursorPage[Comment]:
                page = client.issues.comments.list_thread(
                    issue_id=issue_id, thread_id=thread_id, cursor=cursor, limit=50
                )
                return CursorPage(
                    items=tuple(_bind_comment(item, client) for item in page.items),
                    next_cursor=cast("CommentCursor | None", page.next_cursor),
                )

            def page_command_loader(
                cursor: CommentCursor | None,
            ) -> Command[CursorPage[Comment]]:
                return client.issues.comments._thread_page_command(
                    issue_id=issue_id, thread_id=thread_id, cursor=cursor, limit=50
                )

            _comments: CursorLazyCollection[Comment] = CursorLazyCollection(
                page_loader, page_command_loader=page_command_loader
            )
            self._set_runtime("_comments", _comments)
        return self._comments  # type: ignore[return-value]


def _bind_comment(comment: Comment, client: MulticaClient | None) -> Comment:
    return comment._with_client(client)


def _bind_thread(
    thread: CommentThread,
    client: MulticaClient | None,
    issue_id: str,
) -> CommentThread:
    result = thread
    result = result._with_client(client)
    if result.issue_id is None:
        result = msgspec.structs.replace(result, issue_id=issue_id)
    return result
