from __future__ import annotations

import datetime
import json
import os
from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import TYPE_CHECKING, cast, overload

from multica_py._generated.approved_sdk import (
    ISSUE_TIMELINE_BINDING,
    validate_nonblank,
    validate_since_cursor,
)
from multica_py._internal.commands import Command, _replace_plan, _Step, _StepRef
from multica_py._internal.decoders import decode_json
from multica_py._internal.issue_wires import (
    _issue_children_result_from_wire,
    _issue_from_wire,
    _issue_list_page_from_wire,
    _issue_pull_requests_from_wire,
    _IssueChildrenResultWire,
    _IssueListPageWire,
    _IssuePullRequestsResultWire,
    _IssueSearchResultWire,
    _IssueWire,
    _LabelWire,
)
from multica_py._internal.json_values import _coerce_json_value
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import _task_run_from_wire, _TaskRunWire, decode_run_messages
from multica_py.config import ClientConfig, OperationOptions
from multica_py.entities._base import _normalize_entity_id
from multica_py.entities.comments import Comment, CommentThread
from multica_py.entities.issues import Issue, TaskRun
from multica_py.entities.labels import Label
from multica_py.enums import IssueStatus
from multica_py.exceptions import JsonOutputError, OutputShapeError
from multica_py.models.common import ActionResult, Page
from multica_py.models.issue_activity import (
    CommentCursor,
    IssueUsage,
    MetadataEntry,
    RunMessage,
    Subscriber,
)
from multica_py.models.issue_timeline import IssueTimelineEvent, IssueTimelinePage
from multica_py.models.issues import (
    AssignmentTarget,
    FileDescription,
    InlineDescription,
    IssueChildrenResult,
    IssueDescriptionInput,
    IssueListFilter,
    IssueListPage,
    IssueMetadataItem,
    IssuePropertyAssignment,
    IssueReference,
    LinkedPullRequest,
    NoDescription,
    ProjectReference,
    StdinDescription,
)
from multica_py.models.properties import PropertyValue
from multica_py.models.relations import (
    CursorPage,
    OffsetPage,
    RelationMetadata,
    _RelationLoad,
)
from multica_py.resources._base import (
    BaseResource,
    _normalize_description_file,
    _operation_minimum_cli_version,
    _page_items,
)
from multica_py.resources.issue_comments import IssueCommentResource
from multica_py.resources.issue_labels import IssueLabelResource
from multica_py.resources.issue_metadata import IssueMetadataResource
from multica_py.resources.issue_properties import IssuePropertyResource
from multica_py.resources.issue_subscribers import IssueSubscriberResource
from multica_py.sentinels import Unset, UnsetType
from multica_py.types import MetadataValue

if TYPE_CHECKING:
    from multica_py.client import MulticaClient

__all__ = ["Issue", "IssueResource", "TaskRun"]


_NO_DESCRIPTION_TYPE: type[object] = type(NoDescription())
_STDIN_DESCRIPTION_TYPE: type[object] = type(StdinDescription())

