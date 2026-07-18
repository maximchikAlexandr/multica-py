from __future__ import annotations

import pytest

from multica_py.client import MulticaClient
from multica_py.models.projects import ProjectUpdateRequest
from tests.live.oracle import DirectApiOracle
from tests.live.sdk_compat import project_update_via_sdk
from tests.live.settings import label_name

pytestmark = [pytest.mark.live, pytest.mark.live_smoke]

BASE_TITLE = "oracle-base-title"
BASE_DESCRIPTION = "oracle-keep-me"


def test_sdk_create_label_fields_match_oracle_read(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource,
    resource_name: str,
) -> None:
    """SDK-created label fields must match independent oracle read."""
    name = label_name(resource_name, "ox")
    color = "#112233"
    created = live_client.labels.create(name, color=color)
    register_resource(
        key=f"label-{created.id}",
        cleanup=api_oracle.delete_callback(f"/api/labels/{created.id}", "label"),
    )
    oracle_label = api_oracle.get_label(created.id)
    assert oracle_label["name"] == name
    assert oracle_label["color"] == color
    assert oracle_label["id"] == created.id


def test_oracle_create_sdk_update_preserves_omitted_description(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource,
    resource_name: str,
) -> None:
    """Oracle-created project updated via SDK must preserve omitted description."""
    title = f"{resource_name}-{BASE_TITLE}"[:80]
    created = api_oracle.create_project(title, description=BASE_DESCRIPTION)
    project_id = str(created["id"])
    register_resource(
        key=f"project-{project_id}",
        cleanup=api_oracle.delete_callback(f"/api/projects/{project_id}", "project"),
    )
    project_update_via_sdk(live_client, project_id, ProjectUpdateRequest(name="sdk-only-title"))
    body = api_oracle.get_project(project_id)
    assert api_oracle.project_title(body) == "sdk-only-title"
    assert api_oracle.project_description(body) == BASE_DESCRIPTION


def test_sdk_delete_label_confirmed_absent_by_oracle(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource,
    resource_name: str,
) -> None:
    """SDK delete must leave label absent per independent oracle GET."""
    name = label_name(resource_name, "dx")
    created = live_client.labels.create(name, color="#445566")
    register_resource(
        key=f"label-{created.id}",
        cleanup=api_oracle.delete_callback(f"/api/labels/{created.id}", "label"),
    )
    assert api_oracle.get_label(created.id)["name"] == name
    live_client.labels.delete(created.id)
    api_oracle.assert_absent(f"/api/labels/{created.id}", "label")
