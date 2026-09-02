from __future__ import annotations

import datetime
import pathlib
from collections.abc import Mapping
from typing import TYPE_CHECKING, Literal, cast

import msgspec

from multica_py._generated.approved_sdk import validate_since_cursor
from multica_py._internal.decoders import decode_json
from multica_py._internal.json_values import _coerce_json_value
from multica_py.enums import ProjectStatus, _coerce_issue_status
from multica_py.exceptions import OutputShapeError
from multica_py.models.autopilots import (
    AutopilotListPage,
    AutopilotRunListPage,
    AutopilotSubscriber,
    AutopilotTrigger,
    TriggerConfigItem,
)
from multica_py.models.common import CommentCursor
from multica_py.models.issues import (
    IssueAssignee,
    IssueChildrenResult,
    IssueChildStageGroup,
    IssueListPage,
    IssueMetadataItem,
    LinkedPullRequest,
)
from multica_py.models.plugins import Plugin, PluginDigest
from multica_py.models.project_resources import LocalDirectoryResourceRef, ProjectResourceRecord
from multica_py.models.properties import PropertyDefinition
from multica_py.models.system import AttachmentResult
from multica_py.types import JsonValue, MetadataValue

if TYPE_CHECKING:
    from multica_py.entities.autopilots import Autopilot, AutopilotRun
    from multica_py.entities.comments import Comment, CommentThread
    from multica_py.entities.issues import Issue, TaskRun
    from multica_py.entities.projects import Project
    from multica_py.models.issue_activity import RunMessage


class _LabelWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    color: str | None = None


class _IssueWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    title: str
    description: str | None = None
    status: str
    priority: str | None = None
    assignee: IssueAssignee | None | msgspec.UnsetType = msgspec.UNSET
    assignee_id: str | None | msgspec.UnsetType = msgspec.UNSET
    assignee_type: str | None | msgspec.UnsetType = msgspec.UNSET
    pull_requests: tuple[LinkedPullRequest, ...] | msgspec.UnsetType = msgspec.UNSET
    children: tuple[IssueChildStageGroup, ...] | msgspec.UnsetType = msgspec.UNSET
    labels: tuple[_LabelWire, ...] | msgspec.UnsetType = msgspec.UNSET
    metadata: dict[str, MetadataValue] | msgspec.UnsetType = msgspec.UNSET
    attachments: tuple[AttachmentResult, ...] | msgspec.UnsetType = msgspec.UNSET
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    parent_issue_id: str | None | msgspec.UnsetType = msgspec.UNSET
    project_id: str | None | msgspec.UnsetType = msgspec.UNSET
    creator_id: str | None = None
    creator_type: str | None = (
        None  # ponytail: free string, no enum — upstream values not stabilised; add CreatorType enum when they are
    )
    match_source: str | None = None


class _IssueListPageWire(msgspec.Struct, frozen=True, kw_only=True):
    issues: tuple[_IssueWire, ...] = ()
    has_more: bool = False
    limit: int | None = None
    offset: int | None = None
    total: int | None = None
    next_cursor: str | CommentCursor | None = None


class _IssueSearchResultWire(msgspec.Struct, frozen=True, kw_only=True):
    issues: tuple[_IssueWire, ...]
    total: int | None = None


def _issue_list_page_from_wire(wire: _IssueListPageWire) -> IssueListPage:
    return IssueListPage(
        items=tuple(_issue_from_wire(item) for item in wire.issues),
        has_more=wire.has_more,
        limit=wire.limit,
        offset=wire.offset,
        total=wire.total,
        next_cursor=wire.next_cursor,
    )


def _attachments_from_wire(wire: _IssueWire) -> tuple[AttachmentResult, ...]:
    return () if wire.attachments is msgspec.UNSET else wire.attachments


_PresenceSeed = Literal["missing", "null", "value"]


def _presence_seed(value: object) -> _PresenceSeed:
    if value is msgspec.UNSET:
        return "missing"
    if value is None:
        return "null"
    return "value"


