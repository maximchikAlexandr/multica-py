from __future__ import annotations

import datetime
import pathlib

import msgspec

from multica_py.enums import IssueStatus, ProjectStatus
from multica_py.exceptions import OutputShapeError
from multica_py.models.autopilots import (
    Autopilot,
    AutopilotData,
    AutopilotListPage,
    AutopilotRun,
    AutopilotRunData,
    AutopilotRunListPage,
    AutopilotSubscriber,
    AutopilotTrigger,
    TriggerConfigItem,
)
from multica_py.models.issue_activity import Comment, CommentThread
from multica_py.models.issues import (
    Issue,
    IssueAssignee,
    IssueChildrenResult,
    IssueChildStageGroup,
    IssueData,
    IssueListPage,
    IssueMetadataItem,
    IssueSummary,
    LinkedPullRequest,
)
from multica_py.models.labels import LabelData
from multica_py.models.project_resources import LocalDirectoryResourceRef, ProjectResourceRecord
from multica_py.models.projects import Project
from multica_py.models.system import AttachmentResult
from multica_py.types import JsonValue, MetadataValue


class IssueSummaryWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    title: str
    status: IssueStatus
    priority: str | None = None
    created_at: datetime.datetime | None = None
    parent_issue_id: str | None = None
    project_id: str | None = None
    creator_id: str | None = None
    creator_type: str | None = None
    labels: tuple[LabelData, ...] | msgspec.UnsetType = msgspec.UNSET
    metadata: dict[str, MetadataValue] | msgspec.UnsetType = msgspec.UNSET


def issue_summary_from_wire(wire: IssueSummaryWire) -> IssueSummary:
    labels = () if wire.labels is msgspec.UNSET else wire.labels
    metadata = {} if wire.metadata is msgspec.UNSET else wire.metadata
    return IssueSummary(
        id=wire.id,
        title=wire.title,
        status=wire.status,
        priority=wire.priority,
        created_at=wire.created_at,
        parent_id=wire.parent_issue_id,
        project_id=wire.project_id,
        creator_id=wire.creator_id,
        creator_type=wire.creator_type,
        label_names=tuple(label.name for label in labels),
        metadata_snapshot=tuple(
            IssueMetadataItem(key=key, value=value) for key, value in metadata.items()
        ),
    )


class IssueListPageWire(msgspec.Struct, frozen=True, kw_only=True):
    issues: tuple[IssueSummaryWire, ...] = ()
    has_more: bool = False
    limit: int | None = None
    offset: int | None = None
    total: int | None = None


def issue_list_page_from_wire(wire: IssueListPageWire) -> IssueListPage:
    return IssueListPage(
        issues=tuple(issue_summary_from_wire(item) for item in wire.issues),
        has_more=wire.has_more,
        limit=wire.limit,
        offset=wire.offset,
        total=wire.total,
    )


class IssueWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    title: str
    description: str | None = None
    status: IssueStatus
    priority: str | None = None
    assignee: IssueAssignee | None = None
    pull_requests: tuple[LinkedPullRequest, ...] | msgspec.UnsetType = msgspec.UNSET
    children: tuple[IssueChildStageGroup, ...] | msgspec.UnsetType = msgspec.UNSET
    labels: tuple[LabelData, ...] | msgspec.UnsetType = msgspec.UNSET
    metadata: dict[str, MetadataValue] | msgspec.UnsetType = msgspec.UNSET
    attachments: tuple[AttachmentResult, ...] | msgspec.UnsetType = msgspec.UNSET
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    parent_issue_id: str | None = None
    project_id: str | None = None
    creator_id: str | None = None
    creator_type: str | None = (
        None  # ponytail: free string, no enum — upstream values not stabilised; add CreatorType enum when they are
    )


def _attachments_from_wire(wire: IssueWire) -> tuple[AttachmentResult, ...]:
    return () if wire.attachments is msgspec.UNSET else wire.attachments


def issue_data_from_wire(wire: IssueWire) -> IssueData:
    pull_requests = () if wire.pull_requests is msgspec.UNSET else wire.pull_requests
    children = () if wire.children is msgspec.UNSET else wire.children
    labels = () if wire.labels is msgspec.UNSET else wire.labels
    metadata = {} if wire.metadata is msgspec.UNSET else wire.metadata
    attachments = _attachments_from_wire(wire)
    return IssueData(
        id=wire.id,
        title=wire.title,
        description=wire.description,
        status=wire.status,
        priority=wire.priority,
        assignee=wire.assignee,
        pull_requests=pull_requests,
        child_stages=children,
        label_names=tuple(label.name for label in labels),
        metadata_snapshot=tuple(
            IssueMetadataItem(key=key, value=value) for key, value in metadata.items()
        ),
        attachments=attachments,
        created_at=wire.created_at,
        updated_at=wire.updated_at,
        parent_id=wire.parent_issue_id,
        project_id=wire.project_id,
        creator_id=wire.creator_id,
        creator_type=wire.creator_type,
    )


