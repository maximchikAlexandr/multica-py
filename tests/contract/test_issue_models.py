from __future__ import annotations

import datetime
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast
from unittest.mock import MagicMock

import pytest

import multica_py
from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    _issue_from_wire,
    _issue_list_page_from_wire,
    _IssueListPageWire,
    _IssueWire,
    _task_run_from_wire,
    _TaskRunWire,
)
from multica_py.config import ClientConfig
from multica_py.entities._base import _entity_policy
from multica_py.entities.issues import Issue, TaskRun
from multica_py.enums import IssueStatus
from multica_py.exceptions import OutputShapeError
from multica_py.models.issue_activity import IssueUsage
from multica_py.models.issues import (
    IssueAssignee,
    IssueListFilter,
    IssueListPage,
    LinkedPullRequest,
)
from multica_py.resources.issues import IssueResource
from multica_py.types import JsonValue

_ACTIVITY_FIXTURE = json.loads(
    (Path(__file__).parents[1] / "fixtures/provenance/issue_activity_v0432.json").read_text()
)


@dataclass(frozen=True)
class AssigneeProjectionCase:
    id: str
    projection: dict[str, object]
    expected: IssueAssignee | None
    error: str | None = None


ASSIGNEE_PROJECTION_CASES = (
    AssigneeProjectionCase(
        "nested",
        {"assignee": {"id": "agent-1", "type": "agent", "name": "Agent"}},
        IssueAssignee(id="agent-1", type="agent", name="Agent"),
    ),
    AssigneeProjectionCase(
        "scalar",
        {"assignee_id": "agent-1", "assignee_type": "agent"},
        IssueAssignee(id="agent-1", type="agent"),
    ),
    AssigneeProjectionCase(
        "matching-dual",
        {
            "assignee": {"id": "agent-1", "type": "agent", "name": "Agent"},
            "assignee_id": "agent-1",
            "assignee_type": "agent",
        },
        IssueAssignee(id="agent-1", type="agent", name="Agent"),
    ),
    AssigneeProjectionCase(
        "null-dual",
        {"assignee": None, "assignee_id": None, "assignee_type": None},
        None,
    ),
    AssigneeProjectionCase("omitted", {}, None),
    AssigneeProjectionCase("partial-id", {"assignee_id": "agent-1"}, None, "must contain both"),
    AssigneeProjectionCase(
        "partial-null", {"assignee_id": None, "assignee_type": "agent"}, None, "two values"
    ),
    AssigneeProjectionCase(
        "conflicting-dual",
        {
            "assignee": {"id": "agent-1", "type": "agent"},
            "assignee_id": "agent-2",
            "assignee_type": "agent",
        },
        None,
        "projections conflict",
    ),
)


@dataclass(frozen=True)
class DecodeCase:
    id: str
    payload: dict[str, object]
    expected: dict[str, object]


USAGE_DECODE_CASES = (
    DecodeCase(
        "current",
        _ACTIVITY_FIXTURE["usage"],
        {
            "total_runs": 0,
            "cost_usd": None,
            "period_start": None,
            "period_end": None,
            "task_count": 1,
            "total_input_tokens": 3800,
            "total_output_tokens": 11700,
            "total_cache_read_tokens": 537800,
            "total_cache_write_tokens": 42400,
            "cost_usd_ticks": 125000,
            "uncosted_input_tokens": 10,
            "uncosted_output_tokens": 20,
            "uncosted_cache_read_tokens": 30,
            "uncosted_cache_write_tokens": 40,
            "total_tokens": None,
        },
    ),
    DecodeCase(
        "legacy",
        _ACTIVITY_FIXTURE["legacy_usage"],
        {
            "total_runs": 2,
            "total_tokens": 15,
            "cost_usd": 0.08,
            "task_count": None,
            "total_input_tokens": None,
            "total_cache_read_tokens": None,
        },
    ),
    DecodeCase(
        "explicit-null-current",
        _ACTIVITY_FIXTURE["null_usage"],
        {
            "total_runs": 0,
            "task_count": None,
            "total_input_tokens": None,
            "total_output_tokens": None,
            "total_cache_read_tokens": None,
            "total_cache_write_tokens": None,
            "cost_usd_ticks": None,
            "uncosted_input_tokens": None,
            "uncosted_output_tokens": None,
            "uncosted_cache_read_tokens": None,
            "uncosted_cache_write_tokens": None,
        },
    ),
)


