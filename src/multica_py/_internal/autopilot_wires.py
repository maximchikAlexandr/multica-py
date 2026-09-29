from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import msgspec

from multica_py._internal.json_values import _coerce_json_value
from multica_py._internal.wire_presence import presence as _presence_seed
from multica_py.entities._base import _runtime_state
from multica_py.models.autopilots import (
    AutopilotListPage,
    AutopilotRunListPage,
    AutopilotSubscriber,
    AutopilotTrigger,
)

if TYPE_CHECKING:
    from multica_py.entities.autopilots import Autopilot, AutopilotRun


class _AutopilotTriggerWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    autopilot_id: str
    kind: str
    enabled: bool
    cron_expression: str | None = None
    timezone: str | None = None
    next_run_at: datetime.datetime | None = None
    label: str | None = None
    last_fired_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


def trigger_from_wire(wire: _AutopilotTriggerWire) -> AutopilotTrigger:
    return AutopilotTrigger(
        id=wire.id,
        autopilot_id=wire.autopilot_id,
        kind=wire.kind,
        enabled=wire.enabled,
        cron_expression=wire.cron_expression,
        timezone=wire.timezone,
        next_run_at=wire.next_run_at,
        label=wire.label,
        last_fired_at=wire.last_fired_at,
        created_at=wire.created_at,
        updated_at=wire.updated_at,
    )


class _AutopilotSubscriberWire(msgspec.Struct, frozen=True, kw_only=True):
    user_type: str
    user_id: str
    created_at: datetime.datetime | None = None


class _AutopilotWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    workspace_id: str
    title: str
    description: str | None = None
    project_id: str | None | msgspec.UnsetType = msgspec.UNSET
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
    subscribers: tuple[_AutopilotSubscriberWire, ...] | msgspec.UnsetType = msgspec.UNSET
    can_write: bool | None = None
    can_manage_access: bool | None = None
    has_webhook_token: bool | None = None
    webhook_token_hint: str | None = None
    webhook_token: str | None = None
    webhook_path: str | None = None
    webhook_url: str | None = None


class _AutopilotListWire(msgspec.Struct, frozen=True, kw_only=True):
    autopilots: tuple[_AutopilotWire, ...] = ()
    total: int = 0


def _autopilot_from_wire(wire: _AutopilotWire, *, secret_access: bool = False) -> Autopilot:
    from multica_py.entities.autopilots import Autopilot

    result = Autopilot(
        id=wire.id,
        workspace_id=wire.workspace_id,
        title=wire.title,
        description=wire.description,
        project_id=None if wire.project_id is msgspec.UNSET else wire.project_id,
        assignee_type=wire.assignee_type,
        assignee_id=wire.assignee_id,
        status=wire.status,
        execution_mode=wire.execution_mode,
        issue_title_template=wire.issue_title_template,
        created_by_type=wire.created_by_type,
        created_by_id=wire.created_by_id,
        last_run_at=wire.last_run_at,
        created_at=wire.created_at,
        updated_at=wire.updated_at,
        trigger_kinds=wire.trigger_kinds,
        next_run_at=wire.next_run_at,
        last_run_status=wire.last_run_status,
        subscriber_snapshot=tuple(
            AutopilotSubscriber(
                user_type=subscriber.user_type,
                user_id=subscriber.user_id,
                created_at=subscriber.created_at,
            )
            for subscriber in (() if wire.subscribers is msgspec.UNSET else wire.subscribers)
        ),
        can_write=wire.can_write,
        can_manage_access=wire.can_manage_access,
        has_webhook_token=wire.has_webhook_token,
        webhook_token_hint=wire.webhook_token_hint,
        webhook_token=wire.webhook_token if secret_access else None,
        webhook_path=wire.webhook_path if secret_access else None,
        webhook_url=wire.webhook_url if secret_access else None,
        _wire_presence=(("project_id", _presence_seed(wire.project_id)),),
    )
    if secret_access and any((wire.webhook_token, wire.webhook_path, wire.webhook_url)):
        _runtime_state(result)["secret_access"] = True
    return result


