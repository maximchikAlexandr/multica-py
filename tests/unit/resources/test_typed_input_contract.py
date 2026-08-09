from __future__ import annotations

import importlib
import inspect
import pkgutil
import typing
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import msgspec
import pytest

from multica_py import Command
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import AutopilotExecutionMode, MetadataValueType, ProjectStatus
from multica_py.models.agents import AgentCreateRequest, AgentUpdateRequest
from multica_py.models.autopilots import (
    AutopilotTriggerCreate,
    AutopilotTriggerUpdate,
    AutopilotUpdateRequest,
)
from multica_py.models.issue_activity import (
    CommentListFlatRequest,
    CommentListRecentRequest,
    CommentListThreadRequest,
    MetadataListRequest,
    MetadataPredicate,
    MetadataSetRequest,
)
from multica_py.models.issues import (
    InlineDescription,
    IssueAssignmentRequest,
    IssueCreateRequest,
    IssueListFilter,
    IssueReorderRequest,
    IssueUpdateRequest,
)
from multica_py.models.labels import LabelUpdateRequest
from multica_py.models.project_resources import (
    ProjectResourceAddLocalDirectoryRequest,
    ProjectResourceUpdateLocalDirectoryRequest,
)
from multica_py.models.projects import ProjectCreateRequest, ProjectUpdateRequest
from multica_py.models.skills import SkillCreateRequest, SkillUpdateRequest
from multica_py.models.system import RuntimeUpdate, UserProfileUpdate
from multica_py.resources.agents import AgentResource
from multica_py.resources.autopilots import Autopilot, AutopilotResource
from multica_py.resources.issue_comments import IssueCommentResource
from multica_py.resources.issue_metadata import IssueMetadataResource
from multica_py.resources.issues import IssueResource
from multica_py.resources.labels import LabelResource
from multica_py.resources.project_resources import ProjectResourceCollection
from multica_py.resources.projects import Project, ProjectResource
from multica_py.resources.runtimes import RuntimeResource
from multica_py.resources.skills import SkillResource
from multica_py.resources.users import UserResource


@dataclass(frozen=True, slots=True)
class TypedInputCase:
    case_id: str
    owner: type[object]
    eager_name: str
    command_name: str
    request: msgspec.Struct
    target_args: tuple[object, ...]
    direct_kwargs: tuple[tuple[str, object], ...]
    owner_factory: Callable[[MagicMock], object]
    requires_request: bool = True
    allows_empty: bool = False


def _resource_factory(owner: type[object]) -> Callable[[MagicMock], object]:
    def build(transport: MagicMock) -> object:
        constructor = typing.cast("Callable[[CliTransport, ClientConfig], object]", owner)
        return constructor(transport, ClientConfig())

    return build


def _bound_autopilot(transport: MagicMock) -> Autopilot:
    client = MagicMock(spec=MulticaClient)
    client.autopilots = AutopilotResource(transport, ClientConfig())
    return Autopilot(
        id="a1",
        workspace_id="w1",
        title="Autopilot",
        assignee_type="member",
        assignee_id="u1",
        status="active",
        execution_mode="create_issue",
        created_by_type="member",
        created_by_id="u1",
        _client=client,
    )


def _bound_project(transport: MagicMock) -> Project:
    client = MagicMock(spec=MulticaClient)
    client.projects = ProjectResource(transport, ClientConfig())
    return Project(id="p1", name="Project", status=ProjectStatus.planned, _client=client)


def _case(
    case_id: str,
    owner: type[object],
    eager_name: str,
    request: msgspec.Struct,
    direct_kwargs: tuple[tuple[str, object], ...],
    *,
    target_args: tuple[object, ...] = (),
    owner_factory: Callable[[MagicMock], object] | None = None,
    requires_request: bool = True,
    allows_empty: bool = False,
) -> TypedInputCase:
    return TypedInputCase(
        case_id=case_id,
        owner=owner,
        eager_name=eager_name,
        command_name=f"{eager_name}_command",
        request=request,
        target_args=target_args,
        direct_kwargs=direct_kwargs,
        owner_factory=owner_factory or _resource_factory(owner),
        requires_request=requires_request,
        allows_empty=allows_empty,
    )


