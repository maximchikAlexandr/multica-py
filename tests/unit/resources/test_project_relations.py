from __future__ import annotations

import datetime
import os
import shlex
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast
from unittest.mock import MagicMock

import pytest

from multica_py._internal.commands import Command, _Step
from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.exceptions import DetachedEntityError
from multica_py.models.common import ActionResult, Page
from multica_py.models.issues import IssueListFilter, IssueListPage, IssueSummary
from multica_py.models.project_resources import (
    ProjectResourceAddLocalDirectoryRequest,
    ProjectResourceRecord,
)
from multica_py.models.projects import ProjectCreateRequest, ProjectUpdateRequest
from multica_py.models.relations import LazyCollection, OffsetPage
from multica_py.resources._base import BaseResource
from multica_py.resources.issues import IssueResource
from multica_py.resources.project_resources import ProjectResourceCollection
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


@dataclass(frozen=True)
class ProjectRelationCommandCase:
    name: str
    relation: str
    method: str
    limit: int | None
    offset: int
    expected_argv: tuple[str, ...]


PROJECT_RELATION_COMMAND_CASES = (
    ProjectRelationCommandCase(
        "resources all",
        "resources",
        "all_command",
        None,
        0,
        ("project", "resource", "list", "p1", "--output", "json"),
    ),
    ProjectRelationCommandCase(
        "issues page",
        "issues",
        "page_command",
        2,
        3,
        (
            "issue",
            "list",
            "--limit",
            "2",
            "--offset",
            "3",
            "--project",
            "p1",
            "--output",
            "json",
        ),
    ),
    ProjectRelationCommandCase(
        "issues all",
        "issues",
        "all_command",
        None,
        0,
        (
            "issue",
            "list",
            "--limit",
            "50",
            "--offset",
            "0",
            "--project",
            "p1",
            "--output",
            "json",
        ),
    ),
)


def _make_mock_resources(
    project_list_result: tuple[object, ...] = (),
    resource_list_result: tuple[ProjectResourceRecord, ...] = (),
    issue_page_results: list[IssueListPage] | None = None,
) -> MagicMock:
    client = MagicMock()

    def mutation_command(
        loader: Callable[[], object], argv: tuple[str, ...] = ("project", "resource", "mutation")
    ) -> Command[object]:
        transport = MagicMock(spec=CliTransport)
        result: dict[str, object] = {}

        def run_text(_argv: tuple[str, ...]) -> TextResult:
            result["value"] = loader()
            return TextResult("", "", 0)

        cast("MagicMock", transport.run_text).side_effect = run_text
        resource = BaseResource(transport, ClientConfig())
        return resource._plan(
            steps=(_Step(argv, "run_text"),),
            finalize=lambda _results: result["value"],
        )

    client.projects.resources.list.return_value = resource_list_result
    client.projects.resources.list_command = lambda project_id: mutation_command(
        lambda: client.projects.resources.list(project_id),
        ("project", "resource", "list", project_id),
    )
    client.projects.resources.add_local_directory_command = lambda project_id, request: (
        mutation_command(lambda: client.projects.resources.add_local_directory(project_id, request))
    )
    client.projects.resources.remove_command = lambda project_id, resource_id: mutation_command(
        lambda: client.projects.resources.remove(project_id, resource_id)
    )
    if issue_page_results is not None:
        client.issues.list.side_effect = issue_page_results
    else:
        client.issues.list.return_value = IssueListPage(
            items=(), has_more=False, limit=50, offset=0, total=0
        )

    def issue_list_command(issue_filter: object) -> Command[object]:
        args = ["issue", "list"]
        limit = getattr(issue_filter, "limit")
        offset = getattr(issue_filter, "offset")
        project_id = getattr(issue_filter, "project_id")
        if limit is not None:
            args.extend(("--limit", str(limit)))
        if offset is not None:
            args.extend(("--offset", str(offset)))
        if project_id is not None:
            args.extend(("--project", project_id))

        def decode_page(_stdout: bytes, command_text: str) -> IssueListPage:
            command_args = command_text.split()
            command_limit = int(command_args[command_args.index("--limit") + 1])
            command_offset = int(command_args[command_args.index("--offset") + 1])
            command_project = command_args[command_args.index("--project") + 1]
            return client.issues.list(
                IssueListFilter(
                    limit=command_limit,
                    offset=command_offset,
                    project_id=command_project,
                )
            )

        transport = MagicMock(spec=CliTransport)
        transport.run_text.return_value = TextResult("", "", 0)
        resource = BaseResource(transport, ClientConfig())
        return resource._plan(
            steps=(
                _Step(
                    tuple(args),
                    "run_text",
                    decode=decode_page,
                ),
            ),
            finalize=lambda results: results[0],
        )

    client.issues.list_command = issue_list_command
    return client


@pytest.mark.parametrize("case", PROJECT_BINDING_CASES, ids=lambda case: case.name)
def test_project_resource_returns_bound_immutable_projects(case: ProjectBindingCase) -> None:
    transport = MagicMock()
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
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

    command = getattr(resource, f"{case.method}_command")(*case.args)
    assert command.commands == (f"multica {shlex.join(case.expected_argv)}",)
    assert transport.run_bytes.call_count == 0
    result = command.run()
    project = result.items[0] if isinstance(result, Page) else result

    assert isinstance(project, Project)
    assert project._client is client
    assert client.mock_calls == []
    transport.run_bytes.assert_called_once_with(case.expected_argv, stdin=None, timeout=None)
    assert transport.run_text.call_count == 0


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

    # Second .all() uses cache, no new call
    result2 = entity.resources.all()
    assert len(result2) == 1
    assert client.projects.resources.list.call_count == 1


