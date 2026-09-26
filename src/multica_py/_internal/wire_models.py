from __future__ import annotations

import datetime
import pathlib
from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

import msgspec

from multica_py._generated.approved_sdk import validate_since_cursor
from multica_py._internal.decoders import decode_json
from multica_py._internal.json_values import _coerce_json_value
from multica_py._internal.wire_presence import WirePresence
from multica_py._internal.wire_presence import presence as _presence_seed
from multica_py.enums import ProjectStatus
from multica_py.exceptions import OutputShapeError
from multica_py.models.autopilots import (
    AutopilotListPage,
    AutopilotRunListPage,
    AutopilotSubscriber,
    AutopilotTrigger,
)
from multica_py.models.issue_activity import (
    IssueUsage,
    RunMessage,
    TaskIssueStatusData,
    TaskPluginHookTool,
    TaskProjectResourceData,
    TaskUsageData,
)
from multica_py.models.project_resources import (
    GithubRepoResourceRef,
    LocalDirectoryResourceRef,
    ProjectResourceRecord,
)
from multica_py.models.properties import PropertyDefinition
from multica_py.types import JsonValue

if TYPE_CHECKING:
    from multica_py.entities.autopilots import Autopilot, AutopilotRun
    from multica_py.entities.comments import Comment, CommentThread
    from multica_py.entities.issues import TaskRun
    from multica_py.entities.projects import Project

from multica_py._internal.agent_wires import (
    _agent_from_wire,
    _AgentConversationStarterWire,
    _AgentWire,
    _task_cancellation_actor_from_wire,
    _TaskCancellationActorWire,
)
from multica_py._internal.issue_wires import (
    _issue_assignee_from_wire,
    _issue_children_result_from_wire,
    _issue_from_wire,
    _issue_list_page_from_wire,
    _issue_pull_requests_from_wire,
    _issue_row_from_wire,
    _IssueChildrenResultWire,
    _IssueListPageWire,
    _IssuePullRequestsResultWire,
    _IssueSearchResultWire,
    _IssueWire,
    _LabelWire,
)

__all__ = [
    "_AgentConversationStarterWire",
    "_AgentWire",
    "_IssueChildrenResultWire",
    "_IssueListPageWire",
    "_IssuePullRequestsResultWire",
    "_IssueSearchResultWire",
    "_IssueWire",
    "_LabelWire",
    "_agent_from_wire",
    "_issue_assignee_from_wire",
    "_issue_children_result_from_wire",
    "_issue_from_wire",
    "_issue_list_page_from_wire",
    "_issue_pull_requests_from_wire",
    "_issue_row_from_wire",
]

_PresenceSeed = WirePresence


class _AutopilotTriggerWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    autopilot_id: str
    kind: str
    enabled: bool
    cron_expression: str | None = None
    timezone: str | None = None
    next_run_at: datetime.datetime | None = None
    label: str | None = None
    last_fired_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


