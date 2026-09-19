from __future__ import annotations

import datetime
from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, cast

import msgspec

from multica_py._internal.json_values import _coerce_json_value
from multica_py.enums import _coerce_issue_status
from multica_py.exceptions import OutputShapeError
from multica_py.models.common import CommentCursor
from multica_py.models.issues import (
    IssueAssignee,
    IssueChildrenResult,
    IssueChildStageGroup,
    IssueListPage,
    IssueMetadataItem,
    LinkedPullRequest,
)
from multica_py.models.system import AttachmentResult
from multica_py.types import JsonValue, MetadataValue

if TYPE_CHECKING:
    from multica_py.entities.issues import Issue


class _LabelWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    color: str | None = None
    description: str | None = None
    resource_type: str | None = None


class _IssueWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    title: str | msgspec.UnsetType = msgspec.UNSET
    description: str | None | msgspec.UnsetType = msgspec.UNSET
    status: str | msgspec.UnsetType = msgspec.UNSET
    status_name: str | msgspec.UnsetType = msgspec.UNSET
    revision: int | msgspec.UnsetType = msgspec.UNSET
    last_activity_at: datetime.datetime | None | msgspec.UnsetType = msgspec.UNSET
    source_context: object | None | msgspec.UnsetType = msgspec.UNSET
    priority: str | None | msgspec.UnsetType = msgspec.UNSET
    assignee: IssueAssignee | None | msgspec.UnsetType = msgspec.UNSET
    assignee_id: str | None | msgspec.UnsetType = msgspec.UNSET
    assignee_type: str | None | msgspec.UnsetType = msgspec.UNSET
    pull_requests: tuple[LinkedPullRequest, ...] | msgspec.UnsetType = msgspec.UNSET
    children: tuple[IssueChildStageGroup, ...] | msgspec.UnsetType = msgspec.UNSET
    labels: tuple[_LabelWire, ...] | None | msgspec.UnsetType = msgspec.UNSET
    metadata: dict[str, MetadataValue] | None | msgspec.UnsetType = msgspec.UNSET
    attachments: tuple[AttachmentResult, ...] | msgspec.UnsetType = msgspec.UNSET
    created_at: datetime.datetime | None | msgspec.UnsetType = msgspec.UNSET
    updated_at: datetime.datetime | None | msgspec.UnsetType = msgspec.UNSET
    parent_issue_id: str | None | msgspec.UnsetType = msgspec.UNSET
    project_id: str | None | msgspec.UnsetType = msgspec.UNSET
    creator_id: str | None | msgspec.UnsetType = msgspec.UNSET
    creator_type: str | None | msgspec.UnsetType = (
        msgspec.UNSET  # ponytail: free string, no enum — upstream values not stabilised; add CreatorType enum when they are
    )
    match_source: str | None = None
    properties: object | msgspec.UnsetType = msgspec.UNSET
    # List projections contain fields that are not part of the stable Issue
    # value. Keep them on the private wire and expose them only on partial
    # Issue rows; never decode a projection into a second public row type.
    workspace_id: object | msgspec.UnsetType = msgspec.UNSET
    number: object | msgspec.UnsetType = msgspec.UNSET
    identifier: object | msgspec.UnsetType = msgspec.UNSET
    status_category: str | msgspec.UnsetType = msgspec.UNSET
    position: object | msgspec.UnsetType = msgspec.UNSET
    stage: object | msgspec.UnsetType = msgspec.UNSET
    start_date: object | msgspec.UnsetType = msgspec.UNSET
    due_date: object | msgspec.UnsetType = msgspec.UNSET


class _IssueListPageWire(msgspec.Struct, frozen=True, kw_only=True):
    issues: tuple[_IssueWire, ...]
    has_more: bool = False
    limit: int | None = None
    offset: int | None = None
    total: int | None = None
    next_cursor: str | CommentCursor | None = None


class _IssueSearchResultWire(msgspec.Struct, frozen=True, kw_only=True):
    issues: tuple[_IssueWire, ...]
    total: int | None = None
    has_more: bool = False
    limit: int | None = None
    offset: int | None = None
    next_cursor: str | CommentCursor | None = None


