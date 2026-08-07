from __future__ import annotations

import datetime
from typing import Generic, TypeVar

import msgspec

from multica_py.models.common import _PageSequence
from multica_py.sentinels import Unset, UnsetType

TAutopilot = TypeVar("TAutopilot")
TAutopilotRun = TypeVar("TAutopilotRun")


class AutopilotSubscriber(msgspec.Struct, frozen=True, kw_only=True):
    user_type: str
    user_id: str
    created_at: datetime.datetime | None = None


class AutopilotListPage(
    _PageSequence[TAutopilot], msgspec.Struct, Generic[TAutopilot], frozen=True, kw_only=True
):
    autopilots: tuple[TAutopilot, ...] = ()
    total: int = 0
    limit: int | None = None
    offset: int | None = None
    has_more: bool = False
    next_cursor: str | None = None

    @property
    def items(self) -> tuple[TAutopilot, ...]:
        return self.autopilots


class AutopilotRunListPage(
    _PageSequence[TAutopilotRun], msgspec.Struct, Generic[TAutopilotRun], frozen=True, kw_only=True
):
    runs: tuple[TAutopilotRun, ...] = ()
    total: int = 0
    limit: int | None = None
    offset: int | None = None
    has_more: bool = False
    next_cursor: str | None = None

    @property
    def items(self) -> tuple[TAutopilotRun, ...]:
        return self.runs


class TriggerConfigItem(msgspec.Struct, frozen=True, kw_only=True):
    key: str
    value: str


class AutopilotTrigger(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    type: str
    config: tuple[TriggerConfigItem, ...] = ()


class AutopilotTriggerCreate(msgspec.Struct, frozen=True, kw_only=True):
    title: str
    kind: str


class AutopilotTriggerUpdate(msgspec.Struct, frozen=True, kw_only=True):
    title: str | UnsetType = Unset
    kind: str | UnsetType = Unset
