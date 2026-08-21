from __future__ import annotations

import importlib
import inspect
import pkgutil
import re
import types
from collections.abc import Iterator
from types import ModuleType
from typing import Any, ForwardRef, TypeGuard, TypeVar, cast, get_args, get_origin, get_type_hints

import msgspec

import multica_py.models as models_pkg
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.entities.issues import Issue
from multica_py.models.autopilots import AutopilotListPage, AutopilotRunListPage
from multica_py.models.common import ActionResult, CommentCursor, Page
from multica_py.models.issue_activity import MetadataPage
from multica_py.models.issues import IssueChildrenResult, IssueListFilter, IssueListPage
from multica_py.models.project_resources import (
    LocalDirectoryResourceRef,
    ProjectResourceRecord,
)
from multica_py.models.relations import (
    CursorLazyCollection,
    CursorPage,
    LazyCollection,
    LazyMapping,
    OffsetLazyCollection,
    OffsetPage,
    RelationMetadata,
)
from multica_py.models.system import RuntimeUpdateResult
from multica_py.resources.cli import CliResult
from multica_py.resources.project_resources import ProjectResourceCollection

_DIRECT_KEYWORD_METHODS = frozenset(
    {
        ("AgentResource", "create"),
        ("AgentResource", "create_command"),
        ("AgentResource", "update"),
        ("AgentResource", "update_command"),
        ("IssueResource", "assign"),
        ("IssueResource", "assign_command"),
        ("IssueResource", "create"),
        ("IssueResource", "create_command"),
        ("IssueResource", "reorder"),
        ("IssueResource", "reorder_command"),
        ("IssueResource", "update"),
        ("IssueResource", "update_command"),
        ("IssueResource", "list"),
        ("IssueResource", "list_command"),
        ("IssueCommentResource", "list_flat"),
        ("IssueCommentResource", "list_flat_command"),
        ("IssueCommentResource", "list_thread"),
        ("IssueCommentResource", "list_thread_command"),
        ("IssueCommentResource", "list_recent"),
        ("IssueCommentResource", "list_recent_command"),
        ("IssueMetadataResource", "query"),
        ("IssueMetadataResource", "query_command"),
        ("IssueMetadataResource", "set_typed"),
        ("IssueMetadataResource", "set_typed_command"),
        ("AutopilotResource", "trigger_add"),
        ("AutopilotResource", "trigger_add_command"),
        ("AutopilotResource", "trigger_update"),
        ("AutopilotResource", "trigger_update_command"),
        ("AutopilotResource", "update"),
        ("AutopilotResource", "update_command"),
        ("LabelResource", "update"),
        ("LabelResource", "update_command"),
        ("ProjectResource", "create"),
        ("ProjectResource", "create_command"),
        ("ProjectResource", "update"),
        ("ProjectResource", "update_command"),
        ("ProjectResourceCollection", "add_local_directory"),
        ("ProjectResourceCollection", "add_local_directory_command"),
        ("ProjectResourceCollection", "update_local_directory"),
        ("ProjectResourceCollection", "update_local_directory_command"),
        ("RuntimeResource", "update"),
        ("RuntimeResource", "update_command"),
        ("SkillResource", "create"),
        ("SkillResource", "create_command"),
        ("SkillResource", "update"),
        ("SkillResource", "update_command"),
        ("UserResource", "profile_update"),
        ("UserResource", "profile_update_command"),
    }
)


def _assert_hint_clean(owner_name: str, callable_name: str, hints: dict[str, object]) -> None:
    for param_name, param_type in hints.items():
        type_str = str(param_type)
        assert "Any" not in type_str, (
            f"{owner_name}.{callable_name} parameter {param_name} uses Any"
        )
        if (
            param_name == "kwargs"
            and type_str == "<class 'object'>"
            and (owner_name, callable_name) in _DIRECT_KEYWORD_METHODS
        ):
            continue
        assert type_str != "<class 'object'>", (
            f"{owner_name}.{callable_name} parameter {param_name} uses object"
        )
        if param_name == "return":
            assert "list[" not in type_str and type_str != "list", (
                f"{owner_name}.{callable_name} returns list, use tuple instead"
            )


