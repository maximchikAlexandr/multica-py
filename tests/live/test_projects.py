from __future__ import annotations

from collections.abc import Callable

import pytest

from multica_py.client import MulticaClient
from multica_py.models.projects import ProjectUpdateRequest
from tests.live.oracle import DirectApiOracle

pytestmark = [pytest.mark.live, pytest.mark.live_smoke]

BASE_TITLE = "base-title"
BASE_DESCRIPTION = "keep-me"


def _create_presence_project(
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
) -> str:
    created = api_oracle.create_project(BASE_TITLE, description=BASE_DESCRIPTION)
    project_id = str(created["id"])
    register_resource(
        key=f"project-{project_id}",
        cleanup=api_oracle.delete_callback(f"/api/projects/{project_id}", "project"),
    )
    body = api_oracle.get_project(project_id)
    assert api_oracle.project_title(body) == BASE_TITLE
    assert api_oracle.project_description(body) == BASE_DESCRIPTION
    return project_id


def test_p_omit_update_title_only_preserves_description(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
) -> None:
    """Case P-OMIT: updating title without description leaves description unchanged."""
    project_id = _create_presence_project(api_oracle, register_resource)
    updated = live_client.projects.update(project_id, ProjectUpdateRequest(name="only-title"))
    assert updated.name == "only-title"
    body = api_oracle.get_project(project_id)
    assert api_oracle.project_title(body) == "only-title"
    assert api_oracle.project_description(body) == BASE_DESCRIPTION


def test_p_empty_clears_description_without_omit_semantics(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
) -> None:
    """Case P-EMPTY: explicit empty description differs from omitted description."""
    project_id = _create_presence_project(api_oracle, register_resource)
    live_client.projects.update(project_id, ProjectUpdateRequest(description=""))
    empty_body = api_oracle.get_project(project_id)
    assert api_oracle.project_description(empty_body) == ""
    assert api_oracle.project_title(empty_body) == BASE_TITLE
    live_client.projects.update(project_id, ProjectUpdateRequest(name="title-after-empty"))
    omit_body = api_oracle.get_project(project_id)
    assert api_oracle.project_title(omit_body) == "title-after-empty"
    assert api_oracle.project_description(omit_body) == ""


def test_p_null_http_clears_description_via_oracle_only(
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
) -> None:
    """Case P-NULL-HTTP: raw PUT null description documents backend clear semantics."""
    project_id = _create_presence_project(api_oracle, register_resource)
    api_oracle.update_project(project_id, {"description": None})
    body = api_oracle.get_project(project_id)
    assert api_oracle.project_description(body) is None
    assert api_oracle.project_title(body) == BASE_TITLE


def test_p_set_updates_description_and_updated_at_without_touching_unrelated_fields(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
) -> None:
    """Case P-SET: description update preserves unrelated fields and bumps updated_at."""
    project_id = _create_presence_project(api_oracle, register_resource)
    before = api_oracle.get_project(project_id)
    before_updated_at = before.get("updated_at")
    before_status = before.get("status")
    live_client.projects.update(project_id, ProjectUpdateRequest(description="new"))
    after = api_oracle.get_project(project_id)
    assert api_oracle.project_description(after) == "new"
    assert api_oracle.project_title(after) == BASE_TITLE
    if before_status is not None:
        assert after.get("status") == before_status
    if isinstance(before_updated_at, str) and isinstance(
        after_updated_at := after.get("updated_at"), str
    ):
        assert after_updated_at >= before_updated_at
