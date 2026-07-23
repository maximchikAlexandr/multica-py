from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from multica_py.models.labels import Label
from multica_py.models.projects import Project, ProjectCreateRequest, ProjectUpdateRequest
from tests.live.session import LiveSession

T = TypeVar("T")


@dataclass(frozen=True)
class CrudDescriptor(Generic[T]):
    """Declarative generic CRUD descriptor (spec §10, T061, T062)."""

    id: str
    profile: str
    create: Callable[..., T]
    identity: Callable[[T], str]
    get: Callable[..., T]
    update: Callable[..., T]
    delete: Callable[..., None]
    assert_created: Callable[[T], None]
    assert_fetched: Callable[..., None]
    assert_updated: Callable[..., None]
    assert_oracle: Callable[..., None]
    assert_deleted: Callable[..., None]


def _updated(prefix: str) -> str:
    return f"{prefix[:20]}-updated"


def _create_label(ctx: LiveSession, name: str) -> Label:
    return ctx.client.labels.create(name, color="#ff0000")


def _create_project(ctx: LiveSession, name: str) -> Project:
    return ctx.client.projects.create(ProjectCreateRequest(name=name))


def _get_label(ctx: LiveSession, label: Label) -> Label:
    return ctx.client.labels.get(str(label.id))


def _get_project(ctx: LiveSession, project: Project) -> Project:
    return ctx.client.projects.get(str(project.id))


def _update_label(ctx: LiveSession, label: Label) -> Label:
    label_id = str(label.id)
    return ctx.client.labels.update(label_id, name=_updated(label_id), color="#00ff00")


def _update_project(ctx: LiveSession, project: Project) -> Project:
    project_id = str(project.id)
    return ctx.client.projects.update(project_id, ProjectUpdateRequest(name=_updated(project_id)))


def _delete_label(ctx: LiveSession, label: Label) -> None:
    ctx.client.labels.delete(str(label.id))


def _delete_project(ctx: LiveSession, project: Project) -> None:
    ctx.client.projects.delete(str(project.id))


def _assert_created(obj: Label | Project) -> None:
    assert obj.id and obj.name


def _assert_same(fetched: Label | Project, created: Label | Project) -> None:
    assert fetched.id == created.id and fetched.name == created.name


def _assert_updated_state(fetched: Label | Project, updated: Label | Project) -> None:
    assert updated.id == fetched.id and updated.name != fetched.name


def _label_identity(label: Label) -> str:
    return str(label.id)


def _project_identity(project: Project) -> str:
    return str(project.id)


def _check(cond: bool) -> None:
    assert cond


CRUD_CASES: tuple[CrudDescriptor[Any], ...] = (
    CrudDescriptor(
        id="labels",
        profile="live_extended",
        create=_create_label,
        identity=_label_identity,
        get=_get_label,
        update=_update_label,
        delete=_delete_label,
        assert_created=_assert_created,
        assert_fetched=_assert_same,
        assert_updated=_assert_updated_state,
        assert_oracle=lambda api, label: _check(
            api.get(f"/api/labels/{label.id}").status_code in (200,)
        ),
        assert_deleted=lambda api, label: _check(
            api.get(f"/api/labels/{label.id}").status_code in (404, 204)
        ),
    ),
    CrudDescriptor(
        id="projects",
        profile="live_extended",
        create=_create_project,
        identity=_project_identity,
        get=_get_project,
        update=_update_project,
        delete=_delete_project,
        assert_created=_assert_created,
        assert_fetched=_assert_same,
        assert_updated=_assert_updated_state,
        assert_oracle=lambda api, proj: _check(
            api.get(f"/api/projects/{proj.id}").status_code in (200,)
        ),
        assert_deleted=lambda api, proj: _check(
            api.get(f"/api/projects/{proj.id}").status_code in (404, 204)
        ),
    ),
)