def _issue_list_page_from_wire(
    wire: _IssueListPageWire, *, fields: tuple[str, ...] | None = None
) -> IssueListPage:
    if wire.total is not None and wire.total < 0:
        raise OutputShapeError("issue list page total must be nonnegative")
    if wire.has_more and not wire.issues:
        raise OutputShapeError("issue list page cannot continue after an empty page")
    items = tuple(_issue_row_from_wire(item, projection_fields=fields) for item in wire.issues)
    total = None if wire.total == 0 and items else wire.total
    return IssueListPage(
        items=items,
        has_more=wire.has_more,
        limit=wire.limit,
        offset=wire.offset,
        total=total,
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


_ISSUE_PROJECTION_FIELDS: tuple[tuple[str, str], ...] = (
    ("id", "id"),
    ("workspace_id", "workspace_id"),
    ("number", "number"),
    ("identifier", "identifier"),
    ("title", "title"),
    ("description", "description"),
    ("status", "status"),
    ("status_category", "status_category"),
    ("status_name", "status_name"),
    ("priority", "priority"),
    ("assignee_type", "assignee_type"),
    ("assignee_id", "assignee_id"),
    ("creator_type", "creator_type"),
    ("creator_id", "creator_id"),
    ("parent_issue_id", "parent_id"),
    ("project_id", "project_id"),
    ("position", "position"),
    ("stage", "stage"),
    ("start_date", "start_date"),
    ("due_date", "due_date"),
    ("created_at", "created_at"),
    ("updated_at", "updated_at"),
    ("revision", "revision"),
    ("last_activity_at", "last_activity_at"),
    ("metadata", "metadata"),
    ("properties", "properties"),
    ("labels", "labels"),
)


def _projection_value(value: object, *, field_name: str) -> object:
    if field_name == "labels" and isinstance(value, tuple):
        value = tuple(
            {"id": row.id, "name": row.name, "color": row.color}
            for row in value
            if isinstance(row, _LabelWire)
        )
    if isinstance(value, (Mapping, list, tuple)):
        return _coerce_json_value(value, field_name=f"issue.{field_name}")
    return value


_CUSTOM_STATUS_CATEGORY_PROJECTION = {
    "unstarted": "todo",
    "started": "in_progress",
    "done": "done",
    "closed": "closed",
}


def _issue_status_category_from_wire(wire: _IssueWire) -> str | msgspec.UnsetType:
    category = wire.status_category
    if category is msgspec.UNSET or wire.status is msgspec.UNSET:
        return category
    if type(_coerce_issue_status(wire.status)) is str:
        return _CUSTOM_STATUS_CATEGORY_PROJECTION.get(category, category)
    return category


def _issue_projection_from_wire(
    wire: _IssueWire, *, fields: tuple[str, ...] | None = None
) -> Mapping[str, object]:
    values: dict[str, object] = {}
    selected = set(fields) if fields is not None else None
    for wire_name, public_name in _ISSUE_PROJECTION_FIELDS:
        if selected is not None and wire_name not in selected and public_name not in selected:
            continue
        value = (
            _issue_status_category_from_wire(wire)
            if wire_name == "status_category"
            else cast("object", getattr(wire, wire_name))
        )
        if value is not msgspec.UNSET:
            values[public_name] = _projection_value(value, field_name=wire_name)
    return MappingProxyType(values)


def _issue_from_wire(
    wire: _IssueWire,
    *,
    include_wire_presence: bool = True,
    allow_partial: bool = False,
    projection_fields: tuple[str, ...] | None = None,
    force_projection: bool = False,
) -> Issue:
    from multica_py.entities._base import _runtime_state
    from multica_py.entities.issues import Issue
    from multica_py.entities.labels import Label
    from multica_py.models.relations import LazyCollection, LazyMapping

    assignee, assignee_presence = _issue_assignee_from_wire(wire, allow_partial=allow_partial)
    pull_requests = () if wire.pull_requests is msgspec.UNSET else wire.pull_requests
    children = () if wire.children is msgspec.UNSET else wire.children
    labels = () if wire.labels is msgspec.UNSET or wire.labels is None else wire.labels
    metadata = {} if wire.metadata is msgspec.UNSET or wire.metadata is None else wire.metadata
    attachments = _attachments_from_wire(wire)
    partial = (
        force_projection
        or projection_fields is not None
        or (
            allow_partial
            and (wire.status_category is not msgspec.UNSET or wire.status_name is not msgspec.UNSET)
        )
        or wire.title is msgspec.UNSET
        or wire.status is msgspec.UNSET
    )
    if partial and not allow_partial:
        raise OutputShapeError("full issue projection requires title and status")
    issue = Issue(
        id=wire.id,
        title=cast("str", wire.title),
        description=None if wire.description is msgspec.UNSET else wire.description,
        status=(
            cast("str", msgspec.UNSET)
            if wire.status is msgspec.UNSET
            else _coerce_issue_status(wire.status)
        ),
        status_name=None if wire.status_name is msgspec.UNSET else wire.status_name,
        revision=None if wire.revision is msgspec.UNSET else wire.revision,
        last_activity_at=(
            None if wire.last_activity_at is msgspec.UNSET else wire.last_activity_at
        ),
        source_context=(
            None
            if wire.source_context is msgspec.UNSET or wire.source_context is None
            else _coerce_json_value(wire.source_context, field_name="source_context")
        ),
        priority=None if wire.priority is msgspec.UNSET else wire.priority,
        assignee=assignee,
        pull_request_snapshot=pull_requests,
        child_stages=children,
        label_names=tuple(label.name for label in labels),
        metadata_snapshot=tuple(
            IssueMetadataItem(key=key, value=value) for key, value in metadata.items()
        ),
        attachments=attachments,
        created_at=None if wire.created_at is msgspec.UNSET else wire.created_at,
        updated_at=None if wire.updated_at is msgspec.UNSET else wire.updated_at,
        parent_id=None if wire.parent_issue_id is msgspec.UNSET else wire.parent_issue_id,
        project_id=None if wire.project_id is msgspec.UNSET else wire.project_id,
        creator_id=None if wire.creator_id is msgspec.UNSET else wire.creator_id,
        creator_type=None if wire.creator_type is msgspec.UNSET else wire.creator_type,
        match_source=wire.match_source,
        _property_projection=_issue_property_projection(wire.properties),
        _projection=(
            _issue_projection_from_wire(wire, fields=projection_fields) if partial else {}
        ),
        _wire_presence=(
            (
                ("status_name", _presence_seed(wire.status_name)),
                ("revision", _presence_seed(wire.revision)),
                ("last_activity_at", _presence_seed(wire.last_activity_at)),
                ("source_context", _presence_seed(wire.source_context)),
                ("parent_id", _presence_seed(wire.parent_issue_id)),
                ("project_id", _presence_seed(wire.project_id)),
                ("assignee", assignee_presence),
            )
            if include_wire_presence
            else ()
        ),
    )
    if partial:
        runtime = _runtime_state(issue)
        if isinstance(wire.labels, tuple):
            label_values = tuple(
                Label(
                    id=row.id,
                    name=row.name,
                    color=row.color,
                    description=row.description,
                    resource_type=row.resource_type,
                )
                for row in labels
            )
            runtime["_labels"] = LazyCollection(lambda: label_values, initial=label_values)
        if wire.metadata is not msgspec.UNSET and isinstance(wire.metadata, Mapping):
            runtime["_metadata"] = LazyMapping(
                lambda: cast("Mapping[str, MetadataValue]", wire.metadata),
                initial=cast("Mapping[str, MetadataValue]", wire.metadata),
            )
    return issue


def _issue_property_projection(value: object) -> JsonValue | None:
    if value is msgspec.UNSET:
        return None
    return _coerce_json_value(value, field_name="issue.properties")


def _issue_row_from_wire(
    wire: _IssueWire, *, projection_fields: tuple[str, ...] | None = None
) -> Issue:
    return _issue_from_wire(wire, allow_partial=True, projection_fields=projection_fields)


def _issue_assignee_from_wire(
    wire: _IssueWire, *, allow_partial: bool = False
) -> tuple[IssueAssignee | None, _PresenceSeed]:
    scalar_id_present = wire.assignee_id is not msgspec.UNSET
    scalar_type_present = wire.assignee_type is not msgspec.UNSET
    if scalar_id_present != scalar_type_present:
        if allow_partial and wire.assignee is msgspec.UNSET:
            return None, "missing"
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
