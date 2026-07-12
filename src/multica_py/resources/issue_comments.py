from __future__ import annotations

import datetime
import re

from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.common import Page
from multica_py.models.issue_activity import (
    Comment,
    CommentListFlatRequest,
    CommentListRecentRequest,
    CommentListThreadRequest,
    CommentThread,
)
from multica_py.resources._base import BaseResource

_CURSOR_PATTERN = re.compile(r"(?:next[_ -]?cursor|cursor)[:=]\s*(\S+)", re.IGNORECASE)


def _format_since(value: datetime.datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _extract_cursor(stderr: str) -> str | None:
    match = _CURSOR_PATTERN.search(stderr)
    return match.group(1) if match is not None else None


class IssueCommentResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list(self, issue_id: str) -> tuple[Comment, ...]:
        return self._run_json_decode_list(("issue", "comment", "list", issue_id), Comment)

    def list_flat(self, request: CommentListFlatRequest) -> Page[Comment]:
        args = ["issue", "comment", "list", request.issue_id]
        if request.cursor is not None:
            args.extend(["--cursor", request.cursor])
        if request.limit is not None:
            args.extend(["--limit", str(request.limit)])
        since = _format_since(request.since)
        if since is not None:
            args.extend(["--since", since])
        result = self._transport.run_text((*args, "--output", "json"))
        return Page(
            items=tuple(self._run_decode_comments(result.text)),
            next_cursor=_extract_cursor(result.stderr),
        )

    def list_thread(self, request: CommentListThreadRequest) -> Page[Comment]:
        args = ["issue", "comment", "list", request.issue_id, "--thread-id", request.thread_id]
        if request.cursor is not None:
            args.extend(["--cursor", request.cursor])
        if request.limit is not None:
            args.extend(["--limit", str(request.limit)])
        since = _format_since(request.since)
        if since is not None:
            args.extend(["--since", since])
        result = self._transport.run_text((*args, "--output", "json"))
        return Page(
            items=tuple(self._run_decode_comments(result.text)),
            next_cursor=_extract_cursor(result.stderr),
        )

    def list_recent(self, request: CommentListRecentRequest) -> Page[CommentThread]:
        args = ["issue", "comment", "list", request.issue_id, "--recent"]
        if request.cursor is not None:
            args.extend(["--cursor", request.cursor])
        if request.limit is not None:
            args.extend(["--limit", str(request.limit)])
        since = _format_since(request.since)
        if since is not None:
            args.extend(["--since", since])
        result = self._transport.run_text((*args, "--output", "json"))
        return Page(
            items=tuple(self._run_decode_threads(result.text)),
            next_cursor=_extract_cursor(result.stderr),
        )

    def add(self, issue_id: str, body: str) -> Comment:
        return self._run_json_decode(("issue", "comment", "add", issue_id, "--body", body), Comment)

    def reply(self, issue_id: str, thread_id: str, body: str) -> Comment:
        args = ("issue", "comment", "reply", issue_id, "--thread-id", thread_id, "--body", body)
        return self._run_json_decode((args), Comment)

    def delete(self, issue_id: str, comment_id: str) -> None:
        self._transport.run_text(
            ("issue", "comment", "delete", issue_id, "--comment-id", comment_id)
        )

    def resolve(self, issue_id: str, thread_id: str) -> None:
        self._transport.run_text(
            ("issue", "comment", "resolve", issue_id, "--thread-id", thread_id)
        )

    def unresolve(self, issue_id: str, thread_id: str) -> None:
        self._transport.run_text(
            ("issue", "comment", "unresolve", issue_id, "--thread-id", thread_id)
        )

    def _run_decode_comments(self, payload: str) -> tuple[Comment, ...]:
        return tuple(decode_json(payload.encode("utf-8"), list[Comment]))

    def _run_decode_threads(self, payload: str) -> tuple[CommentThread, ...]:
        return tuple(decode_json(payload.encode("utf-8"), list[CommentThread]))
