from __future__ import annotations

import datetime
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast
from unittest.mock import MagicMock

import msgspec
import pytest

import multica_py
from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    _CommentWire,
    _issue_from_wire,
    _issue_list_page_from_wire,
    _IssueListPageWire,
    _IssueWire,
    _task_run_from_wire,
    _TaskRunWire,
    comment_from_wire,
    decode_run_messages,
)
from multica_py.config import ClientConfig
from multica_py.entities._base import _entity_policy
from multica_py.entities.agents import Agent
from multica_py.entities.issues import Issue, TaskRun
from multica_py.enums import IssueStatus
from multica_py.exceptions import OutputShapeError
from multica_py.models.agents import AgentTask
from multica_py.models.issue_activity import (
    IssueUsage,
    TaskCancellationActor,
    TaskIssueStatusData,
    TaskPluginHookTool,
    TaskProjectResourceData,
    TaskUsageData,
)
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
    error: str | None = None


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
    DecodeCase(
        "divergent-exact-counts",
        {
            "total_runs": 2,
            "task_count": 3,
            "terminal_task_count": 9007199254740993,
            "metered_task_count": 0,
            "unreported_task_count": 7,
        },
        {
            "total_runs": 2,
            "task_count": 3,
            "terminal_task_count": 9007199254740993,
            "metered_task_count": 0,
            "unreported_task_count": 7,
        },
    ),
    DecodeCase("negative-exact-count", {"terminal_task_count": -1}, {}, "negative"),
    DecodeCase("null-exact-count", {"terminal_task_count": None}, {}, "null"),
)


