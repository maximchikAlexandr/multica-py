from __future__ import annotations

import pathlib

import pytest

_LAYER_MARKERS: dict[str, str] = {
    "tests/unit": "unit",
    "tests/contract": "contract",
    "tests/component": "component",
    "tests/packaging": "packaging",
}


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


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        layer_marker = _layer_marker_for_path(item.path)
        if layer_marker is not None:
            item.add_marker(getattr(pytest.mark, layer_marker))
