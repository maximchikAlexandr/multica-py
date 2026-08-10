from __future__ import annotations

import datetime
import json
from typing import Protocol
from unittest.mock import MagicMock

import pytest

from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    _issue_from_wire,
    _issue_list_page_from_wire,
    _IssueListPageWire,
    _IssueSummaryWire,
    _IssueWire,
    issue_summary_from_wire,
)
from multica_py.config import ClientConfig
from multica_py.exceptions import OutputShapeError
from multica_py.models.issue_activity import IssueUsage
from multica_py.models.issues import (
    IssueCreateRequest,
    IssueListFilter,
    IssueListPage,
    IssueSummary,
    IssueUpdateRequest,
    LinkedPullRequest,
)
from multica_py.resources.issues import IssueResource


class _IdFieldFactory(Protocol):
    def __call__(self, **kw: object) -> IssueCreateRequest | IssueUpdateRequest: ...


def _make_create_req(**kw: object) -> IssueCreateRequest:
    return IssueCreateRequest(title="t", **kw)  # type: ignore[arg-type]


def _make_update_req(**kw: object) -> IssueUpdateRequest:
    return IssueUpdateRequest(**kw)  # type: ignore[arg-type]


def test_issue_get_decoding() -> None:
    data = {
        "id": "iss_001",
        "title": "Test issue",
        "description": "A test issue description",
        "status": "todo",
        "priority": "high",
        "assignee": {"id": "usr_001", "name": "Test User", "type": "member"},
        "pull_requests": [],
        "children": [],
        "labels": [{"id": "lbl_001", "name": "bug", "color": "#ff0000"}],
        "metadata": {},
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "unknown_field": "should be ignored by msgspec",
    }

    wire = decode_json(json.dumps(data).encode(), _IssueWire)
    issue = _issue_from_wire(wire)
    assert issue.id == "iss_001"
    assert issue.title == "Test issue"
    assert issue.status.value == "todo"
    assert issue.assignee is not None
    assert issue.assignee.id == "usr_001"


def test_issue_get_decodes_cli_scalar_assignee_projection() -> None:
    wire = decode_json(
        b'{"id":"iss_001","title":"T","status":"backlog",'
        b'"assignee_id":"agent-1","assignee_type":"agent"}',
        _IssueWire,
    )

    issue = _issue_from_wire(wire)

    assert issue.assignee is not None
    assert issue.assignee.id == "agent-1"
    assert issue.assignee.type == "agent"


def test_issue_get_rejects_conflicting_assignee_projections() -> None:
    wire = decode_json(
        b'{"id":"iss_001","title":"T","status":"backlog",'
        b'"assignee":{"id":"agent-1","type":"agent"},'
        b'"assignee_id":"agent-2","assignee_type":"agent"}',
        _IssueWire,
    )

    with pytest.raises(OutputShapeError, match="assignee projections conflict"):
        _issue_from_wire(wire)


def test_issue_pull_request_snapshot_preserves_r26_relation_name() -> None:
    wire = decode_json(
        b'{"id":"iss_001","title":"T","status":"todo",'
        b'"pull_requests":[{"url":"https://example.test/pr/1"}]}',
        _IssueWire,
    )
    issue = _issue_from_wire(wire)

    assert issue.pull_request_snapshot == (LinkedPullRequest(url="https://example.test/pr/1"),)
    assert "pull_request_snapshot" in issue._PUBLIC_FIELDS
    assert "pull_requests" not in issue._PUBLIC_FIELDS


def test_issue_additive_fields_ignored() -> None:
    wire = decode_json(
        b'{"id":"iss_001","title":"T","description":"D","status":"todo","unknown":"x"}',
        _IssueWire,
    )
    assert _issue_from_wire(wire).title == "T"


def test_issue_list_decoding() -> None:
    data = [
        {"id": "iss_001", "title": "Issue one", "status": "todo", "priority": "high"},
        {"id": "iss_002", "title": "Issue two", "status": "in_progress", "priority": "medium"},
    ]
    for item in data:
        summary = decode_json(json.dumps(item).encode(), IssueSummary)
        assert summary.id
        assert summary.title


def test_issue_usage_decodes_cost_usd() -> None:
    usage = decode_json(b'{"total_runs": 2, "cost_usd": 0.08}', IssueUsage)
    assert usage.cost_usd == 0.08


