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
        project = prepared_client.projects.create_command(
            ProjectCreateRequest(name=_live_name())
        ).run()
        stack.callback(prepared_client.projects.delete_command(project.id).run)
        assert prepared_client.projects.get_command(project.id).run().id == project.id

        updated = prepared_client.projects.update_command(
            project.id, ProjectUpdateRequest(name=f"{project.name}-updated")
        ).run()
        assert updated.name == f"{project.name}-updated"
        assert prepared_client.projects.get_command(project.id).run().name == updated.name

        stack.close()
        with pytest.raises(NotFoundError):
            prepared_client.projects.get_command(project.id).run()


def test_comment_list(prepared_client: MulticaClient) -> None:
    with ExitStack() as stack:
        project = prepared_client.projects.create_command(
            ProjectCreateRequest(name=_live_name())
        ).run()
        stack.callback(prepared_client.projects.delete_command(project.id).run)
        issue = prepared_client.issues.create_command(
            IssueCreateRequest(title=_live_name(), project_id=project.id)
        ).run()
        comments = tuple(
            prepared_client.issues.comments.add_command(issue.id, f"comment-{index}").run()
            for index in range(3)
        )

        listed = prepared_client.issues.comments.list_command(issue.id).run()
        assert tuple(comment.id for comment in listed) == tuple(comment.id for comment in comments)


def test_not_found_mapping(prepared_client: MulticaClient) -> None:
    with pytest.raises(NotFoundError):
        prepared_client.projects.get_command(_ABSENT_PROJECT_ID).run()


def test_project_update_presence(prepared_client: MulticaClient) -> None:
    with ExitStack() as stack:
        project = prepared_client.projects.create_command(
            ProjectCreateRequest(name=_live_name(), description="before")
        ).run()
        stack.callback(prepared_client.projects.delete_command(project.id).run)

        omitted = prepared_client.projects.update_command(
            project.id, ProjectUpdateRequest(name=f"{project.name}-updated")
        ).run()
        assert omitted.description == "before"

        empty = prepared_client.projects.update_command(
            project.id, ProjectUpdateRequest(description="")
        ).run()
        assert empty.description == ""

        with (
            patch.object(prepared_client._transport, "run_bytes") as run_bytes,
            patch.object(prepared_client._transport, "run_text") as run_text,
        ):
            with pytest.raises(ValidationError):
                prepared_client.projects.update_command(
                    project.id, ProjectUpdateRequest(description=None)
                )
            run_bytes.assert_not_called()
            run_text.assert_not_called()


def test_bound_relation_graph(prepared_client: MulticaClient) -> None:
    workspace_id = os.environ["MULTICA_LIVE_WORKSPACE_ID"]
    workspace = prepared_client.workspaces.get_command(workspace_id).run()

    members = workspace.members.all_command().run()
    agents = workspace.agents.all_command().run()
    skills = workspace.skills.all_command().run()
    squads = workspace.squads.all_command().run()
    autopilots = workspace.autopilots.all_command().run()
    assert all(
        isinstance(snapshot, tuple) for snapshot in (members, agents, skills, squads, autopilots)
    )
    assert members, "prepared workspace must contain a member"
    assert agents, "prepared workspace must contain an agent"
    assert skills, "prepared workspace must contain a skill"
    assert squads, "prepared workspace must contain a squad"
    assert autopilots, "prepared workspace must contain an autopilot"

    issue_page = workspace.issues.page_command(limit=1).run()
    assert isinstance(issue_page.items, tuple)
    project_snapshot = workspace.projects.all_command().run()
    label_snapshot = workspace.labels.all_command().run()
    repository_snapshot = workspace.repositories.all_command().run()
    runtime_snapshot = workspace.runtimes.all_command().run()
    assert all(
        isinstance(snapshot, tuple)
        for snapshot in (project_snapshot, label_snapshot, repository_snapshot, runtime_snapshot)
    )

    first_workspace = prepared_client.workspaces.get_command(workspace_id).run()
    second_workspace = prepared_client.workspaces.get_command(workspace_id).run()
    assert first_workspace is not second_workspace
    assert first_workspace.id == second_workspace.id
    assert first_workspace.name == second_workspace.name
    prepared_client.prefetch(
        (first_workspace, second_workspace),  # type: ignore[type-var]
        lambda item: cast("LazyCollection[object]", item.members),
        max_parallel=2,
    )
    assert first_workspace.members.loaded
    assert second_workspace.members.loaded

    agent = prepared_client.agents.get_command(agents[0].id).run()
    agent.skills.all_command().run()
    agent.tasks.all_command().run()
    agent.issues.page_command(limit=1).run()

    skill = prepared_client.skills.get_command(skills[0].id).run()
    skill.files.all_command().run()

    squad = prepared_client.squads.get_command(squads[0].id).run()
    squad.members.all_command().run()
    squad.issues.page_command(limit=1).run()

    autopilot = prepared_client.autopilots.get_command(autopilots[0].id).run()
    autopilot.triggers.all_command().run()
    autopilot.subscribers.all_command().run()
    autopilot_runs = autopilot.runs.page_command(limit=20).run()
    assert isinstance(autopilot_runs.items, tuple)
    autopilot_run = next(
        (run for run in autopilot_runs.items if run.task_id is not None),
        None,
    )
    assert autopilot_run is not None, "prepared autopilot must have a run with task context"
    autopilot_run.messages.all_command().run()

    with ExitStack() as stack:
        project = prepared_client.projects.create_command(
            ProjectCreateRequest(name=_live_name())
        ).run()
        stack.callback(prepared_client.projects.delete_command(project.id).run)
        project_entity = prepared_client.projects.get_command(project.id).run()
        assert isinstance(project_entity.resources.all_command().run(), tuple)
        project_issue_page = project_entity.issues.page_command(limit=1).run()
        assert isinstance(project_issue_page.items, tuple)

        issue = prepared_client.issues.create_command(
            IssueCreateRequest(title=_live_name(), project_id=project.id)
        ).run()
        comments = issue.comments
        assert comments.all_command().run() == ()
        comment = issue.add_comment(_live_name())
        assert not comments.loaded
        comment_snapshot = comments.all_command().run()
        assert isinstance(comment_snapshot, tuple)
        assert comment.id in {item.id for item in comment_snapshot}

        recent_threads = issue.recent_comment_threads(limit=1)
        thread_page = recent_threads.page_command().run()
        assert thread_page.items, "new comment must appear in recent thread query"
        assert isinstance(thread_page.items, tuple)
        cast("_ThreadRelationOwner", thread_page.items[0]).comments.page_command().run()

        metadata_key = f"live_{uuid4().hex}"
        metadata = issue.metadata
        metadata.all_command().run()
        issue.set_metadata(metadata_key, "verified")
        assert not metadata.loaded
        assert metadata[metadata_key] == "verified"
        issue.delete_metadata(metadata_key)
        assert not metadata.loaded
        assert metadata_key not in metadata

        issue.labels.all_command().run()
        issue.subscribers.all_command().run()
        issue.pull_requests.all_command().run()
        issue.children.all_command().run()

        prepared_run = None
        for summary in workspace.issues.page_command(limit=50).run().items:
            candidate_runs = (
                prepared_client.issues.get_command(summary.id).run().runs.all_command().run()
            )
            if candidate_runs:
                prepared_run = candidate_runs[0]
                break
        assert prepared_run is not None, "prepared workspace must contain an issue task run"
        prepared_run.messages.all_command().run()

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
