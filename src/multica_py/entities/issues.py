from __future__ import annotations

import datetime
import math
import time
from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING, TypeVar, cast

import msgspec

from multica_py._generated.approved_sdk import validate_since_cursor
from multica_py._internal.commands import Command, _cached_value_command
from multica_py._internal.json_values import _coerce_json_value
from multica_py._internal.permalinks import build_permalink
from multica_py.config import OperationOptions
from multica_py.entities._base import (
    _BoundEntity,
    _reference_presence,
    _runtime_state,
)
from multica_py.entities.comments import Comment, CommentThread, _bind_comment, _bind_thread
from multica_py.entities.labels import Label
from multica_py.enums import IssueStatus, _coerce_issue_status
from multica_py.exceptions import (
    DetachedEntityError,
    MissingRelationContextError,
    OutputShapeError,
    ProtocolError,
    UnsupportedReferenceTargetError,
)
from multica_py.models.common import ActionResult, Page
from multica_py.models.issue_activity import (
    CommentCursor,
    MetadataEntry,
    RunMessage,
    Subscriber,
    TaskIssueStatusData,
    TaskPluginHookTool,
    TaskProjectResourceData,
    TaskUsageData,
)
from multica_py.models.issues import (
    AssignmentTarget,
    IssueAssignee,
    IssueChildrenResult,
    IssueChildStageGroup,
    IssueMetadataItem,
    IssueReference,
    LinkedPullRequest,
)
from multica_py.models.properties import PropertyValue
from multica_py.models.relations import (
    _GENERATION_UNSET,
    CursorLazyCollection,
    CursorPage,
    LazyCollection,
    LazyMapping,
    LazyRef,
    RelationMetadata,
    _RelationLoad,
)
from multica_py.models.run_events import RunEvent, RunStatusChangedEvent, _convert_run_message
from multica_py.models.system import AttachmentResult
from multica_py.sentinels import Unset, UnsetType
from multica_py.types import JsonValue, MetadataValue

if TYPE_CHECKING:
    from multica_py.client import MulticaClient
    from multica_py.entities.agents import Agent
    from multica_py.entities.projects import Project
    from multica_py.entities.squads import Squad


S = TypeVar("S")
_TERMINAL_DRAIN_POLL_LIMIT = 1024


def _page_items(page: Page[S] | tuple[S, ...]) -> tuple[S, ...]:
    return page.items if isinstance(page, Page) else page


def _property_relation_initial(
    value: object | None,
) -> Mapping[str, PropertyValue] | None:
    # Raw issue projections are UUID-keyed JSON maps. Keep them as the
    # already-loaded relation snapshot; resolved rows continue through the
    # reviewed property resource projection.
    if isinstance(value, Mapping):
        if all(isinstance(row, Mapping) for row in value.values()):
            resolved: dict[str, PropertyValue] = {}
            for row in value.values():
                assert isinstance(row, Mapping)
                property_id = row.get("property_id", row.get("id"))
                name = row.get("name")
                property_type = row.get("type")
                if not all(isinstance(item, str) for item in (property_id, name, property_type)):
                    return cast("Mapping[str, PropertyValue]", value)
                property_id = cast("str", property_id)
                name = cast("str", name)
                property_type = cast("str", property_type)
                resolved[name] = PropertyValue(
                    property_id=property_id,
                    name=name,
                    type=property_type,
                    value=cast("MetadataValue", row.get("value")),
                    display=cast("str", row.get("display", "")),
                    archived=cast("bool", row.get("archived", False)),
                )
            return resolved
        return cast("Mapping[str, PropertyValue]", value)
    if isinstance(value, tuple):
        resolved = {}
        for row in value:
            if not isinstance(row, Mapping):
                return None
            property_id = row.get("property_id", row.get("id"))
            name = row.get("name")
            property_type = row.get("type")
            if not all(isinstance(item, str) for item in (property_id, name, property_type)):
                return None
            property_id = cast("str", property_id)
            name = cast("str", name)
            property_type = cast("str", property_type)
            resolved[name] = PropertyValue(
                property_id=property_id,
                name=name,
                type=property_type,
                value=cast("MetadataValue", row.get("value")),
                display=cast("str", row.get("display", "")),
                archived=cast("bool", row.get("archived", False)),
            )
        return resolved
    return None


