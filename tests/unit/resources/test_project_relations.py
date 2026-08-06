from __future__ import annotations

import datetime
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.exceptions import DetachedEntityError
from multica_py.models.issues import IssueListPage, IssueSummary
from multica_py.models.project_resources import (
    ProjectResourceAddLocalDirectoryRequest,
    ProjectResourceRecord,
)
from multica_py.models.projects import ProjectCreateRequest, ProjectUpdateRequest
from multica_py.models.relations import OffsetPage
from multica_py.resources.projects import Project, ProjectResource

_TODO = IssueStatus("todo")
_DONE = IssueStatus("done")

_PLANNED = ProjectStatus("planned")


@dataclass(frozen=True)
class ProjectBindingCase:
    name: str
    method: str
    args: tuple[object, ...]
    stdout: bytes
    expected_argv: tuple[str, ...]


PROJECT_BINDING_CASES = (
    ProjectBindingCase(
        "list",
        "list",
        (),
        b'[{"id":"p1","title":"Project","status":"planned"}]',
        ("project", "list", "--output", "json"),
    ),
    ProjectBindingCase(
        "get",
        "get",
        ("p1",),
        b'{"id":"p1","title":"Project","status":"planned"}',
        ("project", "get", "p1", "--output", "json"),
    ),
    ProjectBindingCase(
        "create",
        "create",
        (ProjectCreateRequest(name="Project"),),
        b'{"id":"p1","title":"Project","status":"planned"}',
        ("project", "create", "--title", "Project", "--output", "json"),
    ),
    ProjectBindingCase(
        "update",
        "update",
        ("p1", ProjectUpdateRequest(name="Renamed")),
        b'{"id":"p1","title":"Renamed","status":"planned"}',
        ("project", "update", "p1", "--title", "Renamed", "--output", "json"),
    ),
    ProjectBindingCase(
        "set status",
        "set_status",
        ("p1", ProjectStatus.completed),
        b'{"id":"p1","title":"Project","status":"completed"}',
        ("project", "status", "p1", "completed", "--output", "json"),
    ),
)


@dataclass(frozen=True)
class ProjectParentMutationCase:
    name: str
    method: str
    args: tuple[object, ...]
    child_method: str
    succeeds: bool


_RESOURCE_RECORD = ProjectResourceRecord(
    id="r1",
    project_id="p1",
    resource_type="local_directory",
    resource_ref=MagicMock(local_path="/tmp", daemon_id="d1", label="main"),
)


PROJECT_PARENT_MUTATION_CASES = (
    ProjectParentMutationCase(
        "add succeeds",
        "add_local_directory",
        (ProjectResourceAddLocalDirectoryRequest(local_path="/tmp", daemon_id="d1"),),
        "add_local_directory",
        True,
    ),
    ProjectParentMutationCase("remove succeeds", "remove_resource", ("r1",), "remove", True),
    ProjectParentMutationCase(
        "add transport failure",
        "add_local_directory",
        (ProjectResourceAddLocalDirectoryRequest(local_path="/tmp", daemon_id="d1"),),
        "add_local_directory",
        False,
    ),
    ProjectParentMutationCase(
        "remove transport failure", "remove_resource", ("r1",), "remove", False
    ),
)


@dataclass(frozen=True)
class ProjectParentValidationCase:
    method: str
    args: tuple[object, ...]
    child_method: str


PROJECT_PARENT_VALIDATION_CASES = (ProjectParentValidationCase("remove_resource", ("",), "remove"),)


def _make_mock_resources(
    project_list_result: tuple[object, ...] = (),
    resource_list_result: tuple[ProjectResourceRecord, ...] = (),
    issue_page_results: list[IssueListPage] | None = None,
) -> MagicMock:
    client = MagicMock()
    client.projects.resources.list.return_value = resource_list_result
    if issue_page_results is not None:
        client.issues.list.side_effect = issue_page_results
    else:
        client.issues.list.return_value = IssueListPage(
            issues=(), has_more=False, limit=50, offset=0, total=0
        )
    return client


