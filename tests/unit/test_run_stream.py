from __future__ import annotations

import datetime
from collections.abc import Iterator
from types import MappingProxyType
from unittest.mock import MagicMock

import pytest

from multica_py.entities.issues import TaskRun
from multica_py.exceptions import (
    DetachedEntityError,
    MissingRelationContextError,
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


def _msg(
    seq: int, *, type: str = "text", content: str | None = "m", task_id: str = "task_1"
) -> RunMessage:
    return RunMessage(task_id=task_id, seq=seq, type=type, content=content)


def _collect(run: TaskRun, *, poll_interval: float = 1.0) -> list[object]:
    return list(run.stream_events(poll_interval=poll_interval))


def _assert_terminal(events: list[object], status: str) -> None:
    last = events[-1]
    assert isinstance(last, RunStatusChangedEvent)
    assert last.status == status


@pytest.fixture
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("multica_py.entities.issues.time.sleep", lambda _seconds: None)


def test_stream_initial_poll_starts_at_zero(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [_messages(_msg(1)), _empty(), _empty()]
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
        _messages(_msg(1), _msg(2), _msg(4)),
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
        _messages(_msg(1, content="hello")),
        _messages(_msg(1, content="hello")),
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
        _messages(_msg(1, content="hello")),
        _messages(_msg(1, content="different")),
    ]
    client.issues.runs.return_value = _runs(client, _run(client, status="running"))
    run = _run(client)

    with pytest.raises(OutputShapeError):
        _collect(run)


def test_stream_conflict_within_batch_raises(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.return_value = _messages(_msg(1, content="a"), _msg(1, content="b"))
    client.issues.runs.return_value = _runs(client, _run(client, status="running"))
    run = _run(client)

    with pytest.raises(OutputShapeError):
        _collect(run)


def test_stream_out_of_order_rows_are_sorted(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(_msg(3), _msg(1), _msg(2)),
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
    client.issues.run_messages.side_effect = [_messages(_msg(1)), _empty(), _empty(), _empty()]
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


def test_stream_completed_drains_tail_before_status_event(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(_msg(1)),
        _messages(_msg(2)),
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
    assert [e.sequence for e in text_events] == [1, 2]
    assert isinstance(events[-1], RunStatusChangedEvent)
    _assert_terminal(events, "completed")


def test_stream_failed_uses_ordinary_drain(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(_msg(1, type="error", content="boom")),
        _empty(),
        _empty(),
    ]
    client.issues.runs.side_effect = [
        _runs(client, _run(client, status="running")),
        _runs(client, _run(client, status="failed")),
    ]
    run = _run(client)

    events = _collect(run)

    assert any(isinstance(e, RunErrorEvent) for e in events)
    assert isinstance(events[-1], RunStatusChangedEvent)
    _assert_terminal(events, "failed")


def test_stream_cancelled_requires_two_quiet_reads(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(_msg(1)),
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

    assert isinstance(events[-1], RunStatusChangedEvent)
    _assert_terminal(events, "cancelled")


def test_stream_cancelled_delayed_tail_resets_quiet_count(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(_msg(1)),
        _empty(),
        _messages(_msg(2)),
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
    assert isinstance(events[-1], RunStatusChangedEvent)
    _assert_terminal(events, "cancelled")


def test_stream_unknown_terminal_via_completed_at_uses_cancellation_path(no_sleep: None) -> None:
    completed_at = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    client = MagicMock()
    client.issues.run_messages.side_effect = [
        _messages(_msg(1)),
        _empty(),
        _empty(),
        _empty(),
    ]
    client.issues.runs.side_effect = [
        _runs(client, _run(client, status="running")),
        _runs(client, _run(client, status="paused", completed_at=completed_at)),
    ]
    run = _run(client)

    events = _collect(run)

    assert isinstance(events[-1], RunStatusChangedEvent)
    _assert_terminal(events, "paused")


def test_stream_target_disappears_raises_protocol_error(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.return_value = _messages(_msg(1))
    client.issues.runs.return_value = _runs(client)
    run = _run(client)

    with pytest.raises(ProtocolError):
        _collect(run)


def test_stream_invalid_interval_raises_before_io() -> None:
    client = MagicMock()
    run = _run(client)

    for value in (0, -1, float("inf"), True):
        with pytest.raises((TypeError, ValueError)):
            next(run.stream_events(poll_interval=value))
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


def test_stream_command_failure_propagates(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = RuntimeError("boom")
    run = _run(client)

    with pytest.raises(RuntimeError, match="boom"):
        _collect(run)


def test_stream_independent_of_raw_cache(no_sleep: None) -> None:
    client = MagicMock()
    client.issues.run_messages.side_effect = [_messages(_msg(1)), _empty(), _empty()]
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
        _messages(_msg(1, type="tool-use", content=None)),
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
