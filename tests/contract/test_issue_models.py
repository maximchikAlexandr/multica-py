from __future__ import annotations

import json
from typing import TypedDict

from multica_py._internal.decoders import decode_json
from multica_py._internal.manifest import CLI_MANIFEST_PATH
from multica_py._internal.wire_models import IssueWire, issue_from_wire
from multica_py.models.issues import IssueSummary


class IssueFixture(TypedDict):
    stdout: object


def test_issue_get_decoding() -> None:
    fixture_path = (
        CLI_MANIFEST_PATH.parent.parent.parent.parent
        / "tests"
        / "fixtures"
        / "json"
        / "issues"
        / "issue_get.json"
    )
    with open(fixture_path, encoding="utf-8") as f:
        wrapped: IssueFixture = json.load(f)
    data = wrapped["stdout"]

    wire = decode_json(json.dumps(data).encode(), IssueWire)
    issue = issue_from_wire(wire)
    assert issue.id == "iss_001"
    assert issue.title == "Test issue"
    assert issue.status.value == "todo"


def test_issue_additive_fields_ignored() -> None:
    data = {
        "id": "iss_001",
        "title": "Test",
        "description": "Desc",
        "status": "todo",
        "unknown_field": "should_be_ignored",
    }
    wire = decode_json(json.dumps(data).encode(), IssueWire)
    issue = issue_from_wire(wire)
    assert issue.title == "Test"
    assert hasattr(issue, "title")


def test_issue_list_decoding() -> None:
    data = [
        {"id": "iss_001", "title": "Issue one", "status": "todo", "priority": "high"},
        {"id": "iss_002", "title": "Issue two", "status": "in_progress", "priority": "medium"},
    ]
    for item in data:
        summary = decode_json(json.dumps(item).encode(), IssueSummary)
        assert summary.id
        assert summary.title
