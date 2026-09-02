from __future__ import annotations

import datetime
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    _issue_from_wire,
    _IssueWire,
    _task_run_from_wire,
    _TaskRunWire,
)
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.entities.agents import Agent
from multica_py.entities.comments import Comment, CommentThread
from multica_py.entities.issues import Issue, TaskRun
from multica_py.entities.projects import Project
from multica_py.entities.squads import Squad
from multica_py.entities.workspaces import Workspace, WorkspaceMember
from multica_py.enums import IssueStatus
from multica_py.exceptions import OutputShapeError, RelationPaginationError
from multica_py.models.common import Page
from multica_py.models.issue_activity import (
    CommentCursor,
    RunMessage,
)
from multica_py.models.issues import (
    IssueChildrenResult,
    IssueChildStageGroup,
    IssueListFilter,
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
    RelationMetadata,
    _RelationLoad,
)
from multica_py.resources._base import BaseResource
from multica_py.resources.issues import IssueResource

_ACTIVITY_FIXTURE = json.loads(
    (Path(__file__).parents[2] / "fixtures/provenance/issue_activity_v0432.json").read_text()
)


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
    second_hop: Literal["none", "comments", "messages"]


@dataclass(frozen=True)
class IssueOriginCase:
    name: str
    origin: Literal[
        "get",
        "list",
        "search",
        "workspace",
        "workspace-member",
        "project",
        "agent",
        "squad",
    ]


@dataclass(frozen=True)
class IssueChildrenEnvelopeCase:
    name: str
    stdout: bytes
    expected_children: tuple[str, ...]
    expected_unstaged: tuple[str, ...]
    total: int
    child_stages: tuple[IssueChildStageGroup, ...]
    limit: int | None
    offset: int | None
    has_more: bool
    next_cursor: str | None


ISSUE_CHILDREN_ENVELOPE_CASES = (
    IssueChildrenEnvelopeCase(
        "empty",
        b"{}",
        (),
        (),
        0,
        (),
        None,
        None,
        False,
        None,
    ),
    IssueChildrenEnvelopeCase(
        "children only",
        b'{"children":[{"id":"child-1","title":"Child","status":"todo"}],"total":1}',
        ("child-1",),
        (),
        1,
        (),
        None,
        None,
        False,
        None,
    ),
    IssueChildrenEnvelopeCase(
        "unstaged only",
        b'{"unstaged":[{"id":"unstaged-1","title":"Unstaged","status":"done"}],"total":1}',
        (),
        ("unstaged-1",),
        1,
        (),
        None,
        None,
        False,
        None,
    ),
    IssueChildrenEnvelopeCase(
        "mixed and paginated",
        b'{"children":[{"id":"child-1","title":"Child","status":"todo"}],'
        b'"unstaged":[{"id":"unstaged-1","title":"Unstaged","status":"done"}],'
        b'"total":3,"child_stages":[{"name":"todo","count":2}],'
        b'"limit":25,"offset":10,"has_more":true,"next_cursor":"cursor-2"}',
        ("child-1",),
        ("unstaged-1",),
        3,
        (IssueChildStageGroup(name="todo", count=2),),
        25,
        10,
        True,
        "cursor-2",
    ),
)


