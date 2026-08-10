from __future__ import annotations

import datetime
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py.config import ClientConfig
from multica_py.exceptions import JsonOutputError, OutputShapeError
from multica_py.models.common import Page
from multica_py.resources.issues import Issue, IssueResource


@dataclass(frozen=True)
class SearchCase:
    id: str
    query: str
    payload: bytes
    expected: tuple[tuple[str, str | None], ...]


@dataclass(frozen=True)
class SearchValidationCase:
    id: str
    query: str
    expected_exception: type[Exception]


_SEARCH_CASES: tuple[SearchCase, ...] = (
    SearchCase(
        id="envelope-sources",
        query="needle",
        payload=b'{"issues":['
        b'{"id":"i1","title":"Title","status":"todo","match_source":"title"},'
        b'{"id":"i2","title":"Description","status":"todo",'
        b'"match_source":"description"},'
        b'{"id":"i3","title":"Comment","status":"todo",'
        b'"match_source":"comment"}],"total":3}',
        expected=(("i1", "title"), ("i2", "description"), ("i3", "comment")),
    ),
    SearchCase(
        id="number-only-comment-fallback",
        query="412",
        payload=b'{"issues":[{"id":"i4","title":"Issue 412","status":"todo",'
        b'"match_source":"comment"}],"total":1}',
        expected=(("i4", "comment"),),
    ),
    SearchCase(
        id="legacy-array",
        query="legacy",
        payload=b'[{"id":"i1","title":"Legacy","status":"todo","match_source":"comment"}]',
        expected=(("i1", "comment"),),
    ),
    SearchCase(
        id="empty-envelope",
        query="empty",
        payload=b'{"issues":[],"total":0}',
        expected=(),
    ),
    SearchCase(
        id="missing-source",
        query="missing-source",
        payload=b'{"issues":[{"id":"i1","title":"No source","status":"todo"}]}',
        expected=(("i1", None),),
    ),
    SearchCase(
        id="unknown-source",
        query="future",
        payload=b'{"issues":[{"id":"i1","title":"Future","status":"todo","match_source":"future-index"}]}',
        expected=(("i1", "future-index"),),
    ),
)

_SEARCH_VALIDATION_CASES: tuple[SearchValidationCase, ...] = (
    SearchValidationCase("blank-query", "", ValueError),
)


@dataclass(frozen=True)
class MalformedSearchCase:
    id: str
    payload: bytes


_MALFORMED_SEARCH_CASES: tuple[MalformedSearchCase, ...] = (
    MalformedSearchCase("missing-issues", b'{"total":1}'),
    MalformedSearchCase("null", b"null"),
    MalformedSearchCase("string", b'"not-an-envelope"'),
    MalformedSearchCase("number", b"42"),
)


@pytest.mark.parametrize(
    "case",
    _SEARCH_CASES,
    ids=lambda case: case.id,
)
def test_issue_search_accepts_envelope_and_legacy_shapes(
    case: SearchCase,
    mock_transport: MagicMock,
) -> None:
    mock_transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    mock_transport.run_bytes.return_value = RawCommandResult(
        argv=("issue", "search", case.query, "--output", "json"),
        exit_code=0,
        stdout=case.payload,
        stderr=b"",
        duration=datetime.timedelta(),
    )
    client = MagicMock()
    resource = IssueResource(mock_transport, ClientConfig())
    resource._set_client(client)

    command = resource.search_command(case.query)
    assert command.commands == (f"multica issue search {case.query} --output json",)
    mock_transport.run_bytes.assert_not_called()
    client.issues.get.assert_not_called()

    result = command.run()
    assert type(result) is Page
    assert tuple((item.id, item.match_source) for item in result.items) == case.expected
    assert all(isinstance(item, Issue) and item._client is client for item in result.items)
    assert all(item.description is None for item in result.items)
    assert mock_transport.run_bytes.call_args.args[0] == (
        "issue",
        "search",
        case.query,
        "--output",
        "json",
    )


@pytest.mark.parametrize("case", _SEARCH_VALIDATION_CASES, ids=lambda case: case.id)
def test_issue_search_validation_is_zero_io(
    case: SearchValidationCase,
    mock_transport: MagicMock,
) -> None:
    resource = IssueResource(mock_transport, ClientConfig())

    with pytest.raises(case.expected_exception):
        resource.search_command(case.query)

    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()
    mock_transport.spawn.assert_not_called()


@pytest.mark.parametrize("case", _MALFORMED_SEARCH_CASES, ids=lambda case: case.id)
def test_issue_search_rejects_malformed_top_level_shapes(
    case: MalformedSearchCase, mock_transport: MagicMock
) -> None:
    mock_transport.run_bytes.return_value = RawCommandResult(
        argv=("issue", "search", "needle", "--output", "json"),
        exit_code=0,
        stdout=case.payload,
        stderr=b"",
        duration=datetime.timedelta(),
    )
    resource = IssueResource(mock_transport, ClientConfig())

    with pytest.raises(OutputShapeError):
        resource.search("needle")


def test_issue_search_rejects_malformed_json(mock_transport: MagicMock) -> None:
    mock_transport.run_bytes.return_value = RawCommandResult(
        argv=("issue", "search", "needle", "--output", "json"),
        exit_code=0,
        stdout=b"{",
        stderr=b"",
        duration=datetime.timedelta(),
    )
    resource = IssueResource(mock_transport, ClientConfig())

    with pytest.raises(JsonOutputError):
        resource.search("needle")
