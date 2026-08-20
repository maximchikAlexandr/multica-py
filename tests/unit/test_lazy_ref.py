from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import TypeVar
from unittest.mock import MagicMock

import pytest

from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.exceptions import UnloadedReferenceError
from multica_py.models.relations import LazyRef, _GenerationState
from multica_py.resources._base import BaseResource

T = TypeVar("T")


def _assert_loaded(reference: LazyRef[object], expected: bool) -> None:
    assert reference.loaded is expected


@pytest.fixture
def command_resource() -> Iterator[BaseResource]:
    config = ClientConfig()
    transport = CliTransport(config)
    yield BaseResource(transport, config)
    transport.close()


def _command_loader(resource: BaseResource, loader: Callable[[], T]) -> Callable[[], Command[T]]:
    return lambda: resource._plan(steps=(), finalize=lambda _results: loader())


def test_generation_state_distinguishes_unloaded_from_initial_none() -> None:
    unloaded = _GenerationState[str | None](None)
    loaded_none = _GenerationState[str | None](None, initial=None)

    assert unloaded.loaded is False
    assert unloaded.value is None
    assert loaded_none.loaded is True
    assert loaded_none.value is None


def test_lazy_ref_initial_value_and_cached_get(command_resource: BaseResource) -> None:
    calls = 0

    def load() -> str:
        nonlocal calls
        calls += 1
        return "loaded"

    reference = LazyRef(
        load,
        command_loader=_command_loader(command_resource, load),
        initial="initial",
    )

    _assert_loaded(reference, True)
    assert reference.value == "initial"
    assert reference.get() == "initial"
    assert calls == 0

    reference.invalidate()
    _assert_loaded(reference, False)
    assert reference.get() == "loaded"
    assert reference.get() == "loaded"
    assert calls == 1


def test_lazy_ref_value_raises_before_first_load(command_resource: BaseResource) -> None:
    def load() -> str:
        return "loaded"

    reference = LazyRef(
        load,
        command_loader=_command_loader(command_resource, load),
        entity_type="Issue",
        entity_id="i1",
    )

    with pytest.raises(UnloadedReferenceError, match=r"Issue\.reference\.value"):
        _ = reference.value


def test_lazy_ref_failed_first_load_is_retryable(command_resource: BaseResource) -> None:
    attempts = 0

    def load() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("temporary failure")
        return "loaded"

    reference = LazyRef(load, command_loader=_command_loader(command_resource, load))

    with pytest.raises(RuntimeError, match="temporary failure"):
        reference.get()
    _assert_loaded(reference, False)

    assert reference.get() == "loaded"
    _assert_loaded(reference, True)
    assert attempts == 2


def _run_concurrent(
    resource: BaseResource,
    loader: Callable[[], str],
    *,
    expected_loaded: bool,
) -> tuple[list[str], list[Exception]]:
    reference = LazyRef(loader, command_loader=_command_loader(resource, loader))
    results: list[str] = []
    errors: list[Exception] = []

    def call_get() -> None:
        try:
            results.append(reference.get())
        except Exception as error:
            errors.append(error)

    first = threading.Thread(target=call_get)
    second = threading.Thread(target=call_get)
    first.start()
    assert _LOAD_STARTED.wait(timeout=2)
    second.start()
    _LOAD_RELEASE.set()
    first.join(timeout=2)
    second.join(timeout=2)
    assert not first.is_alive()
    assert not second.is_alive()
    if expected_loaded:
        _assert_loaded(reference, True)
    else:
        _assert_loaded(reference, False)
        assert all(isinstance(error, RuntimeError) for error in errors)
    return results, errors


_LOAD_STARTED = threading.Event()
_LOAD_RELEASE = threading.Event()


@dataclass(frozen=True)
class ConcurrentCase:
    name: str
    error_message: str | None
    expected_loaded: bool
    expected_results: tuple[str, ...]
    expected_errors: tuple[str, ...]


_CONCURRENT_CASES = (
    ConcurrentCase(
        "success",
        None,
        True,
        ("loaded", "loaded"),
        (),
    ),
    ConcurrentCase(
        "failure",
        "shared failure",
        False,
        (),
        ("shared failure", "shared failure"),
    ),
)


