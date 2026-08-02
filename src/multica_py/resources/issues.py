from __future__ import annotations

import datetime
import pathlib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from multica_py._generated.approved_sdk import (
    validate_nonblank,
)
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    IssueChildrenResultWire,
    IssueListPageWire,
    IssuePullRequestsResultWire,
    IssueWire,
    issue_children_result_from_wire,
    issue_data_from_wire,
    issue_list_page_from_wire,
    issue_pull_requests_from_wire,
)
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus
from multica_py.models import ResourceEntity
from multica_py.models.issue_activity import (
    CommentCursor,
    CommentListFlatRequest,
    CommentListRecentRequest,
    IssueUsage,
    MetadataEntry,
    RunMessage,
    Subscriber,
    TaskRunData,
)
from multica_py.models.issue_activity import (
    TaskRun as TaskRunRecord,
)
from multica_py.models.issues import (
    FileDescription,
    InlineDescription,
    Issue,
    IssueAssignee,
    IssueAssignmentRequest,
    IssueChildrenResult,
    IssueChildStageGroup,
    IssueCreateRequest,
    IssueData,
    IssueListFilter,
    IssueMetadataItem,
    IssueReorderRequest,
    IssueSummary,
    IssueUpdateRequest,
    LinkedPullRequest,
)
from multica_py.models.labels import LabelData
from multica_py.models.relations import (
    CursorLazyCollection,
    CursorPage,
    LazyCollection,
    LazyMapping,
    RelationMetadata,
    _RelationLoad,
)
from multica_py.resources._base import BaseResource
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


@dataclass(frozen=True, slots=True)
class BoundIssueListPage:
    """Immutable page whose compact issue rows retain their client view."""

    issues: tuple[IssueEntity, ...]
    has_more: bool
    limit: int | None
    offset: int | None
    total: int | None


if TYPE_CHECKING:
    from multica_py.client import MulticaClient


def _issue_data_from_summary(summary: IssueSummary) -> IssueData:
    return IssueData(
        id=summary.id,
        title=summary.title,
        status=summary.status,
        priority=summary.priority,
        created_at=summary.created_at,
        parent_id=summary.parent_id,
        project_id=summary.project_id,
        creator_id=summary.creator_id,
        creator_type=summary.creator_type,
    )


def _issue_data_from_issue(issue: Issue) -> IssueData:
    return IssueData(
        id=issue.id,
        title=issue.title,
        description=issue.description,
        status=issue.status,
        priority=issue.priority,
        assignee=issue.assignee,
        pull_requests=issue.pull_requests,
        child_stages=issue.children,
        label_names=issue.labels,
        metadata_snapshot=issue.metadata,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        parent_id=issue.parent_id,
        project_id=issue.project_id,
        creator_id=issue.creator_id,
        creator_type=issue.creator_type,
    )


class TaskRun(ResourceEntity[TaskRunData]):
    def __init__(
        self,
        data: TaskRunData,
        client: MulticaClient | None = None,
        *,
        issue_id: str | None = None,
    ) -> None:
        super().__init__(data, client=client)
        self._issue_id = issue_id
        self._messages: LazyCollection[RunMessage] | None = None

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def status(self) -> str:
        return self._data.status

    @property
    def agent_id(self) -> str | None:
        return self._data.agent_id

    @property
    def started_at(self) -> datetime.datetime | None:
        return self._data.started_at

    @property
    def completed_at(self) -> datetime.datetime | None:
        return self._data.completed_at

    @property
    def messages(self) -> LazyCollection[RunMessage]:
        if self._messages is None:
            client = self._require_client(
                entity_type="TaskRun", entity_id=self._data.id, relation_name="messages"
            )
            task_run_id = self._data.id
            issue_id = self._issue_id

            def loader() -> tuple[RunMessage, ...]:
                return client.issues.run_messages(task_run_id, issue_id=issue_id)

            self._messages = LazyCollection(loader)
        return self._messages


