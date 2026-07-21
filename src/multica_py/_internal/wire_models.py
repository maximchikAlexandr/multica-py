from __future__ import annotations

import datetime
import pathlib

import msgspec

from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.exceptions import OutputShapeError
from multica_py.models.autopilots import Autopilot, AutopilotTrigger, TriggerConfigItem
from multica_py.models.issue_activity import Comment, CommentThread
from multica_py.models.issues import (
    Issue,
    IssueAssignee,
    IssueChildStageGroup,
    IssueMetadataItem,
    IssueSummary,
    LinkedPullRequest,
)
from multica_py.models.labels import Label
from multica_py.models.project_resources import LocalDirectoryResourceRef, ProjectResourceRecord
from multica_py.models.projects import Project
from multica_py.types import MetadataValue


class IssueSummaryWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    title: str
    status: IssueStatus
    priority: str | None = None


def issue_summary_from_wire(wire: IssueSummaryWire) -> IssueSummary:
    return IssueSummary(
        id=wire.id,
        title=wire.title,
        status=wire.status,
        priority=wire.priority,
    )


class IssueListPageWire(msgspec.Struct, frozen=True, kw_only=True):
    issues: tuple[IssueSummaryWire, ...] = ()


class IssueWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    title: str
    description: str | None = None
    status: IssueStatus
    priority: str | None = None
    assignee: IssueAssignee | None = None
    pull_requests: tuple[LinkedPullRequest, ...] = ()
    children: tuple[IssueChildStageGroup, ...] = ()
    labels: tuple[Label, ...] = ()
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
        labels=tuple(label.name for label in wire.labels),
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


class ProjectWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    title: str
    description: str | None = None
    status: ProjectStatus


def project_from_wire(wire: ProjectWire) -> Project:
    return Project(
        id=wire.id,
        name=wire.title,
        description=wire.description,
        status=wire.status,
    )


class CommentWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    content: str
    parent_id: str | None = None
    author_id: str | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


def comment_from_wire(wire: CommentWire) -> Comment:
    return Comment(
        id=wire.id,
        body=wire.content,
        thread_id=wire.parent_id,
        author_id=wire.author_id,
        created_at=wire.created_at,
        updated_at=wire.updated_at,
    )


class CommentThreadWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    comments: tuple[CommentWire, ...] = ()
    resolved: bool = False
    updated_at: datetime.datetime | None = None


def comment_thread_from_wire(wire: CommentThreadWire) -> CommentThread:
    return CommentThread(
        id=wire.id,
        comments=tuple(comment_from_wire(item) for item in wire.comments),
        resolved=wire.resolved,
        updated_at=wire.updated_at,
    )


class AutopilotListWire(msgspec.Struct, frozen=True, kw_only=True):
    autopilots: tuple[Autopilot, ...] = ()
    total: int = 0


class LocalDirectoryResourceRefWire(msgspec.Struct, frozen=True, kw_only=True):
    local_path: str
    daemon_id: str
    label: str | None = None


class ProjectResourceRecordWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    project_id: str
    resource_type: str
    resource_ref: LocalDirectoryResourceRefWire


def project_resource_from_wire(wire: ProjectResourceRecordWire) -> ProjectResourceRecord:
    if wire.resource_type != "local_directory":
        raise OutputShapeError(
            f"Unsupported resource_type {wire.resource_type!r}; expected 'local_directory'"
        )
    ref = wire.resource_ref
    if not pathlib.Path(ref.local_path).is_absolute():
        raise OutputShapeError("local_path must be an absolute path")
    return ProjectResourceRecord(
        id=wire.id,
        project_id=wire.project_id,
        resource_type=wire.resource_type,
        resource_ref=LocalDirectoryResourceRef(
            local_path=str(pathlib.Path(ref.local_path).resolve()),
            daemon_id=ref.daemon_id,
            label=ref.label,
        ),
    )