@pytest.mark.parametrize("case", _CONCURRENT_CASES, ids=lambda case: case.name)
def test_lazy_ref_concurrent_is_coalesced(
    case: ConcurrentCase, command_resource: BaseResource
) -> None:
    calls = 0
    lock = threading.Lock()
    _LOAD_STARTED.clear()
    _LOAD_RELEASE.clear()

    def load() -> str:
        nonlocal calls
        with lock:
            calls += 1
        _LOAD_STARTED.set()
        assert _LOAD_RELEASE.wait(timeout=2)
        if case.error_message is not None:
            raise RuntimeError(case.error_message)
        return "loaded"

    results, errors = _run_concurrent(command_resource, load, expected_loaded=case.expected_loaded)

    assert calls == 1
    assert results == list(case.expected_results)
    assert [str(error) for error in errors] == list(case.expected_errors)


def test_lazy_ref_refresh_success_replaces_cached_target(command_resource: BaseResource) -> None:
    values = iter(("first", "second"))

    def load() -> str:
        return next(values)

    reference = LazyRef(load, command_loader=_command_loader(command_resource, load))

    assert reference.get() == "first"
    assert reference.refresh() == "second"
    _assert_loaded(reference, True)
    assert reference.value == "second"


def test_lazy_ref_failed_refresh_preserves_cached_target(command_resource: BaseResource) -> None:
    attempts = 0

    def load() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return "first"
        raise RuntimeError("refresh failed")

    reference = LazyRef(load, command_loader=_command_loader(command_resource, load))
    assert reference.get() == "first"

    with pytest.raises(RuntimeError, match="refresh failed"):
        reference.refresh()
    _assert_loaded(reference, True)
    assert reference.value == "first"
    assert reference.get() == "first"


def test_lazy_ref_invalidation_waits_for_active_generation(command_resource: BaseResource) -> None:
    load_started = threading.Event()
    load_release = threading.Event()
    invalidation_done = threading.Event()

    def load() -> str:
        load_started.set()
        assert load_release.wait(timeout=2)
        return "loaded"

    reference = LazyRef(load, command_loader=_command_loader(command_resource, load))
    loading = threading.Thread(target=reference.get)
    loading.start()
    assert load_started.wait(timeout=2)

    def invalidate() -> None:
        reference.invalidate()
        invalidation_done.set()

    invalidating = threading.Thread(target=invalidate)
    invalidating.start()
    assert invalidation_done.wait(timeout=0.05) is False

    load_release.set()
    loading.join(timeout=2)
    invalidating.join(timeout=2)
    assert not loading.is_alive()
    assert not invalidating.is_alive()
    assert invalidation_done.is_set()
    _assert_loaded(reference, False)
    with pytest.raises(UnloadedReferenceError):
        _ = reference.value


def test_lazy_ref_requires_command_loader() -> None:
    with pytest.raises(TypeError, match="missing 1 required keyword-only argument"):
        LazyRef(lambda: "loaded")  # type: ignore[call-arg]

    with pytest.raises(TypeError, match="command_loader is required"):
        LazyRef(lambda: "loaded", command_loader=None)  # type: ignore[arg-type]


def test_direct_lazy_ref_command_paths(command_resource: BaseResource) -> None:
    values = iter(("first", "second"))

    def load() -> str:
        return next(values)

    reference = LazyRef(load, command_loader=_command_loader(command_resource, load))

    assert reference.get_command().run() == "first"
    assert reference.refresh_command().run() == "second"
    assert reference.value == "second"


def test_explicit_null_refresh_is_cached_no_step_and_zero_io() -> None:
    transport = CliTransport(ClientConfig())
    transport.run_bytes = MagicMock()  # type: ignore[method-assign]
    resource = BaseResource(transport, ClientConfig())
    command_builds = 0

    def command_loader() -> Command[str | None]:
        nonlocal command_builds
        command_builds += 1
        return resource._plan(steps=(), finalize=lambda _results: None)

    reference = LazyRef[str | None](
        lambda: pytest.fail("explicit absence must not call loader"),
        command_loader=command_loader,
        initial=None,
    )

    _assert_loaded(reference, True)
    assert reference.value is None
    assert reference.refresh() is None
    refresh_command = reference.refresh_command()
    assert refresh_command.commands == ()
    assert refresh_command.run() is None
    get_command = reference.get_command()
    assert get_command.commands == ()
    assert get_command.run() is None
    _assert_loaded(reference, True)
    assert reference.value is None
    assert command_builds == 2
    transport.run_bytes.assert_not_called()
    transport.close()