ISSUE_ORIGIN_CASES = (
    IssueOriginCase("issue get", "get"),
    IssueOriginCase("issue list", "list"),
    IssueOriginCase("issue search", "search"),
    IssueOriginCase("workspace relation", "workspace"),
    IssueOriginCase("workspace member relation", "workspace-member"),
    IssueOriginCase("project relation", "project"),
    IssueOriginCase("agent relation", "agent"),
    IssueOriginCase("squad relation", "squad"),
)


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
        "none",
    ),
    DirectBoundCase(
        "flat list binds comments",
        "list_flat",
        b'[{"id":"c1","content":"comment"}]',
        ("issue", "comment", "list", "iss_1", "--output", "json"),
        Comment,
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
        "none",
    ),
    DirectBoundCase(
        "recent list binds comment threads",
        "list_recent",
        b'[{"id":"th_1","comments":[]}]',
        ("issue", "comment", "list", "iss_1", "--recent", "10", "--output", "json"),
        CommentThread,
        "comments",
    ),
    DirectBoundCase(
        "add binds comment",
        "add",
        b'{"id":"c1","content":"comment"}',
        ("issue", "comment", "add", "iss_1", "--content", "comment", "--output", "json"),
        Comment,
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
        "none",
    ),
    DirectBoundCase(
        "runs bind task runs",
        "runs",
        b'[{"id":"run_1","status":"done"}]',
        ("issue", "runs", "iss_1", "--output", "json"),
        TaskRun,
        "messages",
    ),
)


def _issue(client: MulticaClient | None = None) -> Issue:
    return Issue(
        id="iss_1",
        title="Issue",
        status=IssueStatus.todo,
        label_names=("bug",),
        child_stages=(IssueChildStageGroup(name="todo", count=1),),
        metadata_snapshot=(IssueMetadataItem(key="priority", value="high"),),
        _client=client,
    )


@pytest.mark.parametrize("case", ISSUE_ORIGIN_CASES, ids=lambda case: case.name)
def test_issue_origins_bind_actionable_items_to_the_origin_client(case: IssueOriginCase) -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    issue_wire = b'{"id":"i1","title":"Issue","status":"todo"}'
    transport.run_bytes.side_effect = lambda argv, **_kwargs: RawCommandResult(
        argv=argv,
        exit_code=0,
        stdout=(
            b'{"issues":[{"id":"i1","title":"Issue","status":"todo"}],'
            b'"has_more":false,"limit":50,"offset":0,"total":1}'
            if argv[:2] in {("issue", "list"), ("issue", "search")}
            else b'[{"id":"membership-1","name":"Member"}]'
            if argv[:3] == ("workspace", "member", "list")
            else b'{"id":"ws1","name":"Workspace"}'
            if argv[:2] == ("workspace", "get")
            else b'{"id":"p1","title":"Project","status":"planned"}'
            if argv[:2] == ("project", "get")
            else b'{"id":"a1","name":"Agent"}'
            if argv[:2] == ("agent", "get")
            else b'{"id":"sq1","name":"Squad"}'
            if argv[:2] == ("squad", "get")
            else issue_wire
        ),
        stderr=b"",
        duration=datetime.timedelta(),
    )
    client = MulticaClient()
    client._transport = transport
    for resource in (
        client.issues,
        client.projects,
        client.workspaces,
        client.agents,
        client.squads,
    ):
        resource._transport = transport

    expected_client = client
    if case.origin == "get":
        item = client.issues.get("i1")
    elif case.origin == "list":
        item = client.issues.list().items[0]
    elif case.origin == "search":
        item = client.issues.search("needle").items[0]
    elif case.origin == "workspace":
        workspace = client.workspaces.get("ws1")
        original_with_workspace = client.with_workspace
        scoped_clients: list[MulticaClient] = []

        def scoped(workspace_id: str) -> MulticaClient:
            scoped_client = original_with_workspace(workspace_id)
            scoped_client.issues._transport = transport
            scoped_clients.append(scoped_client)
            return scoped_client

        client.with_workspace = MagicMock(side_effect=scoped)  # type: ignore[method-assign]
        item = workspace.issues.all()[0]
        assert scoped_clients
        expected_client = scoped_clients[0]
    elif case.origin == "workspace-member":
        item = client.workspaces.members("ws1").items[0].issues.all()[0]
    elif case.origin == "project":
        item = client.projects.get("p1").issues.all()[0]
    elif case.origin == "agent":
        item = client.agents.get("a1").issues.all()[0]
    else:
        item = client.squads.get("sq1").issues.all()[0]

    assert isinstance(item, Issue)
    assert item._client is expected_client
    refresh = item.refresh_command()
    assign = item.assign_command("member-1")
    assert refresh.commands == ("multica issue get i1 --output json",)
    assert assign.commands == ("multica issue assign i1 --to-id member-1 --output json",)
    issue_get_calls = sum(
        call.args[0][:2] == ("issue", "get") for call in transport.run_bytes.call_args_list
    )
    collection_calls = sum(
        call.args[0][:2] in {("issue", "list"), ("issue", "search")}
        for call in transport.run_bytes.call_args_list
    )
    assert issue_get_calls == (1 if case.origin == "get" else 0)
    assert collection_calls == (0 if case.origin == "get" else 1)


