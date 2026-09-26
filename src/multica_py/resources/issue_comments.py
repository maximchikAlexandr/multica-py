from __future__ import annotations

import datetime
import re
from typing import TypeVar, cast

from multica_py._generated.approved_sdk import (
    COMMENT_UPDATE_BINDING,
    validate_nonblank,
    validate_positive_expected_revision,
)
from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.specs import TextResult
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    _CommentThreadWire,
    _CommentWire,
    comment_from_wire,
    comment_thread_from_wire,
)
from multica_py.config import ClientConfig, OperationOptions
from multica_py.entities.comments import Comment, CommentThread, _bind_comment, _bind_thread
from multica_py.exceptions import OutputShapeError
from multica_py.models.common import ActionResult, Page
from multica_py.models.issue_activity import (
    CommentCursor,
)
from multica_py.models.relations import CursorPage
from multica_py.resources._base import BaseResource, _operation_minimum_cli_version

P = TypeVar("P")

__all__ = ["Comment", "CommentThread", "IssueCommentResource"]

_CURSOR_PATTERN = re.compile(
    r"Next (?:thread|reply) cursor:\s+--before\s+(\S+)\s+--before-id\s+(\S+)(?=\s*$)",
    re.IGNORECASE,
)
_CURSOR_MARKER_PATTERN = re.compile(
    r"Next (?:thread|reply) cursor\b|--before(?:-id)?\b", re.IGNORECASE
)


