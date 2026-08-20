from __future__ import annotations

import datetime
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast, get_type_hints
from unittest.mock import MagicMock

import pytest

from multica_py._internal.commands import Command, _Step
from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.entities.agents import Agent
from multica_py.entities.issues import Issue
from multica_py.entities.projects import Project
from multica_py.entities.squads import Squad
from multica_py.entities.workspaces import Workspace, WorkspaceMember
from multica_py.enums import IssueStatus
from multica_py.exceptions import DetachedEntityError
from multica_py.models.common import ActionResult, Page
from multica_py.models.issues import (
    IssueListFilter,
    IssueListPage,
)
from multica_py.models.relations import LazyCollection, OffsetLazyCollection
from multica_py.models.workspaces import McpServer
from multica_py.resources._base import BaseResource
from multica_py.resources.projects import ProjectIssueCollection
from multica_py.resources.workspaces import WorkspaceResource
from tests.unit.resources.workspace_cases import (
    make_workspace_clients,
    workspace_relation_method,
)

_TODO = IssueStatus("todo")


@dataclass(frozen=True)
class WorkspaceUnpagedCase:
    relation_name: str
    expected_args: tuple[str, ...] = ()


_UNPAGED_RELATION_CASES = (
    WorkspaceUnpagedCase("members", ("ws_1",)),
    WorkspaceUnpagedCase("agents"),
    WorkspaceUnpagedCase("skills"),
    WorkspaceUnpagedCase("projects"),
    WorkspaceUnpagedCase("labels"),
    WorkspaceUnpagedCase("repositories"),
    WorkspaceUnpagedCase("runtimes"),
    WorkspaceUnpagedCase("squads"),
    WorkspaceUnpagedCase("autopilots"),
    WorkspaceUnpagedCase("plugins"),
    WorkspaceUnpagedCase("properties"),
    WorkspaceUnpagedCase("mcp_servers"),
)


@dataclass(frozen=True)
class WorkspaceMcpMutationCase:
    method: str
    invoke: Callable[[Workspace], Command[Page[McpServer]]]


def _add_mcp_server_command(workspace: Workspace) -> Command[Page[McpServer]]:
    return workspace.add_mcp_server_command("server", server_config="{}")


def _update_mcp_server_command(workspace: Workspace) -> Command[Page[McpServer]]:
    return workspace.update_mcp_server_command("mcp_1", name="renamed")


WORKSPACE_MCP_MUTATION_CASES = (
    WorkspaceMcpMutationCase("add_mcp_server", _add_mcp_server_command),
    WorkspaceMcpMutationCase("update_mcp_server", _update_mcp_server_command),
)


@dataclass(frozen=True)
class WorkspaceMemberIdentityDefaultCase:
    name: str
    value: WorkspaceMember


WORKSPACE_MEMBER_IDENTITY_DEFAULT_CASES = (
    WorkspaceMemberIdentityDefaultCase(
        "wire model",
        WorkspaceMember(id="membership-1", name="Member"),
    ),
)


@pytest.mark.parametrize(
    "case", WORKSPACE_MEMBER_IDENTITY_DEFAULT_CASES, ids=lambda case: case.name
)
def test_workspace_member_identity_defaults_to_none(
    case: WorkspaceMemberIdentityDefaultCase,
) -> None:
    assert case.value.user_id is None
    assert case.value.email is None


@pytest.mark.parametrize("case", _UNPAGED_RELATION_CASES, ids=lambda case: case.relation_name)
def test_workspace_unpaged_relation_is_lazy_and_cached(case: WorkspaceUnpagedCase) -> None:
    clients = make_workspace_clients()
    entity = Workspace(id="ws_1", name="Test WS", _client=clients.origin)
    relation = getattr(entity, case.relation_name)
    method = workspace_relation_method(clients.scoped, case.relation_name)

    assert method.call_count == 0
    items = relation.all()
    assert isinstance(items, tuple)
    relation.all()
    assert method.call_count == 1
    clients.origin.with_workspace.assert_called_once_with("ws_1")
    method.assert_called_once_with(*case.expected_args)


