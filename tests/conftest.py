from __future__ import annotations

import pathlib

import pytest

_LAYER_MARKERS: dict[str, str] = {
    "tests/unit": "unit",
    "tests/contract": "contract",
    "tests/component": "component",
    "tests/packaging": "packaging",
    "tests/live": "live",
}
_LIVE_PROFILE_MARKERS = frozenset({"live_smoke", "live_extended", "live_opencode_canary"})


def _repo_relative_path(path: pathlib.Path) -> str:
    tests_root = pathlib.Path(__file__).parent
    repo_root = tests_root.parent
    return path.relative_to(repo_root).as_posix()


def _layer_marker_for_path(path: pathlib.Path) -> str | None:
    normalized = _repo_relative_path(path)
    for prefix, marker in _LAYER_MARKERS.items():
        if normalized.startswith(prefix + "/") or normalized == prefix:
            return marker
    return None


def _mark_name(mark: object) -> str | None:
    name = getattr(mark, "name", None)
    if isinstance(name, str):
        return name
    inner = getattr(mark, "mark", None)
    if isinstance(inner, pytest.Mark):
        return inner.name
    return None


def _module_markers(module: object) -> frozenset[str]:
    marks: set[str] = set()
    pytestmark = getattr(module, "pytestmark", ())
    if not pytestmark:
        return frozenset()
    if not isinstance(pytestmark, tuple | list):
        pytestmark = (pytestmark,)
    for mark in pytestmark:
        name = _mark_name(mark)
        if name is not None:
            marks.add(name)
    return frozenset(marks)


def _validate_live_module(module: object, module_file: pathlib.Path) -> None:
    marks = _module_markers(module)
    profiles = marks & _LIVE_PROFILE_MARKERS
    rel_path = _repo_relative_path(module_file)
    if "live" not in marks:
        raise pytest.UsageError(f"{rel_path} must declare pytest.mark.live")
    if len(profiles) != 1:
        raise pytest.UsageError(
            f"{rel_path} must declare exactly one live profile marker, got {sorted(profiles)}"
        )


def _validate_non_live_module(module: object, module_file: pathlib.Path) -> None:
    marks = _module_markers(module)
    profiles = marks & _LIVE_PROFILE_MARKERS
    if profiles:
        rel_path = _repo_relative_path(module_file)
        raise pytest.UsageError(
            f"{rel_path} must not declare live profile markers {sorted(profiles)}"
        )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    validated_modules: set[str] = set()
    for item in items:
        layer_marker = _layer_marker_for_path(item.path)
        if layer_marker is not None:
            item.add_marker(getattr(pytest.mark, layer_marker))
        module = getattr(item, "module", None)
        if module is None:
            continue
        module_name = module.__name__
        if module_name in validated_modules:
            continue
        validated_modules.add(module_name)
        module_file = pathlib.Path(module.__file__)
        layer = _layer_marker_for_path(module_file)
        if layer == "live":
            _validate_live_module(module, module_file)
        else:
            _validate_non_live_module(module, module_file)
