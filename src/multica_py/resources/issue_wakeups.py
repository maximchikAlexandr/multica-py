from __future__ import annotations

import datetime
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
from multica_py._internal.commands import Command, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.json_values import _coerce_json_value
from multica_py.config import OperationOptions
from multica_py.models.issue_wakeups import (
    IssueWakeup,
    IssueWakeupEvent,
    IssueWakeupEvents,
    IssueWakeupPage,
)
from multica_py.resources._base import BaseResource, _operation_minimum_cli_version
from multica_py.sentinels import Unset, UnsetType

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
        next_run_at=timestamp(value.get("next_run_at")),
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


def _decode_wakeups(stdout: bytes, command: str) -> IssueWakeupPage:
    raw = decode_json(stdout, object, command=command)
    rows: object
    total: int | None
    limit: int | None
    offset: int | None
    cursor: str | None
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
        total = raw_total if isinstance(raw_total, int) else None
        limit = raw_limit if isinstance(raw_limit, int) else None
        offset = raw_offset if isinstance(raw_offset, int) else None
        cursor = raw_cursor if isinstance(raw_cursor, str) else None
    else:
        raise TypeError("wakeup list response must be an array or object")
    if not isinstance(rows, list | tuple):
        raise TypeError("wakeup list response items must be an array")
    items = tuple(_wakeup(cast("Mapping[str, object]", item)) for item in rows)
    return IssueWakeupPage(items=items, total=total, limit=limit, offset=offset, next_cursor=cursor)


def _decode_events(stdout: bytes, command: str) -> IssueWakeupEvents:
    raw = decode_json(stdout, object, command=command)
    rows = raw.get("events", raw) if isinstance(raw, Mapping) else raw
    if not isinstance(rows, list | tuple):
        raise TypeError("wakeup events response must be an array")
    return IssueWakeupEvents(
        events=tuple(
            IssueWakeupEvent(
                name=str(cast("Mapping[str, object]", item).get("name", "")),
                description=str(cast("Mapping[str, object]", item).get("description", "")),
            )
            for item in rows
        )
    )


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
        instruction: str | None = None,
        kind: str | None = None,
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
        timezone: str | None = None,
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
        return self._json_command(args, _decode_wakeup, ISSUE_WAKEUP_CREATE_BINDING, options)

    def create(
        self,
        issue_id: str,
        *,
        agent_id: str | None = None,
        instruction: str | None = None,
        kind: str | None = None,
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
        timezone: str | None = None,
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
        agent_id: str | UnsetType = Unset,
        instruction: str | UnsetType = Unset,
        kind: str | UnsetType = Unset,
        mode: str | UnsetType = Unset,
        event_types: tuple[str, ...] | UnsetType = Unset,
        filter_actor_type: str | UnsetType = Unset,
        filter_actor_id: str | UnsetType = Unset,
        filter_agent_id: str | UnsetType = Unset,
        filter_task_id: str | UnsetType = Unset,
        parent_comment_id: str | UnsetType = Unset,
        after_seconds: int | UnsetType = Unset,
        at: str | UnsetType = Unset,
        interval_seconds: int | UnsetType = Unset,
        cron_expression: str | UnsetType = Unset,
        timezone: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[IssueWakeup]:
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
        return self._json_command(args, _decode_wakeup, ISSUE_WAKEUP_UPDATE_BINDING, options)

    def update(
        self,
        issue_id: str,
        wakeup_id: str,
        *,
        agent_id: str | UnsetType = Unset,
        instruction: str | UnsetType = Unset,
        kind: str | UnsetType = Unset,
        mode: str | UnsetType = Unset,
        event_types: tuple[str, ...] | UnsetType = Unset,
        filter_actor_type: str | UnsetType = Unset,
        filter_actor_id: str | UnsetType = Unset,
        filter_agent_id: str | UnsetType = Unset,
        filter_task_id: str | UnsetType = Unset,
        parent_comment_id: str | UnsetType = Unset,
        after_seconds: int | UnsetType = Unset,
        at: str | UnsetType = Unset,
        interval_seconds: int | UnsetType = Unset,
        cron_expression: str | UnsetType = Unset,
        timezone: str | UnsetType = Unset,
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
        agent_id: str | None | UnsetType,
        instruction: str | None | UnsetType,
        wakeup_kind: str | None | UnsetType,
        mode: str | None | UnsetType,
        event_types: tuple[str, ...] | UnsetType,
        filter_actor_type: str | None | UnsetType,
        filter_actor_id: str | None | UnsetType,
        filter_agent_id: str | None | UnsetType,
        filter_task_id: str | None | UnsetType,
        parent_comment_id: str | None | UnsetType,
        after_seconds: int | None | UnsetType,
        at: str | None | UnsetType,
        interval_seconds: int | None | UnsetType,
        cron_expression: str | None | UnsetType,
        timezone: str | None | UnsetType,
    ) -> tuple[str, ...]:
        validate_nonblank(issue_id)
        if wakeup_id is not None:
            validate_nonblank(wakeup_id)
        args = ["issue", "wakeup", command, issue_id]
        if wakeup_id is not None:
            args.append(wakeup_id)
        values = (
            ("agent-id", agent_id),
            ("instruction", instruction),
            ("kind", wakeup_kind),
            ("mode", mode),
            ("filter-actor-type", filter_actor_type),
            ("filter-actor-id", filter_actor_id),
            ("filter-agent-id", filter_agent_id),
            ("task-id", filter_task_id),
            ("parent", parent_comment_id),
            ("after", after_seconds),
            ("at", at),
            ("every", interval_seconds),
            ("cron", cron_expression),
            ("timezone", timezone),
        )
        for flag, value in values:
            if value is not Unset and value is not None:
                args.extend((f"--{flag}", str(value)))
        if event_types is not Unset:
            for event in event_types:
                args.extend(("--event", event))
        return tuple(args)
