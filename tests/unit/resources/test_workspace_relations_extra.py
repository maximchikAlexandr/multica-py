from __future__ import annotations

import datetime
import threading
import types
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol, cast
from unittest.mock import MagicMock

import pytest

from multica_py._internal.commands import Command, _Step
from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.entities.projects import Project
from multica_py.entities.workspaces import Workspace, WorkspaceMember
from multica_py.enums import IssueStatus
from multica_py.exceptions import RelationPaginationError
from multica_py.models.issue_activity import CommentCursor
from multica_py.models.relations import (
    CursorLazyCollection,
    CursorPage,
    LazyCollection,
    LazyMapping,
    OffsetLazyCollection,
    OffsetPage,
)
from multica_py.resources._base import BaseResource
from tests.unit.resources.workspace_cases import (
    make_workspace_clients,
    workspace_relation_method,
)


@dataclass(frozen=True)
class MissingRelationCommandLoaderCase:
    id: str
    invoke: Callable[[], object]


def _empty_offset_page(*, limit: int | None, offset: int) -> OffsetPage[str]:
    return OffsetPage((), 0, limit or 50, offset, False)


def _empty_cursor_page(*, cursor: CommentCursor | None) -> CursorPage[str]:
    return CursorPage(())


MISSING_RELATION_COMMAND_LOADER_CASES = (
    MissingRelationCommandLoaderCase(
        "collection-all",
        lambda: LazyCollection[str](lambda: ()).all_command(),
    ),
    MissingRelationCommandLoaderCase(
        "collection-refresh",
        lambda: LazyCollection[str](lambda: ()).refresh_command(),
    ),
    MissingRelationCommandLoaderCase(
        "offset-page",
        lambda: OffsetLazyCollection[str](_empty_offset_page).page_command(),
    ),
    MissingRelationCommandLoaderCase(
        "offset-all",
        lambda: OffsetLazyCollection[str](_empty_offset_page).all_command(),
    ),
    MissingRelationCommandLoaderCase(
        "cursor-page",
        lambda: CursorLazyCollection[str](_empty_cursor_page).page_command(),
    ),
    MissingRelationCommandLoaderCase(
        "cursor-all",
        lambda: CursorLazyCollection[str](_empty_cursor_page).all_command(),
    ),
    MissingRelationCommandLoaderCase(
        "mapping-all",
        lambda: LazyMapping[str, str](dict).all_command(),
    ),
    MissingRelationCommandLoaderCase(
        "mapping-refresh",
        lambda: LazyMapping[str, str](dict).refresh_command(),
    ),
)

# ============================================================================
# 3.4 - distinct wrappers: lazy object memoized per (entity, relation_name)
# ============================================================================


def test_workspace_repeated_property_access_returns_memoized_lazy() -> None:
    clients = make_workspace_clients()
    entity = Workspace(id="ws_1", name="Test WS", _client=clients.origin)
    r1 = entity.members
    r2 = entity.members
    assert r1 is r2
    assert isinstance(r1, LazyCollection)


@pytest.mark.parametrize(
    "case",
    MISSING_RELATION_COMMAND_LOADER_CASES,
    ids=lambda case: case.id,
)
def test_relation_command_requires_loader(case: MissingRelationCommandLoaderCase) -> None:
    with pytest.raises(RuntimeError, match="command loader"):
        case.invoke()