TASK_RUN_DECODE_CASES = (
    DecodeCase(
        "current",
        {
            **_ACTIVITY_FIXTURE["task_run"],
            "cancelled_by": {"type": "system", "id": "actor-1", "name": "System"},
            "workspace_slug": "acme",
            "issue_identifier": "ACME-1",
            "workspace_context": "repo context",
            "issue_statuses": [
                {"key": "todo", "name": "Todo", "category": "open", "description": ""}
            ],
            "issue_statuses_omitted": 0,
            "project_id": "project-1",
            "project_title": "Project",
            "project_description": "Description",
            "project_resources": [
                {
                    "id": "resource-1",
                    "resource_type": "github_repo",
                    "resource_ref": {"owner": "acme", "repo": "sdk"},
                    "label": "SDK",
                }
            ],
            "trigger_comment_id": "comment-1",
            "coalesced_comment_ids": [],
            "delivered_comment_ids": ["comment-1"],
            "trigger_thread_id": "thread-1",
            "trigger_comment_content": "Please review",
            "trigger_summary": "Review request",
            "trigger_author_type": "member",
            "trigger_author_name": "Alice",
            "new_comment_count": 0,
            "new_comments_since": "2026-08-21T08:59:00Z",
            "new_comments_delta_known": True,
            "quick_create_prompt": None,
            "quick_create_priority": "high",
            "quick_create_due_date": "2026-08-22",
            "quick_create_attachment_ids": [],
            "quick_create_source_context": {"source": "modal"},
            "plugin_hook_tools": [
                {
                    "installation_id": "install-1",
                    "hook_key": "review",
                    "name": "Review",
                    "description": "Review changes",
                    "input_schema": {"required": ["path"]},
                }
            ],
            "usage": [
                {
                    "provider": "openai",
                    "model": "gpt-5",
                    "input_tokens": 1,
                    "output_tokens": 2,
                    "cache_read_tokens": 0,
                    "cache_write_tokens": 0,
                    "cost_usd_ticks": 0,
                }
            ],
        },
        {
            "id": "task-1",
            "status": "completed",
            "cancelled_by": TaskCancellationActor(type="system", id="actor-1", name="System"),
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
            "workspace_slug": "acme",
            "issue_identifier": "ACME-1",
            "workspace_context": "repo context",
            "issue_statuses": (
                TaskIssueStatusData(key="todo", name="Todo", category="open", description=""),
            ),
            "issue_statuses_omitted": 0,
            "project_id": "project-1",
            "project_title": "Project",
            "project_description": "Description",
            "project_resources": (
                TaskProjectResourceData(
                    id="resource-1",
                    resource_type="github_repo",
                    resource_ref=MappingProxyType({"owner": "acme", "repo": "sdk"}),
                    label="SDK",
                ),
            ),
            "trigger_comment_id": "comment-1",
            "coalesced_comment_ids": (),
            "delivered_comment_ids": ("comment-1",),
            "trigger_thread_id": "thread-1",
            "trigger_comment_content": "Please review",
            "trigger_summary": "Review request",
            "trigger_author_type": "member",
            "trigger_author_name": "Alice",
            "new_comment_count": 0,
            "new_comments_since": datetime.datetime(2026, 8, 21, 8, 59, tzinfo=datetime.UTC),
            "new_comments_delta_known": True,
            "quick_create_prompt": None,
            "quick_create_priority": "high",
            "quick_create_due_date": "2026-08-22",
            "quick_create_attachment_ids": (),
            "quick_create_source_context": MappingProxyType({"source": "modal"}),
            "plugin_hook_tools": (
                TaskPluginHookTool(
                    installation_id="install-1",
                    hook_key="review",
                    name="Review",
                    description="Review changes",
                    input_schema=MappingProxyType({"required": ("path",)}),
                ),
            ),
            "usage": (
                TaskUsageData(
                    provider="openai",
                    model="gpt-5",
                    input_tokens=1,
                    output_tokens=2,
                    cache_read_tokens=0,
                    cache_write_tokens=0,
                    cost_usd_ticks=0,
                ),
            ),
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
            "workspace_slug": None,
            "issue_identifier": None,
            "workspace_context": None,
            "issue_statuses": (),
            "issue_statuses_omitted": None,
            "project_id": None,
            "project_title": None,
            "project_description": None,
            "project_resources": (),
            "trigger_comment_id": None,
            "coalesced_comment_ids": (),
            "delivered_comment_ids": (),
            "trigger_thread_id": None,
            "trigger_comment_content": None,
            "trigger_summary": None,
            "trigger_author_type": None,
            "trigger_author_name": None,
            "new_comment_count": None,
            "new_comments_since": None,
            "new_comments_delta_known": None,
            "quick_create_prompt": None,
            "quick_create_priority": None,
            "quick_create_due_date": None,
            "quick_create_attachment_ids": (),
            "quick_create_source_context": None,
            "plugin_hook_tools": (),
            "usage": (),
        },
    ),
    DecodeCase(
        "explicit-null",
        {**_ACTIVITY_FIXTURE["null_task_run"], "new_comments_delta_known": False},
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
            "workspace_slug": None,
            "issue_identifier": None,
            "workspace_context": None,
            "issue_statuses": (),
            "issue_statuses_omitted": None,
            "project_id": None,
            "project_title": None,
            "project_description": None,
            "project_resources": (),
            "trigger_comment_id": None,
            "coalesced_comment_ids": (),
            "delivered_comment_ids": (),
            "trigger_thread_id": None,
            "trigger_comment_content": None,
            "trigger_summary": None,
            "trigger_author_type": None,
            "trigger_author_name": None,
            "new_comment_count": None,
            "new_comments_since": None,
            "new_comments_delta_known": False,
            "quick_create_prompt": None,
            "quick_create_priority": None,
            "quick_create_due_date": None,
            "quick_create_attachment_ids": (),
            "quick_create_source_context": None,
            "plugin_hook_tools": (),
            "usage": (),
        },
    ),
    DecodeCase(
        "future-actor",
        {
            "id": "task-future",
            "status": "cancelled",
            "issue_id": "issue-future",
            "cancelled_by": {"type": "future_actor", "id": "future-1"},
        },
        {
            "id": "task-future",
            "status": "cancelled",
            "cancelled_by": TaskCancellationActor(type="future_actor", id="future-1"),
        },
    ),
    DecodeCase(
        "malformed-null-actor",
        {"id": "task-malformed", "status": "cancelled", "cancelled_by": None},
        {},
        "null",
    ),
    DecodeCase(
        "malformed-missing-actor-type",
        {"id": "task-malformed", "status": "cancelled", "cancelled_by": {}},
        {},
        "type",
    ),
    DecodeCase(
        "malformed-blank-actor-type",
        {
            "id": "task-malformed",
            "status": "cancelled",
            "cancelled_by": {"type": ""},
        },
        {},
        "nonblank",
    ),
    DecodeCase(
        "malformed-wrong-actor-id",
        {
            "id": "task-malformed",
            "status": "cancelled",
            "cancelled_by": {"type": "system", "id": 1},
        },
        {},
        "id",
    ),
)


