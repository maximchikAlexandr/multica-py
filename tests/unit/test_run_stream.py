from __future__ import annotations

import datetime
import inspect
from collections.abc import Generator
from dataclasses import dataclass
from types import MappingProxyType
from typing import cast
from unittest.mock import MagicMock

import pytest

from multica_py.entities.autopilots import AutopilotRun
from multica_py.entities.issues import TaskRun
from multica_py.exceptions import (
    DetachedEntityError,
    MissingRelationContextError,
    NotFoundError,
    OutputShapeError,
    ProtocolError,
)
from multica_py.models.common import Page
from multica_py.models.issue_activity import RunMessage
from multica_py.models.run_events import (
    RunErrorEvent,
    RunStatusChangedEvent,
    RunTextEvent,
    RunToolFinishedEvent,
    RunToolStartedEvent,
    RunUnknownEvent,
)
from tests.unit.resources._factories import make_run_message


def _messages(*messages: RunMessage) -> Page[RunMessage]:
    return Page(items=messages, total=len(messages))


def _empty() -> Page[RunMessage]:
    return Page(items=(), total=0)


def _runs(client: MagicMock, *runs: TaskRun) -> Page[TaskRun]:
    return Page(items=runs, total=len(runs))


def _run(
    client: MagicMock,
    *,
    status: str = "running",
    completed_at: datetime.datetime | None = None,
    task_id: str = "task_1",
    issue_id: str | None = "iss_1",
) -> TaskRun:
    return TaskRun(
        id=task_id,
        status=status,
        completed_at=completed_at,
        issue_id=issue_id,
        _client=client,
    )


def _collect(run: TaskRun, *, poll_interval: float = 1.0) -> list[object]:
    return list(run.stream_events(poll_interval=poll_interval))


def _assert_terminal(events: list[object], status: str) -> None:
    last = events[-1]
    assert isinstance(last, RunStatusChangedEvent)
    assert last.status == status
    assert last.observed_at.tzinfo is datetime.UTC


