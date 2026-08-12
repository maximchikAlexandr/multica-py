from __future__ import annotations

import shlex
from collections.abc import Callable
from dataclasses import replace
from typing import cast

import msgspec

from multica_py._generated.approved_sdk import (
    AUTOPILOT_TRIGGER_ADD_BINDING,
    AUTOPILOT_TRIGGER_DELETE_BINDING,
    AUTOPILOT_TRIGGER_UPDATE_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command, _replace_plan, _Step
from multica_py._internal.decoders import decode_json
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    _autopilot_from_wire,
    _autopilot_get_from_wire,
    _autopilot_run_from_wire,
    _autopilot_run_list_page_from_wire,
    _AutopilotGetWire,
    _AutopilotListWire,
    _AutopilotRunListPageWire,
    _AutopilotRunWire,
    _AutopilotTriggerWire,
    _AutopilotWire,
    trigger_from_wire,
)
from multica_py.config import ClientConfig, OperationOptions
from multica_py.entities.autopilots import (
    Autopilot,
    AutopilotRun,
    _coerce_json_value,
)
from multica_py.enums import AutopilotExecutionMode
from multica_py.exceptions import OutputShapeError
from multica_py.models.autopilots import (
    AutopilotListPage,
    AutopilotRunListPage,
    AutopilotSubscriber,
    AutopilotTrigger,
)
from multica_py.models.common import ActionResult
from multica_py.models.relations import (
    LazyCollection,
    OffsetPage,
)
from multica_py.resources._base import BaseResource
from multica_py.sentinels import Unset, UnsetType

__all__ = ["Autopilot", "AutopilotResource", "AutopilotRun", "_coerce_json_value"]


def _trigger_from_autopilot_get(stdout: bytes, command: str, trigger_id: str) -> AutopilotTrigger:
    wire = decode_json(stdout, _AutopilotGetWire, command=command)
    result = _autopilot_get_from_wire(wire)
    if result.triggers is msgspec.UNSET:
        raise OutputShapeError("Autopilot get response omitted triggers")
    for trigger in result.triggers:
        if trigger.id == trigger_id:
            return trigger
    raise OutputShapeError(f"Autopilot trigger {trigger_id!r} was not found")


class AutopilotResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def _relation_command(
        self, autopilot_id: str, relation_name: str
    ) -> Command[tuple[object, ...]]:
        command = self.get_command(autopilot_id)

        def finalize(autopilot: Autopilot) -> tuple[object, ...]:
            relation = cast("LazyCollection[object]", getattr(autopilot, relation_name))
            return tuple(relation.all())

        return command._map(finalize)

    def _runs_page_command(
        self, autopilot_id: str, limit: int | None, offset: int
    ) -> Command[OffsetPage[AutopilotRun]]:
        client = self._bound_client()
        command = client.autopilots.history_command(autopilot_id, limit=limit, offset=offset)
        plan = command._plan
        source_step = plan.steps[0]

        def decode_page(stdout: bytes, command_text: str) -> object:
            if source_step.decode is None:
                raise RuntimeError("autopilot history command has no decoder")
            wire_page = cast("_AutopilotRunListPageWire", source_step.decode(stdout, command_text))
            words = shlex.split(command_text)
            current_offset = (
                int(words[words.index("--offset") + 1]) if "--offset" in words else offset
            )
            page = _autopilot_run_list_page_from_wire(wire_page, limit=limit, offset=current_offset)
            return OffsetPage(
                items=tuple(run._with_client(client) for run in page.runs),
                total=page.total,
                limit=page.limit or (20 if limit is None else limit),
                offset=page.offset if page.offset is not None else current_offset,
                has_more=page.has_more,
            )

        return Command(
            _replace_plan(
                plan,
                steps=(replace(source_step, decode=decode_page),),
                finalize=lambda results: cast("OffsetPage[AutopilotRun]", results[0]),
            )
        )

    def _trigger_add_command(
        self,
        autopilot_id: str,
        *,
        title: str,
        kind: str,
        invalidate: Callable[[AutopilotTrigger], AutopilotTrigger],
        options: OperationOptions | None,
    ) -> Command[AutopilotTrigger]:
        return self.trigger_add_command(autopilot_id, title=title, kind=kind, options=options)._map(
            invalidate
        )

    def _trigger_update_command(
        self,
        autopilot_id: str,
        trigger_id: str,
        *,
        title: str | UnsetType,
        kind: str | UnsetType,
        invalidate: Callable[[AutopilotTrigger], AutopilotTrigger],
        options: OperationOptions | None,
    ) -> Command[AutopilotTrigger]:
        return self.trigger_update_command(
            autopilot_id, trigger_id, title=title, kind=kind, options=options
        )._map(invalidate)

    def _trigger_delete_command(
        self,
        autopilot_id: str,
        trigger_id: str,
        *,
        invalidate: Callable[[ActionResult[None]], ActionResult[None]],
        options: OperationOptions | None,
    ) -> Command[ActionResult[None]]:
        return self.trigger_delete_command(autopilot_id, trigger_id, options=options)._map(
            invalidate
        )

    def list_command(
        self, *, options: OperationOptions | None = None
    ) -> Command[AutopilotListPage[Autopilot]]:
        def finalize(page: _AutopilotListWire) -> AutopilotListPage[Autopilot]:
            return AutopilotListPage(
                items=tuple(
                    self._bind_autopilot(_autopilot_from_wire(item)) for item in page.autopilots
                ),
                total=page.total,
            )

        return self._decoded_command(
            ("autopilot", "list"), _AutopilotListWire, options=options
        )._map(finalize)

    def list(self, *, options: OperationOptions | None = None) -> AutopilotListPage[Autopilot]:
        return self.list_command(options=options).run()

    def get_command(
        self, autopilot_id: str, *, options: OperationOptions | None = None
    ) -> Command[Autopilot]:
        validate_nonblank(autopilot_id)

        def finalize(wire: _AutopilotGetWire) -> Autopilot:
            result = _autopilot_get_from_wire(wire)
            return self._bind_autopilot(
                result.data,
                triggers=result.triggers,
                subscribers=result.subscribers,
            )

        return self._decoded_command(
            ("autopilot", "get", autopilot_id), _AutopilotGetWire, options=options
        )._map(finalize)

    def get(self, autopilot_id: str, *, options: OperationOptions | None = None) -> Autopilot:
        return self.get_command(autopilot_id, options=options).run()

    def create_command(
        self,
        title: str,
        *,
        description: str | None = None,
        agent: str,
        execution_mode: AutopilotExecutionMode,
        priority: str = "none",
        project_id: str | None = None,
        issue_title_template: str | None = None,
        subscribers: tuple[str, ...] = (),
        options: OperationOptions | None = None,
    ) -> Command[Autopilot]:
        args = [
            "autopilot",
            "create",
            "--title",
            title,
            "--agent",
            agent,
            "--mode",
            execution_mode.value,
            "--priority",
            priority,
        ]
        if description is not None:
            args.extend(["--description", description])
        if project_id is not None:
            args.extend(["--project", project_id])
        if issue_title_template is not None:
            args.extend(["--issue-title-template", issue_title_template])
        if any(not ref.strip() for ref in subscribers):
            raise ValueError("subscribers must be nonblank")
        for ref in subscribers:
            args.extend(["--subscriber", ref])
        return self._decoded_command(tuple(args), _AutopilotWire, options=options)._map(
            self._bind_autopilot_wire
        )

    def create(
        self,
        title: str,
        *,
        description: str | None = None,
        agent: str,
        execution_mode: AutopilotExecutionMode,
        priority: str = "none",
        project_id: str | None = None,
        issue_title_template: str | None = None,
        subscribers: tuple[str, ...] = (),
        options: OperationOptions | None = None,
    ) -> Autopilot:
        return self.create_command(
            title,
            description=description,
            agent=agent,
            execution_mode=execution_mode,
            priority=priority,
            project_id=project_id,
            issue_title_template=issue_title_template,
            subscribers=subscribers,
            options=options,
        ).run()

    def update_command(
        self,
        autopilot_id: str,
        *,
        title: str | UnsetType = Unset,
        agent: str | UnsetType = Unset,
        priority: str | UnsetType = Unset,
        status: str | UnsetType = Unset,
        execution_mode: AutopilotExecutionMode | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        project_id: str | None | UnsetType = Unset,
        issue_title_template: str | None | UnsetType = Unset,
        subscribers: tuple[str, ...] | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[Autopilot]:
        validate_nonblank(autopilot_id)
        if (
            title is Unset
            and agent is Unset
            and priority is Unset
            and status is Unset
            and execution_mode is Unset
            and description is Unset
            and project_id is Unset
            and issue_title_template is Unset
            and subscribers is Unset
        ):
            return self.get_command(autopilot_id, options=options)
        for field_name, value in (
            ("title", title),
            ("agent", agent),
            ("priority", priority),
            ("status", status),
            ("execution_mode", execution_mode),
            ("subscribers", subscribers),
        ):
            if value is None:
                raise TypeError(f"{field_name} must be non-null")
        if subscribers is not Unset and any(not ref.strip() for ref in subscribers):
            raise ValueError("subscribers must be nonblank")
        args = ["autopilot", "update", autopilot_id]
        if title is not Unset:
            args.extend(["--title", title])
        if description is not Unset:
            args.extend(["--description", "" if description is None else description])
        if agent is not Unset:
            args.extend(["--agent", agent])
        if project_id is not Unset:
            args.extend(["--project", "" if project_id is None else project_id])
        if priority is not Unset:
            args.extend(["--priority", priority])
        if status is not Unset:
            args.extend(["--status", status])
        if execution_mode is not Unset:
            args.extend(["--mode", execution_mode.value])
        if issue_title_template is not Unset:
            args.extend(
                [
                    "--issue-title-template",
                    "" if issue_title_template is None else issue_title_template,
                ]
            )
        if subscribers is not Unset:
            if not subscribers:
                args.append("--clear-subscribers")
            else:
                for ref in subscribers:
                    args.extend(["--subscriber", ref])
        return self._decoded_command(tuple(args), _AutopilotWire, options=options)._map(
            self._bind_autopilot_wire
        )

    def update(
        self,
        autopilot_id: str,
        *,
        title: str | UnsetType = Unset,
        agent: str | UnsetType = Unset,
        priority: str | UnsetType = Unset,
        status: str | UnsetType = Unset,
        execution_mode: AutopilotExecutionMode | UnsetType = Unset,
        description: str | None | UnsetType = Unset,
        project_id: str | None | UnsetType = Unset,
        issue_title_template: str | None | UnsetType = Unset,
        subscribers: tuple[str, ...] | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Autopilot:
        return self.update_command(
            autopilot_id,
            title=title,
            agent=agent,
            priority=priority,
            status=status,
            execution_mode=execution_mode,
            description=description,
            project_id=project_id,
            issue_title_template=issue_title_template,
            subscribers=subscribers,
            options=options,
        ).run()

    def delete_command(
        self, autopilot_id: str, *, options: OperationOptions | None = None
    ) -> Command[ActionResult[None]]:
        return self._action_command(("autopilot", "delete", autopilot_id), options=options)

    def delete(
        self, autopilot_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.delete_command(autopilot_id, options=options).run()

    def trigger_command(
        self, autopilot_id: str, *, options: OperationOptions | None = None
    ) -> Command[AutopilotRun]:
        validate_nonblank(autopilot_id)
        return self._decoded_command(
            ("autopilot", "trigger", autopilot_id), _AutopilotRunWire, options=options
        )._map(self._bind_autopilot_run)

    def trigger(
        self, autopilot_id: str, *, options: OperationOptions | None = None
    ) -> AutopilotRun:
        return self.trigger_command(autopilot_id, options=options).run()

    def history_command(
        self,
        autopilot_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
        options: OperationOptions | None = None,
    ) -> Command[AutopilotRunListPage[AutopilotRun]]:
        if limit is not None and limit < 0:
            raise ValueError("limit must be nonnegative")
        if offset is not None and offset < 0:
            raise ValueError("offset must be nonnegative")
        args = ["autopilot", "runs", autopilot_id]
        if limit is not None:
            args.extend(["--limit", str(limit)])
        if offset is not None:
            args.extend(["--offset", str(offset)])

        def finalize(wire: _AutopilotRunListPageWire) -> AutopilotRunListPage[AutopilotRun]:
            page = _autopilot_run_list_page_from_wire(wire, limit=limit, offset=offset)
            return AutopilotRunListPage(
                items=tuple(run._with_client(self._client) for run in page.runs),
                total=page.total,
                limit=page.limit,
                offset=page.offset,
                has_more=page.has_more,
            )

        return self._decoded_command(tuple(args), _AutopilotRunListPageWire, options=options)._map(
            finalize
        )

    def history(
        self,
        autopilot_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
        options: OperationOptions | None = None,
    ) -> AutopilotRunListPage[AutopilotRun]:
        return self.history_command(autopilot_id, limit=limit, offset=offset, options=options).run()

    def trigger_add_command(
        self, autopilot_id: str, *, title: str, kind: str, options: OperationOptions | None = None
    ) -> Command[AutopilotTrigger]:
        _ = cast("object", AUTOPILOT_TRIGGER_ADD_BINDING)
        validate_nonblank(autopilot_id)
        validate_nonblank(title)
        if kind is None:
            raise TypeError("kind must be non-null")
        args = (
            "autopilot",
            "trigger-add",
            autopilot_id,
            "--title",
            title,
            "--kind",
            kind,
        )
        return self._decoded_command(args, _AutopilotTriggerWire, options=options)._map(
            trigger_from_wire
        )

    def trigger_add(
        self,
        autopilot_id: str,
        *,
        title: str,
        kind: str,
        options: OperationOptions | None = None,
    ) -> AutopilotTrigger:
        return self.trigger_add_command(autopilot_id, title=title, kind=kind, options=options).run()

    def trigger_update_command(
        self,
        autopilot_id: str,
        trigger_id: str,
        *,
        title: str | UnsetType = Unset,
        kind: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> Command[AutopilotTrigger]:
        _ = cast("object", AUTOPILOT_TRIGGER_UPDATE_BINDING)
        validate_nonblank(autopilot_id)
        validate_nonblank(trigger_id)
        if title is None:
            raise TypeError("title must be non-null")
        if kind is None:
            raise TypeError("kind must be non-null")
        if title is Unset and kind is Unset:
            get_args = ("autopilot", "get", autopilot_id, "--output", "json")
            return self._plan(
                steps=(
                    _Step(
                        get_args,
                        "run_bytes",
                        decode=lambda stdout, command: _trigger_from_autopilot_get(
                            stdout, command, trigger_id
                        ),
                    ),
                ),
                finalize=lambda results: cast("AutopilotTrigger", results[0]),
                options=options,
            )
        args = ["autopilot", "trigger-update", autopilot_id, trigger_id]
        if title is not msgspec.UNSET:
            args.extend(["--title", title])
        if kind is not msgspec.UNSET:
            args.extend(["--kind", kind])
        return self._decoded_command(tuple(args), _AutopilotTriggerWire, options=options)._map(
            trigger_from_wire
        )

    def trigger_update(
        self,
        autopilot_id: str,
        trigger_id: str,
        *,
        title: str | UnsetType = Unset,
        kind: str | UnsetType = Unset,
        options: OperationOptions | None = None,
    ) -> AutopilotTrigger:
        return self.trigger_update_command(
            autopilot_id, trigger_id, title=title, kind=kind, options=options
        ).run()

    def trigger_delete_command(
        self,
        autopilot_id: str,
        trigger_id: str,
        *,
        options: OperationOptions | None = None,
    ) -> Command[ActionResult[None]]:
        _ = cast("object", AUTOPILOT_TRIGGER_DELETE_BINDING)
        validate_nonblank(autopilot_id)
        validate_nonblank(trigger_id)
        return self._action_command(
            ("autopilot", "trigger-delete", autopilot_id, trigger_id), options=options
        )

    def trigger_delete(
        self, autopilot_id: str, trigger_id: str, *, options: OperationOptions | None = None
    ) -> ActionResult[None]:
        return self.trigger_delete_command(autopilot_id, trigger_id, options=options).run()

    def _bind_autopilot(
        self,
        autopilot: Autopilot,
        *,
        triggers: tuple[AutopilotTrigger, ...] | msgspec.UnsetType = msgspec.UNSET,
        subscribers: tuple[AutopilotSubscriber, ...] | msgspec.UnsetType = msgspec.UNSET,
    ) -> Autopilot:
        autopilot = autopilot._with_client(self._client)
        if triggers is not msgspec.UNSET:
            autopilot = msgspec.structs.replace(autopilot, triggers=triggers)
        if subscribers is not msgspec.UNSET:
            autopilot = msgspec.structs.replace(autopilot, subscribers=subscribers)
        return autopilot

    def _bind_autopilot_wire(self, wire: _AutopilotWire) -> Autopilot:
        return self._bind_autopilot(_autopilot_from_wire(wire))

    def _bind_autopilot_run(self, wire: _AutopilotRunWire) -> AutopilotRun:
        return _autopilot_run_from_wire(wire)._with_client(self._client)
