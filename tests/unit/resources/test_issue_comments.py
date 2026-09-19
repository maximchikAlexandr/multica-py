from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import cast
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py.config import ClientConfig
from multica_py.entities.comments import Comment
from multica_py.exceptions import ConflictError
from multica_py.resources.issue_comments import IssueCommentResource


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