@pytest.mark.parametrize("case", PROJECT_BINDING_CASES, ids=lambda case: case.name)
def test_project_resource_returns_bound_immutable_projects(case: ProjectBindingCase) -> None:
    transport = MagicMock()
    transport.run_bytes.return_value = RawCommandResult(
        argv=case.expected_argv,
        exit_code=0,
        stdout=case.stdout,
        stderr=b"",
        duration=datetime.timedelta(),
    )
    resource = ProjectResource(transport, ClientConfig())
    client = MagicMock()
    resource._set_client(client)

    result = getattr(resource, case.method)(*case.args)
    project = result[0] if isinstance(result, tuple) else result

    assert isinstance(project, Project)
    assert project._client is client
    assert client.mock_calls == []
    transport.run_bytes.assert_called_once_with(case.expected_argv, stdin=None, timeout=None)
    transport.run_text.assert_not_called()


def test_project_resources_loads_once() -> None:
    pr = ProjectResourceRecord(
        id="r1",
        project_id="p1",
        resource_type="local_directory",
        resource_ref=MagicMock(local_path="/tmp", daemon_id="d1", label="main"),
    )
    client = _make_mock_resources(resource_list_result=(pr,))
    entity = Project(
        id="p1",
        name="Test",
        status=_PLANNED,
        _client=client,
    )
    result = entity.resources.all()
    assert len(result) == 1
    assert isinstance(result[0], ProjectResourceRecord)
    assert result[0].id == "r1"
    assert client.projects.resources.list.call_count == 1
    client.projects.resources.list.assert_called_once_with("p1")

    # Second .all() uses cache, no new call
    result2 = entity.resources.all()
    assert len(result2) == 1
    assert client.projects.resources.list.call_count == 1


@pytest.mark.parametrize("case", PROJECT_PARENT_MUTATION_CASES, ids=lambda case: case.name)
def test_project_parent_mutations_invalidate_only_resources(
    case: ProjectParentMutationCase,
) -> None:
    page = IssueListPage(issues=(), has_more=False, limit=50, offset=0, total=0)
    client = _make_mock_resources(
        resource_list_result=(_RESOURCE_RECORD,), issue_page_results=[page]
    )
    child = getattr(client.projects.resources, case.child_method)
    if case.succeeds:
        child.return_value = _RESOURCE_RECORD
    else:
        child.side_effect = RuntimeError("transport failed")
    entity = Project(id="p1", name="Test", status=_PLANNED, _client=client)

    cached_resources = entity.resources.all()
    entity.issues.all()
    if case.succeeds:
        result = getattr(entity, case.method)(*case.args)
        if case.method == "add_local_directory":
            assert isinstance(result, ProjectResourceRecord)
        else:
            assert result is None
        assert entity.resources.all() == cached_resources
        assert client.projects.resources.list.call_count == 2
    else:
        with pytest.raises(RuntimeError, match="transport failed"):
            getattr(entity, case.method)(*case.args)
        assert entity.resources.all() == cached_resources
        assert client.projects.resources.list.call_count == 1
    assert child.call_args.args == ("p1", *case.args)
    assert client.issues.list.call_count == 1


def test_project_parent_mutation_does_not_invalidate_another_wrapper() -> None:
    client = _make_mock_resources(resource_list_result=(_RESOURCE_RECORD,))
    first = Project(id="p1", name="First", status=_PLANNED, _client=client)
    second = Project(id="p1", name="Second", status=_PLANNED, _client=client)

    first.resources.all()
    second.resources.all()
    first.remove_resource("r1")
    first.resources.all()
    second.resources.all()

    assert client.projects.resources.list.call_count == 3


@pytest.mark.parametrize("case", PROJECT_PARENT_VALIDATION_CASES)
def test_project_parent_validation_preserves_loaded_resources(
    case: ProjectParentValidationCase,
) -> None:
    client = _make_mock_resources(resource_list_result=(_RESOURCE_RECORD,))
    entity = Project(id="p1", name="Test", status=_PLANNED, _client=client)
    cached_resources = entity.resources.all()

    with pytest.raises(ValueError):
        getattr(entity, case.method)(*case.args)

    assert entity.resources.all() == cached_resources
    assert client.projects.resources.list.call_count == 1
    getattr(client.projects.resources, case.child_method).assert_not_called()