ISSUE_TARGET_DECODE_CASES = (
    DecodeCase(
        "current",
        {
            "id": "issue-1",
            "title": "Issue",
            "status": "in_progress",
            "status_name": "Working",
            "revision": 0,
            "last_activity_at": "2026-09-11T12:34:56.123456Z",
            "source_context": {"nested": [{"key": "value"}]},
        },
        {
            "status_name": "Working",
            "revision": 0,
            "last_activity_at": datetime.datetime(
                2026, 9, 11, 12, 34, 56, 123456, tzinfo=datetime.UTC
            ),
        },
    ),
    DecodeCase(
        "legacy-omitted",
        {"id": "issue-1", "title": "Issue", "status": "todo"},
        {
            "status_name": None,
            "revision": None,
            "last_activity_at": None,
            "source_context": None,
        },
    ),
)


COMMENT_REVISION_DECODE_CASES = (
    DecodeCase(
        "missing",
        {"id": "comment-1", "content": "body"},
        {"revision": None, "issue_revision": None},
    ),
    DecodeCase(
        "zero",
        {"id": "comment-1", "content": "body", "revision": 0, "issue_revision": 0},
        {"revision": 0, "issue_revision": 0},
    ),
    DecodeCase(
        "values",
        {"id": "comment-1", "content": "body", "revision": 17, "issue_revision": 42},
        {"revision": 17, "issue_revision": 42},
    ),
)


COMMENT_TOMBSTONE_DECODE_CASES = (
    DecodeCase(
        "live-omitted",
        {"id": "comment-1", "content": "body"},
        {"body": "body", "deleted_at": None},
    ),
    DecodeCase(
        "empty-live-content",
        {"id": "comment-1", "content": ""},
        {"body": "", "deleted_at": None},
    ),
    DecodeCase(
        "tombstone",
        {"id": "comment-1", "content": "", "deleted_at": "2026-09-16T05:00:00Z"},
        {
            "body": "",
            "deleted_at": datetime.datetime(2026, 9, 16, 5, 0, tzinfo=datetime.UTC),
        },
    ),
    DecodeCase(
        "explicit-null", {"id": "comment-1", "content": "", "deleted_at": None}, {}, "Expected"
    ),
    DecodeCase(
        "malformed",
        {"id": "comment-1", "content": "", "deleted_at": "not-a-timestamp"},
        {},
        "Expected",
    ),
    DecodeCase("numeric", {"id": "comment-1", "content": "", "deleted_at": 0}, {}, "Expected"),
    DecodeCase("boolean", {"id": "comment-1", "content": "", "deleted_at": True}, {}, "Expected"),
    DecodeCase("array", {"id": "comment-1", "content": "", "deleted_at": []}, {}, "Expected"),
    DecodeCase("object", {"id": "comment-1", "content": "", "deleted_at": {}}, {}, "Expected"),
)


@dataclass(frozen=True)
class MalformedModelDecodeCase:
    id: str
    model_type: object
    payload: dict[str, object]


