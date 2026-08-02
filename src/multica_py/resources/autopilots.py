from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import msgspec

from multica_py._generated.approved_sdk import (
    AUTOPILOT_TRIGGER_ADD_BINDING,
    AUTOPILOT_TRIGGER_DELETE_BINDING,
    AUTOPILOT_TRIGGER_UPDATE_BINDING,
    validate_nonblank,
)
from multica_py._internal.transport import CliTransport
from multica_py._internal.wire_models import (
    AutopilotGetWire,
    AutopilotListWire,
    AutopilotRunListPageWire,
    AutopilotRunWire,
    AutopilotTriggerWire,
    AutopilotWire,
    autopilot_data_from_wire,
    autopilot_get_from_wire,
    autopilot_run_data_from_model,
    autopilot_run_from_wire,
    autopilot_run_list_page_from_wire,
    trigger_from_wire,
)
from multica_py.config import ClientConfig
from multica_py.enums import AutopilotExecutionMode
from multica_py.exceptions import MissingRelationContextError, RelationPaginationError
from multica_py.models import ResourceEntity
from multica_py.models.autopilots import (
    Autopilot as AutopilotRecord,
)
from multica_py.models.autopilots import (
    AutopilotData,
    AutopilotListPage,
    AutopilotRunData,
    AutopilotRunListPage,
    AutopilotSubscriber,
    AutopilotTrigger,
    AutopilotTriggerCreate,
    AutopilotTriggerUpdate,
)
from multica_py.models.issue_activity import RunMessage
from multica_py.models.relations import LazyCollection, OffsetLazyCollection, OffsetPage
from multica_py.resources._base import BaseResource

if TYPE_CHECKING:
    from multica_py.client import MulticaClient


def _autopilot_data_from_model(autopilot: AutopilotRecord) -> AutopilotData:
    return AutopilotData(
        id=autopilot.id,
        workspace_id=autopilot.workspace_id,
        title=autopilot.title,
        description=autopilot.description,
        project_id=autopilot.project_id,
        assignee_type=autopilot.assignee_type,
        assignee_id=autopilot.assignee_id,
        status=autopilot.status,
        execution_mode=autopilot.execution_mode,
        issue_title_template=autopilot.issue_title_template,
        created_by_type=autopilot.created_by_type,
        created_by_id=autopilot.created_by_id,
        last_run_at=autopilot.last_run_at,
        created_at=autopilot.created_at,
        updated_at=autopilot.updated_at,
        trigger_kinds=autopilot.trigger_kinds,
        next_run_at=autopilot.next_run_at,
        last_run_status=autopilot.last_run_status,
        subscriber_snapshot=autopilot.subscribers,
        can_write=autopilot.can_write,
        can_manage_access=autopilot.can_manage_access,
    )


class AutopilotRunEntity(ResourceEntity[AutopilotRunData]):
    def __init__(self, data: AutopilotRunData, client: MulticaClient | None = None) -> None:
        super().__init__(data, client=client)
        self._messages: LazyCollection[RunMessage] | None = None

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def autopilot_id(self) -> str:
        return self._data.autopilot_id

    @property
    def trigger_id(self) -> str | None:
        return self._data.trigger_id

    @property
    def source(self) -> str:
        return self._data.source

    @property
    def status(self) -> str:
        return self._data.status

    @property
    def issue_id(self) -> str | None:
        return self._data.issue_id

    @property
    def task_id(self) -> str | None:
        return self._data.task_id

    @property
    def messages(self) -> LazyCollection[RunMessage]:
        if self._messages is None:
            client = self._require_client(
                entity_type="AutopilotRunEntity", entity_id=self._data.id, relation_name="messages"
            )
            if self._data.task_id is None:

                def missing_context() -> tuple[RunMessage, ...]:
                    raise MissingRelationContextError(
                        "AutopilotRunEntity", self._data.id, "messages", "task_id"
                    )

                self._messages = LazyCollection(missing_context)
            else:
                task_id = self._data.task_id
                issue_id = self._data.issue_id

                def loader() -> tuple[RunMessage, ...]:
                    return client.issues.run_messages(task_id, issue_id=issue_id)

                self._messages = LazyCollection(loader)
        return self._messages


