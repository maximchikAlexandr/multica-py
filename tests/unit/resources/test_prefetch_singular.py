from __future__ import annotations

import datetime
import threading
from collections.abc import Callable, Iterable, Mapping
from concurrent.futures import Future
from dataclasses import dataclass
from typing import cast
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.entities.issues import Issue
from multica_py.enums import CompatibilityPolicy, IssueStatus
from multica_py.exceptions import MissingRelationContextError
from multica_py.execution import LocalExecutor
from multica_py.models.relations import LazyCollection, LazyMapping, LazyRef
from tests.unit.resources._factories import bound_entity_factory, issue_factory


def test_prefetch_coalesces_equal_scopes_and_rebinds_independent_targets() -> None:
    make_issue = issue_factory
    make_target = bound_entity_factory
    client = MulticaClient(ClientConfig())
    derived = client.with_options()
    calls = MagicMock()
    target = make_target(client, title="Target")
    calls.side_effect = lambda _issue_id: client.issues._plan(
        steps=(), finalize=lambda _results: target
    )
    client.issues.get_command = calls  # type: ignore[method-assign]

    first = make_issue(client, "source-1")
    second = make_issue(derived, "source-2")
    first_ref = first.parent
    second_ref = second.parent

    try:
        client.prefetch((first, second), lambda issue: issue.parent, max_parallel=2)

        assert calls.call_count == 1
        first_target = first_ref.value
        second_target = second_ref.value
        assert first_target is not None
        assert second_target is not None
        assert first_target is not second_target
        assert first_target is not target
        assert second_target is not target
        assert first_target._client is client
        assert second_target._client is derived
        first_nested = first_target.parent
        second_nested = second_target.parent
        assert first_nested is not second_nested
    finally:
        derived.close()
        client.close()


def test_prefetch_deduplicates_repeated_singular_destination_handle() -> None:
    make_issue = issue_factory
    make_target = bound_entity_factory
    client = MulticaClient(ClientConfig())
    calls = MagicMock()
    target = make_target(client, title="Target")
    calls.return_value = client.issues._plan(steps=(), finalize=lambda _results: target)
    client.issues.get_command = calls  # type: ignore[method-assign]
    source = make_issue(client, "source-1")
    reference = source.parent
    publish = MagicMock(wraps=reference._prefetch_publish)
    reference._prefetch_publish = publish  # type: ignore[method-assign]

    try:
        client.prefetch((source, source), lambda _issue: reference, max_parallel=1)

        calls.assert_called_once_with("parent-1")
        publish.assert_called_once()
    finally:
        client.close()


def _run_secondary_load_race() -> None:
    root = MulticaClient(ClientConfig())
    secondary = root.with_options()
    first = issue_factory(root, "first", parent_id="shared")
    second = issue_factory(secondary, "second", parent_id="shared")
    secondary_started = threading.Event()
    release_secondary = threading.Event()
    old_target = cast("Issue", bound_entity_factory(root, Issue, "shared", title="old"))
    new_target = cast("Issue", bound_entity_factory(secondary, Issue, "shared", title="new"))

    setattr(
        root.issues,
        "get_command",
        MagicMock(return_value=root.issues._plan(steps=(), finalize=lambda _results: old_target)),
    )

    def secondary_command(_issue_id: str) -> object:
        def finalize(_results: tuple[object, ...]) -> Issue:
            secondary_started.set()
            assert release_secondary.wait(timeout=2)
            return new_target

        return secondary.issues._plan(steps=(), finalize=finalize)

    setattr(secondary.issues, "get_command", MagicMock(side_effect=secondary_command))
    loading = threading.Thread(target=second.parent.get)
    loading.start()
    assert secondary_started.wait(timeout=2)

    try:
        root.prefetch((first, second), lambda issue: issue.parent, max_parallel=1)
        assert first.parent.value is not old_target
        first_value = first.parent.value
        assert first_value is not None
        assert first_value.title == old_target.title
        assert second.parent.loaded is False
    finally:
        release_secondary.set()
        loading.join(timeout=2)
        secondary.close()
        root.close()

    assert not loading.is_alive()
    assert second.parent.value is new_target


