from __future__ import annotations

import datetime
import math
import shlex
from collections.abc import Callable
from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING, cast

import msgspec

from multica_py._generated.approved_sdk import (
    AUTOPILOT_TRIGGER_ADD_BINDING,
    AUTOPILOT_TRIGGER_DELETE_BINDING,
    AUTOPILOT_TRIGGER_UPDATE_BINDING,
    validate_nonblank,
)
from multica_py._internal.commands import Command, _replace_plan, _Step
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
from multica_py.config import ClientConfig
from multica_py.enums import AutopilotExecutionMode
from multica_py.exceptions import (
    DetachedEntityError,
    MissingRelationContextError,
    RelationPaginationError,
)
from multica_py.models._bound import _BoundEntity, _is_mapping, _runtime_state
from multica_py.models.autopilots import (
    AutopilotListPage,
    AutopilotRunListPage,
    AutopilotSubscriber,
    AutopilotTrigger,
    AutopilotTriggerCreate,
    AutopilotTriggerUpdate,
)
from multica_py.models.issue_activity import RunMessage
from multica_py.models.relations import (
    LazyCollection,
    OffsetLazyCollection,
    OffsetPage,
)
from multica_py.resources._base import BaseResource
from multica_py.types import JsonValue

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


def _coerce_json_value(value: object, *, field_name: str) -> JsonValue:
    if isinstance(value, float) and not math.isfinite(value):
        raise msgspec.ValidationError(f"{field_name} must contain only finite JSON numbers")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return tuple(_coerce_json_value(item, field_name=field_name) for item in value)
    if _is_mapping(value):
        result: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise msgspec.ValidationError(f"{field_name} object keys must be strings")
            result[key] = _coerce_json_value(item, field_name=field_name)
        return MappingProxyType(result)
    raise msgspec.ValidationError(f"{field_name} must contain only JSON values")


def _make_triggers_loader(
    client: MulticaClient | None, autopilot_id: str
) -> Callable[[], tuple[AutopilotTrigger, ...]]:
    def loader() -> tuple[AutopilotTrigger, ...]:
        if client is None:
            raise DetachedEntityError("Autopilot", autopilot_id, "triggers")
        fresh = client.autopilots.get(autopilot_id)
        relation = fresh.triggers
        if not relation.loaded:
            raise RelationPaginationError("Autopilot.triggers", "missing complete get seed")
        return relation.all()

    return loader


def _make_subscribers_loader(
    client: MulticaClient | None, autopilot_id: str
) -> Callable[[], tuple[AutopilotSubscriber, ...]]:
    def loader() -> tuple[AutopilotSubscriber, ...]:
        if client is None:
            raise DetachedEntityError("Autopilot", autopilot_id, "subscribers")
        fresh = client.autopilots.get(autopilot_id)
        relation = fresh.subscribers
        if not relation.loaded:
            raise RelationPaginationError("Autopilot.subscribers", "missing complete get seed")
        return relation.all()

    return loader


def _bound_relation_command(
    client: MulticaClient,
    autopilot_id: str,
    relation_name: str,
) -> Command[tuple[object, ...]]:
    command = client.autopilots.get_command(autopilot_id)
    plan = command._plan

    def finalize(results: tuple[object, ...]) -> tuple[object, ...]:
        autopilot = plan.finalize(results)
        relation = cast("LazyCollection[object]", getattr(autopilot, relation_name))
        if not relation.loaded:
            raise RelationPaginationError(f"Autopilot.{relation_name}", "missing complete get seed")
        return tuple(relation.all())

    return Command(_replace_plan(plan, finalize=finalize))