def trigger_from_wire(wire: _AutopilotTriggerWire) -> AutopilotTrigger:
    return AutopilotTrigger(
        id=wire.id,
        autopilot_id=wire.autopilot_id,
        kind=wire.kind,
        enabled=wire.enabled,
        cron_expression=wire.cron_expression,
        timezone=wire.timezone,
        next_run_at=wire.next_run_at,
        label=wire.label,
        last_fired_at=wire.last_fired_at,
        created_at=wire.created_at,
        updated_at=wire.updated_at,
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
    deleted_at: datetime.datetime | msgspec.UnsetType = msgspec.UNSET
    revision: int | msgspec.UnsetType = msgspec.UNSET
    issue_revision: int | msgspec.UnsetType = msgspec.UNSET
    author_type: str | None = None
    author_name: str | None = None
    resolved: bool | None = None
    reactions: object | None = None
    attachments: tuple[object, ...] = ()
    folded: bool | None = None
    trigger: object | None = None
    supplement: object | None = None


def comment_from_wire(wire: _CommentWire) -> Comment:
    from multica_py.entities.comments import Comment

    return Comment(
        id=wire.id,
        body=wire.content,
        thread_id=wire.parent_id,
        author_id=wire.author_id,
        created_at=wire.created_at,
        updated_at=wire.updated_at,
        deleted_at=None if wire.deleted_at is msgspec.UNSET else wire.deleted_at,
        revision=None if wire.revision is msgspec.UNSET else wire.revision,
        issue_revision=(None if wire.issue_revision is msgspec.UNSET else wire.issue_revision),
        author_type=wire.author_type,
        author_name=wire.author_name,
        resolved=wire.resolved,
        reactions=None
        if wire.reactions is None
        else _coerce_json_value(wire.reactions, field_name="reactions"),
        attachments=tuple(
            _coerce_json_value(item, field_name="attachments") for item in wire.attachments
        ),
        folded=wire.folded,
        trigger=None
        if wire.trigger is None
        else _coerce_json_value(wire.trigger, field_name="trigger"),
        supplement=None
        if wire.supplement is None
        else _coerce_json_value(wire.supplement, field_name="supplement"),
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
    has_webhook_token: bool | None = None
    webhook_token_hint: str | None = None
    webhook_token: str | None = None
    webhook_path: str | None = None
    webhook_url: str | None = None


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
        has_webhook_token=wire.has_webhook_token,
        webhook_token_hint=wire.webhook_token_hint,
        webhook_token=wire.webhook_token,
        webhook_path=wire.webhook_path,
        webhook_url=wire.webhook_url,
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


class _TaskIssueStatusWire(msgspec.Struct, frozen=True, kw_only=True):
    key: str
    name: str
    category: str
    description: str = ""


class _TaskPluginHookToolWire(msgspec.Struct, frozen=True, kw_only=True):
    installation_id: str
    hook_key: str
    name: str
    description: str
    input_schema: object | None = None


class _TaskProjectResourceWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    resource_type: str
    resource_ref: object
    label: str = ""


class _TaskUsageWire(msgspec.Struct, frozen=True, kw_only=True):
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    cost_usd_ticks: int | None = None


class _TaskRunWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    status: str
    wakeup_id: str | None | msgspec.UnsetType = msgspec.UNSET
    supplement_capability: str | None | msgspec.UnsetType = msgspec.UNSET
    supplement_comment_ids: tuple[str, ...] | msgspec.UnsetType = msgspec.UNSET
    can_supplement: bool | None | msgspec.UnsetType = msgspec.UNSET
    cancelled_by: _TaskCancellationActorWire | msgspec.UnsetType = msgspec.UNSET
    workspace_slug: str | None | msgspec.UnsetType = msgspec.UNSET
    issue_identifier: str | None | msgspec.UnsetType = msgspec.UNSET
    workspace_context: str | None | msgspec.UnsetType = msgspec.UNSET
    issue_title: str | None | msgspec.UnsetType = msgspec.UNSET
    issue_description: str | None | msgspec.UnsetType = msgspec.UNSET
    issue_status: str | None | msgspec.UnsetType = msgspec.UNSET
    issue_assignee_type: str | None | msgspec.UnsetType = msgspec.UNSET
    issue_assignee_id: str | None | msgspec.UnsetType = msgspec.UNSET
    issue_changed_fields: tuple[str, ...] | None | msgspec.UnsetType = msgspec.UNSET
    issue_state_delta_known: bool | None | msgspec.UnsetType = msgspec.UNSET
    issue_statuses: tuple[_TaskIssueStatusWire, ...] | None | msgspec.UnsetType = msgspec.UNSET
    issue_statuses_omitted: int | None | msgspec.UnsetType = msgspec.UNSET
    project_id: str | None | msgspec.UnsetType = msgspec.UNSET
    project_title: str | None | msgspec.UnsetType = msgspec.UNSET
    project_description: str | None | msgspec.UnsetType = msgspec.UNSET
    project_resources: tuple[_TaskProjectResourceWire, ...] | None | msgspec.UnsetType = (
        msgspec.UNSET
    )
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
    trigger_comment_id: str | None | msgspec.UnsetType = msgspec.UNSET
    coalesced_comment_ids: tuple[str, ...] | None | msgspec.UnsetType = msgspec.UNSET
    delivered_comment_ids: tuple[str, ...] | None | msgspec.UnsetType = msgspec.UNSET
    trigger_thread_id: str | None | msgspec.UnsetType = msgspec.UNSET
    trigger_comment_content: str | None | msgspec.UnsetType = msgspec.UNSET
    trigger_summary: str | None | msgspec.UnsetType = msgspec.UNSET
    trigger_author_type: str | None | msgspec.UnsetType = msgspec.UNSET
    trigger_author_name: str | None | msgspec.UnsetType = msgspec.UNSET
    new_comment_count: int | None | msgspec.UnsetType = msgspec.UNSET
    new_comments_since: datetime.datetime | None | msgspec.UnsetType = msgspec.UNSET
    new_comments_delta_known: bool | None | msgspec.UnsetType = msgspec.UNSET
    quick_create_prompt: str | None | msgspec.UnsetType = msgspec.UNSET
    quick_create_priority: str | None | msgspec.UnsetType = msgspec.UNSET
    quick_create_due_date: str | None | msgspec.UnsetType = msgspec.UNSET
    quick_create_attachment_ids: tuple[str, ...] | None | msgspec.UnsetType = msgspec.UNSET
    quick_create_source_context: object | None | msgspec.UnsetType = msgspec.UNSET
    plugin_hook_tools: tuple[_TaskPluginHookToolWire, ...] | None | msgspec.UnsetType = (
        msgspec.UNSET
    )
    usage: tuple[_TaskUsageWire, ...] | None | msgspec.UnsetType = msgspec.UNSET
    result: object | None = None
    error: str | None = None
    failure_reason: str | None = None


def _task_run_from_wire(
    wire: _TaskRunWire,
    *,
    issue_id: str | None,
    include_agent_presence: bool = True,
    include_wire_presence: bool = True,
) -> TaskRun:
    from multica_py.entities.issues import TaskRun

    issue_statuses = (
        ()
        if wire.issue_statuses in (msgspec.UNSET, None)
        else tuple(
            TaskIssueStatusData(
                key=item.key,
                name=item.name,
                category=item.category,
                description=item.description,
            )
            for item in wire.issue_statuses
        )
    )
    project_resources = (
        ()
        if wire.project_resources in (msgspec.UNSET, None)
        else tuple(
            TaskProjectResourceData(
                id=item.id,
                resource_type=item.resource_type,
                resource_ref=_coerce_json_value(item.resource_ref, field_name="resource_ref"),
                label=item.label,
            )
            for item in wire.project_resources
        )
    )
    plugin_hook_tools = (
        ()
        if wire.plugin_hook_tools in (msgspec.UNSET, None)
        else tuple(
            TaskPluginHookTool(
                installation_id=item.installation_id,
                hook_key=item.hook_key,
                name=item.name,
                description=item.description,
                input_schema=(
                    None
                    if item.input_schema is None
                    else _coerce_json_value(item.input_schema, field_name="input_schema")
                ),
            )
            for item in wire.plugin_hook_tools
        )
    )
    usage = (
        ()
        if wire.usage in (msgspec.UNSET, None)
        else tuple(
            TaskUsageData(
                provider=item.provider,
                model=item.model,
                input_tokens=item.input_tokens,
                output_tokens=item.output_tokens,
                cache_read_tokens=item.cache_read_tokens,
                cache_write_tokens=item.cache_write_tokens,
                cost_usd_ticks=item.cost_usd_ticks,
            )
            for item in wire.usage
        )
    )
    result = (
        None
        if wire.result is msgspec.UNSET or wire.result is None
        else _coerce_json_value(wire.result, field_name="result")
    )
    cancelled_by = (
        None
        if wire.cancelled_by is msgspec.UNSET
        else _task_cancellation_actor_from_wire(wire.cancelled_by)
    )

    return TaskRun(
        id=wire.id,
        status=wire.status,
        wakeup_id=None if wire.wakeup_id is msgspec.UNSET else wire.wakeup_id,
        supplement_capability=(
            None if wire.supplement_capability is msgspec.UNSET else wire.supplement_capability
        ),
        supplement_comment_ids=(
            () if wire.supplement_comment_ids is msgspec.UNSET else wire.supplement_comment_ids
        ),
        can_supplement=(None if wire.can_supplement is msgspec.UNSET else wire.can_supplement),
        cancelled_by=cancelled_by,
        workspace_slug=None if wire.workspace_slug is msgspec.UNSET else wire.workspace_slug,
        issue_identifier=(
            None if wire.issue_identifier is msgspec.UNSET else wire.issue_identifier
        ),
        workspace_context=(
            None if wire.workspace_context is msgspec.UNSET else wire.workspace_context
        ),
        issue_title=None if wire.issue_title is msgspec.UNSET else wire.issue_title,
        issue_description=(
            None if wire.issue_description is msgspec.UNSET else wire.issue_description
        ),
        issue_status=None if wire.issue_status is msgspec.UNSET else wire.issue_status,
        issue_assignee_type=(
            None if wire.issue_assignee_type is msgspec.UNSET else wire.issue_assignee_type
        ),
        issue_assignee_id=(
            None if wire.issue_assignee_id is msgspec.UNSET else wire.issue_assignee_id
        ),
        issue_changed_fields=(
            () if wire.issue_changed_fields in (msgspec.UNSET, None) else wire.issue_changed_fields
        ),
        issue_state_delta_known=(
            None if wire.issue_state_delta_known is msgspec.UNSET else wire.issue_state_delta_known
        ),
        issue_statuses=issue_statuses,
        issue_statuses_omitted=(
            None if wire.issue_statuses_omitted is msgspec.UNSET else wire.issue_statuses_omitted
        ),
        project_id=None if wire.project_id is msgspec.UNSET else wire.project_id,
        project_title=None if wire.project_title is msgspec.UNSET else wire.project_title,
        project_description=(
            None if wire.project_description is msgspec.UNSET else wire.project_description
        ),
        project_resources=project_resources,
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
        trigger_comment_id=(
            None if wire.trigger_comment_id is msgspec.UNSET else wire.trigger_comment_id
        ),
        coalesced_comment_ids=(
            ()
            if wire.coalesced_comment_ids in (msgspec.UNSET, None)
            else wire.coalesced_comment_ids
        ),
        delivered_comment_ids=(
            ()
            if wire.delivered_comment_ids in (msgspec.UNSET, None)
            else wire.delivered_comment_ids
        ),
        trigger_thread_id=(
            None if wire.trigger_thread_id is msgspec.UNSET else wire.trigger_thread_id
        ),
        trigger_comment_content=(
            None if wire.trigger_comment_content is msgspec.UNSET else wire.trigger_comment_content
        ),
        trigger_summary=None if wire.trigger_summary is msgspec.UNSET else wire.trigger_summary,
        trigger_author_type=(
            None if wire.trigger_author_type is msgspec.UNSET else wire.trigger_author_type
        ),
        trigger_author_name=(
            None if wire.trigger_author_name is msgspec.UNSET else wire.trigger_author_name
        ),
        new_comment_count=(
            None if wire.new_comment_count is msgspec.UNSET else wire.new_comment_count
        ),
        new_comments_since=(
            None if wire.new_comments_since is msgspec.UNSET else wire.new_comments_since
        ),
        new_comments_delta_known=(
            None
            if wire.new_comments_delta_known is msgspec.UNSET
            else wire.new_comments_delta_known
        ),
        quick_create_prompt=(
            None if wire.quick_create_prompt is msgspec.UNSET else wire.quick_create_prompt
        ),
        quick_create_priority=(
            None if wire.quick_create_priority is msgspec.UNSET else wire.quick_create_priority
        ),
        quick_create_due_date=(
            None if wire.quick_create_due_date is msgspec.UNSET else wire.quick_create_due_date
        ),
        quick_create_attachment_ids=(
            ()
            if wire.quick_create_attachment_ids in (msgspec.UNSET, None)
            else wire.quick_create_attachment_ids
        ),
        quick_create_source_context=(
            None
            if wire.quick_create_source_context in (msgspec.UNSET, None)
            else _coerce_json_value(
                wire.quick_create_source_context, field_name="quick_create_source_context"
            )
        ),
        plugin_hook_tools=plugin_hook_tools,
        usage=usage,
        result=result,
        error=wire.error,
        failure_reason=wire.failure_reason,
        issue_id=issue_id,
        _wire_presence=(
            (
                ((("agent_id", _presence_seed(wire.agent_id)),) if include_agent_presence else ())
                + (
                    ("workspace_slug", _presence_seed(wire.workspace_slug)),
                    ("wakeup_id", _presence_seed(wire.wakeup_id)),
                    ("supplement_capability", _presence_seed(wire.supplement_capability)),
                    ("supplement_comment_ids", _presence_seed(wire.supplement_comment_ids)),
                    ("can_supplement", _presence_seed(wire.can_supplement)),
                    ("issue_identifier", _presence_seed(wire.issue_identifier)),
                    ("workspace_context", _presence_seed(wire.workspace_context)),
                    ("issue_title", _presence_seed(wire.issue_title)),
                    ("issue_description", _presence_seed(wire.issue_description)),
                    ("issue_status", _presence_seed(wire.issue_status)),
                    ("issue_assignee_type", _presence_seed(wire.issue_assignee_type)),
                    ("issue_assignee_id", _presence_seed(wire.issue_assignee_id)),
                    ("issue_changed_fields", _presence_seed(wire.issue_changed_fields)),
                    ("issue_state_delta_known", _presence_seed(wire.issue_state_delta_known)),
                    ("issue_statuses", _presence_seed(wire.issue_statuses)),
                    ("issue_statuses_omitted", _presence_seed(wire.issue_statuses_omitted)),
                    ("project_id", _presence_seed(wire.project_id)),
                    ("project_title", _presence_seed(wire.project_title)),
                    ("project_description", _presence_seed(wire.project_description)),
                    ("project_resources", _presence_seed(wire.project_resources)),
                    ("trigger_comment_id", _presence_seed(wire.trigger_comment_id)),
                    ("coalesced_comment_ids", _presence_seed(wire.coalesced_comment_ids)),
                    ("delivered_comment_ids", _presence_seed(wire.delivered_comment_ids)),
                    ("trigger_thread_id", _presence_seed(wire.trigger_thread_id)),
                    ("trigger_comment_content", _presence_seed(wire.trigger_comment_content)),
                    ("trigger_summary", _presence_seed(wire.trigger_summary)),
                    ("trigger_author_type", _presence_seed(wire.trigger_author_type)),
                    ("trigger_author_name", _presence_seed(wire.trigger_author_name)),
                    ("new_comment_count", _presence_seed(wire.new_comment_count)),
                    ("new_comments_since", _presence_seed(wire.new_comments_since)),
                    ("new_comments_delta_known", _presence_seed(wire.new_comments_delta_known)),
                    ("quick_create_prompt", _presence_seed(wire.quick_create_prompt)),
                    ("quick_create_priority", _presence_seed(wire.quick_create_priority)),
                    ("quick_create_due_date", _presence_seed(wire.quick_create_due_date)),
                    (
                        "quick_create_attachment_ids",
                        _presence_seed(wire.quick_create_attachment_ids),
                    ),
                    (
                        "quick_create_source_context",
                        _presence_seed(wire.quick_create_source_context),
                    ),
                    ("plugin_hook_tools", _presence_seed(wire.plugin_hook_tools)),
                    ("usage", _presence_seed(wire.usage)),
                    ("cancelled_by", _presence_seed(wire.cancelled_by)),
                )
            )
            if include_wire_presence
            else ()
        ),
    )


class _RunMessageWire(msgspec.Struct, frozen=True, kw_only=True):
    task_id: str
    seq: int
    type: str
    call_id: str | None = None
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
    output_truncated: bool | msgspec.UnsetType = msgspec.UNSET


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
        call_id=wire.call_id,
        issue_id=wire.issue_id,
        tool=wire.tool,
        content=wire.content,
        input=converted_input,
        output=wire.output,
        created_at=wire.created_at,
        output_truncated=(
            None if wire.output_truncated is msgspec.UNSET else wire.output_truncated
        ),
    )


class _IssueUsageWire(msgspec.Struct, frozen=True, kw_only=True):
    total_runs: int = 0
    total_tokens: int | None = None
    cost_usd: float | None = None
    period_start: datetime.datetime | None = None
    period_end: datetime.datetime | None = None
    task_count: int | None = None
    total_input_tokens: int | None = None
    total_output_tokens: int | None = None
    total_cache_read_tokens: int | None = None
    total_cache_write_tokens: int | None = None
    cost_usd_ticks: int | None = None
    uncosted_input_tokens: int | None = None
    uncosted_output_tokens: int | None = None
    uncosted_cache_read_tokens: int | None = None
    uncosted_cache_write_tokens: int | None = None
    terminal_task_count: int | msgspec.UnsetType = msgspec.UNSET
    metered_task_count: int | msgspec.UnsetType = msgspec.UNSET
    unreported_task_count: int | msgspec.UnsetType = msgspec.UNSET


def _issue_usage_from_wire(wire: _IssueUsageWire) -> IssueUsage:
    counts = (wire.terminal_task_count, wire.metered_task_count, wire.unreported_task_count)
    if any(value is not msgspec.UNSET and value < 0 for value in counts):
        raise OutputShapeError("issue usage coverage counts must be nonnegative integers")
    return IssueUsage(
        total_runs=wire.total_runs,
        total_tokens=wire.total_tokens,
        cost_usd=wire.cost_usd,
        period_start=wire.period_start,
        period_end=wire.period_end,
        task_count=wire.task_count,
        total_input_tokens=wire.total_input_tokens,
        total_output_tokens=wire.total_output_tokens,
        total_cache_read_tokens=wire.total_cache_read_tokens,
        total_cache_write_tokens=wire.total_cache_write_tokens,
        cost_usd_ticks=wire.cost_usd_ticks,
        uncosted_input_tokens=wire.uncosted_input_tokens,
        uncosted_output_tokens=wire.uncosted_output_tokens,
        uncosted_cache_read_tokens=wire.uncosted_cache_read_tokens,
        uncosted_cache_write_tokens=wire.uncosted_cache_write_tokens,
        terminal_task_count=(
            None if wire.terminal_task_count is msgspec.UNSET else wire.terminal_task_count
        ),
        metered_task_count=(
            None if wire.metered_task_count is msgspec.UNSET else wire.metered_task_count
        ),
        unreported_task_count=(
            None if wire.unreported_task_count is msgspec.UNSET else wire.unreported_task_count
        ),
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
    execution_mode: str | None = None


class _ProjectResourceRecordWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    project_id: str
    resource_type: str
    resource_ref: object
    label: str | None = None
    position: int | None = None


def project_resource_from_wire(wire: _ProjectResourceRecordWire) -> ProjectResourceRecord:
    if not isinstance(wire.resource_ref, Mapping):
        raise OutputShapeError("resource_ref must be a JSON object")
    ref = wire.resource_ref
    if wire.resource_type == "local_directory":
        local_path = ref.get("local_path")
        daemon_id = ref.get("daemon_id")
        if not isinstance(local_path, str) or not isinstance(daemon_id, str):
            raise OutputShapeError("local_directory resource_ref requires local_path and daemon_id")
        if not pathlib.Path(local_path).is_absolute():
            raise OutputShapeError("local_path must be an absolute path")
        resource_ref: object = LocalDirectoryResourceRef(
            local_path=str(pathlib.Path(local_path).resolve()),
            daemon_id=daemon_id,
            label=ref.get("label") if isinstance(ref.get("label"), str) else None,
            execution_mode=(
                ref.get("execution_mode") if isinstance(ref.get("execution_mode"), str) else None
            ),
        )
    elif wire.resource_type == "github_repo":
        url = ref.get("url")
        if not isinstance(url, str):
            raise OutputShapeError("github_repo resource_ref requires url")
        resource_ref = GithubRepoResourceRef(
            url=url,
            default_branch_hint=(
                ref.get("default_branch_hint")
                if isinstance(ref.get("default_branch_hint"), str)
                else None
            ),
            ref=ref.get("ref") if isinstance(ref.get("ref"), str) else None,
        )
    else:
        resource_ref = dict(ref)
    return ProjectResourceRecord(
        id=wire.id,
        project_id=wire.project_id,
        resource_type=wire.resource_type,
        resource_ref=resource_ref,  # type: ignore[arg-type]
        label=wire.label,
        position=wire.position,
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