def _assert_public_methods_typed(cls: type[object]) -> None:
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        hints = get_type_hints(method)
        _assert_hint_clean(cls.__name__, name, hints)


def _is_struct_type(obj: object) -> TypeGuard[type[msgspec.Struct]]:
    return isinstance(obj, type) and issubclass(obj, msgspec.Struct)


def _iter_model_modules() -> Iterator[tuple[str, ModuleType]]:
    for _importer, modname, _ispkg in pkgutil.walk_packages(
        models_pkg.__path__, prefix="multica_py.models."
    ):
        yield modname, importlib.import_module(modname)


def _iter_struct_types() -> Iterator[tuple[str, str, type[msgspec.Struct]]]:
    for modname, mod in _iter_model_modules():
        for name in dir(mod):
            obj = getattr(mod, name)
            if _is_struct_type(obj):
                yield modname, name, obj


def test_no_any_in_public_api() -> None:
    _assert_public_methods_typed(MulticaClient)
    _assert_public_methods_typed(ClientConfig)

    client = MulticaClient(ClientConfig())
    for resource_name in (
        "auth",
        "setup",
        "daemon",
        "workspaces",
        "issues",
        "projects",
        "labels",
        "agents",
        "skills",
        "autopilots",
        "repositories",
        "runtimes",
        "attachments",
        "configuration",
        "squads",
        "users",
        "maintenance",
    ):
        resource = getattr(client, resource_name)
        _assert_public_methods_typed(type(resource))
    _assert_public_methods_typed(ProjectResourceCollection)


def test_public_model_exports() -> None:
    import multica_py

    assert len(multica_py.__all__) == len(set(multica_py.__all__))
    assert len(models_pkg.__all__) == len(set(models_pkg.__all__))
    dedicated_exports = {
        "AutopilotListPage": AutopilotListPage,
        "AutopilotRunListPage": AutopilotRunListPage,
        "CommentCursor": CommentCursor,
        "CursorLazyCollection": CursorLazyCollection,
        "CursorPage": CursorPage,
        "IssueChildrenResult": IssueChildrenResult,
        "IssueListFilter": IssueListFilter,
        "IssueListPage": IssueListPage,
        "LazyCollection": LazyCollection,
        "LazyMapping": LazyMapping,
        "LocalDirectoryResourceRef": LocalDirectoryResourceRef,
        "MetadataPage": MetadataPage,
        "OffsetLazyCollection": OffsetLazyCollection,
        "OffsetPage": OffsetPage,
        "ProjectResourceRecord": ProjectResourceRecord,
        "RelationMetadata": RelationMetadata,
        "RuntimeUpdateResult": RuntimeUpdateResult,
    }
    for name, value in dedicated_exports.items():
        assert name not in multica_py.__all__
        assert not hasattr(multica_py, name)
        assert name in models_pkg.__all__
        assert value is getattr(models_pkg, name)
    for name, value in {
        "CliResult": CliResult,
        "IssueListFilter": IssueListFilter,
        "IssueListPage": IssueListPage,
    }.items():
        assert name not in multica_py.__all__
        assert not hasattr(multica_py, name)
        assert value is not getattr(multica_py, name, None)


EXPECTED_ROOT_EXPORTS = (
    "ActionResult",
    "Agent",
    "AuthenticationError",
    "AuthorizationError",
    "Autopilot",
    "AutopilotRun",
    "ClientConfig",
    "Command",
    "CommandCancelledError",
    "CommandExecutionError",
    "CommandTimeoutError",
    "Comment",
    "CommentThread",
    "CompatibilityPolicy",
    "ConflictError",
    "DetachedEntityError",
    "EncodingError",
    "ExecutableNotFoundError",
    "ExecutableNotRunnableError",
    "Issue",
    "IssueStatus",
    "JsonOutputError",
    "Label",
    "ManagedProcess",
    "MissingPermalinkContextError",
    "MissingRelationContextError",
    "MulticaClient",
    "MulticaError",
    "NetworkError",
    "NotFoundError",
    "OperationOptions",
    "OutputShapeError",
    "Page",
    "ProcessOutputModeError",
    "ProcessResult",
    "Project",
    "ProjectStatus",
    "ProtocolError",
    "RelationError",
    "RelationPaginationError",
    "Skill",
    "Squad",
    "TaskRun",
    "UnknownCommandError",
    "UnloadedReferenceError",
    "Unset",
    "UnsupportedCliVersionError",
    "UnsupportedReferenceTargetError",
    "ValidationError",
    "Workspace",
    "WorkspaceMember",
)