def _run_secondary_refresh_race() -> None:
    root = MulticaClient(ClientConfig())
    secondary = root.with_options()
    first = issue_factory(root, "first", parent_id="shared")
    second = issue_factory(secondary, "second", parent_id="shared")
    old_target = cast("Issue", bound_entity_factory(secondary, Issue, "shared", title="old"))
    new_target = cast("Issue", bound_entity_factory(secondary, Issue, "shared", title="new"))
    refresh_started = threading.Event()
    release_refresh = threading.Event()
    calls = 0

    def secondary_command(_issue_id: str) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            return secondary.issues._plan(steps=(), finalize=lambda _results: old_target)

        def finalize(_results: tuple[object, ...]) -> Issue:
            refresh_started.set()
            assert release_refresh.wait(timeout=2)
            return new_target

        return secondary.issues._plan(steps=(), finalize=finalize)

    setattr(secondary.issues, "get_command", MagicMock(side_effect=secondary_command))
    setattr(
        root.issues,
        "get_command",
        MagicMock(
            return_value=root.issues._plan(
                steps=(),
                finalize=lambda _results: cast(
                    "Issue", bound_entity_factory(root, Issue, "shared")
                ),
            )
        ),
    )
    assert second.parent.get() is old_target
    second.parent.invalidate()
    first_selected = threading.Event()
    continue_selection = threading.Event()

    def selector(issue: Issue) -> LazyRef[Issue | None]:
        if issue is first:
            first_selected.set()
            assert continue_selection.wait(timeout=2)
        return issue.parent

    prefetching = threading.Thread(
        target=lambda: root.prefetch((first, second), selector, max_parallel=1)
    )
    prefetching.start()
    assert first_selected.wait(timeout=2)
    refreshing = threading.Thread(target=second.parent.refresh)
    refreshing.start()
    assert refresh_started.wait(timeout=2)

    try:
        continue_selection.set()
        prefetching.join(timeout=2)
        assert first.parent.loaded
        assert second.parent.loaded is False
    finally:
        release_refresh.set()
        refreshing.join(timeout=2)
        secondary.close()
        root.close()

    assert not prefetching.is_alive()
    assert not refreshing.is_alive()
    assert second.parent.value is new_target


def _run_invalidation_race() -> None:
    root = MulticaClient(ClientConfig())
    secondary = root.with_options()
    first = issue_factory(root, "first", parent_id="shared")
    second = issue_factory(secondary, "second", parent_id="shared")
    primary_started = threading.Event()
    release_primary = threading.Event()
    invalidation_done = threading.Event()
    target = cast("Issue", bound_entity_factory(root, Issue, "shared"))

    def primary_command(_issue_id: str) -> object:
        def finalize(_results: tuple[object, ...]) -> Issue:
            primary_started.set()
            assert release_primary.wait(timeout=2)
            return target

        return root.issues._plan(steps=(), finalize=finalize)

    setattr(root.issues, "get_command", MagicMock(side_effect=primary_command))
    secondary_get_command = MagicMock()
    setattr(secondary.issues, "get_command", secondary_get_command)
    prefetching = threading.Thread(
        target=lambda: root.prefetch((first, second), lambda issue: issue.parent, max_parallel=1)
    )
    prefetching.start()
    assert primary_started.wait(timeout=2)

    def invalidate() -> None:
        second.parent.invalidate()
        invalidation_done.set()

    invalidating = threading.Thread(target=invalidate)
    invalidating.start()
    assert invalidation_done.wait(timeout=0.05) is False
    release_primary.set()

    prefetching.join(timeout=2)
    invalidating.join(timeout=2)
    try:
        assert not prefetching.is_alive()
        assert not invalidating.is_alive()
        assert first.parent.loaded
        assert second.parent.loaded is False
        secondary_get_command.assert_not_called()
    finally:
        secondary.close()
        root.close()


@dataclass(frozen=True)
class PrefetchRaceCase:
    name: str
    run: Callable[[], None]