class AutopilotEntity(ResourceEntity[AutopilotData]):
    def __init__(
        self,
        data: AutopilotData,
        client: MulticaClient | None = None,
        *,
        triggers: tuple[AutopilotTrigger, ...] | msgspec.UnsetType = msgspec.UNSET,
        subscribers: tuple[AutopilotSubscriber, ...] | msgspec.UnsetType = msgspec.UNSET,
    ) -> None:
        super().__init__(data, client=client)
        self._triggers: LazyCollection[AutopilotTrigger] | None = None
        self._subscribers: LazyCollection[AutopilotSubscriber] | None = None
        self._runs: OffsetLazyCollection[AutopilotRunEntity] | None = None
        if triggers is not msgspec.UNSET:
            self._triggers = LazyCollection(self._load_triggers, initial=triggers)
        if subscribers is not msgspec.UNSET:
            self._subscribers = LazyCollection(self._load_subscribers, initial=subscribers)

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def workspace_id(self) -> str:
        return self._data.workspace_id

    @property
    def title(self) -> str:
        return self._data.title

    @property
    def description(self) -> str | None:
        return self._data.description

    @property
    def project_id(self) -> str | None:
        return self._data.project_id

    @property
    def assignee_type(self) -> str:
        return self._data.assignee_type

    @property
    def assignee_id(self) -> str:
        return self._data.assignee_id

    @property
    def status(self) -> str:
        return self._data.status

    @property
    def execution_mode(self) -> str:
        return self._data.execution_mode

    @property
    def issue_title_template(self) -> str | None:
        return self._data.issue_title_template

    @property
    def created_by_type(self) -> str:
        return self._data.created_by_type

    @property
    def created_by_id(self) -> str:
        return self._data.created_by_id

    @property
    def last_run_at(self) -> datetime.datetime | None:
        return self._data.last_run_at

    @property
    def created_at(self) -> datetime.datetime | None:
        return self._data.created_at

    @property
    def updated_at(self) -> datetime.datetime | None:
        return self._data.updated_at

    @property
    def trigger_kinds(self) -> tuple[str, ...]:
        return self._data.trigger_kinds

    @property
    def next_run_at(self) -> datetime.datetime | None:
        return self._data.next_run_at

    @property
    def last_run_status(self) -> str | None:
        return self._data.last_run_status

    @property
    def subscriber_snapshot(self) -> tuple[AutopilotSubscriber, ...]:
        return self._data.subscriber_snapshot

    @property
    def can_write(self) -> bool | None:
        return self._data.can_write

    @property
    def can_manage_access(self) -> bool | None:
        return self._data.can_manage_access

    def _check_client(self, relation_name: str) -> MulticaClient:
        return self._require_client(
            entity_type="AutopilotEntity", entity_id=self._data.id, relation_name=relation_name
        )

    def _load_triggers(self) -> tuple[AutopilotTrigger, ...]:
        client = self._check_client("triggers")
        fresh = client.autopilots.get(self._data.id)
        relation = fresh.triggers
        if not relation.loaded:
            raise RelationPaginationError("Autopilot.triggers", "missing complete get seed")
        return relation.all()

    def _load_subscribers(self) -> tuple[AutopilotSubscriber, ...]:
        client = self._check_client("subscribers")
        fresh = client.autopilots.get(self._data.id)
        relation = fresh.subscribers
        if not relation.loaded:
            raise RelationPaginationError("Autopilot.subscribers", "missing complete get seed")
        return relation.all()

    @property
    def triggers(self) -> LazyCollection[AutopilotTrigger]:
        if self._triggers is None:
            self._triggers = LazyCollection(self._load_triggers)
        return self._triggers

    @property
    def subscribers(self) -> LazyCollection[AutopilotSubscriber]:
        if self._subscribers is None:
            self._subscribers = LazyCollection(self._load_subscribers)
        return self._subscribers

    @property
    def runs(self) -> OffsetLazyCollection[AutopilotRunEntity]:
        if self._runs is None:
            client = self._check_client("runs")
            autopilot_id = self._data.id

            def page_loader(
                limit: int | None = None, offset: int = 0
            ) -> OffsetPage[AutopilotRunEntity]:
                page: AutopilotRunListPage[AutopilotRunEntity] = client.autopilots.history(
                    autopilot_id, limit=20 if limit is None else limit, offset=offset
                )
                return OffsetPage(
                    items=page.runs,
                    total=page.total,
                    limit=page.limit or 20,
                    offset=page.offset or offset,
                    has_more=page.has_more,
                )

            self._runs = OffsetLazyCollection(page_loader, default_limit=20)
        return self._runs

    def trigger_add(self, request: AutopilotTriggerCreate) -> AutopilotTrigger:
        client = self._check_client("triggers")
        result = client.autopilots.trigger_add(self.id, request)
        self.triggers.invalidate()
        return result

    def trigger_update(self, trigger_id: str, request: AutopilotTriggerUpdate) -> AutopilotTrigger:
        client = self._check_client("triggers")
        result = client.autopilots.trigger_update(self.id, trigger_id, request)
        self.triggers.invalidate()
        return result

    def trigger_delete(self, trigger_id: str) -> None:
        client = self._check_client("triggers")
        client.autopilots.trigger_delete(self.id, trigger_id)
        self.triggers.invalidate()