@pytest.mark.parametrize("case", WORKSPACE_MCP_MUTATION_CASES, ids=lambda case: case.method)
def test_workspace_mcp_mutation_command_invalidates_loaded_relation(
    case: WorkspaceMcpMutationCase,
) -> None:
    origin = MagicMock()
    scoped = MagicMock()
    origin.with_workspace.return_value = scoped
    resource = BaseResource(MagicMock(spec=CliTransport), ClientConfig())
    result: Page[McpServer] = Page(items=())
    command = resource._plan(steps=(), finalize=lambda _results: result)
    mcp_method = getattr(
        scoped.workspaces.mcp, f"{case.method.removesuffix('_mcp_server')}_command"
    )
    mcp_method.return_value = command
    setattr(
        scoped.workspaces,
        f"_{case.method}_command",
        lambda *args, invalidate, options, **kwargs: mcp_method(
            *args, options=options, **kwargs
        )._map(invalidate),
    )
    entity = Workspace(id="ws_1", name="Test WS", _client=origin)
    entity._set_runtime("_mcp_servers", LazyCollection(lambda: ()))
    assert entity.mcp_servers.all() == ()

    bound_command = case.invoke(entity)

    assert bound_command.run() is result
    assert not entity.mcp_servers.loaded
    origin.with_workspace.assert_called_once_with("ws_1")


def test_workspace_mcp_remove_command_invalidates_loaded_relation() -> None:
    origin = MagicMock()
    scoped = MagicMock()
    origin.with_workspace.return_value = scoped
    resource = BaseResource(MagicMock(spec=CliTransport), ClientConfig())
    result = ActionResult[None](value=None)
    scoped.workspaces.mcp.remove_command.return_value = resource._plan(
        steps=(), finalize=lambda _results: result
    )
    scoped.workspaces._remove_mcp_server_command = lambda server_id, *, invalidate, options: (
        scoped.workspaces.mcp.remove_command(server_id, options=options)._map(invalidate)
    )
    entity = Workspace(id="ws_1", name="Test WS", _client=origin)
    entity._set_runtime("_mcp_servers", LazyCollection(lambda: ()))
    assert entity.mcp_servers.all() == ()

    assert entity.remove_mcp_server_command("mcp_1").run() is result

    assert not entity.mcp_servers.loaded


def test_workspace_mcp_remove_failure_preserves_loaded_relation() -> None:
    origin = MagicMock()
    scoped = MagicMock()
    origin.with_workspace.return_value = scoped
    resource = BaseResource(MagicMock(spec=CliTransport), ClientConfig())
    result = ActionResult[None](success=False, value=None)
    scoped.workspaces.mcp.remove_command.return_value = resource._plan(
        steps=(), finalize=lambda _results: result
    )
    scoped.workspaces._remove_mcp_server_command = lambda server_id, *, invalidate, options: (
        scoped.workspaces.mcp.remove_command(server_id, options=options)._map(invalidate)
    )
    entity = Workspace(id="ws_1", name="Test WS", _client=origin)
    entity._set_runtime("_mcp_servers", LazyCollection(lambda: ()))
    assert entity.mcp_servers.all() == ()

    assert entity.remove_mcp_server_command("mcp_1").run() is result

    assert entity.mcp_servers.loaded


def test_workspace_members_loader_preserves_bound_items() -> None:
    clients = make_workspace_clients()
    member = WorkspaceMember(id="m1", name="Member", _client=clients.scoped)
    clients.scoped.workspaces.members.return_value = (member,)
    entity = Workspace(id="ws_1", name="Test WS", _client=clients.origin)

    items = entity.members.all()

    assert clients.origin is not clients.scoped
    clients.origin.with_workspace.assert_called_once_with("ws_1")
    clients.scoped.workspaces.members.assert_called_once_with("ws_1")
    clients.origin.workspaces.members.assert_not_called()
    assert items[0] is member
    assert items[0]._client is clients.scoped