def _runs_page_command(
    client: MulticaClient, autopilot_id: str, limit: int | None, offset: int
) -> Command[OffsetPage[AutopilotRun]]:
    command = client.autopilots.history_command(autopilot_id, limit=limit, offset=offset)
    plan = command._plan
    source_step = plan.steps[0]

    def decode_page(stdout: bytes, command_text: str) -> object:
        if source_step.decode is None:
            raise RuntimeError("autopilot history command has no decoder")
        wire_page = cast("_AutopilotRunListPageWire", source_step.decode(stdout, command_text))
        words = shlex.split(command_text)
        current_offset = int(words[words.index("--offset") + 1]) if "--offset" in words else offset
        page = _autopilot_run_list_page_from_wire(
            wire_page,
            limit=limit,
            offset=current_offset,
        )
        return OffsetPage(
            items=tuple(run._with_client(client) for run in page.runs),
            total=page.total,
            limit=page.limit or (20 if limit is None else limit),
            offset=page.offset if page.offset is not None else current_offset,
            has_more=page.has_more,
        )

    def finalize(results: tuple[object, ...]) -> OffsetPage[AutopilotRun]:
        return cast("OffsetPage[AutopilotRun]", results[0])

    return Command(
        _replace_plan(
            plan,
            steps=(replace(source_step, decode=decode_page),),
            finalize=finalize,
        )
    )


class AutopilotRun(_BoundEntity):  # type: ignore[misc]
    id: str
    autopilot_id: str
    source: str
    status: str
    trigger_id: str | None = None
    issue_id: str | None = None
    task_id: str | None = None
    triggered_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None
    failure_reason: str | None = None
    reason_code: str | None = None
    trigger_payload: JsonValue | None = None
    result: JsonValue | None = None
    created_at: datetime.datetime | None = None

    _messages: LazyCollection[RunMessage] | None = msgspec.field(default=None, name="_messages")

    def __post_init__(self) -> None:
        # Frozen msgspec fields cannot be replaced from ``__post_init__`` on
        # Python 3.12. Keep a normalized private snapshot for the two public
        # JSON fields; the fixed runtime overlay makes the public constructor
        # as snapshot-safe as the wire/converter paths.
        trigger_payload = cast("object", object.__getattribute__(self, "trigger_payload"))
        runtime = _runtime_state(self)
        if trigger_payload is not None and "trigger_payload" not in runtime:
            self._set_runtime(
                "trigger_payload",
                _coerce_json_value(trigger_payload, field_name="trigger_payload"),
            )
        result = cast("object", object.__getattribute__(self, "result"))
        if result is not None and "result" not in runtime:
            self._set_runtime("result", _coerce_json_value(result, field_name="result"))

    @classmethod
    def _normalize_from_dict(cls, data: dict[str, object]) -> dict[str, object]:
        normalized: dict[str, object] = {}
        for key, value in data.items():
            normalized[key] = value
        for field_name in ("trigger_payload", "result"):
            value = normalized.get(field_name)
            if value is not None:
                normalized[field_name] = _coerce_json_value(value, field_name=field_name)
        return normalized

    @classmethod
    def _from_encoded_dict(cls, data: dict[str, object]) -> AutopilotRun:
        from multica_py._internal.wire_models import _autopilot_run_from_wire, _AutopilotRunWire

        wire = msgspec.convert(data, type=_AutopilotRunWire, strict=True)
        return _autopilot_run_from_wire(wire)

    _PUBLIC_FIELDS = (
        "id",
        "autopilot_id",
        "trigger_id",
        "source",
        "status",
        "issue_id",
        "task_id",
        "triggered_at",
        "completed_at",
        "failure_reason",
        "reason_code",
        "trigger_payload",
        "result",
        "created_at",
    )

    @property
    def messages(self) -> LazyCollection[RunMessage]:
        if self._messages is None:
            client = self._require_client(
                entity_type="AutopilotRun", entity_id=self.id, relation_name="messages"
            )
            if self.task_id is None:

                def missing_context() -> tuple[RunMessage, ...]:
                    raise MissingRelationContextError(
                        "AutopilotRun", self.id, "messages", "task_id"
                    )

                def missing_context_command() -> Command[tuple[RunMessage, ...]]:
                    raise MissingRelationContextError(
                        "AutopilotRun", self.id, "messages", "task_id"
                    )

                self._set_runtime(
                    "_messages",
                    LazyCollection[RunMessage](
                        missing_context, command_loader=missing_context_command
                    ),
                )
            else:
                task_id = self.task_id
                issue_id = self.issue_id
                issues = client.issues

                def loader() -> tuple[RunMessage, ...]:
                    return issues.run_messages(task_id, issue_id=issue_id)

                self._set_runtime(
                    "_messages",
                    LazyCollection[RunMessage](
                        loader,
                        command_loader=lambda: issues.run_messages_command(
                            task_id, issue_id=issue_id
                        ),
                    ),
                )
        return self._messages  # type: ignore[return-value]

    def messages_command(self) -> Command[tuple[RunMessage, ...]]:
        client = self._require_client(
            entity_type="AutopilotRun", entity_id=self.id, relation_name="messages"
        )
        if self.task_id is None:
            raise MissingRelationContextError("AutopilotRun", self.id, "messages", "task_id")
        task_id = self.task_id
        issue_id = self.issue_id
        return client.issues.run_messages_command(task_id, issue_id=issue_id)


