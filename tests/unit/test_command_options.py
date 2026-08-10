from __future__ import annotations

import datetime
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from multica_py._internal.commands import _Step
from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig, OperationOptions
from multica_py.enums import AutopilotExecutionMode, IssueStatus, MetadataValueType
from multica_py.models.relations import LazyCollection, OffsetLazyCollection, OffsetPage
from multica_py.resources._base import BaseResource
from multica_py.resources.agent_skills import AgentSkillResource
from multica_py.resources.agents import AgentResource
from multica_py.resources.attachments import AttachmentResource
from multica_py.resources.auth import AuthResource
from multica_py.resources.autopilots import AutopilotResource
from multica_py.resources.configuration import ConfigurationResource
from multica_py.resources.daemon import DaemonResource
from multica_py.resources.issue_comments import IssueCommentResource
from multica_py.resources.issue_labels import IssueLabelResource
from multica_py.resources.issue_metadata import IssueMetadataResource
from multica_py.resources.issue_subscribers import IssueSubscriberResource
from multica_py.resources.issues import Issue, IssueResource
from multica_py.resources.labels import LabelResource
from multica_py.resources.maintenance import MaintenanceResource
from multica_py.resources.project_resources import ProjectResourceCollection
from multica_py.resources.projects import ProjectResource
from multica_py.resources.repositories import RepositoryResource
from multica_py.resources.runtimes import RuntimeResource
from multica_py.resources.setup import SetupResource
from multica_py.resources.skill_files import SkillFileResource
from multica_py.resources.skills import SkillResource
from multica_py.resources.squad_members import SquadMemberResource
from multica_py.resources.squads import SquadResource
from multica_py.resources.users import UserResource
from multica_py.resources.workspaces import WorkspaceResource


def test_plan_snapshots_precedence_and_transport_once() -> None:
    base = ClientConfig(
        profile="base",
        workspace_id="base-ws",
        timeout=datetime.timedelta(seconds=10),
        environment=(("BASE", "1"),),
    )
    transport = CliTransport(base)
    resource = BaseResource(transport, base)
    options = OperationOptions(
        profile="operation",
        workspace_id="operation-ws",
        timeout=5,
        environment={"OPERATION": "1"},
    )
    command = resource._raw_command(("issue", "get", "i1"), options=options)

    assert command._plan.config_snapshot == ClientConfig(
        profile="operation",
        workspace_id="operation-ws",
        timeout=datetime.timedelta(seconds=5),
        environment=(("OPERATION", "1"),),
    )
    assert command._plan.transport is not transport
    assert command._plan.transport._config is command._plan.config_snapshot
    assert command._plan.transport._semaphore is transport._semaphore
    assert command.commands == (
        "multica --workspace-id operation-ws --profile operation issue get i1",
    )


def test_plan_snapshot_is_stable_for_preview_and_execution(
    raw_result: Callable[..., RawCommandResult],
) -> None:
    config = ClientConfig(profile="base", workspace_id="base-ws")
    transport = CliTransport(config)
    resource = BaseResource(transport, config)
    transport.run_bytes = MagicMock(return_value=raw_result(argv=("multica", "issue", "get", "i1")))  # type: ignore[method-assign]
    command = resource._raw_command(
        ("issue", "get", "i1"),
        options=OperationOptions(profile="operation"),
    )
    expected = command.commands

    later = resource._raw_command(
        ("issue", "get", "i1"),
        options=OperationOptions(profile="later"),
    )

    assert command.commands == expected
    command.run()
    assert command.commands == expected
    assert later.commands == ("multica --workspace-id base-ws --profile later issue get i1",)


def test_explicit_clears_apply_without_mutating_scoped_client() -> None:
    client = MulticaClient(
        ClientConfig(
            profile="base",
            workspace_id="base-ws",
            timeout=datetime.timedelta(seconds=10),
            cwd=Path("base"),
            environment=(("BASE", "1"),),
        )
    )
    try:
        scoped = client.with_options(
            profile="scoped",
            workspace_id="scoped-ws",
            timeout=20,
            cwd="scoped",
            environment={"SCOPED": "1"},
        )
        try:
            command = scoped.issues._raw_command(
                ("issue", "list"),
                options=OperationOptions(
                    profile=None,
                    workspace_id=None,
                    timeout=None,
                    cwd=None,
                    environment=(),
                ),
            )
            assert command._plan.config_snapshot == ClientConfig()
            assert client.config.profile == "base"
            assert scoped.config.profile == "scoped"
            assert scoped._semaphore is client._semaphore
        finally:
            scoped._transport.close()
    finally:
        client._transport.close()


