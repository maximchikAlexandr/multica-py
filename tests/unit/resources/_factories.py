from __future__ import annotations

import datetime
from collections.abc import Mapping

from multica_py.client import MulticaClient
from multica_py.entities._base import _BoundEntity
from multica_py.entities.agents import Agent
from multica_py.entities.autopilots import Autopilot
from multica_py.entities.issues import Issue
from multica_py.entities.projects import Project
from multica_py.entities.squads import Squad
from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.models.issue_activity import RunMessage
from multica_py.types import JsonValue


def make_run_message(
    *,
    seq: int,
    type: str = "text",
    task_id: str = "task_1",
    issue_id: str | None = "iss_1",
    tool: str | None = None,
    content: str | None = "m",
    input: Mapping[str, JsonValue] | None = None,
    output: str | None = None,
    created_at: datetime.datetime | None = None,
) -> RunMessage:
    return RunMessage(
        task_id=task_id,
        seq=seq,
        type=type,
        issue_id=issue_id,
        tool=tool,
        content=content,
        input=input,
        output=output,
        created_at=created_at,
    )


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
