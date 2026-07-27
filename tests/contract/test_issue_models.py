from __future__ import annotations

import json
from typing import Protocol

import pytest

from multica_py._internal.decoders import decode_json
from multica_py._internal.wire_models import IssueWire, issue_from_wire
from multica_py.models.issue_activity import IssueUsage
from multica_py.models.issues import IssueCreateRequest, IssueSummary, IssueUpdateRequest


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

    wire = decode_json(json.dumps(data).encode(), IssueWire)
    issue = issue_from_wire(wire)
    assert issue.id == "iss_001"
    assert issue.title == "Test issue"
    assert issue.status.value == "todo"


def test_issue_additive_fields_ignored() -> None:
    wire = decode_json(
        b'{"id":"iss_001","title":"T","description":"D","status":"todo","unknown":"x"}',
        IssueWire,
    )
    assert issue_from_wire(wire).title == "T"


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
    wire = decode_json(json.dumps(data).encode(), IssueWire)
    issue = issue_from_wire(wire)
    assert issue.parent_id == "p_1"
    assert issue.project_id == "pr_1"
    assert issue.creator_id == "u_1"
    assert issue.creator_type == "member"

    minimal = decode_json(b'{"id":"iss_1","title":"t","status":"todo"}', IssueWire)
    minimal_issue = issue_from_wire(minimal)
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
