from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Literal, cast
from unittest.mock import MagicMock

import pytest

from multica_py._internal.decoders import decode_json
from multica_py._internal.specs import RawCommandResult
from multica_py._internal.wire_models import IssueWire, issue_data_from_wire
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus
from multica_py.exceptions import OutputShapeError, RelationPaginationError
from multica_py.models.common import Page
from multica_py.models.issue_activity import (
    Comment as CommentRecord,
)
from multica_py.models.issue_activity import (
    CommentCursor,
    CommentData,
    CommentListFlatRequest,
    CommentListRecentRequest,
    CommentListThreadRequest,
    CommentThreadData,
    RunMessage,
    TaskRunData,
)
from multica_py.models.issue_activity import (
    CommentThread as CommentThreadRecord,
)
from multica_py.models.issue_activity import (
    TaskRun as TaskRunRecord,
)
from multica_py.models.issues import (
    Issue,
    IssueChildrenResult,
    IssueChildStageGroup,
    IssueData,
    IssueMetadataItem,
    LinkedPullRequest,
)
from multica_py.models.relations import (
    CursorLazyCollection,
    CursorPage,
    LazyCollection,
    LazyMapping,
    OffsetLazyCollection,
    OffsetPage,
)
from multica_py.resources.issue_comments import Comment, CommentThread
from multica_py.resources.issues import IssueEntity, IssueResource, TaskRun


@dataclass(frozen=True)
class IssueRelationCase:
    name: str
    relation: str
    expected_type: type[object]


@dataclass(frozen=True)
class IssueAddressingCase:
    name: str
    method: str
    args: tuple[str, ...]
    expected_argv: tuple[str, ...]
    transport_method: str


@dataclass(frozen=True)
class DirectBoundCase:
    name: str
    operation: Literal["list", "list_flat", "list_thread", "list_recent", "add", "reply", "runs"]
    stdout: bytes
    expected_argv: tuple[str, ...]
    expected_type: type[Comment | CommentThread | TaskRun]
    expected_data_type: type[CommentData | CommentThreadData | TaskRunData]
    second_hop: Literal["none", "comments", "messages"]


RELATION_CASES = (
    IssueRelationCase("comments", "comments", LazyCollection),
    IssueRelationCase("labels", "labels", LazyCollection),
    IssueRelationCase("subscribers", "subscribers", LazyCollection),
    IssueRelationCase("metadata", "metadata", LazyMapping),
    IssueRelationCase("pull requests", "pull_requests", LazyCollection),
    IssueRelationCase("children", "children", LazyCollection),
    IssueRelationCase("runs", "runs", LazyCollection),
)

ADDRESSING_CASES = (
    IssueAddressingCase(
        "rerun uses issue id only",
        "rerun",
        ("iss_1",),
        ("issue", "rerun", "iss_1"),
        "run_text",
    ),
    IssueAddressingCase(
        "cancel task uses task id",
        "cancel_task",
        ("task_1",),
        ("issue", "cancel-task", "task_1"),
        "run_text",
    ),
)