def test_composite_steps_retain_one_snapshot_and_semaphore() -> None:
    config = ClientConfig(profile="base")
    transport = CliTransport(config)
    resource = BaseResource(transport, config)
    command = resource._plan(
        steps=(
            _Step(("first",), "run_bytes"),
            _Step(("second",), "run_bytes"),
        ),
        finalize=lambda results: results,
        options=OperationOptions(profile="scoped"),
    )

    assert command._plan.transport._config.profile == "scoped"
    assert command._plan.transport._semaphore is transport._semaphore
    assert command._plan.steps[0].argv == ("first",)
    assert command._plan.steps[1].argv == ("second",)


def test_mapped_and_cached_commands_retain_one_effective_snapshot() -> None:
    config = ClientConfig(profile="base")
    transport = CliTransport(config)
    resource = BaseResource(transport, config)
    command = resource._plan(
        steps=(_Step(("first",), "run_bytes"),),
        finalize=lambda results: cast("str", results[0]),
        options=OperationOptions(profile="scoped"),
    )
    mapped = command._map(lambda value: f"mapped:{value}")
    relation = LazyCollection(
        lambda: ("loaded",),
        initial=("loaded",),
        command_loader=lambda: command._map(lambda _value: ("loaded",)),
    )
    cached = relation.all_command()

    for derived in (mapped, cached):
        assert derived._plan.config_snapshot.profile == "scoped"
        assert derived._plan.transport._config is derived._plan.config_snapshot
        assert derived._plan.transport._semaphore is transport._semaphore
    assert cached._plan.steps == ()
    transport.close()


def test_paginated_continuations_retain_one_effective_snapshot() -> None:
    config = ClientConfig(profile="base")
    transport = CliTransport(config)
    resource = BaseResource(transport, config)
    command = resource._plan(
        steps=(_Step(("items", "--offset", "0"), "run_bytes"),),
        finalize=lambda _results: OffsetPage(
            items=("item",), total=2, limit=1, offset=0, has_more=True
        ),
        options=OperationOptions(profile="scoped"),
    )
    relation = OffsetLazyCollection(
        lambda *, limit, offset: OffsetPage(
            items=(), total=0, limit=limit or 1, offset=offset, has_more=False
        ),
        default_limit=1,
        page_command_loader=lambda _limit, _offset: command,
    )
    paginated = relation.all_command()

    assert paginated._plan.config_snapshot.profile == "scoped"
    assert paginated._plan.transport._config is paginated._plan.config_snapshot
    assert paginated._plan.transport._semaphore is transport._semaphore
    assert len(paginated._plan.steps) == 2
    assert paginated._plan.steps[1].refs
    assert paginated._plan.steps[1].argv[2] == "${page.next_offset}"
    transport.close()


@dataclass(frozen=True)
class OperationOptionsCase:
    resource_cls: type
    method: str
    kwargs: tuple[tuple[str, object], ...]