def test_issue_scalar_relation_fields_decoding() -> None:
    data = {
        "id": "iss_1",
        "title": "t",
        "status": "todo",
        "parent_issue_id": "p_1",
        "project_id": "pr_1",
        "creator_id": "u_1",
        "creator_type": "member",
    }
    wire = decode_json(json.dumps(data).encode(), _IssueWire)
    issue = _issue_from_wire(wire)
    assert issue.parent_id == "p_1"
    assert issue.project_id == "pr_1"
    assert issue.creator_id == "u_1"
    assert issue.creator_type == "member"

    minimal = decode_json(b'{"id":"iss_1","title":"t","status":"todo"}', _IssueWire)
    minimal_issue = _issue_from_wire(minimal)
    assert minimal_issue.parent_id is None
    assert minimal_issue.project_id is None
    assert minimal_issue.creator_id is None
    assert minimal_issue.creator_type is None


@pytest.mark.parametrize(
    ("factory", "field_name", "bad_value"),
    [
        (_make_create_req, "project_id", ""),
        (_make_create_req, "parent_id", ""),
        (_make_create_req, "parent_id", "  "),
        (_make_update_req, "project_id", ""),
        (_make_update_req, "parent_id", ""),
        (_make_update_req, "parent_id", "  "),
    ],
)
def test_request_rejects_empty_id_field(
    factory: _IdFieldFactory,
    field_name: str,
    bad_value: str,
) -> None:
    with pytest.raises(ValueError) as exc:
        factory(**{field_name: bad_value})
    assert field_name in str(exc.value)


def test_issue_list_page_decoding() -> None:
    full_data = (
        b'{"issues":[{"id":"i1","title":"t","status":"todo",'
        b'"created_at":"2026-01-01T00:00:00Z","parent_issue_id":"p1",'
        b'"project_id":"pr1","creator_id":"u1","creator_type":"member"}],'
        b'"has_more":true,"limit":50,"offset":20,"total":137}'
    )
    wire = decode_json(full_data, _IssueListPageWire)
    page = _issue_list_page_from_wire(wire)
    assert page.has_more is True
    assert page.limit == 50
    assert page.offset == 20
    assert page.total == 137
    assert len(page.issues) == 1
    assert page.issues[0].created_at == datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    assert page.issues[0].parent_id == "p1"
    assert page.issues[0].project_id == "pr1"
    assert page.issues[0].creator_id == "u1"
    assert page.issues[0].creator_type == "member"

    empty_data = b'{"issues":[]}'
    empty_wire = decode_json(empty_data, _IssueListPageWire)
    empty_page = _issue_list_page_from_wire(empty_wire)
    assert empty_page.has_more is False
    assert empty_page.limit is None
    assert empty_page.offset is None
    assert empty_page.total is None
    assert empty_page.issues == ()


def test_issue_summary_scalar_fields_decoding() -> None:
    minimal_data = b'{"id":"i1","title":"t","status":"todo"}'
    minimal = decode_json(minimal_data, IssueSummary)
    assert minimal.created_at is None
    assert minimal.parent_id is None
    assert minimal.project_id is None
    assert minimal.creator_id is None
    assert minimal.creator_type is None

    full_data = (
        b'{"id":"i1","title":"t","status":"todo",'
        b'"created_at":"2026-01-01T00:00:00Z","parent_issue_id":"p1",'
        b'"project_id":"pr1","creator_id":"u1","creator_type":"member"}'
    )
    wire = decode_json(full_data, _IssueSummaryWire)
    summary = issue_summary_from_wire(wire)
    assert summary.created_at == datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    assert summary.parent_id == "p1"
    assert summary.project_id == "pr1"
    assert summary.creator_id == "u1"
    assert summary.creator_type == "member"


@pytest.fixture
def _mock_transport() -> MagicMock:
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.return_value = MagicMock(
        stdout=b'{"issues":[],"has_more":false,"limit":0,"offset":0,"total":0}',
        argv=("test",),
    )
    transport.run_text.return_value = MagicMock()
    return transport


@pytest.mark.parametrize(
    ("offset", "should_raise"),
    [
        (-1, True),
        (-5, True),
        (0, False),
    ],
)
def test_issue_list_filter_rejects_negative_offset(
    offset: int, should_raise: bool, _mock_transport: MagicMock
) -> None:
    resource = IssueResource(_mock_transport, ClientConfig())
    if should_raise:
        with pytest.raises(ValueError) as exc:
            resource.list(IssueListFilter(offset=offset))
        assert "offset" in str(exc.value)
        _mock_transport.run_bytes.assert_not_called()
    else:
        resource.list(IssueListFilter(offset=offset))
        _mock_transport.run_bytes.assert_called_once()
        call_args = _mock_transport.run_bytes.call_args
        assert call_args.args == (("issue", "list", "--offset", "0", "--output", "json"),)