DIRECT_BOUND_CASES = (
    DirectBoundCase(
        "list binds comments",
        "list",
        b'[{"id":"c1","content":"comment"}]',
        ("issue", "comment", "list", "iss_1", "--output", "json"),
        Comment,
        CommentData,
        "none",
    ),
    DirectBoundCase(
        "flat list binds comments",
        "list_flat",
        b'[{"id":"c1","content":"comment"}]',
        ("issue", "comment", "list", "iss_1", "--output", "json"),
        Comment,
        CommentData,
        "none",
    ),
    DirectBoundCase(
        "thread list binds comments",
        "list_thread",
        b'[{"id":"c1","content":"reply","parent_id":"th_1"}]',
        (
            "issue",
            "comment",
            "list",
            "iss_1",
            "--thread",
            "th_1",
            "--tail",
            "10",
            "--output",
            "json",
        ),
        Comment,
        CommentData,
        "none",
    ),
    DirectBoundCase(
        "recent list binds comment threads",
        "list_recent",
        b'[{"id":"th_1","comments":[]}]',
        ("issue", "comment", "list", "iss_1", "--recent", "10", "--output", "json"),
        CommentThread,
        CommentThreadData,
        "comments",
    ),
    DirectBoundCase(
        "add binds comment",
        "add",
        b'{"id":"c1","content":"comment"}',
        ("issue", "comment", "add", "iss_1", "--content", "comment", "--output", "json"),
        Comment,
        CommentData,
        "none",
    ),
    DirectBoundCase(
        "reply binds comment",
        "reply",
        b'{"id":"c1","content":"reply","parent_id":"th_1"}',
        (
            "issue",
            "comment",
            "add",
            "iss_1",
            "--content",
            "reply",
            "--parent",
            "th_1",
            "--output",
            "json",
        ),
        Comment,
        CommentData,
        "none",
    ),
    DirectBoundCase(
        "runs bind task runs",
        "runs",
        b'[{"id":"run_1","status":"done"}]',
        ("issue", "runs", "iss_1", "--output", "json"),
        TaskRun,
        TaskRunData,
        "messages",
    ),
)


def _issue(client: MulticaClient | None = None) -> IssueEntity:
    return IssueEntity(
        IssueData(
            id="iss_1",
            title="Issue",
            status=IssueStatus.todo,
            label_names=("bug",),
            child_stages=(IssueChildStageGroup(name="todo", count=1),),
            metadata_snapshot=(IssueMetadataItem(key="priority", value="high"),),
        ),
        client=client,
    )


def _client() -> MagicMock:
    client = MagicMock()
    client.issues.comments.list_flat.return_value = Page(items=())
    client.issues.comments.list_recent.return_value = Page(items=(), next_cursor=None)
    client.issues.comments.list_thread.return_value = Page(items=(), next_cursor=None)
    client.issues.labels.list.return_value = ()
    client.issues.subscribers.list.return_value = ()
    client.issues.metadata.list.return_value = {}
    client.issues.pull_requests.return_value = ()
    client.issues.children.return_value = IssueChildrenResult()
    client.issues.runs.return_value = ()
    return client


@pytest.mark.parametrize("case", RELATION_CASES, ids=lambda case: case.name)
def test_issue_relation_properties_are_lazy(case: IssueRelationCase) -> None:
    client = _client()
    entity = _issue(client)

    relation = cast(
        "LazyCollection[object] | LazyMapping[str, object]",
        getattr(entity, case.relation),
    )

    assert isinstance(relation, case.expected_type)
    assert relation.loaded is False
    client.issues.assert_not_called()


def test_issue_snapshot_names_are_migrated() -> None:
    entity = _issue(_client())

    assert entity.label_names == ("bug",)
    assert entity.child_stages == (IssueChildStageGroup(name="todo", count=1),)
    assert entity.metadata_snapshot == (IssueMetadataItem(key="priority", value="high"),)
    assert isinstance(entity.metadata, LazyMapping)


def test_issue_children_preserve_aggregate_metadata() -> None:
    client = _client()
    child = Issue(id="child", title="Child", status=IssueStatus.done)
    client.issues.children.return_value = IssueChildrenResult(
        children=(child,),
        total=2,
        child_stages=(IssueChildStageGroup(name="done", count=1),),
        unstaged=(child,),
    )
    entity = _issue(client)

    result = entity.children.all()

    assert [item.id for item in result] == ["child"]
    assert entity.children.metadata.total == 2
    assert entity.children.metadata.child_stages == (IssueChildStageGroup(name="done", count=1),)
    assert [item.id for item in entity.children.metadata.unstaged] == ["child"]