class Autopilot(_BoundEntity):  # type: ignore[misc]
    id: str
    workspace_id: str
    title: str
    assignee_type: str
    assignee_id: str
    status: str
    execution_mode: str
    created_by_type: str
    created_by_id: str
    description: str | None = None
    project_id: str | None = None
    issue_title_template: str | None = None
    last_run_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    trigger_kinds: tuple[str, ...] = ()
    next_run_at: datetime.datetime | None = None
    last_run_status: str | None = None
    subscriber_snapshot: tuple[AutopilotSubscriber, ...] = msgspec.field(
        default_factory=tuple, name="subscribers"
    )
    can_write: bool | None = None
    can_manage_access: bool | None = None

    _triggers: LazyCollection[AutopilotTrigger] | None = msgspec.field(
        default=None, name="_triggers"
    )
    _subscribers: LazyCollection[AutopilotSubscriber] | None = msgspec.field(
        default=None, name="_subscribers"
    )
    _runs: OffsetLazyCollection[AutopilotRun] | None = msgspec.field(default=None, name="_runs")
    if TYPE_CHECKING:

        @property
        def triggers(self) -> LazyCollection[AutopilotTrigger]: ...

        @property
        def subscribers(self) -> LazyCollection[AutopilotSubscriber]: ...

        def __init__(self, **kwargs: object) -> None: ...

    else:
        triggers: tuple[AutopilotTrigger, ...] | msgspec.UnsetType = msgspec.field(
            default=msgspec.UNSET, name="_triggers_seed"
        )
        subscribers: tuple[AutopilotSubscriber, ...] | msgspec.UnsetType = msgspec.field(
            default=msgspec.UNSET, name="_subscribers_seed"
        )

    _RUNTIME_INIT_FIELDS = ("triggers", "subscribers")

    _PUBLIC_FIELDS = (
        "id",
        "workspace_id",
        "title",
        "description",
        "project_id",
        "assignee_type",
        "assignee_id",
        "status",
        "execution_mode",
        "issue_title_template",
        "created_by_type",
        "created_by_id",
        "last_run_at",
        "created_at",
        "updated_at",
        "trigger_kinds",
        "next_run_at",
        "last_run_status",
        "subscriber_snapshot",
        "can_write",
        "can_manage_access",
    )

    def __post_init__(self) -> None:
        client = cast("MulticaClient | None", object.__getattribute__(self, "_client"))
        autopilot_id = self.id
        triggers = cast(
            "tuple[AutopilotTrigger, ...] | msgspec.UnsetType",
            object.__getattribute__(self, "triggers"),
        )
        if triggers is not msgspec.UNSET:
            _triggers: LazyCollection[AutopilotTrigger] = LazyCollection(
                _make_triggers_loader(client, autopilot_id),
                initial=triggers,
                command_loader=(
                    None
                    if client is None
                    else lambda: cast(
                        "Command[tuple[AutopilotTrigger, ...]]",
                        _bound_relation_command(client, autopilot_id, "triggers"),
                    )
                ),
            )
            self._set_runtime("_triggers", _triggers)

        subscribers = cast(
            "tuple[AutopilotSubscriber, ...] | msgspec.UnsetType",
            object.__getattribute__(self, "subscribers"),
        )
        if subscribers is not msgspec.UNSET:
            _subscribers: LazyCollection[AutopilotSubscriber] = LazyCollection(
                _make_subscribers_loader(client, autopilot_id),
                initial=subscribers,
                command_loader=(
                    None
                    if client is None
                    else lambda: cast(
                        "Command[tuple[AutopilotSubscriber, ...]]",
                        _bound_relation_command(client, autopilot_id, "subscribers"),
                    )
                ),
            )
            self._set_runtime("_subscribers", _subscribers)

    def __getattribute__(self, name: str) -> object:
        if name == "triggers":
            relation = self._triggers
            if relation is None:
                client = cast("MulticaClient | None", object.__getattribute__(self, "_client"))
                autopilot_id = cast("str", object.__getattribute__(self, "id"))
                relation = LazyCollection(_make_triggers_loader(client, autopilot_id))
                if client is not None:
                    relation = LazyCollection(
                        _make_triggers_loader(client, autopilot_id),
                        command_loader=lambda: cast(
                            "Command[tuple[AutopilotTrigger, ...]]",
                            _bound_relation_command(
                                cast("MulticaClient", client), autopilot_id, "triggers"
                            ),
                        ),
                    )
                self._set_runtime("_triggers", relation)
            return relation
        if name == "subscribers":
            subscriber_relation = self._subscribers
            if subscriber_relation is None:
                client = cast("MulticaClient | None", object.__getattribute__(self, "_client"))
                autopilot_id = cast("str", object.__getattribute__(self, "id"))
                subscriber_relation = LazyCollection(_make_subscribers_loader(client, autopilot_id))
                if client is not None:
                    subscriber_relation = LazyCollection(
                        _make_subscribers_loader(client, autopilot_id),
                        command_loader=lambda: cast(
                            "Command[tuple[AutopilotSubscriber, ...]]",
                            _bound_relation_command(client, autopilot_id, "subscribers"),
                        ),
                    )
                self._set_runtime("_subscribers", subscriber_relation)
            return subscriber_relation
        return super().__getattribute__(name)

    def _with_client(self, client: MulticaClient | None) -> Autopilot:
        if client is None or client is self._client:
            return self
        result = super()._with_client(client)
        autopilot_id = self.id
        triggers = cast(
            "LazyCollection[AutopilotTrigger] | None",
            _runtime_state(self).get("_triggers"),
        )
        if triggers is not None:
            trigger_initial = triggers.all() if triggers.loaded else None
            result._set_runtime(
                "_triggers",
                LazyCollection(
                    _make_triggers_loader(client, autopilot_id),
                    initial=trigger_initial,
                    command_loader=lambda: cast(
                        "Command[tuple[AutopilotTrigger, ...]]",
                        _bound_relation_command(client, autopilot_id, "triggers"),
                    ),
                ),
            )
        subscribers = cast(
            "LazyCollection[AutopilotSubscriber] | None",
            _runtime_state(self).get("_subscribers"),
        )
        if subscribers is not None:
            subscriber_initial = subscribers.all() if subscribers.loaded else None
            result._set_runtime(
                "_subscribers",
                LazyCollection(
                    _make_subscribers_loader(client, autopilot_id),
                    initial=subscriber_initial,
                    command_loader=lambda: cast(
                        "Command[tuple[AutopilotSubscriber, ...]]",
                        _bound_relation_command(client, autopilot_id, "subscribers"),
                    ),
                ),
            )
        return result

    @property
    def runs(self) -> OffsetLazyCollection[AutopilotRun]:
        if self._runs is None:
            client = self._require_client(
                entity_type="Autopilot", entity_id=self.id, relation_name="runs"
            )
            autopilot_id = self.id

            def page_loader(limit: int | None = None, offset: int = 0) -> OffsetPage[AutopilotRun]:
                page: AutopilotRunListPage[AutopilotRun] = client.autopilots.history(
                    autopilot_id, limit=20 if limit is None else limit, offset=offset
                )
                return OffsetPage(
                    items=page.runs,
                    total=page.total,
                    limit=page.limit or 20,
                    offset=page.offset or offset,
                    has_more=page.has_more,
                )

            self._set_runtime(
                "_runs",
                OffsetLazyCollection(
                    page_loader,
                    default_limit=20,
                    page_command_loader=lambda limit, offset: _runs_page_command(
                        client, autopilot_id, limit, offset
                    ),
                ),
            )
        return self._runs  # type: ignore[return-value]

    def trigger_add(self, request: AutopilotTriggerCreate) -> AutopilotTrigger:
        return self.trigger_add_command(request).run()

    def trigger_add_command(self, request: AutopilotTriggerCreate) -> Command[AutopilotTrigger]:
        validate_nonblank(self.id)
        validate_nonblank(request.title)
        client = self._require_client(
            entity_type="Autopilot", entity_id=self.id, relation_name="triggers"
        )
        args = (
            "autopilot",
            "trigger-add",
            self.id,
            "--title",
            request.title,
            "--kind",
            request.kind,
        )
        plan_args, decode = client.autopilots._plan_decode(args, _AutopilotTriggerWire)

        def finalize(results: tuple[object, ...]) -> AutopilotTrigger:
            result = trigger_from_wire(cast("_AutopilotTriggerWire", results[0]))
            self.triggers.invalidate()
            return result

        return client.autopilots._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),), finalize=finalize
        )

    def trigger_update(self, trigger_id: str, request: AutopilotTriggerUpdate) -> AutopilotTrigger:
        return self.trigger_update_command(trigger_id, request).run()

    def trigger_update_command(
        self, trigger_id: str, request: AutopilotTriggerUpdate
    ) -> Command[AutopilotTrigger]:
        validate_nonblank(self.id)
        validate_nonblank(trigger_id)
        client = self._require_client(
            entity_type="Autopilot", entity_id=self.id, relation_name="triggers"
        )
        args = ["autopilot", "trigger-update", self.id, trigger_id]
        if request.title is not msgspec.UNSET:
            args.extend(["--title", request.title])
        if request.kind is not msgspec.UNSET:
            args.extend(["--kind", request.kind])
        plan_args, decode = client.autopilots._plan_decode(tuple(args), _AutopilotTriggerWire)

        def finalize(results: tuple[object, ...]) -> AutopilotTrigger:
            result = trigger_from_wire(cast("_AutopilotTriggerWire", results[0]))
            self.triggers.invalidate()
            return result

        return client.autopilots._plan(
            steps=(_Step(plan_args, "run_bytes", decode=decode),), finalize=finalize
        )

    def trigger_delete(self, trigger_id: str) -> None:
        self.trigger_delete_command(trigger_id).run()

    def trigger_delete_command(self, trigger_id: str) -> Command[None]:
        validate_nonblank(self.id)
        validate_nonblank(trigger_id)
        client = self._require_client(
            entity_type="Autopilot", entity_id=self.id, relation_name="triggers"
        )
        args = ("autopilot", "trigger-delete", self.id, trigger_id)
        return client.autopilots._plan(
            steps=(_Step(args, "run_text"),),
            finalize=lambda results: self.triggers.invalidate(),
        )


class AutopilotResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list_command(self) -> Command[AutopilotListPage[Autopilot]]:
        args, decode = self._plan_decode(("autopilot", "list"), _AutopilotListWire)

        def finalize(results: tuple[object, ...]) -> AutopilotListPage[Autopilot]:
            page = cast("_AutopilotListWire", results[0])
            return AutopilotListPage(
                autopilots=tuple(
                    self._bind_autopilot(_autopilot_from_wire(item)) for item in page.autopilots
                ),
                total=page.total,
            )

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def list(self) -> AutopilotListPage[Autopilot]:
        return self.list_command().run()

    def get_command(self, autopilot_id: str) -> Command[Autopilot]:
        validate_nonblank(autopilot_id)
        args, decode = self._plan_decode(("autopilot", "get", autopilot_id), _AutopilotGetWire)

        def finalize(results: tuple[object, ...]) -> Autopilot:
            result = _autopilot_get_from_wire(cast("_AutopilotGetWire", results[0]))
            return self._bind_autopilot(
                result.data,
                triggers=result.triggers,
                subscribers=result.subscribers,
            )

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def get(self, autopilot_id: str) -> Autopilot:
        return self.get_command(autopilot_id).run()

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
        plan_args, decode = self._plan_decode(tuple(args), _AutopilotWire)

        def finalize(results: tuple[object, ...]) -> Autopilot:
            return self._bind_autopilot(_autopilot_from_wire(cast("_AutopilotWire", results[0])))

        return self._plan(steps=(_Step(plan_args, "run_bytes", decode=decode),), finalize=finalize)

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
        ).run()

    def update_command(
        self,
        autopilot_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        agent: str | None = None,
        project_id: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        execution_mode: AutopilotExecutionMode | None = None,
        issue_title_template: str | None = None,
        subscribers: tuple[str, ...] | None = None,
        clear_subscribers: bool = False,
    ) -> Command[Autopilot]:
        if clear_subscribers and subscribers is not None:
            raise ValueError("clear_subscribers and subscribers are mutually exclusive")
        if subscribers is not None and any(not ref.strip() for ref in subscribers):
            raise ValueError("subscribers must be nonblank")
        args = ["autopilot", "update", autopilot_id]
        if title is not None:
            args.extend(["--title", title])
        if description is not None:
            args.extend(["--description", description])
        if agent is not None:
            args.extend(["--agent", agent])
        if project_id is not None:
            args.extend(["--project", project_id])
        if priority is not None:
            args.extend(["--priority", priority])
        if status is not None:
            args.extend(["--status", status])
        if execution_mode is not None:
            args.extend(["--mode", execution_mode.value])
        if issue_title_template is not None:
            args.extend(["--issue-title-template", issue_title_template])
        if clear_subscribers:
            args.append("--clear-subscribers")
        elif subscribers is not None:
            for ref in subscribers:
                args.extend(["--subscriber", ref])
        plan_args, decode = self._plan_decode(tuple(args), _AutopilotWire)

        def finalize(results: tuple[object, ...]) -> Autopilot:
            return self._bind_autopilot(_autopilot_from_wire(cast("_AutopilotWire", results[0])))

        return self._plan(steps=(_Step(plan_args, "run_bytes", decode=decode),), finalize=finalize)

    def update(
        self,
        autopilot_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        agent: str | None = None,
        project_id: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        execution_mode: AutopilotExecutionMode | None = None,
        issue_title_template: str | None = None,
        subscribers: tuple[str, ...] | None = None,
        clear_subscribers: bool = False,
    ) -> Autopilot:
        return self.update_command(
            autopilot_id,
            title=title,
            description=description,
            agent=agent,
            project_id=project_id,
            priority=priority,
            status=status,
            execution_mode=execution_mode,
            issue_title_template=issue_title_template,
            subscribers=subscribers,
            clear_subscribers=clear_subscribers,
        ).run()

    def delete_command(self, autopilot_id: str) -> Command[None]:
        return self._plan(
            steps=(_Step(("autopilot", "delete", autopilot_id), "run_text"),),
            finalize=lambda results: None,
        )

    def delete(self, autopilot_id: str) -> None:
        self.delete_command(autopilot_id).run()

    def trigger_command(self, autopilot_id: str) -> Command[AutopilotRun]:
        validate_nonblank(autopilot_id)
        args, decode = self._plan_decode(("autopilot", "trigger", autopilot_id), _AutopilotRunWire)

        def finalize(results: tuple[object, ...]) -> AutopilotRun:
            run = _autopilot_run_from_wire(cast("_AutopilotRunWire", results[0]))
            return run._with_client(self._client)

        return self._plan(steps=(_Step(args, "run_bytes", decode=decode),), finalize=finalize)

    def trigger(self, autopilot_id: str) -> AutopilotRun:
        return self.trigger_command(autopilot_id).run()

    def history_command(
        self,
        autopilot_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
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
        plan_args, decode = self._plan_decode(tuple(args), _AutopilotRunListPageWire)

        def finalize(results: tuple[object, ...]) -> AutopilotRunListPage[AutopilotRun]:
            page = _autopilot_run_list_page_from_wire(
                cast("_AutopilotRunListPageWire", results[0]), limit=limit, offset=offset
            )
            return AutopilotRunListPage(
                runs=tuple(run._with_client(self._client) for run in page.runs),
                total=page.total,
                limit=page.limit,
                offset=page.offset,
                has_more=page.has_more,
            )

        return self._plan(steps=(_Step(plan_args, "run_bytes", decode=decode),), finalize=finalize)

    def history(
        self,
        autopilot_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AutopilotRunListPage[AutopilotRun]:
        return self.history_command(autopilot_id, limit=limit, offset=offset).run()

    def trigger_add_command(
        self, autopilot_id: str, request: AutopilotTriggerCreate
    ) -> Command[AutopilotTrigger]:
        _ = cast("object", AUTOPILOT_TRIGGER_ADD_BINDING)
        validate_nonblank(autopilot_id)
        validate_nonblank(request.title)
        args = (
            "autopilot",
            "trigger-add",
            autopilot_id,
            "--title",
            request.title,
            "--kind",
            request.kind,
        )
        plan_args, decode = self._plan_decode(args, _AutopilotTriggerWire)

        def finalize(results: tuple[object, ...]) -> AutopilotTrigger:
            return trigger_from_wire(cast("_AutopilotTriggerWire", results[0]))

        return self._plan(steps=(_Step(plan_args, "run_bytes", decode=decode),), finalize=finalize)

    def trigger_add(self, autopilot_id: str, request: AutopilotTriggerCreate) -> AutopilotTrigger:
        return self.trigger_add_command(autopilot_id, request).run()

    def trigger_update_command(
        self,
        autopilot_id: str,
        trigger_id: str,
        request: AutopilotTriggerUpdate,
    ) -> Command[AutopilotTrigger]:
        _ = cast("object", AUTOPILOT_TRIGGER_UPDATE_BINDING)
        validate_nonblank(autopilot_id)
        validate_nonblank(trigger_id)
        args = ["autopilot", "trigger-update", autopilot_id, trigger_id]
        if request.title is not msgspec.UNSET:
            args.extend(["--title", request.title])
        if request.kind is not msgspec.UNSET:
            args.extend(["--kind", request.kind])
        plan_args, decode = self._plan_decode(tuple(args), _AutopilotTriggerWire)

        def finalize(results: tuple[object, ...]) -> AutopilotTrigger:
            return trigger_from_wire(cast("_AutopilotTriggerWire", results[0]))

        return self._plan(steps=(_Step(plan_args, "run_bytes", decode=decode),), finalize=finalize)

    def trigger_update(
        self,
        autopilot_id: str,
        trigger_id: str,
        request: AutopilotTriggerUpdate,
    ) -> AutopilotTrigger:
        return self.trigger_update_command(autopilot_id, trigger_id, request).run()

    def trigger_delete_command(self, autopilot_id: str, trigger_id: str) -> Command[None]:
        _ = cast("object", AUTOPILOT_TRIGGER_DELETE_BINDING)
        validate_nonblank(autopilot_id)
        validate_nonblank(trigger_id)
        return self._plan(
            steps=(_Step(("autopilot", "trigger-delete", autopilot_id, trigger_id), "run_text"),),
            finalize=lambda results: None,
        )

    def trigger_delete(self, autopilot_id: str, trigger_id: str) -> None:
        self.trigger_delete_command(autopilot_id, trigger_id).run()

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
