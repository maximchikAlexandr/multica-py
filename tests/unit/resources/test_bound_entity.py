from __future__ import annotations

import datetime
import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import cast, get_type_hints
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.commands import _Step
from multica_py._internal.json_values import _coerce_json_value
from multica_py._internal.specs import TextResult
from multica_py.config import ClientConfig
from multica_py.entities._base import _BoundEntity, _entity_policy
from multica_py.entities.agents import Agent
from multica_py.entities.autopilots import Autopilot, AutopilotRun
from multica_py.entities.comments import Comment, CommentThread
from multica_py.entities.issues import Issue, TaskRun
from multica_py.entities.labels import Label
from multica_py.entities.projects import Project
from multica_py.entities.skills import Skill
from multica_py.entities.squads import Squad
from multica_py.entities.workspaces import Workspace, WorkspaceMember
from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.exceptions import DetachedEntityError
from multica_py.models.agents import AgentSkill
from multica_py.models.autopilots import AutopilotSubscriber, AutopilotTrigger
from multica_py.models.common import Page
from multica_py.models.issues import (
    IssueAssignee,
    IssueChildStageGroup,
    IssueMetadataItem,
    LinkedPullRequest,
)
from multica_py.models.relations import CursorPage
from multica_py.models.system import AttachmentResult
from multica_py.resources._base import BaseResource
from multica_py.types import JsonValue

_BOUND_ENTITY_CASES: tuple[_BoundEntity, ...] = (
    Issue(
        id="issue-1",
        title="Title",
        status=IssueStatus.in_progress,
        description="Description",
        priority="high",
        assignee=IssueAssignee(id="agent-1", name="Agent", type="agent"),
        child_stages=(IssueChildStageGroup(name="stage", count=2),),
        label_names=("bug",),
        metadata_snapshot=(IssueMetadataItem(key="severity", value="high"),),
        attachments=(AttachmentResult(id="attachment-1", filename="report.txt"),),
        pull_request_snapshot=(LinkedPullRequest(url="https://example.test/pr/1", title="Fix"),),
        created_at=datetime.datetime(2026, 8, 5, 12, 0, tzinfo=datetime.UTC),
        updated_at=datetime.datetime(2026, 8, 5, 12, 1, tzinfo=datetime.UTC),
        parent_id="parent-1",
        project_id="project-1",
        creator_id="member-1",
        creator_type="member",
    ),
    Project(
        id="project-1", name="Project", description="Description", status=ProjectStatus.planned
    ),
    Agent(
        id="agent-1",
        name="Agent",
        description="Description",
        skill_refs=(AgentSkill(id="skill-1", name="Skill", enabled=True),),
        archived_at=datetime.datetime(2026, 8, 5, tzinfo=datetime.UTC),
    ),
    Skill(id="skill-1", name="Skill", description="Description", file_count=3),
    Autopilot(
        id="autopilot-1",
        workspace_id="workspace-1",
        title="Autopilot",
        description="Description",
        project_id="project-1",
        assignee_type="agent",
        assignee_id="agent-1",
        status="active",
        execution_mode="manual",
        issue_title_template="{{title}}",
        created_by_type="member",
        created_by_id="member-1",
        last_run_at=datetime.datetime(2026, 8, 5, 12, 0, tzinfo=datetime.UTC),
        created_at=datetime.datetime(2026, 8, 5, 12, 0, tzinfo=datetime.UTC),
        updated_at=datetime.datetime(2026, 8, 5, 12, 1, tzinfo=datetime.UTC),
        trigger_kinds=("webhook",),
        next_run_at=datetime.datetime(2026, 8, 6, tzinfo=datetime.UTC),
        last_run_status="completed",
        subscriber_snapshot=(AutopilotSubscriber(user_type="member", user_id="member-1"),),
        can_write=True,
        can_manage_access=False,
    ),
    AutopilotRun(
        id="run-1",
        autopilot_id="autopilot-1",
        trigger_id="trigger-1",
        source="webhook",
        status="completed",
        issue_id="issue-1",
        task_id="task-1",
        triggered_at=datetime.datetime(2026, 8, 5, 12, 0, tzinfo=datetime.UTC),
        completed_at=datetime.datetime(2026, 8, 5, 12, 1, tzinfo=datetime.UTC),
        failure_reason=None,
        reason_code="ok",
        trigger_payload={"event": "push", "commits": (("id", "abc"),)},
        result={"ok": True, "summary": ("done",)},
        created_at=datetime.datetime(2026, 8, 5, 12, 0, tzinfo=datetime.UTC),
    ),
    Squad(
        id="squad-1",
        name="Squad",
        member_count=2,
        leader_id="agent-1",
        archived_at=datetime.datetime(2026, 8, 5, tzinfo=datetime.UTC),
    ),
    WorkspaceMember(
        id="member-1", name="Member", role="owner", user_id="user-1", email="member@example.test"
    ),
    Workspace(id="workspace-1", name="Workspace", description="Description"),
    Comment(
        id="comment-1",
        body="Comment",
        thread_id="thread-1",
        author_id="member-1",
        created_at=datetime.datetime(2026, 8, 5, 12, 0, tzinfo=datetime.UTC),
        updated_at=datetime.datetime(2026, 8, 5, 12, 1, tzinfo=datetime.UTC),
    ),
    CommentThread(
        id="thread-1",
        resolved=True,
        updated_at=datetime.datetime(2026, 8, 5, 12, 1, tzinfo=datetime.UTC),
    ),
    TaskRun(
        id="task-1",
        status="completed",
        agent_id="agent-1",
        started_at=datetime.datetime(2026, 8, 5, 12, 0, tzinfo=datetime.UTC),
        completed_at=datetime.datetime(2026, 8, 5, 12, 1, tzinfo=datetime.UTC),
    ),
    Label(id="label-1", name="bug", color="#ff0000"),
)


