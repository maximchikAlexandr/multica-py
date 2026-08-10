from __future__ import annotations

import datetime
import json
import pathlib
from collections.abc import Mapping
from dataclasses import replace
from typing import TYPE_CHECKING, cast, overload

import msgspec

from multica_py._generated.approved_sdk import (
    validate_nonblank,
)
from multica_py._internal.commands import Command, _replace_plan, _Step, _StepRef
from multica_py._internal.decoders import decode_json
from multica_py._internal.permalinks import build_permalink
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
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
from multica_py.config import ClientConfig, OperationOptions
from multica_py.enums import IssueSort, IssueStatus, SortDirection
from multica_py.exceptions import JsonOutputError, OutputShapeError
from multica_py.models._bound import _BoundEntity, _normalize_entity_id
from multica_py.models.common import ActionResult, Page
from multica_py.models.issue_activity import (
    CommentCursor,
    IssueUsage,
    MetadataEntry,
    RunMessage,
    Subscriber,
)
from multica_py.models.issues import (
    AssignmentTarget,
    FileDescription,
    InlineDescription,
    IssueAssignee,
    IssueChildrenResult,
    IssueChildStageGroup,
    IssueDescriptionInput,
    IssueListFilter,
    IssueListPage,
    IssueMetadataItem,
    IssueReference,
    LinkedPullRequest,
    NoDescription,
)
from multica_py.models.relations import (
    CursorLazyCollection,
    CursorPage,
    LazyCollection,
    LazyMapping,
    OffsetPage,
    RelationMetadata,
    _RelationLoad,
)
from multica_py.models.system import AttachmentResult
from multica_py.resources._base import BaseResource, _page_items
from multica_py.resources.issue_comments import (
    Comment,
    CommentThread,
    IssueCommentResource,
    _adapt_cursor_page_command,
    _bind_comment,
    _bind_thread,
)
from multica_py.resources.issue_labels import IssueLabelResource
from multica_py.resources.issue_metadata import IssueMetadataResource
from multica_py.resources.issue_subscribers import IssueSubscriberResource
from multica_py.resources.labels import Label
from multica_py.sentinels import Unset, UnsetType
from multica_py.types import MetadataValue

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


def _normalize_assignment_target(value: AssignmentTarget) -> str:
    # Local imports keep the resource dependency graph acyclic: those modules
    # themselves use Issue for their relation annotations.
    from multica_py.resources.agents import Agent
    from multica_py.resources.squads import Squad
    from multica_py.resources.workspaces import WorkspaceMember

    return _normalize_entity_id(
        value,
        field_name="assignee",
        allowed_types=(Agent, Squad, WorkspaceMember),
    )


def _normalize_issue_reference(value: IssueReference, *, field_name: str = "other_issue") -> str:
    return _normalize_entity_id(value, field_name=field_name, allowed_types=(Issue,))


def _normalize_issue_filter(
    filter: IssueListFilter | None,
    *,
    status: IssueStatus | None,
    priority: str | None,
    assignee_id: str | None,
    limit: int | None,
    offset: int | None,
    project_id: str | None,
    sort: IssueSort | None,
    direction: SortDirection | None,
    metadata: tuple[IssueMetadataItem, ...],
) -> IssueListFilter:
    direct_values = (
        status,
        priority,
        assignee_id,
        limit,
        offset,
        project_id,
        sort,
        direction,
        metadata,
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
    )


def _issue_labels_command(client: MulticaClient, issue_id: str) -> Command[tuple[Label, ...]]:
    def convert(page: Page[_LabelWire] | tuple[_LabelWire, ...]) -> tuple[Label, ...]:
        return tuple(
            Label(id=item.id, name=item.name, color=item.color, _client=client)
            for item in _page_items(page)
        )

    return client.issues.labels.list_command(issue_id)._map(convert)


def _issue_offset_page(issues: IssueResource, issue_filter: IssueListFilter) -> OffsetPage[Issue]:
    page = issues.list(issue_filter)
    return OffsetPage(
        items=page.items,
        total=page.total or 0,
        limit=page.limit or 50,
        offset=page.offset or 0,
        has_more=page.has_more,
    )