class IssueEntity(ResourceEntity[IssueData]):
    def __init__(self, data: IssueData, client: MulticaClient | None = None) -> None:
        super().__init__(data, client=client)
        self._comments: LazyCollection[Comment] | None = None
        self._recent_threads: dict[
            tuple[int, tuple[str, str] | None], CursorLazyCollection[CommentThread]
        ] = {}
        self._labels: LazyCollection[Label] | None = None
        self._subscribers: LazyCollection[Subscriber] | None = None
        self._metadata: LazyMapping[str, MetadataValue] | None = None
        self._pull_requests: LazyCollection[LinkedPullRequest] | None = None
        self._children: LazyCollection[IssueEntity] | None = None
        self._runs: LazyCollection[TaskRun] | None = None

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def title(self) -> str:
        return self._data.title

    @property
    def description(self) -> str | None:
        return self._data.description

    @property
    def status(self) -> IssueStatus:
        return self._data.status

    @property
    def priority(self) -> str | None:
        return self._data.priority

    @property
    def assignee(self) -> IssueAssignee | None:
        return self._data.assignee

    @property
    def label_names(self) -> tuple[str, ...]:
        return self._data.label_names

    @property
    def child_stages(self) -> tuple[IssueChildStageGroup, ...]:
        return self._data.child_stages

    @property
    def metadata_snapshot(self) -> tuple[IssueMetadataItem, ...]:
        return self._data.metadata_snapshot

    @property
    def pull_request_snapshot(self) -> tuple[LinkedPullRequest, ...]:
        return self._data.pull_requests

    @property
    def parent_id(self) -> str | None:
        return self._data.parent_id

    @property
    def project_id(self) -> str | None:
        return self._data.project_id

    @property
    def creator_id(self) -> str | None:
        return self._data.creator_id

    @property
    def creator_type(self) -> str | None:
        return self._data.creator_type

    def _check_client(self, relation_name: str) -> MulticaClient:
        return self._require_client(
            entity_type="IssueEntity", entity_id=self._data.id, relation_name=relation_name
        )

    @property
    def comments(self) -> LazyCollection[Comment]:
        if self._comments is None:
            client = self._check_client("comments")
            issue_id = self._data.id

            def loader() -> tuple[Comment, ...]:
                page = client.issues.comments.list_flat(CommentListFlatRequest(issue_id=issue_id))
                return tuple(_bind_comment(item, client) for item in page.items)

            self._comments = LazyCollection(loader)
        return self._comments

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
            client = self._check_client("recent_comment_threads")
            issue_id = self._data.id

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
            client = self._check_client("labels")
            issue_id = self._data.id
            self._labels = LazyCollection(
                lambda: tuple(
                    Label(LabelData(id=item.id, name=item.name, color=item.color), client=client)
                    for item in client.issues.labels.list(issue_id)
                )
            )
        return self._labels

    @property
    def subscribers(self) -> LazyCollection[Subscriber]:
        if self._subscribers is None:
            client = self._check_client("subscribers")
            issue_id = self._data.id
            subscribers = client.issues.subscribers
            self._subscribers = LazyCollection(lambda: subscribers.list(issue_id))
        return self._subscribers

    @property
    def metadata(self) -> LazyMapping[str, MetadataValue]:
        if self._metadata is None:
            client = self._check_client("metadata")
            issue_id = self._data.id

            def loader() -> Mapping[str, MetadataValue]:
                return client.issues.metadata.list(issue_id)

            self._metadata = LazyMapping(loader)
        return self._metadata

    @property
    def pull_requests(self) -> LazyCollection[LinkedPullRequest]:
        if self._pull_requests is None:
            client = self._check_client("pull_requests")
            issue_id = self._data.id
            issues = client.issues
            self._pull_requests = LazyCollection(lambda: issues.pull_requests(issue_id))
        return self._pull_requests

    @property
    def children(self) -> LazyCollection[IssueEntity]:
        if self._children is None:
            client = self._check_client("children")
            issue_id = self._data.id

            def loader() -> _RelationLoad[IssueEntity]:
                result: IssueChildrenResult = client.issues.children(issue_id)
                return _RelationLoad(
                    tuple(
                        IssueEntity(_issue_data_from_issue(item), client=client)
                        for item in result.children
                    ),
                    RelationMetadata(
                        total=result.total,
                        child_stages=result.child_stages,
                        unstaged=tuple(
                            IssueEntity(_issue_data_from_issue(item), client=client)
                            for item in result.unstaged
                        ),
                    ),
                )

            self._children = LazyCollection(loader)
        return self._children

    @property
    def runs(self) -> LazyCollection[TaskRun]:
        if self._runs is None:
            client = self._check_client("runs")
            issue_id = self._data.id

            def loader() -> tuple[TaskRun, ...]:
                runs = client.issues.runs(issue_id)
                return tuple(
                    TaskRun(
                        TaskRunData(
                            id=run.id,
                            status=run.status,
                            agent_id=run.agent_id,
                            started_at=run.started_at,
                            completed_at=run.completed_at,
                        ),
                        client=client,
                        issue_id=issue_id,
                    )
                    for run in runs
                )

            self._runs = LazyCollection(loader)
        return self._runs

    def add_comment(self, body: str) -> Comment:
        client = self._check_client("comments")
        result = client.issues.comments.add(self._data.id, body)
        self._invalidate_comments()
        return _bind_comment(result, client)

    def reply(self, thread_id: str, body: str) -> Comment:
        client = self._check_client("comments")
        result = client.issues.comments.reply(self._data.id, thread_id, body)
        self._invalidate_comments()
        return _bind_comment(result, client)

    def add_label(self, label_id: str) -> tuple[Label, ...]:
        client = self._check_client("labels")
        result = client.issues.labels.add(self._data.id, label_id)
        self._invalidate_labels()
        return tuple(
            Label(LabelData(id=item.id, name=item.name, color=item.color), client=client)
            for item in result
        )

    def remove_label(self, label_id: str) -> tuple[Label, ...]:
        client = self._check_client("labels")
        result = client.issues.labels.remove(self._data.id, label_id)
        self._invalidate_labels()
        return tuple(
            Label(LabelData(id=item.id, name=item.name, color=item.color), client=client)
            for item in result
        )

    def add_subscriber(self, user_id: str) -> None:
        client = self._check_client("subscribers")
        client.issues.subscribers.add(self._data.id, user_id)
        self._invalidate_subscribers()

    def remove_subscriber(self, user_id: str) -> None:
        client = self._check_client("subscribers")
        client.issues.subscribers.remove(self._data.id, user_id)
        self._invalidate_subscribers()

    def set_metadata(self, key: str, value: MetadataValue) -> MetadataEntry:
        client = self._check_client("metadata")
        result = client.issues.metadata.set(self._data.id, key, value)
        self._invalidate_metadata()
        return result

    def delete_metadata(self, key: str) -> None:
        client = self._check_client("metadata")
        client.issues.metadata.delete(self._data.id, key)
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

    def list(self, filter: IssueListFilter | None = None) -> BoundIssueListPage:
        args = ["issue", "list"]
        if filter is not None:
            if filter.offset is not None and filter.offset < 0:
                raise ValueError(
                    "IssueResource.list: offset must be nonnegative (offset_nonnegative)"
                )
            if filter.direction is not None and filter.sort is None:
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
            if filter.sort is not None:
                args.extend(["--sort", filter.sort.value])
            if filter.direction is not None:
                args.extend(["--direction", filter.direction.value])
        page = issue_list_page_from_wire(self._run_json_decode(tuple(args), IssueListPageWire))
        return BoundIssueListPage(
            issues=tuple(self._bind_summary(summary) for summary in page.issues),
            has_more=page.has_more,
            limit=page.limit,
            offset=page.offset,
            total=page.total,
        )

    def _bind_issue(self, data: IssueData) -> IssueEntity:
        return IssueEntity(data, client=self._client)

    def _bind_summary(self, summary: IssueSummary) -> IssueEntity:
        return self._bind_issue(_issue_data_from_summary(summary))

    def get(self, issue_id: str) -> IssueEntity:
        validate_nonblank(issue_id)
        return self._bind_issue(
            issue_data_from_wire(self._run_json_decode(("issue", "get", issue_id), IssueWire))
        )

    def pull_requests(self, issue_id: str) -> tuple[LinkedPullRequest, ...]:
        result = self._run_json_decode(
            ("issue", "pull-requests", issue_id), IssuePullRequestsResultWire
        )
        return issue_pull_requests_from_wire(result)

    def children(self, issue_id: str) -> IssueChildrenResult:
        result = self._run_json_decode(("issue", "children", issue_id), IssueChildrenResultWire)
        return issue_children_result_from_wire(result)

    def create(self, request: IssueCreateRequest) -> IssueEntity:
        """Create an issue and optionally attach labels.

        Creates the issue first, then attaches each ``label_ids`` entry via
        separate ``issue label add`` calls. A failure mid-loop can leave a
        partially labeled issue.
        """
        validate_nonblank(request.title)
        args = ["issue", "create", "--title", request.title]
        desc = request.description_input
        if isinstance(desc, InlineDescription):
            args.extend(["--description", desc.text])
        elif isinstance(desc, FileDescription):
            args.extend(["--description-file", str(pathlib.Path(desc.path).resolve())])
        elif desc.__class__.__name__ == "StdinDescription":
            args.append("--description-stdin")
        if request.priority is not None:
            args.extend(["--priority", request.priority])
        if request.assignee_id is not None:
            args.extend(["--assignee-id", request.assignee_id])
        if request.project_id is not None:
            args.extend(["--project", request.project_id])
        if request.parent_id is not None:
            args.extend(["--parent", request.parent_id])
        issue = self._bind_issue(
            issue_data_from_wire(self._run_json_decode(tuple(args), IssueWire))
        )
        for label_id in request.label_ids:
            self.labels.add(issue.id, label_id)
        if request.label_ids:
            return self.get(issue.id)
        return issue

    def update(self, issue_id: str, request: IssueUpdateRequest) -> IssueEntity:
        args = ["issue", "update", issue_id]
        if request.title is not None:
            args.extend(["--title", request.title])
        if request.description is not None:
            args.extend(["--description", request.description])
        if request.priority is not None:
            args.extend(["--priority", request.priority])
        if request.assignee_id is not None:
            args.extend(["--assignee-id", request.assignee_id])
        if request.project_id is not None:
            args.extend(["--project", request.project_id])
        if request.parent_id is not None:
            args.extend(["--parent", request.parent_id])
        return self._bind_issue(issue_data_from_wire(self._run_json_decode(tuple(args), IssueWire)))

    def assign(self, request: IssueAssignmentRequest) -> IssueEntity:
        args = ["issue", "assign", request.issue_id]
        if request.member_id is not None:
            args.extend(["--to-id", request.member_id])
        elif request.agent_id is not None:
            args.extend(["--to-id", request.agent_id])
        elif request.squad_id is not None:
            args.extend(["--to-id", request.squad_id])
        elif request.unassign:
            args.append("--unassign")
        return self._bind_issue(issue_data_from_wire(self._run_json_decode(tuple(args), IssueWire)))

    def set_status(self, issue_id: str, status: IssueStatus) -> IssueEntity:
        return self._bind_issue(
            issue_data_from_wire(
                self._run_json_decode(("issue", "status", issue_id, status.value), IssueWire)
            )
        )

    def deprioritize(self, issue_id: str) -> str:
        return self._transport.run_text(("issue", "deprioritize", issue_id)).text

    def reorder(self, request: IssueReorderRequest) -> IssueEntity:
        args = ["issue", "reorder", request.issue_id]
        if request.before_id is not None:
            args.extend(["--before", request.before_id])
        elif request.after_id is not None:
            args.extend(["--after", request.after_id])
        elif request.top:
            args.append("--top")
        elif request.bottom:
            args.append("--bottom")
        return self._bind_issue(issue_data_from_wire(self._run_json_decode(tuple(args), IssueWire)))

    def search(self, query: str) -> tuple[IssueSummary, ...]:
        return self._run_json_decode_list(("issue", "search", query), IssueSummary)

    def runs(self, issue_id: str) -> tuple[TaskRun, ...]:
        return tuple(
            TaskRun(
                TaskRunData(
                    id=run.id,
                    status=run.status,
                    agent_id=run.agent_id,
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                ),
                client=self._client,
                issue_id=issue_id,
            )
            for run in self._run_json_decode_list(("issue", "runs", issue_id), TaskRunRecord)
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
