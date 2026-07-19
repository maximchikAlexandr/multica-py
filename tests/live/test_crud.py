from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import cast

import pytest

from multica_py.models.labels import Label
from multica_py.models.projects import Project
from tests.live.context import LiveContext
from tests.live.crud_descriptors import CRUD_DESCRIPTORS, CrudDescriptor

pytestmark = [pytest.mark.live, pytest.mark.live_extended]

_UNICODE_NAME_BUILDER: str = "日本語🏷️"


def _unicode_name(identity: str) -> str:
    tag = hashlib.sha256(identity.encode()).hexdigest()[:6]
    return f"  {tag}{_UNICODE_NAME_BUILDER}  "


@pytest.mark.parametrize(
    ("descriptor", "name_builder"),
    [(d, d.name_builder) for d in CRUD_DESCRIPTORS]
    + [(d, _unicode_name) for d in CRUD_DESCRIPTORS],
    ids=[d.id for d in CRUD_DESCRIPTORS] + [f"{d.id}.unicode" for d in CRUD_DESCRIPTORS],
)
def test_crud_round_trip(
    descriptor: CrudDescriptor,
    name_builder: Callable[[str], str],
    live_ctx: LiveContext,
) -> None:
    uid = live_ctx.identity.user_id
    name = name_builder(uid)
    created = descriptor.create(live_ctx.client, name)
    resource_id = str(cast("Label | Project", created).id)
    live_ctx.register_resource(
        key=f"{descriptor.id}-{resource_id}",
        cleanup=live_ctx.oracle.delete_callback(descriptor.oracle_path(resource_id), descriptor.id),
    )
    oracle_body = live_ctx.oracle.get(descriptor.oracle_path(resource_id))
    assert isinstance(oracle_body, dict)
    fetched = descriptor.get(live_ctx.client, resource_id)
    fetched_id = str(cast("Label | Project", fetched).id)
    assert fetched_id == resource_id
    descriptor.update(live_ctx.client, resource_id)
    oracle_after = live_ctx.oracle.get(descriptor.oracle_path(resource_id))
    assert isinstance(oracle_after, dict)
    descriptor.delete(live_ctx.client, resource_id)
    live_ctx.oracle.assert_absent(descriptor.oracle_path(resource_id), descriptor.id)