def _client() -> MagicMock:
    client = MagicMock()
    command_resource = BaseResource(MagicMock(), ClientConfig())

    def empty_command(loader: Callable[[], object]) -> Command[object]:
        return command_resource._plan(steps=(), finalize=lambda _results: loader())

    client.issues.comments.list_flat.return_value = Page(items=())
    client.issues.comments.list_recent.return_value = Page(items=(), next_cursor=None)
    client.issues.comments.list_thread.return_value = Page(items=(), next_cursor=None)
    client.issues.labels.list.return_value = ()
    client.issues.subscribers.list.return_value = ()
    client.issues.metadata.list.return_value = {}
    client.issues.pull_requests.return_value = ()
    client.issues.children.return_value = IssueChildrenResult()
    client.issues.runs.return_value = ()
    client.issues.comments.list_flat_command = lambda **kwargs: empty_command(
        lambda: client.issues.comments.list_flat(**kwargs)
    )
    client.issues.comments.list_recent_command = lambda **kwargs: empty_command(
        lambda: client.issues.comments.list_recent(**kwargs)
    )
    client.issues.comments.list_thread_command = lambda **kwargs: empty_command(
        lambda: client.issues.comments.list_thread(**kwargs)
    )
    client.issues.labels.list_command = lambda issue_id: empty_command(
        lambda: client.issues.labels.list(issue_id)
    )
    client.issues.subscribers.list_command = lambda issue_id: empty_command(
        lambda: client.issues.subscribers.list(issue_id)
    )
    client.issues.metadata.list_command = lambda issue_id: empty_command(
        lambda: client.issues.metadata.list(issue_id)
    )
    client.issues.pull_requests_command = lambda issue_id: empty_command(
        lambda: client.issues.pull_requests(issue_id)
    )
    client.issues.children_command = lambda issue_id: empty_command(
        lambda: client.issues.children(issue_id)
    )

    def cursor_command(loader: Callable[[], object], kind: str) -> Command[object]:
        return command_resource._plan(
            steps=(
                _Step(
                    ("issue", "comment", "list", kind, "--output", "json"),
                    "run_text",
                    decode=lambda _stdout, _command: loader(),
                ),
            ),
            finalize=lambda results: results[0],
        )

    client.issues._comments_relation_command = lambda issue_id: empty_command(
        lambda: tuple(client.issues.comments.list_flat(issue_id=issue_id).items)
    )
    client.issues.comments._thread_page_command = lambda **request: cursor_command(
        lambda: CursorPage(
            items=client.issues.comments.list_thread(**request).items,
            next_cursor=None,
        ),
        "thread",
    )
    client.issues._recent_comment_threads_relation_command = lambda issue_id, *, limit, cursor: (
        cursor_command(
            lambda: CursorPage(
                items=tuple(
                    msgspec.structs.replace(item, issue_id=issue_id, _client=client)
                    for item in client.issues.comments.list_recent(
                        issue_id=issue_id, limit=limit, cursor=cursor
                    ).items
                ),
                next_cursor=None,
            ),
            "recent",
        )
    )
    client.issues._children_relation_command = lambda issue_id: empty_command(
        lambda: _RelationLoad(
            items=tuple(
                item._with_client(client) for item in client.issues.children(issue_id).children
            ),
            metadata=RelationMetadata(
                total=client.issues.children(issue_id).total,
                child_stages=client.issues.children(issue_id).child_stages,
                unstaged=tuple(
                    item._with_client(client) for item in client.issues.children(issue_id).unstaged
                ),
            ),
        )
    )

    def runs_command(issue_id):
        def loader():
            return tuple(run._with_client(client) for run in client.issues.runs(issue_id))

        return empty_command(loader)

    client.issues.runs_command = runs_command
    client.issues._runs_relation_command = runs_command
    client.issues.run_messages_command = lambda run_id, *, issue_id=None, since=0, options=None: (
        empty_command(lambda: client.issues.run_messages(run_id, issue_id=issue_id, since=since))
    )
    client.issues._run_messages_relation_command = (
        lambda run_id, *, issue_id=None, since=0, options=None: empty_command(
            lambda: client.issues.run_messages(run_id, issue_id=issue_id, since=since)
        )
    )
    client.issues._add_comment_command = lambda issue_id, body, *, invalidate, options: (
        client.issues.comments.add_command(issue_id, body, options=options)._map(
            lambda result: (invalidate(), result)[1]
        )
    )
    client.issues.comments.add_command = lambda issue_id, body, *, options=None: empty_command(
        lambda: client.issues.comments.add(issue_id, body)
    )
    client.issues.comments.reply_command = lambda issue_id, thread_id, body, *, options=None: (
        empty_command(lambda: client.issues.comments.reply(issue_id, thread_id, body))
    )
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
    second_child = Issue(id="child-2", title="Child 2", status=IssueStatus.todo)
    client.issues.children.return_value = IssueChildrenResult(
        items=(child, second_child),
        total=2,
        child_stages=(IssueChildStageGroup(name="done", count=1),),
        unstaged=(child,),
    )
    entity = _issue(client)

    result = entity.children.all()

    assert [item.id for item in result] == ["child", "child-2"]
    assert all(isinstance(item, Issue) for item in result)
    assert entity.children.metadata.total == 2
    assert entity.children.metadata.child_stages == (IssueChildStageGroup(name="done", count=1),)
    assert [item.id for item in entity.children.metadata.unstaged] == ["child"]
    client.issues.get.assert_not_called()