def test_issue_comments_and_query_views_invalidate_after_add() -> None:
    client = _client()
    client.issues.comments.list_flat.side_effect = [
        Page(items=(CommentRecord(id="c1", body="one"),)),
        Page(items=(CommentRecord(id="c2", body="two"),)),
    ]
    client.issues.comments.list_recent.return_value = Page(
        items=(CommentThreadRecord(id="th_1"),), next_cursor=None
    )
    entity = _issue(client)

    entity.comments.all()
    recent = entity.recent_comment_threads()
    recent.all()
    entity.add_comment("new")

    assert entity.comments.loaded is False
    assert recent.loaded is False


def test_comment_thread_cursor_relation_inherits_issue_context() -> None:
    client = _client()
    entity = _issue(client)
    client.issues.comments.list_recent.return_value = Page(
        items=(CommentThreadRecord(id="th_1"),), next_cursor=None
    )
    bound_thread = entity.recent_comment_threads().all()[0]
    client.issues.comments.list_thread.return_value = Page(
        items=(CommentRecord(id="c1", body="reply"),), next_cursor=None
    )

    assert isinstance(bound_thread.comments, CursorLazyCollection)
    assert [comment.id for comment in bound_thread.comments.all()] == ["c1"]
    client.issues.comments.list_thread.assert_called_once()
    request = client.issues.comments.list_thread.call_args.args[0]
    assert request.issue_id == "iss_1"
    assert request.thread_id == "th_1"


def test_task_run_messages_preserve_issue_and_task_ids() -> None:
    client = _client()
    client.issues.runs.return_value = (TaskRunRecord(id="run_1", status="done"),)
    client.issues.run_messages.return_value = (
        RunMessage(id="m1", run_id="run_1", role="assistant", content="ok"),
    )
    entity = _issue(client)

    run = entity.runs.all()[0]
    assert [message.id for message in run.messages.all()] == ["m1"]
    client.issues.run_messages.assert_called_once_with("run_1", issue_id="iss_1")


def test_cursor_query_passes_complete_pair() -> None:
    client = _client()
    entity = _issue(client)
    cursor = CommentCursor(before="before", before_id="before-id")
    entity.recent_comment_threads(limit=5, cursor=cursor).page(cursor=cursor)

    request = client.issues.comments.list_recent.call_args.args[0]
    assert request.limit == 5
    assert request.cursor == cursor


def test_cursor_no_progress_is_typed_and_retryable() -> None:
    cursor = CommentCursor(before="before", before_id="before-id")
    calls = 0

    def loader(*, cursor: CommentCursor | None = None) -> CursorPage[str]:
        nonlocal calls
        calls += 1
        return CursorPage(items=("item",), next_cursor=cursor or cursor_value)

    cursor_value = cursor
    relation: CursorLazyCollection[str] = CursorLazyCollection(loader)
    with pytest.raises(RelationPaginationError) as exc:
        relation.all()
    assert exc.value.reason == "repeated_cursor"
    assert relation.loaded is False
    assert calls == 2


def test_offset_pagination_has_a_hard_page_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("multica_py.models.relations._MAX_RELATION_PAGES", 2)
    calls = 0

    def loader(*, limit: int | None, offset: int) -> OffsetPage[str]:
        nonlocal calls
        calls += 1
        return OffsetPage(
            items=(str(offset),), total=3, limit=limit or 1, offset=offset, has_more=True
        )

    relation: OffsetLazyCollection[str] = OffsetLazyCollection(loader, default_limit=1)
    with pytest.raises(RelationPaginationError, match="repeated_offset"):
        relation.all()

    assert calls == 2
    assert relation.loaded is False


