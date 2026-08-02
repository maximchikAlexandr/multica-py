from __future__ import annotations

from dataclasses import dataclass

import pytest

from multica_py.enums import IssueStatus
from multica_py.exceptions import DetachedEntityError
from multica_py.models.issues import IssueListPage, IssueSummary
from multica_py.models.workspaces import WorkspaceMember
from multica_py.resources.workspaces import WorkspaceEntity
from tests.unit.resources.workspace_cases import (
    make_workspace_clients,
    workspace_data,
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


@pytest.mark.parametrize("case", _UNPAGED_RELATION_CASES, ids=lambda case: case.relation_name)
def test_workspace_unpaged_relation_is_lazy_and_cached(case: WorkspaceUnpagedCase) -> None:
    clients = make_workspace_clients()
    entity = WorkspaceEntity(workspace_data(), client=clients.origin)
    relation = getattr(entity, case.relation_name)
    method = workspace_relation_method(clients.scoped, case.relation_name)

    assert method.call_count == 0
    items = relation.all()
    assert isinstance(items, tuple)
    relation.all()
    assert method.call_count == 1
    clients.origin.with_workspace.assert_called_once_with("ws_1")
    method.assert_called_once_with(*case.expected_args)


def test_workspace_member_is_bound_to_distinct_scoped_client() -> None:
    clients = make_workspace_clients(members=(WorkspaceMember(id="m1", name="Member"),))
    entity = WorkspaceEntity(workspace_data(), client=clients.origin)

    items = entity.members.all()

    assert clients.origin is not clients.scoped
    clients.origin.with_workspace.assert_called_once_with("ws_1")
    clients.scoped.workspaces.members.assert_called_once_with("ws_1")
    clients.origin.workspaces.members.assert_not_called()
    assert items[0]._client is clients.scoped


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
    entity = WorkspaceEntity(workspace_data(), client=clients.origin)
    items = entity.issues.all()
    assert len(items) == 3
    assert clients.scoped.issues.list.call_count == 2
    assert all(item._client is clients.scoped for item in items)


def test_workspace_issues_single_page() -> None:
    page = IssueListPage(
        issues=(IssueSummary(id="i1", title="t1", status=_TODO),),
        has_more=False,
        limit=50,
        offset=0,
        total=1,
    )
    clients = make_workspace_clients(issues=[page])
    entity = WorkspaceEntity(workspace_data(), client=clients.origin)
    items = entity.issues.all()
    assert len(items) == 1
    assert clients.scoped.issues.list.call_count == 1
    assert items[0]._client is clients.scoped


def test_workspace_detached_access_raises() -> None:
    entity: WorkspaceEntity = WorkspaceEntity.from_data(workspace_data())
    with pytest.raises(DetachedEntityError):
        entity.members.all()
    with pytest.raises(DetachedEntityError):
        entity.issues.all()