def test_issue_comments_and_query_views_invalidate_after_add() -> None:
    client = _client()
    client.issues.comments.list_flat.side_effect = [
        Page(items=(Comment(id="c1", body="one"),)),
        Page(items=(Comment(id="c2", body="two"),)),
    ]
    client.issues.comments.list_recent.return_value = Page(
        items=(CommentThread(id="th_1"),), next_cursor=None
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
        items=(CommentThread(id="th_1"),), next_cursor=None
    )
    bound_thread = entity.recent_comment_threads().all()[0]
    client.issues.comments.list_thread.return_value = Page(
        items=(Comment(id="c1", body="reply"),), next_cursor=None
    )

    assert isinstance(bound_thread.comments, CursorLazyCollection)
    assert [comment.id for comment in bound_thread.comments.all()] == ["c1"]
    client.issues.comments.list_thread.assert_called_once()
    request = client.issues.comments.list_thread.call_args.kwargs
    assert request["issue_id"] == "iss_1"
    assert request["thread_id"] == "th_1"


def test_task_run_messages_preserve_issue_and_task_ids() -> None:
    client = _client()
    client.issues.runs.return_value = (TaskRun(id="run_1", status="done", issue_id="iss_1"),)
    client.issues.run_messages.return_value = (
        RunMessage(task_id="run_1", seq=1, type="text", issue_id="iss_1", content="ok"),
    )
    entity = _issue(client)

    run = entity.runs.all()[0]
    assert [message.seq for message in run.messages.all()] == [1]
    client.issues.run_messages.assert_called_once_with("run_1", issue_id="iss_1", since=0)


