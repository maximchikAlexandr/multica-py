from __future__ import annotations

import datetime

import msgspec


class AutopilotSubscriber(msgspec.Struct, frozen=True, kw_only=True):
    user_type: str
    user_id: str
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
    trigger_payload: object | None = None
    result: object | None = None
    created_at: datetime.datetime | None = None


class AutopilotListPage(msgspec.Struct, frozen=True, kw_only=True):
    autopilots: tuple[Autopilot, ...] = ()
    total: int = 0


class AutopilotRunListPage(msgspec.Struct, frozen=True, kw_only=True):
    runs: tuple[AutopilotRun, ...] = ()
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