def test_root_exports_match_curated_expected_table() -> None:
    import multica_py

    assert tuple(multica_py.__all__) == EXPECTED_ROOT_EXPORTS
    assert all(hasattr(multica_py, name) for name in EXPECTED_ROOT_EXPORTS)

    for removed_name in (
        "AgentCreateRequest",
        "AgentUpdateRequest",
        "ProjectCreateRequest",
        "ProjectUpdateRequest",
        "SkillCreateRequest",
        "SkillUpdateRequest",
        "CommentListFlatRequest",
        "CommentListRecentRequest",
        "CommentListThreadRequest",
        "IssueAssignmentRequest",
        "IssueCreateRequest",
        "IssueReorderRequest",
        "IssueUpdateRequest",
        "LabelUpdateRequest",
        "MetadataListRequest",
        "MetadataSetRequest",
        "ProjectResourceAddLocalDirectoryRequest",
        "ProjectResourceUpdateLocalDirectoryRequest",
        "AutopilotUpdateRequest",
        "AutopilotTriggerCreate",
        "AutopilotTriggerUpdate",
        "RuntimeUpdate",
        "UserProfileUpdate",
    ):
        assert removed_name not in multica_py.__all__
        assert removed_name not in models_pkg.__all__
        assert not hasattr(multica_py, removed_name)
        assert not hasattr(models_pkg, removed_name)


def test_canonical_entity_root_and_resource_identity() -> None:
    import multica_py
    from multica_py.entities import Agent, Issue, Project, Workspace
    from multica_py.resources.agents import Agent as ResourceAgent
    from multica_py.resources.issues import Issue as ResourceIssue
    from multica_py.resources.projects import Project as ResourceProject
    from multica_py.resources.workspaces import Workspace as ResourceWorkspace

    assert Agent is multica_py.Agent is ResourceAgent
    assert Issue is multica_py.Issue is ResourceIssue
    assert Project is multica_py.Project is ResourceProject
    assert Workspace is multica_py.Workspace is ResourceWorkspace


def test_process_exports_are_exactly_the_new_process_root_surface() -> None:
    import multica_py

    process_exports = {name for name in multica_py.__all__ if name.startswith("Process")}
    assert process_exports == {"ProcessOutputModeError", "ProcessResult"}
    assert multica_py.ProcessResult.__module__ == "multica_py.process"
    assert multica_py.ProcessOutputModeError.__module__ == "multica_py.exceptions"


def test_removed_request_flow_is_absent_from_package_sources() -> None:
    import inspect

    import multica_py
    import multica_py.resources as resources_pkg

    removed_names = (
        "AgentCreateRequest",
        "AgentUpdateRequest",
        "AutopilotUpdateRequest",
        "AutopilotTriggerCreate",
        "AutopilotTriggerUpdate",
        "CommentListFlatRequest",
        "CommentListRecentRequest",
        "CommentListThreadRequest",
        "IssueAssignmentRequest",
        "IssueCreateRequest",
        "IssueReorderRequest",
        "IssueUpdateRequest",
        "LabelUpdateRequest",
        "MetadataListRequest",
        "MetadataSetRequest",
        "ProjectCreateRequest",
        "ProjectResourceAddLocalDirectoryRequest",
        "ProjectResourceUpdateLocalDirectoryRequest",
        "ProjectUpdateRequest",
        "RuntimeUpdate",
        "SkillCreateRequest",
        "SkillUpdateRequest",
        "UserProfileUpdate",
    )
    for module_name, module in (("multica_py", multica_py),):
        source = inspect.getsource(module)
        assert "_resolve_request" not in source
        assert not any(
            re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", source)
            for name in removed_names
        ), module_name
    for module_info in pkgutil.walk_packages(
        resources_pkg.__path__, prefix="multica_py.resources."
    ):
        module = importlib.import_module(module_info.name)
        source = inspect.getsource(module)
        assert "_resolve_request" not in source, module_info.name
        assert not any(
            re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", source)
            for name in removed_names
        ), module_info.name


