from __future__ import annotations

import json

from multica_py._internal.decoders import decode_json
from multica_py._internal.wire_models import IssueWire, issue_from_wire
from multica_py.models.issue_activity import IssueUsage
from multica_py.models.issues import IssueCreateRequest, IssueSummary, IssueUpdateRequest


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


def test_issue_create_request_rejects_empty_project_id() -> None:
    try:
        IssueCreateRequest(title="Test", project_id="")
    except ValueError as exc:
        assert "project_id" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_issue_update_request_rejects_empty_project_id() -> None:
    try:
        IssueUpdateRequest(project_id="")
    except ValueError as exc:
        assert "project_id" in str(exc)
    else:
        raise AssertionError("expected ValueError")