@pytest.fixture
def sleep_calls(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    calls: list[float] = []
    monkeypatch.setattr("multica_py.entities.issues.time.sleep", calls.append)
    return calls


@dataclass(frozen=True)
class _StatusRun:
    status: str
    completed_at: datetime.datetime | None = None


@dataclass(frozen=True)
class StreamCase:
    id: str
    run_messages: tuple[Page[RunMessage], ...]
    status_runs: tuple[_StatusRun, ...]
    terminal_status: str
    expected_text_sequences: tuple[int, ...] = ()
    expected_error_event: bool = False
    expected_unknown_types: tuple[str, ...] = ()
    expected_since: tuple[int, ...] | None = None
    expected_status_sequence: tuple[str, ...] | None = None
    expected_sleeps: int | None = None
    expected_text: str | None = None
    expected_tool: str | None = None
    expected_tool_input: MappingProxyType[str, str] | None = None
    expected_tool_output: str | None = None


_STREAM_CASES: tuple[StreamCase, ...] = (
    StreamCase(
        id="completed-drains-tail-before-status",
        run_messages=(
            _messages(make_run_message(seq=1, content="m")),
            _messages(make_run_message(seq=2, content="m")),
            _empty(),
            _empty(),
        ),
        status_runs=(_StatusRun("running"), _StatusRun("completed")),
        terminal_status="completed",
        expected_text_sequences=(1, 2),
        expected_sleeps=1,
    ),
    StreamCase(
        id="failed-uses-ordinary-drain",
        run_messages=(
            _messages(make_run_message(seq=1, type="error", content="boom")),
            _empty(),
            _empty(),
        ),
        status_runs=(_StatusRun("running"), _StatusRun("failed")),
        terminal_status="failed",
        expected_error_event=True,
        expected_sleeps=1,
    ),
    StreamCase(
        id="completed-immediate-without-sleep",
        run_messages=(_empty(), _empty()),
        status_runs=(_StatusRun("completed"),),
        terminal_status="completed",
        expected_sleeps=0,
        expected_since=(0, 0),
    ),
    StreamCase(
        id="cancelled-requires-two-quiet-reads",
        run_messages=(
            _messages(make_run_message(seq=1, content="m")),
            _empty(),
            _empty(),
            _empty(),
        ),
        status_runs=(_StatusRun("running"), _StatusRun("cancelled")),
        terminal_status="cancelled",
        expected_text_sequences=(1,),
        expected_sleeps=2,
    ),
    StreamCase(
        id="stale-identical-replay-counts-as-quiet",
        run_messages=(
            _messages(make_run_message(seq=1, content="m")),
            _messages(make_run_message(seq=1, content="m")),
            _empty(),
        ),
        status_runs=(_StatusRun("cancelled"),),
        terminal_status="cancelled",
        expected_text_sequences=(1,),
        expected_sleeps=1,
    ),
    StreamCase(
        id="future-status-terminal-via-completed-at-uses-quiescence",
        run_messages=(
            _messages(make_run_message(seq=1, content="m")),
            _empty(),
            _empty(),
            _empty(),
        ),
        status_runs=(
            _StatusRun("running"),
            _StatusRun("paused", completed_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)),
        ),
        terminal_status="paused",
        expected_text_sequences=(1,),
        expected_sleeps=2,
    ),
    StreamCase(
        id="initial-poll-starts-at-zero",
        run_messages=(
            _messages(make_run_message(seq=1, content="m")),
            _empty(),
            _empty(),
        ),
        status_runs=(_StatusRun("running"), _StatusRun("completed")),
        terminal_status="completed",
        expected_text_sequences=(1,),
        expected_since=(0, 1, 1),
    ),
    StreamCase(
        id="cursor-advances-to-greatest-sequence",
        run_messages=(
            _messages(
                make_run_message(seq=1, content="m"),
                make_run_message(seq=2, content="m"),
                make_run_message(seq=4, content="m"),
            ),
            _empty(),
            _empty(),
        ),
        status_runs=(_StatusRun("running"), _StatusRun("completed")),
        terminal_status="completed",
        expected_text_sequences=(1, 2, 4),
        expected_since=(0, 4, 4),
    ),
    StreamCase(
        id="yields-sequence-zero",
        run_messages=(
            _messages(make_run_message(seq=0, content="m")),
            _empty(),
            _empty(),
        ),
        status_runs=(_StatusRun("running"), _StatusRun("completed")),
        terminal_status="completed",
        expected_text_sequences=(0,),
        expected_since=(0, 0, 0),
    ),
    StreamCase(
        id="suppresses-duplicate-replay",
        run_messages=(
            _messages(make_run_message(seq=1, content="hello")),
            _messages(make_run_message(seq=1, content="hello")),
            _empty(),
            _empty(),
        ),
        status_runs=(
            _StatusRun("running"),
            _StatusRun("running"),
            _StatusRun("completed"),
        ),
        terminal_status="completed",
        expected_text_sequences=(1,),
        expected_text="hello",
    ),
    StreamCase(
        id="out-of-order-rows-are-sorted",
        run_messages=(
            _messages(
                make_run_message(seq=3, content="m"),
                make_run_message(seq=1, content="m"),
                make_run_message(seq=2, content="m"),
            ),
            _empty(),
            _empty(),
        ),
        status_runs=(_StatusRun("running"), _StatusRun("completed")),
        terminal_status="completed",
        expected_text_sequences=(1, 2, 3),
    ),
    StreamCase(
        id="running-status-emitted-once",
        run_messages=(
            _messages(make_run_message(seq=1, content="m")),
            _empty(),
            _empty(),
            _empty(),
        ),
        status_runs=(
            _StatusRun("running"),
            _StatusRun("running"),
            _StatusRun("completed"),
        ),
        terminal_status="completed",
        expected_text_sequences=(1,),
        expected_status_sequence=("running", "completed"),
    ),
    StreamCase(
        id="cancelled-delayed-tail-resets-quiet-count",
        run_messages=(
            _messages(make_run_message(seq=1, content="m")),
            _empty(),
            _messages(make_run_message(seq=2, content="m")),
            _empty(),
            _empty(),
            _empty(),
        ),
        status_runs=(_StatusRun("running"), _StatusRun("cancelled")),
        terminal_status="cancelled",
        expected_text_sequences=(1, 2),
    ),
    StreamCase(
        id="unknown-message-type-preserved",
        run_messages=(
            _messages(make_run_message(seq=1, type="tool-use", content=None)),
            _empty(),
            _empty(),
        ),
        status_runs=(_StatusRun("running"), _StatusRun("completed")),
        terminal_status="completed",
        expected_unknown_types=("tool-use",),
    ),
    StreamCase(
        id="tool-lifecycle-preserves-structured-data",
        run_messages=(
            _messages(
                make_run_message(
                    seq=1,
                    type="tool_use",
                    tool="bash",
                    input=MappingProxyType({"cmd": "ls"}),
                    content=None,
                ),
                make_run_message(
                    seq=2, type="tool_result", tool="bash", output="done", content=None
                ),
            ),
            _empty(),
            _empty(),
        ),
        status_runs=(_StatusRun("running"), _StatusRun("completed")),
        terminal_status="completed",
        expected_tool="bash",
        expected_tool_input=MappingProxyType({"cmd": "ls"}),
        expected_tool_output="done",
    ),
)