def test_workspace_members_preserve_user_identity() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.return_value = RawCommandResult(
        argv=("workspace", "member", "list", "ws_1", "--output", "json"),
        exit_code=0,
        stdout=(
            b'[{"id":"membership-1","name":"Member","role":"admin",'
            b'"user_id":"user-1","email":"member@example.test"}]'
        ),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    client = MagicMock()
    client.issues.list.return_value = IssueListPage(
        items=(Issue(id="i1", title="Issue", status=_TODO),),
        has_more=False,
        limit=50,
        offset=0,
        total=1,
    )
    command_resource = BaseResource(MagicMock(spec=CliTransport), ClientConfig())

    def list_command(issue_filter: IssueListFilter) -> Command[object]:
        def decode(_stdout: bytes, command_text: str) -> object:
            words = command_text.split()
            offset = int(words[words.index("--offset") + 1])
            limit = int(words[words.index("--limit") + 1])
            return client.issues.list(
                IssueListFilter(
                    assignee_id=issue_filter.assignee_id,
                    limit=limit,
                    offset=offset,
                )
            )

        transport = command_resource._transport
        cast("MagicMock", transport.run_bytes).side_effect = lambda argv, **_kwargs: (
            RawCommandResult(
                argv=argv,
                exit_code=0,
                stdout=b"",
                stderr=b"",
                duration=datetime.timedelta(),
            )
        )
        args = (
            "issue",
            "list",
            "--limit",
            str(issue_filter.limit),
            "--offset",
            str(issue_filter.offset),
            "--output",
            "json",
        )
        return command_resource._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: results[0],
        )

    client.issues.list_command = list_command
    client.issues._offset_page_command = list_command
    client.issues._offset_page = lambda issue_filter: list_command(issue_filter).run()
    resource = WorkspaceResource(transport, ClientConfig())
    resource._set_client(client)
    client.workspaces._issues_page = resource._issues_page
    client.workspaces._issues_page_command = resource._issues_page_command

    members = resource.members_command("ws_1").run()
    member = members[0]
    items = member.issues.all()

    assert member.id == "membership-1"
    assert member.user_id == "user-1"
    assert member.email == "member@example.test"
    assert len(items) == 1
    issue_filter = client.issues.list.call_args.args[0]
    assert issue_filter.assignee_id == "membership-1"
    assert issue_filter.assignee_id != member.user_id
    client.users.list.assert_not_called()
    transport.run_bytes.assert_called_once_with(
        ("workspace", "member", "list", "ws_1", "--output", "json"),
        stdin=None,
        timeout=None,
    )


def test_workspace_member_creator_reconciliation_is_typed() -> None:
    issue: Issue = Issue(
        id="i1",
        title="Issue",
        status=_TODO,
        creator_id="user-1",
    )
    members: tuple[WorkspaceMember, ...] = (
        WorkspaceMember(
            id="membership-1",
            name="Member",
            role="admin",
            user_id="user-1",
            email="member@example.test",
        ),
    )

    email = next(member.email for member in members if member.user_id == issue.creator_id)

    assert email == "member@example.test"


def test_workspace_issues_paginates_offset() -> None:
    p1 = IssueListPage(
        items=cast(
            "tuple[Issue, ...]",
            (
                Issue(id="i1", title="t1", status=_TODO),
                Issue(id="i2", title="t2", status=_TODO),
            ),
        ),
        has_more=True,
        limit=2,
        offset=0,
        total=3,
    )
    p2 = IssueListPage(
        items=(Issue(id="i3", title="t3", status=_TODO),),
        has_more=False,
        limit=2,
        offset=2,
        total=3,
    )
    clients = make_workspace_clients(issues=[p1, p2])
    entity = Workspace(id="ws_1", name="Test WS", _client=clients.origin)
    items = entity.issues.all()
    assert len(items) == 3
    assert clients.scoped.issues.list.call_count == 2
    assert all(isinstance(item, Issue) for item in items)
    first_filter = clients.scoped.issues.list.call_args_list[0].args[0]
    second_filter = clients.scoped.issues.list.call_args_list[1].args[0]
    assert first_filter.limit == 50
    assert first_filter.offset == 0
    assert second_filter.limit == 50
    assert second_filter.offset == 2
    clients.scoped.issues.get.assert_not_called()


