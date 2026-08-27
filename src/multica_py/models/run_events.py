"""Semantic immutable run-event models for incremental task-run streaming.

Each event is a frozen, keyword-only :mod:`msgspec` struct.  Message-backed
events carry the complete :class:`RunMessage` they were derived from in
``raw_message``; :class:`RunStatusChangedEvent` is status-only and narrows the
message-backed fields to literal ``None``.
"""

from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TypedDict

import msgspec

from multica_py.models.issue_activity import RunMessage
from multica_py.types import JsonValue

__all__ = [
    "RunErrorEvent",
    "RunEvent",
    "RunStatusChangedEvent",
    "RunTextEvent",
    "RunThinkingEvent",
    "RunToolFinishedEvent",
    "RunToolStartedEvent",
    "RunUnknownEvent",
]


class RunEvent(msgspec.Struct, frozen=True, kw_only=True):
    """Base class for all semantic run events."""

    task_id: str
    issue_id: str | None
    sequence: int | None
    created_at: datetime.datetime | None
    raw_message: RunMessage | None


class _MessageBackedRunEvent(RunEvent):  # type: ignore[misc]
    sequence: int
    raw_message: RunMessage


class RunTextEvent(_MessageBackedRunEvent):  # type: ignore[misc]
    text: str | None


class RunThinkingEvent(_MessageBackedRunEvent):  # type: ignore[misc]
    thinking: str | None


class RunToolStartedEvent(_MessageBackedRunEvent):  # type: ignore[misc]
    tool: str | None
    input: Mapping[str, JsonValue] | None


class RunToolFinishedEvent(_MessageBackedRunEvent):  # type: ignore[misc]
    tool: str | None
    output: str | None


class RunErrorEvent(_MessageBackedRunEvent):  # type: ignore[misc]
    error: str | None


class RunUnknownEvent(_MessageBackedRunEvent):  # type: ignore[misc]
    message_type: str


class RunStatusChangedEvent(RunEvent):  # type: ignore[misc]
    sequence: None
    created_at: None
    raw_message: None
    previous_status: str | None
    status: str
    observed_at: datetime.datetime


class _MessageFields(TypedDict):
    task_id: str
    issue_id: str | None
    sequence: int
    created_at: datetime.datetime | None
    raw_message: RunMessage


def _convert_run_message(message: RunMessage) -> RunEvent:
    """Map one :class:`RunMessage` to exactly one :class:`RunEvent`.

    Known persisted categories (``text``, ``thinking``, ``tool_use``,
    ``tool_result``, ``error``) map to their concrete event.  Every other
    string — including blank and the internal hyphen spellings ``tool-use`` /
    ``tool-result`` — maps losslessly to :class:`RunUnknownEvent`.
    """

    shared: _MessageFields = {
        "task_id": message.task_id,
        "issue_id": message.issue_id,
        "sequence": message.seq,
        "created_at": message.created_at,
        "raw_message": message,
    }
    message_type = message.type
    if message_type == "text":
        return RunTextEvent(**shared, text=message.content)
    if message_type == "thinking":
        return RunThinkingEvent(**shared, thinking=message.content)
    if message_type == "tool_use":
        return RunToolStartedEvent(**shared, tool=message.tool, input=message.input)
    if message_type == "tool_result":
        return RunToolFinishedEvent(**shared, tool=message.tool, output=message.output)
    if message_type == "error":
        return RunErrorEvent(**shared, error=message.content)
    return RunUnknownEvent(**shared, message_type=message_type)