TYPED_INPUT_CASES: tuple[TypedInputCase, ...] = (
    _case(
        "agents.create",
        AgentResource,
        "create",
        AgentCreateRequest(name="agent"),
        (("name", "agent"),),
    ),
    _case(
        "agents.update",
        AgentResource,
        "update",
        AgentUpdateRequest(name="agent-new"),
        (("name", "agent-new"),),
        target_args=("a1",),
        requires_request=False,
        allows_empty=True,
    ),
    _case(
        "autopilots.update",
        AutopilotResource,
        "update",
        AutopilotUpdateRequest(
            title="Autopilot-new",
            execution_mode=AutopilotExecutionMode.create_issue,
            subscribers=("u1",),
        ),
        (
            ("title", "Autopilot-new"),
            ("execution_mode", AutopilotExecutionMode.create_issue),
            ("subscribers", ("u1",)),
        ),
        target_args=("a1",),
        requires_request=False,
        allows_empty=True,
    ),
    _case(
        "autopilots.trigger_add",
        AutopilotResource,
        "trigger_add",
        AutopilotTriggerCreate(title="Webhook", kind="webhook"),
        (("title", "Webhook"), ("kind", "webhook")),
        target_args=("a1",),
    ),
    _case(
        "autopilots.trigger_update",
        AutopilotResource,
        "trigger_update",
        AutopilotTriggerUpdate(title="Webhook-new"),
        (("title", "Webhook-new"),),
        target_args=("a1", "t1"),
        requires_request=False,
        allows_empty=True,
    ),
    _case(
        "autopilots.bound.trigger_add",
        Autopilot,
        "trigger_add",
        AutopilotTriggerCreate(title="Webhook", kind="webhook"),
        (("title", "Webhook"), ("kind", "webhook")),
        owner_factory=_bound_autopilot,
    ),
    _case(
        "autopilots.bound.trigger_update",
        Autopilot,
        "trigger_update",
        AutopilotTriggerUpdate(title="Webhook-new"),
        (("title", "Webhook-new"),),
        target_args=("t1",),
        owner_factory=_bound_autopilot,
        requires_request=False,
        allows_empty=True,
    ),
    _case(
        "issues.comments.list_flat",
        IssueCommentResource,
        "list_flat",
        CommentListFlatRequest(issue_id="i1"),
        (("issue_id", "i1"),),
    ),
    _case(
        "issues.comments.list_thread",
        IssueCommentResource,
        "list_thread",
        CommentListThreadRequest(issue_id="i1", thread_id="t1", limit=5),
        (("issue_id", "i1"), ("thread_id", "t1"), ("limit", 5)),
    ),
    _case(
        "issues.comments.list_recent",
        IssueCommentResource,
        "list_recent",
        CommentListRecentRequest(issue_id="i1", limit=3),
        (("issue_id", "i1"), ("limit", 3)),
    ),
    _case(
        "issues.metadata.query",
        IssueMetadataResource,
        "query",
        MetadataListRequest(
            issue_id="i1",
            predicates=(MetadataPredicate(key="priority", value=3),),
            cursor="next",
            limit=5,
        ),
        (
            ("issue_id", "i1"),
            ("predicates", (MetadataPredicate(key="priority", value=3),)),
            ("cursor", "next"),
            ("limit", 5),
        ),
    ),
    _case(
        "issues.metadata.set_typed",
        IssueMetadataResource,
        "set_typed",
        MetadataSetRequest(
            issue_id="i1", key="enabled", value=True, value_type=MetadataValueType.boolean
        ),
        (
            ("issue_id", "i1"),
            ("key", "enabled"),
            ("value", True),
            ("value_type", MetadataValueType.boolean),
        ),
    ),
    _case(
        "issues.list",
        IssueResource,
        "list",
        IssueListFilter(limit=10, offset=2),
        (("limit", 10), ("offset", 2)),
        requires_request=False,
        allows_empty=True,
    ),
    _case(
        "issues.create",
        IssueResource,
        "create",
        IssueCreateRequest(title="Issue", description_input=InlineDescription(text="body")),
        (("title", "Issue"), ("description_input", InlineDescription(text="body"))),
    ),
    _case(
        "issues.update",
        IssueResource,
        "update",
        IssueUpdateRequest(title="Issue-new"),
        (("title", "Issue-new"),),
        target_args=("i1",),
        requires_request=False,
        allows_empty=True,
    ),
    _case(
        "issues.assign",
        IssueResource,
        "assign",
        IssueAssignmentRequest(issue_id="i1", member_id="u1"),
        (("issue_id", "i1"), ("member_id", "u1")),
    ),
    _case(
        "issues.reorder",
        IssueResource,
        "reorder",
        IssueReorderRequest(issue_id="i1", top=True),
        (("issue_id", "i1"), ("top", True)),
    ),
    _case(
        "labels.update",
        LabelResource,
        "update",
        LabelUpdateRequest(name="feature", color="blue"),
        (("name", "feature"), ("color", "blue")),
        target_args=("label1",),
        requires_request=False,
        allows_empty=True,
    ),
    _case(
        "projects.bound.resources.add_local_directory",
        Project,
        "add_local_directory",
        ProjectResourceAddLocalDirectoryRequest(local_path="/tmp", daemon_id="d1"),
        (("local_path", "/tmp"), ("daemon_id", "d1")),
        owner_factory=_bound_project,
    ),
    _case(
        "projects.resources.add_local_directory",
        ProjectResourceCollection,
        "add_local_directory",
        ProjectResourceAddLocalDirectoryRequest(local_path="/tmp", daemon_id="d1"),
        (("local_path", "/tmp"), ("daemon_id", "d1")),
        target_args=("p1",),
    ),
    _case(
        "projects.resources.update_local_directory",
        ProjectResourceCollection,
        "update_local_directory",
        ProjectResourceUpdateLocalDirectoryRequest(local_path="/tmp/new"),
        (("local_path", "/tmp/new"),),
        target_args=("p1", "r1"),
    ),
    _case(
        "projects.create",
        ProjectResource,
        "create",
        ProjectCreateRequest(name="Project"),
        (("name", "Project"),),
    ),
    _case(
        "projects.update",
        ProjectResource,
        "update",
        ProjectUpdateRequest(name="Project-new"),
        (("name", "Project-new"),),
        target_args=("p1",),
        requires_request=False,
        allows_empty=True,
    ),
    _case(
        "runtimes.update",
        RuntimeResource,
        "update",
        RuntimeUpdate(target_version="v1"),
        (("target_version", "v1"),),
        target_args=("r1",),
    ),
    _case(
        "skills.create",
        SkillResource,
        "create",
        SkillCreateRequest(name="skill"),
        (("name", "skill"),),
    ),
    _case(
        "skills.update",
        SkillResource,
        "update",
        SkillUpdateRequest(name="skill-new"),
        (("name", "skill-new"),),
        target_args=("s1",),
        requires_request=False,
        allows_empty=True,
    ),
    _case(
        "users.profile_update",
        UserResource,
        "profile_update",
        UserProfileUpdate(description="about"),
        (("description", "about"),),
        requires_request=False,
    ),
)