def _format_since(value: datetime.datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _extract_cursor(stderr: str) -> CommentCursor | None:
    match = _CURSOR_PATTERN.search(stderr)
    if match is not None:
        return CommentCursor(before=match.group(1), before_id=match.group(2))
    if _CURSOR_MARKER_PATTERN.search(stderr) is not None:
        raise OutputShapeError("comment pagination response must contain a cursor pair")
    return None


def _comment_list_args(
    args: list[str],
    *,
    roots_only: bool = False,
    summary: bool = False,
    full: bool = False,
    compact: bool = False,
) -> tuple[str, ...]:
    if roots_only:
        args.append("--roots-only")
    if summary:
        args.append("--summary")
    if full:
        args.append("--full")
    if compact:
        args.append("--compact")
    args.extend(("--output", "json"))
    return tuple(args)


class IssueCommentResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def _thread_page_command(
        self,
        *,
        issue_id: str,
        thread_id: str,
        cursor: CommentCursor | None,
        limit: int,
    ) -> Command[CursorPage[Comment]]:
        return self.list_thread_command(
            issue_id=issue_id, thread_id=thread_id, cursor=cursor, limit=limit
        )._map(
            lambda page: CursorPage(
                items=tuple(_bind_comment(item, self._client) for item in page.items),
                next_cursor=cast("CommentCursor | None", page.next_cursor),
            )
        )

    def _recent_threads_page_command(
        self,
        *,
        issue_id: str,
        cursor: CommentCursor | None,
        limit: int,
    ) -> Command[CursorPage[CommentThread]]:
        return self.list_recent_command(issue_id=issue_id, cursor=cursor, limit=limit)._map(
            lambda page: CursorPage(
                items=tuple(_bind_thread(item, self._client, issue_id) for item in page.items),
                next_cursor=cast("CommentCursor | None", page.next_cursor),
            )
        )

    def list_command(
        self,
        issue_id: str,
        *,
        roots_only: bool = False,
        summary: bool = False,
        full: bool = False,
        compact: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[Page[Comment]]:
        args = _comment_list_args(
            ["issue", "comment", "list", issue_id],
            roots_only=roots_only,
            summary=summary,
            full=full,
            compact=compact,
        )
        return self._decoded_page_command(args[:-2], _CommentWire, options=options)._map(
            lambda page: Page(
                items=tuple(
                    _bind_comment(comment_from_wire(item), self._client) for item in page.items
                ),
                limit=page.limit,
                offset=page.offset,
                total=page.total,
                has_more=page.has_more,
                next_cursor=page.next_cursor,
            )
        )

    def list(
        self,
        issue_id: str,
        *,
        roots_only: bool = False,
        summary: bool = False,
        full: bool = False,
        compact: bool = False,
        options: OperationOptions | None = None,
    ) -> Page[Comment]:
        return self.list_command(
            issue_id,
            roots_only=roots_only,
            summary=summary,
            full=full,
            compact=compact,
            options=options,
        ).run()

    def list_flat_command(
        self,
        *,
        issue_id: str,
        since: datetime.datetime | None = None,
        roots_only: bool = False,
        summary: bool = False,
        full: bool = False,
        compact: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[Page[Comment]]:
        args = ["issue", "comment", "list", issue_id]
        since_value = _format_since(since)
        if since_value is not None:
            args.extend(["--since", since_value])

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
            steps=(
                _Step(
                    _comment_list_args(
                        args,
                        roots_only=roots_only,
                        summary=summary,
                        full=full,
                        compact=compact,
                    ),
                    "run_text",
                ),
            ),
            finalize=finalize,
            options=options,
        )

    def list_flat(
        self,
        *,
        issue_id: str,
        since: datetime.datetime | None = None,
        roots_only: bool = False,
        summary: bool = False,
        full: bool = False,
        compact: bool = False,
        options: OperationOptions | None = None,
    ) -> Page[Comment]:
        return self.list_flat_command(
            issue_id=issue_id,
            since=since,
            roots_only=roots_only,
            summary=summary,
            full=full,
            compact=compact,
            options=options,
        ).run()

    def list_thread_command(
        self,
        *,
        issue_id: str,
        thread_id: str,
        cursor: CommentCursor | None = None,
        limit: int | None = None,
        since: datetime.datetime | None = None,
        summary: bool = False,
        full: bool = False,
        compact: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[Page[Comment]]:
        if cursor is not None and limit is None:
            raise ValueError("cursor requires limit")
        if limit is not None and limit < 0:
            raise ValueError("limit must be nonnegative")
        args = [
            "issue",
            "comment",
            "list",
            issue_id,
            "--thread",
            thread_id,
        ]
        if cursor is not None:
            args.extend(["--before", cursor.before, "--before-id", cursor.before_id])
        if limit is not None:
            args.extend(["--tail", str(limit)])
        since_value = _format_since(since)
        if since_value is not None:
            args.extend(["--since", since_value])

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
            steps=(
                _Step(
                    _comment_list_args(
                        args,
                        summary=summary,
                        full=full,
                        compact=compact,
                    ),
                    "run_text",
                ),
            ),
            finalize=finalize,
            options=options,
        )

    def list_thread(
        self,
        *,
        issue_id: str,
        thread_id: str,
        cursor: CommentCursor | None = None,
        limit: int | None = None,
        since: datetime.datetime | None = None,
        summary: bool = False,
        full: bool = False,
        compact: bool = False,
        options: OperationOptions | None = None,
    ) -> Page[Comment]:
        return self.list_thread_command(
            issue_id=issue_id,
            thread_id=thread_id,
            cursor=cursor,
            limit=limit,
            since=since,
            summary=summary,
            full=full,
            compact=compact,
            options=options,
        ).run()

    def list_recent_command(
        self,
        *,
        issue_id: str,
        cursor: CommentCursor | None = None,
        limit: int = 10,
        since: datetime.datetime | None = None,
        summary: bool = False,
        full: bool = False,
        compact: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[Page[CommentThread]]:
        if limit < 1:
            raise ValueError("limit must be positive")
        args = ["issue", "comment", "list", issue_id, "--recent", str(limit)]
        if cursor is not None:
            args.extend(["--before", cursor.before, "--before-id", cursor.before_id])
        since_value = _format_since(since)
        if since_value is not None:
            args.extend(["--since", since_value])

        def finalize(results: tuple[object, ...]) -> Page[CommentThread]:
            result = cast("TextResult", results[0])
            return Page(
                items=tuple(
                    _bind_thread(
                        item,
                        self._client,
                        issue_id,
                        comments=comments if comments else None,
                    )
                    for item, comments in self._run_decode_threads(result.text)
                ),
                next_cursor=_extract_cursor(result.stderr),
            )

        return self._plan(
            steps=(
                _Step(
                    _comment_list_args(
                        args,
                        summary=summary,
                        full=full,
                        compact=compact,
                    ),
                    "run_text",
                ),
            ),
            finalize=finalize,
            options=options,
        )

    def list_recent(
        self,
        *,
        issue_id: str,
        cursor: CommentCursor | None = None,
        limit: int = 10,
        since: datetime.datetime | None = None,
        summary: bool = False,
        full: bool = False,
        compact: bool = False,
        options: OperationOptions | None = None,
    ) -> Page[CommentThread]:
        return self.list_recent_command(
            issue_id=issue_id,
            cursor=cursor,
            limit=limit,
            since=since,
            summary=summary,
            full=full,
            compact=compact,
            options=options,
        ).run()

    def add_command(
        self, issue_id: str, body: str, *, options: OperationOptions | None = None
    ) -> Command[Comment]:
        return self._decoded_command(
            ("issue", "comment", "add", issue_id, "--content", body),
            _CommentWire,
            options=options,
        )._map(lambda wire: _bind_comment(comment_from_wire(wire), self._client))

    def add(self, issue_id: str, body: str, *, options: OperationOptions | None = None) -> Comment:
        return self.add_command(issue_id, body, options=options).run()

    def update_command(
        self,
        comment_id: str,
        body: str,
        *,
        expected_revision: int,
        options: OperationOptions | None = None,
    ) -> Command[Comment]:
        _ = cast("object", COMMENT_UPDATE_BINDING)
        validate_nonblank(comment_id)
        if not isinstance(body, str):
            raise TypeError("body must be a string")
        validate_positive_expected_revision(expected_revision)
        return self._decoded_command(
            (
                "issue",
                "comment",
                "update",
                comment_id,
                "--content",
                body,
                "--expected-revision",
                str(expected_revision),
            ),
            _CommentWire,
            options=options,
            minimum_cli_version=_operation_minimum_cli_version(
                cast("object", COMMENT_UPDATE_BINDING)
            ),
        )._map(lambda wire: _bind_comment(comment_from_wire(wire), self._client))

    def update(
        self,
        comment_id: str,
        body: str,
        *,
        expected_revision: int,
        options: OperationOptions | None = None,
    ) -> Comment:
        return self.update_command(
            comment_id, body, expected_revision=expected_revision, options=options
        ).run()

    def reply_command(
        self,
        issue_id: str,
        thread_id: str,
        body: str,
        *,
        options: OperationOptions | None = None,
    ) -> Command[Comment]:
        return self._decoded_command(
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
            options=options,
        )._map(lambda wire: _bind_comment(comment_from_wire(wire), self._client))

    def reply(
        self, issue_id: str, thread_id: str, body: str, *, options: OperationOptions | None = None
    ) -> Comment:
        return self.reply_command(issue_id, thread_id, body, options=options).run()

    def delete_command(
        self, comment_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("issue", "comment", "delete", comment_id), options=options)

    def delete(
        self, comment_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_command(comment_id, options=options).run()

    def resolve_command(
        self, thread_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("issue", "comment", "resolve", thread_id), options=options)

    def resolve(
        self, thread_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.resolve_command(thread_id, options=options).run()

    def unresolve_command(
        self, thread_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("issue", "comment", "unresolve", thread_id), options=options)

    def unresolve(
        self, thread_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.unresolve_command(thread_id, options=options).run()

    def _run_decode_comments(self, payload: str) -> tuple[Comment, ...]:
        return tuple(
            comment_from_wire(item)
            for item in decode_json(payload.encode("utf-8"), list[_CommentWire])
        )

    def _run_decode_threads(
        self, payload: str
    ) -> tuple[tuple[CommentThread, tuple[Comment, ...]], ...]:
        raw_items = decode_json(payload.encode("utf-8"), list[dict[str, object]])
        if not raw_items:
            return ()
        has_content = ["content" in item for item in raw_items]
        has_comments = ["comments" in item for item in raw_items]
        if all(has_content):
            comments = tuple(
                comment_from_wire(item)
                for item in decode_json(payload.encode("utf-8"), list[_CommentWire])
            )
            return self._group_flat_comments(comments)
        if all(has_comments):
            return tuple(
                (
                    comment_thread_from_wire(item),
                    tuple(comment_from_wire(comment) for comment in item.comments),
                )
                for item in decode_json(payload.encode("utf-8"), list[_CommentThreadWire])
            )
        raise OutputShapeError("recent comment response must contain flat comments or threads")

    @staticmethod
    def _group_flat_comments(
        comments: tuple[Comment, ...],
    ) -> tuple[tuple[CommentThread, tuple[Comment, ...]], ...]:
        by_id: dict[str, Comment] = {}
        for comment in comments:
            if comment.id in by_id:
                raise OutputShapeError(
                    f"recent comment response contains duplicate id {comment.id}"
                )
            by_id[comment.id] = comment

        def root_id(comment: Comment) -> str:
            current = comment
            seen: set[str] = set()
            while current.thread_id is not None:
                if current.id in seen:
                    raise OutputShapeError("recent comment response contains a parent cycle")
                seen.add(current.id)
                parent = by_id.get(current.thread_id)
                if parent is None:
                    raise OutputShapeError(
                        f"recent comment response has unknown parent {current.thread_id}"
                    )
                current = parent
            return current.id

        grouped: dict[str, list[Comment]] = {}
        order: list[str] = []
        for comment in comments:
            thread_id = root_id(comment)
            if thread_id not in grouped:
                grouped[thread_id] = []
                order.append(thread_id)
            grouped[thread_id].append(comment)

        result: list[tuple[CommentThread, tuple[Comment, ...]]] = []
        for thread_id in order:
            items = grouped[thread_id]
            root = by_id[thread_id]
            ordered = (root, *(item for item in items if item.id != thread_id))
            result.append((CommentThread(id=thread_id), ordered))
        return tuple(result)
