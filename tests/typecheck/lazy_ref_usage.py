from typing import assert_type, cast

from multica_py._internal.commands import Command
from multica_py.client import MulticaClient
from multica_py.entities.projects import Project
from multica_py.enums import ProjectStatus
from multica_py.models.relations import LazyRef

project = Project(id="project", name="Project", status=ProjectStatus("planned"))
project_command = cast("Command[Project]", object())
optional_command = cast("Command[Project | None]", object())
required: LazyRef[Project] = LazyRef(command_loader=lambda: project_command)
optional: LazyRef[Project | None] = LazyRef(command_loader=lambda: optional_command, initial=None)

required_value: Project = required.get()
optional_value: Project | None = optional.get()
assert_type(required_value, Project)
assert_type(optional_value, Project | None)

if required.loaded:
    assert_type(required.value, Project)
if optional.loaded:
    assert_type(optional.value, Project | None)

client = MulticaClient()
client.prefetch((project,), lambda item: item.issues)
