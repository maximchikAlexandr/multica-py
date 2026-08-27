from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from multica_py.models.issue_activity import RunMessage
from multica_py.models.run_events import (
    RunErrorEvent,
    RunEvent,
    RunTextEvent,
    RunThinkingEvent,
    RunToolFinishedEvent,
    RunToolStartedEvent,
    RunUnknownEvent,
)
from tests.unit.resources._factories import make_run_message


@dataclass(frozen=True)
class RunMessageCase:
    message: RunMessage
    event_type: type[RunEvent]
    extra: Mapping[str, object]
    id: str


@dataclass(frozen=True)
class DecodeCase:
    id: str
    payload: object
    expect_error: bool = False
    expected_sparse: bool = False
    expected_complete: bool = False
    expected_blank_unknown: bool = False


RUN_MESSAGE_CASES: tuple[RunMessageCase, ...] = (
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
    RunMessageCase(
        make_run_message(type="text", seq=10, content=None),
        RunTextEvent,
        {"text": None},
        "text-sparse",
    ),
    RunMessageCase(
        make_run_message(type="thinking", seq=11, content=None),
        RunThinkingEvent,
        {"thinking": None},
        "thinking-sparse",
    ),
    RunMessageCase(
        make_run_message(type="tool_use", seq=12, tool=None, input=None, content=None),
        RunToolStartedEvent,
        {"tool": None, "input": None},
        "tool-use-sparse",
    ),
    RunMessageCase(
        make_run_message(type="tool_result", seq=13, tool=None, output=None, content=None),
        RunToolFinishedEvent,
        {"tool": None, "output": None},
        "tool-result-sparse",
    ),
    RunMessageCase(
        make_run_message(type="error", seq=14, content=None),
        RunErrorEvent,
        {"error": None},
        "error-sparse",
    ),
)


DECODE_CASES: tuple[DecodeCase, ...] = (
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