MALFORMED_MODEL_DECODE_CASES = (
    MalformedModelDecodeCase(
        "issue-status-name-null",
        _IssueWire,
        {"id": "issue-1", "title": "Issue", "status": "todo", "status_name": None},
    ),
    MalformedModelDecodeCase(
        "issue-revision-null",
        _IssueWire,
        {"id": "issue-1", "title": "Issue", "status": "todo", "revision": None},
    ),
    MalformedModelDecodeCase(
        "comment-revision-null",
        _CommentWire,
        {"id": "comment-1", "content": "body", "revision": None},
    ),
    MalformedModelDecodeCase(
        "agent-starters-null",
        Agent,
        {"id": "agent-1", "name": "Agent", "conversation_starters": None},
    ),
    MalformedModelDecodeCase(
        "usage-provider-missing",
        _TaskRunWire,
        {
            "id": "task-1",
            "status": "completed",
            "usage": [
                {
                    "model": "gpt-5",
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "cache_read_tokens": 0,
                    "cache_write_tokens": 0,
                }
            ],
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
    if case.error is not None:
        with pytest.raises(OutputShapeError, match=case.error):
            decode_json(json.dumps(case.payload).encode(), IssueUsage)
        return
    usage = decode_json(json.dumps(case.payload).encode(), IssueUsage)
    for field, expected in case.expected.items():
        assert getattr(usage, field) == expected


@pytest.mark.parametrize("case", TASK_RUN_DECODE_CASES, ids=lambda case: case.id)
def test_task_run_decode_matrix(case: DecodeCase) -> None:
    if case.error is not None:
        with pytest.raises(OutputShapeError, match=case.error):
            wire = decode_json(json.dumps(case.payload).encode(), _TaskRunWire)
            _task_run_from_wire(wire, issue_id="issue-1")
        return
    wire = decode_json(json.dumps(case.payload).encode(), _TaskRunWire)
    run = _task_run_from_wire(wire, issue_id="issue-1")
    assert run.issue_id == "issue-1"
    expected_presence = {
        "current": "value",
        "legacy-omitted": "missing",
        "explicit-null": "null",
        "future-actor": "missing",
    }[case.id]
    assert ("agent_id", expected_presence) in run._wire_presence
    expected_delta_presence = {
        "current": "value",
        "legacy-omitted": "missing",
        "explicit-null": "value",
        "future-actor": "missing",
    }[case.id]
    assert ("new_comments_delta_known", expected_delta_presence) in run._wire_presence
    for field, expected in case.expected.items():
        assert getattr(run, field) == expected
    if case.id == "current":
        assert isinstance(run.result, MappingProxyType)
        assert not hasattr(wire, "plugin_execution_manifest")
        assert not hasattr(wire, "active_sibling_runs")


@pytest.mark.parametrize("case", ISSUE_TARGET_DECODE_CASES, ids=lambda case: case.id)
def test_issue_target_projection_decode_matrix(case: DecodeCase) -> None:
    issue = _issue_from_wire(decode_json(json.dumps(case.payload).encode(), _IssueWire))
    for field, expected in case.expected.items():
        assert getattr(issue, field) == expected
    if case.id == "current":
        assert isinstance(issue.source_context, MappingProxyType)
        assert issue.source_context["nested"][0]["key"] == "value"
        with pytest.raises(TypeError):
            issue.source_context["new"] = True  # type: ignore[index]


@pytest.mark.parametrize("case", COMMENT_REVISION_DECODE_CASES, ids=lambda case: case.id)
def test_comment_revision_decode_matrix(case: DecodeCase) -> None:
    comment = comment_from_wire(decode_json(json.dumps(case.payload).encode(), _CommentWire))
    for field, expected in case.expected.items():
        assert getattr(comment, field) == expected


@pytest.mark.parametrize("case", COMMENT_TOMBSTONE_DECODE_CASES, ids=lambda case: case.id)
def test_comment_tombstone_decode_matrix(case: DecodeCase) -> None:
    if case.error is not None:
        with pytest.raises(OutputShapeError):
            decode_json(json.dumps(case.payload).encode(), _CommentWire)
        return
    comment = comment_from_wire(decode_json(json.dumps(case.payload).encode(), _CommentWire))
    for field, expected in case.expected.items():
        assert getattr(comment, field) == expected


@pytest.mark.parametrize("case", MALFORMED_MODEL_DECODE_CASES, ids=lambda case: case.id)
def test_malformed_target_model_shapes_are_rejected(case: MalformedModelDecodeCase) -> None:
    with pytest.raises(OutputShapeError):
        decode_json(json.dumps(case.payload).encode(), case.model_type)  # type: ignore[arg-type]


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


def test_task_cancellation_actor_is_shared_by_agent_and_issue_task_paths() -> None:
    payload = {
        "id": "task-1",
        "status": "cancelled",
        "issue_id": "issue-1",
        "cancelled_by": {"type": "future_actor", "id": "actor-1", "name": "System"},
    }
    issue_run = _task_run_from_wire(
        decode_json(json.dumps(payload).encode(), _TaskRunWire), issue_id="issue-1"
    )
    agent_task = decode_json(json.dumps([payload]).encode(), list[AgentTask])[0]
    expected = TaskCancellationActor(type="future_actor", id="actor-1", name="System")
    assert issue_run.cancelled_by == expected
    assert agent_task.cancelled_by == expected


@pytest.mark.parametrize(
    "payload",
    (
        {"id": "task-1", "status": "cancelled", "issue_id": "issue-1"},
        {
            "id": "task-1",
            "status": "cancelled",
            "issue_id": "issue-1",
            "cancelled_by": {"type": "system"},
        },
        {
            "id": "task-1",
            "status": "cancelled",
            "issue_id": "issue-1",
            "cancelled_by": {"type": "future_actor", "name": "Future"},
        },
    ),
    ids=("legacy-omitted", "current", "future"),
)
def test_task_cancellation_actor_decodes_on_both_task_paths(payload: dict[str, object]) -> None:
    issue_run = _task_run_from_wire(
        decode_json(json.dumps(payload).encode(), _TaskRunWire), issue_id="issue-1"
    )
    agent_task = decode_json(json.dumps([payload]).encode(), list[AgentTask])[0]
    assert issue_run.cancelled_by == agent_task.cancelled_by


@pytest.mark.parametrize(
    "payload",
    (
        {"id": "task-1", "status": "cancelled", "issue_id": "issue-1", "cancelled_by": None},
        {"id": "task-1", "status": "cancelled", "issue_id": "issue-1", "cancelled_by": {}},
        {
            "id": "task-1",
            "status": "cancelled",
            "issue_id": "issue-1",
            "cancelled_by": {"type": ""},
        },
        {
            "id": "task-1",
            "status": "cancelled",
            "issue_id": "issue-1",
            "cancelled_by": {"type": "system", "id": 1},
        },
    ),
    ids=("null", "missing-type", "blank-type", "wrong-id"),
)
def test_task_cancellation_actor_malformed_on_both_task_paths(
    payload: dict[str, object],
) -> None:
    with pytest.raises(OutputShapeError):
        _task_run_from_wire(
            decode_json(json.dumps(payload).encode(), _TaskRunWire), issue_id="issue-1"
        )
    with pytest.raises(OutputShapeError):
        decode_json(json.dumps([payload]).encode(), list[AgentTask])


def test_task_run_from_dict_rejects_explicit_null_actor() -> None:
    with pytest.raises((OutputShapeError, msgspec.ValidationError)):
        TaskRun.from_dict({"id": "t", "status": "cancelled", "cancelled_by": None})


@pytest.mark.parametrize(
    "payload",
    (
        {"id": "task-1", "status": "cancelled", "cancelled_by": None},
        {"id": "task-1", "status": "cancelled", "cancelled_by": {}},
        {
            "id": "task-1",
            "status": "cancelled",
            "cancelled_by": {"type": "system", "id": 1},
        },
    ),
    ids=("null", "missing-type", "wrong-optional-type"),
)
def test_task_cancellation_actor_malformed_shapes_fail_closed(payload: dict[str, object]) -> None:
    with pytest.raises(OutputShapeError):
        _task_run_from_wire(
            decode_json(json.dumps(payload).encode(), _TaskRunWire), issue_id="issue-1"
        )


@pytest.mark.parametrize("value", (None, False, True), ids=("legacy", "complete", "truncated"))
def test_run_message_output_truncated_is_tri_state(value: bool | None) -> None:
    payload: dict[str, object] = {"task_id": "task-1", "seq": 1, "type": "tool_result"}
    if value is not None:
        payload["output_truncated"] = value
    message = decode_run_messages(json.dumps([payload]).encode(), "issue run-messages")[0]
    assert message.output_truncated is value


def test_run_message_preserves_timestamp_and_rejects_null_truncation() -> None:
    payload = {
        "task_id": "task-1",
        "seq": 1,
        "type": "text",
        "created_at": "2026-09-12T12:34:56.123456Z",
    }
    message = decode_run_messages(json.dumps([payload]).encode(), "issue run-messages")[0]
    assert message.created_at == datetime.datetime(
        2026, 9, 12, 12, 34, 56, 123456, tzinfo=datetime.UTC
    )
    with pytest.raises(OutputShapeError):
        decode_run_messages(
            b'[{"task_id":"task-1","seq":1,"type":"text","output_truncated":null}]',
            "issue run-messages",
        )


def test_issue_usage_counts_preserve_large_integers_independently() -> None:
    usage = decode_json(
        b'{"task_count":2,"terminal_task_count":9007199254740993,'
        b'"metered_task_count":0,"unreported_task_count":7}',
        IssueUsage,
    )
    assert (usage.task_count, usage.terminal_task_count) == (2, 9007199254740993)
    assert (usage.metered_task_count, usage.unreported_task_count) == (0, 7)


@pytest.mark.parametrize(
    "field",
    ("terminal_task_count", "metered_task_count", "unreported_task_count"),
)
@pytest.mark.parametrize("value", (-1, True, 1.5, "1", None))
def test_issue_usage_counts_reject_invalid_values(field: str, value: object) -> None:
    payload = json.dumps({field: value}).encode()
    with pytest.raises(OutputShapeError):
        decode_json(payload, IssueUsage)


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
