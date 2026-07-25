from __future__ import annotations

import json
import os
import subprocess
from contextlib import ExitStack
from unittest.mock import patch
from uuid import uuid4

import pytest

from multica_py.client import MulticaClient
from multica_py.exceptions import NotFoundError, ValidationError
from multica_py.models.issues import IssueCreateRequest
from multica_py.models.projects import ProjectCreateRequest, ProjectUpdateRequest

pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]

_ABSENT_PROJECT_ID = "00000000-0000-0000-0000-000000000000"


def _live_name() -> str:
    return f"multica-py-live-{uuid4().hex}"


def test_release_identity(prepared_client: MulticaClient) -> None:
    client_config = prepared_client.config
    result = subprocess.run(
        [str(client_config.executable), "version", "--output", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["version"] == os.environ["MULTICA_LIVE_EXPECTED_VERSION"]


def test_project_crud(prepared_client: MulticaClient) -> None:
    with ExitStack() as stack:
        project = prepared_client.projects.create(ProjectCreateRequest(name=_live_name()))
        stack.callback(prepared_client.projects.delete, project.id)
        assert prepared_client.projects.get(project.id).id == project.id

        updated = prepared_client.projects.update(
            project.id, ProjectUpdateRequest(name=f"{project.name}-updated")
        )
        assert updated.name == f"{project.name}-updated"
        assert prepared_client.projects.get(project.id).name == updated.name

        stack.close()
        with pytest.raises(NotFoundError):
            prepared_client.projects.get(project.id)


def test_comment_list(prepared_client: MulticaClient) -> None:
    with ExitStack() as stack:
        project = prepared_client.projects.create(ProjectCreateRequest(name=_live_name()))
        stack.callback(prepared_client.projects.delete, project.id)
        issue = prepared_client.issues.create(
            IssueCreateRequest(title=_live_name(), project_id=project.id)
        )
        comments = tuple(
            prepared_client.issues.comments.add(issue.id, f"comment-{index}") for index in range(3)
        )

        listed = prepared_client.issues.comments.list(issue.id)
        assert tuple(comment.id for comment in listed) == tuple(comment.id for comment in comments)


def test_not_found_mapping(prepared_client: MulticaClient) -> None:
    with pytest.raises(NotFoundError):
        prepared_client.projects.get(_ABSENT_PROJECT_ID)


def test_project_update_presence(prepared_client: MulticaClient) -> None:
    with ExitStack() as stack:
        project = prepared_client.projects.create(
            ProjectCreateRequest(name=_live_name(), description="before")
        )
        stack.callback(prepared_client.projects.delete, project.id)

        omitted = prepared_client.projects.update(
            project.id, ProjectUpdateRequest(name=f"{project.name}-updated")
        )
        assert omitted.description == "before"

        empty = prepared_client.projects.update(project.id, ProjectUpdateRequest(description=""))
        assert empty.description == ""

        with (
            patch.object(prepared_client._transport, "run_bytes") as run_bytes,
            patch.object(prepared_client._transport, "run_text") as run_text,
        ):
            with pytest.raises(ValidationError):
                prepared_client.projects.update(project.id, ProjectUpdateRequest(description=None))
            run_bytes.assert_not_called()
            run_text.assert_not_called()