OPERATION_OPTIONS_CASES = (
    OperationOptionsCase(AgentResource, "create_command", (("name", "agent"),)),
    OperationOptionsCase(AgentResource, "update_command", (("agent_id", "a1"), ("name", "agent"))),
    OperationOptionsCase(
        AutopilotResource,
        "create_command",
        (
            ("title", "auto"),
            ("agent", "a1"),
            ("execution_mode", AutopilotExecutionMode.create_issue),
        ),
    ),
    OperationOptionsCase(
        AutopilotResource, "update_command", (("autopilot_id", "ap1"), ("title", "auto"))
    ),
    OperationOptionsCase(
        AutopilotResource,
        "trigger_add_command",
        (("autopilot_id", "ap1"), ("title", "hook"), ("kind", "manual")),
    ),
    OperationOptionsCase(
        AutopilotResource,
        "trigger_update_command",
        (("autopilot_id", "ap1"), ("trigger_id", "tr1"), ("title", "hook")),
    ),
    OperationOptionsCase(LabelResource, "create_command", (("name", "bug"),)),
    OperationOptionsCase(LabelResource, "update_command", (("label_id", "l1"), ("name", "bug"))),
    OperationOptionsCase(ProjectResource, "create_command", (("name", "project"),)),
    OperationOptionsCase(
        ProjectResource, "update_command", (("project_id", "p1"), ("name", "project"))
    ),
    OperationOptionsCase(
        ProjectResourceCollection,
        "add_local_directory_command",
        (("project_id", "p1"), ("local_path", "/repo"), ("daemon_id", "d1")),
    ),
    OperationOptionsCase(
        ProjectResourceCollection,
        "update_local_directory_command",
        (("project_id", "p1"), ("resource_id", "r1"), ("local_path", "/repo")),
    ),
    OperationOptionsCase(
        RuntimeResource, "update_command", (("runtime_id", "r1"), ("target_version", "1.2"))
    ),
    OperationOptionsCase(SkillResource, "create_command", (("name", "skill"),)),
    OperationOptionsCase(SkillResource, "update_command", (("skill_id", "s1"), ("name", "skill"))),
    OperationOptionsCase(UserResource, "profile_update_command", (("description", "profile"),)),
    OperationOptionsCase(AgentSkillResource, "list_command", (("agent_id", "a1"),)),
    OperationOptionsCase(
        AgentSkillResource, "set_command", (("agent_id", "a1"), ("skill_ids", ("s1",)))
    ),
    OperationOptionsCase(AttachmentResource, "upload_command", (("source", Path("file.txt")),)),
    OperationOptionsCase(
        AttachmentResource, "upload_bytes_command", (("filename", "file.txt"), ("payload", b"x"))
    ),
    OperationOptionsCase(
        AttachmentResource,
        "download_command",
        (("attachment_id", "att1"), ("output_dir", Path("."))),
    ),
    OperationOptionsCase(
        AttachmentResource, "download_bytes_command", (("attachment_id", "att1"),)
    ),
    OperationOptionsCase(AuthResource, "login_command", (("token", "token"),)),
    OperationOptionsCase(AuthResource, "logout_command", ()),
    OperationOptionsCase(
        ConfigurationResource, "set_command", (("key", "key"), ("value", "value"))
    ),
    OperationOptionsCase(DaemonResource, "start_command", ()),
    OperationOptionsCase(DaemonResource, "logs_command", (("follow", True),)),
    OperationOptionsCase(MaintenanceResource, "update_command", ()),
    OperationOptionsCase(
        RepositoryResource, "add_command", (("urls", ("https://example.test/repo",)),)
    ),
    OperationOptionsCase(SetupResource, "self_host_command", (("url", "https://example.test"),)),
    OperationOptionsCase(
        SkillFileResource,
        "upsert_command",
        (("skill_id", "s1"), ("path", "README.md"), ("content", "x")),
    ),
    OperationOptionsCase(
        SquadMemberResource, "add_command", (("squad_id", "sq1"), ("member_id", "m1"))
    ),
    OperationOptionsCase(SquadResource, "get_command", (("squad_id", "sq1"),)),
    OperationOptionsCase(WorkspaceResource, "switch_command", (("workspace_id", "ws1"),)),
    OperationOptionsCase(IssueResource, "list_command", ()),
    OperationOptionsCase(IssueResource, "get_command", (("issue_id", "i1"),)),
    OperationOptionsCase(IssueResource, "create_command", (("title", "issue"),)),
    OperationOptionsCase(IssueResource, "update_command", (("issue_id", "i1"), ("title", "issue"))),
    OperationOptionsCase(IssueResource, "assign_command", (("issue_id", "i1"), ("assignee", "m1"))),
    OperationOptionsCase(
        IssueResource, "set_status_command", (("issue_id", "i1"), ("status", IssueStatus.todo))
    ),
    OperationOptionsCase(IssueResource, "deprioritize_command", (("issue_id", "i1"),)),
    OperationOptionsCase(IssueResource, "reorder_command", (("issue_id", "i1"), ("top", True))),
    OperationOptionsCase(IssueResource, "search_command", (("query", "needle"),)),
    OperationOptionsCase(IssueResource, "pull_requests_command", (("issue_id", "i1"),)),
    OperationOptionsCase(IssueResource, "children_command", (("issue_id", "i1"),)),
    OperationOptionsCase(IssueResource, "runs_command", (("issue_id", "i1"),)),
    OperationOptionsCase(IssueResource, "run_messages_command", (("task_run_id", "run1"),)),
    OperationOptionsCase(IssueResource, "usage_command", (("issue_id", "i1"),)),
    OperationOptionsCase(IssueResource, "rerun_command", (("issue_id", "i1"),)),
    OperationOptionsCase(IssueResource, "cancel_task_command", (("task_id", "run1"),)),
    OperationOptionsCase(IssueCommentResource, "list_command", (("issue_id", "i1"),)),
    OperationOptionsCase(IssueCommentResource, "list_flat_command", (("issue_id", "i1"),)),
    OperationOptionsCase(
        IssueCommentResource, "list_thread_command", (("issue_id", "i1"), ("thread_id", "t1"))
    ),
    OperationOptionsCase(IssueCommentResource, "list_recent_command", (("issue_id", "i1"),)),
    OperationOptionsCase(
        IssueCommentResource, "add_command", (("issue_id", "i1"), ("body", "body"))
    ),
    OperationOptionsCase(
        IssueCommentResource,
        "reply_command",
        (("issue_id", "i1"), ("thread_id", "t1"), ("body", "body")),
    ),
    OperationOptionsCase(IssueCommentResource, "delete_command", (("comment_id", "c1"),)),
    OperationOptionsCase(IssueCommentResource, "resolve_command", (("thread_id", "t1"),)),
    OperationOptionsCase(IssueCommentResource, "unresolve_command", (("thread_id", "t1"),)),
    OperationOptionsCase(IssueLabelResource, "list_command", (("issue_id", "i1"),)),
    OperationOptionsCase(
        IssueLabelResource, "add_command", (("issue_id", "i1"), ("label_id", "l1"))
    ),
    OperationOptionsCase(
        IssueLabelResource, "remove_command", (("issue_id", "i1"), ("label_id", "l1"))
    ),
    OperationOptionsCase(IssueMetadataResource, "list_command", (("issue_id", "i1"),)),
    OperationOptionsCase(IssueMetadataResource, "query_command", (("issue_id", "i1"),)),
    OperationOptionsCase(IssueMetadataResource, "get_command", (("issue_id", "i1"), ("key", "k"))),
    OperationOptionsCase(
        IssueMetadataResource, "set_command", (("issue_id", "i1"), ("key", "k"), ("value", "v"))
    ),
    OperationOptionsCase(
        IssueMetadataResource,
        "set_typed_command",
        (
            ("issue_id", "i1"),
            ("key", "k"),
            ("value", "v"),
            ("value_type", MetadataValueType.string),
        ),
    ),
    OperationOptionsCase(
        IssueMetadataResource, "delete_command", (("issue_id", "i1"), ("key", "k"))
    ),
    OperationOptionsCase(IssueSubscriberResource, "list_command", (("issue_id", "i1"),)),
    OperationOptionsCase(
        IssueSubscriberResource, "add_command", (("issue_id", "i1"), ("user_id", "u1"))
    ),
    OperationOptionsCase(
        IssueSubscriberResource, "remove_command", (("issue_id", "i1"), ("user_id", "u1"))
    ),
)


