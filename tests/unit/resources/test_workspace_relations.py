from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import get_type_hints
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus
from multica_py.exceptions import DetachedEntityError
from multica_py.models.issues import IssueListPage, IssueSummary
from multica_py.models.relations import OffsetLazyCollection
from multica_py.resources.agents import Agent
from multica_py.resources.projects import Project
from multica_py.resources.squads import Squad
from multica_py.resources.workspaces import (
    Workspace,
    WorkspaceMember,
    WorkspaceResource,
)
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
        issues=(IssueSummary(id="i1", title="Issue", status=_TODO),),
        has_more=False,
        limit=50,
        offset=0,
        total=1,
    )
    resource = WorkspaceResource(transport, ClientConfig())
    resource._set_client(client)

    members = resource.members("ws_1")
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
    issue: IssueSummary = IssueSummary(
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
        issues=(
            IssueSummary(id="i1", title="t1", status=_TODO),
            IssueSummary(id="i2", title="t2", status=_TODO),
        ),
        has_more=True,
        limit=2,
        offset=0,
        total=3,
    )
    p2 = IssueListPage(
        issues=(IssueSummary(id="i3", title="t3", status=_TODO),),
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
    assert all(isinstance(item, IssueSummary) for item in items)
    first_filter = clients.scoped.issues.list.call_args_list[0].args[0]
    second_filter = clients.scoped.issues.list.call_args_list[1].args[0]
    assert first_filter.limit == 50
    assert first_filter.offset == 0
    assert second_filter.limit == 50
    assert second_filter.offset == 2
    clients.scoped.issues.get.assert_not_called()


def test_workspace_issues_single_page() -> None:
    page = IssueListPage(
        issues=(IssueSummary(id="i1", title="t1", status=_TODO),),
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
    assert isinstance(items[0], IssueSummary)
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
def test_issue_relations_are_typed_as_summary_collections(case: IssueRelationTypeCase) -> None:
    relation = getattr(case.owner, case.relation_name)
    assert get_type_hints(relation.fget)["return"] == OffsetLazyCollection[IssueSummary]


def test_workspace_detached_access_raises() -> None:
    entity: Workspace = Workspace(id="ws_1", name="Test WS")
    with pytest.raises(DetachedEntityError):
        entity.members.all()
    with pytest.raises(DetachedEntityError):
        entity.issues.all()