_GOVERNED_REQUEST_TYPES = frozenset(
    {
        AgentCreateRequest,
        AgentUpdateRequest,
        AutopilotTriggerCreate,
        AutopilotTriggerUpdate,
        AutopilotUpdateRequest,
        CommentListFlatRequest,
        CommentListRecentRequest,
        CommentListThreadRequest,
        IssueAssignmentRequest,
        IssueCreateRequest,
        IssueListFilter,
        IssueReorderRequest,
        IssueUpdateRequest,
        LabelUpdateRequest,
        MetadataListRequest,
        MetadataSetRequest,
        ProjectCreateRequest,
        ProjectResourceAddLocalDirectoryRequest,
        ProjectResourceUpdateLocalDirectoryRequest,
        ProjectUpdateRequest,
        RuntimeUpdate,
        SkillCreateRequest,
        SkillUpdateRequest,
        UserProfileUpdate,
    }
)


def _iter_resource_classes() -> Iterator[type[object]]:
    import multica_py.resources as resources_pkg

    seen: set[type[object]] = set()
    for module_info in pkgutil.walk_packages(
        resources_pkg.__path__, prefix="multica_py.resources."
    ):
        module = importlib.import_module(module_info.name)
        for value in vars(module).values():
            if not inspect.isclass(value) or value.__module__ != module_info.name:
                continue
            owner = typing.cast("type[object]", value)
            if owner not in seen:
                seen.add(owner)
                yield owner


def _governed_annotations() -> frozenset[tuple[type[object], str, type[msgspec.Struct]]]:
    discovered: set[tuple[type[object], str, type[msgspec.Struct]]] = set()
    for owner in _iter_resource_classes():
        for method_name, method in owner.__dict__.items():
            if method_name.startswith("_") or not inspect.isfunction(method):
                continue
            for overload in typing.get_overloads(method):
                hints = typing.get_type_hints(overload)
                for parameter_name, annotation in hints.items():
                    if parameter_name == "return" or annotation not in _GOVERNED_REQUEST_TYPES:
                        continue
                    discovered.add(
                        (owner, method_name, typing.cast("type[msgspec.Struct]", annotation))
                    )
    return frozenset(discovered)