PREFETCH_RACE_CASES = (
    PrefetchRaceCase("secondary-get", _run_secondary_load_race),
    PrefetchRaceCase("secondary-refresh", _run_secondary_refresh_race),
    PrefetchRaceCase("invalidation", _run_invalidation_race),
)


@pytest.mark.parametrize("case", PREFETCH_RACE_CASES, ids=lambda case: case.name)
def test_prefetch_race_matrix_preserves_newer_destination_state(case: PrefetchRaceCase) -> None:
    case.run()


def test_prefetch_runs_equal_targets_in_different_profiles_separately() -> None:
    client = MulticaClient(ClientConfig())
    other = client.with_profile("other")
    first_calls = MagicMock()
    other_calls = MagicMock()
    first_calls.side_effect = lambda _issue_id: client.issues._plan(
        steps=(), finalize=lambda _results: bound_entity_factory(client, title="first")
    )
    other_calls.side_effect = lambda _issue_id: other.issues._plan(
        steps=(), finalize=lambda _results: bound_entity_factory(other, title="other")
    )
    client.issues.get_command = first_calls  # type: ignore[method-assign]
    other.issues.get_command = other_calls  # type: ignore[method-assign]
    first = issue_factory(client, "source-1")
    second = issue_factory(other, "source-2")

    try:
        client.prefetch((first, second), lambda issue: issue.parent, max_parallel=2)

        assert first_calls.call_count == 1
        assert other_calls.call_count == 1
        assert first.parent.value is not second.parent.value
    finally:
        other.close()
        client.close()


def test_prefetch_skips_explicit_null_singular_absence() -> None:
    client = MulticaClient(ClientConfig())
    calls = MagicMock()
    client.issues.get_command = calls  # type: ignore[method-assign]
    issue = issue_factory(client, "source-1", parent_id=None)

    try:
        reference = issue.parent
        assert reference.loaded
        client.prefetch((issue,), lambda value: value.parent)
        assert reference.value is None
        calls.assert_not_called()
    finally:
        client.close()


def test_singular_scope_preserves_environment_order_and_ignores_display_fields() -> None:
    base = MulticaClient(
        ClientConfig(
            environment=(("X", "b"), ("X", "a")),
            app_url="https://app.example",
            workspace_slug="base",
        )
    )
    reversed_environment = MulticaClient(
        ClientConfig(
            environment=(("X", "a"), ("X", "b")),
            app_url="https://other.example",
            workspace_slug="other",
        ),
        executor=base._executor,
        _semaphore=base._semaphore,
    )
    display_variant = MulticaClient(
        ClientConfig(
            environment=(("X", "b"), ("X", "a")),
            app_url="https://other.example",
            workspace_slug="other",
        ),
        executor=base._executor,
        _semaphore=base._semaphore,
    )

    try:
        base_key = base._singular_scope_key("Issue", "issue-1")
        assert base_key != reversed_environment._singular_scope_key("Issue", "issue-1")
        assert base_key == display_variant._singular_scope_key("Issue", "issue-1")
    finally:
        display_variant.close()
        reversed_environment.close()
        base.close()


@dataclass(frozen=True)
class ScopeComponentCase:
    name: str
    field: str | None
    value: object | None
    separate_executor: bool


SCOPE_COMPONENT_CASES = (
    ScopeComponentCase("workspace", "workspace_id", "workspace-2", False),
    ScopeComponentCase("profile", "profile", "profile-2", False),
    ScopeComponentCase("server", "server_url", "https://server.example", False),
    ScopeComponentCase("executable", "executable", "/opt/multica", False),
    ScopeComponentCase("cwd", "cwd", "/tmp/multica", False),
    ScopeComponentCase("environment", "environment", (("X", "b"), ("X", "a")), False),
    ScopeComponentCase("timeout", "timeout", datetime.timedelta(seconds=12), False),
    ScopeComponentCase("debug", "debug", True, False),
    ScopeComponentCase("encoding", "encoding", "utf-16", False),
    ScopeComponentCase("compatibility", "compatibility", CompatibilityPolicy.strict, False),
    ScopeComponentCase("min-cli", "min_cli_version", "0.4.28", False),
    ScopeComponentCase("max-cli", "max_cli_version", "0.4.29", False),
    ScopeComponentCase("executor", None, None, True),
)