_BOUND_ENTITY_IDS = tuple(type(entity).__name__ for entity in _BOUND_ENTITY_CASES)


@dataclass(frozen=True)
class EntityPolicyCase:
    entity_type: type[_BoundEntity]
    public_fields: tuple[str, ...]
    private_fields: tuple[str, ...]
    constructor_seeds: tuple[str, ...]
    encoded_aliases: tuple[tuple[str, str], ...]
    runtime_overlays: tuple[str, ...]


_ENTITY_POLICY_CASES: tuple[EntityPolicyCase, ...] = (
    EntityPolicyCase(
        Issue,
        (
            "id",
            "title",
            "status",
            "description",
            "priority",
            "assignee",
            "child_stages",
            "label_names",
            "metadata_snapshot",
            "attachments",
            "pull_request_snapshot",
            "created_at",
            "updated_at",
            "parent_id",
            "project_id",
            "creator_id",
            "creator_type",
            "match_source",
        ),
        (
            "_assignee_ref",
            "_children",
            "_client",
            "_comments",
            "_labels",
            "_metadata",
            "_parent",
            "_project",
            "_properties",
            "_pull_requests",
            "_recent_threads",
            "_runs",
            "_subscribers",
            "_wire_presence",
        ),
        (),
        (),
        (),
    ),
    EntityPolicyCase(
        Project,
        ("id", "name", "status", "description"),
        ("_client", "_issues", "_resources"),
        (),
        (),
        (),
    ),
    EntityPolicyCase(
        Agent,
        ("id", "name", "description", "skill_refs", "archived_at"),
        ("_client", "_issues", "_mcp_servers", "_skills", "_tasks"),
        (),
        (("skill_refs", "skills"),),
        (),
    ),
    EntityPolicyCase(
        Skill,
        ("id", "name", "description", "file_count"),
        ("_client", "_files"),
        (),
        (),
        (),
    ),
    EntityPolicyCase(
        Autopilot,
        (
            "id",
            "workspace_id",
            "title",
            "assignee_type",
            "assignee_id",
            "status",
            "execution_mode",
            "created_by_type",
            "created_by_id",
            "description",
            "project_id",
            "issue_title_template",
            "last_run_at",
            "created_at",
            "updated_at",
            "trigger_kinds",
            "next_run_at",
            "last_run_status",
            "subscriber_snapshot",
            "can_write",
            "can_manage_access",
        ),
        (
            "_assignee_ref",
            "_client",
            "_project",
            "_runs",
            "_subscribers",
            "_triggers",
            "_wire_presence",
        ),
        ("triggers", "subscribers"),
        (
            ("subscriber_snapshot", "subscribers"),
            ("triggers", "_triggers_seed"),
            ("subscribers", "_subscribers_seed"),
        ),
        (),
    ),
    EntityPolicyCase(
        AutopilotRun,
        (
            "id",
            "autopilot_id",
            "source",
            "status",
            "trigger_id",
            "issue_id",
            "task_id",
            "triggered_at",
            "completed_at",
            "failure_reason",
            "reason_code",
            "trigger_payload",
            "result",
            "created_at",
        ),
        ("_autopilot", "_client", "_issue", "_messages", "_wire_presence"),
        (),
        (),
        ("result", "trigger_payload"),
    ),
    EntityPolicyCase(
        Squad,
        ("id", "name", "member_count", "leader_id", "archived_at"),
        ("_client", "_issues", "_members"),
        (),
        (),
        (),
    ),
    EntityPolicyCase(
        WorkspaceMember,
        ("id", "name", "role", "user_id", "email"),
        ("_client", "_issues"),
        (),
        (),
        (),
    ),
    EntityPolicyCase(
        Workspace,
        ("id", "name", "description"),
        (
            "_agents",
            "_autopilots",
            "_client",
            "_issues",
            "_labels",
            "_mcp_servers",
            "_members",
            "_plugins",
            "_projects",
            "_properties",
            "_repositories",
            "_runtimes",
            "_skills",
            "_squads",
        ),
        (),
        (),
        (),
    ),
    EntityPolicyCase(
        Comment,
        ("id", "body", "thread_id", "author_id", "created_at", "updated_at"),
        ("_client",),
        (),
        (),
        (),
    ),
    EntityPolicyCase(
        CommentThread,
        ("id", "resolved", "updated_at"),
        ("_client", "_comments"),
        ("issue_id",),
        (("issue_id", "_issue_id"),),
        (),
    ),
    EntityPolicyCase(
        TaskRun,
        (
            "id",
            "status",
            "agent_id",
            "runtime_id",
            "workspace_id",
            "started_at",
            "completed_at",
            "dispatched_at",
            "created_at",
            "work_dir",
            "relative_work_dir",
            "durable_work_dir",
            "relative_durable_work_dir",
            "branch_name",
            "result",
            "error",
            "failure_reason",
        ),
        ("_agent", "_client", "_issue", "_messages", "_wire_presence"),
        ("issue_id",),
        (("issue_id", "_issue_id"),),
        ("result",),
    ),
    EntityPolicyCase(
        Label,
        ("id", "name", "color"),
        ("_client",),
        (),
        (),
        (),
    ),
)

