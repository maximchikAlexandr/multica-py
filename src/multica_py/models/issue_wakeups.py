from __future__ import annotations

import datetime

import msgspec

from multica_py.models.common import Page
from multica_py.types import JsonValue

__all__ = [
    "IssueWakeup",
    "IssueWakeupDeleteResult",
    "IssueWakeupEvent",
    "IssueWakeupEvents",
    "IssueWakeupPage",
    "IssueWakeupRun",
    "IssueWakeupRunsPage",
    "IssueWakeupTriggerResult",
]


class IssueWakeup(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    issue_id: str | None = None
    agent_id: str | None = None
    instruction: str | None = None
    kind: str | None = None
    mode: str | None = None
    event_types: tuple[str, ...] = ()
    filter_actor_type: str | None = None
    filter_actor_id: str | None = None
    filter_agent_id: str | None = None
    filter_task_id: str | None = None
    parent_comment_id: str | None = None
    after_seconds: int | None = None
    at: datetime.datetime | None = None
    interval_seconds: int | None = None
    cron_expression: str | None = None
    timezone: str | None = None
    enabled: bool | None = None
    status: str | None = None
    next_run_at: datetime.datetime | None = None
    last_run_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    metadata: JsonValue | None = None
    expires_in_seconds: int | None = None
    expires_at: datetime.datetime | None = None
    on_timeout: str | None = None
    max_fires: int | None = None
    fire_count: int | None = None
    paused: bool | None = None
    condition: JsonValue | None = None
    provenance: JsonValue | None = None


class IssueWakeupEvent(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    description: str = ""
    condition: JsonValue | None = None
    loop_protection: str | None = None


class IssueWakeupEvents(msgspec.Struct, frozen=True, kw_only=True):
    events: tuple[IssueWakeupEvent, ...] = ()
    loop_protection: str | None = None


IssueWakeupPage = Page[IssueWakeup]


class IssueWakeupRun(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    status: str
    created_at: datetime.datetime
    checkin_note: str | None = None


class IssueWakeupTriggerResult(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    triggered: bool


class IssueWakeupDeleteResult(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    deleted: bool


IssueWakeupRunsPage = Page[IssueWakeupRun]