def _issue_from_wire(wire: _IssueWire) -> Issue:
    from multica_py.entities.issues import Issue

    assignee, assignee_presence = _issue_assignee_from_wire(wire)
    pull_requests = () if wire.pull_requests is msgspec.UNSET else wire.pull_requests
    children = () if wire.children is msgspec.UNSET else wire.children
    labels = () if wire.labels is msgspec.UNSET else wire.labels
    metadata = {} if wire.metadata is msgspec.UNSET else wire.metadata
    attachments = _attachments_from_wire(wire)
    return Issue(
        id=wire.id,
        title=wire.title,
        description=wire.description,
        status=_coerce_issue_status(wire.status),
        priority=wire.priority,
        assignee=assignee,
        pull_request_snapshot=pull_requests,
        child_stages=children,
        label_names=tuple(label.name for label in labels),
        metadata_snapshot=tuple(
            IssueMetadataItem(key=key, value=value) for key, value in metadata.items()
        ),
        attachments=attachments,
        created_at=wire.created_at,
        updated_at=wire.updated_at,
        parent_id=None if wire.parent_issue_id is msgspec.UNSET else wire.parent_issue_id,
        project_id=None if wire.project_id is msgspec.UNSET else wire.project_id,
        creator_id=wire.creator_id,
        creator_type=wire.creator_type,
        match_source=wire.match_source,
        _wire_presence=(
            ("parent_id", _presence_seed(wire.parent_issue_id)),
            ("project_id", _presence_seed(wire.project_id)),
            ("assignee", assignee_presence),
        ),
    )


def _issue_assignee_from_wire(wire: _IssueWire) -> tuple[IssueAssignee | None, _PresenceSeed]:
    scalar_id_present = wire.assignee_id is not msgspec.UNSET
    scalar_type_present = wire.assignee_type is not msgspec.UNSET
    if scalar_id_present != scalar_type_present:
        raise OutputShapeError(
            "issue assignee scalar projection must contain both assignee_id and assignee_type"
        )

    nested_present = wire.assignee is not msgspec.UNSET
    scalar_present = scalar_id_present and scalar_type_present
    scalar: IssueAssignee | None = None
    if scalar_present:
        if (wire.assignee_id is None) != (wire.assignee_type is None):
            raise OutputShapeError(
                "issue assignee scalar projection must contain two values or two nulls"
            )
        if wire.assignee_id is not None and wire.assignee_type is not None:
            scalar = IssueAssignee(
                id=cast("str", wire.assignee_id), type=cast("str", wire.assignee_type)
            )

    nested = None if wire.assignee is msgspec.UNSET else wire.assignee
    if nested_present and scalar_present:
        if nested is None and scalar is None:
            return None, "null"
        if nested is None or scalar is None or nested.id != scalar.id or nested.type != scalar.type:
            raise OutputShapeError("issue assignee projections conflict")
        return nested, "value"
    if nested_present:
        return nested, _presence_seed(wire.assignee)
    if scalar_present:
        return scalar, "null" if scalar is None else "value"
    return None, "missing"


class _IssueChildrenResultWire(msgspec.Struct, frozen=True, kw_only=True):
    children: tuple[_IssueWire, ...] = ()
    total: int = 0
    child_stages: tuple[IssueChildStageGroup, ...] = ()
    unstaged: tuple[_IssueWire, ...] = ()
    limit: int | None = None
    offset: int | None = None
    has_more: bool = False
    next_cursor: str | CommentCursor | None = None


def _issue_children_result_from_wire(wire: _IssueChildrenResultWire) -> IssueChildrenResult:
    return IssueChildrenResult(
        items=tuple(_issue_from_wire(item) for item in wire.children),
        total=wire.total,
        child_stages=wire.child_stages,
        unstaged=tuple(_issue_from_wire(item) for item in wire.unstaged),
        limit=wire.limit,
        offset=wire.offset,
        has_more=wire.has_more,
        next_cursor=wire.next_cursor,
    )


class _IssuePullRequestsResultWire(msgspec.Struct, frozen=True, kw_only=True):
    pull_requests: tuple[LinkedPullRequest, ...] = ()


def _issue_pull_requests_from_wire(
    wire: _IssuePullRequestsResultWire,
) -> tuple[LinkedPullRequest, ...]:
    return wire.pull_requests


class _AutopilotTriggerWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    type: str
    config: dict[str, str] = msgspec.field(default_factory=dict)


