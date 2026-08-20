from __future__ import annotations

import pytest

from multica_py.entities.projects import Project
from multica_py.enums import ProjectStatus
from multica_py.exceptions import (
    DetachedEntityError,
    UnloadedReferenceError,
    UnsupportedReferenceTargetError,
)
from multica_py.models.relations import LazyCollection

_PLANNED = ProjectStatus("planned")


def test_project_entity_to_data_is_immutable_snapshot() -> None:
    entity = Project(id="p1", name="Test", status=_PLANNED)
    assert entity.id == "p1"
    assert entity.name == "Test"


def test_project_entity_from_data_returns_distinct_wrapper() -> None:
    e1 = Project(id="p1", name="Test", status=_PLANNED)
    e2 = Project(id="p1", name="Test", status=_PLANNED)
    assert e1 is not e2
    assert e1.id == e2.id
    assert e1.name == e2.name


def test_project_entity_list_get_return_distinct_wrappers() -> None:
    e1 = Project(id="p1", name="A", status=_PLANNED)
    e2 = Project(id="p1", name="A", status=_PLANNED)
    assert e1 is not e2
    assert e1.id == e2.id
    assert e1.name == e2.name


def test_bound_entity_equality_is_type_safe() -> None:
    entity = Project(id="p1", name="Test", status=_PLANNED)

    assert entity.__eq__(object()) is NotImplemented


def test_bound_entity_rejects_unknown_runtime_field() -> None:
    entity = Project(id="p1", name="Test", status=_PLANNED)

    with pytest.raises(AttributeError, match="unsupported runtime field"):
        entity._set_runtime("_unknown", ())


def test_project_entity_no_cross_wrapper_lazy_state() -> None:
    e1 = Project(id="p1", name="Test", status=_PLANNED)
    e2 = Project(id="p1", name="Test", status=_PLANNED)
    assert e1._resources is None
    assert e2._resources is None
    e1._set_runtime("_resources", LazyCollection(lambda: ()))
    assert e2._resources is None


def test_detached_entity_error_has_typed_fields() -> None:
    err = DetachedEntityError("Project", "p1", "resources")
    assert err.entity_type == "Project"
    assert err.entity_id == "p1"
    assert err.relation_name == "resources"
    assert "detached" in str(err).lower()


def test_reference_errors_have_typed_fields_and_stable_messages() -> None:
    unloaded = UnloadedReferenceError("Issue", "i1", "project")
    assert unloaded.entity_type == "Issue"
    assert unloaded.entity_id == "i1"
    assert unloaded.relation_name == "project"
    assert unloaded.source_type == "Issue"
    assert unloaded.source_id == "i1"
    assert unloaded.reference_name == "project"
    assert unloaded.source == "Issue"
    assert unloaded.reference == "project"
    assert str(unloaded) == (
        "Cannot access Issue.project.value: reference is unloaded for Issue 'i1'. "
        "Call get() or prefetch() first."
    )

    unsupported = UnsupportedReferenceTargetError(
        "Issue", "i1", "assignee_ref", "assignee_type", "member"
    )
    assert unsupported.entity_type == "Issue"
    assert unsupported.entity_id == "i1"
    assert unsupported.relation_name == "assignee_ref"
    assert unsupported.discriminator == "assignee_type"
    assert unsupported.value == "member"
    assert unsupported.source_type == "Issue"
    assert unsupported.source_id == "i1"
    assert unsupported.reference_name == "assignee_ref"
    assert unsupported.source == "Issue"
    assert unsupported.reference == "assignee_ref"
    assert str(unsupported) == (
        "Cannot access Issue.assignee_ref: unsupported reference target "
        "assignee_type='member' for Issue 'i1'."
    )
