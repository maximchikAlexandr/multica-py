from __future__ import annotations

import datetime
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, cast

import msgspec

from multica_py._internal.commands import Command, _replace_plan, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.specs import TextResult
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    _CommentThreadWire,
    _CommentWire,
    comment_from_wire,
    comment_thread_from_wire,
)
from multica_py.config import ClientConfig
from multica_py.exceptions import MissingRelationContextError, OutputShapeError
from multica_py.models._bound import _BoundEntity
from multica_py.models.common import Page
from multica_py.models.issue_activity import (
    CommentCursor,
    CommentListFlatRequest,
    CommentListRecentRequest,
    CommentListThreadRequest,
)
from multica_py.models.relations import CursorLazyCollection, CursorPage
from multica_py.resources._base import BaseResource

if TYPE_CHECKING:
    from multica_py.client import MulticaClient

P = TypeVar("P")

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


class Comment(_BoundEntity):  # type: ignore[misc]
    id: str
    body: str
    thread_id: str | None = None
    author_id: str | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None

    _PUBLIC_FIELDS = ("id", "body", "thread_id", "author_id", "created_at", "updated_at")


class CommentThread(_BoundEntity):  # type: ignore[misc]
    id: str
    resolved: bool = False
    updated_at: datetime.datetime | None = None

    issue_id: str | None = msgspec.field(default=None, name="_issue_id")
    _comments: CursorLazyCollection[Comment] | None = msgspec.field(default=None, name="_comments")

    _RUNTIME_INIT_FIELDS = ("issue_id",)
    _PUBLIC_FIELDS = ("id", "resolved", "updated_at")

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

            def page_command_loader(cursor: CommentCursor | None) -> Command[CursorPage[Comment]]:
                request = CommentListThreadRequest(
                    issue_id=issue_id,
                    thread_id=thread_id,
                    cursor=cursor,
                    limit=50,
                )
                return _adapt_cursor_page_command(
                    client.issues.comments.list_thread_command(request),
                    lambda page: CursorPage(
                        items=tuple(
                            _bind_comment(item, client)
                            for item in cast("tuple[Comment, ...]", getattr(page, "items"))
                        ),
                        next_cursor=cast("CommentCursor | None", getattr(page, "next_cursor")),
                    ),
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


def _adapt_cursor_page_command(
    command: Command[object],
    convert: Callable[[object], CursorPage[P]],
) -> Command[CursorPage[P]]:
    plan = command._plan
    return Command(_replace_plan(plan, finalize=lambda results: convert(plan.finalize(results))))


class IssueCommentResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list_command(self, issue_id: str) -> Command[tuple[Comment, ...]]:
        args, decode = self._plan_decode_list(("issue", "comment", "list", issue_id), _CommentWire)

        def finalize(results: tuple[object, ...]) -> tuple[Comment, ...]:
            items = cast("tuple[_CommentWire, ...]", results[0])
            return tuple(_bind_comment(comment_from_wire(item), self._client) for item in items)

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def list(self, issue_id: str) -> tuple[Comment, ...]:
        return self.list_command(issue_id).run()

    def list_flat_command(self, request: CommentListFlatRequest) -> Command[Page[Comment]]:
        args = ["issue", "comment", "list", request.issue_id]
        since = _format_since(request.since)
        if since is not None:
            args.extend(["--since", since])

        def finalize(results: tuple[object, ...]) -> Page[Comment]:
            result = cast("TextResult", results[0])
            return Page(
                items=tuple(
                    _bind_comment(item, self._client)
                    for item in self._run_decode_comments(result.text)
                ),
                next_cursor=_extract_cursor(result.stderr),
            )

        return self._plan(
            steps=(_Step((*args, "--output", "json"), "run_text"),), finalize=finalize
        )

    def list_flat(self, request: CommentListFlatRequest) -> Page[Comment]:
        return self.list_flat_command(request).run()

    def list_thread_command(self, request: CommentListThreadRequest) -> Command[Page[Comment]]:
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
            args.extend(
                ["--before", request.cursor.before, "--before-id", request.cursor.before_id]
            )
        if request.limit is not None:
            args.extend(["--tail", str(request.limit)])
        since = _format_since(request.since)
        if since is not None:
            args.extend(["--since", since])

        def finalize(results: tuple[object, ...]) -> Page[Comment]:
            result = cast("TextResult", results[0])
            return Page(
                items=tuple(
                    _bind_comment(item, self._client)
                    for item in self._run_decode_comments(result.text)
                ),
                next_cursor=_extract_cursor(result.stderr),
            )

        return self._plan(
            steps=(_Step((*args, "--output", "json"), "run_text"),), finalize=finalize
        )

    def list_thread(self, request: CommentListThreadRequest) -> Page[Comment]:
        return self.list_thread_command(request).run()

    def list_recent_command(
        self, request: CommentListRecentRequest
    ) -> Command[Page[CommentThread]]:
        if request.limit < 1:
            raise ValueError("limit must be positive")
        args = ["issue", "comment", "list", request.issue_id, "--recent", str(request.limit)]
        if request.cursor is not None:
            args.extend(
                ["--before", request.cursor.before, "--before-id", request.cursor.before_id]
            )
        since = _format_since(request.since)
        if since is not None:
            args.extend(["--since", since])

        def finalize(results: tuple[object, ...]) -> Page[CommentThread]:
            result = cast("TextResult", results[0])
            return Page(
                items=tuple(
                    _bind_thread(item, self._client, request.issue_id)
                    for item in self._run_decode_threads(result.text)
                ),
                next_cursor=_extract_cursor(result.stderr),
            )

        return self._plan(
            steps=(_Step((*args, "--output", "json"), "run_text"),), finalize=finalize
        )

    def list_recent(self, request: CommentListRecentRequest) -> Page[CommentThread]:
        return self.list_recent_command(request).run()

    def add_command(self, issue_id: str, body: str) -> Command[Comment]:
        args, decode = self._plan_decode(
            ("issue", "comment", "add", issue_id, "--content", body), _CommentWire
        )

        def finalize(results: tuple[object, ...]) -> Comment:
            return _bind_comment(comment_from_wire(cast("_CommentWire", results[0])), self._client)

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def add(self, issue_id: str, body: str) -> Comment:
        return self.add_command(issue_id, body).run()

    def reply_command(self, issue_id: str, thread_id: str, body: str) -> Command[Comment]:
        args, decode = self._plan_decode(
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
            _CommentWire,
        )

        def finalize(results: tuple[object, ...]) -> Comment:
            return _bind_comment(comment_from_wire(cast("_CommentWire", results[0])), self._client)

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def reply(self, issue_id: str, thread_id: str, body: str) -> Comment:
        return self.reply_command(issue_id, thread_id, body).run()

    def delete_command(self, comment_id: str) -> Command[None]:
        return self._plan(
            steps=(_Step(("issue", "comment", "delete", comment_id), "run_text"),),
            finalize=lambda results: None,
        )

    def delete(self, comment_id: str) -> None:
        self.delete_command(comment_id).run()

    def resolve_command(self, thread_id: str) -> Command[None]:
        return self._plan(
            steps=(_Step(("issue", "comment", "resolve", thread_id), "run_text"),),
            finalize=lambda results: None,
        )

    def resolve(self, thread_id: str) -> None:
        self.resolve_command(thread_id).run()

    def unresolve_command(self, thread_id: str) -> Command[None]:
        return self._plan(
            steps=(_Step(("issue", "comment", "unresolve", thread_id), "run_text"),),
            finalize=lambda results: None,
        )

    def unresolve(self, thread_id: str) -> None:
        self.unresolve_command(thread_id).run()

    def _run_decode_comments(self, payload: str) -> tuple[Comment, ...]:
        return tuple(
            comment_from_wire(item)
            for item in decode_json(payload.encode("utf-8"), list[_CommentWire])
        )

    def _run_decode_threads(self, payload: str) -> tuple[CommentThread, ...]:
        return tuple(
            comment_thread_from_wire(item)
            for item in decode_json(payload.encode("utf-8"), list[_CommentThreadWire])
        )
