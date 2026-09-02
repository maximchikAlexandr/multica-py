from __future__ import annotations

import datetime
from types import MappingProxyType

import msgspec
import pytest

from multica_py._internal.wire_models import decode_run_messages
from multica_py.exceptions import OutputShapeError
from multica_py.models.run_events import (
    RunEvent,
    RunTextEvent,
    RunUnknownEvent,
    _convert_run_message,
)
from tests.unit.resources._factories import make_run_message
from tests.unit.resources.run_event_cases import (
    DECODE_CASES,
    RUN_MESSAGE_CASES,
    DecodeCase,
    RunMessageCase,
)


@pytest.mark.parametrize(
    "case",
    RUN_MESSAGE_CASES,
    ids=[c.id for c in RUN_MESSAGE_CASES],
)
def test_convert_run_message_maps_known_and_unknown_types(case: RunMessageCase) -> None:
    message = case.message
    event = _convert_run_message(message)
    assert isinstance(event, case.event_type)
    assert event.task_id == message.task_id
    assert event.issue_id == message.issue_id
    assert event.sequence == message.seq
    assert event.created_at == message.created_at
    assert event.raw_message == message
    for key, value in case.extra.items():
        assert getattr(event, key) == value


def test_run_events_are_immutable() -> None:
    event: RunEvent = _convert_run_message(make_run_message(type="text", seq=1, content="hi"))
    with pytest.raises((msgspec.ValidationError, TypeError, AttributeError)):
        event.text = "changed"  # type: ignore[attr-defined]


def test_pattern_match_narrows_message_fields() -> None:
    event = _convert_run_message(make_run_message(type="text", seq=1, content="hi"))
    match event:
        case RunTextEvent(sequence=sequence, raw_message=raw_message, text=text):
            assert sequence == 1
            assert text == "hi"
            assert raw_message.seq == 1
        case _:
            raise AssertionError("expected RunTextEvent")


@pytest.mark.parametrize("case", DECODE_CASES, ids=[c.id for c in DECODE_CASES])
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
