from __future__ import annotations

import dataclasses
import datetime
import inspect
import threading
import types
from typing import Literal, cast, get_type_hints
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.exceptions import MissingRelationContextError
from multica_py.models.autopilots import (
    AutopilotData,
    AutopilotListPage,
    AutopilotRunData,
    AutopilotRunListPage,
    AutopilotTrigger,
    AutopilotTriggerCreate,
    AutopilotTriggerUpdate,
)
from multica_py.models.issue_activity import RunMessage
from multica_py.models.relations import LazyCollection, LazyMapping
from multica_py.resources.autopilots import AutopilotEntity, AutopilotResource, AutopilotRunEntity
from multica_py.sentinels import Unset


@dataclasses.dataclass(frozen=True)
class TriggerValidationCase:
    method: str
    args: tuple[object, ...]


TRIGGER_VALIDATION_CASES = (
    TriggerValidationCase("trigger_add", ("", AutopilotTriggerCreate(title="Webhook", kind="k"))),
    TriggerValidationCase("trigger_add", ("ap_1", AutopilotTriggerCreate(title="", kind="k"))),
    TriggerValidationCase("trigger_update", ("", "tr_1", AutopilotTriggerUpdate(title="x"))),
    TriggerValidationCase("trigger_update", ("ap_1", "", AutopilotTriggerUpdate(title="x"))),
    TriggerValidationCase("trigger_delete", ("", "tr_1")),
    TriggerValidationCase("trigger_delete", ("ap_1", "")),
)


@dataclasses.dataclass(frozen=True)
class SeedCase:
    name: str
    payload: bytes
    triggers_loaded: bool
    subscribers_loaded: bool


@dataclasses.dataclass(frozen=True)
class BoundPageCase:
    name: str
    method: Literal["list", "history"]
    args: tuple[object, ...]
    stdout: bytes
    expected_argv: tuple[str, ...]
    item_attribute: Literal["autopilots", "runs"]
    expected_item_type: type[AutopilotEntity | AutopilotRunEntity]
    expected_data_type: type[AutopilotData | AutopilotRunData]
    expected_return: object


_AUTOPILOT = {
    "id": "a1",
    "workspace_id": "w1",
    "title": "AP",
    "assignee_type": "member",
    "assignee_id": "u1",
    "status": "active",
    "execution_mode": "create_issue",
    "created_by_type": "member",
    "created_by_id": "u1",
}

_SEED_CASES = (
    SeedCase(
        "complete",
        msgspec.json.encode(
            {
                "autopilot": {
                    **_AUTOPILOT,
                    "subscribers": [{"user_type": "member", "user_id": "u2"}],
                },
                "triggers": [{"id": "tr1", "type": "webhook", "config": {}}],
            }
        ),
        True,
        True,
    ),
    SeedCase(
        "missing",
        msgspec.json.encode({"autopilot": _AUTOPILOT}),
        False,
        False,
    ),
    SeedCase(
        "explicit-empty",
        msgspec.json.encode({"autopilot": {**_AUTOPILOT, "subscribers": []}, "triggers": []}),
        True,
        True,
    ),
)

BOUND_PAGE_CASES = (
    BoundPageCase(
        "list has bound autopilot items",
        "list",
        (),
        msgspec.json.encode({"autopilots": [_AUTOPILOT], "total": 1}),
        ("autopilot", "list", "--output", "json"),
        "autopilots",
        AutopilotEntity,
        AutopilotData,
        AutopilotListPage[AutopilotEntity],
    ),
    BoundPageCase(
        "history has bound run items",
        "history",
        ("a1",),
        msgspec.json.encode(
            {
                "runs": [
                    {
                        "id": "r1",
                        "autopilot_id": "a1",
                        "source": "manual",
                        "status": "done",
                        "task_id": "task_1",
                        "issue_id": "iss_1",
                    }
                ],
                "total": 1,
            }
        ),
        ("autopilot", "runs", "a1", "--output", "json"),
        "runs",
        AutopilotRunEntity,
        AutopilotRunData,
        AutopilotRunListPage[AutopilotRunEntity],
    ),
)


