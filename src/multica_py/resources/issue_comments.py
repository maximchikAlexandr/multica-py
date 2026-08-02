from __future__ import annotations

import datetime
import re
from typing import TYPE_CHECKING, cast

from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    CommentThreadWire,
    CommentWire,
    comment_from_wire,
    comment_thread_from_wire,
)
from multica_py.config import ClientConfig
from multica_py.exceptions import MissingRelationContextError, OutputShapeError
from multica_py.models import ResourceEntity
from multica_py.models.common import Page
from multica_py.models.issue_activity import (
    Comment as CommentRecord,
)
from multica_py.models.issue_activity import (
    CommentCursor,
    CommentData,
    CommentListFlatRequest,
    CommentListRecentRequest,
    CommentListThreadRequest,
    CommentThreadData,
)
from multica_py.models.issue_activity import (
    CommentThread as CommentThreadRecord,
)
from multica_py.models.relations import CursorLazyCollection, CursorPage
from multica_py.resources._base import BaseResource

if TYPE_CHECKING:
    from multica_py.client import MulticaClient

_CURSOR_PATTERN = re.compile(r"(?:next[_ -]?cursor|cursor)[:=]\s*(\S+)", re.IGNORECASE)
_BEFORE_PATTERN = re.compile(r"(?:before|next[_ -]?before)[:=]\s*(\S+)", re.IGNORECASE)
_BEFORE_ID_PATTERN = re.compile(
    r"(?:before[_ -]?id|next[_ -]?before[_ -]?id)[:=]\s*(\S+)", re.IGNORECASE
)


