from __future__ import annotations

import importlib
import inspect
import pkgutil
import types
from collections.abc import Iterator
from types import ModuleType
from typing import Any, ForwardRef, TypeGuard, TypeVar, cast, get_args, get_origin, get_type_hints

import msgspec

import multica_py.models as models_pkg
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.models.project_resources import (
    LocalDirectoryResourceRef,
    ProjectResourceAddLocalDirectoryRequest,
    ProjectResourceRecord,
    ProjectResourceUpdateLocalDirectoryRequest,
)
from multica_py.resources.issues import Issue
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

    exports = {
        "LocalDirectoryResourceRef": LocalDirectoryResourceRef,
        "ProjectResourceAddLocalDirectoryRequest": ProjectResourceAddLocalDirectoryRequest,
        "ProjectResourceRecord": ProjectResourceRecord,
        "ProjectResourceUpdateLocalDirectoryRequest": ProjectResourceUpdateLocalDirectoryRequest,
    }
    for name, model in exports.items():
        assert getattr(multica_py, name) is model


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
            assert_annotation(annotation, f"{public_class.__name__}.{name}.{hint_name}")