def test_prefetch_separates_every_non_semaphore_scope_component() -> None:
    base_config = ClientConfig(environment=(("X", "a"), ("X", "b")))
    root = MulticaClient(base_config)
    clients: list[MulticaClient] = [root]
    sources = [issue_factory(root, "source-root")]
    calls: list[MagicMock] = []

    for case in SCOPE_COMPONENT_CASES:
        config = (
            base_config
            if case.field is None
            else msgspec.structs.replace(base_config, **{case.field: case.value})
        )
        executor = LocalExecutor() if case.separate_executor else root._executor
        client = MulticaClient(config, executor=executor, _semaphore=root._semaphore)
        clients.append(client)
        sources.append(issue_factory(client, f"source-{case.name}"))
        calls_for_client = MagicMock()
        target = bound_entity_factory(client, title=case.name)
        calls_for_client.side_effect = lambda _issue_id, target=target, client=client: (
            client.issues._plan(steps=(), finalize=lambda _results, target=target: target)
        )
        client.issues.get_command = calls_for_client  # type: ignore[method-assign]
        calls.append(calls_for_client)

    root_calls = MagicMock()
    root_target = bound_entity_factory(root, title="root")
    root_calls.side_effect = lambda _issue_id: root.issues._plan(
        steps=(), finalize=lambda _results: root_target
    )
    root.issues.get_command = root_calls  # type: ignore[method-assign]
    calls.insert(0, root_calls)

    try:
        root.prefetch(tuple(sources), lambda issue: issue.parent, max_parallel=len(sources))
        assert [call.call_count for call in calls] == [1] * len(calls)
    finally:
        for client in reversed(clients[1:]):
            client.close()
        root.close()


def test_prefetch_rejects_foreign_semaphore_before_singular_io() -> None:
    root = MulticaClient(ClientConfig())
    derived = root.with_profile("derived")
    foreign = MulticaClient(ClientConfig())
    first = issue_factory(root, "first")
    second = issue_factory(derived, "second")
    third = issue_factory(foreign, "third")
    selected = 0

    def selector(issue: Issue) -> LazyRef[Issue | None]:
        nonlocal selected
        selected += 1
        return issue.parent

    try:
        with pytest.raises(ValueError, match="origin"):
            root.prefetch((first, second, third), selector)
        assert selected == 2
        assert first.parent.loaded is False
        assert second.parent.loaded is False
    finally:
        foreign.close()
        derived.close()
        root.close()


def test_prefetch_rolls_back_reservations_before_late_validation_error() -> None:
    root = MulticaClient(ClientConfig())
    foreign = MulticaClient(ClientConfig())
    first = issue_factory(root, "first")
    second = issue_factory(foreign, "second")
    target = bound_entity_factory(root, title="retryable")
    setattr(
        root.issues,
        "get_command",
        MagicMock(return_value=root.issues._plan(steps=(), finalize=lambda _results: target)),
    )

    try:
        with pytest.raises(ValueError, match="origin"):
            root.prefetch((first, second), lambda issue: issue.parent)

        assert first.parent.loaded is False
        root.prefetch((first,), lambda issue: issue.parent)
        assert first.parent.value is not None
        assert first.parent.value.id == target.id
    finally:
        foreign.close()
        root.close()


class _CancelledPrefetchExecutor:
    def __init__(self, max_workers: int) -> None:
        del max_workers
        self._submitted = 0

    def __enter__(self) -> _CancelledPrefetchExecutor:
        return self

    def __exit__(self, *args: object) -> None:
        del args

    def submit(self, load: Callable[[], None]) -> Future[None]:
        del load
        future: Future[None] = Future()
        if self._submitted == 0:
            future.set_exception(RuntimeError("first job failed"))
        self._submitted += 1
        return future


