from __future__ import annotations

import threading
from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.exceptions import UnloadedReferenceError
from multica_py.models.relations import LazyRef, _GenerationState
from multica_py.resources._base import BaseResource


def _assert_loaded(reference: LazyRef[object], expected: bool) -> None:
    assert reference.loaded is expected


def test_generation_state_distinguishes_unloaded_from_initial_none() -> None:
    unloaded = _GenerationState[str | None](None)
    loaded_none = _GenerationState[str | None](None, initial=None)

    assert unloaded.loaded is False
    assert unloaded.value is None
    assert loaded_none.loaded is True
    assert loaded_none.value is None


def test_lazy_ref_initial_value_and_cached_get() -> None:
    calls = 0

    def load() -> str:
        nonlocal calls
        calls += 1
        return "loaded"

    reference = LazyRef(load, initial="initial")

    _assert_loaded(reference, True)
    assert reference.value == "initial"
    assert reference.get() == "initial"
    assert calls == 0

    reference.invalidate()
    _assert_loaded(reference, False)
    assert reference.get() == "loaded"
    assert reference.get() == "loaded"
    assert calls == 1


def test_lazy_ref_value_raises_before_first_load() -> None:
    reference = LazyRef(lambda: "loaded", entity_type="Issue", entity_id="i1")

    with pytest.raises(UnloadedReferenceError, match=r"Issue\.reference\.value"):
        _ = reference.value


def test_lazy_ref_failed_first_load_is_retryable() -> None:
    attempts = 0

    def load() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("temporary failure")
        return "loaded"

    reference = LazyRef(load)

    with pytest.raises(RuntimeError, match="temporary failure"):
        reference.get()
    _assert_loaded(reference, False)

    assert reference.get() == "loaded"
    _assert_loaded(reference, True)
    assert attempts == 2


def _run_concurrent(
    loader: Callable[[], str],
    *,
    expected_error: type[Exception] | None = None,
) -> tuple[list[str], list[Exception]]:
    reference = LazyRef(loader)
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
    if expected_error is None:
        _assert_loaded(reference, True)
    else:
        _assert_loaded(reference, False)
        assert all(isinstance(error, expected_error) for error in errors)
    return results, errors


_LOAD_STARTED = threading.Event()
_LOAD_RELEASE = threading.Event()


def test_lazy_ref_concurrent_success_is_coalesced() -> None:
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
        return "loaded"

    results, errors = _run_concurrent(load)

    assert calls == 1
    assert results == ["loaded", "loaded"]
    assert errors == []


def test_lazy_ref_concurrent_failure_is_coalesced() -> None:
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
        raise RuntimeError("shared failure")

    results, errors = _run_concurrent(load, expected_error=RuntimeError)

    assert calls == 1
    assert results == []
    assert [str(error) for error in errors] == ["shared failure", "shared failure"]


def test_lazy_ref_refresh_success_replaces_cached_target() -> None:
    values = iter(("first", "second"))
    reference = LazyRef(lambda: next(values))

    assert reference.get() == "first"
    assert reference.refresh() == "second"
    _assert_loaded(reference, True)
    assert reference.value == "second"


def test_lazy_ref_failed_refresh_preserves_cached_target() -> None:
    attempts = 0

    def load() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return "first"
        raise RuntimeError("refresh failed")

    reference = LazyRef(load)
    assert reference.get() == "first"

    with pytest.raises(RuntimeError, match="refresh failed"):
        reference.refresh()
    _assert_loaded(reference, True)
    assert reference.value == "first"
    assert reference.get() == "first"


def test_lazy_ref_invalidation_waits_for_active_generation() -> None:
    load_started = threading.Event()
    load_release = threading.Event()
    invalidation_done = threading.Event()

    def load() -> str:
        load_started.set()
        assert load_release.wait(timeout=2)
        return "loaded"

    reference = LazyRef(load)
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