def _table_annotations() -> frozenset[tuple[type[object], str, type[msgspec.Struct]]]:
    return frozenset(
        (case.owner, method_name, type(case.request))
        for case in TYPED_INPUT_CASES
        for method_name in (case.eager_name, case.command_name)
    )


def _overload_hints(method: Callable[..., object]) -> tuple[tuple[object, dict[str, object]], ...]:
    return tuple(
        (overload, typing.cast("dict[str, object]", typing.get_type_hints(overload)))
        for overload in typing.get_overloads(method)
    )


def _request_overload(method: Callable[..., object], request_type: type[msgspec.Struct]) -> object:
    for overload, hints in _overload_hints(method):
        if any(
            annotation is request_type for name, annotation in hints.items() if name != "return"
        ):
            return overload
    raise AssertionError(f"{method.__qualname__} has no typed-object overload")


def _direct_overload(method: Callable[..., object], request_type: type[msgspec.Struct]) -> object:
    fields = {field.name for field in msgspec.structs.fields(request_type)}
    for overload, hints in _overload_hints(method):
        signature = inspect.signature(typing.cast("Callable[..., object]", overload))
        keyword_names = {
            parameter.name
            for parameter in signature.parameters.values()
            if parameter.kind == inspect.Parameter.KEYWORD_ONLY
        }
        if keyword_names == fields:
            return overload
    raise AssertionError(f"{method.__qualname__} has no exact direct-keyword overload")


def _without_return(method: object) -> inspect.Signature:
    callable_method = typing.cast("Callable[..., object]", method)
    return inspect.signature(callable_method).replace(return_annotation=inspect.Signature.empty)


def _same_default(left: object, right: object) -> bool:
    if left is msgspec.NODEFAULT or right is msgspec.NODEFAULT:
        return left is right
    if left is msgspec.UNSET or right is msgspec.UNSET:
        return left is right
    return left == right


def _assert_overload_contract(case: TypedInputCase) -> None:
    eager = typing.cast("Callable[..., object]", getattr(case.owner, case.eager_name))
    command = typing.cast("Callable[..., object]", getattr(case.owner, case.command_name))
    eager_overloads = typing.get_overloads(eager)
    command_overloads = typing.get_overloads(command)
    assert len(eager_overloads) == len(command_overloads), case.case_id
    for eager_overload, command_overload in zip(eager_overloads, command_overloads, strict=True):
        assert _without_return(eager_overload) == _without_return(command_overload), case.case_id
        eager_return = typing.get_type_hints(eager_overload)["return"]
        command_return = typing.get_type_hints(command_overload)["return"]
        assert typing.get_origin(command_return) is Command, case.case_id
        assert typing.get_args(command_return) == (eager_return,), case.case_id

    request_type = type(case.request)
    for method in (eager, command):
        object_overload = _request_overload(method, request_type)
        direct_overload = _direct_overload(method, request_type)
        object_signature = inspect.signature(typing.cast("Callable[..., object]", object_overload))
        object_hints = typing.get_type_hints(object_overload)
        request_parameters = [
            parameter
            for parameter in object_signature.parameters.values()
            if object_hints.get(parameter.name) is request_type
        ]
        assert len(request_parameters) == 1, case.case_id
        assert request_parameters[0].kind == inspect.Parameter.POSITIONAL_ONLY, case.case_id
        direct_signature = inspect.signature(typing.cast("Callable[..., object]", direct_overload))
        direct_parameters = {
            parameter.name: parameter
            for parameter in direct_signature.parameters.values()
            if parameter.kind == inspect.Parameter.KEYWORD_ONLY
        }
        fields = msgspec.structs.fields(request_type)
        assert set(direct_parameters) == {field.name for field in fields}, case.case_id
        direct_hints = typing.get_type_hints(direct_overload)
        for field in fields:
            parameter = direct_parameters[field.name]
            assert direct_hints[field.name] == field.type, case.case_id
            parameter_default = (
                msgspec.NODEFAULT
                if parameter.default is inspect.Parameter.empty
                else parameter.default
            )
            assert _same_default(parameter_default, field.default), case.case_id


def _step_shapes(command: Command[object]) -> tuple[tuple[object, ...], ...]:
    plan = getattr(command, "_plan")
    return tuple((step.argv, step.mode, step.stdin, step.timeout) for step in plan.steps)


def _transport() -> MagicMock:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    return transport


def test_governed_request_inventory_matches_frozen_case_table() -> None:
    assert {type(case.request) for case in TYPED_INPUT_CASES} == _GOVERNED_REQUEST_TYPES
    assert _governed_annotations() == _table_annotations()
    assert len(TYPED_INPUT_CASES) == 27