def test_prefetch_rolls_back_reservations_for_cancelled_jobs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MulticaClient(ClientConfig())
    first = issue_factory(client, "first")
    second = issue_factory(client, "second")
    collection: LazyCollection[object] = LazyCollection(lambda: ())
    target = bound_entity_factory(client, title="retryable")
    setattr(
        client.issues,
        "get_command",
        MagicMock(return_value=client.issues._plan(steps=(), finalize=lambda _results: target)),
    )
    monkeypatch.setattr("multica_py.client.ThreadPoolExecutor", _CancelledPrefetchExecutor)
    monkeypatch.setattr(
        "multica_py.client.as_completed",
        lambda futures: iter((next(iter(futures)),)),
    )

    def selector(issue: Issue) -> LazyCollection[object] | LazyRef[object]:
        return collection if issue is first else issue.parent

    try:
        with pytest.raises(RuntimeError, match="first job failed"):
            client.prefetch((first, second), selector, max_parallel=1)

        assert second.parent.loaded is False
        monkeypatch.undo()
        client.prefetch((second,), lambda issue: issue.parent)
        assert second.parent.value is not None
        assert second.parent.value.id == target.id
    finally:
        client.close()


def test_prefetch_rejects_unknown_relation_before_reading_relation_state() -> None:
    client = MulticaClient(ClientConfig())
    issue = issue_factory(client, "source")

    class UnsupportedRelation:
        @property
        def loaded(self) -> bool:
            pytest.fail("unsupported relation state must not be read")

        def all(self) -> object:
            pytest.fail("unsupported relation must not be loaded")

    try:
        with pytest.raises(ValueError, match="LazyRef, LazyCollection, or LazyMapping"):
            client.prefetch((issue,), lambda _issue: UnsupportedRelation())
    finally:
        client.close()


@dataclass(frozen=True)
class RelationInventoryCase:
    name: str
    build: Callable[[Callable[[], object]], LazyCollection[object] | LazyMapping[str, str]]


def _build_collection(loader: Callable[[], object]) -> LazyCollection[object]:
    return LazyCollection(cast("Callable[[], Iterable[object]]", loader))


def _build_mapping(loader: Callable[[], object]) -> LazyMapping[str, str]:
    return LazyMapping(cast("Callable[[], Mapping[str, str]]", loader))


PREFETCH_RELATION_CASES = (
    RelationInventoryCase("Workspace.members", _build_collection),
    RelationInventoryCase("Workspace.agents", _build_collection),
    RelationInventoryCase("Workspace.skills", _build_collection),
    RelationInventoryCase("Workspace.projects", _build_collection),
    RelationInventoryCase("Workspace.issues", _build_collection),
    RelationInventoryCase("Workspace.labels", _build_collection),
    RelationInventoryCase("Workspace.autopilots", _build_collection),
    RelationInventoryCase("Workspace.repositories", _build_collection),
    RelationInventoryCase("Workspace.runtimes", _build_collection),
    RelationInventoryCase("Workspace.squads", _build_collection),
    RelationInventoryCase("Workspace.plugins", _build_collection),
    RelationInventoryCase("Workspace.properties", _build_collection),
    RelationInventoryCase("Workspace.mcp_servers", _build_collection),
    RelationInventoryCase("Agent.skills", _build_collection),
    RelationInventoryCase("Agent.tasks", _build_collection),
    RelationInventoryCase("Agent.issues", _build_collection),
    RelationInventoryCase("Agent.mcp_servers", _build_collection),
    RelationInventoryCase("Skill.files", _build_collection),
    RelationInventoryCase("Squad.members", _build_collection),
    RelationInventoryCase("Squad.issues", _build_collection),
    RelationInventoryCase("WorkspaceMember.issues", _build_collection),
    RelationInventoryCase("Project.resources", _build_collection),
    RelationInventoryCase("Project.issues", _build_collection),
    RelationInventoryCase("Issue.comments", _build_collection),
    RelationInventoryCase("Issue.recent_comment_threads", _build_collection),
    RelationInventoryCase("Issue.labels", _build_collection),
    RelationInventoryCase("Issue.subscribers", _build_collection),
    RelationInventoryCase("Issue.metadata", _build_mapping),
    RelationInventoryCase("Issue.pull_requests", _build_collection),
    RelationInventoryCase("Issue.children", _build_collection),
    RelationInventoryCase("Issue.runs", _build_collection),
    RelationInventoryCase("Issue.properties", _build_mapping),
    RelationInventoryCase("CommentThread.comments", _build_collection),
    RelationInventoryCase("TaskRun.messages", _build_collection),
    RelationInventoryCase("Autopilot.runs", _build_collection),
    RelationInventoryCase("Autopilot.triggers", _build_collection),
    RelationInventoryCase("Autopilot.subscribers", _build_collection),
    RelationInventoryCase("AutopilotRun.messages", _build_collection),
)


