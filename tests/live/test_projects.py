from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pytest

from multica_py.client import MulticaClient
from multica_py.models.projects import ProjectUpdateRequest
from tests.live.oracle import DirectApiOracle

pytestmark = [pytest.mark.live, pytest.mark.live_smoke]

BASE_TITLE = "base-title"
BASE_DESCRIPTION = "keep-me"


@dataclass(frozen=True)
class PresenceCase:
    """One update-request presence variant for project updates.

    Attributes:
        update_request: The SDK update payload.
        expected_title: Expected title after update.
        expected_description: Expected description after update.
        id: pytest.param id.
    """

    update_request: ProjectUpdateRequest
    expected_title: str
    expected_description: str | None
    id: str


PRESENCE_CASES: tuple[PresenceCase, ...] = (
    PresenceCase(
        update_request=ProjectUpdateRequest(name="only-title"),
        expected_title="only-title",
        expected_description=BASE_DESCRIPTION,
        id="P-OMIT",
    ),
    PresenceCase(
        update_request=ProjectUpdateRequest(description=""),
        expected_title=BASE_TITLE,
        expected_description="",
        id="P-EMPTY",
    ),
    PresenceCase(
        update_request=ProjectUpdateRequest(description="new"),
        expected_title=BASE_TITLE,
        expected_description="new",
        id="P-SET",
    ),
)


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


@pytest.mark.parametrize("case", PRESENCE_CASES, ids=lambda c: c.id)
def test_project_presence(
    case: PresenceCase,
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    resource_name: str,
) -> None:
    """Parametrized presence semantics: P-OMIT, P-EMPTY, P-SET."""
    project_id = _create_presence_project(api_oracle, register_resource)
    live_client.projects.update(project_id, case.update_request)
    body = api_oracle.get_project(project_id)
    assert api_oracle.project_title(body) == case.expected_title
    assert api_oracle.project_description(body) == case.expected_description


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