def _resource(transport: MagicMock, client: MulticaClient | None = None) -> AutopilotResource:
    resource = AutopilotResource(cast("CliTransport", transport), ClientConfig())
    resource._set_client(client if client is not None else MagicMock())
    return resource


def _result(payload: bytes, *argv: str) -> RawCommandResult:
    return RawCommandResult(
        stdout=payload,
        stderr=b"",
        exit_code=0,
        argv=argv,
        duration=datetime.timedelta(),
    )


@pytest.mark.parametrize("case", BOUND_PAGE_CASES, ids=lambda case: case.name)
def test_direct_pages_have_exact_bound_item_annotations(case: BoundPageCase) -> None:
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.return_value = _result(case.stdout, *case.expected_argv)
    client = MagicMock()
    resource = _resource(transport, client)

    page = getattr(resource, case.method)(*case.args)
    items = getattr(page, case.item_attribute)

    assert get_type_hints(getattr(AutopilotResource, case.method))["return"] == case.expected_return
    assert isinstance(items[0], case.expected_item_type)
    assert items[0]._client is client
    assert isinstance(items[0].to_data(), case.expected_data_type)
    assert items[0].to_data() is items[0].to_data()
    assert client.mock_calls == []
    transport.run_bytes.assert_called_once_with(case.expected_argv, stdin=None, timeout=None)
    transport.run_text.assert_not_called()
    if case.method == "history":
        client.issues.run_messages.return_value = (
            RunMessage(id="m1", run_id="task_1", role="assistant", content="done"),
        )
        run = cast("AutopilotRunEntity", items[0])
        assert [message.id for message in run.messages.all()] == ["m1"]
        client.issues.run_messages.assert_called_once_with("task_1", issue_id="iss_1")


def test_direct_list_item_second_hop_uses_origin_client() -> None:
    transport = MagicMock(spec=CliTransport)
    client = MagicMock()
    resource = _resource(transport, client)
    client.autopilots = resource
    transport.run_bytes.side_effect = (
        _result(
            msgspec.json.encode({"autopilots": [_AUTOPILOT], "total": 1}),
            "autopilot",
            "list",
            "--output",
            "json",
        ),
        _result(
            msgspec.json.encode(
                {
                    "runs": [
                        {"id": "r1", "autopilot_id": "a1", "source": "manual", "status": "done"}
                    ],
                    "total": 1,
                }
            ),
            "autopilot",
            "runs",
            "a1",
            "--limit",
            "20",
            "--offset",
            "0",
            "--output",
            "json",
        ),
    )

    autopilot = resource.list().autopilots[0]

    assert [run.id for run in autopilot.runs.all()] == ["r1"]
    assert transport.run_bytes.call_args_list[1].args[0] == (
        "autopilot",
        "runs",
        "a1",
        "--limit",
        "20",
        "--offset",
        "0",
        "--output",
        "json",
    )


@pytest.mark.parametrize("case", _SEED_CASES, ids=lambda case: case.name)
def test_get_binds_autopilot_and_seeds_only_present_relations(
    case: SeedCase,
) -> None:
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.return_value = _result(
        case.payload, "autopilot", "get", "a1", "--output", "json"
    )
    entity = _resource(transport).get("a1")

    assert isinstance(entity, AutopilotEntity)
    assert entity.triggers.loaded is case.triggers_loaded
    assert entity.subscribers.loaded is case.subscribers_loaded
    assert transport.run_bytes.call_count == 1


def test_history_binds_runs_and_autopilot_runs_retains_total() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.side_effect = [
        _result(
            msgspec.json.encode(
                {
                    "runs": [
                        {"id": "r1", "autopilot_id": "a1", "source": "manual", "status": "done"}
                    ],
                    "total": 2,
                }
            ),
            "autopilot",
            "runs",
            "a1",
            "--limit",
            "20",
            "--offset",
            "0",
            "--output",
            "json",
        ),
        _result(
            msgspec.json.encode(
                {
                    "runs": [
                        {"id": "r2", "autopilot_id": "a1", "source": "manual", "status": "done"}
                    ],
                    "total": 2,
                }
            ),
            "autopilot",
            "runs",
            "a1",
            "--limit",
            "20",
            "--offset",
            "1",
            "--output",
            "json",
        ),
    ]
    client = MagicMock()
    client.autopilots = _resource(transport, client)
    entity = AutopilotEntity(
        AutopilotData(
            id="a1",
            workspace_id="w1",
            title="AP",
            assignee_type="member",
            assignee_id="u1",
            status="active",
            execution_mode="create_issue",
            created_by_type="member",
            created_by_id="u1",
        ),
        client=client,
    )

    runs = entity.runs.all()

    assert [run.id for run in runs] == ["r1", "r2"]
    assert entity.runs.metadata.total == 2
    assert transport.run_bytes.call_count == 2