def _validate_poll_interval(value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("poll_interval must be a positive finite real number")
    if not math.isfinite(value) or value <= 0:
        raise ValueError("poll_interval must be a positive finite real number")


def _status_event(
    *,
    task_id: str,
    issue_id: str,
    previous_status: str | None,
    status: str,
    observed_at: datetime.datetime,
) -> RunStatusChangedEvent:
    return RunStatusChangedEvent(
        task_id=task_id,
        issue_id=issue_id,
        sequence=None,
        created_at=None,
        raw_message=None,
        previous_status=previous_status,
        status=status,
        observed_at=observed_at,
    )


def _run_message_seq(message: RunMessage) -> int:
    return message.seq


def _emit_unseen(
    page: Page[RunMessage] | tuple[RunMessage, ...],
    *,
    seen: dict[int, RunMessage],
    cursor: list[int],
    task_id: str,
    issue_id: str,
) -> Iterator[RunEvent]:
    """Yield semantic events for unseen messages, advancing the cursor in place."""
    for message in sorted(_page_items(page), key=_run_message_seq):
        seq = message.seq
        try:
            validate_since_cursor(seq)
        except ValueError as exc:
            raise OutputShapeError("run message seq must be a nonnegative int32") from exc
        if message.task_id != task_id or (
            message.issue_id is not None and message.issue_id != issue_id
        ):
            raise OutputShapeError("run message identity does not match the bound task run")
        stored = seen.get(seq)
        if stored is not None:
            if stored != message:
                raise OutputShapeError(f"run message sequence {seq} returned a conflicting payload")
            continue
        seen[seq] = message
        yield _convert_run_message(message)
        cursor[0] = max(cursor[0], seq)


def _refresh_run(client: MulticaClient, issue_id: str, task_id: str) -> TaskRun:
    runs = _page_items(client.issues.runs(issue_id))
    for run in runs:
        if run.id == task_id:
            return run
    raise ProtocolError(
        f"task run {task_id!r} disappeared from issue {issue_id!r} during stream refresh"
    )


def _stream_task_run_events(
    *,
    client: MulticaClient,
    task_id: str,
    issue_id: str,
    poll_interval: float,
) -> Iterator[RunEvent]:
    cursor = [0]
    seen: dict[int, RunMessage] = {}
    last_status: str | None = None

    while True:
        page = client.issues.run_messages(task_id, issue_id=issue_id, since=cursor[0])
        yield from _emit_unseen(page, seen=seen, cursor=cursor, task_id=task_id, issue_id=issue_id)

        run = _refresh_run(client, issue_id=issue_id, task_id=task_id)
        status = run.status
        observed_at = datetime.datetime.now(datetime.UTC)
        is_terminal = status in {"completed", "failed", "cancelled"} or run.completed_at is not None

        if is_terminal:
            ordinary_terminal = status in {"completed", "failed"}
            quiet_needed = 1 if ordinary_terminal else 2
            quiet_reads = 0
            drain_polls = 0
            while quiet_reads < quiet_needed:
                drain_polls += 1
                if drain_polls > _TERMINAL_DRAIN_POLL_LIMIT:
                    raise ProtocolError("task run stream exceeded the terminal drain poll limit")
                tail_page = client.issues.run_messages(task_id, issue_id=issue_id, since=cursor[0])
                emitted = list(
                    _emit_unseen(
                        tail_page, seen=seen, cursor=cursor, task_id=task_id, issue_id=issue_id
                    )
                )
                yield from emitted
                quiet_reads = 0 if emitted else quiet_reads + 1
                if quiet_reads < quiet_needed and not ordinary_terminal:
                    time.sleep(poll_interval)
            yield _status_event(
                task_id=task_id,
                issue_id=issue_id,
                previous_status=last_status,
                status=status,
                observed_at=observed_at,
            )
            return

        if status != last_status:
            yield _status_event(
                task_id=task_id,
                issue_id=issue_id,
                previous_status=last_status,
                status=status,
                observed_at=observed_at,
            )
            last_status = status

        time.sleep(poll_interval)


class TaskRun(_BoundEntity):  # type: ignore[misc]
    id: str
    status: str
    workspace_slug: str | None = None
    issue_identifier: str | None = None
    workspace_context: str | None = None
    issue_statuses: tuple[TaskIssueStatusData, ...] = ()
    issue_statuses_omitted: int | None = None
    project_id: str | None = None
    project_title: str | None = None
    project_description: str | None = None
    project_resources: tuple[TaskProjectResourceData, ...] = ()
    agent_id: str | None = None
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
    trigger_comment_id: str | None = None
    coalesced_comment_ids: tuple[str, ...] = ()
    delivered_comment_ids: tuple[str, ...] = ()
    trigger_thread_id: str | None = None
    trigger_comment_content: str | None = None
    trigger_summary: str | None = None
    trigger_author_type: str | None = None
    trigger_author_name: str | None = None
    new_comment_count: int | None = None
    new_comments_since: datetime.datetime | None = None
    new_comments_delta_known: bool | None = None
    quick_create_prompt: str | None = None
    quick_create_priority: str | None = None
    quick_create_due_date: str | None = None
    quick_create_attachment_ids: tuple[str, ...] = ()
    quick_create_source_context: JsonValue | None = None
    plugin_hook_tools: tuple[TaskPluginHookTool, ...] = ()
    usage: tuple[TaskUsageData, ...] = ()
    result: JsonValue | None = None
    error: str | None = None
    failure_reason: str | None = None
    issue_id: str | None = msgspec.field(default=None, name="_issue_id")
    _wire_presence: tuple[tuple[str, str], ...] = msgspec.field(default_factory=tuple)
    _messages: LazyCollection[RunMessage] | None = msgspec.field(default=None, name="_messages")
    _issue: object | None = msgspec.field(default=None, name="_issue")
    _agent: object | None = msgspec.field(default=None, name="_agent")

    def __post_init__(self) -> None:
        # Frozen msgspec fields cannot be replaced from ``__post_init__`` on
        # Python 3.12. Keep a normalized private snapshot for the public JSON
        # result so direct construction is as snapshot-safe as wire decoding.
        result = cast("object", object.__getattribute__(self, "result"))
        if result is not None and "result" not in _runtime_state(self):
            self._set_runtime("result", _coerce_json_value(result, field_name="result"))

    @classmethod
    def _from_encoded_dict(cls, data: dict[str, object]) -> TaskRun:
        from multica_py._internal.wire_models import _task_run_from_wire, _TaskRunWire

        wire = msgspec.convert(data, type=_TaskRunWire, strict=True)
        return _task_run_from_wire(
            wire,
            issue_id=None,
            include_agent_presence=False,
            include_wire_presence=False,
        )

    @property
    def issue(self) -> LazyRef[Issue]:
        if self._issue is None:
            issue_id = self.issue_id
            client = cast("MulticaClient | None", self._client)

            def command() -> Command[Issue]:
                if not issue_id:
                    raise MissingRelationContextError("TaskRun", self.id, "issue", "issue_id")
                if client is None:
                    raise DetachedEntityError("TaskRun", self.id, "issue")
                return client.issues.get_command(issue_id)

            self._set_runtime(
                "_issue",
                LazyRef(
                    command_loader=command,
                    _prefetch_target=lambda: ("Issue", issue_id),
                    _origin_client=client,
                    entity_type="TaskRun",
                    entity_id=self.id,
                    relation_name="issue",
                ),
            )
        return self._issue  # type: ignore[return-value]

    @property
    def agent(self) -> LazyRef[Agent | None]:
        if self._agent is None:
            agent_id = self.agent_id
            client = cast("MulticaClient | None", self._client)
            presence = _reference_presence(self, "agent_id", agent_id)

            def command() -> Command[Agent | None]:
                if presence == "null" and agent_id is None:
                    return _cached_value_command(lambda: None)
                if presence == "missing" or not agent_id:
                    raise MissingRelationContextError("TaskRun", self.id, "agent", "agent_id")
                if client is None:
                    raise DetachedEntityError("TaskRun", self.id, "agent")
                return client.agents.get_command(agent_id)

            self._set_runtime(
                "_agent",
                LazyRef(
                    command_loader=command,
                    initial=None if presence == "null" else _GENERATION_UNSET,
                    _prefetch_target=lambda: ("Agent", agent_id),
                    _origin_client=client,
                    entity_type="TaskRun",
                    entity_id=self.id,
                    relation_name="agent",
                ),
            )
        return self._agent  # type: ignore[return-value]

    @property
    def messages(self) -> LazyCollection[RunMessage]:
        if self._messages is None:
            client = self._require_client(
                entity_type="TaskRun", entity_id=self.id, relation_name="messages"
            )
            task_run_id = self.id
            issue_id = self.issue_id
            issues = client.issues

            def loader() -> tuple[RunMessage, ...]:
                return _page_items(issues.run_messages(task_run_id, issue_id=issue_id, since=0))

            self._set_runtime(
                "_messages",
                LazyCollection[RunMessage](
                    loader,
                    command_loader=lambda: issues._run_messages_relation_command(
                        task_run_id, issue_id=issue_id, since=0
                    ),
                ),
            )
        return self._messages  # type: ignore[return-value]

    def messages_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[tuple[RunMessage, ...]]:
        client = self._require_client(
            entity_type="TaskRun", entity_id=self.id, relation_name="messages"
        )
        return client.issues._run_messages_relation_command(
            self.id, issue_id=self.issue_id, since=0, options=options
        )

    def stream_events(self, *, poll_interval: float = 1.0) -> Iterator[RunEvent]:
        """Incrementally yield semantic :class:`RunEvent` objects for this task run.

        This is polling-backed incremental delivery, not server push or a
        real-time/completeness guarantee.  See ``docs/api.md`` for the
        completion-aware termination contract.
        """
        _validate_poll_interval(poll_interval)
        client = self._require_client(
            entity_type="TaskRun", entity_id=self.id, relation_name="stream_events"
        )
        issue_id = self.issue_id
        if not issue_id:
            raise MissingRelationContextError("TaskRun", self.id, "stream_events", "issue_id")
        return _stream_task_run_events(
            client=client,
            task_id=self.id,
            issue_id=issue_id,
            poll_interval=poll_interval,
        )


class Issue(_BoundEntity):  # type: ignore[misc]
    id: str
    title: str
    status: str
    status_name: str | None = None
    revision: int | None = None
    last_activity_at: datetime.datetime | None = None
    source_context: JsonValue | None = None
    description: str | None = None
    priority: str | None = None
    assignee: IssueAssignee | None = None
    child_stages: tuple[IssueChildStageGroup, ...] = ()
    label_names: tuple[str, ...] = ()
    metadata_snapshot: tuple[IssueMetadataItem, ...] = ()
    attachments: tuple[AttachmentResult, ...] = ()
    pull_request_snapshot: tuple[LinkedPullRequest, ...] = ()
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    parent_id: str | None = None
    project_id: str | None = None
    creator_id: str | None = None
    creator_type: str | None = None
    match_source: str | None = None
    _property_projection: object | None = msgspec.field(default=None, name="_property_projection")
    _projection: Mapping[str, object] = msgspec.field(default_factory=dict, name="_projection")
    _wire_presence: tuple[tuple[str, str], ...] = msgspec.field(default_factory=tuple)

    _comments: LazyCollection[Comment] | None = msgspec.field(default=None, name="_comments")
    _recent_threads: dict[
        tuple[int, tuple[str, str] | None], CursorLazyCollection[CommentThread]
    ] = msgspec.field(default_factory=dict, name="_recent_threads")
    _labels: LazyCollection[Label] | None = msgspec.field(default=None, name="_labels")
    _subscribers: LazyCollection[Subscriber] | None = msgspec.field(
        default=None, name="_subscribers"
    )
    _metadata: LazyMapping[str, MetadataValue] | None = msgspec.field(
        default=None, name="_metadata"
    )
    _properties: LazyMapping[str, PropertyValue] | None = msgspec.field(
        default=None, name="_properties"
    )
    _pull_requests: LazyCollection[LinkedPullRequest] | None = msgspec.field(
        default=None, name="_pull_requests"
    )
    _children: LazyCollection[Issue] | None = msgspec.field(default=None, name="_children")
    _runs: LazyCollection[TaskRun] | None = msgspec.field(default=None, name="_runs")
    _parent: object | None = msgspec.field(default=None, name="_parent")
    _project: object | None = msgspec.field(default=None, name="_project")
    _assignee_ref: object | None = msgspec.field(default=None, name="_assignee_ref")

    def __getattribute__(self, name: str) -> object:
        # Partial list rows are still Issue values (the approved page type),
        # while this private immutable projection retains omitted-vs-null state
        # for fields outside the stable Issue declaration.
        if name in {
            "workspace_id",
            "number",
            "identifier",
            "title",
            "description",
            "status",
            "status_category",
            "status_name",
            "priority",
            "assignee_type",
            "assignee_id",
            "creator_type",
            "creator_id",
            "parent_id",
            "project_id",
            "position",
            "stage",
            "start_date",
            "due_date",
            "created_at",
            "updated_at",
            "revision",
            "last_activity_at",
        }:
            projection = cast("Mapping[str, object]", object.__getattribute__(self, "_projection"))
            if name in projection:
                return projection[name]
            if projection:
                return msgspec.UNSET
        return super().__getattribute__(name)

    def __getattr__(self, name: str) -> object:
        projection = cast("Mapping[str, object]", object.__getattribute__(self, "_projection"))
        if isinstance(projection, Mapping) and name in projection:
            return projection[name]
        raise AttributeError(name)

    def _serialized_projection(self) -> Mapping[str, object] | None:
        return self._projection or None

    @classmethod
    def _from_dict_projection(cls, data: dict[str, object]) -> Issue | None:
        projection_input_names = {
            "id",
            "workspace_id",
            "number",
            "identifier",
            "title",
            "description",
            "status",
            "status_category",
            "status_name",
            "priority",
            "assignee_type",
            "assignee_id",
            "creator_type",
            "creator_id",
            "parent_id",
            "parent_issue_id",
            "project_id",
            "position",
            "stage",
            "start_date",
            "due_date",
            "created_at",
            "updated_at",
            "revision",
            "last_activity_at",
            "metadata",
            "properties",
            "labels",
        }
        if "id" not in data or not set(data).issubset(projection_input_names):
            return None
        from multica_py._internal.issue_wires import _issue_from_wire, _IssueWire

        wire_data = dict(data)
        if "parent_id" in wire_data and "parent_issue_id" not in wire_data:
            wire_data["parent_issue_id"] = wire_data["parent_id"]
        wire = msgspec.convert(wire_data, type=_IssueWire, strict=True)
        return _issue_from_wire(wire, allow_partial=True, force_projection=True)

    @classmethod
    def _normalize_from_dict(cls, data: dict[str, object]) -> dict[str, object]:
        status = data.get("status")
        if isinstance(status, str):
            return {**data, "status": _coerce_issue_status(status)}
        return data

    @classmethod
    def _from_encoded_dict(cls, data: dict[str, object]) -> Issue:
        from multica_py._internal.issue_wires import _issue_from_wire, _IssueWire

        wire_data = dict(data)
        status = wire_data.get("status")
        if isinstance(status, IssueStatus):
            wire_data["status"] = status.value
        if "parent_id" in wire_data:
            wire_data["parent_issue_id"] = wire_data.pop("parent_id")
        if "pull_request_snapshot" in wire_data:
            wire_data["pull_requests"] = wire_data.pop("pull_request_snapshot")
        if "child_stages" in wire_data:
            wire_data["children"] = wire_data.pop("child_stages")
        if "label_names" in wire_data:
            label_names = cast("tuple[str, ...] | list[str]", wire_data.pop("label_names"))
            wire_data["labels"] = tuple(
                {"id": f"label-{index}", "name": name} for index, name in enumerate(label_names)
            )
        if "metadata_snapshot" in wire_data:
            metadata_snapshot = cast(
                "tuple[IssueMetadataItem, ...] | list[IssueMetadataItem | Mapping[str, object]]",
                wire_data.pop("metadata_snapshot"),
            )
            wire_data["metadata"] = {
                item.key: item.value
                for item in (
                    item
                    if isinstance(item, IssueMetadataItem)
                    else msgspec.convert(item, type=IssueMetadataItem, strict=True)
                    for item in metadata_snapshot
                )
            }
        for field_name in ("status_name", "revision"):
            if wire_data.get(field_name) is None:
                wire_data.pop(field_name, None)
        wire = msgspec.convert(wire_data, type=_IssueWire, strict=True)
        return _issue_from_wire(wire, include_wire_presence=False)

    def permalink(self) -> str:
        client = cast("MulticaClient | None", self._client)
        return build_permalink(
            entity_type="Issue",
            entity_id=self.id,
            collection="issues",
            app_url=client.config.app_url if client is not None else None,
            workspace_slug=client.config.workspace_slug if client is not None else None,
        )

    @property
    def parent(self) -> LazyRef[Issue | None]:
        if self._parent is None:
            parent_id = self.parent_id
            client = cast("MulticaClient | None", self._client)
            presence = _reference_presence(self, "parent_id", parent_id)

            def command() -> Command[Issue | None]:
                if presence == "null" and parent_id is None:
                    return _cached_value_command(lambda: None)
                if presence == "missing" or not parent_id:
                    raise MissingRelationContextError("Issue", self.id, "parent", "parent_id")
                if client is None:
                    raise DetachedEntityError("Issue", self.id, "parent")
                return client.issues.get_command(parent_id)

            self._set_runtime(
                "_parent",
                LazyRef(
                    command_loader=command,
                    initial=None if presence == "null" else _GENERATION_UNSET,
                    _prefetch_target=lambda: ("Issue", parent_id),
                    _origin_client=client,
                    entity_type="Issue",
                    entity_id=self.id,
                    relation_name="parent",
                ),
            )
        return self._parent  # type: ignore[return-value]

    @property
    def project(self) -> LazyRef[Project | None]:
        if self._project is None:
            project_id = self.project_id
            client = cast("MulticaClient | None", self._client)
            presence = _reference_presence(self, "project_id", project_id)

            def command() -> Command[Project | None]:
                if presence == "null" and project_id is None:
                    return _cached_value_command(lambda: None)
                if presence == "missing" or not project_id:
                    raise MissingRelationContextError("Issue", self.id, "project", "project_id")
                if client is None:
                    raise DetachedEntityError("Issue", self.id, "project")
                return client.projects.get_command(project_id)

            self._set_runtime(
                "_project",
                LazyRef(
                    command_loader=command,
                    initial=None if presence == "null" else _GENERATION_UNSET,
                    _prefetch_target=lambda: ("Project", project_id),
                    _origin_client=client,
                    entity_type="Issue",
                    entity_id=self.id,
                    relation_name="project",
                ),
            )
        return self._project  # type: ignore[return-value]

    @property
    def assignee_ref(self) -> LazyRef[Agent | Squad | None]:
        if self._assignee_ref is None:
            assignee = self.assignee
            client = cast("MulticaClient | None", self._client)
            presence = _reference_presence(self, "assignee", assignee)

            def target() -> tuple[str, str] | None:
                if assignee is None:
                    return None
                if not assignee.id:
                    raise MissingRelationContextError(
                        "Issue", self.id, "assignee_ref", "assignee_id"
                    )
                if assignee.type not in {"agent", "squad"}:
                    if assignee.type is None:
                        return None
                    raise UnsupportedReferenceTargetError(
                        "Issue", self.id, "assignee_ref", "assignee_type", assignee.type
                    )
                return assignee.type, assignee.id

            def command() -> Command[Agent | Squad | None]:
                if presence == "null" and assignee is None:
                    return _cached_value_command(lambda: None)
                if presence == "missing" and assignee is None:
                    raise MissingRelationContextError("Issue", self.id, "assignee_ref", "assignee")
                resolved = target()
                if resolved is None:
                    raise MissingRelationContextError(
                        "Issue", self.id, "assignee_ref", "assignee_type"
                    )
                discriminator, assignee_id = resolved
                if client is None:
                    raise DetachedEntityError("Issue", self.id, "assignee_ref")
                if discriminator == "agent":
                    return client.agents.get_command(assignee_id)
                return client.squads.get_command(assignee_id)

            self._set_runtime(
                "_assignee_ref",
                LazyRef(
                    command_loader=command,
                    initial=None if presence == "null" and assignee is None else _GENERATION_UNSET,
                    _prefetch_target=target,
                    _origin_client=client,
                    entity_type="Issue",
                    entity_id=self.id,
                    relation_name="assignee_ref",
                ),
            )
        return self._assignee_ref  # type: ignore[return-value]

    @property
    def comments(self) -> LazyCollection[Comment]:
        if self._comments is None:
            client = self._require_client(
                entity_type="Issue", entity_id=self.id, relation_name="comments"
            )
            issue_id = self.id

            def loader() -> tuple[Comment, ...]:
                page = client.issues.comments.list_flat(issue_id=issue_id)
                return tuple(_bind_comment(item, client) for item in page.items)

            def command_loader() -> Command[tuple[Comment, ...]]:
                return client.issues._comments_relation_command(issue_id)

            self._set_runtime("_comments", LazyCollection(loader, command_loader=command_loader))
        return self._comments  # type: ignore[return-value]

    def recent_comment_threads(
        self,
        limit: int = 10,
        *,
        cursor: CommentCursor | None = None,
    ) -> CursorLazyCollection[CommentThread]:
        if limit < 1:
            raise ValueError("limit must be positive")
        key = (limit, None if cursor is None else (cursor.before, cursor.before_id))
        if key not in self._recent_threads:
            client = self._require_client(
                entity_type="Issue", entity_id=self.id, relation_name="recent_comment_threads"
            )
            issue_id = self.id

            def page_loader(*, cursor: CommentCursor | None) -> CursorPage[CommentThread]:
                page = client.issues.comments.list_recent(
                    issue_id=issue_id, limit=limit, cursor=cursor
                )
                return CursorPage(
                    items=tuple(_bind_thread(item, client, issue_id) for item in page.items),
                    next_cursor=cast("CommentCursor | None", page.next_cursor),
                )

            def page_command_loader(
                next_cursor: CommentCursor | None,
            ) -> Command[CursorPage[CommentThread]]:
                return client.issues._recent_comment_threads_relation_command(
                    issue_id, limit=limit, cursor=next_cursor
                )

            self._recent_threads[key] = CursorLazyCollection(
                page_loader,
                initial_cursor=cursor,
                page_command_loader=page_command_loader,
            )
        return self._recent_threads[key]

    @property
    def labels(self) -> LazyCollection[Label]:
        if self._labels is None:
            client = self._require_client(
                entity_type="Issue", entity_id=self.id, relation_name="labels"
            )
            issue_id = self.id

            def _load_labels() -> tuple[Label, ...]:
                return client.issues._labels_relation(issue_id)

            def _load_labels_command() -> Command[tuple[Label, ...]]:
                return client.issues._labels_relation_command(issue_id)

            self._set_runtime(
                "_labels",
                LazyCollection[Label](
                    _load_labels,
                    command_loader=_load_labels_command,
                ),
            )
        return self._labels  # type: ignore[return-value]

    @property
    def subscribers(self) -> LazyCollection[Subscriber]:
        if self._subscribers is None:
            client = self._require_client(
                entity_type="Issue", entity_id=self.id, relation_name="subscribers"
            )
            issue_id = self.id
            subscribers = client.issues.subscribers
            self._set_runtime(
                "_subscribers",
                LazyCollection[Subscriber](
                    lambda: _page_items(subscribers.list(issue_id)),
                    command_loader=lambda: client.issues._subscribers_relation_command(issue_id),
                ),
            )
        return self._subscribers  # type: ignore[return-value]

    @property
    def metadata(self) -> LazyMapping[str, MetadataValue]:
        if self._metadata is None:
            client = self._require_client(
                entity_type="Issue", entity_id=self.id, relation_name="metadata"
            )
            issue_id = self.id
            metadata_resource = client.issues.metadata

            def loader() -> Mapping[str, MetadataValue]:
                return metadata_resource.list(issue_id)

            self._set_runtime(
                "_metadata",
                LazyMapping[str, MetadataValue](
                    loader,
                    command_loader=lambda: client.issues._metadata_relation_command(issue_id),
                ),
            )
        return self._metadata  # type: ignore[return-value]

    @property
    def properties(self) -> LazyMapping[str, PropertyValue]:
        if self._properties is None:
            client = self._require_client(
                entity_type="Issue", entity_id=self.id, relation_name="properties"
            )
            issue_id = self.id
            properties_resource = client.issues.properties

            def loader() -> Mapping[str, PropertyValue]:
                return {row.name: row for row in properties_resource.list(issue_id)}

            initial = _property_relation_initial(self._property_projection)
            command_loader = (
                None
                if initial is not None
                else lambda: client.issues._properties_relation_command(issue_id)
            )
            self._set_runtime(
                "_properties",
                LazyMapping[str, PropertyValue](
                    loader,
                    command_loader=command_loader,
                    initial=initial,
                ),
            )
        return self._properties  # type: ignore[return-value]

    @property
    def pull_requests(self) -> LazyCollection[LinkedPullRequest]:
        if self._pull_requests is None:
            client = self._require_client(
                entity_type="Issue", entity_id=self.id, relation_name="pull_requests"
            )
            issue_id = self.id
            issues = client.issues
            self._set_runtime(
                "_pull_requests",
                LazyCollection[LinkedPullRequest](
                    lambda: _page_items(issues.pull_requests(issue_id)),
                    command_loader=lambda: issues._pull_requests_relation_command(issue_id),
                ),
            )
        return self._pull_requests  # type: ignore[return-value]

    @property
    def children(self) -> LazyCollection[Issue]:
        if self._children is None:
            client = self._require_client(
                entity_type="Issue", entity_id=self.id, relation_name="children"
            )
            issue_id = self.id

            def loader() -> _RelationLoad[Issue]:
                result: IssueChildrenResult = client.issues.children(issue_id)
                return _RelationLoad(
                    tuple(item._with_client(client) for item in result.children),
                    RelationMetadata(
                        total=result.total,
                        child_stages=result.child_stages,
                        unstaged=tuple(item._with_client(client) for item in result.unstaged),
                    ),
                )

            def command_loader() -> Command[_RelationLoad[Issue]]:
                return client.issues._children_relation_command(issue_id)

            self._set_runtime("_children", LazyCollection(loader, command_loader=command_loader))
        return self._children  # type: ignore[return-value]

    @property
    def runs(self) -> LazyCollection[TaskRun]:
        if self._runs is None:
            client = self._require_client(
                entity_type="Issue", entity_id=self.id, relation_name="runs"
            )
            issue_id = self.id

            def loader() -> tuple[TaskRun, ...]:
                runs = _page_items(client.issues.runs(issue_id))
                return tuple(run._with_client(client) for run in runs)

            def command_loader() -> Command[tuple[TaskRun, ...]]:
                return client.issues._runs_relation_command(issue_id)

            self._set_runtime(
                "_runs",
                LazyCollection[TaskRun](
                    loader,
                    command_loader=command_loader,
                ),
            )
        return self._runs  # type: ignore[return-value]

    def refresh_command(self, *, options: OperationOptions | None = None) -> Command[Issue]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="refresh"
        )
        return client.issues.get_command(self.id, options=options)

    def refresh(self, *, options: OperationOptions | None = None) -> Issue:
        return self.refresh_command(options=options).run()

    def update_command(
        self,
        *,
        title: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        priority: str | UnsetType = Unset,
        assignee_id: str | None | UnsetType = Unset,
        project_id: str | None | UnsetType = Unset,
        parent_id: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[Issue]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="update"
        )
        return client.issues.update_command(
            self.id,
            title=title,
            description=description,
            priority=priority,
            assignee_id=assignee_id,
            project_id=project_id,
            parent_id=parent_id,
            options=options,
        )

    def update(
        self,
        *,
        title: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        priority: str | UnsetType = Unset,
        assignee_id: str | None | UnsetType = Unset,
        project_id: str | None | UnsetType = Unset,
        parent_id: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.update_command(
            title=title,
            description=description,
            priority=priority,
            assignee_id=assignee_id,
            project_id=project_id,
            parent_id=parent_id,
            options=options,
        ).run()

    def assign_command(
        self, assignee: AssignmentTarget, *, options: OperationOptions | None = None
    ) -> Command[Issue]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="assign"
        )
        return client.issues.assign_command(self.id, assignee, options=options)

    def assign(
        self, assignee: AssignmentTarget, *, options: OperationOptions | None = None
    ) -> Issue:
        return self.assign_command(assignee, options=options).run()

    def unassign_command(self, *, options: OperationOptions | None = None) -> Command[Issue]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="unassign"
        )
        return client.issues.unassign_command(self.id, options=options)

    def unassign(self, *, options: OperationOptions | None = None) -> Issue:
        return self.unassign_command(options=options).run()

    def set_status_command(
        self, status: IssueStatus | str, *, options: OperationOptions | None = None
    ) -> Command[Issue]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="set_status"
        )
        return client.issues.set_status_command(self.id, status, options=options)

    def set_status(
        self, status: IssueStatus | str, *, options: OperationOptions | None = None
    ) -> Issue:
        return self.set_status_command(status, options=options).run()

    def move_to_top_command(self, *, options: OperationOptions | None = None) -> Command[Issue]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="move_to_top"
        )
        return client.issues.move_to_top_command(self.id, options=options)

    def move_to_top(self, *, options: OperationOptions | None = None) -> Issue:
        return self.move_to_top_command(options=options).run()

    def move_to_bottom_command(self, *, options: OperationOptions | None = None) -> Command[Issue]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="move_to_bottom"
        )
        return client.issues.move_to_bottom_command(self.id, options=options)

    def move_to_bottom(self, *, options: OperationOptions | None = None) -> Issue:
        return self.move_to_bottom_command(options=options).run()

    def move_before_command(
        self, other_issue: IssueReference, *, options: OperationOptions | None = None
    ) -> Command[Issue]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="move_before"
        )
        return client.issues.move_before_command(self.id, other_issue, options=options)

    def move_before(
        self, other_issue: IssueReference, *, options: OperationOptions | None = None
    ) -> Issue:
        return self.move_before_command(other_issue, options=options).run()

    def move_after_command(
        self, other_issue: IssueReference, *, options: OperationOptions | None = None
    ) -> Command[Issue]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="move_after"
        )
        return client.issues.move_after_command(self.id, other_issue, options=options)

    def move_after(
        self, other_issue: IssueReference, *, options: OperationOptions | None = None
    ) -> Issue:
        return self.move_after_command(other_issue, options=options).run()

    def add_comment_command(
        self, body: str, *, options: OperationOptions | None = None
    ) -> Command[Comment]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="comments"
        )

        return client.issues._add_comment_command(
            self.id, body, invalidate=self._invalidate_comments, options=options
        )

    def add_comment(self, body: str, *, options: OperationOptions | None = None) -> Comment:
        return self.add_comment_command(body, options=options).run()

    def reply_command(
        self, thread_id: str, body: str, *, options: OperationOptions | None = None
    ) -> Command[Comment]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="comments"
        )

        return client.issues._reply_command(
            self.id,
            thread_id,
            body,
            invalidate=self._invalidate_comments,
            options=options,
        )

    def reply(
        self, thread_id: str, body: str, *, options: OperationOptions | None = None
    ) -> Comment:
        return self.reply_command(thread_id, body, options=options).run()

    def add_label_command(
        self, label_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[Label]]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="labels"
        )

        return client.issues._add_label_command(
            self.id, label_id, invalidate=self._invalidate_labels, options=options
        )

    def add_label(self, label_id: str, *, options: OperationOptions | None = None) -> Page[Label]:
        return self.add_label_command(label_id, options=options).run()

    def remove_label_command(
        self, label_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[Label]]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="labels"
        )

        return client.issues._remove_label_command(
            self.id, label_id, invalidate=self._invalidate_labels, options=options
        )

    def remove_label(
        self, label_id: str, *, options: OperationOptions | None = None
    ) -> Page[Label]:
        return self.remove_label_command(label_id, options=options).run()

    def add_subscriber_command(
        self, user_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="subscribers"
        )

        return client.issues._add_subscriber_command(
            self.id, user_id, invalidate=self._invalidate_subscribers, options=options
        )

    def add_subscriber(
        self, user_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.add_subscriber_command(user_id, options=options).run()

    def remove_subscriber_command(
        self, user_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="subscribers"
        )

        return client.issues._remove_subscriber_command(
            self.id, user_id, invalidate=self._invalidate_subscribers, options=options
        )

    def remove_subscriber(
        self, user_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.remove_subscriber_command(user_id, options=options).run()

    def set_metadata_command(
        self, key: str, value: MetadataValue, *, options: OperationOptions | None = None
    ) -> Command[MetadataEntry]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="metadata"
        )

        return client.issues._set_metadata_command(
            self.id, key, value, invalidate=self._invalidate_metadata, options=options
        )

    def set_metadata(
        self, key: str, value: MetadataValue, *, options: OperationOptions | None = None
    ) -> MetadataEntry:
        return self.set_metadata_command(key, value, options=options).run()

    def delete_metadata_command(
        self, key: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="metadata"
        )

        return client.issues._delete_metadata_command(
            self.id, key, invalidate=self._invalidate_metadata, options=options
        )

    def delete_metadata(
        self, key: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_metadata_command(key, options=options).run()

    def _invalidate_comments(self) -> None:
        if self._comments is not None:
            self._comments.invalidate()
        for relation in self._recent_threads.values():
            relation.invalidate()

    def _invalidate_labels(self) -> None:
        if self._labels is not None:
            self._labels.invalidate()

    def _invalidate_subscribers(self) -> None:
        if self._subscribers is not None:
            self._subscribers.invalidate()

    def _invalidate_metadata(self) -> None:
        if self._metadata is not None:
            self._metadata.invalidate()