_ENTITY_POLICY_IDS = tuple(case.entity_type.__name__ for case in _ENTITY_POLICY_CASES)


@dataclass(frozen=True)
class BoundComparisonCase:
    name: str
    first: _BoundEntity
    second: _BoundEntity
    expected_equal: bool


_BOUND_COMPARISON_CASES: tuple[BoundComparisonCase, ...] = (
    BoundComparisonCase(
        name="same-public-fields",
        first=Issue(id="i1", title="A", status=IssueStatus.todo),
        second=Issue(id="i1", title="A", status=IssueStatus.todo),
        expected_equal=True,
    ),
    BoundComparisonCase(
        name="different-clients",
        first=Issue(id="i1", title="A", status=IssueStatus.todo, _client=MagicMock()),
        second=Issue(id="i1", title="A", status=IssueStatus.todo, _client=MagicMock()),
        expected_equal=True,
    ),
    BoundComparisonCase(
        name="different-public-fields",
        first=Issue(id="i1", title="A", status=IssueStatus.todo),
        second=Issue(id="i2", title="A", status=IssueStatus.todo),
        expected_equal=False,
    ),
    BoundComparisonCase(
        name="json-object-payload",
        first=AutopilotRun(
            id="run-1",
            autopilot_id="autopilot-1",
            source="webhook",
            status="completed",
            trigger_payload={"event": "push", "meta": {"attempt": 1}},
            result={"items": ("one", "two")},
        ),
        second=AutopilotRun(
            id="run-1",
            autopilot_id="autopilot-1",
            source="webhook",
            status="completed",
            trigger_payload={"meta": {"attempt": 1}, "event": "push"},
            result={"items": ("one", "two")},
        ),
        expected_equal=True,
    ),
    BoundComparisonCase(
        name="json-array-payload",
        first=AutopilotRun(
            id="run-1",
            autopilot_id="autopilot-1",
            source="webhook",
            status="completed",
            trigger_payload=({"step": 1}, {"step": 2}),
        ),
        second=AutopilotRun(
            id="run-1",
            autopilot_id="autopilot-1",
            source="webhook",
            status="completed",
            trigger_payload=({"step": 1}, {"step": 2}),
        ),
        expected_equal=True,
    ),
)


