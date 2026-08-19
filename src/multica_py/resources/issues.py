from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import TYPE_CHECKING, cast, overload

from multica_py._generated.approved_sdk import validate_nonblank
from multica_py._internal.commands import Command, _replace_plan, _Step, _StepRef
from multica_py._internal.decoders import decode_json
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
from multica_py.entities._base import _normalize_entity_id
from multica_py.entities.comments import Comment, CommentThread
from multica_py.entities.issues import Issue, TaskRun
from multica_py.entities.labels import Label
from multica_py.enums import IssueSort, IssueStatus, SortDirection
from multica_py.exceptions import JsonOutputError, OutputShapeError
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
    IssueChildrenResult,
    IssueDescriptionInput,
    IssueListFilter,
    IssueListPage,
    IssueMetadataItem,
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
from multica_py.resources._base import BaseResource, _normalize_description_file, _page_items
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
            Label(id=item.id, name=item.name, color=item.color, _client=self._client)
            for item in _page_items(self.labels.list(issue_id))
        )

    def _labels_relation_command(self, issue_id: str) -> Command[tuple[Label, ...]]:
        return self.labels.list_command(issue_id)._map(
            lambda page: tuple(
                Label(id=item.id, name=item.name, color=item.color, _client=self._client)
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
        options: OperationOptions | None = None,
    ) -> Command[tuple[RunMessage, ...]]:
        return self.run_messages_command(task_run_id, issue_id=issue_id, options=options)._map(
            _page_items
        )

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
        return OffsetPage(
            items=page.items,
            total=page.total or 0,
            limit=page.limit or 50,
            offset=page.offset or 0,
            has_more=page.has_more,
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
                page = _issue_list_page_from_wire(decoded)
            elif isinstance(decoded, IssueListPage):
                page = decoded
            else:
                raise TypeError("issue list command decoder returned an unexpected page")
            page = self._bind_issue_list_page(page)
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
        status: IssueStatus | str | None = None,
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
        status = _issue_status_token(filter.status) if filter.status is not None else None
        priority = filter.priority
        assignee_id = filter.assignee_id
        limit = filter.limit
        offset = filter.offset
        project_id = filter.project_id
        metadata = filter.metadata
        resolved_sort = filter.sort
        resolved_direction = filter.direction
        if offset is not None and offset < 0:
            raise ValueError("IssueResource.list: offset must be nonnegative (offset_nonnegative)")
        if resolved_direction is not None and resolved_sort is None:
            raise ValueError(
                "IssueResource.list: direction requires sort (direction_requires_sort)"
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
        status: IssueStatus | str | None = None,
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
        status: IssueStatus | str | None = None,
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

    def create_command(
        self,
        *,
        title: str,
        description: str | None = None,
        description_file: str | os.PathLike[str] | None = None,
        description_input: IssueDescriptionInput | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        label_ids: tuple[str, ...] = (),
        project: ProjectReference | None = None,
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
        args = ["issue", "create", "--title", title]
        args.extend(description_args)
        if priority is not None:
            args.extend(["--priority", priority])
        if assignee_id is not None:
            args.extend(["--assignee-id", assignee_id])
        if normalized_project is not None:
            args.extend(["--project", normalized_project])
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
        description: str | None = None,
        description_file: str | os.PathLike[str] | None = None,
        description_input: IssueDescriptionInput | None = None,
        priority: str | None = None,
        assignee_id: str | None = None,
        label_ids: tuple[str, ...] = (),
        project: ProjectReference | None = None,
        project_id: str | None = None,
        parent_id: str | None = None,
        options: OperationOptions | None = None,
    ) -> Issue:
        return self.create_command(
            title=title,
            description=description,
            description_file=description_file,
            description_input=description_input,
            priority=priority,
            assignee_id=assignee_id,
            label_ids=label_ids,
            project=project,
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
        args = ["issue", "assign", issue_id, *_assignee_assign_args(assignee)]
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
        self, issue_id: str, status: IssueStatus | str, *, options: OperationOptions | None = None
    ) -> Command[Issue]:
        validate_nonblank(issue_id)
        status_token = _issue_status_token(status)
        return self._decoded_command(
            ("issue", "status", issue_id, status_token), _IssueWire, options=options
        )._map(self._bind_issue)

    def set_status(
        self, issue_id: str, status: IssueStatus | str, *, options: OperationOptions | None = None
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
                        issue_id=issue_id,
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
