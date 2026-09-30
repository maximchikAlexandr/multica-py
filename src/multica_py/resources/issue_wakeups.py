from __future__ import annotations

import datetime
import json
import time
from collections.abc import Callable, Mapping
from typing import TypeVar, cast

from multica_py._generated.approved_sdk import (
    ISSUE_WAKEUP_CREATE_BINDING,
    ISSUE_WAKEUP_DISABLE_BINDING,
    ISSUE_WAKEUP_EVENTS_BINDING,
    ISSUE_WAKEUP_GET_BINDING,
    ISSUE_WAKEUP_LIST_BINDING,
    ISSUE_WAKEUP_UPDATE_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command, _coalesced_command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.json_values import _coerce_json_value
from multica_py.config import OperationOptions
from multica_py.exceptions import CommandExecutionError, OutputShapeError
from multica_py.models.common import ActionResult, Page
from multica_py.models.issue_wakeups import (
    IssueWakeup,
    IssueWakeupDeleteResult,
    IssueWakeupEvent,
    IssueWakeupEvents,
    IssueWakeupPage,
    IssueWakeupRun,
    IssueWakeupRunsPage,
    IssueWakeupTriggerResult,
)
from multica_py.resources._base import BaseResource, _operation_minimum_cli_version

__all__ = [
    "IssueWakeup",
    "IssueWakeupDeleteResult",
    "IssueWakeupEvent",
    "IssueWakeupEvents",
    "IssueWakeupPage",
    "IssueWakeupResource",
    "IssueWakeupRun",
    "IssueWakeupRunsPage",
    "IssueWakeupTriggerResult",
]

T = TypeVar("T")


def _wakeup(value: Mapping[str, object]) -> IssueWakeup:
    def timestamp(raw: object, *, field_name: str) -> datetime.datetime | None:
        if raw is None:
            return None
        if isinstance(raw, datetime.datetime):
            return raw
        if isinstance(raw, str):
            try:
                return datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                pass
        raise TypeError(f"{field_name} must be an RFC3339 timestamp or null")

    def optional_string(field_name: str) -> str | None:
        raw = value.get(field_name)
        if raw is not None and not isinstance(raw, str):
            raise TypeError(f"wakeup {field_name} must be a string or null")
        return raw

    def optional_int(field_name: str) -> int | None:
        raw = value.get(field_name)
        if raw is not None and (type(raw) is not int):
            raise TypeError(f"wakeup {field_name} must be an integer or null")
        return raw

    def optional_bool(field_name: str) -> bool | None:
        raw = value.get(field_name)
        if raw is not None and type(raw) is not bool:
            raise TypeError(f"wakeup {field_name} must be a boolean or null")
        return raw

    raw_id = value.get("id")
    if not isinstance(raw_id, str) or not raw_id:
        raise TypeError("wakeup id must be a nonblank string")

    raw_events = value.get("event_types", ()) or ()
    if not isinstance(raw_events, (list, tuple)):
        raise TypeError("wakeup event_types must be an array")
    if any(not isinstance(event, str) for event in raw_events):
        raise TypeError("wakeup event_types must contain strings")
    return IssueWakeup(
        id=raw_id,
        issue_id=optional_string("issue_id"),
        agent_id=optional_string("agent_id"),
        instruction=optional_string("instruction"),
        kind=optional_string("kind"),
        mode=optional_string("mode"),
        event_types=tuple(raw_events),
        filter_actor_type=optional_string("filter_actor_type"),
        filter_actor_id=optional_string("filter_actor_id"),
        filter_agent_id=optional_string("filter_agent_id"),
        filter_task_id=optional_string("filter_task_id"),
        parent_comment_id=optional_string("parent_comment_id"),
        after_seconds=optional_int("after_seconds"),
        at=timestamp(value.get("at"), field_name="wakeup.at"),
        interval_seconds=optional_int("interval_seconds"),
        cron_expression=optional_string("cron_expression"),
        timezone=optional_string("timezone"),
        enabled=optional_bool("enabled"),
        status=optional_string("status"),
        next_run_at=timestamp(
            value.get("next_run_at", value.get("next_fire_at")), field_name="wakeup.next_run_at"
        ),
        last_run_at=timestamp(value.get("last_run_at"), field_name="wakeup.last_run_at"),
        created_at=timestamp(value.get("created_at"), field_name="wakeup.created_at"),
        updated_at=timestamp(value.get("updated_at"), field_name="wakeup.updated_at"),
        metadata=_coerce_json_value(value.get("metadata"), field_name="wakeup.metadata")
        if value.get("metadata") is not None
        else None,
        expires_in_seconds=optional_int("expires_in_seconds"),
        expires_at=timestamp(value.get("expires_at"), field_name="wakeup.expires_at"),
        on_timeout=optional_string("on_timeout"),
        max_fires=optional_int("max_fires"),
        fire_count=optional_int("fire_count"),
        paused=optional_bool("paused"),
        condition=_coerce_json_value(value.get("condition"), field_name="wakeup.condition")
        if value.get("condition") is not None
        else None,
        provenance=_coerce_json_value(value.get("provenance"), field_name="wakeup.provenance")
        if value.get("provenance") is not None
        else None,
    )


def _decode_wakeup(stdout: bytes, command: str) -> IssueWakeup:
    raw = decode_json(stdout, dict[str, object], command=command)
    payload = raw.get("wakeup", raw)
    if not isinstance(payload, Mapping):
        raise TypeError("wakeup response must be an object")
    return _wakeup(payload)


def _decode_reenabled_wakeup(stdout: bytes, command: str) -> IssueWakeup:
    wakeup = _decode_wakeup(stdout, command)
    if wakeup.enabled is not True:
        raise OutputShapeError("issue wakeup update must return an enabled wakeup")
    return wakeup


def _decode_wakeups(stdout: bytes, command: str) -> IssueWakeupPage:
    raw = decode_json(stdout, object, command=command)
    rows: object
    total: int | None
    limit: int | None
    offset: int | None
    cursor: str | None
    has_more = False
    if isinstance(raw, list):
        rows = cast("list[object]", raw)
        total = len(rows)
        limit = offset = None
        cursor = None
    elif isinstance(raw, Mapping):
        mapping = cast("Mapping[str, object]", raw)
        rows = mapping.get("wakeups", mapping.get("items", ()))
        raw_total = mapping.get("total")
        raw_limit = mapping.get("limit")
        raw_offset = mapping.get("offset")
        raw_cursor = mapping.get("next_cursor")
        raw_has_more = mapping.get("has_more")
        total = raw_total if isinstance(raw_total, int) else None
        limit = raw_limit if isinstance(raw_limit, int) else None
        offset = raw_offset if isinstance(raw_offset, int) else None
        cursor = raw_cursor if isinstance(raw_cursor, str) else None
        has_more = raw_has_more if isinstance(raw_has_more, bool) else False
    else:
        raise TypeError("wakeup list response must be an array or object")
    if not isinstance(rows, list | tuple):
        raise TypeError("wakeup list response items must be an array")
    items: list[IssueWakeup] = []
    for item in rows:
        if not isinstance(item, Mapping):
            raise TypeError("wakeup list response items must be objects")
        items.append(_wakeup(item))
    return IssueWakeupPage(
        items=tuple(items),
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more,
        next_cursor=cursor,
    )


def _decode_events(stdout: bytes, command: str) -> IssueWakeupEvents:
    raw = decode_json(stdout, object, command=command)
    loop_protection: str | None = None
    if isinstance(raw, Mapping):
        rows = raw.get("events", raw.get("event_types", ()))
        raw_loop_protection = raw.get("loop_protection")
        if raw_loop_protection is not None and not isinstance(raw_loop_protection, str):
            raise TypeError("wakeup loop_protection must be a string or null")
        loop_protection = raw_loop_protection
    else:
        rows = raw
    if not isinstance(rows, list | tuple):
        raise TypeError("wakeup events response must be an array or object")
    events: list[IssueWakeupEvent] = []
    for item in rows:
        if isinstance(item, str):
            events.append(IssueWakeupEvent(name=item))
        elif isinstance(item, Mapping):
            raw_name = item.get("name", item.get("event_type"))
            if not isinstance(raw_name, str) or not raw_name:
                raise TypeError("wakeup event name must be a nonblank string")
            raw_description = item.get("description", "")
            if not isinstance(raw_description, str):
                raise TypeError("wakeup event description must be a string")
            raw_loop_protection = item.get("loop_protection")
            if raw_loop_protection is not None and not isinstance(raw_loop_protection, str):
                raise TypeError("wakeup event loop_protection must be a string or null")
            events.append(
                IssueWakeupEvent(
                    name=raw_name,
                    description=raw_description,
                    condition=_coerce_json_value(
                        item.get("condition"), field_name="wakeup.condition"
                    )
                    if item.get("condition") is not None
                    else None,
                    loop_protection=raw_loop_protection,
                )
            )
        else:
            raise TypeError("wakeup event entries must be strings or objects")
    return IssueWakeupEvents(events=tuple(events), loop_protection=loop_protection)


def _decode_ack(
    stdout: bytes, command: str, *, field_name: str
) -> IssueWakeupTriggerResult | IssueWakeupDeleteResult:
    raw = decode_json(stdout, dict[str, object], command=command)
    raw_id = raw.get("id")
    acknowledged = raw.get(field_name)
    if not isinstance(raw_id, str) or not raw_id:
        raise TypeError("wakeup acknowledgement id must be a nonblank string")
    if type(acknowledged) is not bool:
        raise TypeError(f"wakeup acknowledgement {field_name} must be a boolean")
    if acknowledged is not True:
        raise OutputShapeError(f"wakeup acknowledgement {field_name} must be true")
    if field_name == "triggered":
        return IssueWakeupTriggerResult(id=raw_id, triggered=acknowledged)
    return IssueWakeupDeleteResult(id=raw_id, deleted=acknowledged)


def _decode_trigger(stdout: bytes, command: str) -> IssueWakeupTriggerResult:
    result = _decode_ack(stdout, command, field_name="triggered")
    return cast("IssueWakeupTriggerResult", result)


def _decode_delete(stdout: bytes, command: str) -> IssueWakeupDeleteResult:
    result = _decode_ack(stdout, command, field_name="deleted")
    return cast("IssueWakeupDeleteResult", result)


def _decode_runs(stdout: bytes, command: str) -> IssueWakeupRunsPage:
    raw = decode_json(stdout, list[object], command=command)
    runs: list[IssueWakeupRun] = []
    for item in raw:
        if not isinstance(item, Mapping):
            raise TypeError("wakeup run rows must be objects")
        raw_id = item.get("id")
        raw_status = item.get("status")
        if not isinstance(raw_id, str) or not raw_id:
            raise TypeError("wakeup run id must be a nonblank string")
        if not isinstance(raw_status, str) or not raw_status:
            raise TypeError("wakeup run status must be a nonblank string")
        raw_created_at = item.get("created_at")
        if not isinstance(raw_created_at, str):
            raise TypeError("wakeup run created_at must be an RFC3339 timestamp")
        try:
            created_at = datetime.datetime.fromisoformat(raw_created_at.replace("Z", "+00:00"))
        except ValueError as error:
            raise TypeError("wakeup run created_at must be an RFC3339 timestamp") from error
        raw_note = item.get("checkin_note")
        if raw_note is not None and not isinstance(raw_note, str):
            raise TypeError("wakeup run checkin_note must be a string or null")
        runs.append(
            IssueWakeupRun(
                id=raw_id,
                status=raw_status,
                created_at=created_at,
                checkin_note=raw_note,
            )
        )
    return Page(items=tuple(runs), total=len(runs))


def _is_wakeup_source_busy(error: CommandExecutionError) -> bool:
    return error.code == "wakeup_source_busy" or "wakeup_source_busy" in str(error).lower()


def _with_busy_retry(command: Command[T]) -> Command[T]:
    """Retry the CLI's explicit wakeup-source conflict at most once."""
    plan = command._plan
    if len(plan.steps) != 1:
        raise ValueError("wakeup retry requires one command step")
    step = plan.steps[0]

    def run() -> T:
        for attempt in range(2):
            try:
                return cast("T", plan._run_step(step, step.argv))
            except CommandExecutionError as error:
                if attempt == 0 and _is_wakeup_source_busy(error):
                    time.sleep(0.25)
                    continue
                raise
        raise AssertionError("bounded wakeup retry exhausted without a result")

    return _coalesced_command(command, run)


def _validate_wakeup_inputs(
    *,
    kind: str,
    mode: str | None,
    event_types: tuple[str, ...],
    filter_actor_type: str | None,
    filter_actor_id: str | None,
    filter_agent_id: str | None,
    filter_task_id: str | None,
    after_seconds: int | None,
    at: str | None,
    interval_seconds: int | None,
    cron_expression: str | None,
    expires_in_seconds: int | None,
    expires_at: str | None,
    on_timeout: str | None,
    max_fires: int | None,
    condition: Mapping[str, object] | None,
) -> None:
    if kind not in {"event", "at", "every", "cron"}:
        raise ValueError("kind must be event, at, every or cron")
    if mode is not None and mode not in {"once", "continuous"}:
        raise ValueError("mode must be once or continuous")
    if at is not None and (not isinstance(at, str) or not at.strip()):
        raise ValueError("at must be a nonblank timestamp when provided")
    if cron_expression is not None and (
        not isinstance(cron_expression, str) or not cron_expression.strip()
    ):
        raise ValueError("cron_expression must be nonblank when provided")
    for name, value in (("after_seconds", after_seconds), ("interval_seconds", interval_seconds)):
        if value is not None and (type(value) is not int or value <= 0):
            raise ValueError(f"{name} must be a positive whole number of seconds")

    if expires_in_seconds is not None and (
        type(expires_in_seconds) is not int or not 60 <= expires_in_seconds <= 31_536_000
    ):
        raise ValueError("expires_in_seconds must be an integer from 60 to 31536000")
    expiry: datetime.datetime | None = None
    if expires_at is not None:
        if not isinstance(expires_at, str) or not expires_at.strip():
            raise ValueError("expires_at must be a nonblank RFC3339 timestamp")
        try:
            expiry = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("expires_at must be an RFC3339 timestamp") from error
        if expiry.tzinfo is None:
            raise ValueError("expires_at must include a timezone")
        now = datetime.datetime.now(datetime.UTC)
        if not now < expiry <= now + datetime.timedelta(days=365):
            raise ValueError("expires_at must be in the future and no more than one year ahead")
    if expires_in_seconds is not None and expires_at is not None:
        raise ValueError("expires_in_seconds and expires_at are mutually exclusive")
    if on_timeout is not None:
        if not isinstance(on_timeout, str) or on_timeout not in {"end", "wake"}:
            raise ValueError("on_timeout must be end or wake")
        if expires_in_seconds is None and expires_at is None:
            raise ValueError("on_timeout requires a deadline")
        if on_timeout == "wake" and kind != "event":
            raise ValueError("on_timeout wake requires event kind")
    if max_fires is not None:
        if type(max_fires) is not int or not 1 <= max_fires <= 1000:
            raise ValueError("max_fires must be an integer from 1 to 1000")
        if mode != "continuous":
            raise ValueError("max_fires requires continuous mode")
    if kind == "at" and any(
        value is not None for value in (expires_in_seconds, expires_at, on_timeout, max_fires)
    ):
        raise ValueError("at wakeups cannot contain deadline or fire-limit fields")

    has_schedule = any(
        value is not None for value in (after_seconds, at, interval_seconds, cron_expression)
    )
    has_filter = any(
        value is not None
        for value in (filter_actor_type, filter_actor_id, filter_agent_id, filter_task_id)
    )

    if condition is not None:
        if not isinstance(condition, Mapping):
            raise TypeError("condition must be a mapping")
        families = {
            "status",
            "assignee",
            "label",
            "property",
            "children_done",
            "pull_request",
            "referenced_issue",
        }
        keys = set(condition)
        if len(keys) != 1 or not keys <= families:
            raise ValueError("condition must contain exactly one approved condition family")
        family = next(iter(keys))
        raw_condition = condition[family]
        if family in {"status", "label"}:
            if not isinstance(raw_condition, str) or not raw_condition.strip():
                raise ValueError(f"condition {family} must be a nonblank string")
        elif family == "assignee":
            if not isinstance(raw_condition, str) or not raw_condition.strip():
                raise ValueError("condition assignee must be nonblank")
            assignee_type, separator, assignee_id = raw_condition.partition(":")
            if (
                assignee_type not in {"member", "agent", "squad"}
                or not separator
                or not assignee_id
            ):
                raise ValueError("condition assignee must be member|agent|squad:ID")
        elif family == "property":
            if raw_condition is None:
                raise ValueError("condition property must be non-null JSON")
            if isinstance(raw_condition, str) and len(raw_condition) > 1024:
                raise ValueError("condition property string must be at most 1 KiB")
            _coerce_json_value(raw_condition, field_name="condition.property")
        elif family == "children_done":
            if not isinstance(raw_condition, Mapping):
                raise TypeError("condition children_done must be an object")
            stage = raw_condition.get("stage")
            if type(stage) is not int or not 1 <= stage <= 1000:
                raise ValueError("condition children_done stage must be an integer from 1 to 1000")
        elif family == "pull_request":
            pull_request_status = (
                raw_condition.get("status") if isinstance(raw_condition, Mapping) else raw_condition
            )
            if pull_request_status not in {"checks", "merged"}:
                raise ValueError("condition pull_request status must be checks or merged")
        else:
            if not isinstance(raw_condition, Mapping):
                raise TypeError("condition referenced_issue must be an object")
            referenced_state = raw_condition.get("state")
            referenced_id = raw_condition.get("id")
            if referenced_state not in {"done", "ended", "in_review"}:
                raise ValueError(
                    "condition referenced_issue state must be done, ended or in_review"
                )
            if not isinstance(referenced_id, str) or not referenced_id.strip():
                raise ValueError("condition referenced_issue id must be nonblank")
        if kind != "event":
            raise ValueError("conditions require event kind")
        if event_types or has_schedule or has_filter:
            raise ValueError("conditions cannot be combined with events, filters or schedules")

    if filter_actor_type is not None or filter_actor_id is not None:
        if filter_actor_type not in {"member", "agent"} or not filter_actor_id:
            raise ValueError("actor filters require member|agent and a nonblank actor ID")
        if filter_agent_id is not None or filter_task_id is not None:
            raise ValueError("actor filters cannot be combined with agent or task filters")
    if filter_task_id is not None and (
        not event_types or any(not event.startswith("task.") for event in event_types)
    ):
        raise ValueError("task filter requires only task events")

    if kind == "event":
        if not event_types and condition is None:
            raise ValueError("event wakeups require at least one event type")
        if has_schedule:
            raise ValueError("event wakeups cannot contain a schedule")
        return
    if event_types or has_filter:
        raise ValueError("schedule wakeups cannot contain event or filter inputs")
    if kind == "at":
        if (at is None) == (after_seconds is None):
            raise ValueError("at wakeups require exactly one of at or after_seconds")
        if mode not in (None, "once"):
            raise ValueError("at wakeups require once mode")
        if interval_seconds is not None or cron_expression is not None:
            raise ValueError("at wakeups cannot combine schedules")
    elif kind == "every":
        if interval_seconds is None or interval_seconds < 60 or interval_seconds > 31536000:
            raise ValueError("every wakeups require interval_seconds from 60 to 31536000")
        if (
            mode not in (None, "continuous")
            or at is not None
            or after_seconds is not None
            or cron_expression
        ):
            raise ValueError("every wakeups require continuous mode and only interval_seconds")
    elif kind == "cron":
        if (
            mode not in (None, "continuous")
            or at is not None
            or after_seconds is not None
            or interval_seconds is not None
        ):
            raise ValueError("cron wakeups require continuous mode and only cron_expression")
        if cron_expression is None:
            raise ValueError("cron wakeups require cron_expression")


def _condition_arg(condition: Mapping[str, object]) -> str:
    normalized = _coerce_json_value(condition, field_name="condition")

    def plain(value: object) -> object:
        if isinstance(value, Mapping):
            return {str(key): plain(item) for key, item in value.items()}
        if isinstance(value, tuple):
            return [plain(item) for item in value]
        return value

    return json.dumps(plain(normalized), separators=(",", ":"), sort_keys=True)


class IssueWakeupResource(BaseResource):
    def events_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[IssueWakeupEvents]:
        return self._json_command(
            ("issue", "wakeup", "events"),
            _decode_events,
            cast("object", ISSUE_WAKEUP_EVENTS_BINDING),
            options,
        )

    def events(self, *, options: OperationOptions | None = None) -> IssueWakeupEvents:
        return self.events_command(options=options).run()

    def list_command(
        self, issue_id: str, *, options: OperationOptions | None = None
    ) -> Command[IssueWakeupPage]:
        validate_nonblank(issue_id)
        return self._json_command(
            ("issue", "wakeup", "list", issue_id),
            _decode_wakeups,
            cast("object", ISSUE_WAKEUP_LIST_BINDING),
            options,
        )

    def list(self, issue_id: str, *, options: OperationOptions | None = None) -> IssueWakeupPage:
        return self.list_command(issue_id, options=options).run()

    def get_command(
        self, issue_id: str, wakeup_id: str, *, options: OperationOptions | None = None
    ) -> Command[IssueWakeup]:
        validate_nonblank(issue_id)
        validate_nonblank(wakeup_id)
        return self._json_command(
            ("issue", "wakeup", "get", issue_id, wakeup_id),
            _decode_wakeup,
            cast("object", ISSUE_WAKEUP_GET_BINDING),
            options,
        )

    def get(
        self, issue_id: str, wakeup_id: str, *, options: OperationOptions | None = None
    ) -> IssueWakeup:
        return self.get_command(issue_id, wakeup_id, options=options).run()

    def disable_command(
        self, issue_id: str, wakeup_id: str, *, options: OperationOptions | None = None
    ) -> Command[IssueWakeup]:
        validate_nonblank(issue_id)
        validate_nonblank(wakeup_id)
        return self._json_command(
            ("issue", "wakeup", "disable", issue_id, wakeup_id),
            _decode_wakeup,
            cast("object", ISSUE_WAKEUP_DISABLE_BINDING),
            options,
        )

    def disable(
        self, issue_id: str, wakeup_id: str, *, options: OperationOptions | None = None
    ) -> IssueWakeup:
        return self.disable_command(issue_id, wakeup_id, options=options).run()

    def trigger_command(
        self, issue_id: str, wakeup_id: str, *, options: OperationOptions | None = None
    ) -> Command[IssueWakeupTriggerResult]:
        validate_nonblank(issue_id)
        validate_nonblank(wakeup_id)
        return self._json_command(
            ("issue", "wakeup", "trigger", issue_id, wakeup_id),
            _decode_trigger,
            None,
            options,
        )

    def trigger(
        self, issue_id: str, wakeup_id: str, *, options: OperationOptions | None = None
    ) -> IssueWakeupTriggerResult:
        return self.trigger_command(issue_id, wakeup_id, options=options).run()

    def delete_command(
        self, issue_id: str, wakeup_id: str, *, options: OperationOptions | None = None
    ) -> Command[IssueWakeupDeleteResult]:
        validate_nonblank(issue_id)
        validate_nonblank(wakeup_id)
        return self._json_command(
            ("issue", "wakeup", "delete", issue_id, wakeup_id),
            _decode_delete,
            None,
            options,
        )

    def delete(
        self, issue_id: str, wakeup_id: str, *, options: OperationOptions | None = None
    ) -> IssueWakeupDeleteResult:
        return self.delete_command(issue_id, wakeup_id, options=options).run()

    def checkin_command(
        self,
        issue_id: str,
        wakeup_id: str,
        note: str,
        *,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[None]]:
        validate_nonblank(issue_id)
        validate_nonblank(wakeup_id)
        if not isinstance(note, str) or not note.strip():
            raise ValueError("note must be a nonblank string")
        return self._action_command(
            ("issue", "wakeup", "checkin", issue_id, wakeup_id, "--note", note),
            options=options,
        )

    def checkin(
        self,
        issue_id: str,
        wakeup_id: str,
        note: str,
        *,
        options: OperationOptions | None = None,
    ) -> ActionResult[None]:
        return self.checkin_command(issue_id, wakeup_id, note, options=options).run()

    def runs_command(
        self, issue_id: str, wakeup_id: str, *, options: OperationOptions | None = None
    ) -> Command[IssueWakeupRunsPage]:
        validate_nonblank(issue_id)
        validate_nonblank(wakeup_id)
        return self._json_command(
            ("issue", "wakeup", "runs", issue_id, wakeup_id), _decode_runs, None, options
        )

    def runs(
        self, issue_id: str, wakeup_id: str, *, options: OperationOptions | None = None
    ) -> IssueWakeupRunsPage:
        return self.runs_command(issue_id, wakeup_id, options=options).run()

    def create_command(
        self,
        issue_id: str,
        *,
        agent_id: str | None = None,
        instruction: str,
        kind: str = "event",
        mode: str | None = None,
        event_types: tuple[str, ...] = (),
        filter_actor_type: str | None = None,
        filter_actor_id: str | None = None,
        filter_agent_id: str | None = None,
        filter_task_id: str | None = None,
        parent_comment_id: str | None = None,
        after_seconds: int | None = None,
        at: str | None = None,
        interval_seconds: int | None = None,
        cron_expression: str | None = None,
        timezone: str = "UTC",
        expires_in_seconds: int | None = None,
        expires_at: str | None = None,
        on_timeout: str | None = None,
        max_fires: int | None = None,
        condition: Mapping[str, object] | None = None,
        options: OperationOptions | None = None,
    ) -> Command[IssueWakeup]:
        args = self._build_args(
            "create",
            issue_id,
            wakeup_id=None,
            agent_id=agent_id,
            instruction=instruction,
            wakeup_kind=kind,
            mode=mode,
            event_types=event_types,
            filter_actor_type=filter_actor_type,
            filter_actor_id=filter_actor_id,
            filter_agent_id=filter_agent_id,
            filter_task_id=filter_task_id,
            parent_comment_id=parent_comment_id,
            after_seconds=after_seconds,
            at=at,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            timezone=timezone,
            expires_in_seconds=expires_in_seconds,
            expires_at=expires_at,
            on_timeout=on_timeout,
            max_fires=max_fires,
            condition=condition,
        )
        return _with_busy_retry(
            self._json_command(
                args, _decode_wakeup, cast("object", ISSUE_WAKEUP_CREATE_BINDING), options
            )
        )

    def create(
        self,
        issue_id: str,
        *,
        agent_id: str | None = None,
        instruction: str,
        kind: str = "event",
        mode: str | None = None,
        event_types: tuple[str, ...] = (),
        filter_actor_type: str | None = None,
        filter_actor_id: str | None = None,
        filter_agent_id: str | None = None,
        filter_task_id: str | None = None,
        parent_comment_id: str | None = None,
        after_seconds: int | None = None,
        at: str | None = None,
        interval_seconds: int | None = None,
        cron_expression: str | None = None,
        timezone: str = "UTC",
        expires_in_seconds: int | None = None,
        expires_at: str | None = None,
        on_timeout: str | None = None,
        max_fires: int | None = None,
        condition: Mapping[str, object] | None = None,
        options: OperationOptions | None = None,
    ) -> IssueWakeup:
        return self.create_command(
            issue_id,
            agent_id=agent_id,
            instruction=instruction,
            kind=kind,
            mode=mode,
            event_types=event_types,
            filter_actor_type=filter_actor_type,
            filter_actor_id=filter_actor_id,
            filter_agent_id=filter_agent_id,
            filter_task_id=filter_task_id,
            parent_comment_id=parent_comment_id,
            after_seconds=after_seconds,
            at=at,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            timezone=timezone,
            expires_in_seconds=expires_in_seconds,
            expires_at=expires_at,
            on_timeout=on_timeout,
            max_fires=max_fires,
            condition=condition,
            options=options,
        ).run()

    def update_command(
        self,
        issue_id: str,
        wakeup_id: str,
        *,
        agent_id: str | None = None,
        instruction: str,
        kind: str = "event",
        mode: str | None = None,
        event_types: tuple[str, ...] = (),
        filter_actor_type: str | None = None,
        filter_actor_id: str | None = None,
        filter_agent_id: str | None = None,
        filter_task_id: str | None = None,
        parent_comment_id: str | None = None,
        after_seconds: int | None = None,
        at: str | None = None,
        interval_seconds: int | None = None,
        cron_expression: str | None = None,
        timezone: str = "UTC",
        expires_in_seconds: int | None = None,
        expires_at: str | None = None,
        on_timeout: str | None = None,
        max_fires: int | None = None,
        condition: Mapping[str, object] | None = None,
        options: OperationOptions | None = None,
    ) -> Command[IssueWakeup]:
        """Replace the full configuration; the service re-enables it atomically."""
        args = self._build_args(
            "update",
            issue_id,
            wakeup_id=wakeup_id,
            agent_id=agent_id,
            instruction=instruction,
            wakeup_kind=kind,
            mode=mode,
            event_types=event_types,
            filter_actor_type=filter_actor_type,
            filter_actor_id=filter_actor_id,
            filter_agent_id=filter_agent_id,
            filter_task_id=filter_task_id,
            parent_comment_id=parent_comment_id,
            after_seconds=after_seconds,
            at=at,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            timezone=timezone,
            expires_in_seconds=expires_in_seconds,
            expires_at=expires_at,
            on_timeout=on_timeout,
            max_fires=max_fires,
            condition=condition,
        )
        return self._json_command(
            args, _decode_reenabled_wakeup, cast("object", ISSUE_WAKEUP_UPDATE_BINDING), options
        )

    def update(
        self,
        issue_id: str,
        wakeup_id: str,
        *,
        agent_id: str | None = None,
        instruction: str,
        kind: str = "event",
        mode: str | None = None,
        event_types: tuple[str, ...] = (),
        filter_actor_type: str | None = None,
        filter_actor_id: str | None = None,
        filter_agent_id: str | None = None,
        filter_task_id: str | None = None,
        parent_comment_id: str | None = None,
        after_seconds: int | None = None,
        at: str | None = None,
        interval_seconds: int | None = None,
        cron_expression: str | None = None,
        timezone: str = "UTC",
        expires_in_seconds: int | None = None,
        expires_at: str | None = None,
        on_timeout: str | None = None,
        max_fires: int | None = None,
        condition: Mapping[str, object] | None = None,
        options: OperationOptions | None = None,
    ) -> IssueWakeup:
        return self.update_command(
            issue_id,
            wakeup_id,
            agent_id=agent_id,
            instruction=instruction,
            kind=kind,
            mode=mode,
            event_types=event_types,
            filter_actor_type=filter_actor_type,
            filter_actor_id=filter_actor_id,
            filter_agent_id=filter_agent_id,
            filter_task_id=filter_task_id,
            parent_comment_id=parent_comment_id,
            after_seconds=after_seconds,
            at=at,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            timezone=timezone,
            expires_in_seconds=expires_in_seconds,
            expires_at=expires_at,
            on_timeout=on_timeout,
            max_fires=max_fires,
            condition=condition,
            options=options,
        ).run()

    def _json_command(
        self,
        args: tuple[str, ...],
        decoder: Callable[[bytes, str], T],
        binding: object,
        options: OperationOptions | None,
    ) -> Command[T]:
        return self._plan(
            steps=(_Step((*args, "--output", "json"), "run_bytes", decode=decoder),),
            finalize=lambda results: cast("T", results[0]),
            options=options,
            minimum_cli_version=_operation_minimum_cli_version(binding),
        )

    @staticmethod
    def _build_args(
        command: str,
        issue_id: str,
        *,
        wakeup_id: str | None,
        agent_id: str | None,
        instruction: str,
        wakeup_kind: str,
        mode: str | None,
        event_types: tuple[str, ...],
        filter_actor_type: str | None,
        filter_actor_id: str | None,
        filter_agent_id: str | None,
        filter_task_id: str | None,
        parent_comment_id: str | None,
        after_seconds: int | None,
        at: str | None,
        interval_seconds: int | None,
        cron_expression: str | None,
        timezone: str,
        expires_in_seconds: int | None,
        expires_at: str | None,
        on_timeout: str | None,
        max_fires: int | None,
        condition: Mapping[str, object] | None,
    ) -> tuple[str, ...]:
        validate_nonblank(issue_id)
        validate_nonblank(instruction)
        validate_nonblank(wakeup_kind)
        if not isinstance(event_types, tuple):
            raise TypeError("event_types must be a tuple of strings")
        if any(not isinstance(event, str) or not event for event in event_types):
            raise ValueError("event_types must contain nonblank strings")
        _validate_wakeup_inputs(
            kind=wakeup_kind,
            mode=mode,
            event_types=event_types,
            filter_actor_type=filter_actor_type,
            filter_actor_id=filter_actor_id,
            filter_agent_id=filter_agent_id,
            filter_task_id=filter_task_id,
            after_seconds=after_seconds,
            at=at,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            expires_in_seconds=expires_in_seconds,
            expires_at=expires_at,
            on_timeout=on_timeout,
            max_fires=max_fires,
            condition=condition,
        )
        if wakeup_id is not None:
            validate_nonblank(wakeup_id)
        args = ["issue", "wakeup", command, issue_id]
        if wakeup_id is not None:
            args.append(wakeup_id)
        head_values: tuple[tuple[str, object], ...] = (
            ("agent-id", agent_id),
            ("instruction", instruction),
            ("kind", wakeup_kind),
            ("mode", mode),
        )
        for flag, value in head_values:
            if value is not None:
                args.extend((f"--{flag}", str(value)))
        for event in event_types:
            args.extend(("--event", event))
        tail_values: tuple[tuple[str, object], ...] = (
            ("filter-actor-type", filter_actor_type),
            ("filter-actor-id", filter_actor_id),
            ("filter-agent-id", filter_agent_id),
            ("task-id", filter_task_id),
            ("parent", parent_comment_id),
            ("after", after_seconds),
            ("at", at),
            ("every", interval_seconds),
            ("cron", cron_expression),
        )
        for flag, value in tail_values:
            if value is not None:
                args.extend((f"--{flag}", str(value)))
        if timezone != "UTC":
            args.extend(("--timezone", timezone))
        tail_v2: tuple[tuple[str, object], ...] = (
            ("expires-in", expires_in_seconds),
            ("expires-at", expires_at),
            ("on-timeout", on_timeout),
            ("max-fires", max_fires),
        )
        for flag, value in tail_v2:
            if value is not None:
                args.extend((f"--{flag}", str(value)))
        if condition is not None:
            args.extend(("--condition", _condition_arg(condition)))
        return tuple(args)