@pytest.mark.parametrize("case", PROJECT_RELATION_COMMAND_CASES, ids=lambda case: case.name)
def test_project_relation_commands_preserve_project_scope(
    case: ProjectRelationCommandCase,
) -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    projects = ProjectResource(transport, ClientConfig())
    issue_resource = IssueResource(transport, ClientConfig())
    client = MagicMock()
    client.projects = projects
    client.issues = issue_resource
    projects._set_client(client)
    issue_resource._set_client(client)
    entity = Project(id="p1", name="Test", status=_PLANNED, _client=client)

    relation = getattr(entity, case.relation)
    if case.method == "page_command":
        command = getattr(relation, case.method)(limit=case.limit, offset=case.offset)
    else:
        command = getattr(relation, case.method)()

    assert command.commands[0] == f"multica {shlex.join(case.expected_argv)}"
    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


def test_project_add_local_directory_command_freezes_path_and_invalidates_after_success() -> None:
    transport = MagicMock()
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.return_value = RawCommandResult(
        argv=(
            "project",
            "resource",
            "add",
            "p1",
            "--type",
            "local_directory",
            "--local-path",
            os.path.abspath("relative/sandbox"),
            "--daemon-id",
            "d1",
            "--output",
            "json",
        ),
        exit_code=0,
        stdout=(
            b'{"id":"r1","project_id":"p1","resource_type":"local_directory",'
            b'"resource_ref":{"local_path":"/tmp/sandbox","daemon_id":"d1"}}'
        ),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    projects = ProjectResource(transport, ClientConfig())
    client = MagicMock()
    client.projects = projects
    projects._set_client(client)
    entity = Project(id="p1", name="Test", status=_PLANNED, _client=client)
    entity._set_runtime("_resources", LazyCollection(lambda: ()))
    entity.resources.all()

    command = entity.add_local_directory_command(
        ProjectResourceAddLocalDirectoryRequest(local_path="relative/sandbox", daemon_id="d1")
    )

    assert command.commands == (
        "multica project resource add p1 --type local_directory --local-path "
        f"{os.path.abspath('relative/sandbox')} --daemon-id d1 --output json",
    )
    assert entity.resources.loaded
    assert transport.run_bytes.call_count == 0

    result = command.run()

    assert result.id == "r1"
    assert not entity.resources.loaded


def test_project_resource_mutation_command_failure_preserves_cache_and_remove_invalidates() -> None:
    transport = MagicMock()
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    projects = ProjectResource(transport, ClientConfig())
    client = MagicMock()
    client.projects = projects
    projects._set_client(client)
    entity = Project(id="p1", name="Test", status=_PLANNED, _client=client)
    entity._set_runtime("_resources", LazyCollection(lambda: ()))
    entity.resources.all()

    transport.run_bytes.side_effect = RuntimeError("transport failed")
    command = entity.add_local_directory_command(
        ProjectResourceAddLocalDirectoryRequest(local_path="/tmp/sandbox", daemon_id="d1")
    )
    with pytest.raises(RuntimeError, match="transport failed"):
        command.run()
    assert entity.resources.loaded

    transport.run_bytes.side_effect = None
    remove_command = entity.remove_resource_command("r1")
    assert remove_command.commands == ("multica project resource remove p1 r1",)
    assert transport.run_text.call_count == 0
    remove_command.run()
    assert not entity.resources.loaded


@pytest.mark.parametrize(
    ("method", "entity_id", "resource_id", "daemon_id"),
    (
        ("add_local_directory_command", "", "r1", "d1"),
        ("add_local_directory_command", "p1", "r1", ""),
        ("remove_resource_command", "", "r1", "d1"),
        ("remove_resource_command", "p1", "", "d1"),
    ),
)
def test_project_mutation_commands_validate_before_transport(
    method: str, entity_id: str, resource_id: str, daemon_id: str
) -> None:
    transport = MagicMock()
    client = MagicMock()
    client.projects = ProjectResource(transport, ClientConfig())
    entity = Project(id=entity_id, name="Test", status=_PLANNED, _client=client)

    with pytest.raises(ValueError):
        if method == "add_local_directory_command":
            entity.add_local_directory_command(
                ProjectResourceAddLocalDirectoryRequest(
                    local_path="/tmp/sandbox", daemon_id=daemon_id
                )
            )
        else:
            entity.remove_resource_command(resource_id)

    assert transport.run_bytes.call_count == 0
    assert transport.run_text.call_count == 0
    assert transport.spawn.call_count == 0


@pytest.mark.parametrize("case", PROJECT_PARENT_MUTATION_CASES, ids=lambda case: case.name)
def test_project_parent_mutations_invalidate_only_resources(
    case: ProjectParentMutationCase,
) -> None:
    page = IssueListPage(items=(), has_more=False, limit=50, offset=0, total=0)
    client = _make_mock_resources(
        resource_list_result=(_RESOURCE_RECORD,), issue_page_results=[page]
    )
    child = getattr(client.projects.resources, case.child_method)
    if case.succeeds:
        child.return_value = (
            _RESOURCE_RECORD if case.method == "add_local_directory" else ActionResult(value=None)
        )
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
            assert isinstance(result, ActionResult)
            assert result.success and result.value is None
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
        items=(
            IssueSummary(id="i1", title="Task 1", status=_TODO),
            IssueSummary(id="i2", title="Task 2", status=_TODO),
        ),
        has_more=True,
        limit=2,
        offset=0,
        total=3,
    )
    page2 = IssueListPage(
        items=(IssueSummary(id="i3", title="Task 3", status=_DONE),),
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
        items=(IssueSummary(id="i1", title="One", status=_TODO),),
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
    page = IssueListPage(items=(), has_more=False, limit=50, offset=0, total=0)
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
    page = IssueListPage(items=(), has_more=False, limit=50, offset=0, total=0)
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
