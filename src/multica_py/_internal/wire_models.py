from __future__ import annotations

import datetime
import pathlib

import msgspec

from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.exceptions import OutputShapeError
from multica_py.models.autopilots import (
    Autopilot,
    AutopilotListPage,
    AutopilotRun,
    AutopilotRunListPage,
    AutopilotSubscriber,
    AutopilotTrigger,
    TriggerConfigItem,
)
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
    parent_issue_id: str | None = None
    project_id: str | None = None
    creator_id: str | None = None
    creator_type: str | None = (
        None  # ponytail: free string, no enum — upstream values not stabilised; add CreatorType enum when they are
    )


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
        parent_id=wire.parent_issue_id,
        project_id=wire.project_id,
        creator_id=wire.creator_id,
        creator_type=wire.creator_type,
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
    autopilots: tuple[AutopilotWire, ...] = ()
    total: int = 0


def autopilot_list_page_from_wire(wire: AutopilotListWire) -> AutopilotListPage:
    return AutopilotListPage(
        autopilots=tuple(autopilot_from_wire(a) for a in wire.autopilots),
        total=wire.total,
    )


class AutopilotSubscriberWire(msgspec.Struct, frozen=True, kw_only=True):
    user_type: str
    user_id: str
    created_at: datetime.datetime | None = None


class AutopilotWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    workspace_id: str
    title: str
    description: str | None = None
    project_id: str | None = None
    assignee_type: str
    assignee_id: str
    status: str
    execution_mode: str
    issue_title_template: str | None = None
    created_by_type: str
    created_by_id: str
    last_run_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    trigger_kinds: tuple[str, ...] = ()
    next_run_at: datetime.datetime | None = None
    last_run_status: str | None = None
    subscribers: tuple[AutopilotSubscriberWire, ...] = ()
    can_write: bool | None = None
    can_manage_access: bool | None = None


def autopilot_from_wire(wire: AutopilotWire) -> Autopilot:
    return Autopilot(
        id=wire.id,
        workspace_id=wire.workspace_id,
        title=wire.title,
        description=wire.description,
        project_id=wire.project_id,
        assignee_type=wire.assignee_type,
        assignee_id=wire.assignee_id,
        status=wire.status,
        execution_mode=wire.execution_mode,
        issue_title_template=wire.issue_title_template,
        created_by_type=wire.created_by_type,
        created_by_id=wire.created_by_id,
        last_run_at=wire.last_run_at,
        created_at=wire.created_at,
        updated_at=wire.updated_at,
        trigger_kinds=wire.trigger_kinds,
        next_run_at=wire.next_run_at,
        last_run_status=wire.last_run_status,
        subscribers=tuple(
            AutopilotSubscriber(
                user_type=s.user_type,
                user_id=s.user_id,
                created_at=s.created_at,
            )
            for s in wire.subscribers
        ),
        can_write=wire.can_write,
        can_manage_access=wire.can_manage_access,
    )


class AutopilotRunWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    autopilot_id: str
    trigger_id: str | None = None
    source: str
    status: str
    issue_id: str | None = None
    task_id: str | None = None
    triggered_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    failure_reason: str | None = None
    reason_code: str | None = None
    trigger_payload: object | None = None
    result: object | None = None
    created_at: datetime.datetime | None = None


def autopilot_run_from_wire(wire: AutopilotRunWire) -> AutopilotRun:
    return AutopilotRun(
        id=wire.id,
        autopilot_id=wire.autopilot_id,
        trigger_id=wire.trigger_id,
        source=wire.source,
        status=wire.status,
        issue_id=wire.issue_id,
        task_id=wire.task_id,
        triggered_at=wire.triggered_at,
        completed_at=wire.completed_at,
        failure_reason=wire.failure_reason,
        reason_code=wire.reason_code,
        trigger_payload=wire.trigger_payload,
        result=wire.result,
        created_at=wire.created_at,
    )


class AutopilotRunListPageWire(msgspec.Struct, frozen=True, kw_only=True):
    runs: tuple[AutopilotRunWire, ...] = ()
    total: int = 0


def autopilot_run_list_page_from_wire(
    wire: AutopilotRunListPageWire, *, limit: int | None = None, offset: int | None = None
) -> AutopilotRunListPage:
    runs = tuple(autopilot_run_from_wire(r) for r in wire.runs)
    has_more = (offset or 0) + len(runs) < wire.total
    return AutopilotRunListPage(
        runs=runs,
        total=wire.total,
        limit=limit,
        offset=offset,
        has_more=has_more,
    )


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