def trigger_from_wire(wire: _AutopilotTriggerWire) -> AutopilotTrigger:
    return AutopilotTrigger(
        id=wire.id,
        type=wire.type,
        config=tuple(TriggerConfigItem(key=key, value=value) for key, value in wire.config.items()),
    )


class _ProjectWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    title: str
    description: str | None = None
    status: ProjectStatus


def _project_from_wire(wire: _ProjectWire) -> Project:
    from multica_py.entities.projects import Project

    return Project(
        id=wire.id,
        name=wire.title,
        description=wire.description,
        status=wire.status,
    )


class _CommentWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    content: str
    parent_id: str | None = None
    author_id: str | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


def comment_from_wire(wire: _CommentWire) -> Comment:
    from multica_py.entities.comments import Comment

    return Comment(
        id=wire.id,
        body=wire.content,
        thread_id=wire.parent_id,
        author_id=wire.author_id,
        created_at=wire.created_at,
        updated_at=wire.updated_at,
    )


class _CommentThreadWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    comments: tuple[_CommentWire, ...] = ()
    resolved: bool = False
    updated_at: datetime.datetime | None = None


def comment_thread_from_wire(wire: _CommentThreadWire) -> CommentThread:
    from multica_py.entities.comments import CommentThread

    return CommentThread(
        id=wire.id,
        resolved=wire.resolved,
        updated_at=wire.updated_at,
    )


class _AutopilotListWire(msgspec.Struct, frozen=True, kw_only=True):
    autopilots: tuple[_AutopilotWire, ...] = ()
    total: int = 0


def _autopilot_list_page_from_wire(wire: _AutopilotListWire) -> AutopilotListPage[object]:

    return AutopilotListPage(
        items=tuple(_autopilot_from_wire(a) for a in wire.autopilots),
        total=wire.total,
    )


class _AutopilotSubscriberWire(msgspec.Struct, frozen=True, kw_only=True):
    user_type: str
    user_id: str
    created_at: datetime.datetime | None = None


class _AutopilotWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    workspace_id: str
    title: str
    description: str | None = None
    project_id: str | None | msgspec.UnsetType = msgspec.UNSET
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
    subscribers: tuple[_AutopilotSubscriberWire, ...] | msgspec.UnsetType = msgspec.UNSET
    can_write: bool | None = None
    can_manage_access: bool | None = None


def _autopilot_from_wire(wire: _AutopilotWire) -> Autopilot:
    from multica_py.entities.autopilots import Autopilot

    return Autopilot(
        id=wire.id,
        workspace_id=wire.workspace_id,
        title=wire.title,
        description=wire.description,
        project_id=None if wire.project_id is msgspec.UNSET else wire.project_id,
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
        subscriber_snapshot=tuple(
            AutopilotSubscriber(
                user_type=s.user_type,
                user_id=s.user_id,
                created_at=s.created_at,
            )
            for s in (() if wire.subscribers is msgspec.UNSET else wire.subscribers)
        ),
        can_write=wire.can_write,
        can_manage_access=wire.can_manage_access,
        _wire_presence=(("project_id", _presence_seed(wire.project_id)),),
    )


class _AutopilotGetWire(msgspec.Struct, frozen=True, kw_only=True):
    autopilot: _AutopilotWire
    triggers: tuple[_AutopilotTriggerWire, ...] | msgspec.UnsetType = msgspec.UNSET


class _AutopilotGetResult:
    def __init__(
        self,
        data: Autopilot,
        *,
        triggers: tuple[AutopilotTrigger, ...] | msgspec.UnsetType,
        subscribers: tuple[AutopilotSubscriber, ...] | msgspec.UnsetType,
    ) -> None:
        self.data = data
        self.triggers = triggers
        self.subscribers = subscribers


