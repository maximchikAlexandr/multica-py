from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import cast
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py.config import ClientConfig
from multica_py.entities.comments import Comment
from multica_py.exceptions import ConflictError, OutputShapeError
from multica_py.models.common import CommentCursor
from multica_py.resources.issue_comments import IssueCommentResource, _extract_cursor


def test_update_command_is_lazy_and_decodes_comment(mock_transport: MagicMock) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    mock_transport.run_bytes.return_value = RawCommandResult(
        argv=("multica",),
        exit_code=0,
        stdout=b'{"id":"cmt_1","content":"revised","revision":3}',
        stderr=b"",
        duration=datetime.timedelta(),
    )
    resource = IssueCommentResource(mock_transport, ClientConfig())
    expected = (
        "issue",
        "comment",
        "update",
        "cmt_1",
        "--content",
        "revised",
        "--expected-revision",
        "3",
        "--output",
        "json",
    )

    command = resource.update_command("cmt_1", "revised", expected_revision=3)
    assert command.commands == ("multica " + " ".join(expected),)
    mock_transport.run_bytes.assert_not_called()

    result = command.run()

    assert isinstance(result, Comment)
    assert result.id == "cmt_1"
    assert result.body == "revised"
    assert result.revision == 3
    mock_transport.run_bytes.assert_called_once_with(
        expected, stdin=None, timeout=None, minimum_cli_version="0.5.0"
    )
    mock_transport.run_text.assert_not_called()


@pytest.mark.parametrize("revision", (None, 0, -1, True, 1.5))
def test_update_rejects_invalid_revision_before_transport(
    revision: object, mock_transport: MagicMock
) -> None:
    resource = IssueCommentResource(mock_transport, ClientConfig())

    with pytest.raises((TypeError, ValueError)):
        resource.update_command("cmt_1", "body", expected_revision=cast("int", revision))

    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()


def test_update_rejects_non_text_body_before_transport(mock_transport: MagicMock) -> None:
    resource = IssueCommentResource(mock_transport, ClientConfig())

    with pytest.raises(TypeError, match="body must be a string"):
        resource.update_command("cmt_1", cast("str", 42), expected_revision=1)

    mock_transport.run_bytes.assert_not_called()


@pytest.mark.parametrize("comment_id", ("", " ", "\t"))
def test_update_rejects_blank_comment_id_before_transport(
    comment_id: str, mock_transport: MagicMock
) -> None:
    resource = IssueCommentResource(mock_transport, ClientConfig())

    with pytest.raises(ValueError, match="must be nonblank"):
        resource.update(comment_id, "body", expected_revision=1)

    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()


def test_update_preserves_content_and_classifies_stale_revision_once(
    raw_result: Callable[..., RawCommandResult],
) -> None:
    from multica_py._internal.transport import CliTransport

    transport = CliTransport(ClientConfig())
    calls: list[tuple[str, ...]] = []

    def execute(command_args: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
        calls.append(command_args)
        return raw_result(
            ("multica", *command_args),
            exit_code=1,
            stderr=b"Error: PATCH /api/comments/cmt_1 returned 409: stale revision",
        )

    transport._execute = execute  # type: ignore[method-assign]
    resource = IssueCommentResource(transport, ClientConfig())
    expected = (
        "issue",
        "comment",
        "update",
        "cmt_1",
        "--content",
        "mention [@agent]",
        "--expected-revision",
        "7",
        "--output",
        "json",
    )

    with pytest.raises(ConflictError, match="stale revision"):
        resource.update("cmt_1", "mention [@agent]", expected_revision=7)

    assert calls == [expected]


def test_recent_decodes_native_flat_root_and_reply_records(mock_transport: MagicMock) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    mock_transport.run_text.return_value = TextResult(
        '[{"id":"root","content":"root body"},'
        '{"id":"reply","content":"reply body","parent_id":"root"}]',
        "",
        0,
    )
    resource = IssueCommentResource(mock_transport, ClientConfig())

    page = resource.list_recent(issue_id="issue-1", limit=5)

    assert [thread.id for thread in page.items] == ["root"]
    assert [
        (comment.id, comment.body, comment.thread_id) for comment in page.items[0].comments.all()
    ] == [
        ("root", "root body", None),
        ("reply", "reply body", "root"),
    ]
    mock_transport.run_text.assert_called_once_with(
        ("issue", "comment", "list", "issue-1", "--recent", "5", "--output", "json")
    )


def test_recent_rejects_flat_reply_with_missing_parent(mock_transport: MagicMock) -> None:
    mock_transport.run_text.return_value = TextResult(
        '[{"id":"reply","content":"reply body","parent_id":"missing"}]', "", 0
    )
    resource = IssueCommentResource(mock_transport, ClientConfig())

    with pytest.raises(OutputShapeError, match="unknown parent"):
        resource.list_recent(issue_id="issue-1")


@pytest.mark.parametrize(
    ("stderr", "expected"),
    (
        (
            "Next thread cursor: --before 2026-09-26T19:00:00.123456Z --before-id root",
            CommentCursor(before="2026-09-26T19:00:00.123456Z", before_id="root"),
        ),
        (
            "Next reply cursor: --before 2026-09-26T19:00:00.123456Z --before-id reply",
            CommentCursor(before="2026-09-26T19:00:00.123456Z", before_id="reply"),
        ),
        ("no pagination", None),
    ),
)
def test_extract_cursor_accepts_native_thread_and_reply_forms(
    stderr: str, expected: CommentCursor | None
) -> None:
    assert _extract_cursor(stderr) == expected


@pytest.mark.parametrize(
    "stderr",
    (
        "Next thread cursor: --before 2026-09-26T19:00:00Z",
        "Next reply cursor: --before-id reply",
        "Next thread cursor: before: old before-id: root",
    ),
)
def test_extract_cursor_rejects_malformed_native_forms(stderr: str) -> None:
    with pytest.raises(OutputShapeError, match="cursor pair"):
        _extract_cursor(stderr)


def test_recent_preserves_summary_full_and_compact_controls(mock_transport: MagicMock) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    mock_transport.run_text.return_value = TextResult("[]", "", 0)
    resource = IssueCommentResource(mock_transport, ClientConfig())

    resource.list_recent(issue_id="issue-1", summary=True, full=True, compact=True, limit=5)

    mock_transport.run_text.assert_called_once_with(
        (
            "issue",
            "comment",
            "list",
            "issue-1",
            "--recent",
            "5",
            "--summary",
            "--full",
            "--compact",
            "--output",
            "json",
        )
    )