def test_workspace_issues_single_page() -> None:
    page = IssueListPage(
        items=(Issue(id="i1", title="t1", status=_TODO),),
        has_more=False,
        limit=50,
        offset=0,
        total=1,
    )
    clients = make_workspace_clients(issues=[page, page])
    entity = Workspace(id="ws_1", name="Test WS", _client=clients.origin)
    items = entity.issues.all()
    assert len(items) == 1
    assert clients.scoped.issues.list.call_count == 1
    assert isinstance(items[0], Issue)
    clients.scoped.issues.get.assert_not_called()
    entity.issues.refresh()
    assert clients.scoped.issues.list.call_count == 2
    clients.scoped.issues.get.assert_not_called()


@dataclass(frozen=True)
class IssueRelationTypeCase:
    owner: type[object]
    relation_name: str


ISSUE_RELATION_TYPE_CASES = (
    IssueRelationTypeCase(Workspace, "issues"),
    IssueRelationTypeCase(Project, "issues"),
    IssueRelationTypeCase(Agent, "issues"),
    IssueRelationTypeCase(Squad, "issues"),
    IssueRelationTypeCase(WorkspaceMember, "issues"),
)


@pytest.mark.parametrize("case", ISSUE_RELATION_TYPE_CASES, ids=lambda case: case.owner.__name__)
def test_issue_relations_are_typed_as_bound_issue_collections(case: IssueRelationTypeCase) -> None:
    relation = getattr(case.owner, case.relation_name)
    expected = ProjectIssueCollection if case.owner is Project else OffsetLazyCollection[Issue]
    assert get_type_hints(relation.fget)["return"] == expected


def test_workspace_detached_access_raises() -> None:
    entity: Workspace = Workspace(id="ws_1", name="Test WS")
    with pytest.raises(DetachedEntityError):
        entity.members.all()
    with pytest.raises(DetachedEntityError):
        entity.issues.all()


def test_workspace_issue_and_autopilot_relation_commands_preserve_plan_metadata() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.side_effect = (
        RawCommandResult(
            argv=(
                "issue",
                "list",
                "--limit",
                "50",
                "--offset",
                "0",
                "--output",
                "json",
            ),
            exit_code=0,
            stdout=(
                b'{"issues":[{"id":"i1","title":"Issue","status":"todo"}],'
                b'"has_more":false,"limit":50,"offset":0,"total":1}'
            ),
            stderr=b"",
            duration=datetime.timedelta(),
        ),
        RawCommandResult(
            argv=("autopilot", "list", "--output", "json"),
            exit_code=0,
            stdout=b'{"autopilots":[],"total":7}',
            stderr=b"",
            duration=datetime.timedelta(),
        ),
    )
    scoped = MulticaClient(ClientConfig(workspace_id="ws_1"))
    scoped.issues._transport = transport
    scoped.autopilots._transport = transport
    origin = MagicMock()
    origin.with_workspace.return_value = scoped
    workspace = Workspace(id="ws_1", name="Workspace", _client=origin)

    issues = workspace.issues.all_command()
    autopilots = workspace.autopilots.all_command()

    assert transport.run_bytes.call_count == 0
    assert issues.commands == (
        "multica issue list --limit 50 --offset 0 --output json",
        "multica issue list --limit 50 --offset '${page.next_offset}' --output json",
    )
    assert autopilots.commands == ("multica autopilot list --output json",)
    assert [item.id for item in issues.run()] == ["i1"]
    assert autopilots.run() == ()
    assert workspace.autopilots.metadata.total == 7
    assert transport.run_bytes.call_count == 2


