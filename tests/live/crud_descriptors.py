from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from multica_py.client import MulticaClient
from multica_py.models.projects import ProjectCreateRequest, ProjectUpdateRequest


@dataclass(frozen=True)
class CrudDescriptor:
    """One resource's generic CRUD round-trip.

    Attributes:
        create: Create via SDK, returns created model.
        get: Fetch by id via SDK.
        update: Update via SDK.
        delete: Delete via SDK.
        oracle_path: Backend path builder for oracle verification.
        name_builder: Produces a unique resource name from a session identity string.
        id: pytest.param id.
    """

    create: Callable[[MulticaClient, str], object]
    get: Callable[[MulticaClient, str], object]
    update: Callable[[MulticaClient, str], object]
    delete: Callable[[MulticaClient, str], None]
    oracle_path: Callable[[str], str]
    name_builder: Callable[[str], str]
    id: str


def _updated_name(prefix: str) -> str:
    return f"{prefix[:20]}-updated"


CRUD_DESCRIPTORS: tuple[CrudDescriptor, ...] = (
    CrudDescriptor(
        create=lambda c, n: c.labels.create(n, color="#ff0000"),
        get=lambda c, i: c.labels.get(i),
        update=lambda c, i: c.labels.update(i, name=_updated_name(i), color="#00ff00"),
        delete=lambda c, i: c.labels.delete(i),
        oracle_path=lambda i: f"/api/labels/{i}",
        name_builder=lambda uid: f"crud-lbl-{uid[:16]}",
        id="labels",
    ),
    CrudDescriptor(
        create=lambda c, n: c.projects.create(ProjectCreateRequest(name=n)),
        get=lambda c, i: c.projects.get(i),
        update=lambda c, i: c.projects.update(i, ProjectUpdateRequest(name=_updated_name(i))),
        delete=lambda c, i: c.projects.delete(i),
        oracle_path=lambda i: f"/api/projects/{i}",
        name_builder=lambda uid: f"crud-prj-{uid[:16]}",
        id="projects",
    ),
)
