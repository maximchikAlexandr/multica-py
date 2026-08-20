from typing import assert_type

from multica_py.entities.projects import Project
from multica_py.enums import ProjectStatus
from multica_py.models.relations import LazyRef

project = Project(id="project", name="Project", status=ProjectStatus("planned"))
required: LazyRef[Project] = LazyRef(lambda: project)
optional: LazyRef[Project | None] = LazyRef(lambda: None, initial=None)

required_value: Project = required.get()
optional_value: Project | None = optional.get()
assert_type(required_value, Project)
assert_type(optional_value, Project | None)

if required.loaded:
    assert_type(required.value, Project)
if optional.loaded:
    assert_type(optional.value, Project | None)