@pytest.mark.parametrize("case", PREFETCH_RELATION_CASES, ids=lambda case: case.name)
def test_prefetch_keeps_collection_and_mapping_identity_dedup_for_inventory_case(
    case: RelationInventoryCase,
) -> None:
    relation_name = case.name
    client = MulticaClient(ClientConfig())
    try:
        calls = {"count": 0}

        def relation_loader() -> object:
            calls["count"] += 1
            return {"value": relation_name}

        relation = case.build(relation_loader)
        entity = bound_entity_factory(client)
        client.prefetch((entity, entity), lambda _entity: relation, max_parallel=1)
        assert calls["count"] == 1
    finally:
        client.close()


@dataclass(frozen=True)
class FanoutShapeCase:
    name: str
    parent_id: str | None
    wire_presence: tuple[tuple[str, str], ...]


FANOUT_SHAPE_CASES = (
    FanoutShapeCase("omitted", None, ()),
    FanoutShapeCase("null", None, (("parent_id", "null"),)),
    FanoutShapeCase("value", "nested-1", (("parent_id", "value"),)),
)


@pytest.mark.parametrize("case", FANOUT_SHAPE_CASES, ids=lambda case: case.name)
def test_prefetch_fanout_preserves_nested_provenance_and_local_state(
    case: FanoutShapeCase,
) -> None:
    shape = case.name
    root = MulticaClient(ClientConfig())
    secondary = root.with_options()
    nested_target_calls: list[tuple[MulticaClient, str]] = []

    target = Issue(
        id="shared",
        title="Target",
        status=IssueStatus.todo,
        parent_id=case.parent_id,
        _wire_presence=case.wire_presence,
        _client=root,
    )

    def get_command(client: MulticaClient, issue_id: str) -> object:
        nested_target_calls.append((client, issue_id))
        if issue_id == "shared":
            value = target
        else:
            value = Issue(
                id=issue_id,
                title="Nested",
                status=IssueStatus.todo,
                _client=client,
            )

        def finalize(_results: tuple[object, ...], value: Issue = value) -> Issue:
            return value

        return client.issues._plan(steps=(), finalize=finalize)

    root_get = MagicMock(side_effect=lambda issue_id: get_command(root, issue_id))
    secondary_get = MagicMock(side_effect=lambda issue_id: get_command(secondary, issue_id))
    root.issues.get_command = root_get  # type: ignore[method-assign]
    secondary.issues.get_command = secondary_get  # type: ignore[method-assign]
    first = issue_factory(root, "first", parent_id="shared")
    second = issue_factory(secondary, "second", parent_id="shared")

    try:
        root.prefetch((first, second), lambda issue: issue.parent, max_parallel=2)
        first_target = first.parent.value
        second_target = second.parent.value
        assert first_target is not None
        assert second_target is not None
        assert first_target is not second_target
        assert first_target._client is root
        assert second_target._client is secondary
        assert first_target._wire_presence == second_target._wire_presence == target._wire_presence
        first_nested = first_target.parent
        second_nested = second_target.parent
        assert first_nested is not second_nested

        if shape == "omitted":
            with pytest.raises(MissingRelationContextError):
                first_nested.get()
            with pytest.raises(MissingRelationContextError):
                second_nested.get()
            assert root_get.call_count == 1
            assert secondary_get.call_count == 0
        elif shape == "null":
            assert first_nested.loaded and second_nested.loaded
            assert first_nested.value is None and second_nested.value is None
            assert root_get.call_count == 1
            assert secondary_get.call_count == 0
        else:
            first_loaded = first_nested.get()
            second_loaded = second_nested.get()
            assert first_loaded is not None
            assert second_loaded is not None
            assert first_loaded._client is root
            assert second_loaded._client is secondary
            assert first_loaded is not second_loaded
            first_nested.invalidate()
            assert first_nested.loaded is False
            assert second_nested.loaded is True
            assert [(client, issue_id) for client, issue_id in nested_target_calls] == [
                (root, "shared"),
                (root, "nested-1"),
                (secondary, "nested-1"),
            ]
    finally:
        secondary.close()
        root.close()


