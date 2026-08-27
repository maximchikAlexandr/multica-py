from __future__ import annotations

import datetime
from collections.abc import Mapping
from types import MappingProxyType

import msgspec
import pytest

from multica_py._internal.json_values import _coerce_json_value
from multica_py._internal.wire_models import (
    _run_message_from_wire,
    _RunMessageWire,
    decode_run_messages,
)
from multica_py.exceptions import OutputShapeError
from multica_py.models.issue_activity import RunMessage
from multica_py.models.run_events import (
    RunErrorEvent,
    RunEvent,
    RunStatusChangedEvent,
    RunTextEvent,
    RunThinkingEvent,
    RunToolFinishedEvent,
    RunToolStartedEvent,
    RunUnknownEvent,
    _convert_run_message,
)
from multica_py.types import JsonValue


def _msg(
    *,
    type: str,
    seq: int,
    task_id: str = "task_1",
    issue_id: str | None = "iss_1",
    tool: str | None = None,
    content: str | None = None,
    input: Mapping[str, JsonValue] | None = None,
    output: str | None = None,
    created_at: datetime.datetime | None = None,
) -> RunMessage:
    return RunMessage(
        task_id=task_id,
        seq=seq,
        type=type,
        issue_id=issue_id,
        tool=tool,
        content=content,
        input=input,
        output=output,
        created_at=created_at,
    )


@pytest.mark.parametrize(
    "case",
    [
        (_msg(type="text", seq=1, content="hello"), RunTextEvent, {"text": "hello"}),
        (_msg(type="thinking", seq=2, content="hm"), RunThinkingEvent, {"thinking": "hm"}),
        (
            _msg(type="tool_use", seq=3, tool="bash", input=MappingProxyType({"cmd": "ls"})),
            RunToolStartedEvent,
            {"tool": "bash", "input": MappingProxyType({"cmd": "ls"})},
        ),
        (
            _msg(type="tool_result", seq=4, tool="bash", output="ok"),
            RunToolFinishedEvent,
            {"tool": "bash", "output": "ok"},
        ),
        (_msg(type="error", seq=5, content="boom"), RunErrorEvent, {"error": "boom"}),
        (_msg(type="tool-use", seq=6, tool="bash"), RunUnknownEvent, {"message_type": "tool-use"}),
        (_msg(type="tool-result", seq=7), RunUnknownEvent, {"message_type": "tool-result"}),
        (_msg(type="", seq=8), RunUnknownEvent, {"message_type": ""}),
        (_msg(type="future_kind", seq=9), RunUnknownEvent, {"message_type": "future_kind"}),
    ],
    ids=[
        "text",
        "thinking",
        "tool-use",
        "tool-result",
        "error",
        "tool-use-hyphen",
        "tool-result-hyphen",
        "blank",
        "future",
    ],
)
def test_convert_run_message_maps_known_and_unknown_types(
    case: tuple[RunMessage, type[RunEvent], dict[str, object]],
) -> None:
    message, event_type, extra = case
    event = _convert_run_message(message)
    assert isinstance(event, event_type)
    assert event.task_id == message.task_id
    assert event.issue_id == message.issue_id
    assert event.sequence == message.seq
    assert event.created_at == message.created_at
    assert event.raw_message == message
    for key, value in extra.items():
        assert getattr(event, key) == value


@pytest.mark.parametrize(
    "message",
    [
        _msg(type="text", seq=1),
        _msg(type="thinking", seq=2),
        _msg(type="tool_use", seq=3),
        _msg(type="error", seq=4),
    ],
    ids=["text-sparse", "thinking-sparse", "tool-use-sparse", "error-sparse"],
)
def test_sparse_known_payload_keeps_none(message: RunMessage) -> None:
    event = _convert_run_message(message)
    assert isinstance(event, RunEvent)
    assert event.raw_message == message


def test_run_events_are_immutable() -> None:
    event: RunEvent = _convert_run_message(_msg(type="text", seq=1, content="hi"))
    with pytest.raises((msgspec.ValidationError, TypeError, AttributeError)):
        object.__setattr__(event, "text", "changed")


def test_status_changed_event_narrows_message_fields_to_none() -> None:
    event = RunStatusChangedEvent(
        task_id="t1",
        issue_id=None,
        sequence=None,
        created_at=None,
        raw_message=None,
        previous_status=None,
        status="running",
        observed_at=datetime.datetime.now(datetime.UTC),
    )
    assert event.sequence is None
    assert event.created_at is None
    assert event.raw_message is None


def test_decode_run_messages_complete_payload() -> None:
    payload = msgspec.json.encode(
        [
            {
                "task_id": "run_1",
                "seq": 1,
                "type": "tool_use",
                "issue_id": "iss_1",
                "tool": "bash",
                "content": None,
                "input": {"cmd": "ls", "args": ["-l"]},
                "output": None,
                "created_at": "2026-01-01T00:00:00Z",
            }
        ]
    )
    items = decode_run_messages(payload, "test")
    assert len(items) == 1
    message = items[0]
    assert message.task_id == "run_1"
    assert message.seq == 1
    assert message.type == "tool_use"
    assert message.tool == "bash"
    assert message.input == MappingProxyType({"cmd": "ls", "args": ("-l",)})
    assert message.created_at == datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


def test_decode_run_messages_sparse_payload() -> None:
    payload = msgspec.json.encode([{"task_id": "run_1", "seq": 2, "type": "text", "content": "hi"}])
    items = decode_run_messages(payload, "test")
    message = items[0]
    assert message.issue_id is None
    assert message.tool is None
    assert message.input is None
    assert message.output is None
    assert message.created_at is None


def test_decode_run_messages_blank_type_preserved() -> None:
    payload = msgspec.json.encode([{"task_id": "run_1", "seq": 3, "type": ""}])
    items = decode_run_messages(payload, "test")
    assert items[0].type == ""
    event = _convert_run_message(items[0])
    assert isinstance(event, RunUnknownEvent)
    assert event.message_type == ""


def test_decode_run_messages_malformed_input_raises() -> None:
    payload = msgspec.json.encode([{"task_id": "r", "seq": 1, "type": "tool_use", "input": [1, 2]}])
    with pytest.raises((msgspec.ValidationError, OutputShapeError)):
        decode_run_messages(payload, "test")


def test_coerce_json_value_rejects_nonfinite() -> None:
    with pytest.raises(msgspec.ValidationError):
        _coerce_json_value(float("inf"), field_name="input")
    with pytest.raises(msgspec.ValidationError):
        _coerce_json_value(float("nan"), field_name="input")
