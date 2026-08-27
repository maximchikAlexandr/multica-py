from __future__ import annotations

import datetime
from dataclasses import dataclass
from types import MappingProxyType
from unittest.mock import MagicMock

import pytest

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


@pytest.fixture
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("multica_py.entities.issues.time.sleep", lambda _seconds: None)


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


_STREAM_DRAIN_CASES: tuple[StreamCase, ...] = (
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
    ),
)


@pytest.mark.parametrize(
    "case",
    _STREAM_DRAIN_CASES,
    ids=[c.id for c in _STREAM_DRAIN_CASES],
)
def test_stream_terminal_drain_variants(case: StreamCase, no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = list(case.run_messages)
    client.issues.runs.side_effect = [
        _runs(client, _run(client, status=sr.status, completed_at=sr.completed_at))
        for sr in case.status_runs
    ]
    run = _run(client)

    events = _collect(run)

    text_events = [e for e in events if isinstance(e, RunTextEvent)]
    assert [e.sequence for e in text_events] == list(case.expected_text_sequences)
    has_error = any(isinstance(e, RunErrorEvent) for e in events)
    assert has_error == case.expected_error_event
    _assert_terminal(events, case.terminal_status)


def test_stream_initial_poll_starts_at_zero(no_sleep: None) -> None:
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

    events = _collect(run)

    assert client.issues.run_messages.call_args_list[0].kwargs["since"] == 0
    assert any(isinstance(e, RunTextEvent) for e in events)
    assert isinstance(events[-1], RunStatusChangedEvent)


def test_stream_cursor_advances_to_greatest_sequence(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(
            make_run_message(seq=1, content="m"),
            make_run_message(seq=2, content="m"),
            make_run_message(seq=4, content="m"),
        ),
        _empty(),
        _empty(),
    ]
    client.issues.runs.side_effect = [
        _runs(client, _run(client, status="running")),
        _runs(client, _run(client, status="completed")),
    ]
    run = _run(client)

    events = _collect(run)

    assert client.issues.run_messages.call_args_list[0].kwargs["since"] == 0
    assert client.issues.run_messages.call_args_list[1].kwargs["since"] == 4
    _assert_terminal(events, "completed")


def test_stream_suppresses_duplicate_replay(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(make_run_message(seq=1, content="hello")),
        _messages(make_run_message(seq=1, content="hello")),
        _empty(),
        _empty(),
    ]
    client.issues.runs.side_effect = [
        _runs(client, _run(client, status="running")),
        _runs(client, _run(client, status="running")),
        _runs(client, _run(client, status="completed")),
    ]
    run = _run(client)

    events = _collect(run)

    text_events = [e for e in events if isinstance(e, RunTextEvent)]
    assert len(text_events) == 1
    assert text_events[0].text == "hello"


def test_stream_conflicting_repeated_sequence_raises(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(make_run_message(seq=1, content="hello")),
        _messages(make_run_message(seq=1, content="different")),
    ]
    client.issues.runs.return_value = _runs(client, _run(client, status="running"))
    run = _run(client)

    with pytest.raises(OutputShapeError):
        _collect(run)


def test_stream_conflict_within_batch_raises(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.return_value = _messages(
        make_run_message(seq=1, content="a"), make_run_message(seq=1, content="b")
    )
    client.issues.runs.return_value = _runs(client, _run(client, status="running"))
    run = _run(client)

    with pytest.raises(OutputShapeError):
        _collect(run)


def test_stream_out_of_order_rows_are_sorted(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(
            make_run_message(seq=3, content="m"),
            make_run_message(seq=1, content="m"),
            make_run_message(seq=2, content="m"),
        ),
        _empty(),
        _empty(),
    ]
    client.issues.runs.side_effect = [
        _runs(client, _run(client, status="running")),
        _runs(client, _run(client, status="completed")),
    ]
    run = _run(client)

    events = _collect(run)

    text_events = [e for e in events if isinstance(e, RunTextEvent)]
    assert [e.sequence for e in text_events] == [1, 2, 3]


def test_stream_running_status_emitted_once(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(make_run_message(seq=1, content="m")),
        _empty(),
        _empty(),
        _empty(),
    ]
    client.issues.runs.side_effect = [
        _runs(client, _run(client, status="running")),
        _runs(client, _run(client, status="running")),
        _runs(client, _run(client, status="completed")),
    ]
    run = _run(client)

    events = _collect(run)

    status_events = [e for e in events if isinstance(e, RunStatusChangedEvent)]
    assert [e.status for e in status_events] == ["running", "completed"]
    assert status_events[0].previous_status is None
    assert status_events[1].previous_status == "running"


def test_stream_cancelled_delayed_tail_resets_quiet_count(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(make_run_message(seq=1, content="m")),
        _empty(),
        _messages(make_run_message(seq=2, content="m")),
        _empty(),
        _empty(),
        _empty(),
    ]
    client.issues.runs.side_effect = [
        _runs(client, _run(client, status="running")),
        _runs(client, _run(client, status="cancelled")),
    ]
    run = _run(client)

    events = _collect(run)

    text_events = [e for e in events if isinstance(e, RunTextEvent)]
    assert [e.sequence for e in text_events] == [1, 2]
    _assert_terminal(events, "cancelled")


def test_stream_target_disappears_raises_protocol_error(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.return_value = _messages(make_run_message(seq=1, content="m"))
    client.issues.runs.return_value = _runs(client)
    run = _run(client)

    with pytest.raises(ProtocolError):
        _collect(run)


@pytest.mark.parametrize(
    "value",
    [0, -1, float("inf"), True, 3600.5],
    ids=["zero", "negative", "nonfinite", "bool", "exceeds-ceiling"],
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


def test_stream_missing_issue_id_raises(no_sleep: None) -> None:
    client = MagicMock()
    run = _run(client, issue_id=None)
    with pytest.raises(MissingRelationContextError):
        next(run.stream_events())


@pytest.mark.parametrize(
    "exc",
    [RuntimeError("boom"), NotFoundError("missing", exit_code=1)],
    ids=["runtime", "not-found"],
)
def test_stream_transport_failure_propagates(exc: Exception, no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = exc
    run = _run(client)

    with pytest.raises(type(exc)):
        _collect(run)


def test_stream_independent_of_raw_cache(no_sleep: None) -> None:
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

    list(run.stream_events())

    assert run._messages is None or not run._messages.loaded


def test_stream_unknown_message_type_preserved(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(make_run_message(seq=1, type="tool-use", content=None)),
        _empty(),
        _empty(),
    ]
    client.issues.runs.side_effect = [
        _runs(client, _run(client, status="running")),
        _runs(client, _run(client, status="completed")),
    ]
    run = _run(client)

    events = _collect(run)

    unknown = [e for e in events if isinstance(e, RunUnknownEvent)]
    assert len(unknown) == 1
    assert unknown[0].message_type == "tool-use"


def test_stream_tool_lifecycle_preserves_structured_data(no_sleep: None) -> None:
    client = MagicMock()
    start_msg = RunMessage(
        task_id="task_1", seq=1, type="tool_use", tool="bash", input={"cmd": "ls"}
    )
    finish_msg = RunMessage(task_id="task_1", seq=2, type="tool_result", tool="bash", output="done")
    client.issues.run_messages.side_effect = [
        _messages(start_msg, finish_msg),
        _empty(),
        _empty(),
    ]
    client.issues.runs.side_effect = [
        _runs(client, _run(client, status="running")),
        _runs(client, _run(client, status="completed")),
    ]
    run = _run(client)

    events = _collect(run)

    started = next(e for e in events if isinstance(e, RunToolStartedEvent))
    finished = next(e for e in events if isinstance(e, RunToolFinishedEvent))
    assert started.tool == "bash"
    assert started.input == MappingProxyType({"cmd": "ls"})
    assert finished.tool == "bash"
    assert finished.output == "done"
