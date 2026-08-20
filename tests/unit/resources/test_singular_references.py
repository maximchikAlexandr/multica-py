from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast, get_type_hints
from unittest.mock import MagicMock

import pytest

from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.entities._base import _BoundEntity
from multica_py.entities.agents import Agent
from multica_py.entities.autopilots import Autopilot, AutopilotRun
from multica_py.entities.issues import Issue, TaskRun
from multica_py.entities.projects import Project
from multica_py.entities.squads import Squad
from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.models.issues import IssueAssignee
from multica_py.models.relations import LazyRef


@dataclass(frozen=True)
class GovernedReferenceCase:
    name: str
    owner: type[object]
    relation: str
    source: Callable[[MulticaClient], _BoundEntity]
    service: str
    target_id: str
    target_type: type[object]
    annotation: object
    expected_argv: tuple[str, ...]
    scalar_field: str
    scalar_value: object


def _issue_parent(client: MulticaClient) -> Issue:
    return Issue(
        id="issue-1", title="Issue", status=IssueStatus.todo, parent_id="parent-1", _client=client
    )


def _issue_project(client: MulticaClient) -> Issue:
    return Issue(
        id="issue-1", title="Issue", status=IssueStatus.todo, project_id="project-1", _client=client
    )


def _issue_assignee(client: MulticaClient) -> Issue:
    return Issue(
        id="issue-1",
        title="Issue",
        status=IssueStatus.todo,
        assignee=IssueAssignee(id="agent-1", name="Agent", type="agent"),
        _client=client,
    )


def _autopilot(client: MulticaClient, *, project_id: str | None = None) -> Autopilot:
    return Autopilot(
        id="autopilot-1",
        workspace_id="workspace-1",
        title="Autopilot",
        project_id=project_id,
        assignee_type="agent",
        assignee_id="agent-1",
        status="active",
        execution_mode="manual",
        created_by_type="member",
        created_by_id="member-1",
        _client=client,
    )


def _autopilot_project(client: MulticaClient) -> Autopilot:
    return _autopilot(client, project_id="project-1")


def _autopilot_assignee(client: MulticaClient) -> Autopilot:
    return _autopilot(client)


def _autopilot_run(client: MulticaClient, *, issue_id: str | None = None) -> AutopilotRun:
    return AutopilotRun(
        id="run-1",
        autopilot_id="autopilot-1",
        source="manual",
        status="completed",
        issue_id=issue_id,
        _client=client,
    )


def _autopilot_run_autopilot(client: MulticaClient) -> AutopilotRun:
    return _autopilot_run(client, issue_id=None)


def _autopilot_run_issue(client: MulticaClient) -> AutopilotRun:
    return _autopilot_run(client, issue_id="issue-1")


def _task_run_issue(client: MulticaClient) -> TaskRun:
    return TaskRun(id="task-1", status="completed", issue_id="issue-1", _client=client)


def _task_run_agent(client: MulticaClient) -> TaskRun:
    return TaskRun(
        id="task-1", status="completed", agent_id="agent-1", issue_id="issue-1", _client=client
    )


