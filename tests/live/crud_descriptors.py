from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import pytest

from multica_py.models.labels import Label
from multica_py.models.projects import Project, ProjectCreateRequest, ProjectUpdateRequest
from tests.live.environment import LiveContext

if TYPE_CHECKING:
    from tests.live.oracle import DirectApiOracle

CrudOperation = Literal["create", "get", "list", "update", "delete"]


@dataclass(frozen=True)
class CrudDescriptor:
    """Immutable live CRUD descriptor without orchestration logic."""

    resource_id: str
    operations: tuple[CrudOperation, ...]
    make_create_request: Callable[[str], object]
    make_update_request: Callable[[str, object], object]
    normalize: Callable[[object], object]
    fetch_oracle: Callable[[DirectApiOracle, str], dict[str, object]]
    register_cleanup: Callable[[LiveContext, str], None]
    case_marks: tuple[pytest.MarkDecorator, ...]
    capabilities: frozenset[str]


def _updated_name(prefix: str) -> str:
    return f"{prefix[:20]}-updated"


def _normalize_label(value: object) -> Label:
    assert isinstance(value, Label)
    return value


def _normalize_project(value: object) -> Project:
    assert isinstance(value, Project)
    return value


def _label_oracle(oracle: DirectApiOracle, resource_id: str) -> dict[str, object]:
    body = oracle.get(f"/api/labels/{resource_id}")
    assert isinstance(body, dict)
    return body


def _project_oracle(oracle: DirectApiOracle, resource_id: str) -> dict[str, object]:
    body = oracle.get(f"/api/projects/{resource_id}")
    assert isinstance(body, dict)
    return body


def _register_label_cleanup(ctx: LiveContext, resource_id: str) -> None:
    ctx.register_resource(
        key=f"labels-{resource_id}",
        cleanup=ctx.oracle.delete_callback(f"/api/labels/{resource_id}", "label"),
    )


def _register_project_cleanup(ctx: LiveContext, resource_id: str) -> None:
    ctx.register_resource(
        key=f"projects-{resource_id}",
        cleanup=ctx.oracle.delete_callback(f"/api/projects/{resource_id}", "project"),
    )


CRUD_DESCRIPTORS: tuple[CrudDescriptor, ...] = (
    CrudDescriptor(
        resource_id="labels",
        operations=("create", "get", "update", "delete"),
        make_create_request=lambda name: name,
        make_update_request=lambda resource_id, _: (
            resource_id,
            _updated_name(resource_id),
            "#00ff00",
        ),
        normalize=_normalize_label,
        fetch_oracle=_label_oracle,
        register_cleanup=_register_label_cleanup,
        case_marks=(pytest.mark.live, pytest.mark.live_extended, pytest.mark.serial),
        capabilities=frozenset({"naming"}),
    ),
    CrudDescriptor(
        resource_id="projects",
        operations=("create", "get", "update", "delete"),
        make_create_request=lambda name: ProjectCreateRequest(name=name),
        make_update_request=lambda resource_id, _: (
            resource_id,
            ProjectUpdateRequest(name=_updated_name(resource_id)),
        ),
        normalize=_normalize_project,
        fetch_oracle=_project_oracle,
        register_cleanup=_register_project_cleanup,
        case_marks=(pytest.mark.live, pytest.mark.live_extended, pytest.mark.serial),
        capabilities=frozenset({"naming", "presence"}),
    ),
)
