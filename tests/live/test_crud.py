from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import cast

import pytest

from multica_py.models.labels import Label
from multica_py.models.projects import Project, ProjectCreateRequest, ProjectUpdateRequest
from tests.live.crud_descriptors import CRUD_DESCRIPTORS, CrudDescriptor
from tests.live.environment import LiveContext

pytestmark = [pytest.mark.live, pytest.mark.live_extended, pytest.mark.serial]

_UNICODE_NAME_BUILDER: str = "日本語🏷️"


def _unicode_name(identity: str) -> str:
    tag = hashlib.sha256(identity.encode()).hexdigest()[:6]
    return f"  {tag}{_UNICODE_NAME_BUILDER}  "


def _create_resource(descriptor: CrudDescriptor, live_ctx: LiveContext, name: str) -> object:
    payload = descriptor.make_create_request(name)
    if descriptor.resource_id == "labels":
        return live_ctx.client.labels.create(str(payload), color="#ff0000")
    assert isinstance(payload, ProjectCreateRequest)
    return live_ctx.client.projects.create(payload)


def _update_resource(descriptor: CrudDescriptor, live_ctx: LiveContext, resource: object) -> None:
    normalized = descriptor.normalize(resource)
    resource_id = str(cast("Label | Project", normalized).id)
    update_payload = descriptor.make_update_request(resource_id, normalized)
    if descriptor.resource_id == "labels":
        label_id, label_name, label_color = cast(
            "tuple[str, str, str]",
            update_payload,
        )
        live_ctx.client.labels.update(label_id, name=label_name, color=label_color)
        return
    project_id, project_update = cast(
        "tuple[str, ProjectUpdateRequest]",
        update_payload,
    )
    live_ctx.client.projects.update(project_id, project_update)


def _get_resource(descriptor: CrudDescriptor, live_ctx: LiveContext, resource_id: str) -> object:
    if descriptor.resource_id == "labels":
        return live_ctx.client.labels.get(resource_id)
    return live_ctx.client.projects.get(resource_id)


def _delete_resource(descriptor: CrudDescriptor, live_ctx: LiveContext, resource_id: str) -> None:
    if descriptor.resource_id == "labels":
        live_ctx.client.labels.delete(resource_id)
        return
    live_ctx.client.projects.delete(resource_id)


@pytest.mark.parametrize(
    ("descriptor", "name_builder"),
    [
        (CRUD_DESCRIPTORS[0], lambda uid: f"crud-lbl-{uid[:16]}"),
        (CRUD_DESCRIPTORS[1], lambda uid: f"crud-prj-{uid[:16]}"),
    ]
    + [(d, _unicode_name) for d in CRUD_DESCRIPTORS],
    ids=[d.resource_id for d in CRUD_DESCRIPTORS]
    + [f"{d.resource_id}.unicode" for d in CRUD_DESCRIPTORS],
)
def test_crud_round_trip(
    descriptor: CrudDescriptor,
    name_builder: Callable[[str], str],
    live_ctx: LiveContext,
) -> None:
    uid = live_ctx.identity.user_id
    name = name_builder(uid)
    created = _create_resource(descriptor, live_ctx, name)
    normalized = descriptor.normalize(created)
    resource_id = str(cast("Label | Project", normalized).id)
    descriptor.register_cleanup(live_ctx, resource_id)
    descriptor.fetch_oracle(live_ctx.oracle, resource_id)
    if "get" in descriptor.operations:
        fetched = _get_resource(descriptor, live_ctx, resource_id)
        fetched_id = str(cast("Label | Project", descriptor.normalize(fetched)).id)
        assert fetched_id == resource_id
    if "update" in descriptor.operations:
        _update_resource(descriptor, live_ctx, normalized)
        descriptor.fetch_oracle(live_ctx.oracle, resource_id)
    if "delete" in descriptor.operations:
        _delete_resource(descriptor, live_ctx, resource_id)
        live_ctx.oracle.assert_absent(
            f"/api/{descriptor.resource_id}/{resource_id}",
            descriptor.resource_id,
        )