def test_issue_runs_relation_preserves_current_fixture_context() -> None:
    client = _client()
    wire = decode_json(json.dumps(_ACTIVITY_FIXTURE["task_run"]).encode(), _TaskRunWire)
    client.issues.runs.return_value = (_task_run_from_wire(wire, issue_id="issue-1"),)
    entity = _issue(client)

    run = entity.runs.all()[0]

    assert run._client is client
    assert run.issue_id == "issue-1"
    assert run.agent_id == "agent-1"
    assert run.runtime_id == "runtime-1"
    assert run.workspace_id == "workspace-1"
    assert run.dispatched_at == datetime.datetime(2026, 8, 21, 9, tzinfo=datetime.UTC)
    assert run.started_at == datetime.datetime(2026, 8, 21, 9, 0, 1, tzinfo=datetime.UTC)
    assert run.completed_at == datetime.datetime(2026, 8, 21, 9, 5, tzinfo=datetime.UTC)
    assert run.created_at == datetime.datetime(2026, 8, 21, 8, 59, 59, tzinfo=datetime.UTC)
    assert run.work_dir == "/tmp/multica/workspace-1/task-1/workdir"
    assert run.relative_work_dir == "workspace-1/task-1/workdir"
    assert run.durable_work_dir == "/tmp/project"
    assert run.relative_durable_work_dir == "project"
    assert run.branch_name == "fix/issue-81"
    assert run.result == {"summary": "done", "files": ("src/example.py",)}
    assert run.error is None
    assert run.failure_reason == ""


def test_cursor_query_passes_complete_pair() -> None:
    client = _client()
    entity = _issue(client)
    cursor = CommentCursor(before="before", before_id="before-id")
    entity.recent_comment_threads(limit=5, cursor=cursor).page(cursor=cursor)

    request = client.issues.comments.list_recent.call_args.kwargs
    assert request["limit"] == 5
    assert request["cursor"] == cursor


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
    with pytest.raises(RelationPaginationError, match="page_limit_exceeded"):
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
    with pytest.raises(RelationPaginationError, match="page_limit_exceeded"):
        relation.all()

    assert calls == 2
    assert relation.loaded is False