class AutopilotResource(BaseResource):
    def __init__(self, transport: CliTransport, config: ClientConfig) -> None:
        super().__init__(transport, config)

    def list(self) -> AutopilotListPage[AutopilotEntity]:
        page = self._run_json_decode(("autopilot", "list"), AutopilotListWire)
        return AutopilotListPage(
            autopilots=tuple(
                self._bind_autopilot(autopilot_data_from_wire(item)) for item in page.autopilots
            ),
            total=page.total,
        )

    def get(self, autopilot_id: str) -> AutopilotEntity:
        validate_nonblank(autopilot_id)
        result = autopilot_get_from_wire(
            self._run_json_decode(("autopilot", "get", autopilot_id), AutopilotGetWire)
        )
        return self._bind_autopilot(
            result.data,
            triggers=result.triggers,
            subscribers=result.subscribers,
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
    ) -> AutopilotEntity:
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
        return self._bind_autopilot(
            autopilot_data_from_wire(self._run_json_decode(tuple(args), AutopilotWire))
        )

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
    ) -> AutopilotEntity:
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
        return self._bind_autopilot(
            autopilot_data_from_wire(self._run_json_decode(tuple(args), AutopilotWire))
        )

    def delete(self, autopilot_id: str) -> None:
        self._transport.run_text(("autopilot", "delete", autopilot_id))

    def trigger(self, autopilot_id: str) -> AutopilotRunEntity:
        validate_nonblank(autopilot_id)
        run = autopilot_run_from_wire(
            self._run_json_decode(("autopilot", "trigger", autopilot_id), AutopilotRunWire)
        )
        return self._bind_run(autopilot_run_data_from_model(run))

    def history(
        self,
        autopilot_id: str,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> AutopilotRunListPage[AutopilotRunEntity]:
        if limit is not None and limit < 0:
            raise ValueError("limit must be nonnegative")
        if offset is not None and offset < 0:
            raise ValueError("offset must be nonnegative")
        args = ["autopilot", "runs", autopilot_id]
        if limit is not None:
            args.extend(["--limit", str(limit)])
        if offset is not None:
            args.extend(["--offset", str(offset)])
        page = self._run_json_decode(tuple(args), AutopilotRunListPageWire)
        adapted = autopilot_run_list_page_from_wire(page, limit=limit, offset=offset)
        return AutopilotRunListPage(
            runs=tuple(self._bind_run(autopilot_run_data_from_model(run)) for run in adapted.runs),
            total=adapted.total,
            limit=adapted.limit,
            offset=adapted.offset,
            has_more=adapted.has_more,
        )

    def trigger_add(self, autopilot_id: str, request: AutopilotTriggerCreate) -> AutopilotTrigger:
        _ = AUTOPILOT_TRIGGER_ADD_BINDING
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
        return trigger_from_wire(self._run_json_decode(args, AutopilotTriggerWire))

    def trigger_update(
        self,
        autopilot_id: str,
        trigger_id: str,
        request: AutopilotTriggerUpdate,
    ) -> AutopilotTrigger:
        _ = AUTOPILOT_TRIGGER_UPDATE_BINDING
        validate_nonblank(autopilot_id)
        validate_nonblank(trigger_id)
        args = ["autopilot", "trigger-update", autopilot_id, trigger_id]
        if request.title is not msgspec.UNSET:
            args.extend(["--title", request.title])
        if request.kind is not msgspec.UNSET:
            args.extend(["--kind", request.kind])
        return trigger_from_wire(self._run_json_decode(tuple(args), AutopilotTriggerWire))

    def trigger_delete(self, autopilot_id: str, trigger_id: str) -> None:
        _ = AUTOPILOT_TRIGGER_DELETE_BINDING
        validate_nonblank(autopilot_id)
        validate_nonblank(trigger_id)
        self._transport.run_text(("autopilot", "trigger-delete", autopilot_id, trigger_id))

    def _bind_autopilot(
        self,
        data: AutopilotData,
        *,
        triggers: tuple[AutopilotTrigger, ...] | msgspec.UnsetType = msgspec.UNSET,
        subscribers: tuple[AutopilotSubscriber, ...] | msgspec.UnsetType = msgspec.UNSET,
    ) -> AutopilotEntity:
        return AutopilotEntity(
            data,
            client=self._client,
            triggers=triggers,
            subscribers=subscribers,
        )

    def _bind_run(self, data: AutopilotRunData) -> AutopilotRunEntity:
        return AutopilotRunEntity(data, client=self._client)
