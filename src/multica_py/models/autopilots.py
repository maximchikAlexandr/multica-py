from __future__ import annotations

import datetime
from typing import Generic, TypeVar

import msgspec

from multica_py.sentinels import Unset, UnsetType
from multica_py.types import JsonValue

TAutopilot = TypeVar("TAutopilot")
TAutopilotRun = TypeVar("TAutopilotRun")


class AutopilotSubscriber(msgspec.Struct, frozen=True, kw_only=True):
    user_type: str
    user_id: str
    created_at: datetime.datetime | None = None


class AutopilotData(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    workspace_id: str
    title: str
    description: str | None = None
    project_id: str | None = None
    assignee_type: str
    assignee_id: str
    status: str
    execution_mode: str
    issue_title_template: str | None = None
    created_by_type: str
    created_by_id: str
    last_run_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    trigger_kinds: tuple[str, ...] = ()
    next_run_at: datetime.datetime | None = None
    last_run_status: str | None = None
    subscriber_snapshot: tuple[AutopilotSubscriber, ...] = ()
    can_write: bool | None = None
    can_manage_access: bool | None = None


class AutopilotRunData(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    autopilot_id: str
    trigger_id: str | None = None
    source: str
    status: str
    issue_id: str | None = None
    task_id: str | None = None
    triggered_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    failure_reason: str | None = None
    reason_code: str | None = None
    trigger_payload: JsonValue = None
    result: JsonValue = None
    created_at: datetime.datetime | None = None


class Autopilot(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    workspace_id: str
    title: str
    description: str | None = None
    project_id: str | None = None
    assignee_type: str
    assignee_id: str
    status: str
    execution_mode: str
    issue_title_template: str | None = None
    created_by_type: str
    created_by_id: str
    last_run_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    trigger_kinds: tuple[str, ...] = ()
    next_run_at: datetime.datetime | None = None
    last_run_status: str | None = None
    subscribers: tuple[AutopilotSubscriber, ...] = ()
    can_write: bool | None = None
    can_manage_access: bool | None = None


class AutopilotRun(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    autopilot_id: str
    trigger_id: str | None = None
    source: str
    status: str
    issue_id: str | None = None
    task_id: str | None = None
    triggered_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    failure_reason: str | None = None
    reason_code: str | None = None
    trigger_payload: JsonValue = None
    result: JsonValue = None
    created_at: datetime.datetime | None = None


class AutopilotListPage(msgspec.Struct, Generic[TAutopilot], frozen=True, kw_only=True):
    autopilots: tuple[TAutopilot, ...] = ()
    total: int = 0


class AutopilotRunListPage(msgspec.Struct, Generic[TAutopilotRun], frozen=True, kw_only=True):
    runs: tuple[TAutopilotRun, ...] = ()
    total: int = 0
    limit: int | None = None
    offset: int | None = None
    has_more: bool = False


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