def test_cursor_pagination_has_a_hard_page_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("multica_py.models.relations._MAX_RELATION_PAGES", 2)
    calls = 0

    def loader(*, cursor: CommentCursor | None) -> CursorPage[str]:
        nonlocal calls
        calls += 1
        return CursorPage(
            items=(str(calls),),
            next_cursor=CommentCursor(before=str(calls), before_id=str(calls)),
        )

    relation: CursorLazyCollection[str] = CursorLazyCollection(loader)
    with pytest.raises(RelationPaginationError, match="repeated_cursor"):
        relation.all()

    assert calls == 2
    assert relation.loaded is False


@pytest.mark.parametrize(
    ("kind", "reason"), (("offset", "repeated_offset"), ("cursor", "repeated_cursor"))
)
def test_pagination_has_a_hard_item_budget(
    kind: str, reason: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("multica_py.models.relations._MAX_RELATION_ITEMS", 1)
    if kind == "offset":
        relation: LazyCollection[str] = OffsetLazyCollection(
            lambda *, limit, offset: OffsetPage(("one", "two"), 2, limit or 1, offset, False)
        )
    else:
        relation = CursorLazyCollection(lambda *, cursor: CursorPage(("one", "two")))

    with pytest.raises(RelationPaginationError, match=reason):
        relation.all()

    assert relation.loaded is False


def test_offset_pagination_uses_requested_offset_not_response_metadata() -> None:
    relation: OffsetLazyCollection[str] = OffsetLazyCollection(
        lambda *, limit, offset: OffsetPage(("item",), 1, limit or 1, offset + 1, False)
    )

    assert relation.all() == ("item",)

    assert relation.loaded is True


def test_issue_wire_missing_and_empty_fields_do_not_seed_relations() -> None:
    missing = issue_data_from_wire(
        decode_json(b'{"id":"i1","title":"t","status":"todo"}', IssueWire)
    )
    empty = issue_data_from_wire(
        decode_json(
            b'{"id":"i1","title":"t","status":"todo","labels":[],"children":[],"metadata":{}}',
            IssueWire,
        )
    )
    assert missing.label_names == empty.label_names == ()
    assert missing.child_stages == empty.child_stages == ()
    assert missing.metadata_snapshot == empty.metadata_snapshot == ()
    assert not _issue(_client()).labels.loaded
    assert not _issue(_client()).metadata.loaded


def _raw(stdout: bytes) -> RawCommandResult:
    return RawCommandResult(
        argv=(),
        exit_code=0,
        stdout=stdout,
        stderr=b"",
        duration=datetime.timedelta(),
    )


def _direct_result(
    resource: IssueResource,
    operation: Literal["list", "list_flat", "list_thread", "list_recent", "add", "reply", "runs"],
) -> object:
    if operation == "list":
        return resource.comments.list("iss_1")
    if operation == "list_flat":
        return resource.comments.list_flat(CommentListFlatRequest(issue_id="iss_1"))
    if operation == "list_thread":
        return resource.comments.list_thread(
            CommentListThreadRequest(issue_id="iss_1", thread_id="th_1", limit=10)
        )
    if operation == "list_recent":
        return resource.comments.list_recent(CommentListRecentRequest(issue_id="iss_1"))
    if operation == "add":
        return resource.comments.add("iss_1", "comment")
    if operation == "reply":
        return resource.comments.reply("iss_1", "th_1", "reply")
    return resource.runs("iss_1")


def _bound_item(result: object) -> Comment | CommentThread | TaskRun:
    if isinstance(result, tuple):
        return result[0]
    if isinstance(result, Page):
        return result.items[0]
    return cast("Comment | CommentThread | TaskRun", result)


@pytest.mark.parametrize("case", DIRECT_BOUND_CASES, ids=lambda case: case.name)
def test_direct_issue_activity_operations_bind_origin_and_context(case: DirectBoundCase) -> None:
    transport = MagicMock()
    transport.run_bytes.return_value = _raw(case.stdout)
    transport.run_text.return_value = MagicMock(text=case.stdout.decode(), stderr="")
    resource = IssueResource(transport, ClientConfig())
    client = _client()
    resource._set_client(client)

    result = _direct_result(resource, case.operation)
    item = _bound_item(result)

    assert isinstance(item, case.expected_type)
    assert item._client is client
    assert isinstance(item.to_data(), case.expected_data_type)
    assert item.to_data() is item.to_data()
    assert client.mock_calls == []
    if case.operation in {"list_flat", "list_thread", "list_recent"}:
        transport.run_text.assert_called_once_with(case.expected_argv)
        transport.run_bytes.assert_not_called()
    else:
        transport.run_bytes.assert_called_once_with(case.expected_argv, stdin=None, timeout=None)
        transport.run_text.assert_not_called()
    if case.second_hop == "comments":
        client.issues.comments.list_thread.return_value = Page(
            items=(CommentRecord(id="c2", body="reply"),), next_cursor=None
        )
        assert [comment.id for comment in cast("CommentThread", item).comments.all()] == ["c2"]
        request = client.issues.comments.list_thread.call_args.args[0]
        assert (request.issue_id, request.thread_id) == ("iss_1", "th_1")
    if case.second_hop == "messages":
        client.issues.run_messages.return_value = (
            RunMessage(id="m1", run_id="run_1", role="assistant", content="ok"),
        )
        assert [message.id for message in cast("TaskRun", item).messages.all()] == ["m1"]
        client.issues.run_messages.assert_called_once_with("run_1", issue_id="iss_1")


@pytest.mark.parametrize(
    ("method", "stdout", "expected"),
    [
        ("metadata", b'{"priority":"high","count":2}', {"priority": "high", "count": 2}),
        (
            "pull_requests",
            b'{"pull_requests":[{"url":"https://example.test/pr/1"}]}',
            (LinkedPullRequest(url="https://example.test/pr/1"),),
        ),
    ],
)
def test_issue_aggregate_and_mapping_adapters(method: str, stdout: bytes, expected: object) -> None:
    transport = MagicMock()
    transport.run_bytes.return_value = _raw(stdout)
    resource = IssueResource(transport, ClientConfig())

    result = resource.metadata.list("i1") if method == "metadata" else resource.pull_requests("i1")

    assert result == expected


@pytest.mark.parametrize(
    ("method", "stdout"),
    [("pull_requests", b"[]"), ("children", b"[]"), ("metadata", b"[]")],
)
def test_issue_legacy_list_shapes_are_rejected(method: str, stdout: bytes) -> None:
    transport = MagicMock()
    transport.run_bytes.return_value = _raw(stdout)
    resource = IssueResource(transport, ClientConfig())

    with pytest.raises(OutputShapeError):
        if method == "metadata":
            resource.metadata.list("i1")
        elif method == "children":
            resource.children("i1")
        else:
            resource.pull_requests("i1")


def test_run_messages_uses_task_id_and_optional_issue_flag() -> None:
    transport = MagicMock()
    transport.run_bytes.return_value = _raw(b"[]")
    resource = IssueResource(transport, ClientConfig())

    resource.run_messages("run_1", issue_id="issue_1")

    transport.run_bytes.assert_called_once_with(
        (
            "issue",
            "run-messages",
            "run_1",
            "--issue",
            "issue_1",
            "--output",
            "json",
        ),
        stdin=None,
        timeout=None,
    )
    transport.run_text.assert_not_called()


@pytest.mark.parametrize("case", ADDRESSING_CASES, ids=lambda case: case.name)
def test_issue_addressing_commands_are_exact(case: IssueAddressingCase) -> None:
    transport = MagicMock()
    getattr(transport, case.transport_method).return_value = ""
    resource = IssueResource(transport, ClientConfig())

    getattr(resource, case.method)(*case.args)

    selected = getattr(transport, case.transport_method)
    selected.assert_called_once_with(case.expected_argv)
    other_method = "run_bytes" if case.transport_method == "run_text" else "run_text"
    getattr(transport, other_method).assert_not_called()