@pytest.mark.parametrize(
    "case",
    _STREAM_CASES,
    ids=[c.id for c in _STREAM_CASES],
)
def test_stream_poll_and_drain_variants(case: StreamCase, sleep_calls: list[float]) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = list(case.run_messages)
    client.issues.runs.side_effect = [
        _runs(client, _run(client, status=sr.status, completed_at=sr.completed_at))
        for sr in case.status_runs
    ]
    events = _collect(_run(client))
    text_events = [e for e in events if isinstance(e, RunTextEvent)]
    assert [e.sequence for e in text_events] == list(case.expected_text_sequences)
    assert any(isinstance(e, RunErrorEvent) for e in events) == case.expected_error_event
    unknown = [e for e in events if isinstance(e, RunUnknownEvent)]
    assert tuple(e.message_type for e in unknown) == case.expected_unknown_types
    _assert_terminal(events, case.terminal_status)
    if case.expected_since is not None:
        actual_since = tuple(
            call.kwargs["since"] for call in client.issues.run_messages.call_args_list
        )
        assert actual_since == case.expected_since
    if case.expected_status_sequence is not None:
        status_events = [e for e in events if isinstance(e, RunStatusChangedEvent)]
        assert tuple(e.status for e in status_events) == case.expected_status_sequence
        assert status_events[0].previous_status is None
        assert status_events[1].previous_status == "running"
    if case.expected_sleeps is not None:
        assert len(sleep_calls) == case.expected_sleeps
    if case.expected_text is not None:
        assert text_events[0].text == case.expected_text
    if case.expected_tool is not None:
        started = next(e for e in events if isinstance(e, RunToolStartedEvent))
        finished = next(e for e in events if isinstance(e, RunToolFinishedEvent))
        assert started.tool == case.expected_tool
        assert started.input == case.expected_tool_input
        assert finished.tool == case.expected_tool
        assert finished.output == case.expected_tool_output


def test_stream_conflicting_repeated_sequence_raises(sleep_calls: list[float]) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(make_run_message(seq=1, content="hello")),
        _messages(make_run_message(seq=1, content="different")),
    ]
    client.issues.runs.return_value = _runs(client, _run(client, status="running"))
    with pytest.raises(OutputShapeError):
        _collect(_run(client))


def test_stream_conflict_within_batch_raises(sleep_calls: list[float]) -> None:
    client = MagicMock()
    client.issues.run_messages.return_value = _messages(
        make_run_message(seq=1, content="a"), make_run_message(seq=1, content="b")
    )
    client.issues.runs.return_value = _runs(client, _run(client, status="running"))
    with pytest.raises(OutputShapeError):
        _collect(_run(client))
    client.issues.runs.assert_not_called()


