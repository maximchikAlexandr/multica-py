from __future__ import annotations

import datetime
import json
import pathlib
from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import TYPE_CHECKING, TypeVar, cast, overload

import msgspec

from multica_py._generated.approved_sdk import (
    validate_nonblank,
)
from multica_py._internal.commands import Command, _replace_plan, _Step, _StepRef
from multica_py._internal.specs import TextResult
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    _issue_children_result_from_wire,
    _issue_from_wire,
    _issue_list_page_from_wire,
    _issue_pull_requests_from_wire,
    _IssueChildrenResultWire,
    _IssueListPageWire,
    _IssuePullRequestsResultWire,
    _IssueWire,
    _LabelWire,
)
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus
from multica_py.models._bound import _BoundEntity
from multica_py.models.common import Page
from multica_py.models.issue_activity import (
    CommentCursor,
    CommentListFlatRequest,
    CommentListRecentRequest,
    IssueUsage,
    MetadataEntry,
    RunMessage,
    Subscriber,
)
from multica_py.models.issues import (
    FileDescription,
    InlineDescription,
    IssueAssignee,
    IssueAssignmentRequest,
    IssueChildrenResult,
    IssueChildStageGroup,
    IssueCreateRequest,
    IssueDescriptionInput,
    IssueListFilter,
    IssueListPage,
    IssueMetadataItem,
    IssueReorderRequest,
    IssueSummary,
    IssueUpdateRequest,
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
from multica_py.resources._base import BaseResource, _resolve_request
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
from multica_py.types import MetadataValue

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


P = TypeVar("P")
Q = TypeVar("Q")


def _field_value(obj: object, name: str) -> object:
    return cast("object", getattr(obj, name))


def _map_command(command: Command[P], mapper: Callable[[P], Q]) -> Command[Q]:
    plan = command._plan
    override = plan._run_override

    def run_override() -> Q:
        if override is None:
            raise RuntimeError("command has no run override")
        return mapper(override())

    return Command(
        _replace_plan(
            plan,
            finalize=lambda results: mapper(plan.finalize(results)),
            run_override=run_override if override is not None else None,
        )
    )


def _issue_labels_command(client: MulticaClient, issue_id: str) -> Command[tuple[Label, ...]]:
    def convert(items: tuple[_LabelWire, ...]) -> tuple[Label, ...]:
        return tuple(
            Label(id=item.id, name=item.name, color=item.color, _client=client) for item in items
        )

    return _map_command(client.issues.labels.list_command(issue_id), convert)


def _issue_summary_offset_page(
    issues: IssueResource, issue_filter: IssueListFilter
) -> OffsetPage[IssueSummary]:
    page = issues.list(issue_filter)
    return OffsetPage(
        items=page.issues,
        total=page.total or 0,
        limit=page.limit or 50,
        offset=page.offset or 0,
        has_more=page.has_more,
    )


def _issue_summary_offset_page_command(
    issues: IssueResource, issue_filter: IssueListFilter
) -> Command[OffsetPage[IssueSummary]]:
    command = issues.list_command(issue_filter)
    plan = command._plan
    source_step = plan.steps[0]
    default_limit = 50 if issue_filter.limit is None else issue_filter.limit
    default_offset = 0 if issue_filter.offset is None else issue_filter.offset

    def decode_page(stdout: bytes, command_text: str) -> object:
        if source_step.decode is None:
            raise RuntimeError("issue list command has no decoder")
        page = cast("IssueListPage", source_step.decode(stdout, command_text))
        return OffsetPage(
            items=page.issues,
            total=page.total or 0,
            limit=page.limit or default_limit,
            offset=page.offset if page.offset is not None else default_offset,
            has_more=page.has_more,
        )

    return Command(
        _replace_plan(
            plan,
            steps=(replace(source_step, decode=decode_page),),
            finalize=lambda results: cast("OffsetPage[IssueSummary]", results[0]),
        )
    )


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
                return issues.run_messages(task_run_id, issue_id=issue_id)

            self._set_runtime(
                "_messages",
                LazyCollection[RunMessage](
                    loader,
                    command_loader=lambda: issues.run_messages_command(
                        task_run_id, issue_id=issue_id
                    ),
                ),
            )
        return self._messages  # type: ignore[return-value]

    def messages_command(self) -> Command[tuple[RunMessage, ...]]:
        client = self._require_client(
            entity_type="TaskRun", entity_id=self.id, relation_name="messages"
        )
        return client.issues.run_messages_command(self.id, issue_id=self._issue_id)


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
    )

    @property
    def comments(self) -> LazyCollection[Comment]:
        if self._comments is None:
            client = self._require_client(
                entity_type="Issue", entity_id=self.id, relation_name="comments"
            )
            issue_id = self.id

            def loader() -> tuple[Comment, ...]:
                page = client.issues.comments.list_flat(CommentListFlatRequest(issue_id=issue_id))
                return tuple(_bind_comment(item, client) for item in page.items)

            def command_loader() -> Command[tuple[Comment, ...]]:
                request = CommentListFlatRequest(issue_id=issue_id)

                def convert_page(page: Page[Comment]) -> tuple[Comment, ...]:
                    return tuple(page.items)

                return _map_command(client.issues.comments.list_flat_command(request), convert_page)

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
                request = CommentListRecentRequest(
                    issue_id=issue_id,
                    limit=limit,
                    cursor=cursor,
                )
                page = client.issues.comments.list_recent(request)
                return CursorPage(
                    items=tuple(_bind_thread(item, client, issue_id) for item in page.items),
                    next_cursor=cast("CommentCursor | None", page.next_cursor),
                )

            def page_command_loader(
                next_cursor: CommentCursor | None,
            ) -> Command[CursorPage[CommentThread]]:
                request = CommentListRecentRequest(
                    issue_id=issue_id,
                    limit=limit,
                    cursor=next_cursor,
                )
                return _adapt_cursor_page_command(
                    client.issues.comments.list_recent_command(request),
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
                    for item in client.issues.labels.list(issue_id)
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
                    lambda: subscribers.list(issue_id),
                    command_loader=lambda: subscribers.list_command(issue_id),
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
                    lambda: issues.pull_requests(issue_id),
                    command_loader=lambda: issues.pull_requests_command(issue_id),
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

                return _map_command(client.issues.children_command(issue_id), convert)

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
                runs = client.issues.runs(issue_id)
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
                return client.issues.runs_command(issue_id)

            self._set_runtime(
                "_runs",
                LazyCollection[TaskRun](
                    loader,
                    command_loader=command_loader,
                ),
            )
        return self._runs  # type: ignore[return-value]

    def add_comment_command(self, body: str) -> Command[Comment]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="comments"
        )

        def finalize(result: Comment) -> Comment:
            self._invalidate_comments()
            return result

        return _map_command(client.issues.comments.add_command(self.id, body), finalize)

    def add_comment(self, body: str) -> Comment:
        return self.add_comment_command(body).run()

    def reply_command(self, thread_id: str, body: str) -> Command[Comment]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="comments"
        )

        def finalize(result: Comment) -> Comment:
            self._invalidate_comments()
            return result

        return _map_command(
            client.issues.comments.reply_command(self.id, thread_id, body), finalize
        )

    def reply(self, thread_id: str, body: str) -> Comment:
        return self.reply_command(thread_id, body).run()

    def add_label_command(self, label_id: str) -> Command[tuple[Label, ...]]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="labels"
        )

        def finalize(result: tuple[_LabelWire, ...]) -> tuple[Label, ...]:
            self._invalidate_labels()
            return tuple(
                Label(id=item.id, name=item.name, color=item.color, _client=client)
                for item in result
            )

        return _map_command(client.issues.labels.add_command(self.id, label_id), finalize)

    def add_label(self, label_id: str) -> tuple[Label, ...]:
        return self.add_label_command(label_id).run()

    def remove_label_command(self, label_id: str) -> Command[tuple[Label, ...]]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="labels"
        )

        def finalize(result: tuple[_LabelWire, ...]) -> tuple[Label, ...]:
            self._invalidate_labels()
            return tuple(
                Label(id=item.id, name=item.name, color=item.color, _client=client)
                for item in result
            )

        return _map_command(client.issues.labels.remove_command(self.id, label_id), finalize)

    def remove_label(self, label_id: str) -> tuple[Label, ...]:
        return self.remove_label_command(label_id).run()

    def add_subscriber_command(self, user_id: str) -> Command[None]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="subscribers"
        )
        return _map_command(
            client.issues.subscribers.add_command(self.id, user_id),
            lambda result: self._invalidate_subscribers(),
        )

    def add_subscriber(self, user_id: str) -> None:
        self.add_subscriber_command(user_id).run()

    def remove_subscriber_command(self, user_id: str) -> Command[None]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="subscribers"
        )
        return _map_command(
            client.issues.subscribers.remove_command(self.id, user_id),
            lambda result: self._invalidate_subscribers(),
        )

    def remove_subscriber(self, user_id: str) -> None:
        self.remove_subscriber_command(user_id).run()

    def set_metadata_command(self, key: str, value: MetadataValue) -> Command[MetadataEntry]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="metadata"
        )

        def finalize(result: MetadataEntry) -> MetadataEntry:
            self._invalidate_metadata()
            return result

        return _map_command(client.issues.metadata.set_command(self.id, key, value), finalize)

    def set_metadata(self, key: str, value: MetadataValue) -> MetadataEntry:
        return self.set_metadata_command(key, value).run()

    def delete_metadata_command(self, key: str) -> Command[None]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="metadata"
        )
        return _map_command(
            client.issues.metadata.delete_command(self.id, key),
            lambda result: self._invalidate_metadata(),
        )

    def delete_metadata(self, key: str) -> None:
        self.delete_metadata_command(key).run()

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

    def list_command(self, filter: IssueListFilter | None = None) -> Command[IssueListPage]:
        args = ["issue", "list"]
        if filter is not None:
            status = cast("IssueStatus | None", _field_value(filter, "status"))
            priority = cast("str | None", _field_value(filter, "priority"))
            assignee_id = cast("str | None", _field_value(filter, "assignee_id"))
            limit = cast("int | None", _field_value(filter, "limit"))
            offset = cast("int | None", _field_value(filter, "offset"))
            project_id = cast("str | None", _field_value(filter, "project_id"))
            metadata = cast("tuple[IssueMetadataItem, ...]", _field_value(filter, "metadata"))
            sort = cast("str | None", _field_value(filter, "sort"))
            direction = cast("str | None", _field_value(filter, "direction"))
            if offset is not None and offset < 0:
                raise ValueError(
                    "IssueResource.list: offset must be nonnegative (offset_nonnegative)"
                )
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
        plan_args, decode = self._plan_decode(tuple(args), _IssueListPageWire)

        def finalize(results: tuple[object, ...]) -> IssueListPage:
            return _issue_list_page_from_wire(cast("_IssueListPageWire", results[0]))

        return self._plan(steps=(_Step(plan_args, "run_bytes", decode=decode),), finalize=finalize)

    def list(self, filter: IssueListFilter | None = None) -> IssueListPage:
        return self.list_command(filter).run()

    def get_command(self, issue_id: str) -> Command[Issue]:
        validate_nonblank(issue_id)
        args, decode = self._plan_decode(("issue", "get", issue_id), _IssueWire)

        def finalize(results: tuple[object, ...]) -> Issue:
            return _issue_from_wire(cast("_IssueWire", results[0]))._with_client(self._client)

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def get(self, issue_id: str) -> Issue:
        return self.get_command(issue_id).run()

    def pull_requests_command(self, issue_id: str) -> Command[tuple[LinkedPullRequest, ...]]:
        args, decode = self._plan_decode(
            ("issue", "pull-requests", issue_id), _IssuePullRequestsResultWire
        )

        def finalize(results: tuple[object, ...]) -> tuple[LinkedPullRequest, ...]:
            return _issue_pull_requests_from_wire(cast("_IssuePullRequestsResultWire", results[0]))

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def pull_requests(self, issue_id: str) -> tuple[LinkedPullRequest, ...]:
        return self.pull_requests_command(issue_id).run()

    def children_command(self, issue_id: str) -> Command[IssueChildrenResult]:
        args, decode = self._plan_decode(("issue", "children", issue_id), _IssueChildrenResultWire)

        def finalize(results: tuple[object, ...]) -> IssueChildrenResult:
            return _issue_children_result_from_wire(cast("_IssueChildrenResultWire", results[0]))

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def children(self, issue_id: str) -> IssueChildrenResult:
        return self.children_command(issue_id).run()

    @overload
    def create_command(self, request: IssueCreateRequest, /) -> Command[Issue]: ...
    @overload
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
    ) -> Command[Issue]: ...

    def create_command(  # type: ignore[misc]
        self, request: IssueCreateRequest | None = None, /, **kwargs: object
    ) -> Command[Issue]:
        """Create an issue and optionally attach labels.

        Creates the issue first, then attaches each ``label_ids`` entry via
        separate ``issue label add`` calls. A failure mid-loop can leave a
        partially labeled issue.
        """
        req = _resolve_request(request, kwargs, IssueCreateRequest)
        validate_nonblank(req.title)
        args = ["issue", "create", "--title", req.title]
        desc = req.description_input
        if isinstance(desc, InlineDescription):
            args.extend(["--description", desc.text])
        elif isinstance(desc, FileDescription):
            args.extend(["--description-file", str(pathlib.Path(desc.path).resolve())])
        elif desc.__class__.__name__ == "StdinDescription":
            args.append("--description-stdin")
        if req.priority is not None:
            args.extend(["--priority", req.priority])
        if req.assignee_id is not None:
            args.extend(["--assignee-id", req.assignee_id])
        if req.project_id is not None:
            args.extend(["--project", req.project_id])
        if req.parent_id is not None:
            args.extend(["--parent", req.parent_id])
        create_args, create_decode = self._plan_decode(tuple(args), _IssueWire)
        steps = [_Step(create_args, "run_bytes", decode=create_decode, result_alias="create")]
        for label_id in req.label_ids:
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
        if req.label_ids:
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
            wire = cast("_IssueWire", results[-1] if req.label_ids else results[0])
            return _issue_from_wire(wire)._with_client(self._client)

        return self._plan(steps=tuple(steps), finalize=finalize)

    @overload
    def create(self, request: IssueCreateRequest, /) -> Issue: ...
    @overload
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
    ) -> Issue: ...

    def create(self, request: IssueCreateRequest | None = None, /, **kwargs: object) -> Issue:  # type: ignore[misc]
        return self.create_command(cast("IssueCreateRequest", request), **kwargs).run()

    @overload
    def update_command(self, issue_id: str, request: IssueUpdateRequest, /) -> Command[Issue]: ...
    @overload
    def update_command(
        self,
        issue_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        project_id: str | None = None,
        parent_id: str | None = None,
    ) -> Command[Issue]: ...

    def update_command(  # type: ignore[misc]
        self, issue_id: str, request: IssueUpdateRequest | None = None, /, **kwargs: object
    ) -> Command[Issue]:
        req = _resolve_request(request, kwargs, IssueUpdateRequest)
        args = ["issue", "update", issue_id]
        if req.title is not None:
            args.extend(["--title", req.title])
        if req.description is not None:
            args.extend(["--description", req.description])
        if req.priority is not None:
            args.extend(["--priority", req.priority])
        if req.assignee_id is not None:
            args.extend(["--assignee-id", req.assignee_id])
        if req.project_id is not None:
            args.extend(["--project", req.project_id])
        if req.parent_id is not None:
            args.extend(["--parent", req.parent_id])
        plan_args, decode = self._plan_decode(tuple(args), _IssueWire)

        def finalize(results: tuple[object, ...]) -> Issue:
            return _issue_from_wire(cast("_IssueWire", results[0]))._with_client(self._client)

        return self._plan(steps=(_Step(plan_args, "run_bytes", decode=decode),), finalize=finalize)

    @overload
    def update(self, issue_id: str, request: IssueUpdateRequest, /) -> Issue: ...
    @overload
    def update(
        self,
        issue_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        project_id: str | None = None,
        parent_id: str | None = None,
    ) -> Issue: ...

    def update(  # type: ignore[misc]
        self, issue_id: str, request: IssueUpdateRequest | None = None, /, **kwargs: object
    ) -> Issue:
        return self.update_command(issue_id, cast("IssueUpdateRequest", request), **kwargs).run()

    @overload
    def assign_command(self, request: IssueAssignmentRequest, /) -> Command[Issue]: ...
    @overload
    def assign_command(
        self,
        *,
        issue_id: str,
        member_id: str | None = None,
        agent_id: str | None = None,
        squad_id: str | None = None,
        unassign: bool = False,
    ) -> Command[Issue]: ...

    def assign_command(  # type: ignore[misc]
        self, request: IssueAssignmentRequest | None = None, /, **kwargs: object
    ) -> Command[Issue]:
        req = _resolve_request(request, kwargs, IssueAssignmentRequest)
        args = ["issue", "assign", req.issue_id]
        if req.member_id is not None:
            args.extend(["--to-id", req.member_id])
        elif req.agent_id is not None:
            args.extend(["--to-id", req.agent_id])
        elif req.squad_id is not None:
            args.extend(["--to-id", req.squad_id])
        elif req.unassign:
            args.append("--unassign")
        plan_args, decode = self._plan_decode(tuple(args), _IssueWire)

        def finalize(results: tuple[object, ...]) -> Issue:
            return _issue_from_wire(cast("_IssueWire", results[0]))._with_client(self._client)

        return self._plan(steps=(_Step(plan_args, "run_bytes", decode=decode),), finalize=finalize)

    @overload
    def assign(self, request: IssueAssignmentRequest, /) -> Issue: ...
    @overload
    def assign(
        self,
        *,
        issue_id: str,
        member_id: str | None = None,
        agent_id: str | None = None,
        squad_id: str | None = None,
        unassign: bool = False,
    ) -> Issue: ...

    def assign(  # type: ignore[misc]
        self, request: IssueAssignmentRequest | None = None, /, **kwargs: object
    ) -> Issue:
        return self.assign_command(cast("IssueAssignmentRequest", request), **kwargs).run()

    def set_status_command(self, issue_id: str, status: IssueStatus) -> Command[Issue]:
        args, decode = self._plan_decode(("issue", "status", issue_id, status.value), _IssueWire)

        def finalize(results: tuple[object, ...]) -> Issue:
            return _issue_from_wire(cast("_IssueWire", results[0]))._with_client(self._client)

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def set_status(self, issue_id: str, status: IssueStatus) -> Issue:
        return self.set_status_command(issue_id, status).run()

    def deprioritize_command(self, issue_id: str) -> Command[str]:
        args = ("issue", "deprioritize", issue_id)

        def finalize(results: tuple[object, ...]) -> str:
            return cast("TextResult", results[0]).text

        return self._plan(steps=(_Step(args, "run_text"),), finalize=finalize)

    def deprioritize(self, issue_id: str) -> str:
        return self.deprioritize_command(issue_id).run()

    @overload
    def reorder_command(self, request: IssueReorderRequest, /) -> Command[Issue]: ...
    @overload
    def reorder_command(
        self,
        *,
        issue_id: str,
        before_id: str | None = None,
        after_id: str | None = None,
        top: bool = False,
        bottom: bool = False,
    ) -> Command[Issue]: ...

    def reorder_command(  # type: ignore[misc]
        self, request: IssueReorderRequest | None = None, /, **kwargs: object
    ) -> Command[Issue]:
        req = _resolve_request(request, kwargs, IssueReorderRequest)
        args = ["issue", "reorder", req.issue_id]
        if req.before_id is not None:
            args.extend(["--before", req.before_id])
        elif req.after_id is not None:
            args.extend(["--after", req.after_id])
        elif req.top:
            args.append("--top")
        elif req.bottom:
            args.append("--bottom")
        plan_args, decode = self._plan_decode(tuple(args), _IssueWire)

        def finalize(results: tuple[object, ...]) -> Issue:
            return _issue_from_wire(cast("_IssueWire", results[0]))._with_client(self._client)

        return self._plan(steps=(_Step(plan_args, "run_bytes", decode=decode),), finalize=finalize)

    @overload
    def reorder(self, request: IssueReorderRequest, /) -> Issue: ...
    @overload
    def reorder(
        self,
        *,
        issue_id: str,
        before_id: str | None = None,
        after_id: str | None = None,
        top: bool = False,
        bottom: bool = False,
    ) -> Issue: ...

    def reorder(  # type: ignore[misc]
        self, request: IssueReorderRequest | None = None, /, **kwargs: object
    ) -> Issue:
        return self.reorder_command(cast("IssueReorderRequest", request), **kwargs).run()

    def search_command(self, query: str) -> Command[tuple[IssueSummary, ...]]:
        args, decode = self._plan_decode_list(("issue", "search", query), IssueSummary)

        def finalize(results: tuple[object, ...]) -> tuple[IssueSummary, ...]:
            return cast("tuple[IssueSummary, ...]", results[0])

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def search(self, query: str) -> tuple[IssueSummary, ...]:
        return self.search_command(query).run()

    def runs_command(self, issue_id: str) -> Command[tuple[TaskRun, ...]]:
        args, decode = self._plan_decode_list(("issue", "runs", issue_id), TaskRun)

        def finalize(results: tuple[object, ...]) -> tuple[TaskRun, ...]:
            runs = cast("tuple[TaskRun, ...]", results[0])
            return tuple(
                TaskRun(
                    id=run.id,
                    status=run.status,
                    agent_id=run.agent_id,
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                    _client=self._client,
                    _issue_id=issue_id,
                )
                for run in runs
            )

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def runs(self, issue_id: str) -> tuple[TaskRun, ...]:
        return self.runs_command(issue_id).run()

    def run_messages_command(
        self, task_run_id: str, *, issue_id: str | None = None
    ) -> Command[tuple[RunMessage, ...]]:
        validate_nonblank(task_run_id)
        args = ["issue", "run-messages", task_run_id]
        if issue_id is not None:
            validate_nonblank(issue_id)
            args.extend(["--issue", issue_id])
        plan_args, decode = self._plan_decode_list(tuple(args), RunMessage)

        def finalize(results: tuple[object, ...]) -> tuple[RunMessage, ...]:
            return cast("tuple[RunMessage, ...]", results[0])

        return self._plan(steps=(_Step(plan_args, "run_bytes", decode=decode),), finalize=finalize)

    def run_messages(
        self, task_run_id: str, *, issue_id: str | None = None
    ) -> tuple[RunMessage, ...]:
        return self.run_messages_command(task_run_id, issue_id=issue_id).run()

    def usage_command(self, issue_id: str) -> Command[IssueUsage]:
        args, decode = self._plan_decode(("issue", "usage", issue_id), IssueUsage)

        def finalize(results: tuple[object, ...]) -> IssueUsage:
            return cast("IssueUsage", results[0])

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def usage(self, issue_id: str) -> IssueUsage:
        return self.usage_command(issue_id).run()

    def rerun_command(self, issue_id: str) -> Command[None]:
        validate_nonblank(issue_id)
        args = ("issue", "rerun", issue_id)

        def finalize(results: tuple[object, ...]) -> None:
            return None

        return self._plan(steps=(_Step(args, "run_text"),), finalize=finalize)

    def rerun(self, issue_id: str) -> None:
        self.rerun_command(issue_id).run()

    def cancel_task_command(self, task_id: str, *, issue_id: str | None = None) -> Command[None]:
        validate_nonblank(task_id)
        args = ["issue", "cancel-task", task_id]
        if issue_id is not None:
            validate_nonblank(issue_id)
            args.extend(["--issue", issue_id])

        def finalize(results: tuple[object, ...]) -> None:
            return None

        return self._plan(steps=(_Step(tuple(args), "run_text"),), finalize=finalize)

    def cancel_task(self, task_id: str, *, issue_id: str | None = None) -> None:
        self.cancel_task_command(task_id, issue_id=issue_id).run()