@pytest.mark.parametrize("case", _ENTITY_POLICY_CASES, ids=_ENTITY_POLICY_IDS)
def test_entity_policy_is_a_closed_schema_characterization(case: EntityPolicyCase) -> None:
    policy = _entity_policy(case.entity_type)

    assert policy is _entity_policy(case.entity_type)
    assert policy.public_fields == case.public_fields
    assert tuple(sorted(policy.private_fields)) == case.private_fields
    assert policy.constructor_seeds == case.constructor_seeds
    assert (
        tuple((name, encoded) for name, encoded in policy.encoded_names if name != encoded)
        == case.encoded_aliases
    )
    assert tuple(sorted(policy.runtime_overlays)) == case.runtime_overlays


@pytest.mark.parametrize("entity", _BOUND_ENTITY_CASES, ids=_BOUND_ENTITY_IDS)
def test_public_fields_match_declared_msgspec_fields(entity: _BoundEntity) -> None:
    policy = _entity_policy(type(entity))
    declared = tuple(
        field.name
        for field in msgspec.structs.fields(type(entity))
        if field.name in policy.public_fields
    )
    assert declared == policy.public_fields


@pytest.mark.parametrize("entity", _BOUND_ENTITY_CASES, ids=_BOUND_ENTITY_IDS)
def test_every_bound_entity_round_trips_all_public_fields(entity: _BoundEntity) -> None:
    restored = type(entity).from_json(entity.to_json())

    assert restored == entity.detach()
    snapshot = restored.to_dict()
    assert tuple(snapshot) == _entity_policy(type(entity)).public_fields
    assert all(not field.startswith("_") for field in snapshot)


@pytest.mark.parametrize("case", _BOUND_COMPARISON_CASES, ids=lambda case: case.name)
def test_bound_entity_comparisons_are_structural(case: BoundComparisonCase) -> None:
    assert (case.first == case.second) is case.expected_equal
    if case.expected_equal:
        assert hash(case.first) == hash(case.second)


@pytest.mark.compat
def test_runtime_state_cannot_shadow_public_surface() -> None:
    client = MagicMock()
    issue = Issue(id="i1", title="A", status=IssueStatus.todo, _client=client)
    relation = issue.comments

    assert not hasattr(issue, "__dict__")
    with pytest.raises(AttributeError):
        object.__getattribute__(issue, "__dict__")
    assert not hasattr(type(issue), "_PUBLIC_FIELDS")

    rebound = issue._with_client(MagicMock())
    assert _entity_policy(type(rebound)) is _entity_policy(type(issue))
    assert rebound.comments is relation


def test_autopilot_run_constructor_takes_json_snapshot() -> None:
    payload: dict[str, object] = {"nested": ["before"]}
    result: dict[str, object] = {"items": [1]}
    run = AutopilotRun(
        id="run-1",
        autopilot_id="autopilot-1",
        source="manual",
        status="completed",
        trigger_payload=cast("JsonValue", payload),
        result=cast("JsonValue", result),
    )

    payload["nested"] = ["after"]
    result["items"] = [2]

    assert run.trigger_payload == {"nested": ("before",)}
    assert run.result == {"items": (1,)}


def test_autopilot_run_json_snapshot_is_recursively_immutable() -> None:
    run = AutopilotRun(
        id="run-1",
        autopilot_id="autopilot-1",
        source="manual",
        status="completed",
        trigger_payload={"nested": {"value": 1}},
        result={"nested": {"value": 1}},
    )
    before = hash(run)
    for payload_value in (run.trigger_payload, run.result):
        payload = cast("Mapping[str, JsonValue]", payload_value)
        with pytest.raises((TypeError, AttributeError)):
            object.__setattr__(payload, "new", True)
        with pytest.raises(TypeError):
            dict.__setitem__(cast("dict[str, object]", payload), "new", True)
        nested = cast("Mapping[str, JsonValue]", payload["nested"])
        with pytest.raises((TypeError, AttributeError)):
            object.__setattr__(nested, "value", 2)
        with pytest.raises(TypeError):
            dict.__setitem__(cast("dict[str, object]", nested), "value", 2)

    assert hash(run) == before


