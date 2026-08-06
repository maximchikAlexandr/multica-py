from __future__ import annotations

import datetime
import json
import pathlib
from collections.abc import Mapping
from typing import TYPE_CHECKING, cast, overload

import msgspec

from multica_py._generated.approved_sdk import (
    validate_nonblank,
)
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
)
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus
from multica_py.models._bound import _BoundEntity
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

            def loader() -> tuple[RunMessage, ...]:
                return client.issues.run_messages(task_run_id, issue_id=issue_id)

            self._set_runtime("_messages", LazyCollection(loader))
        return self._messages  # type: ignore[return-value]


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

            self._set_runtime("_comments", LazyCollection(loader))
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

            self._recent_threads[key] = CursorLazyCollection(page_loader, initial_cursor=cursor)
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

            self._set_runtime("_labels", LazyCollection(_load_labels))
        return self._labels  # type: ignore[return-value]

    @property
    def subscribers(self) -> LazyCollection[Subscriber]:
        if self._subscribers is None:
            client = self._require_client(
                entity_type="Issue", entity_id=self.id, relation_name="subscribers"
            )
            issue_id = self.id
            subscribers = client.issues.subscribers
            self._set_runtime("_subscribers", LazyCollection(lambda: subscribers.list(issue_id)))
        return self._subscribers  # type: ignore[return-value]

    @property
    def metadata(self) -> LazyMapping[str, MetadataValue]:
        if self._metadata is None:
            client = self._require_client(
                entity_type="Issue", entity_id=self.id, relation_name="metadata"
            )
            issue_id = self.id

            def loader() -> Mapping[str, MetadataValue]:
                return client.issues.metadata.list(issue_id)

            self._set_runtime("_metadata", LazyMapping(loader))
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
                "_pull_requests", LazyCollection(lambda: issues.pull_requests(issue_id))
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

            self._set_runtime("_children", LazyCollection(loader))
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

            self._set_runtime("_runs", LazyCollection(loader))
        return self._runs  # type: ignore[return-value]

    def add_comment(self, body: str) -> Comment:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="comments"
        )
        result = client.issues.comments.add(self.id, body)
        self._invalidate_comments()
        return _bind_comment(result, client)

    def reply(self, thread_id: str, body: str) -> Comment:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="comments"
        )
        result = client.issues.comments.reply(self.id, thread_id, body)
        self._invalidate_comments()
        return _bind_comment(result, client)

    def add_label(self, label_id: str) -> tuple[Label, ...]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="labels"
        )
        result = client.issues.labels.add(self.id, label_id)
        self._invalidate_labels()
        return tuple(
            Label(id=item.id, name=item.name, color=item.color, _client=client) for item in result
        )

    def remove_label(self, label_id: str) -> tuple[Label, ...]:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="labels"
        )
        result = client.issues.labels.remove(self.id, label_id)
        self._invalidate_labels()
        return tuple(
            Label(id=item.id, name=item.name, color=item.color, _client=client) for item in result
        )

    def add_subscriber(self, user_id: str) -> None:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="subscribers"
        )
        client.issues.subscribers.add(self.id, user_id)
        self._invalidate_subscribers()

    def remove_subscriber(self, user_id: str) -> None:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="subscribers"
        )
        client.issues.subscribers.remove(self.id, user_id)
        self._invalidate_subscribers()

    def set_metadata(self, key: str, value: MetadataValue) -> MetadataEntry:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="metadata"
        )
        result = client.issues.metadata.set(self.id, key, value)
        self._invalidate_metadata()
        return result

    def delete_metadata(self, key: str) -> None:
        client = self._require_client(
            entity_type="Issue", entity_id=self.id, relation_name="metadata"
        )
        client.issues.metadata.delete(self.id, key)
        self._invalidate_metadata()

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

    def list(self, filter: IssueListFilter | None = None) -> IssueListPage:
        args = ["issue", "list"]
        if filter is not None:
            sort = filter.sort
            direction = filter.direction
            if filter.offset is not None and filter.offset < 0:
                raise ValueError(
                    "IssueResource.list: offset must be nonnegative (offset_nonnegative)"
                )
            if direction is not None and sort is None:
                raise ValueError(
                    "IssueResource.list: direction requires sort (direction_requires_sort)"
                )
            if filter.status is not None:
                args.extend(["--status", filter.status.value])
            if filter.priority is not None:
                args.extend(["--priority", filter.priority])
            if filter.assignee_id is not None:
                args.extend(["--assignee-id", filter.assignee_id])
            if filter.limit is not None:
                args.extend(["--limit", str(filter.limit)])
            if filter.offset is not None:
                args.extend(["--offset", str(filter.offset)])
            if filter.project_id is not None:
                args.extend(["--project", filter.project_id])
            seen_metadata_keys: set[str] = set()
            for item in filter.metadata:
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
                args.extend(["--sort", sort.value])
            if direction is not None:
                args.extend(["--direction", direction.value])
        page = _issue_list_page_from_wire(self._run_json_decode(tuple(args), _IssueListPageWire))
        return page

    def get(self, issue_id: str) -> Issue:
        validate_nonblank(issue_id)
        return _issue_from_wire(
            self._run_json_decode(("issue", "get", issue_id), _IssueWire)
        )._with_client(self._client)

    def pull_requests(self, issue_id: str) -> tuple[LinkedPullRequest, ...]:
        result = self._run_json_decode(
            ("issue", "pull-requests", issue_id), _IssuePullRequestsResultWire
        )
        return _issue_pull_requests_from_wire(result)

    def children(self, issue_id: str) -> IssueChildrenResult:
        result = self._run_json_decode(("issue", "children", issue_id), _IssueChildrenResultWire)
        return _issue_children_result_from_wire(result)

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
        issue = _issue_from_wire(self._run_json_decode(tuple(args), _IssueWire))._with_client(
            self._client
        )
        for label_id in req.label_ids:
            self.labels.add(issue.id, label_id)
        if req.label_ids:
            return self.get(issue.id)
        return issue

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
        return _issue_from_wire(self._run_json_decode(tuple(args), _IssueWire))._with_client(
            self._client
        )

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
        return _issue_from_wire(self._run_json_decode(tuple(args), _IssueWire))._with_client(
            self._client
        )

    def set_status(self, issue_id: str, status: IssueStatus) -> Issue:
        return _issue_from_wire(
            self._run_json_decode(("issue", "status", issue_id, status.value), _IssueWire)
        )._with_client(self._client)

    def deprioritize(self, issue_id: str) -> str:
        return self._transport.run_text(("issue", "deprioritize", issue_id)).text

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
        return _issue_from_wire(self._run_json_decode(tuple(args), _IssueWire))._with_client(
            self._client
        )

    def search(self, query: str) -> tuple[IssueSummary, ...]:
        return self._run_json_decode_list(("issue", "search", query), IssueSummary)

    def runs(self, issue_id: str) -> tuple[TaskRun, ...]:
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
            for run in self._run_json_decode_list(("issue", "runs", issue_id), TaskRun)
        )

    def run_messages(
        self, task_run_id: str, *, issue_id: str | None = None
    ) -> tuple[RunMessage, ...]:
        validate_nonblank(task_run_id)
        args = ["issue", "run-messages", task_run_id]
        if issue_id is not None:
            validate_nonblank(issue_id)
            args.extend(["--issue", issue_id])
        return self._run_json_decode_list(tuple(args), RunMessage)

    def usage(self, issue_id: str) -> IssueUsage:
        return self._run_json_decode(("issue", "usage", issue_id), IssueUsage)

    def rerun(self, issue_id: str) -> None:
        validate_nonblank(issue_id)
        self._transport.run_text(("issue", "rerun", issue_id))

    def cancel_task(self, task_id: str, *, issue_id: str | None = None) -> None:
        validate_nonblank(task_id)
        args = ["issue", "cancel-task", task_id]
        if issue_id is not None:
            validate_nonblank(issue_id)
            args.extend(["--issue", issue_id])
        self._transport.run_text(tuple(args))