def _issue_offset_page_command(
    issues: IssueResource, issue_filter: IssueListFilter
) -> Command[OffsetPage[Issue]]:
    command = issues.list_command(issue_filter)
    plan = command._plan
    source_step = plan.steps[0]
    default_limit = 50 if issue_filter.limit is None else issue_filter.limit
    default_offset = 0 if issue_filter.offset is None else issue_filter.offset

    def decode_page(stdout: bytes, command_text: str) -> object:
        if source_step.decode is None:
            raise RuntimeError("issue list command has no decoder")
        decoded = source_step.decode(stdout, command_text)
        if isinstance(decoded, _IssueListPageWire):
            page = _issue_list_page_from_wire(decoded)
        elif isinstance(decoded, IssueListPage):
            page = decoded
        else:
            raise TypeError("issue list command decoder returned an unexpected page")
        if isinstance(issues, IssueResource):
            page = issues._bind_issue_list_page(page)
        return OffsetPage(
            items=page.items,
            total=page.total or 0,
            limit=page.limit or default_limit,
            offset=page.offset if page.offset is not None else default_offset,
            has_more=page.has_more,
        )

    return Command(
        _replace_plan(
            plan,
            steps=(replace(source_step, decode=decode_page),),
            finalize=lambda results: cast("OffsetPage[Issue]", results[0]),
        )
    )


def _decode_issue_search(stdout: bytes, command: str) -> Page[Issue]:
    try:
        envelope = decode_json(stdout, _IssueSearchResultWire, command=command)
    except OutputShapeError as envelope_error:
        try:
            rows = decode_json(stdout, list[_IssueWire], command=command)
        except (OutputShapeError, JsonOutputError):
            raise envelope_error
        items = tuple(_issue_from_wire(row) for row in rows)
        return Page(items=items, total=len(items))
    items = tuple(_issue_from_wire(row) for row in envelope.issues)
    return Page(items=items, total=envelope.total if envelope.total is not None else len(items))


class TaskRun(_BoundEntity):  # type: ignore[misc]
    id: str
    status: str
    agent_id: str | None = None
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    _issue_id: str | None = msgspec.field(default=None, name="_issue_id")
    _messages: LazyCollection[RunMessage] | None = msgspec.field(default=None, name="_messages")

    _PUBLIC_FIELDS = ("id", "status", "agent_id", "started_at", "completed_at")

    @property
    def messages(self) -> LazyCollection[RunMessage]:
        if self._messages is None:
            client = self._require_client(
                entity_type="TaskRun", entity_id=self.id, relation_name="messages"
            )
            task_run_id = self.id
            issue_id = self._issue_id
            issues = client.issues

            def loader() -> tuple[RunMessage, ...]:
                return _page_items(issues.run_messages(task_run_id, issue_id=issue_id))

            self._set_runtime(
                "_messages",
                LazyCollection[RunMessage](
                    loader,
                    command_loader=lambda: issues.run_messages_command(
                        task_run_id, issue_id=issue_id
                    )._map(_page_items),
                ),
            )
        return self._messages  # type: ignore[return-value]

    def messages_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[tuple[RunMessage, ...]]:
        client = self._require_client(
            entity_type="TaskRun", entity_id=self.id, relation_name="messages"
        )
        return client.issues.run_messages_command(
            self.id, issue_id=self._issue_id, options=options
        )._map(_page_items)


