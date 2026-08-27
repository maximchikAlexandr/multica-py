from __future__ import annotations

import datetime
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

import msgspec
import pytest

from multica_py._internal.wire_models import decode_run_messages
from multica_py.exceptions import OutputShapeError
from multica_py.models.issue_activity import RunMessage
from multica_py.models.run_events import (
    RunErrorEvent,
    RunEvent,
    RunTextEvent,
    RunThinkingEvent,
    RunToolFinishedEvent,
    RunToolStartedEvent,
    RunUnknownEvent,
    _convert_run_message,
)
from tests.unit.resources._factories import make_run_message


@dataclass(frozen=True)
class RunMessageCase:
    message: RunMessage
    event_type: type[RunEvent]
    extra: Mapping[str, object]
    id: str


_RUN_MESSAGE_CASES: tuple[RunMessageCase, ...] = (
    RunMessageCase(
        make_run_message(type="text", seq=1, content="hello"),
        RunTextEvent,
        {"text": "hello"},
        "text",
    ),
    RunMessageCase(
        make_run_message(type="thinking", seq=2, content="hm"),
        RunThinkingEvent,
        {"thinking": "hm"},
        "thinking",
    ),
    RunMessageCase(
        make_run_message(
            type="tool_use", seq=3, tool="bash", input=MappingProxyType({"cmd": "ls"})
        ),
        RunToolStartedEvent,
        {"tool": "bash", "input": MappingProxyType({"cmd": "ls"})},
        "tool-use",
    ),
    RunMessageCase(
        make_run_message(type="tool_result", seq=4, tool="bash", output="ok"),
        RunToolFinishedEvent,
        {"tool": "bash", "output": "ok"},
        "tool-result",
    ),
    RunMessageCase(
        make_run_message(type="error", seq=5, content="boom"),
        RunErrorEvent,
        {"error": "boom"},
        "error",
    ),
    RunMessageCase(
        make_run_message(type="tool-use", seq=6, tool="bash"),
        RunUnknownEvent,
        {"message_type": "tool-use"},
        "tool-use-hyphen",
    ),
    RunMessageCase(
        make_run_message(type="tool-result", seq=7),
        RunUnknownEvent,
        {"message_type": "tool-result"},
        "tool-result-hyphen",
    ),
    RunMessageCase(
        make_run_message(type="", seq=8),
        RunUnknownEvent,
        {"message_type": ""},
        "blank",
    ),
    RunMessageCase(
        make_run_message(type="future_kind", seq=9),
        RunUnknownEvent,
        {"message_type": "future_kind"},
        "future",
    ),
)


@pytest.mark.parametrize(
    "case",
    _RUN_MESSAGE_CASES,
    ids=[c.id for c in _RUN_MESSAGE_CASES],
)
def test_convert_run_message_maps_known_and_unknown_types(case: RunMessageCase) -> None:
    message = case.message
    event_type = case.event_type
    extra = case.extra
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
    ("message", "event_type", "fields"),
    [
        (make_run_message(type="text", seq=1, content=None), RunTextEvent, {"text": None}),
        (
            make_run_message(type="thinking", seq=2, content=None),
            RunThinkingEvent,
            {"thinking": None},
        ),
        (
            make_run_message(type="tool_use", seq=3, tool=None, input=None, content=None),
            RunToolStartedEvent,
            {"tool": None, "input": None},
        ),
        (
            make_run_message(type="tool_result", seq=4, tool=None, output=None, content=None),
            RunToolFinishedEvent,
            {"tool": None, "output": None},
        ),
        (make_run_message(type="error", seq=5, content=None), RunErrorEvent, {"error": None}),
    ],
    ids=["text", "thinking", "tool-use", "tool-result", "error"],
)
def test_sparse_known_payload_keeps_none(
    message: RunMessage, event_type: type[RunEvent], fields: Mapping[str, object]
) -> None:
    event = _convert_run_message(message)
    assert isinstance(event, event_type)
    assert event.raw_message == message
    for key, value in fields.items():
        assert getattr(event, key) is value


def test_run_events_are_immutable() -> None:
    event: RunEvent = _convert_run_message(make_run_message(type="text", seq=1, content="hi"))
    with pytest.raises((msgspec.ValidationError, TypeError, AttributeError)):
        object.__setattr__(event, "text", "changed")


def test_pattern_match_narrows_message_fields() -> None:
    event = _convert_run_message(make_run_message(type="text", seq=1, content="hi"))
    match event:
        case RunTextEvent(sequence=sequence, raw_message=raw_message, text=text):
            assert sequence == 1
            assert text == "hi"
            assert raw_message.seq == 1
        case _:
            raise AssertionError("expected RunTextEvent")


@dataclass(frozen=True)
class DecodeCase:
    id: str
    payload: object
    expect_error: bool = False
    expected_sparse: bool = False
    expected_complete: bool = False
    expected_blank_unknown: bool = False


_DECODE_CASES: tuple[DecodeCase, ...] = (
    DecodeCase(
        id="complete",
        payload=[
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
        ],
        expected_complete=True,
    ),
    DecodeCase(
        id="sparse",
        payload=[{"task_id": "run_1", "seq": 2, "type": "text", "content": "hi"}],
        expected_sparse=True,
    ),
    DecodeCase(
        id="blank",
        payload=[{"task_id": "run_1", "seq": 3, "type": ""}],
        expected_blank_unknown=True,
    ),
    DecodeCase(
        id="malformed-input",
        payload=[{"task_id": "r", "seq": 1, "type": "tool_use", "input": [1, 2]}],
        expect_error=True,
    ),
    DecodeCase(
        id="negative-seq",
        payload=[{"task_id": "r", "seq": -1, "type": "text"}],
        expect_error=True,
    ),
    DecodeCase(
        id="seq-above-int32",
        payload=[{"task_id": "r", "seq": 2_147_483_648, "type": "text"}],
        expect_error=True,
    ),
)


@pytest.mark.parametrize("case", _DECODE_CASES, ids=[c.id for c in _DECODE_CASES])
def test_decode_run_messages(case: DecodeCase) -> None:
    payload = msgspec.json.encode(case.payload)
    if case.expect_error:
        with pytest.raises((msgspec.ValidationError, OutputShapeError)):
            decode_run_messages(payload, "test")
        return
    items = decode_run_messages(payload, "test")
    message = items[0]
    if case.expected_complete:
        assert message.task_id == "run_1"
        assert message.seq == 1
        assert message.type == "tool_use"
        assert message.tool == "bash"
        assert message.input == MappingProxyType({"cmd": "ls", "args": ("-l",)})
        assert message.created_at == datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    if case.expected_sparse:
        assert message.issue_id is None
        assert message.tool is None
        assert message.input is None
        assert message.output is None
        assert message.created_at is None
    if case.expected_blank_unknown:
        assert message.type == ""
        event = _convert_run_message(message)
        assert isinstance(event, RunUnknownEvent)
        assert event.message_type == ""
