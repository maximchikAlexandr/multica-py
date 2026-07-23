from __future__ import annotations

import pytest

from multica_py.models.projects import ProjectUpdateRequest
from tests.live._live_helpers import label_name
from tests.live.session import LiveCase, LiveSession

pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]

BASE_TITLE = "oracle-base-title"
BASE_DESCRIPTION = "oracle-keep-me"


def test_sdk_create_label_fields_match_oracle_read(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """SDK-created label fields must match independent oracle read."""
    name = label_name(live_case.unique_name, "ox")
    color = "#112233"
    created = live_session.client.labels.create(name, color=color)
    live_case.defer_cleanup(
        live_session.oracle.delete_callback(f"/api/labels/{created.id}", "label"),
    )
    oracle_label = live_session.oracle.get_label(created.id)
    assert oracle_label["name"] == name
    assert oracle_label["color"] == color
    assert oracle_label["id"] == created.id


def test_oracle_create_sdk_update_preserves_omitted_description(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """Oracle-created project updated via SDK must preserve omitted description."""
    title = f"{live_case.unique_name}-{BASE_TITLE}"[:80]
    created = live_session.oracle.create_project(title, description=BASE_DESCRIPTION)
    project_id = str(created["id"])
    live_case.defer_cleanup(
        live_session.oracle.delete_callback(f"/api/projects/{project_id}", "project"),
    )
    updated = live_session.client.projects.update(
        project_id, ProjectUpdateRequest(name="sdk-only-title")
    )
    assert updated.name == "sdk-only-title"
    body = live_session.oracle.get_project(project_id)
    assert live_session.oracle.project_title(body) == "sdk-only-title"
    assert live_session.oracle.project_description(body) == BASE_DESCRIPTION


def test_sdk_delete_label_confirmed_absent_by_oracle(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """SDK delete must leave label absent per independent oracle GET."""
    name = label_name(live_case.unique_name, "dx")
    created = live_session.client.labels.create(name, color="#445566")
    live_case.defer_cleanup(
        live_session.oracle.delete_callback(f"/api/labels/{created.id}", "label"),
    )
    assert live_session.oracle.get_label(created.id)["name"] == name
    live_session.client.labels.delete(created.id)
    live_session.oracle.assert_absent(f"/api/labels/{created.id}", "label")
