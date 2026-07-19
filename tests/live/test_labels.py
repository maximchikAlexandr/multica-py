from __future__ import annotations

import hashlib
from collections.abc import Callable

import pytest

from multica_py.client import MulticaClient
from tests.live.oracle import DirectApiOracle
from tests.live.settings import label_name

pytestmark = [pytest.mark.live, pytest.mark.live_smoke]


def test_label_crud_round_trip(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
) -> None:
    """Create, read, list, update, and delete one label via SDK with oracle checks."""
    name = label_name(resource_name, "crud")
    color = "#ff0000"
    created = live_client.labels.create(name, color=color)
    register_resource(
        key=f"label-{created.id}",
        cleanup=api_oracle.delete_callback(f"/api/labels/{created.id}", "label"),
    )
    oracle_created = api_oracle.get_label(created.id)
    assert oracle_created["name"] == name
    assert oracle_created["color"] == color
    fetched = live_client.labels.get(created.id)
    assert fetched.name == name
    assert fetched.color == color
    listed_ids = {label.id for label in live_client.labels.list()}
    assert created.id in listed_ids
    updated_name = label_name(resource_name, "upd")
    updated_color = "#00ff00"
    live_client.labels.update(created.id, name=updated_name, color=updated_color)
    oracle_updated = api_oracle.get_label(created.id)
    assert oracle_updated["name"] == updated_name
    assert oracle_updated["color"] == updated_color
    live_client.labels.delete(created.id)
    api_oracle.assert_absent(f"/api/labels/{created.id}", "label")


def test_label_unicode_emoji_spaces_and_exact_color(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
) -> None:
    """Round-trip label names with Unicode, emoji, spaces, and exact color values."""
    tag = hashlib.sha256(resource_name.encode()).hexdigest()[:6]
    raw_name = f"  {tag}日本語🏷️  "
    expected_name = raw_name.strip()
    color = "#a1b2c3"
    created = live_client.labels.create(raw_name, color=color)
    register_resource(
        key=f"label-{created.id}",
        cleanup=api_oracle.delete_callback(f"/api/labels/{created.id}", "label"),
    )
    oracle_label = api_oracle.get_label(created.id)
    assert oracle_label["name"] == expected_name
    assert oracle_label["color"] == color
    fetched = live_client.labels.get(created.id)
    assert fetched.name == expected_name
    assert fetched.color == color
    updated_name = label_name(resource_name, "u2")
    live_client.labels.update(created.id, name=updated_name)
    assert api_oracle.get_label(created.id)["name"] == updated_name
