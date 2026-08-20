from __future__ import annotations

from multica_py.client import MulticaClient
from multica_py.entities._base import _BoundEntity
from multica_py.entities.agents import Agent
from multica_py.entities.autopilots import Autopilot
from multica_py.entities.issues import Issue
from multica_py.entities.projects import Project
from multica_py.entities.squads import Squad
from multica_py.enums import IssueStatus, ProjectStatus


def issue_factory(
    client: MulticaClient,
    issue_id: str,
    *,
    parent_id: str | None = "parent-1",
) -> Issue:
    presence = () if parent_id is not None else (("parent_id", "null"),)
    return Issue(
        id=issue_id,
        title="Source",
        status=IssueStatus.todo,
        parent_id=parent_id,
        _wire_presence=presence,
        _client=client,
    )


def bound_entity_factory(
    client: MulticaClient,
    target_type: type[object] = Issue,
    target_id: str = "parent-1",
    *,
    title: str = "Target",
) -> _BoundEntity:
    if target_type is Issue:
        return Issue(id=target_id, title=title, status=IssueStatus.todo, _client=client)
    if target_type is Project:
        return Project(id=target_id, name=title, status=ProjectStatus.planned, _client=client)
    if target_type is Agent:
        return Agent(id=target_id, name=title, _client=client)
    if target_type is Squad:
        return Squad(id=target_id, name=title, _client=client)
    if target_type is Autopilot:
        return Autopilot(
            id=target_id,
            workspace_id="workspace-1",
            title=title,
            assignee_type="agent",
            assignee_id="agent-1",
            status="active",
            execution_mode="manual",
            created_by_type="member",
            created_by_id="member-1",
            _client=client,
        )
    raise AssertionError(f"unsupported target type: {target_type!r}")