def _format_since(value: datetime.datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _extract_cursor(stderr: str) -> CommentCursor | None:
    before = _BEFORE_PATTERN.search(stderr)
    before_id = _BEFORE_ID_PATTERN.search(stderr)
    if before is not None or before_id is not None:
        if before is None or before_id is None:
            raise OutputShapeError("comment pagination response must contain a cursor pair")
        return CommentCursor(before=before.group(1), before_id=before_id.group(1))
    match = _CURSOR_PATTERN.search(stderr)
    if match is not None:
        raise OutputShapeError("comment pagination response must contain a cursor pair")
    return None


class Comment(ResourceEntity[CommentData]):
    def __init__(self, data: CommentData, client: MulticaClient | None = None) -> None:
        super().__init__(data, client=client)

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def body(self) -> str:
        return self._data.body

    @property
    def thread_id(self) -> str | None:
        return self._data.thread_id

    @property
    def author_id(self) -> str | None:
        return self._data.author_id

    @property
    def created_at(self) -> datetime.datetime | None:
        return self._data.created_at

    @property
    def updated_at(self) -> datetime.datetime | None:
        return self._data.updated_at


class CommentThread(ResourceEntity[CommentThreadData]):
    def __init__(
        self,
        data: CommentThreadData,
        client: MulticaClient | None = None,
        *,
        issue_id: str | None = None,
    ) -> None:
        super().__init__(data, client=client)
        self._issue_id = issue_id
        self._comments: CursorLazyCollection[Comment] | None = None

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def resolved(self) -> bool:
        return self._data.resolved

    @property
    def updated_at(self) -> datetime.datetime | None:
        return self._data.updated_at

    @property
    def comments(self) -> CursorLazyCollection[Comment]:
        if self._comments is None:
            client = self._require_client(
                entity_type="CommentThread", entity_id=self._data.id, relation_name="comments"
            )
            if self._issue_id is None:
                raise MissingRelationContextError(
                    "CommentThread", self._data.id, "comments", "issue_id"
                )
            issue_id = self._issue_id
            thread_id = self._data.id

            def page_loader(cursor: CommentCursor | None = None) -> CursorPage[Comment]:
                request = CommentListThreadRequest(
                    issue_id=issue_id,
                    thread_id=thread_id,
                    cursor=cursor,
                    limit=50,
                )
                page = client.issues.comments.list_thread(request)
                return CursorPage(
                    items=tuple(_bind_comment(item, client) for item in page.items),
                    next_cursor=cast("CommentCursor | None", page.next_cursor),
                )

            self._comments = CursorLazyCollection(page_loader)
        return self._comments


def _comment_data(comment: CommentRecord | Comment) -> CommentData:
    if isinstance(comment, Comment):
        return comment.to_data()
    return CommentData(
        id=comment.id,
        body=comment.body,
        thread_id=comment.thread_id,
        author_id=comment.author_id,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


def _bind_comment(comment: CommentRecord | Comment, client: MulticaClient | None) -> Comment:
    return Comment(_comment_data(comment), client=client)


def _thread_data(thread: CommentThreadRecord | CommentThread) -> CommentThreadData:
    if isinstance(thread, CommentThread):
        return thread.to_data()
    return CommentThreadData(
        id=thread.id,
        comments=tuple(
            CommentData(
                id=comment.id,
                body=comment.body,
                thread_id=comment.thread_id,
                author_id=comment.author_id,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
            )
            for comment in thread.comments
        ),
        resolved=thread.resolved,
        updated_at=thread.updated_at,
    )


def _bind_thread(
    thread: CommentThreadRecord | CommentThread,
    client: MulticaClient | None,
    issue_id: str,
) -> CommentThread:
    return CommentThread(_thread_data(thread), client=client, issue_id=issue_id)


class IssueCommentResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list(self, issue_id: str) -> tuple[Comment, ...]:
        return tuple(
            _bind_comment(comment_from_wire(item), self._client)
            for item in self._run_json_decode_list(
                ("issue", "comment", "list", issue_id), CommentWire
            )
        )

    def list_flat(self, request: CommentListFlatRequest) -> Page[Comment]:
        args = ["issue", "comment", "list", request.issue_id]
        since = _format_since(request.since)
        if since is not None:
            args.extend(["--since", since])
        result = self._transport.run_text((*args, "--output", "json"))
        return Page(
            items=tuple(
                _bind_comment(item, self._client) for item in self._run_decode_comments(result.text)
            ),
            next_cursor=_extract_cursor(result.stderr),
        )

    def list_thread(self, request: CommentListThreadRequest) -> Page[Comment]:
        if request.cursor is not None and request.limit is None:
            raise ValueError("cursor requires limit")
        if request.limit is not None and request.limit < 0:
            raise ValueError("limit must be nonnegative")
        args = [
            "issue",
            "comment",
            "list",
            request.issue_id,
            "--thread",
            request.thread_id,
        ]
        if request.cursor is not None:
            args.extend(["--before", request.cursor.before])
            args.extend(["--before-id", request.cursor.before_id])
        if request.limit is not None:
            args.extend(["--tail", str(request.limit)])
        since = _format_since(request.since)
        if since is not None:
            args.extend(["--since", since])
        result = self._transport.run_text((*args, "--output", "json"))
        return Page(
            items=tuple(
                _bind_comment(item, self._client) for item in self._run_decode_comments(result.text)
            ),
            next_cursor=_extract_cursor(result.stderr),
        )

    def list_recent(self, request: CommentListRecentRequest) -> Page[CommentThread]:
        if request.limit < 1:
            raise ValueError("limit must be positive")
        args = ["issue", "comment", "list", request.issue_id, "--recent", str(request.limit)]
        if request.cursor is not None:
            args.extend(["--before", request.cursor.before])
            args.extend(["--before-id", request.cursor.before_id])
        since = _format_since(request.since)
        if since is not None:
            args.extend(["--since", since])
        result = self._transport.run_text((*args, "--output", "json"))
        return Page(
            items=tuple(
                _bind_thread(item, self._client, request.issue_id)
                for item in self._run_decode_threads(result.text)
            ),
            next_cursor=_extract_cursor(result.stderr),
        )

    def add(self, issue_id: str, body: str) -> Comment:
        return _bind_comment(
            comment_from_wire(
                self._run_json_decode(
                    ("issue", "comment", "add", issue_id, "--content", body), CommentWire
                )
            ),
            self._client,
        )

    def reply(self, issue_id: str, thread_id: str, body: str) -> Comment:
        return _bind_comment(
            comment_from_wire(
                self._run_json_decode(
                    (
                        "issue",
                        "comment",
                        "add",
                        issue_id,
                        "--content",
                        body,
                        "--parent",
                        thread_id,
                    ),
                    CommentWire,
                )
            ),
            self._client,
        )

    def delete(self, comment_id: str) -> None:
        self._transport.run_text(("issue", "comment", "delete", comment_id))

    def resolve(self, thread_id: str) -> None:
        self._transport.run_text(("issue", "comment", "resolve", thread_id))

    def unresolve(self, thread_id: str) -> None:
        self._transport.run_text(("issue", "comment", "unresolve", thread_id))

    def _run_decode_comments(self, payload: str) -> tuple[CommentRecord, ...]:
        return tuple(
            comment_from_wire(item)
            for item in decode_json(payload.encode("utf-8"), list[CommentWire])
        )

    def _run_decode_threads(self, payload: str) -> tuple[CommentThreadRecord, ...]:
        return tuple(
            comment_thread_from_wire(item)
            for item in decode_json(payload.encode("utf-8"), list[CommentThreadWire])
        )