TASK_RUN_DECODE_CASES = (
    DecodeCase(
        "current",
        _ACTIVITY_FIXTURE["task_run"],
        {
            "id": "task-1",
            "status": "completed",
            "agent_id": "agent-1",
            "runtime_id": "runtime-1",
            "workspace_id": "workspace-1",
            "started_at": datetime.datetime(2026, 8, 21, 9, 0, 1, tzinfo=datetime.UTC),
            "completed_at": datetime.datetime(2026, 8, 21, 9, 5, tzinfo=datetime.UTC),
            "dispatched_at": datetime.datetime(2026, 8, 21, 9, tzinfo=datetime.UTC),
            "created_at": datetime.datetime(2026, 8, 21, 8, 59, 59, tzinfo=datetime.UTC),
            "work_dir": "/tmp/multica/workspace-1/task-1/workdir",
            "relative_work_dir": "workspace-1/task-1/workdir",
            "durable_work_dir": "/tmp/project",
            "relative_durable_work_dir": "project",
            "branch_name": "fix/issue-81",
            "result": MappingProxyType({"summary": "done", "files": ("src/example.py",)}),
            "error": None,
            "failure_reason": "",
        },
    ),
    DecodeCase(
        "legacy-omitted",
        _ACTIVITY_FIXTURE["legacy_task_run"],
        {
            "id": "task-legacy",
            "status": "completed",
            "agent_id": None,
            "runtime_id": None,
            "workspace_id": None,
            "started_at": None,
            "completed_at": None,
            "dispatched_at": None,
            "created_at": None,
            "work_dir": None,
            "relative_work_dir": None,
            "durable_work_dir": None,
            "relative_durable_work_dir": None,
            "branch_name": None,
            "result": None,
            "error": None,
            "failure_reason": None,
        },
    ),
    DecodeCase(
        "explicit-null",
        _ACTIVITY_FIXTURE["null_task_run"],
        {
            "id": "task-null",
            "status": "failed",
            "agent_id": None,
            "runtime_id": None,
            "workspace_id": None,
            "started_at": None,
            "completed_at": None,
            "dispatched_at": None,
            "created_at": None,
            "work_dir": None,
            "relative_work_dir": None,
            "durable_work_dir": None,
            "relative_durable_work_dir": None,
            "branch_name": None,
            "result": None,
            "error": None,
            "failure_reason": None,
        },
    ),
)


@pytest.mark.parametrize("case", ASSIGNEE_PROJECTION_CASES, ids=lambda case: case.id)
def test_issue_assignee_projection_matrix(case: AssigneeProjectionCase) -> None:
    payload = {"id": "issue-1", "title": "T", "status": "todo", **case.projection}
    wire = decode_json(json.dumps(payload).encode(), _IssueWire)
    if case.error is not None:
        with pytest.raises(OutputShapeError, match=case.error):
            _issue_from_wire(wire)
        return
    assert _issue_from_wire(wire).assignee == case.expected


def test_v0432_provenance_fixture_matches_verified_release() -> None:
    assert _ACTIVITY_FIXTURE["_meta"]["commit"] == ("d60775aa9394b911b18701a326f655465604e7d1")
    issue = _issue_from_wire(
        decode_json(json.dumps(_ACTIVITY_FIXTURE["issue_scalar_assignee"]).encode(), _IssueWire)
    )
    assert issue.assignee == IssueAssignee(id="agent-1", type="agent")


@pytest.mark.parametrize("case", USAGE_DECODE_CASES, ids=lambda case: case.id)
def test_issue_usage_decode_matrix(case: DecodeCase) -> None:
    usage = decode_json(json.dumps(case.payload).encode(), IssueUsage)
    for field, expected in case.expected.items():
        assert getattr(usage, field) == expected


