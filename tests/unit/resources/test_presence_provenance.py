from __future__ import annotations

import json
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.decoders import decode_json
from multica_py._internal.wire_models import (
    _autopilot_from_wire,
    _autopilot_run_from_wire,
    _AutopilotRunWire,
    _AutopilotWire,
    _issue_from_wire,
    _IssueWire,
    _task_run_from_wire,
    _TaskRunWire,
)
from multica_py.entities.issues import Issue, TaskRun
from multica_py.enums import IssueStatus
from multica_py.models.issues import IssueAssignee


def _issue_payload(**fields: object) -> bytes:
    return json.dumps({"id": "issue-1", "title": "Issue", "status": "todo", **fields}).encode()


@pytest.mark.parametrize(
    ("field", "wire_value", "seed"),
    (
        ("parent_issue_id", msgspec.UNSET, "missing"),
        ("parent_issue_id", None, "null"),
        ("parent_issue_id", "parent-1", "value"),
        ("project_id", msgspec.UNSET, "missing"),
        ("project_id", None, "null"),
        ("project_id", "project-1", "value"),
        ("assignee", msgspec.UNSET, "missing"),
        ("assignee", None, "null"),
        (
            "assignee",
            {"id": "agent-1", "name": "Agent", "type": "agent"},
            "value",
        ),
    ),
)
def test_issue_wire_presence_preserves_public_values(
    field: str, wire_value: object, seed: str
) -> None:
    encoded = {} if wire_value is msgspec.UNSET else {field: wire_value}
    issue = _issue_from_wire(decode_json(_issue_payload(**encoded), _IssueWire))

    public_field = "parent_id" if field == "parent_issue_id" else field
    expected = None if wire_value is msgspec.UNSET else wire_value
    if field == "assignee" and isinstance(expected, dict):
        expected = IssueAssignee(**expected)
    assert getattr(issue, public_field) == expected
    presence_field = "parent_id" if field == "parent_issue_id" else field
    assert (presence_field, seed) in issue._wire_presence


@pytest.mark.parametrize(
    ("field", "wire_value", "seed"),
    (
        ("project_id", msgspec.UNSET, "missing"),
        ("project_id", None, "null"),
        ("project_id", "project-1", "value"),
    ),
)
def test_autopilot_project_presence_preserves_public_value(
    field: str, wire_value: object, seed: str
) -> None:
    fields = {} if wire_value is msgspec.UNSET else {field: wire_value}
    wire = decode_json(
        json.dumps(
            {
                "id": "autopilot-1",
                "workspace_id": "workspace-1",
                "title": "Autopilot",
                "assignee_type": "agent",
                "assignee_id": "agent-1",
                "status": "active",
                "execution_mode": "manual",
                "created_by_type": "member",
                "created_by_id": "member-1",
                **fields,
            }
        ).encode(),
        _AutopilotWire,
    )
    autopilot = _autopilot_from_wire(wire)

    assert autopilot.project_id == (None if wire_value is msgspec.UNSET else wire_value)
    assert ("project_id", seed) in autopilot._wire_presence


@pytest.mark.parametrize(
    ("wire_value", "seed"),
    ((msgspec.UNSET, "missing"), (None, "null"), ("issue-1", "value")),
)
def test_autopilot_run_issue_presence_preserves_public_value(wire_value: object, seed: str) -> None:
    fields = {} if wire_value is msgspec.UNSET else {"issue_id": wire_value}
    wire = decode_json(
        json.dumps(
            {
                "id": "run-1",
                "autopilot_id": "autopilot-1",
                "source": "manual",
                "status": "completed",
                **fields,
            }
        ).encode(),
        _AutopilotRunWire,
    )
    run = _autopilot_run_from_wire(wire)

    assert run.issue_id == (None if wire_value is msgspec.UNSET else wire_value)
    assert ("issue_id", seed) in run._wire_presence


@pytest.mark.parametrize(
    ("wire_value", "seed"),
    ((msgspec.UNSET, "missing"), (None, "null"), ("agent-1", "value")),
)
def test_task_run_agent_presence_preserves_inherited_issue_context(
    wire_value: object, seed: str
) -> None:
    fields = {} if wire_value is msgspec.UNSET else {"agent_id": wire_value}
    wire = decode_json(
        json.dumps({"id": "task-1", "status": "completed", **fields}).encode(),
        _TaskRunWire,
    )
    task_run = _task_run_from_wire(wire, issue_id="issue-1")

    assert isinstance(task_run, TaskRun)
    assert task_run.agent_id == (None if wire_value is msgspec.UNSET else wire_value)
    assert task_run.issue_id == "issue-1"
    assert ("agent_id", seed) in task_run._wire_presence


def test_detach_preserves_presence_and_freshens_runtime_state() -> None:
    issue = _issue_from_wire(
        decode_json(
            _issue_payload(parent_issue_id=None, project_id="project-1"),
            _IssueWire,
        )
    )._with_client(MagicMock())
    _ = issue.comments

    detached = issue.detach()

    assert detached._client is None
    assert detached._wire_presence == issue._wire_presence
    assert detached._comments is None
    assert detached == issue
    assert hash(detached) == hash(issue)
    assert "_wire_presence" not in detached.to_dict()
    assert "_wire_presence" not in detached.to_json()
    assert "_wire_presence" not in repr(detached)
    assert issue._comments is not None

    serialized = Issue.from_dict(detached.to_dict())
    assert serialized._wire_presence == ()


def test_detach_preserves_run_context_and_manual_none_has_no_seed() -> None:
    run = _autopilot_run_from_wire(
        decode_json(
            b'{"id":"run-1","autopilot_id":"a1","source":"manual",'
            b'"status":"completed","issue_id":"issue-1"}',
            _AutopilotRunWire,
        )
    )
    detached = run._with_client(MagicMock()).detach()

    assert detached.issue_id == "issue-1"
    assert detached._wire_presence == run._wire_presence
    assert detached._client is None

    direct = Issue(id="issue-1", title="Issue", status=IssueStatus.todo)
    assert direct._wire_presence == ()
    assert direct.to_dict()["parent_id"] is None
    assert "_wire_presence" not in direct.to_json()
