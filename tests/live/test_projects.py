from __future__ import annotations

from dataclasses import dataclass

import pytest

from multica_py.models.projects import ProjectUpdateRequest
from tests.live.session import LiveCase, LiveSession

pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]

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


def _create_presence_project(live_session: LiveSession) -> str:
    created = live_session.oracle.create_project(BASE_TITLE, description=BASE_DESCRIPTION)
    project_id = str(created["id"])
    live_session.defer_cleanup(
        live_session.oracle.delete_callback(f"/api/projects/{project_id}", "project")
    )
    body = live_session.oracle.get_project(project_id)
    assert live_session.oracle.project_title(body) == BASE_TITLE
    assert live_session.oracle.project_description(body) == BASE_DESCRIPTION
    return project_id


@pytest.mark.parametrize("case", PRESENCE_CASES, ids=lambda c: c.id)
def test_project_presence(
    case: PresenceCase,
    live_session: LiveSession,
) -> None:
    """Parametrized presence semantics: P-OMIT, P-EMPTY, P-SET."""
    project_id = _create_presence_project(live_session)
    live_session.client.projects.update(project_id, case.update_request)
    body = live_session.oracle.get_project(project_id)
    assert live_session.oracle.project_title(body) == case.expected_title
    assert live_session.oracle.project_description(body) == case.expected_description


def test_p_null_http_clears_description_via_oracle_only(
    live_session: LiveSession,
) -> None:
    """Case P-NULL-HTTP: raw PUT null description documents backend clear semantics."""
    project_id = _create_presence_project(live_session)
    live_session.oracle.update_project(project_id, {"description": None})
    body = live_session.oracle.get_project(project_id)
    assert live_session.oracle.project_description(body) is None
    assert live_session.oracle.project_title(body) == BASE_TITLE
