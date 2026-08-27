from __future__ import annotations

import dataclasses
import datetime
import gc
import inspect
import threading
import weakref
from typing import Literal, cast, get_type_hints
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.commands import Command
from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig, OperationOptions
from multica_py.entities._base import _BoundEntity
from multica_py.entities.autopilots import Autopilot, AutopilotRun
from multica_py.enums import AutopilotExecutionMode
from multica_py.exceptions import DetachedEntityError, MissingRelationContextError
from multica_py.models.autopilots import (
    AutopilotListPage,
    AutopilotRunListPage,
    AutopilotSubscriber,
    AutopilotTrigger,
)
from multica_py.models.common import ActionResult
from multica_py.models.issue_activity import RunMessage
from multica_py.models.relations import LazyCollection, LazyMapping
from multica_py.resources.autopilots import AutopilotResource
from multica_py.resources.issues import IssueResource
from multica_py.sentinels import UnsetType
from tests.unit.resources._factories import bound_entity_factory


@dataclasses.dataclass(frozen=True)
class TriggerValidationCase:
    method: str
    args: tuple[object, ...]
    kwargs: tuple[tuple[str, object], ...] = ()


TRIGGER_VALIDATION_CASES = (
    TriggerValidationCase("trigger_add", ("",), (("title", "Webhook"), ("kind", "k"))),
    TriggerValidationCase("trigger_add", ("ap_1",), (("title", ""), ("kind", "k"))),
    TriggerValidationCase("trigger_update", ("", "tr_1"), (("title", "x"),)),
    TriggerValidationCase("trigger_update", ("ap_1", ""), (("title", "x"),)),
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
    expected_item_type: type[Autopilot | AutopilotRun]
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
        Autopilot,
        AutopilotListPage[Autopilot],
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
        AutopilotRun,
        AutopilotRunListPage[AutopilotRun],
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

    page = getattr(resource, f"{case.method}_command")(*case.args).run()
    items = getattr(page, case.item_attribute)

    assert get_type_hints(getattr(AutopilotResource, case.method))["return"] == case.expected_return
    assert isinstance(items[0], case.expected_item_type)
    assert items[0]._client is client
    assert client.mock_calls == []
    transport.run_bytes.assert_called_once_with(case.expected_argv, stdin=None, timeout=None)
    transport.run_text.assert_not_called()
    if case.method == "history":
        client.issues.run_messages_command.return_value = resource._plan(
            steps=(),
            finalize=lambda _results: (
                RunMessage(task_id="task_1", seq=1, type="text", issue_id="iss_1", content="done"),
            ),
        )

        def run_messages_adapter(
            task_run_id: str,
            *,
            issue_id: str | None,
            since: int = 0,
            options: object = None,
        ) -> Command[tuple[RunMessage, ...]]:
            kwargs: dict[str, object] = {"issue_id": issue_id, "since": since}
            if options is not None:
                kwargs["options"] = options
            command = client.issues.run_messages_command(task_run_id, **kwargs)
            return command._map(
                lambda page: tuple(page.items) if hasattr(page, "items") else tuple(page)
            )

        client.issues._run_messages_relation_command.side_effect = run_messages_adapter
        run = cast("AutopilotRun", items[0])
        assert [message.seq for message in run.messages.all()] == [1]
        client.issues.run_messages_command.assert_called_once_with(
            "task_1", issue_id="iss_1", since=0
        )


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

    autopilot = resource.list_command().run().autopilots[0]

    assert [run.id for run in autopilot.runs.all_command().run()] == ["r1"]
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
    entity = _resource(transport).get_command("a1").run()

    assert isinstance(entity, Autopilot)
    assert entity.triggers.loaded is case.triggers_loaded
    assert entity.subscribers.loaded is case.subscribers_loaded
    assert transport.run_bytes.call_count == 1


@dataclasses.dataclass(frozen=True)
class SeededRelationsCase:
    name: str
    seeded: bool


SEEDED_RELATIONS_CASES = (
    SeededRelationsCase("lazy", False),
    SeededRelationsCase("seeded", True),
)


@pytest.mark.compat
@pytest.mark.parametrize("case", SEEDED_RELATIONS_CASES, ids=lambda case: case.name)
def test_autopilot_relation_loaders_do_not_retain_entity(case: SeededRelationsCase) -> None:
    client = MagicMock()
    kwargs: dict[str, object] = {"_client": client}
    if case.seeded:
        kwargs.update(
            {
                "triggers": (AutopilotTrigger(id="tr1", type="webhook"),),
                "subscribers": (AutopilotSubscriber(user_type="member", user_id="u1"),),
            }
        )
    entity = Autopilot(
        id="a1",
        workspace_id="w1",
        title="AP",
        assignee_type="member",
        assignee_id="u1",
        status="active",
        execution_mode="create_issue",
        created_by_type="member",
        created_by_id="u1",
        **kwargs,
    )
    relations = (entity.triggers, entity.subscribers)
    assert all(relation.loaded is case.seeded for relation in relations)
    reference = weakref.ref(entity)

    del entity
    gc.collect()

    assert reference() is None


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
    entity = Autopilot(
        id="a1",
        workspace_id="w1",
        title="AP",
        assignee_type="member",
        assignee_id="u1",
        status="active",
        execution_mode="create_issue",
        created_by_type="member",
        created_by_id="u1",
        _client=client,
    )

    runs = entity.runs.all()

    assert [run.id for run in runs] == ["r1", "r2"]
    assert entity.runs.metadata.total == 2
    assert transport.run_bytes.call_count == 2


def test_trigger_mutations_invalidate_relation() -> None:
    client = MagicMock()
    transport = MagicMock(spec=CliTransport)
    transport.run_bytes.side_effect = [
        _result(b'{"id":"tr2","type":"cron","config":{}}'),
        _result(b'{"id":"tr1","type":"cron","config":{}}'),
    ]
    transport.run_text.return_value = TextResult("", "", 0)
    resource = _resource(transport, client)
    client.autopilots = resource
    relation: LazyCollection[AutopilotTrigger] = LazyCollection(
        lambda: (AutopilotTrigger(id="tr1", type="webhook"),)
    )
    entity = Autopilot(
        id="a1",
        workspace_id="w1",
        title="AP",
        assignee_type="member",
        assignee_id="u1",
        status="active",
        execution_mode="create_issue",
        created_by_type="member",
        created_by_id="u1",
        _client=client,
    )
    entity._set_runtime("_triggers", relation)
    relation.all()

    entity.trigger_add(title="new", kind="webhook")
    assert not relation.loaded
    entity.trigger_update("tr1", title="changed")
    entity.trigger_delete("tr1")
    transport.run_text.assert_called_once_with(("autopilot", "trigger-delete", "a1", "tr1"))


def test_autopilot_run_messages_require_task_before_transport() -> None:
    client = MagicMock()
    run = AutopilotRun(
        id="r1",
        autopilot_id="a1",
        source="manual",
        status="done",
        _client=client,
    )

    with pytest.raises(MissingRelationContextError):
        run.messages.all()
    client.issues.run_messages.assert_not_called()
    client.issues.run_messages_command.assert_not_called()


def test_autopilot_trigger_command_invalidates_only_after_success() -> None:
    client = MulticaClient(ClientConfig())
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.return_value = _result(b'{"id":"tr1","type":"webhook","config":{}}')
    client.autopilots._transport = transport
    entity = Autopilot(
        id="a1",
        workspace_id="w1",
        title="AP",
        assignee_type="member",
        assignee_id="u1",
        status="active",
        execution_mode="create_issue",
        created_by_type="member",
        created_by_id="u1",
        _client=client,
    )
    relation = LazyCollection(lambda: (AutopilotTrigger(id="tr0", type="webhook"),))
    entity._set_runtime("_triggers", relation)
    relation.all()

    command = entity.trigger_add_command(title="Webhook", kind="webhook")
    assert command.commands == (
        "multica autopilot trigger-add a1 --title Webhook --kind webhook --output json",
    )
    assert transport.run_bytes.call_count == 0
    command.run()
    assert not relation.loaded

    relation.all()
    transport.run_bytes.side_effect = RuntimeError("transport failure")
    failed = entity.trigger_update_command("tr0", title="Changed")
    with pytest.raises(RuntimeError, match="transport failure"):
        failed.run()
    assert relation.loaded


def test_autopilot_trigger_uses_only_supported_command_spelling() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.return_value = _result(
        b'{"id":"run1","autopilot_id":"a1","source":"manual","status":"running"}',
        "autopilot",
        "trigger",
        "a1",
        "--output",
        "json",
    )
    resource = _resource(transport)

    command = resource.trigger_command("a1")

    assert command.commands == ("multica autopilot trigger a1 --output json",)
    assert "autopilot run" not in command.commands[0]
    assert transport.run_bytes.call_count == 0
    assert command.run().id == "run1"
    assert transport.run_bytes.call_args.args[0] == (
        "autopilot",
        "trigger",
        "a1",
        "--output",
        "json",
    )


def test_autopilot_relation_commands_preserve_preview_and_page_argv() -> None:
    client = MulticaClient(ClientConfig())
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.side_effect = (
        _result(
            msgspec.json.encode(
                {
                    "autopilot": _AUTOPILOT,
                    "triggers": [{"id": "tr1", "type": "webhook", "config": {}}],
                }
            )
        ),
        _result(msgspec.json.encode({"runs": [], "total": 0})),
    )
    client.autopilots._transport = transport
    entity = Autopilot(
        id="a1",
        workspace_id="w1",
        title="AP",
        assignee_type="member",
        assignee_id="u1",
        status="active",
        execution_mode="create_issue",
        created_by_type="member",
        created_by_id="u1",
        _client=client,
    )

    triggers = entity.triggers
    trigger_command = triggers.all_command()
    assert trigger_command.commands == ("multica autopilot get a1 --output json",)
    assert transport.run_bytes.call_count == 0
    assert trigger_command.run()[0].id == "tr1"

    page_command = entity.runs.page_command(limit=10, offset=20)
    assert page_command.commands == (
        "multica autopilot runs a1 --limit 10 --offset 20 --output json",
    )
    assert page_command.run().offset == 20


def test_autopilot_eager_and_dunder_relation_loads_use_command_plan() -> None:
    client = MulticaClient(ClientConfig())
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.side_effect = lambda argv, **_kwargs: _result(
        msgspec.json.encode(
            {
                "autopilot": {
                    **_AUTOPILOT,
                },
                "triggers": [{"id": "tr1", "type": "webhook", "config": {}}],
            }
        ),
        *argv,
    )
    client.autopilots._transport = transport
    entity = Autopilot(
        id="a1",
        workspace_id="w1",
        title="AP",
        assignee_type="member",
        assignee_id="u1",
        status="active",
        execution_mode="create_issue",
        created_by_type="member",
        created_by_id="u1",
        _client=client,
    )

    relation = entity.triggers
    assert relation.all_command().commands == ("multica autopilot get a1 --output json",)
    assert relation.all() == (relation.all()[0],)
    assert len(relation) == 1
    assert next(iter(relation)).id == "tr1"
    assert transport.run_bytes.call_count == 1

    relation.invalidate()
    assert relation.refresh_command().commands == ("multica autopilot get a1 --output json",)
    assert relation.refresh()[0].id == "tr1"
    assert transport.run_bytes.call_count == 2
    assert transport.run_bytes.call_args_list[0].args[0] == (
        "autopilot",
        "get",
        "a1",
        "--output",
        "json",
    )


def test_autopilot_relation_command_runs_coalesce_one_loader_sequence() -> None:
    client = MulticaClient(ClientConfig())
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    started = threading.Event()
    release = threading.Event()

    def run_bytes(argv: tuple[str, ...], **_kwargs: object) -> RawCommandResult:
        started.set()
        assert release.wait(timeout=2)
        return _result(
            msgspec.json.encode(
                {
                    "autopilot": {
                        **_AUTOPILOT,
                    },
                    "triggers": [{"id": "tr1", "type": "webhook", "config": {}}],
                }
            ),
            *argv,
        )

    transport.run_bytes.side_effect = run_bytes
    client.autopilots._transport = transport
    entity = Autopilot(
        id="a1",
        workspace_id="w1",
        title="AP",
        assignee_type="member",
        assignee_id="u1",
        status="active",
        execution_mode="create_issue",
        created_by_type="member",
        created_by_id="u1",
        _client=client,
    )
    relation = entity.triggers
    first = relation.all_command()
    second = relation.all_command()
    assert first.commands == second.commands == ("multica autopilot get a1 --output json",)

    results: list[tuple[AutopilotTrigger, ...]] = []
    errors: list[Exception] = []

    def run(command: object) -> None:
        try:
            results.append(cast("Command[tuple[AutopilotTrigger, ...]]", command).run())
        except Exception as error:
            errors.append(error)

    first_thread = threading.Thread(target=run, args=(first,))
    second_thread = threading.Thread(target=run, args=(second,))
    first_thread.start()
    assert started.wait(timeout=2)
    second_thread.start()
    for _ in range(200):
        if relation._generation_state.waiters:
            break
        threading.Event().wait(0.005)
    release.set()
    first_thread.join(timeout=2)
    second_thread.join(timeout=2)

    assert not first_thread.is_alive()
    assert not second_thread.is_alive()
    assert not errors
    assert len(results) == 2
    assert results[0] == results[1]
    assert transport.run_bytes.call_count == 1


def test_autopilot_run_messages_command_rejects_missing_task_before_io() -> None:
    client = MagicMock()
    run = AutopilotRun(
        id="r1",
        autopilot_id="a1",
        source="manual",
        status="done",
        _client=client,
    )

    with pytest.raises(MissingRelationContextError):
        run.messages_command()
    client.issues.run_messages_command.assert_not_called()
    client.issues.run_messages.assert_not_called()


def test_autopilot_run_messages_relation_command_delegates_to_issue_resource() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    client = MagicMock()
    issues = IssueResource(transport, ClientConfig())
    issues._set_client(client)
    client.issues = issues
    run = AutopilotRun(
        id="r1",
        autopilot_id="a1",
        source="manual",
        status="done",
        issue_id="i1",
        task_id="task1",
        _client=client,
    )

    command = run.messages.all_command()

    assert command.commands == (
        "multica issue run-messages task1 --issue i1 --since 0 --output json",
    )
    transport.run_bytes.assert_not_called()


def test_autopilot_run_messages_relation_command_rejects_missing_task_before_io() -> None:
    client = MagicMock()
    run = AutopilotRun(
        id="r1",
        autopilot_id="a1",
        source="manual",
        status="done",
        _client=client,
    )

    with pytest.raises(MissingRelationContextError):
        run.messages.all_command()
    client.issues.run_messages_command.assert_not_called()


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
        getattr(resource, f"{case.method}_command")(*case.args, **dict(case.kwargs))

    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


@dataclasses.dataclass(frozen=True)
class TriggerSignatureCase:
    method: str
    parameters: tuple[tuple[str, inspect._ParameterKind, object], ...]
    return_annotation: object


TRIGGER_SIGNATURE_CASES = (
    TriggerSignatureCase(
        "trigger_add",
        (
            ("autopilot_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str),
            ("title", inspect.Parameter.KEYWORD_ONLY, str),
            ("kind", inspect.Parameter.KEYWORD_ONLY, str),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None),
        ),
        AutopilotTrigger,
    ),
    TriggerSignatureCase(
        "trigger_update",
        (
            ("autopilot_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str),
            ("trigger_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str),
            ("title", inspect.Parameter.KEYWORD_ONLY, str | UnsetType),
            ("kind", inspect.Parameter.KEYWORD_ONLY, str | UnsetType),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None),
        ),
        AutopilotTrigger,
    ),
    TriggerSignatureCase(
        "trigger_delete",
        (
            ("autopilot_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str),
            ("trigger_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None),
        ),
        ActionResult[None],
    ),
)


@pytest.mark.parametrize("case", TRIGGER_SIGNATURE_CASES, ids=lambda case: case.method)
def test_trigger_public_signatures(
    case: TriggerSignatureCase,
) -> None:
    signature = inspect.signature(getattr(AutopilotResource, case.method), eval_str=True)
    actual = tuple(signature.parameters.values())[1:]

    assert tuple((item.name, item.kind, item.annotation) for item in actual) == case.parameters
    assert signature.return_annotation == case.return_annotation


@dataclasses.dataclass(frozen=True)
class InvalidParallelismCase:
    name: str
    value: int


INVALID_PARALLELISM_CASES = (
    InvalidParallelismCase("zero", 0),
    InvalidParallelismCase("negative", -1),
)


@pytest.mark.parametrize("case", INVALID_PARALLELISM_CASES, ids=lambda case: case.name)
def test_prefetch_rejects_invalid_parallelism_before_io(case: InvalidParallelismCase) -> None:
    client = MulticaClient(ClientConfig())
    relation: LazyCollection[object] = LazyCollection(lambda: ())
    entity = bound_entity_factory(client)

    with pytest.raises(ValueError, match="max_parallel"):
        client.prefetch((entity,), lambda _entity: relation, max_parallel=case.value)


def test_prefetch_accepts_heterogeneous_lazy_types() -> None:
    client = MulticaClient(ClientConfig())
    entities = (
        bound_entity_factory(client, target_id="source-1"),
        bound_entity_factory(client, target_id="source-2"),
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
    entity = bound_entity_factory(client)
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
        bound_entity_factory(client, target_id="source-1"),
        bound_entity_factory(derived, target_id="source-2"),
    )
    relations: tuple[LazyCollection[object], ...] = (
        LazyCollection(lambda: ()),
        LazyCollection(lambda: ()),
    )
    relation_iter = iter(relations)

    client.prefetch(entities, lambda _entity: next(relation_iter), max_parallel=2)


@dataclasses.dataclass(frozen=True)
class PrefetchOriginRejectCase:
    name: str
    error: type[BaseException]
    match: str
    selector_calls: int
    detach_first: bool
    entity_ids: tuple[str, ...]


PREFETCH_ORIGIN_REJECT_CASES = (
    PrefetchOriginRejectCase(
        "mixed-origin",
        ValueError,
        "origin",
        1,
        False,
        ("source-1", "source-2"),
    ),
    PrefetchOriginRejectCase(
        "detached",
        DetachedEntityError,
        "detached",
        0,
        True,
        ("ent-1",),
    ),
)


@pytest.mark.parametrize("case", PREFETCH_ORIGIN_REJECT_CASES, ids=lambda case: case.name)
def test_prefetch_rejects_invalid_origin_before_selector_io(
    case: PrefetchOriginRejectCase,
) -> None:
    client = MulticaClient(ClientConfig())
    entities: tuple[_BoundEntity, ...]
    if case.detach_first:
        entities = (bound_entity_factory(client, target_id=case.entity_ids[0]).detach(),)
    else:
        other = MulticaClient(ClientConfig())
        entities = (
            bound_entity_factory(client, target_id=case.entity_ids[0]),
            bound_entity_factory(other, target_id=case.entity_ids[1]),
        )
    calls = {"selector": 0}

    def selector(_entity: object) -> LazyCollection[object]:
        calls["selector"] += 1
        return LazyCollection(lambda: ())

    with pytest.raises(case.error, match=case.match) as exc_info:
        client.prefetch(entities, selector, max_parallel=1)
    assert calls["selector"] == case.selector_calls
    if case.error is DetachedEntityError:
        error = exc_info.value
        assert isinstance(error, DetachedEntityError)
        assert error.entity_type == "Issue"
        assert error.entity_id == case.entity_ids[0]
        assert error.relation_name == "prefetch"


def test_prefetch_raises_lowest_failed_input_and_cancels_pending() -> None:
    client = MulticaClient(ClientConfig())
    entity = bound_entity_factory(client)
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