def test_autopilot_run_wide_json_object_uses_constant_lookup_snapshot() -> None:
    values = {f"key-{index}": index for index in range(4096)}
    run = AutopilotRun(
        id="run-1",
        autopilot_id="autopilot-1",
        source="manual",
        status="completed",
        trigger_payload=values,
    )

    snapshot = run.trigger_payload
    assert isinstance(snapshot, MappingProxyType)
    assert len(snapshot) == len(values)
    assert snapshot["key-4095"] == 4095
    serialized = run.to_dict()["trigger_payload"]
    assert isinstance(serialized, dict)
    assert serialized["key-4095"] == 4095

    normalized = _coerce_json_value(snapshot, field_name="trigger_payload")
    assert normalized == snapshot
    assert normalized is not snapshot


def test_autopilot_run_mapping_proxy_input_is_recursively_snapshotted() -> None:
    nested_backing: dict[str, object] = {"role": "user"}
    backing: dict[str, object] = {"nested": nested_backing, "count": 1}
    proxy = MappingProxyType(backing)
    run = AutopilotRun(
        id="run-1",
        autopilot_id="autopilot-1",
        source="manual",
        status="completed",
        trigger_payload=cast("JsonValue", proxy),
    )
    before_hash = hash(run)
    seen = {run}

    nested_backing["role"] = "admin"
    backing["count"] = 2
    backing["new"] = True

    assert run.trigger_payload == {"nested": {"role": "user"}, "count": 1}
    assert hash(run) == before_hash
    assert run in seen
    assert run.trigger_payload is not proxy


@pytest.mark.parametrize("field_name", ("trigger_payload", "result"))
def test_autopilot_run_overlays_roundtrip_nested_mutables_and_value_operations(
    field_name: str,
) -> None:
    payload: dict[str, object] = {"nested": [{"values": [1, 2]}]}
    if field_name == "trigger_payload":
        run = AutopilotRun(
            id="run-1",
            autopilot_id="auto-1",
            source="manual",
            status="completed",
            trigger_payload=cast("JsonValue", payload),
        )
    else:
        run = AutopilotRun(
            id="run-1",
            autopilot_id="auto-1",
            source="manual",
            status="completed",
            result=cast("JsonValue", payload),
        )

    payload["nested"] = [{"values": [99]}]
    restored = AutopilotRun.from_json(run.to_json())

    assert getattr(run, field_name) == {"nested": ({"values": (1, 2)},)}
    assert getattr(restored, field_name) == getattr(run, field_name)
    assert hash(restored) == hash(run)
    assert repr(restored) == repr(run)


def test_set_runtime_accepts_only_schema_private_fields_and_overlays() -> None:
    issue = Issue(id="i1", title="A", status=IssueStatus.todo)
    marker = object()

    issue._set_runtime("_comments", marker)
    assert issue._comments is marker
    with pytest.raises(AttributeError, match="unsupported runtime field"):
        issue._set_runtime("not_declared", marker)

    run = AutopilotRun(id="run-1", autopilot_id="auto-1", source="manual", status="completed")
    run._set_runtime("result", {"ok": True})
    assert run.result == {"ok": True}


def test_runtime_overlay_policy_rejects_adversarial_subclass_extensions() -> None:
    class AdversarialRun(AutopilotRun):  # type: ignore[misc]
        _PUBLIC_RUNTIME_OVERLAYS = ("unapproved",)

    assert _entity_policy(AdversarialRun).runtime_overlays == frozenset()
    run = AdversarialRun(
        id="run-1",
        autopilot_id="auto-1",
        source="manual",
        status="completed",
    )
    with pytest.raises(AttributeError, match="unsupported runtime field: unapproved"):
        run._set_runtime("unapproved", object())


@pytest.mark.parametrize(
    "value",
    (
        MappingProxyType({"value": math.nan}),
        MappingProxyType({"nested": [math.inf]}),
        MappingProxyType({"nested": {"value": -math.inf}}),
        MappingProxyType({1: "non-string key"}),
    ),
    ids=("nan", "nested-inf", "nested-negative-inf", "non-string-key"),
)
def test_autopilot_run_mapping_proxy_rejects_invalid_json(value: object) -> None:
    with pytest.raises(msgspec.ValidationError):
        AutopilotRun(
            id="run-1",
            autopilot_id="autopilot-1",
            source="manual",
            status="completed",
            trigger_payload=cast("JsonValue", value),
        )


