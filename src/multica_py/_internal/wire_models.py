from __future__ import annotations

import datetime

import msgspec

from multica_py.enums import IssueStatus
from multica_py.models.autopilots import AutopilotTrigger, TriggerConfigItem
from multica_py.models.issues import (
    Issue,
    IssueAssignee,
    IssueChildStageGroup,
    IssueMetadataItem,
    LinkedPullRequest,
)
from multica_py.types import MetadataValue


class IssueWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    title: str
    description: str | None = None
    status: IssueStatus
    priority: str | None = None
    assignee: IssueAssignee | None = None
    pull_requests: tuple[LinkedPullRequest, ...] = ()
    children: tuple[IssueChildStageGroup, ...] = ()
    labels: tuple[str, ...] = ()
    metadata: dict[str, MetadataValue] = msgspec.field(default_factory=dict)
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


def issue_from_wire(wire: IssueWire) -> Issue:
    return Issue(
        id=wire.id,
        title=wire.title,
        description=wire.description,
        status=wire.status,
        priority=wire.priority,
        assignee=wire.assignee,
        pull_requests=wire.pull_requests,
        children=wire.children,
        labels=wire.labels,
        metadata=tuple(
            IssueMetadataItem(key=key, value=value) for key, value in wire.metadata.items()
        ),
        created_at=wire.created_at,
        updated_at=wire.updated_at,
    )


class AutopilotTriggerWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    type: str
    config: dict[str, str] = msgspec.field(default_factory=dict)


def trigger_from_wire(wire: AutopilotTriggerWire) -> AutopilotTrigger:
    return AutopilotTrigger(
        id=wire.id,
        type=wire.type,
        config=tuple(TriggerConfigItem(key=key, value=value) for key, value in wire.config.items()),
    )
