from __future__ import annotations

from multica_py.enums import ProjectStatus
from multica_py.exceptions import DetachedEntityError
from multica_py.models.relations import LazyCollection
from multica_py.resources.projects import Project

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
