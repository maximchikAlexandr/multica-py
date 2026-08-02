from __future__ import annotations

import json
import os
import subprocess
from contextlib import ExitStack
from typing import Protocol, cast
from unittest.mock import patch
from uuid import uuid4

import pytest

from multica_py.client import MulticaClient
from multica_py.exceptions import NotFoundError, ValidationError
from multica_py.models.issues import IssueCreateRequest
from multica_py.models.projects import ProjectCreateRequest, ProjectUpdateRequest
from multica_py.models.relations import CursorLazyCollection, LazyCollection

pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]

_ABSENT_PROJECT_ID = "00000000-0000-0000-0000-000000000000"


class _ThreadRelationOwner(Protocol):
    @property
    def comments(self) -> CursorLazyCollection[object]: ...


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


def test_bound_relation_graph(prepared_client: MulticaClient) -> None:
    workspace_id = os.environ["MULTICA_LIVE_WORKSPACE_ID"]
    workspace = prepared_client.workspaces.get(workspace_id)

    members = workspace.members.all()
    agents = workspace.agents.all()
    skills = workspace.skills.all()
    squads = workspace.squads.all()
    autopilots = workspace.autopilots.all()
    assert members, "prepared workspace must contain a member"
    assert agents, "prepared workspace must contain an agent"
    assert skills, "prepared workspace must contain a skill"
    assert squads, "prepared workspace must contain a squad"
    assert autopilots, "prepared workspace must contain an autopilot"

    workspace.issues.page(limit=1)
    workspace.projects.all()
    workspace.labels.all()
    workspace.repositories.all()
    workspace.runtimes.all()

    first_workspace = prepared_client.workspaces.get(workspace_id)
    second_workspace = prepared_client.workspaces.get(workspace_id)
    assert first_workspace is not second_workspace
    assert first_workspace.to_data() == second_workspace.to_data()
    prepared_client.prefetch(
        (first_workspace, second_workspace),
        lambda item: cast("LazyCollection[object]", item.members),
        max_parallel=2,
    )
    assert first_workspace.members.loaded
    assert second_workspace.members.loaded

    agent = prepared_client.agents.get(agents[0].id)
    agent.skills.all()
    agent.tasks.all()
    agent.issues.page(limit=1)

    skill = prepared_client.skills.get(skills[0].id)
    skill.files.all()

    squad = prepared_client.squads.get(squads[0].id)
    squad.members.all()
    squad.issues.page(limit=1)

    autopilot = prepared_client.autopilots.get(autopilots[0].id)
    autopilot.triggers.all()
    autopilot.subscribers.all()
    autopilot_runs = autopilot.runs.page(limit=20)
    autopilot_run = next(
        (run for run in autopilot_runs.items if run.task_id is not None),
        None,
    )
    assert autopilot_run is not None, "prepared autopilot must have a run with task context"
    autopilot_run.messages.all()

    with ExitStack() as stack:
        project = prepared_client.projects.create(ProjectCreateRequest(name=_live_name()))
        stack.callback(prepared_client.projects.delete, project.id)
        project_entity = prepared_client.projects.get(project.id)
        project_entity.resources.all()
        project_entity.issues.page(limit=1)

        issue = prepared_client.issues.create(
            IssueCreateRequest(title=_live_name(), project_id=project.id)
        )
        comments = issue.comments
        assert comments.all() == ()
        comment = issue.add_comment(_live_name())
        assert not comments.loaded
        assert comment.id in {item.id for item in comments.all()}

        recent_threads = issue.recent_comment_threads(limit=1)
        thread_page = recent_threads.page()
        assert thread_page.items, "new comment must appear in recent thread query"
        cast("_ThreadRelationOwner", thread_page.items[0]).comments.page()

        metadata_key = f"live_{uuid4().hex}"
        metadata = issue.metadata
        dict(metadata)
        issue.set_metadata(metadata_key, "verified")
        assert not metadata.loaded
        assert metadata[metadata_key] == "verified"
        issue.delete_metadata(metadata_key)
        assert not metadata.loaded
        assert metadata_key not in metadata

        issue.labels.all()
        issue.subscribers.all()
        issue.pull_requests.all()
        issue.children.all()

        prepared_run = None
        for summary in workspace.issues.page(limit=50).items:
            candidate_runs = prepared_client.issues.get(summary.id).runs.all()
            if candidate_runs:
                prepared_run = candidate_runs[0]
                break
        assert prepared_run is not None, "prepared workspace must contain an issue task run"
        prepared_run.messages.all()

        print(
            json.dumps(
                {
                    "live_relation_proof": {
                        "comment_id": comment.id,
                        "issue_id": issue.id,
                        "project_id": project.id,
                    }
                },
                sort_keys=True,
            )
        )
