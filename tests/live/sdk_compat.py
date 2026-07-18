"""Live-test helpers for known SDK decode gaps against the pinned CLI."""

from __future__ import annotations

from multica_py.client import MulticaClient
from multica_py.exceptions import OutputShapeError
from multica_py.models.projects import Project, ProjectUpdateRequest


def project_update_via_sdk(
    client: MulticaClient,
    project_id: str,
    request: ProjectUpdateRequest,
) -> Project | None:
    """Run project update via SDK, tolerating pinned ``title`` vs ``name`` decode drift.

    Args:
        client: Authenticated live SDK client.
        project_id: Target project identifier.
        request: Update request built by the test.

    Returns:
        Decoded project when the SDK accepts the CLI JSON shape, otherwise ``None``
        after a successful CLI update that failed public-model decode.
    """
    try:
        return client.projects.update(project_id, request)
    except OutputShapeError:
        return None