_VALID_ISSUE_FIELDS = frozenset(
    {
        "id",
        "workspace_id",
        "number",
        "identifier",
        "title",
        "description",
        "status",
        "duplicate_of",
        "status_category",
        "status_name",
        "priority",
        "assignee_type",
        "assignee_id",
        "creator_type",
        "creator_id",
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
)
_VALID_ISSUE_SORTS = frozenset(
    {"position", "title", "created_at", "start_date", "due_date", "priority", "status"}
)
_PROPERTY_OPERATORS = (">=", "<=", "!=")


def _normalize_issue_fields(fields: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(fields, tuple):
        raise TypeError("fields must be a tuple of strings")
    normalized: list[str] = []
    for raw_field in fields:
        if type(raw_field) is not str:
            raise TypeError("fields must contain only strings")
        field = raw_field.strip()
        if not field or field not in _VALID_ISSUE_FIELDS:
            raise ValueError(f"IssueResource.list: invalid field {field!r}")
        if field in normalized:
            raise ValueError(f"IssueResource.list: duplicate field {field!r}")
        normalized.append(field)
    return tuple(normalized)


def _normalize_property_filters(filters: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(filters, tuple):
        raise TypeError("property_filters must be a tuple of strings")
    normalized: list[str] = []
    for raw_expression in filters:
        if type(raw_expression) is not str:
            raise TypeError("property_filters must contain only strings")
        expression = raw_expression.strip()
        if not expression or "=" not in expression:
            raise ValueError("IssueResource.list: property filters must use Name=Value")
        if any(operator in expression for operator in _PROPERTY_OPERATORS):
            raise ValueError(
                "IssueResource.list: property comparisons >=, <=, and != are unsupported"
            )
        name, value = expression.split("=", 1)
        if not name.strip() or not value.strip():
            raise ValueError("IssueResource.list: property filters must use Name=Value")
        normalized.append(expression)
    return tuple(normalized)


def _normalize_issue_sort(sort: object) -> str | None:
    if sort is None:
        return None
    if not isinstance(sort, str):
        raise TypeError("sort must be a sort string")
    if sort in _VALID_ISSUE_SORTS:
        return sort
    if sort.startswith("property:") and sort.removeprefix("property:").strip():
        return sort
    raise ValueError(f"IssueResource.list: invalid sort {sort!r}")


def _normalize_issue_direction(direction: object) -> str | None:
    if direction is None:
        return None
    if not isinstance(direction, str):
        raise TypeError("direction must be a sort direction string")
    if direction not in {"asc", "desc"}:
        raise ValueError(f"IssueResource.list: invalid direction {direction!r}")
    return direction


def _validate_issue_query_options(
    *, limit: int | None, offset: int | None, resolve_properties: bool
) -> None:
    if limit is not None and (type(limit) is not int or not 1 <= limit <= 100):
        raise ValueError("IssueResource.list: limit must be between 1 and 100")
    if offset is not None and (type(offset) is not int or offset < 0):
        raise ValueError("IssueResource.list: offset must be nonnegative (offset_nonnegative)")
    if type(resolve_properties) is not bool:
        raise TypeError("resolve_properties must be a bool")


def _issue_status_token(value: IssueStatus | str) -> str:
    if isinstance(value, IssueStatus):
        return value.value
    if type(value) is str:
        return value
    raise TypeError("status must be an IssueStatus or status string")


def _assignee_assign_args(assignee: AssignmentTarget) -> tuple[str, ...]:
    from multica_py.entities.agents import Agent
    from multica_py.entities.squads import Squad
    from multica_py.entities.workspaces import WorkspaceMember

    allowed_types = (Agent, Squad, WorkspaceMember)
    if isinstance(assignee, allowed_types):
        return (
            "--to-id",
            _normalize_entity_id(
                assignee,
                field_name="assignee",
                allowed_types=allowed_types,
            ),
        )
    if isinstance(assignee, str):
        if not assignee.strip():
            raise ValueError("assignee must be non-empty")
        if "@" in assignee:
            return ("--assignee", assignee)
        return ("--to-id", assignee)
    raise TypeError("assignee must be a non-empty ID or one of: Agent, Squad, WorkspaceMember")


def _normalize_issue_reference(value: IssueReference, *, field_name: str = "other_issue") -> str:
    return _normalize_entity_id(value, field_name=field_name, allowed_types=(Issue,))


def _normalize_project_reference(value: ProjectReference) -> str:
    from multica_py.entities.projects import Project

    return _normalize_entity_id(value, field_name="project", allowed_types=(Project,))


def _normalize_project_id(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("project_id must be a non-empty string")
    if not value.strip():
        raise ValueError("project_id must be non-empty")
    return value


def _normalize_issue_description(
    description: str | None,
    description_file: str | os.PathLike[str] | None,
    description_input: IssueDescriptionInput | None,
    *,
    cwd: str | os.PathLike[str] | None,
) -> tuple[str, ...]:
    sources = sum(value is not None for value in (description, description_file, description_input))
    if sources > 1:
        raise TypeError(
            "description, description_file, and description_input are mutually exclusive"
        )
    if description is not None:
        if not isinstance(description, str):
            raise TypeError("description must be a string or None")
        return ("--description", description)
    if description_file is not None:
        return (
            "--description-file",
            _normalize_description_file(description_file, cwd=cwd),
        )
    if description_input is None or isinstance(description_input, _NO_DESCRIPTION_TYPE):
        return ()
    if isinstance(description_input, InlineDescription):
        if not isinstance(description_input.text, str):
            raise TypeError("description_input.text must be a string")
        return ("--description", description_input.text)
    if isinstance(description_input, FileDescription):
        return (
            "--description-file",
            _normalize_description_file(description_input.path, cwd=cwd),
        )
    if isinstance(description_input, _STDIN_DESCRIPTION_TYPE):
        return ("--description-stdin",)
    raise TypeError("description_input must be a supported issue description")


def _normalize_issue_filter(
    filter: IssueListFilter | None,
    *,
    status: IssueStatus | str | None,
    priority: str | None,
    assignee_id: str | None,
    limit: int | None,
    offset: int | None,
    project_id: str | None,
    sort: str | None,
    direction: str | None,
    metadata: tuple[IssueMetadataItem, ...],
    fields: tuple[str, ...],
    property_filters: tuple[str, ...],
    resolve_properties: bool,
) -> IssueListFilter:
    direct_values = (
        status,
        priority,
        assignee_id,
        limit,
        offset,
        project_id,
        sort,
        cast("object", direction),
        metadata,
        fields,
        property_filters,
        resolve_properties if resolve_properties else None,
    )
    if filter is not None:
        if any(value is not None and value != () for value in direct_values):
            raise TypeError("Pass either an IssueListFilter or direct filter fields, not both.")
        if not isinstance(filter, IssueListFilter):
            raise TypeError(f"Expected IssueListFilter, got {type(filter).__name__}.")
        return filter
    return IssueListFilter(
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        limit=limit,
        offset=offset,
        project_id=project_id,
        sort=sort,
        direction=direction,
        metadata=metadata,
        fields=fields,
        property_filters=property_filters,
        resolve_properties=resolve_properties,
    )


def _normalize_issue_properties(
    properties: tuple[IssuePropertyAssignment, ...],
) -> tuple[IssuePropertyAssignment, ...]:
    if type(properties) is not tuple:
        raise TypeError("properties must be a tuple of IssuePropertyAssignment")
    for assignment in properties:
        if type(assignment) is not IssuePropertyAssignment:
            raise TypeError("properties must contain only IssuePropertyAssignment values")
    return properties


def _decode_issue_search(stdout: bytes, command: str) -> Page[Issue]:
    try:
        envelope = decode_json(stdout, _IssueSearchResultWire, command=command)
    except OutputShapeError as envelope_error:
        try:
            rows = decode_json(stdout, list[_IssueWire], command=command)
        except (OutputShapeError, JsonOutputError):
            raise envelope_error
        items = tuple(_issue_from_wire(row) for row in rows)
        return Page(items=items)
    items = tuple(_issue_from_wire(row) for row in envelope.issues)
    if envelope.total is not None and envelope.total < 0:
        raise OutputShapeError("issue search total must be nonnegative")
    if envelope.has_more and not items:
        raise OutputShapeError("issue search cannot continue after an empty page")
    total = None if envelope.total == 0 and items else envelope.total
    return Page(
        items=items,
        total=total,
        limit=envelope.limit,
        offset=envelope.offset,
        has_more=envelope.has_more,
        next_cursor=envelope.next_cursor,
    )


def _offset_page_from_issue_page(
    page: IssueListPage, *, default_limit: int, default_offset: int
) -> OffsetPage[Issue]:
    limit = page.limit if page.limit is not None else default_limit
    offset = page.offset if page.offset is not None else default_offset
    if not 1 <= limit <= 100:
        raise OutputShapeError("issue list page limit must be between 1 and 100")
    if offset < 0:
        raise OutputShapeError("issue list page offset must be nonnegative")
    if page.total is not None and page.total < 0:
        raise OutputShapeError("issue list page total must be nonnegative")
    if page.has_more and not page.items:
        raise OutputShapeError("issue list page cannot continue after an empty page")
    total = None if page.total == 0 and page.items else page.total
    return OffsetPage(
        items=page.items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=page.has_more,
    )


def _decode_issue_timeline(stdout: bytes, command: str) -> IssueTimelinePage:
    raw = decode_json(stdout, object, command=command)
    if isinstance(raw, list):
        rows = raw
        total = limit = offset = None
        cursor = None
    elif isinstance(raw, Mapping):
        rows = raw.get("events", raw.get("activities", raw.get("items", ())))
        total = raw.get("total") if isinstance(raw.get("total"), int) else None
        limit = raw.get("limit") if isinstance(raw.get("limit"), int) else None
        offset = raw.get("offset") if isinstance(raw.get("offset"), int) else None
        cursor = raw.get("next_cursor") if isinstance(raw.get("next_cursor"), str) else None
    else:
        raise OutputShapeError("issue timeline response must be an array or object")
    if not isinstance(rows, list | tuple):
        raise OutputShapeError("issue timeline items must be an array")
    items: list[IssueTimelineEvent] = []
    for item in rows:
        if not isinstance(item, Mapping):
            raise OutputShapeError("issue timeline item must be an object")
        raw_timestamp = item.get("created_at", item.get("ts"))
        created_at = None
        if isinstance(raw_timestamp, datetime.datetime):
            created_at = raw_timestamp
        elif isinstance(raw_timestamp, str):
            try:
                created_at = datetime.datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
            except ValueError:
                raise OutputShapeError(
                    "issue timeline created_at must be an ISO timestamp"
                ) from None
        items.append(
            IssueTimelineEvent(
                id=str(item.get("id", "")),
                type=str(item.get("type", item.get("event_type", ""))),
                action=cast("str | None", item.get("action")),
                actor_type=cast("str | None", item.get("actor_type")),
                actor_id=cast("str | None", item.get("actor_id")),
                summary=cast("str | None", item.get("summary", item.get("content"))),
                created_at=created_at,
                data=_coerce_json_value(item.get("data"), field_name="timeline.data")
                if item.get("data") is not None
                else None,
                metadata=_coerce_json_value(item.get("metadata"), field_name="timeline.metadata")
                if item.get("metadata") is not None
                else None,
            )
        )
    return IssueTimelinePage(
        items=tuple(items), total=total, limit=limit, offset=offset, next_cursor=cursor
    )


class IssueResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.comments = IssueCommentResource(transport, config)
        self.metadata = IssueMetadataResource(transport, config)
        self.properties = IssuePropertyResource(transport, config)
        self.subscribers = IssueSubscriberResource(transport, config)
        self.labels = IssueLabelResource(transport, config)

    def _set_client(self, client: MulticaClient) -> None:
        super()._set_client(client)
        self.comments._set_client(client)
        self.metadata._set_client(client)
        self.properties._set_client(client)
        self.subscribers._set_client(client)
        self.labels._set_client(client)

    def _labels_relation(self, issue_id: str) -> tuple[Label, ...]:
        return tuple(
            Label(
                id=item.id,
                name=item.name,
                color=item.color,
                description=item.description,
                resource_type=item.resource_type,
                _client=self._client,
            )
            for item in _page_items(self.labels.list(issue_id))
        )

    def _labels_relation_command(self, issue_id: str) -> Command[tuple[Label, ...]]:
        return self.labels.list_command(issue_id)._map(
            lambda page: tuple(
                Label(
                    id=item.id,
                    name=item.name,
                    color=item.color,
                    description=item.description,
                    resource_type=item.resource_type,
                    _client=self._client,
                )
                for item in page.items
            )
        )

    def _comments_relation_command(self, issue_id: str) -> Command[tuple[Comment, ...]]:
        return self.comments.list_flat_command(issue_id=issue_id)._map(
            lambda page: tuple(page.items)
        )

    def _recent_comment_threads_relation_command(
        self, issue_id: str, *, limit: int, cursor: CommentCursor | None
    ) -> Command[CursorPage[CommentThread]]:
        return self.comments._recent_threads_page_command(
            issue_id=issue_id, limit=limit, cursor=cursor
        )

    def _subscribers_relation_command(self, issue_id: str) -> Command[tuple[Subscriber, ...]]:
        return self.subscribers.list_command(issue_id)._map(_page_items)

    def _metadata_relation_command(self, issue_id: str) -> Command[Mapping[str, MetadataValue]]:
        return self.metadata.list_command(issue_id)

    def _properties_relation_command(self, issue_id: str) -> Command[Mapping[str, PropertyValue]]:
        return self.properties.list_command(issue_id)._map(
            lambda rows: {row.name: row for row in rows}
        )

    def _pull_requests_relation_command(
        self, issue_id: str
    ) -> Command[tuple[LinkedPullRequest, ...]]:
        return self.pull_requests_command(issue_id)._map(_page_items)

    def _children_relation_command(self, issue_id: str) -> Command[_RelationLoad[Issue]]:
        return self.children_command(issue_id)._map(
            lambda result: _RelationLoad(
                tuple(result.children),
                RelationMetadata(
                    total=result.total,
                    child_stages=result.child_stages,
                    unstaged=tuple(result.unstaged),
                ),
            )
        )

    def _runs_relation_command(self, issue_id: str) -> Command[tuple[TaskRun, ...]]:
        return self.runs_command(issue_id)._map(_page_items)

    def _run_messages_relation_command(
        self,
        task_run_id: str,
        *,
        issue_id: str | None,
        since: int = 0,
        options: OperationOptions | None = None,
    ) -> Command[tuple[RunMessage, ...]]:
        return self.run_messages_command(
            task_run_id, issue_id=issue_id, since=since, options=options
        )._map(_page_items)

    def _add_comment_command(
        self,
        issue_id: str,
        body: str,
        *,
        invalidate: Callable[[], None],
        options: OperationOptions | None,
    ) -> Command[Comment]:
        def finalize(result: Comment) -> Comment:
            invalidate()
            return result

        return self.comments.add_command(issue_id, body, options=options)._map(finalize)

    def _reply_command(
        self,
        issue_id: str,
        thread_id: str,
        body: str,
        *,
        invalidate: Callable[[], None],
        options: OperationOptions | None,
    ) -> Command[Comment]:
        def finalize(result: Comment) -> Comment:
            invalidate()
            return result

        return self.comments.reply_command(issue_id, thread_id, body, options=options)._map(
            finalize
        )

    def _add_label_command(
        self,
        issue_id: str,
        label_id: str,
        *,
        invalidate: Callable[[], None],
        options: OperationOptions | None,
    ) -> Command[Page[Label]]:
        def finalize(result: Page[Label]) -> Page[Label]:
            invalidate()
            return result

        return self.labels._add_bound_command(issue_id, label_id, options=options)._map(finalize)

    def _remove_label_command(
        self,
        issue_id: str,
        label_id: str,
        *,
        invalidate: Callable[[], None],
        options: OperationOptions | None,
    ) -> Command[Page[Label]]:
        def finalize(result: Page[Label]) -> Page[Label]:
            invalidate()
            return result

        return self.labels._remove_bound_command(issue_id, label_id, options=options)._map(finalize)

    def _add_subscriber_command(
        self,
        issue_id: str,
        user_id: str,
        *,
        invalidate: Callable[[], None],
        options: OperationOptions | None,
    ) -> Command[ActionResult[None]]:
        def finalize(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                invalidate()
            return result

        return self.subscribers.add_command(issue_id, user_id, options=options)._map(finalize)

    def _remove_subscriber_command(
        self,
        issue_id: str,
        user_id: str,
        *,
        invalidate: Callable[[], None],
        options: OperationOptions | None,
    ) -> Command[ActionResult[None]]:
        def finalize(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                invalidate()
            return result

        return self.subscribers.remove_command(issue_id, user_id, options=options)._map(finalize)

    def _set_metadata_command(
        self,
        issue_id: str,
        key: str,
        value: MetadataValue,
        *,
        invalidate: Callable[[], None],
        options: OperationOptions | None,
    ) -> Command[MetadataEntry]:
        def finalize(result: MetadataEntry) -> MetadataEntry:
            invalidate()
            return result

        return self.metadata.set_command(issue_id, key, value, options=options)._map(finalize)

    def _delete_metadata_command(
        self,
        issue_id: str,
        key: str,
        *,
        invalidate: Callable[[], None],
        options: OperationOptions | None,
    ) -> Command[ActionResult[None]]:
        def finalize(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                invalidate()
            return result

        return self.metadata.delete_command(issue_id, key, options=options)._map(finalize)

    def _offset_page(self, issue_filter: IssueListFilter) -> OffsetPage[Issue]:
        page = self.list(issue_filter)
        return _offset_page_from_issue_page(
            page,
            default_limit=50 if issue_filter.limit is None else issue_filter.limit,
            default_offset=0 if issue_filter.offset is None else issue_filter.offset,
        )

    def _offset_page_command(self, issue_filter: IssueListFilter) -> Command[OffsetPage[Issue]]:
        command = self.list_command(issue_filter)
        plan = command._plan
        source_step = plan.steps[0]
        default_limit = 50 if issue_filter.limit is None else issue_filter.limit
        default_offset = 0 if issue_filter.offset is None else issue_filter.offset

        def decode_page(stdout: bytes, command_text: str) -> object:
            if source_step.decode is None:
                raise RuntimeError("issue list command has no decoder")
            decoded = source_step.decode(stdout, command_text)
            if isinstance(decoded, _IssueListPageWire):
                page = _issue_list_page_from_wire(decoded, fields=issue_filter.fields or None)
            elif isinstance(decoded, IssueListPage):
                page = decoded
            else:
                raise TypeError("issue list command decoder returned an unexpected page")
            page = self._bind_issue_list_page(page)
            return _offset_page_from_issue_page(
                page,
                default_limit=default_limit,
                default_offset=default_offset,
            )

        return Command(
            _replace_plan(
                plan,
                steps=(replace(source_step, decode=decode_page),),
                finalize=lambda results: cast("OffsetPage[Issue]", results[0]),
            )
        )

    @overload
    def list_command(
        self, filter: IssueListFilter, /, *, options: OperationOptions | None = None
    ) -> Command[IssueListPage]: ...

    @overload
    def list_command(
        self,
        *,
        status: IssueStatus | str | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        project_id: str | None = None,
        sort: str | None = None,
        direction: str | None = None,
        metadata: tuple[IssueMetadataItem, ...] = (),
        fields: tuple[str, ...] = (),
        property_filters: tuple[str, ...] = (),
        resolve_properties: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[IssueListPage]: ...

    def list_command(  # type: ignore[misc]
        self,
        filter: IssueListFilter | None = None,
        /,
        *,
        status: IssueStatus | str | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        project_id: str | None = None,
        sort: str | None = None,
        direction: str | None = None,
        metadata: tuple[IssueMetadataItem, ...] = (),
        fields: tuple[str, ...] = (),
        property_filters: tuple[str, ...] = (),
        resolve_properties: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[IssueListPage]:
        filter = _normalize_issue_filter(
            filter,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            limit=limit,
            offset=offset,
            project_id=project_id,
            sort=sort,
            direction=direction,
            metadata=metadata,
            fields=fields,
            property_filters=property_filters,
            resolve_properties=resolve_properties,
        )
        args = ["issue", "list"]
        status = _issue_status_token(filter.status) if filter.status is not None else None
        priority = filter.priority
        assignee_id = filter.assignee_id
        limit = filter.limit
        offset = filter.offset
        project_id = filter.project_id
        metadata = filter.metadata
        resolved_sort = _normalize_issue_sort(cast("object", filter.sort))
        resolved_direction = _normalize_issue_direction(cast("object", filter.direction))
        fields = _normalize_issue_fields(filter.fields)
        property_filters = _normalize_property_filters(filter.property_filters)
        if fields and "id" not in fields:
            raise ValueError("IssueResource.list: fields must include id (identity_required)")
        _validate_issue_query_options(
            limit=limit, offset=offset, resolve_properties=filter.resolve_properties
        )
        if filter.resolve_properties and fields and "properties" not in fields:
            raise ValueError("IssueResource.list: resolve_properties requires properties in fields")
        if resolved_direction is not None and resolved_sort is None:
            raise ValueError(
                "IssueResource.list: direction requires sort (direction_requires_sort)"
            )
        if resolved_direction is not None and resolved_sort == "position":
            raise ValueError(
                "IssueResource.list: direction cannot be used with position sort "
                "(position_forbids_direction)"
            )
        if status is not None:
            args.extend(["--status", status])
        if priority is not None:
            args.extend(["--priority", priority])
        if assignee_id is not None:
            args.extend(["--assignee-id", assignee_id])
        if limit is not None:
            args.extend(["--limit", str(limit)])
        if offset is not None:
            args.extend(["--offset", str(offset)])
        if project_id is not None:
            args.extend(["--project", project_id])
        seen_metadata_keys: set[str] = set()
        for item in metadata:
            if not item.key.strip() or "=" in item.key:
                raise ValueError(f"IssueResource.list: invalid metadata key {item.key!r}")
            if item.key in seen_metadata_keys:
                raise ValueError(f"IssueResource.list: duplicate metadata key {item.key!r}")
            seen_metadata_keys.add(item.key)
            encoded = json.dumps(
                item.value,
                ensure_ascii=False,
                separators=(",", ":"),
                allow_nan=False,
            )
            args.extend(["--metadata", f"{item.key}={encoded}"])
        if resolved_sort is not None:
            args.extend(["--sort", resolved_sort])
        if resolved_direction is not None:
            args.extend(["--direction", resolved_direction])
        for expression in property_filters:
            args.extend(["--property", expression])
        if fields:
            args.extend(["--fields", ",".join(fields)])
        if filter.resolve_properties:
            args.append("--resolve-properties")
        return (
            self._decoded_command(tuple(args), _IssueListPageWire, options=options)
            ._map(lambda wire: _issue_list_page_from_wire(wire, fields=fields or None))
            ._map(self._bind_issue_list_page)
        )

    @overload
    def list(
        self, filter: IssueListFilter, /, *, options: OperationOptions | None = None
    ) -> IssueListPage: ...

    @overload
    def list(
        self,
        *,
        status: IssueStatus | str | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        project_id: str | None = None,
        sort: str | None = None,
        direction: str | None = None,
        metadata: tuple[IssueMetadataItem, ...] = (),
        fields: tuple[str, ...] = (),
        property_filters: tuple[str, ...] = (),
        resolve_properties: bool = False,
        options: OperationOptions | None = None,
    ) -> IssueListPage: ...

    def list(  # type: ignore[misc]
        self,
        filter: IssueListFilter | None = None,
        /,
        *,
        status: IssueStatus | str | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        project_id: str | None = None,
        sort: str | None = None,
        direction: str | None = None,
        metadata: tuple[IssueMetadataItem, ...] = (),
        fields: tuple[str, ...] = (),
        property_filters: tuple[str, ...] = (),
        resolve_properties: bool = False,
        options: OperationOptions | None = None,
    ) -> IssueListPage:
        normalized = _normalize_issue_filter(
            filter,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            limit=limit,
            offset=offset,
            project_id=project_id,
            sort=sort,
            direction=direction,
            metadata=metadata,
            fields=fields,
            property_filters=property_filters,
            resolve_properties=resolve_properties,
        )
        return self.list_command(normalized, options=options).run()

    def get_command(
        self,
        issue_id: str,
        *,
        resolve_properties: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[Issue]:
        validate_nonblank(issue_id)
        if type(resolve_properties) is not bool:
            raise TypeError("resolve_properties must be a bool")
        args = ["issue", "get", issue_id]
        if resolve_properties:
            args.append("--resolve-properties")
        return self._decoded_command(tuple(args), _IssueWire, options=options)._map(
            self._bind_issue
        )

    def get(
        self,
        issue_id: str,
        *,
        resolve_properties: bool = False,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.get_command(
            issue_id, resolve_properties=resolve_properties, options=options
        ).run()

    def pull_requests_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[LinkedPullRequest]]:
        return self._decoded_command(
            ("issue", "pull-requests", issue_id), _IssuePullRequestsResultWire, options=options
        )._map(
            lambda result: Page(
                items=_issue_pull_requests_from_wire(result), total=len(result.pull_requests)
            )
        )

    def pull_requests(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Page[LinkedPullRequest]:
        return self.pull_requests_command(issue_id, options=options).run()

    def children_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[IssueChildrenResult]:
        return (
            self._decoded_command(
                ("issue", "children", issue_id), _IssueChildrenResultWire, options=options
            )
            ._map(_issue_children_result_from_wire)
            ._map(self._bind_issue_children_result)
        )

    def children(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> IssueChildrenResult:
        return self.children_command(issue_id, options=options).run()

    def timeline_command(
        self,
        issue_id: str,
        *,
        activity_only: bool = False,
        actions: tuple[str, ...] = (),
        since: str | None = None,
        tail: int | None = None,
        options: OperationOptions | None = None,
    ) -> Command[IssueTimelinePage]:
        _ = cast("object", ISSUE_TIMELINE_BINDING)
        validate_nonblank(issue_id)
        if type(activity_only) is not bool:
            raise TypeError("activity_only must be a bool")
        if type(actions) is not tuple or any(
            type(action) is not str or not action for action in actions
        ):
            raise TypeError("actions must be a tuple of nonblank strings")
        if since is not None and not isinstance(since, str):
            raise TypeError("since must be a string or None")
        if tail is not None and (type(tail) is not int or tail < 0):
            raise ValueError("tail must be nonnegative")
        args = ["issue", "timeline", issue_id]
        if activity_only:
            args.append("--activity-only")
        for action in actions:
            args.extend(("--action", action))
        if since:
            args.extend(("--since", since))
        if tail is not None:
            args.extend(("--tail", str(tail)))
        return self._plan(
            steps=(
                _Step(
                    (*args, "--output", "json"),
                    "run_bytes",
                    decode=_decode_issue_timeline,
                ),
            ),
            finalize=lambda results: cast("IssueTimelinePage", results[0]),
            options=options,
            minimum_cli_version=_operation_minimum_cli_version(
                cast("object", ISSUE_TIMELINE_BINDING)
            ),
        )

    def timeline(
        self,
        issue_id: str,
        *,
        activity_only: bool = False,
        actions: tuple[str, ...] = (),
        since: str | None = None,
        tail: int | None = None,
        options: OperationOptions | None = None,
    ) -> IssueTimelinePage:
        return self.timeline_command(
            issue_id,
            activity_only=activity_only,
            actions=actions,
            since=since,
            tail=tail,
            options=options,
        ).run()

    def create_command(
        self,
        *,
        title: str,
        description: str | None = None,
        description_file: str | os.PathLike[str] | None = None,
        description_input: IssueDescriptionInput | None = None,
        priority: str | None = None,
        status: IssueStatus | str | None = None,
        stage: int | None = None,
        start_date: str | None = None,
        due_date: str | None = None,
        assignee_id: str | None = None,
        label_ids: tuple[str, ...] = (),
        properties: tuple[IssuePropertyAssignment, ...] = (),
        project: ProjectReference | None = None,
        project_id: str | None = None,
        parent_id: str | None = None,
        attachments: tuple[str, ...] = (),
        no_start: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[Issue]:
        """Create an issue and optionally attach labels.

        Creates the issue first, then attaches each ``label_ids`` entry via
        separate ``issue label add`` calls. A failure mid-loop can leave a
        partially labeled issue.
        """
        validate_nonblank(title)
        if parent_id is not None and not parent_id.strip():
            raise ValueError("parent_id must be non-empty when set")
        description_args = _normalize_issue_description(
            description,
            description_file,
            description_input,
            cwd=self._effective_config(options).cwd,
        )
        if project is not None and project_id is not None:
            raise TypeError("project and project_id are mutually exclusive")
        normalized_project = (
            _normalize_project_reference(project)
            if project is not None
            else _normalize_project_id(project_id)
            if project_id is not None
            else None
        )
        properties = _normalize_issue_properties(properties)
        args = ["issue", "create", "--title", title]
        args.extend(description_args)
        if priority is not None:
            args.extend(["--priority", priority])
        if status is not None:
            args.extend(["--status", _issue_status_token(status)])
        if stage is not None:
            if type(stage) is not int or stage < 0:
                raise ValueError("stage must be a nonnegative integer")
            args.extend(["--stage", str(stage)])
        if start_date is not None:
            args.extend(["--start-date", start_date])
        if due_date is not None:
            args.extend(["--due-date", due_date])
        if assignee_id is not None:
            args.extend(["--assignee-id", assignee_id])
        if normalized_project is not None:
            args.extend(["--project", normalized_project])
        if parent_id is not None:
            args.extend(["--parent", parent_id])
        for attachment in attachments:
            validate_nonblank(attachment)
            args.extend(["--attachment", attachment])
        if no_start:
            args.append("--no-start")
        for assignment in properties:
            args.extend(["--property", f"{assignment.reference}={assignment.value}"])
        create_args, create_decode = self._plan_decode(tuple(args), _IssueWire)
        steps = [_Step(create_args, "run_bytes", decode=create_decode, result_alias="create")]
        for label_id in label_ids:
            label_args, label_decode = self._plan_decode_list(
                ("issue", "label", "add", "", label_id), _LabelWire
            )
            steps.append(
                _Step(
                    label_args,
                    "run_bytes",
                    refs=((3, _StepRef("result", field="id", alias="create")),),
                    decode=label_decode,
                )
            )
        if label_ids:
            get_args, get_decode = self._plan_decode(("issue", "get", ""), _IssueWire)
            steps.append(
                _Step(
                    get_args,
                    "run_bytes",
                    refs=((2, _StepRef("result", field="id", alias="create")),),
                    decode=get_decode,
                )
            )

        def finalize(results: tuple[object, ...]) -> Issue:
            wire = cast("_IssueWire", results[-1] if label_ids else results[0])
            return self._bind_issue(wire)

        return self._plan(
            steps=tuple(steps),
            finalize=finalize,
            options=options,
            minimum_cli_version="0.5.2" if properties else None,
        )

    def create(
        self,
        *,
        title: str,
        description: str | None = None,
        description_file: str | os.PathLike[str] | None = None,
        description_input: IssueDescriptionInput | None = None,
        priority: str | None = None,
        status: IssueStatus | str | None = None,
        stage: int | None = None,
        start_date: str | None = None,
        due_date: str | None = None,
        assignee_id: str | None = None,
        label_ids: tuple[str, ...] = (),
        properties: tuple[IssuePropertyAssignment, ...] = (),
        project: ProjectReference | None = None,
        project_id: str | None = None,
        parent_id: str | None = None,
        attachments: tuple[str, ...] = (),
        no_start: bool = False,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.create_command(
            title=title,
            description=description,
            description_file=description_file,
            description_input=description_input,
            priority=priority,
            status=status,
            stage=stage,
            start_date=start_date,
            due_date=due_date,
            assignee_id=assignee_id,
            label_ids=label_ids,
            properties=properties,
            project=project,
            project_id=project_id,
            parent_id=parent_id,
            attachments=attachments,
            no_start=no_start,
            options=options,
        ).run()

    def update_command(
        self,
        issue_id: str,
        *,
        title: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        priority: str | UnsetType = Unset,
        status: IssueStatus | str | UnsetType = Unset,
        stage: int | None | UnsetType = Unset,
        start_date: str | None | UnsetType = Unset,
        due_date: str | None | UnsetType = Unset,
        position: float | UnsetType = Unset,
        assignee_id: str | None | UnsetType = Unset,
        project_id: str | None | UnsetType = Unset,
        parent_id: str | None | UnsetType = Unset,
        attachments: tuple[str, ...] | UnsetType = Unset,
        no_start: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[Issue]:
        validate_nonblank(issue_id)
        if title is None:
            raise TypeError("title must be non-null")
        if priority is None:
            raise TypeError("priority must be non-null")
        for field_name, value in (("project_id", project_id), ("parent_id", parent_id)):
            if value is not Unset and value is not None and not value.strip():
                raise ValueError(f"{field_name} must be non-empty when set")
        if (
            title is Unset
            and description is Unset
            and priority is Unset
            and status is Unset
            and stage is Unset
            and start_date is Unset
            and due_date is Unset
            and position is Unset
            and assignee_id is Unset
            and project_id is Unset
            and parent_id is Unset
        ):
            return self.get_command(issue_id, options=options)
        args = ["issue", "update", issue_id]
        if title is not Unset:
            args.extend(["--title", title])
        if description is not Unset:
            args.extend(["--description", "" if description is None else description])
        if priority is not Unset:
            args.extend(["--priority", priority])
        if status is not Unset:
            args.extend(["--status", _issue_status_token(status)])
        if stage is not Unset:
            if stage is not None and (type(stage) is not int or stage < 0):
                raise ValueError("stage must be a nonnegative integer")
            args.extend(["--stage", "" if stage is None else str(stage)])
        if start_date is not Unset:
            args.extend(["--start-date", "" if start_date is None else start_date])
        if due_date is not Unset:
            args.extend(["--due-date", "" if due_date is None else due_date])
        if position is not Unset:
            if type(position) not in (int, float) or isinstance(position, bool):
                raise TypeError("position must be a number or Unset")
            args.extend(["--position", str(position)])
        if assignee_id is not Unset and assignee_id is not None:
            args.extend(["--assignee-id", assignee_id])
        if project_id is not Unset:
            args.extend(["--project", "" if project_id is None else project_id])
        if parent_id is not Unset:
            args.extend(["--parent", "" if parent_id is None else parent_id])
        if attachments is not Unset:
            for attachment in attachments:
                validate_nonblank(attachment)
                args.extend(["--attachment", attachment])
        if no_start:
            args.append("--no-start")

        steps: list[_Step] = []
        if len(args) > 3:
            update_args, update_decode = self._plan_decode(tuple(args), _IssueWire)
            steps.append(
                _Step(update_args, "run_bytes", decode=update_decode, result_alias="update")
            )

        if assignee_id is None:
            assign_args, assign_decode = self._plan_decode(
                ("issue", "assign", issue_id, "--unassign"), _IssueWire
            )
            steps.append(
                _Step(assign_args, "run_bytes", decode=assign_decode, result_alias="assign")
            )
            get_args, get_decode = self._plan_decode(("issue", "get", issue_id), _IssueWire)
            steps.append(
                _Step(get_args, "run_bytes", decode=get_decode, result_alias="authoritative")
            )

        def finalize(results: tuple[object, ...]) -> Issue:
            return self._bind_issue(cast("_IssueWire", results[-1]))

        return self._plan(steps=tuple(steps), finalize=finalize, options=options)

    def update(
        self,
        issue_id: str,
        *,
        title: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        priority: str | UnsetType = Unset,
        status: IssueStatus | str | UnsetType = Unset,
        stage: int | None | UnsetType = Unset,
        start_date: str | None | UnsetType = Unset,
        due_date: str | None | UnsetType = Unset,
        position: float | UnsetType = Unset,
        assignee_id: str | None | UnsetType = Unset,
        project_id: str | None | UnsetType = Unset,
        parent_id: str | None | UnsetType = Unset,
        attachments: tuple[str, ...] | UnsetType = Unset,
        no_start: bool = False,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.update_command(
            issue_id,
            title=title,
            description=description,
            priority=priority,
            status=status,
            stage=stage,
            start_date=start_date,
            due_date=due_date,
            position=position,
            assignee_id=assignee_id,
            project_id=project_id,
            parent_id=parent_id,
            attachments=attachments,
            no_start=no_start,
            options=options,
        ).run()

    def assign_command(
        self,
        issue_id: str,
        assignee: AssignmentTarget,
        *,
        no_start: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[Issue]:
        validate_nonblank(issue_id)
        args = ["issue", "assign", issue_id, *_assignee_assign_args(assignee)]
        if type(no_start) is not bool:
            raise TypeError("no_start must be a bool")
        if no_start:
            args.append("--no-start")
        return self._decoded_command(tuple(args), _IssueWire, options=options)._map(
            self._bind_issue
        )

    def assign(
        self,
        issue_id: str,
        assignee: AssignmentTarget,
        *,
        no_start: bool = False,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.assign_command(issue_id, assignee, no_start=no_start, options=options).run()

    def unassign_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[Issue]:
        validate_nonblank(issue_id)
        return self._decoded_command(
            ("issue", "assign", issue_id, "--unassign"), _IssueWire, options=options
        )._map(self._bind_issue)

    def unassign(self, issue_id: str, *, options: OperationOptions | None = None) -> Issue:
        return self.unassign_command(issue_id, options=options).run()

    def set_status_command(
        self,
        issue_id: str,
        status: IssueStatus | str,
        *,
        no_start: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[Issue]:
        validate_nonblank(issue_id)
        status_token = _issue_status_token(status)
        if type(no_start) is not bool:
            raise TypeError("no_start must be a bool")
        args = ["issue", "status", issue_id, status_token]
        if no_start:
            args.append("--no-start")
        return self._decoded_command(tuple(args), _IssueWire, options=options)._map(
            self._bind_issue
        )

    def set_status(
        self,
        issue_id: str,
        status: IssueStatus | str,
        *,
        no_start: bool = False,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.set_status_command(issue_id, status, no_start=no_start, options=options).run()

    def reorder_command(
        self,
        issue_id: str,
        *,
        before_id: str | None = None,
        after_id: str | None = None,
        top: bool = False,
        bottom: bool = False,
        options: OperationOptions | None = None,
    ) -> Command[Issue]:
        validate_nonblank(issue_id)
        selected = sum(value is not None for value in (before_id, after_id)) + top + bottom
        if selected != 1:
            raise ValueError("Exactly one reorder target must be set")
        if before_id is not None:
            validate_nonblank(before_id)
        if after_id is not None:
            validate_nonblank(after_id)
        args = ["issue", "reorder", issue_id]
        if before_id is not None:
            args.extend(["--before", before_id])
        elif after_id is not None:
            args.extend(["--after", after_id])
        elif top:
            args.append("--top")
        elif bottom:
            args.append("--bottom")
        return self._decoded_command(tuple(args), _IssueWire, options=options)._map(
            self._bind_issue
        )

    def reorder(
        self,
        issue_id: str,
        *,
        before_id: str | None = None,
        after_id: str | None = None,
        top: bool = False,
        bottom: bool = False,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.reorder_command(
            issue_id=issue_id,
            before_id=before_id,
            after_id=after_id,
            top=top,
            bottom=bottom,
            options=options,
        ).run()

    def move_to_top_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[Issue]:
        return self.reorder_command(issue_id, top=True, options=options)

    def move_to_top(self, issue_id: str, *, options: OperationOptions | None = None) -> Issue:
        return self.move_to_top_command(issue_id, options=options).run()

    def move_to_bottom_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[Issue]:
        return self.reorder_command(issue_id, bottom=True, options=options)

    def move_to_bottom(self, issue_id: str, *, options: OperationOptions | None = None) -> Issue:
        return self.move_to_bottom_command(issue_id, options=options).run()

    def move_before_command(
        self,
        issue_id: str,
        other_issue: IssueReference,
        *,
        options: OperationOptions | None = None,
    ) -> Command[Issue]:
        return self.reorder_command(
            issue_id,
            before_id=_normalize_issue_reference(other_issue),
            options=options,
        )

    def move_before(
        self,
        issue_id: str,
        other_issue: IssueReference,
        *,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.move_before_command(issue_id, other_issue, options=options).run()

    def move_after_command(
        self,
        issue_id: str,
        other_issue: IssueReference,
        *,
        options: OperationOptions | None = None,
    ) -> Command[Issue]:
        return self.reorder_command(
            issue_id,
            after_id=_normalize_issue_reference(other_issue),
            options=options,
        )

    def move_after(
        self,
        issue_id: str,
        other_issue: IssueReference,
        *,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.move_after_command(issue_id, other_issue, options=options).run()

    def search_command(
        self,
        query: str,
        *,
        limit: int | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Page[Issue]]:
        validate_nonblank(query)
        if limit is not None and (type(limit) is not int or limit < 0):
            raise ValueError("limit must be nonnegative")
        args = ["issue", "search", query]
        if limit is not None:
            args.extend(("--limit", str(limit)))
        args.extend(("--output", "json"))
        return self._plan(
            steps=(_Step(tuple(args), "run_bytes", decode=_decode_issue_search),),
            finalize=lambda results: cast("Page[Issue]", results[0]),
            options=options,
        )._map(self._bind_issue_search_page)

    def search(
        self, query: str, *, limit: int | None = None, options: OperationOptions | None = None
    ) -> Page[Issue]:
        return self.search_command(query, limit=limit, options=options).run()

    def runs_command(
        self,
        issue_id: str,
        *,
        active: bool = False,
        siblings: bool = False,
        limit: int | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Page[TaskRun]]:
        validate_nonblank(issue_id)
        if type(active) is not bool or type(siblings) is not bool:
            raise TypeError("active and siblings must be bools")
        if limit is not None and (type(limit) is not int or limit < 0):
            raise ValueError("limit must be nonnegative")
        args = ["issue", "runs", issue_id]
        if active:
            args.append("--active")
        if siblings:
            args.append("--siblings")
        if limit is not None:
            args.extend(("--limit", str(limit)))

        def finalize(page: Page[_TaskRunWire]) -> Page[TaskRun]:
            return Page(
                items=tuple(
                    _task_run_from_wire(run, issue_id=issue_id)._with_client(self._client)
                    for run in page.items
                ),
                limit=page.limit,
                offset=page.offset,
                total=page.total,
                has_more=page.has_more,
                next_cursor=page.next_cursor,
            )

        return self._decoded_page_command(tuple(args), _TaskRunWire, options=options)._map(finalize)

    def runs(
        self,
        issue_id: str,
        *,
        active: bool = False,
        siblings: bool = False,
        limit: int | None = None,
        options: OperationOptions | None = None,
    ) -> Page[TaskRun]:
        return self.runs_command(
            issue_id,
            active=active,
            siblings=siblings,
            limit=limit,
            options=options,
        ).run()

    def run_messages_command(
        self,
        task_run_id: str,
        *,
        issue_id: str | None = None,
        since: int = 0,
        options: OperationOptions | None = None,
    ) -> Command[Page[RunMessage]]:
        validate_nonblank(task_run_id)
        validate_since_cursor(since)
        args = ["issue", "run-messages", task_run_id]
        if issue_id is not None:
            validate_nonblank(issue_id)
            args.extend(["--issue", issue_id])
        args.extend(["--since", str(since)])
        plan_args = (*args, "--output", "json")

        def decode(stdout: bytes, command: str) -> object:
            items = decode_run_messages(stdout, command)
            return Page(items=items, total=len(items))

        return self._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),),
            finalize=lambda results: cast("Page[RunMessage]", results[0]),
            options=options,
        )

    def run_messages(
        self,
        task_run_id: str,
        *,
        issue_id: str | None = None,
        since: int = 0,
        options: OperationOptions | None = None,
    ) -> Page[RunMessage]:
        return self.run_messages_command(
            task_run_id, issue_id=issue_id, since=since, options=options
        ).run()

    def usage_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[IssueUsage]:
        return self._decoded_command(("issue", "usage", issue_id), IssueUsage, options=options)

    def usage(self, issue_id: str, *, options: OperationOptions | None = None) -> IssueUsage:
        return self.usage_command(issue_id, options=options).run()

    def rerun_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        validate_nonblank(issue_id)
        return self._action_command(("issue", "rerun", issue_id), options=options)

    def rerun(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.rerun_command(issue_id, options=options).run()

    def cancel_task_command(
        self,
        task_id: str,
        *,
        issue_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[None]]:
        validate_nonblank(task_id)
        args = ["issue", "cancel-task", task_id]
        if issue_id is not None:
            validate_nonblank(issue_id)
            args.extend(["--issue", issue_id])

        return self._action_command(tuple(args), options=options)

    def cancel_task(
        self, task_id: str, *, issue_id: str | None = None, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.cancel_task_command(task_id, issue_id=issue_id, options=options).run()

    def _bind_issue(self, wire: _IssueWire) -> Issue:
        return _issue_from_wire(wire)._with_client(self._client)

    def _bind_issue_children_result(self, result: IssueChildrenResult) -> IssueChildrenResult:
        return IssueChildrenResult(
            items=tuple(item._with_client(self._client) for item in result.items),
            total=result.total,
            child_stages=result.child_stages,
            unstaged=tuple(item._with_client(self._client) for item in result.unstaged),
            limit=result.limit,
            offset=result.offset,
            has_more=result.has_more,
            next_cursor=result.next_cursor,
        )

    def _bind_issue_list_page(self, page: IssueListPage) -> IssueListPage:
        items = tuple(item._with_client(self._client) for item in page.items)
        return IssueListPage(
            items=items,
            limit=page.limit,
            offset=page.offset,
            total=page.total,
            has_more=page.has_more,
            next_cursor=page.next_cursor,
        )

    def _bind_issue_search_page(self, page: Page[Issue]) -> Page[Issue]:
        items = tuple(item._with_client(self._client) for item in page.items)
        return Page(
            items=items,
            limit=page.limit,
            offset=page.offset,
            total=page.total,
            has_more=page.has_more,
            next_cursor=page.next_cursor,
        )
