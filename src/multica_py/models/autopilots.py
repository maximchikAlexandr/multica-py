from __future__ import annotations

import datetime

import msgspec


class Autopilot(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    name: str
    enabled: bool = False


class AutopilotRun(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    status: str
    started_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None


class TriggerConfigItem(msgspec.Struct, frozen=True, kw_only=True):
    key: str
    value: str


class AutopilotTrigger(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    type: str
    config: tuple[TriggerConfigItem, ...] = ()