def issue_from_wire(wire: IssueWire) -> Issue:
    data = issue_data_from_wire(wire)
    return Issue(
        id=data.id,
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        assignee=data.assignee,
        pull_requests=data.pull_requests,
        children=data.child_stages,
        labels=data.label_names,
        metadata=data.metadata_snapshot,
        attachments=data.attachments,
        created_at=data.created_at,
        updated_at=data.updated_at,
        parent_id=data.parent_id,
        project_id=data.project_id,
        creator_id=data.creator_id,
        creator_type=data.creator_type,
    )


class IssueChildrenResultWire(msgspec.Struct, frozen=True, kw_only=True):
    children: tuple[IssueWire, ...] = ()
    total: int = 0
    child_stages: tuple[IssueChildStageGroup, ...] = ()
    unstaged: tuple[IssueWire, ...] = ()


def issue_children_result_from_wire(wire: IssueChildrenResultWire) -> IssueChildrenResult:
    return IssueChildrenResult(
        children=tuple(issue_from_wire(item) for item in wire.children),
        total=wire.total,
        child_stages=wire.child_stages,
        unstaged=tuple(issue_from_wire(item) for item in wire.unstaged),
    )


class IssuePullRequestsResultWire(msgspec.Struct, frozen=True, kw_only=True):
    pull_requests: tuple[LinkedPullRequest, ...] = ()


def issue_pull_requests_from_wire(
    wire: IssuePullRequestsResultWire,
) -> tuple[LinkedPullRequest, ...]:
    return wire.pull_requests


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


def autopilot_list_page_from_wire(wire: AutopilotListWire) -> AutopilotListPage[Autopilot]:
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
    subscribers: tuple[AutopilotSubscriberWire, ...] | msgspec.UnsetType = msgspec.UNSET
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
            for s in (() if wire.subscribers is msgspec.UNSET else wire.subscribers)
        ),
        can_write=wire.can_write,
        can_manage_access=wire.can_manage_access,
    )


class AutopilotGetWire(msgspec.Struct, frozen=True, kw_only=True):
    autopilot: AutopilotWire
    triggers: tuple[AutopilotTriggerWire, ...] | msgspec.UnsetType = msgspec.UNSET


class AutopilotGetResult:
    def __init__(
        self,
        data: AutopilotData,
        *,
        triggers: tuple[AutopilotTrigger, ...] | msgspec.UnsetType,
        subscribers: tuple[AutopilotSubscriber, ...] | msgspec.UnsetType,
    ) -> None:
        self.data = data
        self.triggers = triggers
        self.subscribers = subscribers


def _autopilot_subscribers(
    wire: tuple[AutopilotSubscriberWire, ...] | msgspec.UnsetType,
) -> tuple[AutopilotSubscriber, ...] | msgspec.UnsetType:
    if wire is msgspec.UNSET:
        return msgspec.UNSET
    return tuple(
        AutopilotSubscriber(
            user_type=item.user_type,
            user_id=item.user_id,
            created_at=item.created_at,
        )
        for item in wire
    )


def autopilot_data_from_wire(wire: AutopilotWire) -> AutopilotData:
    subscribers = _autopilot_subscribers(wire.subscribers)
    return AutopilotData(
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
        subscriber_snapshot=() if subscribers is msgspec.UNSET else subscribers,
        can_write=wire.can_write,
        can_manage_access=wire.can_manage_access,
    )


def autopilot_get_from_wire(wire: AutopilotGetWire) -> AutopilotGetResult:
    return AutopilotGetResult(
        autopilot_data_from_wire(wire.autopilot),
        triggers=(
            msgspec.UNSET
            if wire.triggers is msgspec.UNSET
            else tuple(trigger_from_wire(item) for item in wire.triggers)
        ),
        subscribers=_autopilot_subscribers(wire.autopilot.subscribers),
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
    trigger_payload: JsonValue | None = None
    result: JsonValue | None = None
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


def autopilot_run_data_from_model(run: AutopilotRun) -> AutopilotRunData:
    return AutopilotRunData(
        id=run.id,
        autopilot_id=run.autopilot_id,
        trigger_id=run.trigger_id,
        source=run.source,
        status=run.status,
        issue_id=run.issue_id,
        task_id=run.task_id,
        triggered_at=run.triggered_at,
        completed_at=run.completed_at,
        failure_reason=run.failure_reason,
        reason_code=run.reason_code,
        trigger_payload=run.trigger_payload,
        result=run.result,
        created_at=run.created_at,
    )


class AutopilotRunListPageWire(msgspec.Struct, frozen=True, kw_only=True):
    runs: tuple[AutopilotRunWire, ...] = ()
    total: int = 0


def autopilot_run_list_page_from_wire(
    wire: AutopilotRunListPageWire, *, limit: int | None = None, offset: int | None = None
) -> AutopilotRunListPage[AutopilotRun]:
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