@pytest.mark.parametrize("case", TASK_RUN_DECODE_CASES, ids=lambda case: case.id)
def test_task_run_decode_matrix(case: DecodeCase) -> None:
    wire = decode_json(json.dumps(case.payload).encode(), _TaskRunWire)
    run = _task_run_from_wire(wire, issue_id="issue-1")
    assert run.issue_id == "issue-1"
    expected_presence = {
        "current": "value",
        "legacy-omitted": "missing",
        "explicit-null": "null",
    }[case.id]
    assert run._wire_presence == (("agent_id", expected_presence),)
    for field, expected in case.expected.items():
        assert getattr(run, field) == expected
    if case.id == "current":
        assert isinstance(run.result, MappingProxyType)


@pytest.mark.parametrize(
    "factory",
    (
        lambda: TaskRun(
            id="task-1",
            status="completed",
            result=cast("JsonValue", {"files": ["before"]}),
        ),
        lambda: TaskRun.from_dict(
            {"id": "task-1", "status": "completed", "result": {"files": ["before"]}}
        ),
    ),
    ids=("constructor", "from-dict"),
)
def test_task_run_result_is_recursively_immutable(factory: Callable[[], TaskRun]) -> None:
    run = factory()
    assert run._wire_presence == ()
    assert isinstance(run.result, MappingProxyType)
    assert run.result["files"] == ("before",)
    with pytest.raises(TypeError):
        run.result["files"] = ("after",)  # type: ignore[index]
    with pytest.raises(AttributeError):
        run.result["files"].append("after")


def test_issue_summary_is_not_a_public_model() -> None:
    import multica_py.models.issues as issue_models

    assert not hasattr(multica_py, "IssueSummary")
    assert not hasattr(issue_models, "IssueSummary")


def test_issue_summary_name_is_absent_from_package_source() -> None:
    source_root = Path(__file__).parents[2] / "src" / "multica_py"
    assert all("IssueSummary" not in path.read_text() for path in source_root.rglob("*.py"))


def test_issue_unknown_status_decodes_without_constructor_crash() -> None:
    wire = decode_json(b'{"id":"iss_001","title":"T","status":"open"}', _IssueWire)
    issue = _issue_from_wire(wire)
    assert issue.status == "open"


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
    assert issue.status == IssueStatus.todo


def test_issue_pull_request_snapshot_preserves_r26_relation_name() -> None:
    wire = decode_json(
        b'{"id":"iss_001","title":"T","status":"todo",'
        b'"pull_requests":[{"url":"https://example.test/pr/1"}]}',
        _IssueWire,
    )
    issue = _issue_from_wire(wire)

    assert issue.pull_request_snapshot == (LinkedPullRequest(url="https://example.test/pr/1"),)
    assert "pull_request_snapshot" in _entity_policy(type(issue)).public_fields
    assert "pull_requests" not in _entity_policy(type(issue)).public_fields


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
        issue = _issue_from_wire(decode_json(json.dumps(item).encode(), _IssueWire))
        assert issue.id
        assert issue.title
        assert issue.description is None


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
    assert page.items is page.issues
    assert isinstance(page.items[0], Issue)
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


def test_issue_collection_row_scalar_fields_decoding() -> None:
    minimal_data = b'{"id":"i1","title":"t","status":"todo"}'
    minimal = _issue_from_wire(decode_json(minimal_data, _IssueWire))
    assert minimal.created_at is None
    assert minimal.parent_id is None
    assert minimal.project_id is None
    assert minimal.creator_id is None
    assert minimal.creator_type is None
    assert minimal.match_source is None

    full_data = (
        b'{"id":"i1","title":"t","status":"todo",'
        b'"created_at":"2026-01-01T00:00:00Z","parent_issue_id":"p1",'
        b'"project_id":"pr1","creator_id":"u1","creator_type":"member"}'
    )
    issue = _issue_from_wire(decode_json(full_data, _IssueWire))
    assert issue.created_at == datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    assert issue.parent_id == "p1"
    assert issue.project_id == "pr1"
    assert issue.creator_id == "u1"
    assert issue.creator_type == "member"


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
