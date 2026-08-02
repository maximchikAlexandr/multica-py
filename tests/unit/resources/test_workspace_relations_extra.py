from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol
from unittest.mock import MagicMock

import pytest

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus
from multica_py.models.issue_activity import CommentCursor
from multica_py.models.relations import (
    CursorLazyCollection,
    CursorPage,
    LazyCollection,
    LazyMapping,
    OffsetLazyCollection,
    OffsetPage,
)
from multica_py.models.workspaces import WorkspaceMember
from multica_py.resources.workspaces import WorkspaceEntity
from tests.unit.resources.workspace_cases import (
    make_workspace_clients,
    workspace_data,
    workspace_relation_method,
)

# ============================================================================
# 3.4 - distinct wrappers: lazy object memoized per (entity, relation_name)
# ============================================================================


def test_workspace_repeated_property_access_returns_memoized_lazy() -> None:
    clients = make_workspace_clients()
    entity = WorkspaceEntity(workspace_data(), client=clients.origin)
    r1 = entity.members
    r2 = entity.members
    assert r1 is r2
    assert isinstance(r1, LazyCollection)


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
    entity = WorkspaceEntity(workspace_data(), client=clients.origin)
    r1 = getattr(entity, relation_name)
    r2 = getattr(entity, relation_name)
    assert r1 is r2


def test_workspace_bound_project_wrappers_are_distinct() -> None:
    from multica_py.enums import ProjectStatus
    from multica_py.models.autopilots import AutopilotListPage
    from multica_py.models.labels import LabelData
    from multica_py.models.skills import Skill

    _PS = ProjectStatus("planned")
    p1 = MagicMock(id="p1", name="P1", description=None, status=_PS)
    p2 = MagicMock(id="p1", name="P1", description=None, status=_PS)
    clients = make_workspace_clients(projects=(p1, p2))
    entity = WorkspaceEntity(workspace_data(), client=clients.origin)
    r1 = entity.projects.all()
    call_count_after_first = clients.scoped.projects.list.call_count
    assert entity._projects is not None
    entity._projects.invalidate()
    r2 = entity.projects.all()
    call_count_after_second = clients.scoped.projects.list.call_count
    assert call_count_after_second == call_count_after_first + 1
    assert r1[0] is not r2[0]
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
    entity = WorkspaceEntity(workspace_data(), client=clients.origin)
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
    _condition: threading.Condition

    @property
    def _waiters(self) -> Mapping[int, int]: ...

    @property
    def _outcomes(self) -> Mapping[int, object]: ...

    def all(self) -> object: ...

    def refresh(self) -> object: ...

    def invalidate(self) -> None: ...


def _collection(load: Callable[[], tuple[str, ...]]) -> LazyCollection[str]:
    return LazyCollection(load)


def _wait_for_generation_waiter(relation: _Loadable, *, generation: int) -> None:
    with relation._condition:
        assert relation._condition.wait_for(
            lambda: relation._waiters.get(generation, 0) > 0,
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
    assert errors == [error, error]
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

    assert owner_errors == [first_error]
    assert waiter_errors == [first_error]
    assert retry_values
    assert calls == 2
    assert not relation._outcomes


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
    assert not relation._outcomes