class Issue(_BoundEntity):  # type: ignore[misc]
    id: str
    title: str
    status: IssueStatus
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
    _pull_requests: LazyCollection[LinkedPullRequest] | None = msgspec.field(
        default=None, name="_pull_requests"
    )
    _children: LazyCollection[Issue] | None = msgspec.field(default=None, name="_children")
    _runs: LazyCollection[TaskRun] | None = msgspec.field(default=None, name="_runs")

    _PUBLIC_FIELDS = (
        "id",
        "title",
        "description",
        "status",
        "priority",
        "assignee",
        "child_stages",
        "label_names",
        "metadata_snapshot",
        "attachments",
        "pull_request_snapshot",
        "created_at",
        "updated_at",
        "parent_id",
        "project_id",
        "creator_id",
        "creator_type",
        "match_source",
    )

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
                def convert_page(page: Page[Comment]) -> tuple[Comment, ...]:
                    return tuple(page.items)

                return client.issues.comments.list_flat_command(issue_id=issue_id)._map(
                    convert_page
                )

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
                return _adapt_cursor_page_command(
                    client.issues.comments.list_recent_command(
                        issue_id=issue_id, limit=limit, cursor=next_cursor
                    ),
                    lambda page: CursorPage(
                        items=tuple(
                            _bind_thread(item, client, issue_id)
                            for item in cast("tuple[CommentThread, ...]", getattr(page, "items"))
                        ),
                        next_cursor=cast("CommentCursor | None", getattr(page, "next_cursor")),
                    ),
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
                return tuple(
                    Label(id=item.id, name=item.name, color=item.color, _client=client)
                    for item in _page_items(client.issues.labels.list(issue_id))
                )

            self._set_runtime(
                "_labels",
                LazyCollection[Label](
                    _load_labels,
                    command_loader=lambda: _issue_labels_command(client, issue_id),
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
                LazyCollection(
                    lambda: _page_items(subscribers.list(issue_id)),
                    command_loader=lambda: subscribers.list_command(issue_id)._map(_page_items),
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
                    command_loader=lambda: cast(
                        "Command[Mapping[str, MetadataValue]]",
                        metadata_resource.list_command(issue_id),
                    ),
                ),
            )
        return self._metadata  # type: ignore[return-value]

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
                LazyCollection(
                    lambda: _page_items(issues.pull_requests(issue_id)),
                    command_loader=lambda: issues.pull_requests_command(issue_id)._map(_page_items),
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
                def convert(result: IssueChildrenResult) -> _RelationLoad[Issue]:
                    return _RelationLoad(
                        tuple(item._with_client(client) for item in result.children),
                        RelationMetadata(
                            total=result.total,
                            child_stages=result.child_stages,
                            unstaged=tuple(item._with_client(client) for item in result.unstaged),
                        ),
                    )

                return client.issues.children_command(issue_id)._map(convert)

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
                return tuple(
                    TaskRun(
                        id=run.id,
                        status=run.status,
                        agent_id=run.agent_id,
                        started_at=run.started_at,
                        completed_at=run.completed_at,
                        _client=client,
                        _issue_id=issue_id,
                    )
                    for run in runs
                )

            def command_loader() -> Command[tuple[TaskRun, ...]]:
                return client.issues.runs_command(issue_id)._map(_page_items)

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
        self, status: IssueStatus, *, options: OperationOptions | None = None
    ) -> Command[Issue]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="set_status"
        )
        return client.issues.set_status_command(self.id, status, options=options)

    def set_status(self, status: IssueStatus, *, options: OperationOptions | None = None) -> Issue:
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

        def finalize(result: Comment) -> Comment:
            self._invalidate_comments()
            return result

        return client.issues.comments.add_command(self.id, body, options=options)._map(finalize)

    def add_comment(self, body: str, *, options: OperationOptions | None = None) -> Comment:
        return self.add_comment_command(body, options=options).run()

    def reply_command(
        self, thread_id: str, body: str, *, options: OperationOptions | None = None
    ) -> Command[Comment]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="comments"
        )

        def finalize(result: Comment) -> Comment:
            self._invalidate_comments()
            return result

        return client.issues.comments.reply_command(self.id, thread_id, body, options=options)._map(
            finalize
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

        def finalize(result: Page[_LabelWire] | tuple[_LabelWire, ...]) -> Page[Label]:
            self._invalidate_labels()
            items = _page_items(result)
            return Page(
                items=tuple(
                    Label(id=item.id, name=item.name, color=item.color, _client=client)
                    for item in items
                ),
                limit=result.limit if isinstance(result, Page) else None,
                offset=result.offset if isinstance(result, Page) else None,
                total=result.total if isinstance(result, Page) else len(items),
                has_more=result.has_more if isinstance(result, Page) else False,
                next_cursor=result.next_cursor if isinstance(result, Page) else None,
            )

        return client.issues.labels.add_command(self.id, label_id, options=options)._map(finalize)

    def add_label(self, label_id: str, *, options: OperationOptions | None = None) -> Page[Label]:
        return self.add_label_command(label_id, options=options).run()

    def remove_label_command(
        self, label_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[Label]]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="labels"
        )

        def finalize(result: Page[_LabelWire] | tuple[_LabelWire, ...]) -> Page[Label]:
            self._invalidate_labels()
            items = _page_items(result)
            return Page(
                items=tuple(
                    Label(id=item.id, name=item.name, color=item.color, _client=client)
                    for item in items
                ),
                limit=result.limit if isinstance(result, Page) else None,
                offset=result.offset if isinstance(result, Page) else None,
                total=result.total if isinstance(result, Page) else len(items),
                has_more=result.has_more if isinstance(result, Page) else False,
                next_cursor=result.next_cursor if isinstance(result, Page) else None,
            )

        return client.issues.labels.remove_command(self.id, label_id, options=options)._map(
            finalize
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

        def invalidate(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                self._invalidate_subscribers()
            return result

        return client.issues.subscribers.add_command(self.id, user_id, options=options)._map(
            invalidate
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

        def invalidate(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                self._invalidate_subscribers()
            return result

        return client.issues.subscribers.remove_command(self.id, user_id, options=options)._map(
            invalidate
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

        def finalize(result: MetadataEntry) -> MetadataEntry:
            self._invalidate_metadata()
            return result

        return client.issues.metadata.set_command(self.id, key, value, options=options)._map(
            finalize
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

        def invalidate(result: ActionResult[None]) -> ActionResult[None]:
            if result.success:
                self._invalidate_metadata()
            return result

        return client.issues.metadata.delete_command(self.id, key, options=options)._map(invalidate)

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


class IssueResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)
        self.comments = IssueCommentResource(transport, config)
        self.metadata = IssueMetadataResource(transport, config)
        self.subscribers = IssueSubscriberResource(transport, config)
        self.labels = IssueLabelResource(transport, config)

    def _set_client(self, client: MulticaClient) -> None:
        super()._set_client(client)
        self.comments._set_client(client)
        self.metadata._set_client(client)
        self.subscribers._set_client(client)
        self.labels._set_client(client)

    @overload
    def list_command(
        self, filter: IssueListFilter, /, *, options: OperationOptions | None = None
    ) -> Command[IssueListPage]: ...

    @overload
    def list_command(
        self,
        *,
        status: IssueStatus | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        project_id: str | None = None,
        sort: IssueSort | None = None,
        direction: SortDirection | None = None,
        metadata: tuple[IssueMetadataItem, ...] = (),
        options: OperationOptions | None = None,
    ) -> Command[IssueListPage]: ...

    def list_command(  # type: ignore[misc]
        self,
        filter: IssueListFilter | None = None,
        /,
        *,
        status: IssueStatus | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        project_id: str | None = None,
        sort: IssueSort | None = None,
        direction: SortDirection | None = None,
        metadata: tuple[IssueMetadataItem, ...] = (),
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
        )
        args = ["issue", "list"]
        status = filter.status
        priority = filter.priority
        assignee_id = filter.assignee_id
        limit = filter.limit
        offset = filter.offset
        project_id = filter.project_id
        metadata = filter.metadata
        sort = filter.sort
        direction = filter.direction
        if offset is not None and offset < 0:
            raise ValueError("IssueResource.list: offset must be nonnegative (offset_nonnegative)")
        if direction is not None and sort is None:
            raise ValueError(
                "IssueResource.list: direction requires sort (direction_requires_sort)"
            )
        if status is not None:
            args.extend(["--status", status.value])
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
        if sort is not None:
            args.extend(["--sort", sort])
        if direction is not None:
            args.extend(["--direction", direction])
        return (
            self._decoded_command(tuple(args), _IssueListPageWire, options=options)
            ._map(_issue_list_page_from_wire)
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
        status: IssueStatus | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        project_id: str | None = None,
        sort: IssueSort | None = None,
        direction: SortDirection | None = None,
        metadata: tuple[IssueMetadataItem, ...] = (),
        options: OperationOptions | None = None,
    ) -> IssueListPage: ...

    def list(  # type: ignore[misc]
        self,
        filter: IssueListFilter | None = None,
        /,
        *,
        status: IssueStatus | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        project_id: str | None = None,
        sort: IssueSort | None = None,
        direction: SortDirection | None = None,
        metadata: tuple[IssueMetadataItem, ...] = (),
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
        )
        return self.list_command(normalized, options=options).run()

    def get_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[Issue]:
        validate_nonblank(issue_id)
        return self._decoded_command(("issue", "get", issue_id), _IssueWire, options=options)._map(
            self._bind_issue
        )

    def get(self, issue_id: str, *, options: OperationOptions | None = None) -> Issue:
        return self.get_command(issue_id, options=options).run()

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
        return self._decoded_command(
            ("issue", "children", issue_id), _IssueChildrenResultWire, options=options
        )._map(_issue_children_result_from_wire)

    def children(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> IssueChildrenResult:
        return self.children_command(issue_id, options=options).run()

    def create_command(
        self,
        *,
        title: str,
        description_input: IssueDescriptionInput = NoDescription(),
        priority: str | None = None,
        assignee_id: str | None = None,
        label_ids: tuple[str, ...] = (),
        project_id: str | None = None,
        parent_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Issue]:
        """Create an issue and optionally attach labels.

        Creates the issue first, then attaches each ``label_ids`` entry via
        separate ``issue label add`` calls. A failure mid-loop can leave a
        partially labeled issue.
        """
        validate_nonblank(title)
        if (
            not isinstance(description_input, InlineDescription)
            and not isinstance(description_input, FileDescription)
            and description_input.__class__.__name__ not in {"StdinDescription", "NoDescription"}
        ):
            raise TypeError("description_input must be a supported issue description")
        if project_id is not None and not project_id.strip():
            raise ValueError("project_id must be non-empty when set")
        if parent_id is not None and not parent_id.strip():
            raise ValueError("parent_id must be non-empty when set")
        args = ["issue", "create", "--title", title]
        desc = description_input
        if isinstance(desc, InlineDescription):
            args.extend(["--description", desc.text])
        elif isinstance(desc, FileDescription):
            args.extend(["--description-file", str(pathlib.Path(desc.path).resolve())])
        elif desc.__class__.__name__ == "StdinDescription":
            args.append("--description-stdin")
        if priority is not None:
            args.extend(["--priority", priority])
        if assignee_id is not None:
            args.extend(["--assignee-id", assignee_id])
        if project_id is not None:
            args.extend(["--project", project_id])
        if parent_id is not None:
            args.extend(["--parent", parent_id])
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

        return self._plan(steps=tuple(steps), finalize=finalize, options=options)

    def create(
        self,
        *,
        title: str,
        description_input: IssueDescriptionInput = NoDescription(),
        priority: str | None = None,
        assignee_id: str | None = None,
        label_ids: tuple[str, ...] = (),
        project_id: str | None = None,
        parent_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.create_command(
            title=title,
            description_input=description_input,
            priority=priority,
            assignee_id=assignee_id,
            label_ids=label_ids,
            project_id=project_id,
            parent_id=parent_id,
            options=options,
        ).run()

    def update_command(
        self,
        issue_id: str,
        *,
        title: str | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        priority: str | UnsetType = Unset,
        assignee_id: str | None | UnsetType = Unset,
        project_id: str | None | UnsetType = Unset,
        parent_id: str | None | UnsetType = Unset,
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
        if assignee_id is not Unset and assignee_id is not None:
            args.extend(["--assignee-id", assignee_id])
        if project_id is not Unset:
            args.extend(["--project", "" if project_id is None else project_id])
        if parent_id is not Unset:
            args.extend(["--parent", "" if parent_id is None else parent_id])

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
        assignee_id: str | None | UnsetType = Unset,
        project_id: str | None | UnsetType = Unset,
        parent_id: str | None | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.update_command(
            issue_id,
            title=title,
            description=description,
            priority=priority,
            assignee_id=assignee_id,
            project_id=project_id,
            parent_id=parent_id,
            options=options,
        ).run()

    def assign_command(
        self,
        issue_id: str,
        assignee: AssignmentTarget,
        *,
        options: OperationOptions | None = None,
    ) -> Command[Issue]:
        validate_nonblank(issue_id)
        target = _normalize_assignment_target(assignee)
        args = ["issue", "assign", issue_id]
        args.extend(["--to-id", target])
        return self._decoded_command(tuple(args), _IssueWire, options=options)._map(
            self._bind_issue
        )

    def assign(
        self,
        issue_id: str,
        assignee: AssignmentTarget,
        *,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.assign_command(issue_id, assignee, options=options).run()

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
        self, issue_id: str, status: IssueStatus, *, options: OperationOptions | None = None
    ) -> Command[Issue]:
        validate_nonblank(issue_id)
        return self._decoded_command(
            ("issue", "status", issue_id, status.value), _IssueWire, options=options
        )._map(self._bind_issue)

    def set_status(
        self, issue_id: str, status: IssueStatus, *, options: OperationOptions | None = None
    ) -> Issue:
        return self.set_status_command(issue_id, status, options=options).run()

    def deprioritize_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[str]]:
        return self._action_text_command(("issue", "deprioritize", issue_id), options=options)

    def deprioritize(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[str]:
        return self.deprioritize_command(issue_id, options=options).run()

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
        self, query: str, *, options: OperationOptions | None = None
    ) -> Command[Page[Issue]]:
        validate_nonblank(query)
        args = ("issue", "search", query, "--output", "json")
        return self._plan(
            steps=(_Step(args, "run_bytes", decode=_decode_issue_search),),
            finalize=lambda results: cast("Page[Issue]", results[0]),
            options=options,
        )._map(self._bind_issue_search_page)

    def search(self, query: str, *, options: OperationOptions | None = None) -> Page[Issue]:
        return self.search_command(query, options=options).run()

    def runs_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[Page[TaskRun]]:
        def finalize(page: Page[TaskRun]) -> Page[TaskRun]:
            return Page(
                items=tuple(
                    TaskRun(
                        id=run.id,
                        status=run.status,
                        agent_id=run.agent_id,
                        started_at=run.started_at,
                        completed_at=run.completed_at,
                        _client=self._client,
                        _issue_id=issue_id,
                    )
                    for run in page.items
                ),
                limit=page.limit,
                offset=page.offset,
                total=page.total,
                has_more=page.has_more,
                next_cursor=page.next_cursor,
            )

        return self._decoded_page_command(
            ("issue", "runs", issue_id), TaskRun, options=options
        )._map(finalize)

    def runs(self, issue_id: str, *, options: OperationOptions | None = None) -> Page[TaskRun]:
        return self.runs_command(issue_id, options=options).run()

    def run_messages_command(
        self,
        task_run_id: str,
        *,
        issue_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Command[Page[RunMessage]]:
        validate_nonblank(task_run_id)
        args = ["issue", "run-messages", task_run_id]
        if issue_id is not None:
            validate_nonblank(issue_id)
            args.extend(["--issue", issue_id])
        return self._decoded_page_command(tuple(args), RunMessage, options=options)

    def run_messages(
        self,
        task_run_id: str,
        *,
        issue_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Page[RunMessage]:
        return self.run_messages_command(task_run_id, issue_id=issue_id, options=options).run()

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