class TestBoundEntitySerialization:
    @pytest.mark.parametrize("serializer", ("to_json", "to_dict"))
    def test_serializers_exclude_client_and_cache(self, serializer: str) -> None:
        issue = Issue(id="i1", title="A", status=IssueStatus.todo, _client=MagicMock())
        serialized = getattr(issue, serializer)()
        assert "_client" not in serialized
        assert "_comments" not in serialized
        assert "_labels" not in serialized

    def test_public_autopilot_run_annotations_remain_closed(self) -> None:
        assert AutopilotRun.__annotations__["trigger_payload"] == "JsonValue | None"
        assert AutopilotRun.__annotations__["result"] == "JsonValue | None"
        assert "object" not in str(get_type_hints(AutopilotRun)["trigger_payload"])

    def test_roundtrip_restores_typed_public_fields(self) -> None:
        issue = Issue(
            id="i1",
            title="A",
            status=IssueStatus.todo,
            assignee=IssueAssignee(id="agent-1", name="Agent"),
            label_names=("bug",),
            metadata_snapshot=(IssueMetadataItem(key="severity", value="high"),),
            created_at=datetime.datetime(2026, 8, 5, tzinfo=datetime.UTC),
        )

        restored = Issue.from_json(issue.to_json())

        assert restored == issue.detach()
        assert restored.status is IssueStatus.todo
        assert isinstance(restored.created_at, datetime.datetime)
        assert type(restored.label_names) is tuple
        assert isinstance(restored.assignee, IssueAssignee)
        assert type(restored.metadata_snapshot) is tuple
        assert isinstance(restored.metadata_snapshot[0], IssueMetadataItem)

    @pytest.mark.parametrize("private_name", ("_client", "_comments", "_recent_threads"))
    def test_from_dict_rejects_private_runtime_state(self, private_name: str) -> None:
        data: dict[str, object] = {
            "id": "i1",
            "title": "A",
            "status": "todo",
            private_name: {},
        }

        with pytest.raises(ValueError, match=private_name):
            Issue.from_dict(data)

    def test_from_dict_rejects_malformed_public_values(self) -> None:
        with pytest.raises(msgspec.ValidationError):
            Issue.from_dict({"id": "i1", "title": "A", "status": 42})

    def test_autopilot_run_deserialization_is_recursive_and_strict(self) -> None:
        fields: dict[str, object] = {
            "id": "run-1",
            "autopilot_id": "autopilot-1",
            "source": "webhook",
            "status": "completed",
            "trigger_payload": {"event": ["push"], "meta": {"attempt": 1}},
            "result": [{"ok": True}],
        }

        run = AutopilotRun.from_dict(fields)

        assert run.trigger_payload == {"event": ("push",), "meta": {"attempt": 1}}
        assert run.result == ({"ok": True},)
        with pytest.raises(msgspec.ValidationError, match="JSON values"):
            AutopilotRun.from_dict({**fields, "result": object()})

    @pytest.mark.parametrize(
        ("field_name", "value"),
        (
            ("trigger_payload", math.nan),
            ("trigger_payload", {"nested": [math.inf]}),
            ("result", -math.inf),
            ("result", {"nested": {"value": math.nan}}),
        ),
    )
    def test_autopilot_run_rejects_nonfinite_json_values(
        self, field_name: str, value: object
    ) -> None:
        fields: dict[str, object] = {
            "id": "run-1",
            "autopilot_id": "autopilot-1",
            "source": "webhook",
            "status": "completed",
            field_name: value,
        }

        with pytest.raises(msgspec.ValidationError, match="finite JSON numbers"):
            AutopilotRun.from_dict(fields)

    def test_comment_thread_issue_context_is_init_only(self) -> None:
        thread = CommentThread(id="thread-1", issue_id="issue-1")

        assert thread.issue_id == "issue-1"
        assert thread.to_dict() == {"id": "thread-1", "resolved": False, "updated_at": None}
        assert "issue_id" not in thread.to_json()

    def test_bound_comment_thread_uses_init_issue_context(self) -> None:
        client = MagicMock()
        transport = MagicMock()
        transport.run_text.return_value = TextResult(text="", stderr="", exit_code=0)
        command_resource = BaseResource(transport, ClientConfig())
        client.issues.comments.list_thread.return_value = Page(
            items=(Comment(id="comment-1", body="body"),),
            next_cursor=None,
        )
        client.issues.comments.list_thread_command = lambda **request: command_resource._plan(
            steps=(),
            finalize=lambda _results: CursorPage(
                items=client.issues.comments.list_thread(**request).items,
                next_cursor=None,
            ),
        )
        client.issues.comments._thread_page_command = lambda **request: command_resource._plan(
            steps=(
                _Step(
                    (
                        "issue",
                        "comment",
                        "list",
                        "thread",
                        request["issue_id"],
                        request["thread_id"],
                        "--limit",
                        str(request["limit"]),
                        "--output",
                        "json",
                    ),
                    "run_text",
                    decode=lambda _stdout, _command: CursorPage(
                        items=client.issues.comments.list_thread(**request).items,
                        next_cursor=None,
                    ),
                ),
            ),
            finalize=lambda results: results[0],
        )
        thread = CommentThread(id="thread-1", issue_id="issue-1", _client=client)

        assert thread.comments.all() == (Comment(id="comment-1", body="body"),)
        request = client.issues.comments.list_thread.call_args.kwargs
        assert (request["issue_id"], request["thread_id"]) == ("issue-1", "thread-1")

    def test_to_dict_returns_independent_nested_mutables(self) -> None:
        run = AutopilotRun(
            id="run-1",
            autopilot_id="auto-1",
            source="manual",
            status="completed",
            trigger_payload={"nested": {"items": {"member": "user"}}},
        )

        snapshot = run.to_dict()
        trigger_payload = snapshot["trigger_payload"]
        assert isinstance(trigger_payload, dict)
        nested = trigger_payload["nested"]
        assert isinstance(nested, dict)
        items = nested["items"]
        assert isinstance(items, dict)
        items["member"] = "admin"

        assert run.trigger_payload == {"nested": {"items": {"member": "user"}}}


