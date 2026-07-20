from __future__ import annotations

import importlib
import inspect
import pkgutil
from collections.abc import Iterator
from types import ModuleType
from typing import TypeGuard, cast, get_type_hints

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
from multica_py.resources.project_resources import ProjectResourceCollection


def _assert_hint_clean(owner_name: str, callable_name: str, hints: dict[str, object]) -> None:
    for param_name, param_type in hints.items():
        type_str = str(param_type)
        assert "Any" not in type_str, (
            f"{owner_name}.{callable_name} parameter {param_name} uses Any"
        )
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
