from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

from multica_py.models.autopilots import AutopilotListPage
from multica_py.models.issues import IssueListPage
from multica_py.models.system import RepositoryRecord, RuntimeDefinition
from multica_py.resources.agents import Agent
from multica_py.resources.autopilots import Autopilot
from multica_py.resources.labels import Label
from multica_py.resources.skills import Skill
from multica_py.resources.squads import Squad
from multica_py.resources.workspaces import Workspace, WorkspaceMember


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
            issues=(), has_more=False, limit=50, offset=0, total=0
        )
    else:
        scoped.issues.list.side_effect = issues
    scoped.autopilots.list.return_value = autopilots or AutopilotListPage(autopilots=(), total=0)
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