@pytest.mark.parametrize(
    ("kind", "reason"), (("offset", "item_limit_exceeded"), ("cursor", "item_limit_exceeded"))
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


def test_offset_pagination_rejects_empty_progress_page() -> None:
    relation: OffsetLazyCollection[Issue] = OffsetLazyCollection(
        lambda *, limit, offset: OffsetPage((), 1, limit or 1, offset, True)
    )

    with pytest.raises(RelationPaginationError, match="empty_page"):
        relation.all()

    assert relation.loaded is False


def test_issue_wire_missing_and_empty_fields_do_not_seed_relations() -> None:
    missing = _issue_from_wire(decode_json(b'{"id":"i1","title":"t","status":"todo"}', _IssueWire))
    empty = _issue_from_wire(
        decode_json(
            b'{"id":"i1","title":"t","status":"todo","labels":[],"children":[],"metadata":{}}',
            _IssueWire,
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


def test_issue_offset_page_command_binds_rows_to_origin_client() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.return_value = _raw(
        b'{"issues":[{"id":"i1","title":"Issue","status":"todo"}],'
        b'"has_more":false,"limit":50,"offset":0,"total":1}'
    )
    resource = IssueResource(transport, ClientConfig())
    client = MagicMock()
    resource._set_client(client)

    result = resource._offset_page_command(IssueListFilter(limit=50, offset=0)).run()

    assert len(result.items) == 1
    assert isinstance(result.items[0], Issue)
    assert result.items[0]._client is client
    client.issues.get.assert_not_called()


@pytest.mark.parametrize("case", ISSUE_CHILDREN_ENVELOPE_CASES, ids=lambda case: case.name)
def test_issue_children_finalizer_binds_every_envelope_item_without_extra_get(
    case: IssueChildrenEnvelopeCase,
) -> None:
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.return_value = _raw(case.stdout)
    resource = IssueResource(transport, ClientConfig())
    client = MagicMock()
    resource._set_client(client)

    result = resource.children_command("iss_1").run()

    assert tuple(item.id for item in result.items) == case.expected_children
    assert tuple(item.id for item in result.children) == case.expected_children
    assert tuple(item.id for item in result.unstaged) == case.expected_unstaged
    assert all(item._client is client for item in (*result.items, *result.unstaged))
    assert result.total == case.total
    assert result.child_stages == case.child_stages
    assert result.limit == case.limit
    assert result.offset == case.offset
    assert result.has_more is case.has_more
    assert result.next_cursor == case.next_cursor
    transport.run_bytes.assert_called_once_with(
        ("issue", "children", "iss_1", "--output", "json"),
        stdin=None,
        timeout=None,
    )
    client.issues.get.assert_not_called()


def test_issue_children_eager_uses_bound_envelope_without_hydration() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.return_value = _raw(
        b'{"children":[{"id":"child-1","title":"Child","status":"todo"}],'
        b'"unstaged":[{"id":"unstaged-1","title":"Unstaged","status":"done"}],'
        b'"total":2}'
    )
    resource = IssueResource(transport, ClientConfig())
    client = MulticaClient()
    client._transport = transport
    client.issues._transport = transport
    resource._set_client(client)

    result = resource.children("iss_1")

    assert result.children[0]._client is client
    assert result.unstaged[0]._client is client
    assert result.children[0].refresh_command().commands == (
        "multica issue get child-1 --output json",
    )
    transport.run_bytes.assert_called_once_with(
        ("issue", "children", "iss_1", "--output", "json"),
        stdin=None,
        timeout=None,
    )


def test_issue_children_relation_command_preserves_scope_cache_and_refresh() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.return_value = _raw(
        b'{"children":[{"id":"child-1","title":"Child","status":"todo"}],'
        b'"unstaged":[{"id":"unstaged-1","title":"Unstaged","status":"done"}],'
        b'"total":2,"child_stages":[{"name":"todo","count":1}],'
        b'"limit":10,"offset":0,"has_more":false}'
    )
    client = MulticaClient()
    client._transport = transport
    client.issues._transport = transport
    entity = _issue(client)

    relation = entity.children
    command = relation.all_command()
    assert command.commands == ("multica issue children iss_1 --output json",)
    assert transport.run_bytes.call_count == 0

    loaded = relation.all()
    assert tuple(item.id for item in loaded) == ("child-1",)
    assert relation.metadata.total == 2
    assert relation.metadata.child_stages == (IssueChildStageGroup(name="todo", count=1),)
    assert tuple(item.id for item in relation.metadata.unstaged) == ("unstaged-1",)
    assert loaded[0]._client is client
    assert relation.metadata.unstaged[0]._client is client
    assert loaded[0].refresh_command().commands == ("multica issue get child-1 --output json",)
    assert transport.run_bytes.call_count == 1

    assert relation.all() == loaded
    assert transport.run_bytes.call_count == 1
    relation.refresh_command().run()
    assert transport.run_bytes.call_count == 2
    assert all(
        call.args[0][:2] == ("issue", "children") for call in transport.run_bytes.call_args_list
    )


def _direct_result(
    resource: IssueResource,
    operation: Literal["list", "list_flat", "list_thread", "list_recent", "add", "reply", "runs"],
) -> object:
    if operation == "list":
        return resource.comments.list_command("iss_1").run()
    if operation == "list_flat":
        return resource.comments.list_flat_command(issue_id="iss_1").run()
    if operation == "list_thread":
        return resource.comments.list_thread_command(
            issue_id="iss_1", thread_id="th_1", limit=10
        ).run()
    if operation == "list_recent":
        return resource.comments.list_recent_command(issue_id="iss_1").run()
    if operation == "add":
        return resource.comments.add_command("iss_1", "comment").run()
    if operation == "reply":
        return resource.comments.reply_command("iss_1", "th_1", "reply").run()
    return resource.runs_command("iss_1").run()


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
    assert client.mock_calls == []
    if case.operation in {"list_flat", "list_thread", "list_recent"}:
        transport.run_text.assert_called_once_with(case.expected_argv)
        transport.run_bytes.assert_not_called()
    else:
        transport.run_bytes.assert_called_once_with(case.expected_argv, stdin=None, timeout=None)
        transport.run_text.assert_not_called()
    if case.second_hop == "comments":
        client.issues.comments.list_thread.return_value = Page(
            items=(Comment(id="c2", body="reply"),), next_cursor=None
        )
        assert [comment.id for comment in cast("CommentThread", item).comments.all()] == ["c2"]
        request = client.issues.comments.list_thread.call_args.kwargs
        assert (request["issue_id"], request["thread_id"]) == ("iss_1", "th_1")
    if case.second_hop == "messages":
        client.issues.run_messages.return_value = (
            RunMessage(task_id="run_1", seq=1, type="text", issue_id="iss_1", content="ok"),
        )
        assert [message.seq for message in cast("TaskRun", item).messages.all()] == [1]
        client.issues.run_messages.assert_called_once_with("run_1", issue_id="iss_1", since=0)


@pytest.mark.parametrize(
    ("method", "stdout", "expected"),
    [
        ("metadata", b'{"priority":"high","count":2}', {"priority": "high", "count": 2}),
        (
            "pull_requests",
            b'{"pull_requests":[{"url":"https://example.test/pr/1"}]}',
            Page(
                items=(LinkedPullRequest(url="https://example.test/pr/1"),),
                total=1,
            ),
        ),
    ],
)
def test_issue_aggregate_and_mapping_adapters(method: str, stdout: bytes, expected: object) -> None:
    transport = MagicMock()
    transport.run_bytes.return_value = _raw(stdout)
    resource = IssueResource(transport, ClientConfig())

    result = (
        resource.metadata.list_command("i1").run()
        if method == "metadata"
        else resource.pull_requests_command("i1").run()
    )

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
            resource.metadata.list_command("i1").run()
        elif method == "children":
            resource.children_command("i1").run()
        else:
            resource.pull_requests_command("i1").run()


def test_run_messages_uses_task_id_and_optional_issue_flag() -> None:
    transport = MagicMock()
    transport.run_bytes.return_value = _raw(b"[]")
    resource = IssueResource(transport, ClientConfig())

    resource.run_messages_command("run_1", issue_id="issue_1").run()

    transport.run_bytes.assert_called_once_with(
        (
            "issue",
            "run-messages",
            "run_1",
            "--issue",
            "issue_1",
            "--since",
            "0",
            "--output",
            "json",
        ),
        stdin=None,
        timeout=None,
    )
    transport.run_text.assert_not_called()


@pytest.mark.parametrize(
    "value",
    [-1, True, False, "0", 2_147_483_648, 3.5, None],
    ids=["negative", "bool-true", "bool-false", "string", "overflow", "float", "none"],
)
def test_run_messages_rejects_invalid_since_before_io(value: object) -> None:
    transport = MagicMock()
    resource = IssueResource(transport, ClientConfig())

    with pytest.raises((TypeError, ValueError)):
        resource.run_messages_command("run_1", issue_id="issue_1", since=value)  # type: ignore[arg-type]

    transport.run_bytes.assert_not_called()


@pytest.mark.parametrize("case", ADDRESSING_CASES, ids=lambda case: case.name)
def test_issue_addressing_commands_are_exact(case: IssueAddressingCase) -> None:
    transport = MagicMock()
    getattr(transport, case.transport_method).return_value = ""
    resource = IssueResource(transport, ClientConfig())

    getattr(resource, f"{case.method}_command")(*case.args).run()

    selected = getattr(transport, case.transport_method)
    selected.assert_called_once_with(case.expected_argv)
    other_method = "run_bytes" if case.transport_method == "run_text" else "run_text"
    getattr(transport, other_method).assert_not_called()