def test_trigger_mutations_invalidate_relation() -> None:
    client = MagicMock()
    relation: LazyCollection[AutopilotTrigger] = LazyCollection(
        lambda: (AutopilotTrigger(id="tr1", type="webhook"),)
    )
    client.autopilots.trigger_add.return_value = AutopilotTrigger(id="tr2", type="cron")
    client.autopilots.trigger_update.return_value = AutopilotTrigger(id="tr1", type="cron")
    entity = AutopilotEntity(
        AutopilotData(
            id="a1",
            workspace_id="w1",
            title="AP",
            assignee_type="member",
            assignee_id="u1",
            status="active",
            execution_mode="create_issue",
            created_by_type="member",
            created_by_id="u1",
        ),
        client=client,
    )
    entity._triggers = relation
    relation.all()

    entity.trigger_add(AutopilotTriggerCreate(title="new", kind="webhook"))
    assert not relation.loaded
    entity.trigger_update("tr1", AutopilotTriggerUpdate(title="changed"))
    entity.trigger_delete("tr1")
    client.autopilots.trigger_delete.assert_called_once_with("a1", "tr1")


def test_autopilot_run_messages_require_task_before_transport() -> None:
    client = MagicMock()
    run = AutopilotRunEntity(
        AutopilotRunData(id="r1", autopilot_id="a1", source="manual", status="done"),
        client=client,
    )

    with pytest.raises(MissingRelationContextError):
        run.messages.all()
    client.issues.run_messages.assert_not_called()


def test_legacy_autopilot_methods_are_absent() -> None:
    assert not hasattr(AutopilotResource, "run")
    assert not hasattr(AutopilotResource, "get_run")
    assert not hasattr(AutopilotResource, "trigger_create")
    assert not hasattr(AutopilotResource, "trigger_list")


@pytest.mark.parametrize("case", TRIGGER_VALIDATION_CASES)
def test_trigger_operations_reject_invalid_context_before_transport(
    case: TriggerValidationCase,
) -> None:
    transport = MagicMock(spec=CliTransport)
    resource = AutopilotResource(transport, ClientConfig())

    with pytest.raises(ValueError):
        getattr(resource, case.method)(*case.args)

    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


def test_trigger_requests_are_frozen_and_default_to_unset() -> None:
    request = AutopilotTriggerUpdate()

    assert request.title is Unset
    assert request.kind is Unset
    with pytest.raises(AttributeError):
        setattr(request, "title", "changed")