@pytest.mark.parametrize("case", TYPED_INPUT_CASES, ids=lambda case: case.case_id)
def test_governed_overloads_have_exact_fields_and_eager_command_parity(
    case: TypedInputCase,
) -> None:
    _assert_overload_contract(case)


@pytest.mark.parametrize("case", TYPED_INPUT_CASES, ids=lambda case: case.case_id)
def test_object_and_direct_forms_have_exact_plan_and_result_parity(
    case: TypedInputCase,
) -> None:
    transport = _transport()
    owner = case.owner_factory(transport)
    target_args = case.target_args
    direct_kwargs = dict(case.direct_kwargs)
    object_command = typing.cast(
        "Command[object]",
        getattr(owner, case.command_name)(*target_args, case.request),
    )
    direct_command = typing.cast(
        "Command[object]",
        getattr(owner, case.command_name)(*target_args, **direct_kwargs),
    )
    assert object_command.commands == direct_command.commands
    assert _step_shapes(object_command) == _step_shapes(direct_command)

    result = object()
    with patch.object(Command, "run", return_value=result) as run:
        object_result = getattr(owner, case.eager_name)(*target_args, case.request)
        direct_result = getattr(owner, case.eager_name)(*target_args, **direct_kwargs)
    assert object_result is result
    assert direct_result is result
    assert run.call_count == 2
    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()
    transport.spawn.assert_not_called()


@pytest.mark.parametrize("case", TYPED_INPUT_CASES, ids=lambda case: case.case_id)
def test_mixed_input_unknown_keyword_and_required_missing_fail_before_transport(
    case: TypedInputCase,
) -> None:
    transport = _transport()
    owner = case.owner_factory(transport)
    method = getattr(owner, case.command_name)
    direct_kwargs = dict(case.direct_kwargs)
    first_name, first_value = next(iter(direct_kwargs.items()))

    with pytest.raises(
        TypeError, match=r"Pass either a request object or keyword arguments, not both\."
    ):
        method(*case.target_args, case.request, **{first_name: first_value})
    with pytest.raises(TypeError):
        method(*case.target_args, unknown_typed_input="value")
    if case.requires_request:
        with pytest.raises(TypeError, match=r"Pass a .* or its keyword arguments; got neither\."):
            method(*case.target_args)

    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()
    transport.spawn.assert_not_called()


@pytest.mark.parametrize(
    "case",
    tuple(case for case in TYPED_INPUT_CASES if case.allows_empty),
    ids=lambda case: f"{case.case_id}:empty",
)
def test_optional_empty_object_and_direct_forms_have_same_plan(case: TypedInputCase) -> None:
    transport = _transport()
    owner = case.owner_factory(transport)
    object_command = typing.cast(
        "Command[object]",
        getattr(owner, case.command_name)(*case.target_args, type(case.request)()),
    )
    direct_command = typing.cast(
        "Command[object]", getattr(owner, case.command_name)(*case.target_args)
    )
    assert object_command.commands == direct_command.commands
    assert _step_shapes(object_command) == _step_shapes(direct_command)
    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


@pytest.mark.parametrize(
    ("case_id", "field"),
    (
        ("agents.update", "name"),
        ("autopilots.update", "title"),
        ("autopilots.trigger_update", "title"),
        ("issues.update", "title"),
        ("labels.update", "name"),
        ("projects.update", "name"),
        ("skills.update", "name"),
        ("projects.resources.update_local_directory", "local_path"),
        ("runtimes.update", "target_version"),
    ),
)
def test_request_post_init_failures_are_zero_io(
    case_id: str, field: str, mock_transport: MagicMock
) -> None:
    case = next(case for case in TYPED_INPUT_CASES if case.case_id == case_id)
    owner = case.owner_factory(mock_transport)
    with pytest.raises((TypeError, ValueError)):
        getattr(owner, case.command_name)(*case.target_args, **{field: None})
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()
    mock_transport.spawn.assert_not_called()


def test_direct_request_fields_are_not_positional(mock_transport: MagicMock) -> None:
    case = next(case for case in TYPED_INPUT_CASES if case.case_id == "issues.list")
    owner = case.owner_factory(mock_transport)
    with pytest.raises(TypeError):
        getattr(owner, case.command_name)(10)
    mock_transport.run_bytes.assert_not_called()
    mock_transport.run_text.assert_not_called()
    mock_transport.spawn.assert_not_called()