def test_project_issues_two_pages() -> None:
    page1 = IssueListPage(
        issues=(
            IssueSummary(id="i1", title="Task 1", status=_TODO),
            IssueSummary(id="i2", title="Task 2", status=_TODO),
        ),
        has_more=True,
        limit=2,
        offset=0,
        total=3,
    )
    page2 = IssueListPage(
        issues=(IssueSummary(id="i3", title="Task 3", status=_DONE),),
        has_more=False,
        limit=2,
        offset=2,
        total=3,
    )
    client = _make_mock_resources(issue_page_results=[page1, page2])
    entity = Project(
        id="p1",
        name="Test",
        status=_PLANNED,
        _client=client,
    )

    result = entity.issues.all()
    assert len(result) == 3
    assert client.issues.list.call_count == 2
    assert all(isinstance(item, IssueSummary) for item in result)

    call1_flt = client.issues.list.call_args_list[0][0][0]
    assert call1_flt.limit == 50
    assert call1_flt.offset == 0
    assert call1_flt.project_id == "p1"

    call2_flt = client.issues.list.call_args_list[1][0][0]
    assert call2_flt.offset == 2
    assert call2_flt.project_id == "p1"
    client.issues.get.assert_not_called()


def test_project_issues_single_page() -> None:
    page = IssueListPage(
        issues=(IssueSummary(id="i1", title="One", status=_TODO),),
        has_more=False,
        limit=50,
        offset=0,
        total=1,
    )
    client = _make_mock_resources(issue_page_results=[page, page])
    entity = Project(
        id="p1",
        name="Test",
        status=_PLANNED,
        _client=client,
    )
    result = entity.issues.all()
    assert len(result) == 1
    assert client.issues.list.call_count == 1
    assert isinstance(result[0], IssueSummary)
    client.issues.get.assert_not_called()
    entity.issues.refresh()
    assert client.issues.list.call_count == 2
    client.issues.get.assert_not_called()


def test_project_issues_cached_after_all() -> None:
    page = IssueListPage(issues=(), has_more=False, limit=50, offset=0, total=0)
    client = _make_mock_resources(issue_page_results=[page])
    entity = Project(
        id="p1",
        name="Test",
        status=_PLANNED,
        _client=client,
    )
    entity.issues.all()
    assert client.issues.list.call_count == 1
    client.issues.get.assert_not_called()
    entity.issues.all()
    assert client.issues.list.call_count == 1


def test_project_issues_invalidate_triggers_new_load() -> None:
    page = IssueListPage(issues=(), has_more=False, limit=50, offset=0, total=0)
    client = _make_mock_resources(issue_page_results=[page, page])
    entity = Project(
        id="p1",
        name="Test",
        status=_PLANNED,
        _client=client,
    )
    entity.issues.all()
    assert client.issues.list.call_count == 1
    entity.issues.invalidate()
    entity.issues.all()
    assert client.issues.list.call_count == 2
    client.issues.get.assert_not_called()


def test_detached_entity_error_on_resource_access() -> None:
    entity: Project = Project(id="p1", name="Test", status=_PLANNED)
    with pytest.raises(DetachedEntityError) as exc:
        entity.resources.all()
    assert exc.value.entity_id == "p1"
    assert exc.value.relation_name == "resources"


def test_detached_entity_error_on_issues_access() -> None:
    entity: Project = Project(id="p1", name="Test", status=_PLANNED)
    with pytest.raises(DetachedEntityError) as exc:
        entity.issues.all()
    assert exc.value.entity_id == "p1"
    assert exc.value.relation_name == "issues"


def test_offset_page_exact_fields() -> None:
    page = OffsetPage(items=("a", "b"), total=10, limit=5, offset=0, has_more=True)
    assert page.items == ("a", "b")
    assert page.total == 10
    assert page.limit == 5
    assert page.offset == 0
    assert page.has_more is True
    assert len(page.items) == 2