def test_workspace_member_issue_page_command_preserves_assignee_and_is_lazy() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.return_value = RawCommandResult(
        argv=(
            "issue",
            "list",
            "--assignee-id",
            "membership-1",
            "--limit",
            "50",
            "--offset",
            "0",
            "--output",
            "json",
        ),
        exit_code=0,
        stdout=(
            b'{"issues":[{"id":"i1","title":"Issue","status":"todo"}],'
            b'"has_more":false,"limit":50,"offset":0,"total":1}'
        ),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    client = MulticaClient(ClientConfig())
    client.issues._transport = transport
    member = WorkspaceMember(id="membership-1", name="Member", _client=client)

    command = member.issues.page_command()

    assert transport.run_bytes.call_count == 0
    assert command.commands == (
        "multica issue list --assignee-id membership-1 --offset 0 --output json",
    )
    assert command.run().items[0].id == "i1"


NORMATIVE_RELATION_MEMBERS: frozenset[str] = frozenset(
    {
        "Workspace.members",
        "Workspace.agents",
        "Workspace.skills",
        "Workspace.projects",
        "Workspace.issues",
        "Workspace.labels",
        "Workspace.autopilots",
        "Workspace.repositories",
        "Workspace.runtimes",
        "Workspace.squads",
        "Workspace.plugins",
        "Workspace.properties",
        "Workspace.mcp_servers",
        "Agent.skills",
        "Agent.tasks",
        "Agent.issues",
        "Agent.mcp_servers",
        "Skill.files",
        "Squad.members",
        "Squad.issues",
        "WorkspaceMember.issues",
        "Project.resources",
        "Project.issues",
        "Issue.comments",
        "Issue.recent_comment_threads",
        "Issue.labels",
        "Issue.subscribers",
        "Issue.metadata",
        "Issue.pull_requests",
        "Issue.children",
        "Issue.runs",
        "Issue.properties",
        "CommentThread.comments",
        "TaskRun.messages",
        "Autopilot.runs",
        "Autopilot.triggers",
        "Autopilot.subscribers",
        "AutopilotRun.messages",
    }
)


def test_normative_relation_inventory_matches_public_surface() -> None:
    from multica_py.entities.agents import Agent
    from multica_py.entities.autopilots import Autopilot, AutopilotRun
    from multica_py.entities.comments import CommentThread
    from multica_py.entities.issues import Issue, TaskRun
    from multica_py.entities.projects import Project
    from multica_py.entities.skills import Skill
    from multica_py.entities.squads import Squad

    inventory = {
        (Workspace, "members"),
        (Workspace, "agents"),
        (Workspace, "skills"),
        (Workspace, "projects"),
        (Workspace, "issues"),
        (Workspace, "labels"),
        (Workspace, "autopilots"),
        (Workspace, "repositories"),
        (Workspace, "runtimes"),
        (Workspace, "squads"),
        (Workspace, "plugins"),
        (Workspace, "properties"),
        (Workspace, "mcp_servers"),
        (Agent, "skills"),
        (Agent, "tasks"),
        (Agent, "issues"),
        (Agent, "mcp_servers"),
        (Skill, "files"),
        (Squad, "members"),
        (Squad, "issues"),
        (WorkspaceMember, "issues"),
        (Project, "resources"),
        (Project, "issues"),
        (Issue, "comments"),
        (Issue, "labels"),
        (Issue, "subscribers"),
        (Issue, "metadata"),
        (Issue, "pull_requests"),
        (Issue, "children"),
        (Issue, "runs"),
        (Issue, "properties"),
        (CommentThread, "comments"),
        (TaskRun, "messages"),
        (Autopilot, "runs"),
        (Autopilot, "triggers"),
        (Autopilot, "subscribers"),
        (AutopilotRun, "messages"),
    }
    discovered = {f"{owner.__name__}.{member}" for owner, member in inventory}
    discovered.add("Issue.recent_comment_threads")
    assert discovered == NORMATIVE_RELATION_MEMBERS
    assert len(discovered) == 38
    for owner, member in inventory:
        assert hasattr(owner, member)
    assert callable(Issue.recent_comment_threads)