def _autopilot_subscribers(
    wire: tuple[_AutopilotSubscriberWire, ...] | msgspec.UnsetType,
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


def _autopilot_get_from_wire(wire: _AutopilotGetWire) -> _AutopilotGetResult:
    return _AutopilotGetResult(
        _autopilot_from_wire(wire.autopilot),
        triggers=(
            msgspec.UNSET
            if wire.triggers is msgspec.UNSET
            else tuple(trigger_from_wire(item) for item in wire.triggers)
        ),
        subscribers=_autopilot_subscribers(wire.autopilot.subscribers),
    )


class _AutopilotRunWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    autopilot_id: str
    trigger_id: str | None = None
    source: str
    status: str
    issue_id: str | None | msgspec.UnsetType = msgspec.UNSET
    task_id: str | None = None
    triggered_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    failure_reason: str | None = None
    reason_code: str | None = None
    # The recursive public JsonValue alias cannot be compiled by msgspec's
    # runtime schema builder. This private wire boundary intentionally accepts
    # the decoded tree as object; _autopilot_run_from_wire applies the strict
    # recursive JsonValue converter before constructing the public model.
    trigger_payload: object | None = None
    result: object | None = None
    created_at: datetime.datetime | None = None


def _autopilot_run_from_wire(wire: _AutopilotRunWire) -> AutopilotRun:
    from multica_py.entities.autopilots import AutopilotRun

    trigger_payload = (
        None
        if wire.trigger_payload is None
        else _coerce_json_value(wire.trigger_payload, field_name="trigger_payload")
    )
    result = None if wire.result is None else _coerce_json_value(wire.result, field_name="result")

    return AutopilotRun(
        id=wire.id,
        autopilot_id=wire.autopilot_id,
        trigger_id=wire.trigger_id,
        source=wire.source,
        status=wire.status,
        issue_id=None if wire.issue_id is msgspec.UNSET else wire.issue_id,
        task_id=wire.task_id,
        triggered_at=wire.triggered_at,
        completed_at=wire.completed_at,
        failure_reason=wire.failure_reason,
        reason_code=wire.reason_code,
        trigger_payload=trigger_payload,
        result=result,
        created_at=wire.created_at,
        _wire_presence=(("issue_id", _presence_seed(wire.issue_id)),),
    )


class _TaskRunWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    status: str
    agent_id: str | None | msgspec.UnsetType = msgspec.UNSET
    runtime_id: str | None = None
    workspace_id: str | None = None
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    dispatched_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    work_dir: str | None = None
    relative_work_dir: str | None = None
    durable_work_dir: str | None = None
    relative_durable_work_dir: str | None = None
    branch_name: str | None = None
    result: object | None = None
    error: str | None = None
    failure_reason: str | None = None


def _task_run_from_wire(wire: _TaskRunWire, *, issue_id: str | None) -> TaskRun:
    from multica_py.entities.issues import TaskRun

    result = None if wire.result is None else _coerce_json_value(wire.result, field_name="result")
    return TaskRun(
        id=wire.id,
        status=wire.status,
        agent_id=None if wire.agent_id is msgspec.UNSET else wire.agent_id,
        runtime_id=wire.runtime_id,
        workspace_id=wire.workspace_id,
        started_at=wire.started_at,
        completed_at=wire.completed_at,
        dispatched_at=wire.dispatched_at,
        created_at=wire.created_at,
        work_dir=wire.work_dir,
        relative_work_dir=wire.relative_work_dir,
        durable_work_dir=wire.durable_work_dir,
        relative_durable_work_dir=wire.relative_durable_work_dir,
        branch_name=wire.branch_name,
        result=result,
        error=wire.error,
        failure_reason=wire.failure_reason,
        issue_id=issue_id,
        _wire_presence=(("agent_id", _presence_seed(wire.agent_id)),),
    )


class _RunMessageWire(msgspec.Struct, frozen=True, kw_only=True):
    task_id: str
    seq: int
    type: str
    issue_id: str | None = None
    tool: str | None = None
    content: str | None = None
    # The recursive public JsonValue alias cannot be compiled by msgspec's
    # runtime schema builder.  This private wire boundary accepts the decoded
    # tree as object; _run_message_from_wire applies the strict recursive
    # JsonValue converter before constructing the public model.
    input: object | None = None
    output: str | None = None
    created_at: datetime.datetime | None = None


def _run_message_from_wire(wire: _RunMessageWire) -> RunMessage:
    from multica_py.models.issue_activity import RunMessage

    try:
        validate_since_cursor(wire.seq)
    except ValueError as exc:
        raise OutputShapeError("run message seq must be a nonnegative int32") from exc
    raw_input = wire.input
    if raw_input is None:
        converted_input = None
    elif isinstance(raw_input, Mapping):
        converted_input = cast(
            "Mapping[str, JsonValue]", _coerce_json_value(raw_input, field_name="input")
        )
    else:
        raise OutputShapeError("run message input must be a JSON object or null")
    return RunMessage(
        task_id=wire.task_id,
        seq=wire.seq,
        type=wire.type,
        issue_id=wire.issue_id,
        tool=wire.tool,
        content=wire.content,
        input=converted_input,
        output=wire.output,
        created_at=wire.created_at,
    )


def decode_run_messages(stdout: bytes, command: str) -> tuple[RunMessage, ...]:
    """Decoder hook for the governed run-message collection response."""

    wire_items = decode_json(stdout, list[_RunMessageWire], command=command)
    return tuple(_run_message_from_wire(item) for item in wire_items)


class _AutopilotRunListPageWire(msgspec.Struct, frozen=True, kw_only=True):
    runs: tuple[_AutopilotRunWire, ...] = ()
    total: int = 0


def _autopilot_run_list_page_from_wire(
    wire: _AutopilotRunListPageWire, *, limit: int | None = None, offset: int | None = None
) -> AutopilotRunListPage[AutopilotRun]:

    runs = tuple(_autopilot_run_from_wire(r) for r in wire.runs)
    has_more = (offset or 0) + len(runs) < wire.total
    return AutopilotRunListPage(
        items=runs,
        total=wire.total,
        limit=limit,
        offset=offset,
        has_more=has_more,
    )


class _LocalDirectoryResourceRefWire(msgspec.Struct, frozen=True, kw_only=True):
    local_path: str
    daemon_id: str
    label: str | None = None


class _ProjectResourceRecordWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    project_id: str
    resource_type: str
    resource_ref: _LocalDirectoryResourceRefWire


def project_resource_from_wire(wire: _ProjectResourceRecordWire) -> ProjectResourceRecord:
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


class _PropertyOptionWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    color: str = ""


class _PropertyConfigWire(msgspec.Struct, frozen=True, kw_only=True):
    options: tuple[_PropertyOptionWire, ...] = ()


class _PropertyDefinitionWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    type: str
    description: str = ""
    icon: str = ""
    config: _PropertyConfigWire = msgspec.field(default_factory=_PropertyConfigWire)
    position: float = 0.0
    archived: bool = False
    usage_count: int = 0
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


class _PluginWire(msgspec.Struct, frozen=True, kw_only=True):
    plugin_key: str
    desired_version: str
    lifecycle_status: str
    trust_tier: str
    uploader_id: str = ""


class _PluginDigestWire(msgspec.Struct, frozen=True, kw_only=True):
    plugin_key: str
    version: str
    manifest_digest: str
    archive_digest: str
    artifact_digest: str
    size_bytes: int
    file_count: int


def plugin_from_wire(wire: _PluginWire) -> Plugin:
    from multica_py.models.plugins import Plugin

    return Plugin(
        plugin_key=wire.plugin_key,
        desired_version=wire.desired_version,
        lifecycle_status=wire.lifecycle_status,
        trust_tier=wire.trust_tier,
        uploader_id=wire.uploader_id,
    )


def plugin_digest_from_wire(wire: _PluginDigestWire) -> PluginDigest:
    from multica_py.models.plugins import PluginDigest

    return PluginDigest(
        plugin_key=wire.plugin_key,
        version=wire.version,
        manifest_digest=wire.manifest_digest,
        archive_digest=wire.archive_digest,
        artifact_digest=wire.artifact_digest,
        size_bytes=wire.size_bytes,
        file_count=wire.file_count,
    )


def property_definition_from_wire(wire: _PropertyDefinitionWire) -> PropertyDefinition:
    from multica_py.models.properties import PropertyDefinition, PropertyOption

    return PropertyDefinition(
        id=wire.id,
        name=wire.name,
        type=wire.type,
        description=wire.description,
        icon=wire.icon,
        options=tuple(
            PropertyOption(id=option.id, name=option.name, color=option.color)
            for option in wire.config.options
        ),
        position=wire.position,
        archived=wire.archived,
        usage_count=wire.usage_count,
        created_at=wire.created_at,
        updated_at=wire.updated_at,
    )
