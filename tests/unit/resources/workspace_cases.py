from __future__ import annotations

import datetime
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast
from unittest.mock import MagicMock

from multica_py._internal.commands import Command, _Step
from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.entities.agents import Agent
from multica_py.entities.autopilots import Autopilot
from multica_py.entities.labels import Label
from multica_py.entities.skills import Skill
from multica_py.entities.squads import Squad
from multica_py.entities.workspaces import Workspace, WorkspaceMember
from multica_py.models.autopilots import AutopilotListPage
from multica_py.models.issues import IssueListFilter, IssueListPage
from multica_py.models.relations import OffsetPage, RelationMetadata, _RelationLoad
from multica_py.models.system import RepositoryRecord, RuntimeDefinition
from multica_py.resources._base import BaseResource


@dataclass(frozen=True)
class WorkspaceClients:
    origin: MagicMock
    scoped: MagicMock


def make_workspace_clients(
    *,
    members: tuple[WorkspaceMember, ...] = (),
    agents: tuple[Agent, ...] = (),
    skills: tuple[Skill, ...] = (),
    projects: tuple[object, ...] = (),
    labels: tuple[Label, ...] = (),
    repositories: tuple[RepositoryRecord, ...] = (),
    runtimes: tuple[RuntimeDefinition, ...] = (),
    squads: tuple[Squad, ...] = (),
    issues: list[IssueListPage] | None = None,
    autopilots: AutopilotListPage[Autopilot] | None = None,
) -> WorkspaceClients:
    origin = MagicMock(name="origin_client")
    scoped = MagicMock(name="workspace_client")
    command_resource = BaseResource(MagicMock(spec=CliTransport), ClientConfig())

    def empty_command(loader: Callable[[], object]) -> Command[object]:
        return command_resource._plan(steps=(), finalize=lambda _results: loader())

    def direct_list_command(loader: Callable[[], object]) -> Callable[[], Command[object]]:
        return lambda: empty_command(loader)

    origin.with_workspace.return_value = scoped
    scoped.workspaces.members.return_value = members
    scoped.agents.list.return_value = agents
    scoped.skills.list.return_value = skills
    scoped.projects.list.return_value = projects
    scoped.labels.list.return_value = labels
    scoped.repositories.list.return_value = repositories
    scoped.runtimes.list.return_value = runtimes
    scoped.squads.list.return_value = squads
    if issues is None:
        scoped.issues.list.return_value = IssueListPage(
            items=(), has_more=False, limit=50, offset=0, total=0
        )
    else:
        scoped.issues.list.side_effect = issues
    scoped.autopilots.list.return_value = autopilots or AutopilotListPage(items=(), total=0)

    def issues_command(issue_filter: IssueListFilter) -> Command[object]:
        def decode(_stdout: bytes, command_text: str) -> object:
            words = command_text.split()
            offset = int(words[words.index("--offset") + 1])
            limit = int(words[words.index("--limit") + 1])
            request = IssueListFilter(
                assignee_id=issue_filter.assignee_id,
                limit=limit,
                offset=offset,
            )
            page = scoped.issues.list(request)
            return OffsetPage(
                items=page.items,
                total=page.total,
                limit=page.limit,
                offset=page.offset,
                has_more=page.has_more,
            )

        def run_bytes(argv: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
            return RawCommandResult(
                argv=argv,
                exit_code=0,
                stdout=b"",
                stderr=b"",
                duration=datetime.timedelta(),
            )

        cast("MagicMock", command_resource._transport.run_bytes).side_effect = run_bytes
        args = (
            "issue",
            "list",
            "--limit",
            str(issue_filter.limit),
            "--offset",
            str(issue_filter.offset),
            "--output",
            "json",
        )
        return command_resource._plan(
            steps=(_Step(args, "run_bytes", decode=decode),),
            finalize=lambda results: results[0],
        )

    scoped.issues.list_command = issues_command

    scoped.workspaces.members_command = lambda workspace_id: empty_command(
        lambda: scoped.workspaces.members(workspace_id)
    )
    scoped.agents.list_command = direct_list_command(scoped.agents.list)
    scoped.skills.list_command = direct_list_command(scoped.skills.list)
    scoped.projects.list_command = direct_list_command(scoped.projects.list)
    scoped.labels.list_command = direct_list_command(scoped.labels.list)
    scoped.repositories.list_command = direct_list_command(scoped.repositories.list)
    scoped.runtimes.list_command = direct_list_command(scoped.runtimes.list)
    scoped.squads.list_command = direct_list_command(scoped.squads.list)
    scoped.autopilots.list_command = direct_list_command(scoped.autopilots.list)

    scoped.workspaces._members_relation_command = scoped.workspaces.members_command
    scoped.workspaces._agents_relation_command = scoped.agents.list_command
    scoped.workspaces._skills_relation_command = scoped.skills.list_command
    scoped.workspaces._projects_relation_command = scoped.projects.list_command
    scoped.workspaces._labels_relation_command = scoped.labels.list_command
    scoped.workspaces._repositories_relation_command = scoped.repositories.list_command
    scoped.workspaces._runtimes_relation_command = scoped.runtimes.list_command
    scoped.workspaces._squads_relation_command = scoped.squads.list_command
    scoped.workspaces._issues_page_command = lambda assignee_id, limit, offset: issues_command(
        IssueListFilter(assignee_id=assignee_id, limit=limit, offset=offset)
    )
    scoped.workspaces._issues_page = lambda assignee_id, limit, offset: issues_command(
        IssueListFilter(assignee_id=assignee_id, limit=limit, offset=offset)
    ).run()

    def autopilots_relation() -> Command[object]:
        def load() -> _RelationLoad[Autopilot]:
            page = scoped.autopilots.list()
            return _RelationLoad(
                tuple(page.autopilots),
                RelationMetadata(total=page.total),
            )

        return empty_command(load)

    scoped.workspaces._autopilots_relation_command = autopilots_relation

    return WorkspaceClients(origin=origin, scoped=scoped)


def workspace_data() -> Workspace:
    return Workspace(id="ws_1", name="Test WS")


def workspace_relation_method(client: MagicMock, relation_name: str) -> MagicMock:
    dotted = {
        "members": "workspaces.members",
        "agents": "agents.list",
        "skills": "skills.list",
        "projects": "projects.list",
        "labels": "labels.list",
        "repositories": "repositories.list",
        "runtimes": "runtimes.list",
        "squads": "squads.list",
        "autopilots": "autopilots.list",
    }[relation_name]
    current = client
    for part in dotted.split("."):
        current = getattr(current, part)
    return current
