from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import msgspec

from multica_py._internal.specs import TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.models.common import Page
from multica_py.models.issue_activity import (
    CommentListFlatRequest,
    CommentListRecentRequest,
    CommentListThreadRequest,
)
from multica_py.resources.issue_comments import IssueCommentResource


def _transport() -> MagicMock:
    return MagicMock(spec=CliTransport)


class TestIssueCommentResource:
    def test_list_flat_includes_before_limit_and_since(self) -> None:
        transport = _transport()
        payload = msgspec.json.encode([{"id": "c1", "content": "hello"}]).decode("utf-8")
        transport.run_text.return_value = TextResult(
            text=payload,
            stderr="next_cursor: cur_2",
            exit_code=0,
        )
        resource = IssueCommentResource(transport, ClientConfig())

        result = resource.list_flat(
            CommentListFlatRequest(
                issue_id="iss_1",
                cursor="cur_1",
                limit=50,
                since=datetime.datetime(2026, 7, 12, 10, 0, tzinfo=datetime.UTC),
            )
        )

        transport.run_text.assert_called_once()
        args = transport.run_text.call_args[0][0]
        assert args == (
            "issue",
            "comment",
            "list",
            "iss_1",
            "--before",
            "cur_1",
            "--limit",
            "50",
            "--since",
            "2026-07-12T10:00:00+00:00",
            "--output",
            "json",
        )
        assert isinstance(result, Page)
        assert result.next_cursor == "cur_2"
        assert result.items[0].id == "c1"
        assert result.items[0].body == "hello"

    def test_list_thread_includes_thread_flag(self) -> None:
        transport = _transport()
        payload = msgspec.json.encode(
            [{"id": "c1", "content": "reply", "parent_id": "th_1"}]
        ).decode("utf-8")
        transport.run_text.return_value = TextResult(text=payload, stderr="", exit_code=0)
        resource = IssueCommentResource(transport, ClientConfig())

        result = resource.list_thread(
            CommentListThreadRequest(issue_id="iss_1", thread_id="th_1", limit=10)
        )

        args = transport.run_text.call_args[0][0]
        assert "--thread" in args
        assert args[args.index("--thread") + 1] == "th_1"
        assert "--tail" in args
        assert args[args.index("--tail") + 1] == "10"
        assert result.items[0].thread_id == "th_1"

    def test_list_recent_returns_thread_page(self) -> None:
        transport = _transport()
        payload = msgspec.json.encode(
            [
                {
                    "id": "th_1",
                    "comments": [{"id": "c1", "content": "root comment"}],
                    "resolved": False,
                }
            ]
        ).decode("utf-8")
        transport.run_text.return_value = TextResult(
            text=payload, stderr="cursor=next_1", exit_code=0
        )
        resource = IssueCommentResource(transport, ClientConfig())

        result = resource.list_recent(CommentListRecentRequest(issue_id="iss_1", limit=5))

        args = transport.run_text.call_args[0][0]
        assert "--recent" in args
        assert args[args.index("--recent") + 1] == "5"
        assert result.next_cursor == "next_1"
        assert result.items[0].id == "th_1"
        assert len(result.items[0].comments) == 1
        assert result.items[0].comments[0].body == "root comment"

    def test_list_recent_uses_default_limit(self) -> None:
        transport = _transport()
        transport.run_text.return_value = TextResult(text="[]", stderr="", exit_code=0)
        resource = IssueCommentResource(transport, ClientConfig())

        resource.list_recent(CommentListRecentRequest(issue_id="iss_1"))

        args = transport.run_text.call_args[0][0]
        assert args[args.index("--recent") + 1] == "10"
