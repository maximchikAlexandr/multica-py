"""Registry/source-AST tests for tests.live.crud_descriptors (T063)."""

from __future__ import annotations

import ast
import pathlib

import pytest

from tests.live.crud_descriptors import CRUD_CASES, CrudDescriptor

CRUD_DESCRIPTORS_PATH = pathlib.Path(__file__).resolve().parents[1] / "live" / "crud_descriptors.py"
# fmt: off
_CALLABLE_FIELDS = frozenset(["create", "identity", "get", "update", "delete", "assert_created", "assert_fetched", "assert_updated", "assert_oracle", "assert_deleted"])
# fmt: on


def test_registry_unique_ids() -> None:
    ids = [d.id for d in CRUD_CASES]
    assert len(ids) == len(set(ids)) and CRUD_CASES


def test_descriptor_field_invariants() -> None:
    registry_ids = {id(d) for d in CRUD_CASES}
    for desc in CRUD_CASES:
        assert isinstance(desc, CrudDescriptor)
        assert isinstance(desc.profile, str) and desc.profile
        for field_name in _CALLABLE_FIELDS:
            value = getattr(desc, field_name)
            assert callable(value) and id(value) not in registry_ids


def test_no_identity_branch_in_source() -> None:
    forbidden = {"labels", "projects", "label", "project"}
    tree = ast.parse(CRUD_DESCRIPTORS_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        for comparator in node.comparators:
            if (
                isinstance(comparator, ast.Constant)
                and isinstance(comparator.value, str)
                and comparator.value in forbidden
            ):
                pytest.fail(f"identity branch on {comparator.value!r} at line {node.lineno}")