def test_stream_target_disappears_raises_protocol_error(sleep_calls: list[float]) -> None:
    client = MagicMock()
    client.issues.run_messages.return_value = _messages(make_run_message(seq=1, content="m"))
    client.issues.runs.return_value = _runs(client)
    with pytest.raises(ProtocolError):
        _collect(_run(client))


@pytest.mark.parametrize(
    "value",
    [0, -1, float("inf"), float("nan"), True, "1"],
    ids=["zero", "negative", "infinity", "nan", "bool", "nonnumeric"],
)
def test_stream_invalid_interval_raises_before_io(value: object) -> None:
    client = MagicMock()
    run = _run(client)
    with pytest.raises((TypeError, ValueError)):
        next(run.stream_events(poll_interval=value))  # type: ignore[arg-type]
    client.issues.run_messages.assert_not_called()
    client.issues.runs.assert_not_called()


def test_stream_detached_run_raises() -> None:
    run = TaskRun(id="task_1", status="running", issue_id="iss_1")
    with pytest.raises(DetachedEntityError):
        next(run.stream_events())
    with pytest.raises((TypeError, ValueError)):
        next(run.stream_events(poll_interval=0))


def test_stream_missing_issue_id_raises(sleep_calls: list[float]) -> None:
    client = MagicMock()
    with pytest.raises(MissingRelationContextError):
        next(_run(client, issue_id=None).stream_events())


@pytest.mark.parametrize(
    "exc",
    [RuntimeError("boom"), NotFoundError("missing", exit_code=1)],
    ids=["runtime", "not-found"],
)
def test_stream_transport_failure_propagates(exc: Exception, sleep_calls: list[float]) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = exc
    with pytest.raises(type(exc)):
        _collect(_run(client))


def test_stream_independent_of_raw_cache(sleep_calls: list[float]) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(make_run_message(seq=1, content="m")),
        _empty(),
        _empty(),
    ]
    client.issues.runs.side_effect = [
        _runs(client, _run(client, status="running")),
        _runs(client, _run(client, status="completed")),
    ]
    run = _run(client)
    iterator = run.stream_events()
    events = list(iterator)
    assert run._messages is None or not run._messages.loaded
    assert inspect.getgeneratorstate(cast("Generator[object, None, None]", iterator)) == (
        inspect.GEN_CLOSED
    )
    message_events = [event for event in events if not isinstance(event, RunStatusChangedEvent)]
    assert len(message_events) == len({event.sequence for event in message_events})


def test_stream_refresh_failure_propagates(sleep_calls: list[float]) -> None:
    client = MagicMock()
    client.issues.run_messages.return_value = _messages(make_run_message(seq=1, content="m"))
    client.issues.runs.side_effect = NotFoundError("missing", exit_code=1)
    with pytest.raises(NotFoundError):
        _collect(_run(client))


def test_stream_rejects_identity_mismatch(sleep_calls: list[float]) -> None:
    client = MagicMock()
    client.issues.run_messages.return_value = _messages(
        make_run_message(seq=1, task_id="other", content="m")
    )
    client.issues.runs.return_value = _runs(client, _run(client, status="completed"))
    with pytest.raises(OutputShapeError):
        _collect(_run(client))


def test_stream_terminal_drain_is_bounded(
    sleep_calls: list[float], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("multica_py.entities.issues._TERMINAL_DRAIN_POLL_LIMIT", 3)
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _empty(),
        _messages(make_run_message(seq=1, content="m")),
        _messages(make_run_message(seq=2, content="m")),
        _messages(make_run_message(seq=3, content="m")),
        _messages(make_run_message(seq=4, content="m")),
    ]
    client.issues.runs.return_value = _runs(client, _run(client, status="completed"))
    with pytest.raises(ProtocolError):
        _collect(_run(client))


def test_autopilot_run_has_no_stream_events() -> None:
    assert not hasattr(AutopilotRun, "stream_events")
    assert "stream_events" not in getattr(AutopilotRun, "__annotations__", {})