class TestBoundEntityDetach:
    def test_detach_resets_issue_relation_caches(self) -> None:
        client = MagicMock()
        issue = Issue(id="i1", title="A", status=IssueStatus.todo, _client=client)
        _ = issue.comments
        _ = issue.recent_comment_threads()

        detached = issue.detach()

        assert detached._client is None
        assert detached._comments is None
        assert detached._recent_threads == {}
        with pytest.raises(DetachedEntityError):
            detached.comments.all()
        with pytest.raises(DetachedEntityError):
            detached.recent_comment_threads()
        client.issues.comments.list_flat.assert_not_called()
        client.issues.comments.list_recent.assert_not_called()

    def test_detach_resets_seeded_autopilot_relations(self) -> None:
        client = MagicMock()
        autopilot = Autopilot(
            id="auto-1",
            workspace_id="ws-1",
            title="A",
            assignee_type="agent",
            assignee_id="agent-1",
            status="active",
            execution_mode="manual",
            created_by_type="agent",
            created_by_id="agent-1",
            _client=client,
            triggers=(AutopilotTrigger(id="trigger-1", type="schedule"),),
            subscribers=(AutopilotSubscriber(user_type="member", user_id="member-1"),),
        )
        assert autopilot.triggers.loaded
        assert autopilot.subscribers.loaded

        detached = autopilot.detach()

        assert detached._client is None
        assert detached._triggers is None
        assert detached._subscribers is None
        assert object.__getattribute__(detached, "triggers") is msgspec.UNSET
        assert object.__getattribute__(detached, "subscribers") is msgspec.UNSET
        with pytest.raises(DetachedEntityError):
            detached.triggers.all()
        with pytest.raises(DetachedEntityError):
            detached.subscribers.all()
        client.autopilots.get.assert_not_called()


class TestBoundEntityRepr:
    def test_repr_excludes_client(self) -> None:
        issue = Issue(id="i1", title="A", status=IssueStatus.todo, _client=MagicMock())
        r = repr(issue)
        assert "_client" not in r
        assert r.startswith("Issue(")
        assert "id=" in r
        assert "title=" in r