def test_prefetch_distinguishes_target_type_collision() -> None:
    root = MulticaClient(ClientConfig())
    issue = issue_factory(root, "issue-source", parent_id="same-id")
    project_source = Issue(
        id="project-source",
        title="Source",
        status=IssueStatus.todo,
        project_id="same-id",
        _client=root,
    )
    issue_target = bound_entity_factory(root, title="Issue target")
    project_target = bound_entity_factory(root, title="Project target")
    issue_get = MagicMock(
        return_value=root.issues._plan(steps=(), finalize=lambda _results: issue_target)
    )
    project_get = MagicMock(
        return_value=root.projects._plan(steps=(), finalize=lambda _results: project_target)
    )
    root.issues.get_command = issue_get  # type: ignore[method-assign]
    root.projects.get_command = project_get  # type: ignore[method-assign]

    try:
        root.prefetch(
            (issue, project_source), lambda value: value.parent if value is issue else value.project
        )
        assert issue_get.call_count == 1
        assert project_get.call_count == 1
        assert id(issue.parent.value) != id(project_source.project.value)
    finally:
        root.close()


def test_prefetch_retries_a_failed_singular_generation() -> None:
    root = MulticaClient(ClientConfig())
    source = issue_factory(root, "source")
    calls: int = 0

    def command_for(_issue_id: str) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:

            def fail(_results: tuple[object, ...]) -> Issue:
                raise RuntimeError("transient")

            return root.issues._plan(steps=(), finalize=fail)
        return root.issues._plan(
            steps=(), finalize=lambda _results: bound_entity_factory(root, title="retry")
        )

    root.issues.get_command = MagicMock(side_effect=command_for)  # type: ignore[method-assign]
    try:
        with pytest.raises(RuntimeError, match="transient"):
            root.prefetch((source,), lambda value: value.parent)
        assert source.parent.loaded is False
        root.prefetch((source,), lambda value: value.parent)
        retry_value = source.parent.value
        assert retry_value is not None
        assert retry_value.title == "retry"
        assert calls == 2
    finally:
        root.close()


def test_prefetch_respects_max_parallel_for_distinct_singular_jobs() -> None:
    root = MulticaClient(ClientConfig())
    clients = [root, root.with_profile("one"), root.with_profile("two")]
    sources = [issue_factory(client, f"source-{index}") for index, client in enumerate(clients)]
    lock = threading.Lock()
    release = threading.Event()
    active = 0
    maximum = 0

    def command_for(client: MulticaClient, _issue_id: str) -> object:
        def finalize(_results: tuple[object, ...]) -> Issue:
            nonlocal active, maximum
            with lock:
                active += 1
                maximum = max(maximum, active)
                if active == 2:
                    release.set()
            assert release.wait(timeout=2)
            with lock:
                active -= 1
            return cast("Issue", bound_entity_factory(client, title="bounded"))

        return client.issues._plan(steps=(), finalize=finalize)

    for client in clients:
        client.issues.get_command = MagicMock(  # type: ignore[method-assign]
            side_effect=lambda issue_id, client=client: command_for(client, issue_id)
        )

    try:
        root.prefetch(tuple(sources), lambda value: value.parent, max_parallel=2)
        assert maximum == 2
    finally:
        for client in reversed(clients[1:]):
            client.close()
        root.close()
