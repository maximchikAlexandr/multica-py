from __future__ import annotations

from multica_py.enums import ProjectStatus
from multica_py.exceptions import DetachedEntityError
from multica_py.models import ResourceEntity
from multica_py.models.projects import ProjectData
from multica_py.models.relations import LazyCollection
from multica_py.resources.projects import Project

_PLANNED = ProjectStatus("planned")


def test_project_entity_to_data_is_immutable_snapshot() -> None:
    data = ProjectData(id="p1", name="Test", status=_PLANNED)
    entity = Project(data)
    assert entity.to_data() is data
    assert entity.to_data().id == "p1"
    assert entity.to_data().name == "Test"


def test_project_entity_from_data_returns_distinct_wrapper() -> None:
    data = ProjectData(id="p1", name="Test", status=_PLANNED)
    e1 = Project(data)
    e2 = Project(data)
    assert e1 is not e2
    assert e1.to_data() is e2.to_data()
    assert e1.id == e2.id
    assert e1.name == e2.name


def test_project_entity_list_get_return_distinct_wrappers() -> None:
    data_a = ProjectData(id="p1", name="A", status=_PLANNED)
    data_b = ProjectData(id="p1", name="A", status=_PLANNED)
    e1 = Project(data_a)
    e2 = Project(data_b)
    assert e1 is not e2
    assert e1.to_data() is not e2.to_data()
    assert e1.to_data() == e2.to_data()
    assert e1.id == e2.id
    assert e1.name == e2.name


def test_project_entity_no_cross_wrapper_lazy_state() -> None:
    data = ProjectData(id="p1", name="Test", status=_PLANNED)
    e1 = Project(data)
    e2 = Project(data)
    assert e1._resources is None
    assert e2._resources is None
    e1._resources = LazyCollection(lambda: ())
    assert e2._resources is None


def test_resource_entity_generic_works() -> None:
    data = ProjectData(id="p1", name="Test", status=_PLANNED)
    entity: ResourceEntity[ProjectData] = ResourceEntity(data)
    assert entity.to_data() is data
    restored = ResourceEntity.from_data(data)
    assert restored.to_data() == data
    assert entity.to_data() == restored.to_data()
    assert entity is not restored


def test_detached_entity_error_has_typed_fields() -> None:
    err = DetachedEntityError("Project", "p1", "resources")
    assert err.entity_type == "Project"
    assert err.entity_id == "p1"
    assert err.relation_name == "resources"
    assert "detached" in str(err).lower()