def _autopilot_list_page_from_wire(
    wire: _AutopilotListWire, *, secret_access: bool = False
) -> AutopilotListPage[object]:
    return AutopilotListPage(
        items=tuple(
            _autopilot_from_wire(item, secret_access=secret_access) for item in wire.autopilots
        ),
        total=wire.total,
    )


class _AutopilotGetWire(msgspec.Struct, frozen=True, kw_only=True):
    autopilot: _AutopilotWire
    triggers: tuple[_AutopilotTriggerWire, ...] | msgspec.UnsetType = msgspec.UNSET


class _AutopilotGetResult:
    def __init__(
        self,
        data: Autopilot,
        *,
        triggers: tuple[AutopilotTrigger, ...] | msgspec.UnsetType,
        subscribers: tuple[AutopilotSubscriber, ...] | msgspec.UnsetType,
    ) -> None:
        self.data = data
        self.triggers = triggers
        self.subscribers = subscribers


def _autopilot_subscribers(
    wire: tuple[_AutopilotSubscriberWire, ...] | msgspec.UnsetType,
) -> tuple[AutopilotSubscriber, ...] | msgspec.UnsetType:
    if wire is msgspec.UNSET:
        return msgspec.UNSET
    return tuple(
        AutopilotSubscriber(
            user_type=item.user_type,
            user_id=item.user_id,
            created_at=item.created_at,
        )
        for item in wire
    )


def _autopilot_get_from_wire(
    wire: _AutopilotGetWire, *, secret_access: bool = False
) -> _AutopilotGetResult:
    return _AutopilotGetResult(
        _autopilot_from_wire(wire.autopilot, secret_access=secret_access),
        triggers=(
            msgspec.UNSET
            if wire.triggers is msgspec.UNSET
            else tuple(trigger_from_wire(item) for item in wire.triggers)
        ),
        subscribers=_autopilot_subscribers(wire.autopilot.subscribers),
    )


class _AutopilotRunWire(msgspec.Struct, frozen=True, kw_only=True):
    id: str
    autopilot_id: str
    trigger_id: str | None = None
    source: str
    status: str
    issue_id: str | None | msgspec.UnsetType = msgspec.UNSET
    task_id: str | None = None
    triggered_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    failure_reason: str | None = None
    reason_code: str | None = None
    trigger_payload: object | None = None
    result: object | None = None
    created_at: datetime.datetime | None = None


def _autopilot_run_from_wire(wire: _AutopilotRunWire) -> AutopilotRun:
    from multica_py.entities.autopilots import AutopilotRun

    trigger_payload = (
        None
        if wire.trigger_payload is None
        else _coerce_json_value(wire.trigger_payload, field_name="trigger_payload")
    )
    result = None if wire.result is None else _coerce_json_value(wire.result, field_name="result")
    return AutopilotRun(
        id=wire.id,
        autopilot_id=wire.autopilot_id,
        trigger_id=wire.trigger_id,
        source=wire.source,
        status=wire.status,
        issue_id=None if wire.issue_id is msgspec.UNSET else wire.issue_id,
        task_id=wire.task_id,
        triggered_at=wire.triggered_at,
        completed_at=wire.completed_at,
        failure_reason=wire.failure_reason,
        reason_code=wire.reason_code,
        trigger_payload=trigger_payload,
        result=result,
        created_at=wire.created_at,
        _wire_presence=(("issue_id", _presence_seed(wire.issue_id)),),
    )


class _AutopilotRunListPageWire(msgspec.Struct, frozen=True, kw_only=True):
    runs: tuple[_AutopilotRunWire, ...] = ()
    total: int = 0


def _autopilot_run_list_page_from_wire(
    wire: _AutopilotRunListPageWire, *, limit: int | None = None, offset: int | None = None
) -> AutopilotRunListPage[AutopilotRun]:
    runs = tuple(_autopilot_run_from_wire(run) for run in wire.runs)
    has_more = (offset or 0) + len(runs) < wire.total
    return AutopilotRunListPage(
        items=runs,
        total=wire.total,
        limit=limit,
        offset=offset,
        has_more=has_more,
    )
