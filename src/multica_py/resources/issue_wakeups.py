from __future__ import annotations

import datetime
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
from multica_py.models.issue_wakeups import (
    IssueWakeup,
    IssueWakeupEvent,
    IssueWakeupEvents,
    IssueWakeupPage,
)
from multica_py.resources._base import BaseResource, _operation_minimum_cli_version

__all__ = [
    "IssueWakeup",
    "IssueWakeupEvent",
    "IssueWakeupEvents",
    "IssueWakeupPage",
    "IssueWakeupResource",
]

T = TypeVar("T")


def _wakeup(value: Mapping[str, object]) -> IssueWakeup:
    def timestamp(raw: object) -> datetime.datetime | None:
        if isinstance(raw, datetime.datetime):
            return raw
        if isinstance(raw, str):
            try:
                return datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    raw_events = value.get("event_types", ()) or ()
    if not isinstance(raw_events, (list, tuple)):
        raise TypeError("wakeup event_types must be an array")
    return IssueWakeup(
        id=str(value.get("id", "")),
        issue_id=cast("str | None", value.get("issue_id")),
        agent_id=cast("str | None", value.get("agent_id")),
        instruction=cast("str | None", value.get("instruction")),
        kind=cast("str | None", value.get("kind")),
        mode=cast("str | None", value.get("mode")),
        event_types=tuple(str(event) for event in raw_events),
        filter_actor_type=cast("str | None", value.get("filter_actor_type")),
        filter_actor_id=cast("str | None", value.get("filter_actor_id")),
        filter_agent_id=cast("str | None", value.get("filter_agent_id")),
        filter_task_id=cast("str | None", value.get("filter_task_id")),
        parent_comment_id=cast("str | None", value.get("parent_comment_id")),
        after_seconds=cast("int | None", value.get("after_seconds")),
        at=timestamp(value.get("at")),
        interval_seconds=cast("int | None", value.get("interval_seconds")),
        cron_expression=cast("str | None", value.get("cron_expression")),
        timezone=cast("str | None", value.get("timezone")),
        enabled=cast("bool | None", value.get("enabled")),
        status=cast("str | None", value.get("status")),
        next_run_at=timestamp(value.get("next_run_at", value.get("next_fire_at"))),
        last_run_at=timestamp(value.get("last_run_at")),
        created_at=timestamp(value.get("created_at")),
        updated_at=timestamp(value.get("updated_at")),
        metadata=_coerce_json_value(value.get("metadata"), field_name="wakeup.metadata")
        if value.get("metadata") is not None
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
    if wakeup.enabled is False:
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
            events.append(
                IssueWakeupEvent(
                    name=str(item.get("name", item.get("event_type", ""))),
                    description=str(item.get("description", "")),
                )
            )
        else:
            raise TypeError("wakeup event entries must be strings or objects")
    return IssueWakeupEvents(events=tuple(events), loop_protection=loop_protection)


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


class IssueWakeupResource(BaseResource):
    def events_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[IssueWakeupEvents]:
        return self._json_command(
            ("issue", "wakeup", "events"), _decode_events, ISSUE_WAKEUP_EVENTS_BINDING, options
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
            ISSUE_WAKEUP_LIST_BINDING,
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
            ISSUE_WAKEUP_GET_BINDING,
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
            ISSUE_WAKEUP_DISABLE_BINDING,
            options,
        )

    def disable(
        self, issue_id: str, wakeup_id: str, *, options: OperationOptions | None = None
    ) -> IssueWakeup:
        return self.disable_command(issue_id, wakeup_id, options=options).run()

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
        )
        return _with_busy_retry(
            self._json_command(args, _decode_wakeup, ISSUE_WAKEUP_CREATE_BINDING, options)
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
        )
        return self._json_command(
            args, _decode_reenabled_wakeup, ISSUE_WAKEUP_UPDATE_BINDING, options
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
    ) -> tuple[str, ...]:
        validate_nonblank(issue_id)
        validate_nonblank(instruction)
        validate_nonblank(wakeup_kind)
        if not isinstance(event_types, tuple):
            raise TypeError("event_types must be a tuple of strings")
        if any(not isinstance(event, str) or not event for event in event_types):
            raise ValueError("event_types must contain nonblank strings")
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
        return tuple(args)