@pytest.mark.parametrize("case", OPERATION_OPTIONS_CASES, ids=lambda case: case.method)
def test_public_options_are_planning_only(case: OperationOptionsCase) -> None:
    config = ClientConfig(profile="base")
    transport = CliTransport(config)
    resource = case.resource_cls(transport, config)
    kwargs = dict(case.kwargs)
    plain = getattr(resource, case.method)(**kwargs)
    scoped = getattr(resource, case.method)(**kwargs, options=OperationOptions(profile="operation"))

    assert scoped._plan.steps[0].argv == plain._plan.steps[0].argv
    assert "operation" not in scoped._plan.steps[0].argv
    assert scoped._plan.config_snapshot.profile == "operation"
    assert scoped._plan.transport._semaphore is transport._semaphore
    transport.close()


def test_bound_issue_options_forward_without_changing_relation_origin() -> None:
    client = MulticaClient(ClientConfig(profile="base"))
    issue = Issue(id="i1", title="Issue", status=IssueStatus.todo, _client=client)
    try:
        action = issue.add_label_command("l1", options=OperationOptions(profile="operation"))
        relation = issue.comments.all_command()

        assert action._plan.steps[0].argv == (
            "issue",
            "label",
            "add",
            "i1",
            "l1",
            "--output",
            "json",
        )
        assert action._plan.config_snapshot.profile == "operation"
        assert relation._plan.config_snapshot.profile == "base"
        assert action._plan.transport._semaphore is client._semaphore
        assert relation._plan.transport._semaphore is client._semaphore
    finally:
        client._transport.close()