GOVERNED_REFERENCE_CASES = (
    GovernedReferenceCase(
        "Issue.parent",
        Issue,
        "parent",
        _issue_parent,
        "issues",
        "parent-1",
        Issue,
        LazyRef[Issue | None],
        ("multica", "issue", "get", "parent-1", "--output", "json"),
        "parent_id",
        "parent-1",
    ),
    GovernedReferenceCase(
        "Issue.project",
        Issue,
        "project",
        _issue_project,
        "projects",
        "project-1",
        Project,
        LazyRef[Project | None],
        ("multica", "project", "get", "project-1", "--output", "json"),
        "project_id",
        "project-1",
    ),
    GovernedReferenceCase(
        "Issue.assignee_ref",
        Issue,
        "assignee_ref",
        _issue_assignee,
        "agents",
        "agent-1",
        Agent,
        LazyRef[Agent | Squad | None],
        ("multica", "agent", "get", "agent-1", "--output", "json"),
        "assignee",
        IssueAssignee(id="agent-1", name="Agent", type="agent"),
    ),
    GovernedReferenceCase(
        "Autopilot.project",
        Autopilot,
        "project",
        _autopilot_project,
        "projects",
        "project-1",
        Project,
        LazyRef[Project | None],
        ("multica", "project", "get", "project-1", "--output", "json"),
        "project_id",
        "project-1",
    ),
    GovernedReferenceCase(
        "Autopilot.assignee",
        Autopilot,
        "assignee",
        _autopilot_assignee,
        "agents",
        "agent-1",
        Agent,
        LazyRef[Agent | Squad],
        ("multica", "agent", "get", "agent-1", "--output", "json"),
        "assignee_id",
        "agent-1",
    ),
    GovernedReferenceCase(
        "AutopilotRun.autopilot",
        AutopilotRun,
        "autopilot",
        _autopilot_run_autopilot,
        "autopilots",
        "autopilot-1",
        Autopilot,
        LazyRef[Autopilot],
        ("multica", "autopilot", "get", "autopilot-1", "--output", "json"),
        "autopilot_id",
        "autopilot-1",
    ),
    GovernedReferenceCase(
        "AutopilotRun.issue",
        AutopilotRun,
        "issue",
        _autopilot_run_issue,
        "issues",
        "issue-1",
        Issue,
        LazyRef[Issue | None],
        ("multica", "issue", "get", "issue-1", "--output", "json"),
        "issue_id",
        "issue-1",
    ),
    GovernedReferenceCase(
        "TaskRun.issue",
        TaskRun,
        "issue",
        _task_run_issue,
        "issues",
        "issue-1",
        Issue,
        LazyRef[Issue],
        ("multica", "issue", "get", "issue-1", "--output", "json"),
        "issue_id",
        "issue-1",
    ),
    GovernedReferenceCase(
        "TaskRun.agent",
        TaskRun,
        "agent",
        _task_run_agent,
        "agents",
        "agent-1",
        Agent,
        LazyRef[Agent | None],
        ("multica", "agent", "get", "agent-1", "--output", "json"),
        "agent_id",
        "agent-1",
    ),
)


def _client_with_command_transport() -> tuple[MulticaClient, MagicMock]:
    client = MulticaClient(ClientConfig())
    transport = MagicMock(spec=CliTransport)
    transport._snapshot.side_effect = lambda _config: transport
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    client._transport = transport
    for resource_name in (
        "issues",
        "projects",
        "agents",
        "squads",
        "autopilots",
    ):
        getattr(client, resource_name)._transport = transport
    return client, transport


def _target(case: GovernedReferenceCase, client: MulticaClient) -> _BoundEntity:
    if case.target_type is Issue:
        return Issue(id=case.target_id, title="Target", status=IssueStatus.todo, _client=client)
    if case.target_type is Project:
        return Project(
            id=case.target_id, name="Target", status=ProjectStatus.planned, _client=client
        )
    if case.target_type is Agent:
        return Agent(id=case.target_id, name="Target", _client=client)
    if case.target_type is Squad:
        return Squad(id=case.target_id, name="Target", _client=client)
    return Autopilot(
        id=case.target_id,
        workspace_id="workspace-1",
        title="Target",
        assignee_type="agent",
        assignee_id="agent-1",
        status="active",
        execution_mode="manual",
        created_by_type="member",
        created_by_id="member-1",
        _client=client,
    )


@pytest.mark.parametrize("case", GOVERNED_REFERENCE_CASES, ids=lambda case: case.name)
def test_governed_dispatch_inventory_is_typed_passive_and_bound(
    case: GovernedReferenceCase,
) -> None:
    client, transport = _client_with_command_transport()
    try:
        source = case.source(client)
        descriptor = cast("property", inspect.getattr_static(case.owner, case.relation))
        annotation = get_type_hints(cast("Callable[..., object]", descriptor.fget))["return"]
        assert annotation == case.annotation

        reference = cast("LazyRef[object]", getattr(source, case.relation))
        assert reference.loaded is False
        assert getattr(source, case.scalar_field) == case.scalar_value
        assert transport.run_bytes.call_count == 0
        assert reference.get_command().commands == (" ".join(case.expected_argv),)
        assert transport.run_bytes.call_count == 0

        target = _target(case, client)
        service = getattr(client, case.service)
        service.get_command = MagicMock(
            return_value=client.issues._plan(steps=(), finalize=lambda _results: target)
        )
        loaded = reference.get()
        assert type(loaded) is case.target_type
        assert cast("_BoundEntity", loaded)._client is client
        cast("MagicMock", service.get_command).assert_called_once_with(case.target_id)
    finally:
        client.close()


def test_assignee_squad_dispatch_is_governed() -> None:
    client, transport = _client_with_command_transport()
    try:
        issue = Issue(
            id="issue-1",
            title="Issue",
            status=IssueStatus.todo,
            assignee=IssueAssignee(id="squad-1", name="Squad", type="squad"),
            _client=client,
        )
        reference = issue.assignee_ref
        assert reference.get_command().commands == ("multica squad get squad-1 --output json",)
        assert transport.run_bytes.call_count == 0
    finally:
        client.close()