def test_public_model_annotations_are_closed() -> None:
    for model in (
        ActionResult,
        AutopilotListPage,
        AutopilotRunListPage,
        IssueChildrenResult,
        IssueListPage,
        Page,
    ):
        assert_public_annotations_precise(cast("type[object]", model))


def test_models_are_frozen() -> None:
    for modname, name, obj in _iter_struct_types():
        assert obj.__struct_config__.frozen, f"{name} in {modname} is not frozen"


def test_no_mutable_dict_defaults() -> None:
    for _modname, name, obj in _iter_struct_types():
        fields = obj.__struct_fields__
        defaults = cast("tuple[object, ...]", obj.__struct_defaults__)
        for field, default in zip(fields, defaults, strict=False):
            if isinstance(default, (dict, list)):
                raise TypeError(f"{name}.{field} has mutable default {type(default).__name__}")


def test_no_open_ended_container_fields() -> None:
    for _modname, name, obj in _iter_struct_types():
        fields = obj.__struct_fields__
        annotations = cast("dict[str, object]", obj.__annotations__)
        for fname in fields:
            ann = str(annotations.get(fname, ""))
            if "Any" in ann or "dict[" in ann or ann == "typing.Any" or ann == "<class 'object'>":
                raise TypeError(f"{name}.{fname}: {ann} is an open-ended container")


def assert_public_annotations_precise(public_class: type[object]) -> None:
    resolution_namespace: dict[str, object] = {
        "Issue": Issue,
        "MulticaClient": MulticaClient,
    }

    def assert_annotation(annotation: object, path: str) -> None:
        assert annotation is not Any, f"{path} contains Any"
        assert annotation is not object, f"{path} contains bare object"
        assert not isinstance(annotation, ForwardRef), (
            f"{path} contains unresolved forward reference"
        )
        if isinstance(annotation, TypeVar):
            return
        origin = get_origin(annotation)
        if origin is None:
            return
        assert get_args(annotation), f"{path} uses an unparameterized generic"
        assert origin is not types.UnionType or get_args(annotation), f"{path} is unresolved"
        for index, argument in enumerate(get_args(annotation)):
            assert_annotation(argument, f"{path}[{index}]")

    for name, member in inspect.getmembers(public_class):
        if name.startswith("_") and name != "__init__":
            continue
        callable_member = member.fget if isinstance(member, property) else member
        if not (inspect.isfunction(callable_member) or inspect.ismethod(callable_member)):
            continue
        module = inspect.getmodule(callable_member)
        assert module is not None, f"{public_class.__name__}.{name} has no module"
        if module.__name__ != public_class.__module__:
            continue
        globalns = cast("dict[str, object]", dict(vars(module)))
        globalns.update(resolution_namespace)
        hints = get_type_hints(callable_member, globalns=globalns)
        signature = inspect.signature(callable_member)
        for parameter in signature.parameters.values():
            if parameter.name not in {"self", "cls"}:
                assert parameter.name in hints, (
                    f"{public_class.__name__}.{name}.{parameter.name} is unannotated"
                )
        assert "return" in hints, f"{public_class.__name__}.{name} has no return annotation"
        for hint_name, annotation in hints.items():
            if hint_name == "kwargs" and annotation is object:
                continue
            assert_annotation(annotation, f"{public_class.__name__}.{name}.{hint_name}")