@pytest.mark.parametrize(
    ("method", "parameters", "return_annotation"),
    (
        (
            "trigger_add",
            (
                ("autopilot_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str),
                ("request", inspect.Parameter.POSITIONAL_OR_KEYWORD, AutopilotTriggerCreate),
            ),
            AutopilotTrigger,
        ),
        (
            "trigger_update",
            (
                ("autopilot_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str),
                ("trigger_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str),
                ("request", inspect.Parameter.POSITIONAL_OR_KEYWORD, AutopilotTriggerUpdate),
            ),
            AutopilotTrigger,
        ),
        (
            "trigger_delete",
            (
                ("autopilot_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str),
                ("trigger_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str),
            ),
            None,
        ),
    ),
)
def test_trigger_public_signatures(
    method: str,
    parameters: tuple[tuple[str, inspect._ParameterKind, object], ...],
    return_annotation: object,
) -> None:
    signature = inspect.signature(getattr(AutopilotResource, method), eval_str=True)
    actual = tuple(signature.parameters.values())[1:]

    assert tuple((item.name, item.kind, item.annotation) for item in actual) == parameters
    assert signature.return_annotation == return_annotation


@pytest.mark.parametrize("max_parallel", [0, -1])
def test_prefetch_rejects_invalid_parallelism_before_io(max_parallel: int) -> None:
    client = MulticaClient(ClientConfig())
    relation: LazyCollection[object] = LazyCollection(lambda: ())

    with pytest.raises(ValueError, match="max_parallel"):
        client.prefetch([], lambda _entity: relation, max_parallel=max_parallel)


def test_prefetch_accepts_heterogeneous_lazy_types() -> None:
    client = MulticaClient(ClientConfig())
    entities = (
        types.SimpleNamespace(_client=client),
        types.SimpleNamespace(_client=client),
    )
    relations: tuple[LazyCollection[object] | LazyMapping[object, object], ...] = (
        LazyCollection(lambda: ()),
        LazyMapping(dict),
    )
    relation_iter = iter(relations)

    client.prefetch(entities, lambda _entity: next(relation_iter), max_parallel=1)

    assert all(relation.loaded for relation in relations)


def test_prefetch_deduplicates_and_skips_loaded_relations() -> None:
    client = MulticaClient(ClientConfig())
    entity = types.SimpleNamespace(_client=client)
    calls = {"shared": 0, "loaded": 0}

    def count_loader(key: str) -> tuple[object, ...]:
        calls[key] += 1
        return ()

    shared: LazyCollection[object] = LazyCollection(lambda: count_loader("shared"))
    loaded: LazyCollection[object] = LazyCollection(lambda: count_loader("loaded"))
    loaded.all()

    selected = iter((shared, shared, loaded))
    client.prefetch((entity, entity, entity), lambda _entity: next(selected), max_parallel=2)

    assert calls == {"shared": 1, "loaded": 1}


def test_prefetch_accepts_derived_views_with_common_semaphore() -> None:
    client = MulticaClient(ClientConfig())
    derived = client.with_workspace("w1")
    entities = (
        types.SimpleNamespace(_client=client),
        types.SimpleNamespace(_client=derived),
    )
    relations: tuple[LazyCollection[object], ...] = (
        LazyCollection(lambda: ()),
        LazyCollection(lambda: ()),
    )
    relation_iter = iter(relations)

    client.prefetch(entities, lambda _entity: next(relation_iter), max_parallel=2)


def test_prefetch_rejects_mixed_origin_scopes_before_selector_io() -> None:
    client = MulticaClient(ClientConfig())
    other = MulticaClient(ClientConfig())
    entities = (
        types.SimpleNamespace(_client=client),
        types.SimpleNamespace(_client=other),
    )
    calls = {"selector": 0}

    def selector(_entity: object) -> LazyCollection[object]:
        calls["selector"] += 1
        return LazyCollection(lambda: ())

    with pytest.raises(ValueError, match="origin"):
        client.prefetch(entities, selector, max_parallel=1)
    assert calls["selector"] == 1


def test_prefetch_raises_lowest_failed_input_and_cancels_pending() -> None:
    client = MulticaClient(ClientConfig())
    entity = types.SimpleNamespace(_client=client)
    release_first = threading.Event()
    first_started = threading.Event()
    calls = {"first": 0, "second": 0, "pending": 0}

    def first_loader() -> tuple[object, ...]:
        calls["first"] += 1
        first_started.set()
        release_first.wait(timeout=2)
        raise RuntimeError("first")

    def second_loader() -> tuple[object, ...]:
        calls["second"] += 1
        assert first_started.wait(timeout=2)
        release_first.set()
        raise RuntimeError("second")

    def pending_loader() -> tuple[object, ...]:
        calls["pending"] += 1
        return ()

    relations: tuple[LazyCollection[object], ...] = (
        LazyCollection(first_loader),
        LazyCollection(second_loader),
        LazyCollection(pending_loader),
    )
    relation_iter = iter(relations)
    with pytest.raises(RuntimeError, match="first"):
        client.prefetch(
            (entity, entity, entity), lambda _entity: next(relation_iter), max_parallel=2
        )
    assert calls == {"first": 1, "second": 1, "pending": 0}