def test_generic_relation_command_plans_preview_pages_and_mapping_cache() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.side_effect = lambda argv, **_kwargs: RawCommandResult(
        argv=argv,
        exit_code=0,
        stdout=b"{}",
        stderr=b"",
        duration=datetime.timedelta(),
    )
    resource = BaseResource(transport, ClientConfig())

    offset_pages = iter(
        (
            OffsetPage(("one",), 2, 50, 0, True),
            OffsetPage(("two",), 2, 50, 1, False),
        )
    )

    def offset_command(limit: int | None, offset: int) -> Command[OffsetPage[str]]:
        return resource._plan(
            steps=(
                _Step(
                    ("items", "--limit", str(limit), "--offset", str(offset), "--output", "json"),
                    "run_bytes",
                    decode=lambda _stdout, _command: next(offset_pages),
                ),
            ),
            finalize=lambda results: cast("OffsetPage[str]", results[0]),
        )

    offset_relation = OffsetLazyCollection(
        lambda *, limit, offset: OffsetPage(("legacy",), 1, 50, offset, False),
        default_limit=50,
        page_command_loader=offset_command,
    )
    offset_command_plan = offset_relation.all_command()
    assert offset_command_plan.commands == (
        "multica items --limit 50 --offset 0 --output json",
        "multica items --limit 50 --offset '${page.next_offset}' --output json",
    )
    assert offset_command_plan.run() == ("one", "two")
    assert transport.run_bytes.call_args_list[1].args[0] == (
        "items",
        "--limit",
        "50",
        "--offset",
        "1",
        "--output",
        "json",
    )

    def direct_offset_command() -> Command[tuple[str, ...]]:
        return resource._plan(steps=(), finalize=lambda _results: ("direct",))

    direct_offset_relation: OffsetLazyCollection[str] = OffsetLazyCollection(
        _empty_offset_page,
        command_loader=direct_offset_command,
    )
    assert direct_offset_relation.all_command().run() == ("direct",)
    assert direct_offset_relation.refresh_command().run() == ("direct",)

    cursor_pages = iter(
        (
            CursorPage(("one",), CommentCursor(before="b2", before_id="i2")),
            CursorPage(("two",), None),
        )
    )

    def cursor_command(cursor: CommentCursor | None) -> Command[CursorPage[str]]:
        return resource._plan(
            steps=(
                _Step(
                    ("comments", "--output", "json")
                    if cursor is None
                    else (
                        "comments",
                        "--before",
                        cursor.before,
                        "--before-id",
                        cursor.before_id,
                        "--output",
                        "json",
                    ),
                    "run_bytes",
                    decode=lambda _stdout, _command: next(cursor_pages),
                ),
            ),
            finalize=lambda results: cast("CursorPage[str]", results[0]),
        )

    cursor_relation = CursorLazyCollection(
        lambda *, cursor: CursorPage(("legacy",), None),
        page_command_loader=cursor_command,
    )
    cursor_command_plan = cursor_relation.all_command()
    assert cursor_command_plan.commands == (
        "multica comments --output json",
        "multica comments --before '${page.next_cursor.before}' --before-id '${page.next_cursor.before_id}' --output json",
    )
    assert cursor_command_plan.run() == ("one", "two")
    assert transport.run_bytes.call_args_list[3].args[0] == (
        "comments",
        "--before",
        "b2",
        "--before-id",
        "i2",
        "--output",
        "json",
    )

    def build_mapping_command() -> Command[Mapping[str, str]]:
        return resource._plan(
            steps=(
                _Step(
                    ("mapping", "list", "--output", "json"),
                    "run_bytes",
                    decode=lambda _stdout, _command: {"key": "value"},
                ),
            ),
            finalize=lambda results: cast("Mapping[str, str]", results[0]),
        )

    mapping = LazyMapping(
        lambda: {"legacy": "unused"},
        command_loader=build_mapping_command,
    )
    mapping_command = mapping.all_command()
    assert mapping_command.commands == ("multica mapping list --output json",)
    assert mapping_command.run() == {"key": "value"}
    assert mapping["key"] == "value"
    assert transport.run_bytes.call_count == 5
    cache_hit = mapping.all_command()
    assert cache_hit.commands == ()
    assert cache_hit.run() == {"key": "value"}
    assert transport.run_bytes.call_count == 5
    refresh = mapping.refresh_command()
    assert refresh.commands == ("multica mapping list --output json",)
    assert refresh.run() == {"key": "value"}
    assert transport.run_bytes.call_count == 6


def test_relation_value_protocols_cover_empty_and_cached_paths() -> None:
    page = OffsetPage(items=("one",), total=1, limit=1, offset=0, has_more=False)
    assert page.next_offset is None

    values: LazyCollection[str] = LazyCollection(lambda: ("one",))
    assert "one" in values
    assert len(values) == 1

    mapping = LazyMapping(lambda: {"key": "value"})
    assert mapping.all() == {"key": "value"}
    assert mapping.all() == {"key": "value"}
    assert list(mapping) == ["key"]
    assert len(mapping) == 1
    mapping.invalidate()
    assert not mapping.loaded


@pytest.mark.parametrize("case", ("repeated-offset", "item-budget", "empty-page"))
def test_offset_command_guards_are_behavioral(
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    transport = MagicMock(spec=CliTransport)
    resource = BaseResource(transport, ClientConfig())
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    if case == "repeated-offset":
        pages = iter(
            (
                OffsetPage(("one",), 2, 1, 0, True),
                OffsetPage(("two",), 2, 1, 0, True),
                OffsetPage(("three",), 3, 1, 1, False),
            )
        )
    elif case == "item-budget":
        monkeypatch.setattr("multica_py.models.relations._MAX_RELATION_ITEMS", 1)
        pages = iter(
            (
                OffsetPage(("one",), 2, 1, 0, True),
                OffsetPage(("two",), 3, 1, 1, True),
                OffsetPage(("three",), 3, 1, 2, False),
            )
        )
    else:
        pages = iter(
            (
                OffsetPage(("one",), 2, 1, 0, True),
                OffsetPage((), 2, 1, 1, True),
            )
        )

    def page_command(limit: int | None, offset: int) -> Command[OffsetPage[str]]:
        return resource._plan(
            steps=(
                _Step(
                    (
                        "items",
                        "--limit",
                        str(limit),
                        "--offset",
                        str(offset),
                        "--output",
                        "json",
                    ),
                    "run_bytes",
                    decode=lambda _stdout, _command: next(pages),
                ),
            ),
            finalize=lambda results: cast("OffsetPage[str]", results[0]),
        )

    relation = OffsetLazyCollection(
        lambda *, limit, offset: OffsetPage((), 0, limit or 1, offset, False),
        default_limit=1,
        page_command_loader=page_command,
    )
    transport.run_bytes.side_effect = lambda argv, **_kwargs: RawCommandResult(
        argv=argv,
        exit_code=0,
        stdout=b"{}",
        stderr=b"",
        duration=datetime.timedelta(),
    )
    with pytest.raises(RelationPaginationError, match=r"repeated_offset|empty_page"):
        relation.all_command().run()


def test_offset_command_requires_offset_in_page_argv() -> None:
    resource = BaseResource(MagicMock(spec=CliTransport), ClientConfig())

    def page_command(_limit: int | None, _offset: int) -> Command[OffsetPage[str]]:
        return resource._plan(
            steps=(_Step(("items", "--output", "json"), "run_bytes"),),
            finalize=lambda results: cast("OffsetPage[str]", results[0]),
        )

    relation = OffsetLazyCollection(
        lambda *, limit, offset: OffsetPage((), 0, limit or 1, offset, False),
        page_command_loader=page_command,
    )
    with pytest.raises(RuntimeError, match="no --offset"):
        relation.all_command()


def test_offset_command_empty_plan_falls_back_to_loader() -> None:
    resource = BaseResource(MagicMock(spec=CliTransport), ClientConfig())

    def page_command(_limit: int | None, _offset: int) -> Command[OffsetPage[str]]:
        return resource._plan(
            steps=(),
            finalize=lambda _results: OffsetPage((), 0, 1, 0, False),
        )

    relation = OffsetLazyCollection(
        lambda *, limit, offset: OffsetPage(("loaded",), 1, limit or 1, offset, False),
        page_command_loader=page_command,
    )
    assert relation.all_command().run() == ("loaded",)


@pytest.mark.parametrize(
    "argv",
    (
        ("comments", "--output", "json"),
        ("comments", "--before", "old", "--before-id", "old-id", "--output", "json"),
    ),
)
def test_cursor_command_preview_and_refresh_cover_cursor_bindings(
    argv: tuple[str, ...],
) -> None:
    transport = MagicMock(spec=CliTransport)
    resource = BaseResource(transport, ClientConfig())
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    first = CursorPage(("one",), CommentCursor(before="next", before_id="next-id"))
    last = CursorPage(("two",), None)
    pages = iter((first, last, first, last))

    def page_command(_cursor: CommentCursor | None) -> Command[CursorPage[str]]:
        return resource._plan(
            steps=(_Step(argv, "run_bytes", decode=lambda _stdout, _command: next(pages)),),
            finalize=lambda results: cast("CursorPage[str]", results[0]),
        )

    transport.run_bytes.side_effect = lambda request, **_kwargs: RawCommandResult(
        argv=request,
        exit_code=0,
        stdout=b"{}",
        stderr=b"",
        duration=datetime.timedelta(),
    )
    relation = CursorLazyCollection(
        lambda *, cursor: CursorPage((), None),
        initial_cursor=(
            CommentCursor(before="old", before_id="old-id") if "--before" in argv else None
        ),
        page_command_loader=page_command,
    )
    assert relation.all() == ("one", "two")
    assert relation.refresh() == ("one", "two")
    assert relation.all_command().commands == ()


def test_cursor_command_preserves_mixed_cursor_pair_insertion_and_replacement() -> None:
    transport = MagicMock(spec=CliTransport)
    resource = BaseResource(transport, ClientConfig())
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    pages = iter(
        (
            CursorPage(("one",), CommentCursor(before="next", before_id="next-id")),
            CursorPage(("two",), None),
        )
    )

    def page_command(_cursor: CommentCursor | None) -> Command[CursorPage[str]]:
        return resource._plan(
            steps=(
                _Step(
                    ("comments", "--before", "old", "--output", "json"),
                    "run_bytes",
                    decode=lambda _stdout, _command: next(pages),
                ),
            ),
            finalize=lambda results: cast("CursorPage[str]", results[0]),
        )

    transport.run_bytes.side_effect = lambda request, **_kwargs: RawCommandResult(
        argv=request,
        exit_code=0,
        stdout=b"{}",
        stderr=b"",
        duration=datetime.timedelta(),
    )
    relation = CursorLazyCollection(
        lambda *, cursor: CursorPage((), None), page_command_loader=page_command
    )
    command = relation.all_command()

    assert command.commands == (
        "multica comments --before old --output json",
        "multica comments --before '${page.next_cursor.before}' --before-id '${page.next_cursor.before_id}' --output json",
    )
    assert command.run() == ("one", "two")
    assert transport.run_bytes.call_args_list[1].args[0] == (
        "comments",
        "--before",
        "next",
        "--before-id",
        "next-id",
        "--output",
        "json",
    )


@pytest.mark.parametrize("case", ("page-budget", "item-budget", "empty-page", "repeated-cursor"))
def test_cursor_command_guards_are_behavioral(
    monkeypatch: pytest.MonkeyPatch,
    case: str,
) -> None:
    transport = MagicMock(spec=CliTransport)
    resource = BaseResource(transport, ClientConfig())
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    next_cursor = CommentCursor(before="next", before_id="next-id")
    if case == "page-budget":
        monkeypatch.setattr("multica_py.models.relations._MAX_RELATION_PAGES", 1)
        pages = iter(
            (
                CursorPage(("one",), next_cursor),
                CursorPage(("two",), next_cursor),
                CursorPage(("three",), None),
            )
        )
    elif case == "item-budget":
        monkeypatch.setattr("multica_py.models.relations._MAX_RELATION_ITEMS", 1)
        pages = iter(
            (
                CursorPage(("one",), next_cursor),
                CursorPage(("two",), next_cursor),
                CursorPage(("three",), None),
            )
        )
    elif case == "empty-page":
        pages = iter(
            (
                CursorPage(("one",), next_cursor),
                CursorPage((), next_cursor),
                CursorPage(("three",), None),
            )
        )
    else:
        pages = iter(
            (
                CursorPage(("one",), next_cursor),
                CursorPage(("two",), next_cursor),
                CursorPage(("three",), None),
            )
        )

    def page_command(_cursor: CommentCursor | None) -> Command[CursorPage[str]]:
        return resource._plan(
            steps=(
                _Step(
                    ("comments", "--output", "json"),
                    "run_bytes",
                    decode=lambda _stdout, _command: next(pages),
                ),
            ),
            finalize=lambda results: cast("CursorPage[str]", results[0]),
        )

    transport.run_bytes.side_effect = lambda request, **_kwargs: RawCommandResult(
        argv=request,
        exit_code=0,
        stdout=b"{}",
        stderr=b"",
        duration=datetime.timedelta(),
    )
    relation = CursorLazyCollection(
        lambda *, cursor: CursorPage((), None), page_command_loader=page_command
    )
    with pytest.raises(RelationPaginationError, match=r"repeated_cursor|empty_page"):
        relation.all_command().run()


def test_cursor_direct_loader_rejects_empty_progress_page() -> None:
    next_cursor = CommentCursor(before="next", before_id="next-id")
    relation: CursorLazyCollection[str] = CursorLazyCollection(
        lambda *, cursor: CursorPage((), next_cursor)
    )
    with pytest.raises(RelationPaginationError, match="empty_page"):
        relation.all()


def test_mapping_command_runs_coalesce_and_retry_after_refresh_failure() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    started = threading.Event()
    release = threading.Event()
    calls = 0

    def run_bytes(argv: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
        nonlocal calls
        calls += 1
        if calls == 1:
            started.set()
            assert release.wait(timeout=2)
        if calls == 2:
            raise RuntimeError("refresh failed")
        return RawCommandResult(
            argv=argv,
            exit_code=0,
            stdout=b"{}",
            stderr=b"",
            duration=datetime.timedelta(),
        )

    transport.run_bytes.side_effect = run_bytes
    resource = BaseResource(transport, ClientConfig())

    def command_loader() -> Command[Mapping[str, str]]:
        return resource._plan(
            steps=(
                _Step(
                    ("mapping", "list", "--output", "json"),
                    "run_bytes",
                    decode=lambda _stdout, _command: {"value": "ok"},
                ),
            ),
            finalize=lambda results: cast("Mapping[str, str]", results[0]),
        )

    mapping = LazyMapping(lambda: {"legacy": "unused"}, command_loader=command_loader)
    commands = [mapping.all_command(), mapping.all_command()]
    results: list[Mapping[str, str]] = []
    threads = [
        threading.Thread(target=lambda command=command: results.append(command.run()))
        for command in commands
    ]
    for thread in threads:
        thread.start()
    assert started.wait(timeout=2)
    release.set()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()

    assert results == [{"value": "ok"}, {"value": "ok"}]
    assert calls == 1

    refresh = mapping.refresh_command()
    with pytest.raises(RuntimeError, match="refresh failed"):
        refresh.run()
    assert dict(mapping.all()) == {"value": "ok"}
    assert mapping.all_command().commands == ()
    assert mapping.refresh_command().run() == {"value": "ok"}
    assert calls == 3


def test_prefetch_routes_command_backed_mapping_through_all_command() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.side_effect = lambda argv, **_kwargs: RawCommandResult(
        argv=argv,
        exit_code=0,
        stdout=b"{}",
        stderr=b"",
        duration=datetime.timedelta(),
    )
    resource = BaseResource(transport, ClientConfig())

    def command_loader() -> Command[Mapping[str, str]]:
        return resource._plan(
            steps=(
                _Step(
                    ("mapping", "list", "--output", "json"),
                    "run_bytes",
                    decode=lambda _stdout, _command: {"value": "prefetched"},
                ),
            ),
            finalize=lambda results: cast("Mapping[str, str]", results[0]),
        )

    relation = LazyMapping(
        lambda: (_ for _ in ()).throw(AssertionError("legacy loader bypassed")),
        command_loader=command_loader,
    )
    client = MulticaClient(ClientConfig())
    entities = (
        types.SimpleNamespace(_client=client),
        types.SimpleNamespace(_client=client),
    )
    selected = iter((relation, relation))

    client.prefetch(entities, lambda _entity: next(selected), max_parallel=2)

    assert dict(relation.all()) == {"value": "prefetched"}
    assert transport.run_bytes.call_count == 1


def test_prefetch_runs_command_backed_relations_concurrently() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    started = {"one": threading.Event(), "two": threading.Event()}
    release = threading.Event()

    def run_bytes(argv: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
        key = argv[1]
        started[key].set()
        assert release.wait(timeout=2)
        return RawCommandResult(
            argv=argv,
            exit_code=0,
            stdout=b"{}",
            stderr=b"",
            duration=datetime.timedelta(),
        )

    transport.run_bytes.side_effect = run_bytes
    resource = BaseResource(transport, ClientConfig())

    def command_loader(key: str) -> Callable[[], Command[Mapping[str, str]]]:
        def build() -> Command[Mapping[str, str]]:
            return resource._plan(
                steps=(
                    _Step(
                        ("mapping", key, "--output", "json"),
                        "run_bytes",
                        decode=lambda _stdout, _command: {key: "ok"},
                    ),
                ),
                finalize=lambda results: cast("Mapping[str, str]", results[0]),
            )

        return build

    relations = (
        LazyMapping(dict, command_loader=command_loader("one")),
        LazyMapping(dict, command_loader=command_loader("two")),
    )
    client = MulticaClient(ClientConfig())
    entities = (
        types.SimpleNamespace(_client=client),
        types.SimpleNamespace(_client=client),
    )
    selected = iter(relations)
    errors: list[Exception] = []

    def prefetch() -> None:
        try:
            client.prefetch(entities, lambda _entity: next(selected), max_parallel=2)
        except Exception as error:
            errors.append(error)

    thread = threading.Thread(target=prefetch)
    thread.start()
    assert started["one"].wait(timeout=2)
    assert started["two"].wait(timeout=2)
    release.set()
    thread.join(timeout=2)
    assert not thread.is_alive()
    assert errors == []
    assert all(relation.loaded for relation in relations)
    assert transport.run_bytes.call_count == 2


def test_workspace_after_invalidate_reloads() -> None:
    state = {"calls": 0}

    def loader() -> list[WorkspaceMember]:
        state["calls"] += 1
        return [WorkspaceMember(id=f"m{state['calls']}", name="A")]

    lc: LazyCollection[WorkspaceMember] = LazyCollection(loader)
    r1 = lc.all()
    assert state["calls"] == 1
    assert len(r1) == 1 and r1[0].id == "m1"

    lc.invalidate()
    r2 = lc.all()
    assert state["calls"] == 2
    assert len(r2) == 1 and r2[0].id == "m2"
    assert r1[0].id != r2[0].id


@pytest.mark.parametrize(
    "relation_name",
    [
        "members",
        "agents",
        "skills",
        "projects",
        "labels",
        "repositories",
        "runtimes",
        "squads",
        "autopilots",
    ],
)
def test_workspace_lazy_memoized_per_entity(relation_name: str) -> None:
    clients = make_workspace_clients()
    entity = Workspace(id="ws_1", name="Test WS", _client=clients.origin)
    r1 = getattr(entity, relation_name)
    r2 = getattr(entity, relation_name)
    assert r1 is r2


def test_workspace_projects_loader_preserves_bound_items() -> None:
    from multica_py.enums import ProjectStatus

    _PS = ProjectStatus("planned")
    p1 = Project(id="p1", name="P1", description=None, status=_PS)
    p2 = Project(id="p1", name="P1", description=None, status=_PS)
    clients = make_workspace_clients(projects=(p1, p2))
    entity = Workspace(id="ws_1", name="Test WS", _client=clients.origin)
    r1 = entity.projects.all()
    call_count_after_first = clients.scoped.projects.list.call_count
    assert entity._projects is not None
    entity._projects.invalidate()
    r2 = entity.projects.all()
    call_count_after_second = clients.scoped.projects.list.call_count
    assert call_count_after_second == call_count_after_first + 1
    assert r1[0] is p1
    assert r2[0] is p1
    assert r1[0].id == r2[0].id


# ============================================================================
# 3.5 - shared-semaphore: with_workspace() view shares ProcessSemaphore
# ============================================================================


def test_with_workspace_shares_process_semaphore() -> None:
    parent = MulticaClient(ClientConfig())
    derived = parent.with_workspace("ws_1")
    assert parent._semaphore is derived._semaphore


def test_with_workspace_shares_semaphore_across_chained_views() -> None:
    parent = MulticaClient(ClientConfig())
    v1 = parent.with_workspace("ws_1")
    v2 = parent.with_profile("p1")
    v3 = v1.with_profile("p2")
    assert parent._semaphore is v1._semaphore
    assert parent._semaphore is v2._semaphore
    assert parent._semaphore is v3._semaphore


def test_each_view_keeps_independent_configuration() -> None:
    parent = MulticaClient(ClientConfig())
    derived = parent.with_workspace("ws_42").with_profile("dev")
    assert parent._semaphore is derived._semaphore
    assert parent._config.workspace_id is None
    assert derived._config.workspace_id == "ws_42"
    assert derived._config.profile == "dev"


# ============================================================================
# 3.5 - derived-view: relations bind to derived view's transport
# ============================================================================


def test_workspace_relations_use_derived_view_transport() -> None:
    parent = MulticaClient(ClientConfig())
    derived = parent.with_workspace("ws_42")
    # Derived view has its own transport but shares the semaphore.
    assert parent._transport is not derived._transport
    assert derived._config.workspace_id == "ws_42"


@pytest.mark.parametrize(
    "relation_name",
    [
        "members",
        "agents",
        "skills",
        "projects",
        "labels",
        "repositories",
        "runtimes",
        "squads",
        "autopilots",
    ],
)
def test_workspace_each_relation_uses_scoped_client(
    relation_name: str,
) -> None:
    clients = make_workspace_clients()
    entity = Workspace(id="ws_1", name="Test WS", _client=clients.origin)
    relation = getattr(entity, relation_name)
    relation.all()
    clients.origin.with_workspace.assert_called_once_with("ws_1")
    method = workspace_relation_method(clients.scoped, relation_name)
    assert method.call_count == 1


# ============================================================================
# 3.5 - blocking-refresh: refresh() blocks concurrent loads atomically
# ============================================================================


def test_workspace_refresh_blocks_concurrent_loads() -> None:
    state = {"calls": 0, "in_progress": 0, "max_concurrent": 0}
    lock = threading.Lock()
    refresh_started = threading.Event()
    release_refresh = threading.Event()

    def _slow_loader() -> tuple[WorkspaceMember, ...]:
        with lock:
            state["in_progress"] += 1
            state["max_concurrent"] = max(state["max_concurrent"], state["in_progress"])
        state["calls"] += 1
        if state["calls"] == 2:
            refresh_started.set()
            assert release_refresh.wait(timeout=2)
        with lock:
            state["in_progress"] -= 1
        return (WorkspaceMember(id=f"m{state['calls']}", name="A"),)

    lc: LazyCollection[WorkspaceMember] = LazyCollection(_slow_loader)
    initial = lc.all()
    assert state["calls"] == 1
    assert initial[0].id == "m1"

    results: list[tuple[WorkspaceMember, ...]] = []
    errors: list[Exception] = []

    def _refresh() -> None:
        try:
            results.append(lc.refresh())
        except Exception as e:
            errors.append(e)

    def _all() -> None:
        try:
            results.append(lc.all())
        except Exception as e:
            errors.append(e)

    t1 = threading.Thread(target=_refresh)
    t2 = threading.Thread(target=_all)
    t1.start()
    assert refresh_started.wait(timeout=2)
    t2.start()
    _wait_for_generation_waiter(lc, generation=2)
    release_refresh.set()
    t1.join(timeout=2)
    t2.join(timeout=2)
    assert not t1.is_alive()
    assert not t2.is_alive()
    assert not errors
    assert len(results) == 2
    assert state["max_concurrent"] <= 1


def test_workspace_refresh_failure_preserves_prior_value() -> None:
    """A failed refresh() keeps the previous successful value LOADED
    (per design.md: "failed refresh retains the old LOADED value")."""
    state = {"calls": 0}

    def _loader() -> tuple[WorkspaceMember, ...]:
        state["calls"] += 1
        if state["calls"] == 1:
            return (WorkspaceMember(id="m1", name="A"),)
        raise RuntimeError("boom")

    lc: LazyCollection[WorkspaceMember] = LazyCollection(_loader)
    initial = lc.all()
    assert initial == (WorkspaceMember(id="m1", name="A"),)
    with pytest.raises(RuntimeError):
        lc.refresh()
    assert lc.all() == (WorkspaceMember(id="m1", name="A"),)
    assert state["calls"] == 2


def test_workspace_invalidate_resets_to_unloaded() -> None:
    """invalidate() resets state to UNLOADED; next all() reloads."""
    state = {"calls": 0}

    def _loader() -> tuple[WorkspaceMember, ...]:
        state["calls"] += 1
        return (WorkspaceMember(id="m1", name="A"),)

    lc: LazyCollection[WorkspaceMember] = LazyCollection(_loader)
    lc.all()
    assert state["calls"] == 1
    lc.invalidate()
    assert not lc.loaded
    lc.all()
    assert state["calls"] == 2


def test_workspace_first_load_failure_is_retryable() -> None:
    """A failed first load returns state to UNLOADED (per design.md:
    "First-load failure returns to UNLOADED"); subsequent loads retry."""
    state = {"calls": 0}

    def _loader() -> tuple[WorkspaceMember, ...]:
        state["calls"] += 1
        if state["calls"] == 1:
            raise RuntimeError("first failed")
        return (WorkspaceMember(id="m1", name="A"),)

    lc: LazyCollection[WorkspaceMember] = LazyCollection(_loader)
    with pytest.raises(RuntimeError):
        lc.all()
    assert not lc.loaded
    result = lc.all()
    assert result == (WorkspaceMember(id="m1", name="A"),)
    assert state["calls"] == 2


@dataclass(frozen=True)
class _GenerationCase:
    name: str
    build: Callable[[Callable[[], tuple[str, ...]]], _Loadable]


class _Loadable(Protocol):
    @property
    def _generation_state(self) -> _GenerationStateView: ...

    def all(self) -> object: ...

    def refresh(self) -> object: ...

    def invalidate(self) -> None: ...


class _GenerationStateView(Protocol):
    @property
    def condition(self) -> threading.Condition: ...

    @property
    def waiters(self) -> Mapping[int, int]: ...

    @property
    def outcomes(self) -> Mapping[int, object]: ...


def _collection(load: Callable[[], tuple[str, ...]]) -> LazyCollection[str]:
    return LazyCollection(load)


def _wait_for_generation_waiter(relation: _Loadable, *, generation: int) -> None:
    state = relation._generation_state
    with state.condition:
        assert state.condition.wait_for(
            lambda: state.waiters.get(generation, 0) > 0,
            timeout=2,
        )


_GENERATION_CASES = (
    _GenerationCase("collection", _collection),
    _GenerationCase("mapping", lambda load: LazyMapping(lambda: {"value": load()[0]})),
    _GenerationCase(
        "offset",
        lambda load: OffsetLazyCollection(
            lambda *, limit, offset: OffsetPage(load(), 1, 1, 0, False)
        ),
    ),
    _GenerationCase(
        "cursor", lambda load: CursorLazyCollection(lambda *, cursor: CursorPage(load(), None))
    ),
)


@pytest.mark.parametrize("case", _GENERATION_CASES, ids=lambda case: case.name)
def test_generation_waiters_share_failure_then_later_retry(case: _GenerationCase) -> None:
    started = threading.Event()
    release = threading.Event()
    calls = 0
    error = RuntimeError("generation one")

    def loader() -> tuple[str, ...]:
        nonlocal calls
        calls += 1
        if calls == 1:
            started.set()
            release.wait(timeout=2)
            raise error
        return ("ok",)

    relation = case.build(loader)
    errors: list[Exception] = []
    threads = [threading.Thread(target=lambda: _capture(relation, errors)) for _ in range(2)]
    for thread in threads:
        thread.start()
    assert started.wait(timeout=2)
    release.set()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()
    assert len(errors) == 2
    assert {type(e) for e in errors} == {type(error)}
    assert {e.args for e in errors} == {error.args}
    assert len({id(e) for e in errors}) == 2
    assert relation.all()
    assert calls == 2


def _capture(relation: _Loadable, errors: list[Exception]) -> None:
    try:
        relation.all()
    except Exception as error:
        errors.append(error)


@pytest.mark.parametrize("case", _GENERATION_CASES, ids=lambda case: case.name)
def test_generation_waiters_coalesce_success(case: _GenerationCase) -> None:
    started = threading.Event()
    release = threading.Event()
    calls = 0

    def loader() -> tuple[str, ...]:
        nonlocal calls
        calls += 1
        started.set()
        release.wait(timeout=2)
        return ("loaded",)

    relation = case.build(loader)
    results: list[object] = []
    threads = [threading.Thread(target=lambda: results.append(relation.all())) for _ in range(2)]
    for thread in threads:
        thread.start()
    assert started.wait(timeout=2)
    release.set()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()
    assert calls == 1
    assert len(results) == 2
    assert results[0] == results[1]


@pytest.mark.parametrize("case", _GENERATION_CASES, ids=lambda case: case.name)
def test_generation_waiters_get_distinct_exception_instances(case: _GenerationCase) -> None:
    started = threading.Event()
    release = threading.Event()
    calls = 0
    error = RuntimeError("generation one")

    def loader() -> tuple[str, ...]:
        nonlocal calls
        calls += 1
        if calls == 1:
            started.set()
            release.wait(timeout=2)
            raise error
        return ("ok",)

    relation = case.build(loader)
    errors: list[Exception] = []
    threads = [threading.Thread(target=lambda: _capture(relation, errors)) for _ in range(3)]
    for thread in threads:
        thread.start()
    assert started.wait(timeout=2)
    release.set()
    for thread in threads:
        thread.join(timeout=2)
        assert not thread.is_alive()

    assert len(errors) == 3
    assert sum(e is error for e in errors) == 1
    assert all(type(e) is type(error) for e in errors)
    assert all(e.args == error.args for e in errors)
    clones = [e for e in errors if e is not error]
    assert len(clones) == 2
    assert len({id(e) for e in clones}) == 2
    assert all(e.__traceback__ is not None for e in errors)
    assert len({id(e.__traceback__) for e in clones}) == 2


@pytest.mark.parametrize("case", _GENERATION_CASES, ids=lambda case: case.name)
def test_generation_refresh_is_atomic(case: _GenerationCase) -> None:
    started = threading.Event()
    release = threading.Event()
    calls = 0

    def loader() -> tuple[str, ...]:
        nonlocal calls
        calls += 1
        if calls == 2:
            started.set()
            release.wait(timeout=2)
        return (f"value-{calls}",)

    relation = case.build(loader)
    before = relation.all()
    refreshed: list[object] = []
    observed: list[object] = []
    refresh_thread = threading.Thread(target=lambda: refreshed.append(relation.refresh()))
    reader_thread = threading.Thread(target=lambda: observed.append(relation.all()))
    refresh_thread.start()
    assert started.wait(timeout=2)
    reader_thread.start()
    release.set()
    refresh_thread.join(timeout=2)
    reader_thread.join(timeout=2)
    assert not refresh_thread.is_alive()
    assert not reader_thread.is_alive()
    assert calls == 2
    assert before != refreshed[0]
    assert observed == refreshed


@pytest.mark.parametrize("case", _GENERATION_CASES, ids=lambda case: case.name)
def test_generation_outcomes_survive_a_three_party_later_generation(
    case: _GenerationCase,
) -> None:
    first_started = threading.Event()
    release_first = threading.Event()
    retry_started = threading.Event()
    release_retry = threading.Event()
    first_error = RuntimeError("first generation")
    calls = 0

    def loader() -> tuple[str, ...]:
        nonlocal calls
        calls += 1
        if calls == 1:
            first_started.set()
            release_first.wait(timeout=2)
            raise first_error
        retry_started.set()
        release_retry.wait(timeout=2)
        return ("second",)

    relation = case.build(loader)
    owner_errors: list[Exception] = []
    waiter_errors: list[Exception] = []
    retry_values: list[object] = []
    owner = threading.Thread(target=lambda: _capture(relation, owner_errors))
    waiter = threading.Thread(target=lambda: _capture(relation, waiter_errors))
    owner.start()
    assert first_started.wait(timeout=2)
    waiter.start()
    _wait_for_generation_waiter(relation, generation=1)
    release_first.set()
    owner.join(timeout=2)
    assert not owner.is_alive()
    retry = threading.Thread(target=lambda: retry_values.append(relation.all()))
    retry.start()
    assert retry_started.wait(timeout=2)
    waiter.join(timeout=2)
    assert not waiter.is_alive()
    release_retry.set()
    retry.join(timeout=2)
    assert not retry.is_alive()

    assert len(owner_errors) == 1
    assert owner_errors[0] is first_error
    assert len(waiter_errors) == 1
    assert type(waiter_errors[0]) is type(first_error)
    assert waiter_errors[0].args == first_error.args
    assert waiter_errors[0] is not first_error
    assert retry_values
    assert calls == 2
    assert not relation._generation_state.outcomes


@pytest.mark.parametrize("case", _GENERATION_CASES, ids=lambda case: case.name)
def test_successful_generation_value_survives_invalidate_and_reload(
    case: _GenerationCase,
) -> None:
    first_started = threading.Event()
    release_first = threading.Event()
    second_started = threading.Event()
    release_second = threading.Event()
    calls = 0

    def loader() -> tuple[str, ...]:
        nonlocal calls
        calls += 1
        if calls == 1:
            first_started.set()
            release_first.wait(timeout=2)
            return ("first",)
        second_started.set()
        release_second.wait(timeout=2)
        return ("second",)

    relation = case.build(loader)
    owner_values: list[object] = []
    waiter_values: list[object] = []
    owner = threading.Thread(target=lambda: owner_values.append(relation.all()))
    waiter = threading.Thread(target=lambda: waiter_values.append(relation.all()))
    owner.start()
    assert first_started.wait(timeout=2)
    waiter.start()
    _wait_for_generation_waiter(relation, generation=1)
    release_first.set()
    owner.join(timeout=2)
    assert not owner.is_alive()
    relation.invalidate()
    reload = threading.Thread(target=lambda: owner_values.append(relation.all()))
    reload.start()
    assert second_started.wait(timeout=2)
    waiter.join(timeout=2)
    assert not waiter.is_alive()
    release_second.set()
    reload.join(timeout=2)
    assert not reload.is_alive()

    assert waiter_values == [owner_values[0]]
    assert calls == 2
    assert not relation._generation_state.outcomes
