from __future__ import annotations

import dataclasses
import inspect
import pathlib
from typing import cast
from unittest.mock import MagicMock

import pytest
from mypy import api as mypy_api

from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig, OperationOptions
from multica_py.entities.autopilots import Autopilot
from multica_py.models.autopilots import AutopilotTrigger
from multica_py.models.common import ActionResult
from multica_py.resources.autopilots import AutopilotResource
from multica_py.sentinels import Unset, UnsetType
from tests.unit.resources._factories import autopilot_resource, command_result


@dataclasses.dataclass(frozen=True)
class TriggerValidationCase:
    method: str
    args: tuple[object, ...]
    kwargs: tuple[tuple[str, object], ...] = ()
    expected_error: type[Exception] = ValueError


TRIGGER_VALIDATION_CASES = (
    TriggerValidationCase("trigger_add", ("",), (("kind", "webhook"),)),
    TriggerValidationCase(
        "trigger_add",
        ("ap_1",),
        (("kind", "invalid"), ("cron_expression", "*/30 * * * *")),
    ),
    TriggerValidationCase("trigger_add", ("ap_1",), (("kind", "schedule"),)),
    TriggerValidationCase(
        "trigger_add",
        ("ap_1",),
        (("kind", "webhook"), ("cron_expression", "*/30 * * * *")),
    ),
    TriggerValidationCase(
        "trigger_add",
        ("ap_1",),
        (("kind", "webhook"), ("timezone", "Europe/Minsk")),
    ),
    TriggerValidationCase("trigger_update", ("", "tr_1"), (("label", "x"),)),
    TriggerValidationCase("trigger_update", ("ap_1", ""), (("label", "x"),)),
    TriggerValidationCase(
        "trigger_update",
        ("ap_1", "tr_1"),
        (("cron_expression", None),),
        TypeError,
    ),
    TriggerValidationCase(
        "trigger_update",
        ("ap_1", "tr_1"),
        (("timezone", None),),
        TypeError,
    ),
    TriggerValidationCase(
        "trigger_update",
        ("ap_1", "tr_1"),
        (("label", None),),
        TypeError,
    ),
    TriggerValidationCase(
        "trigger_update",
        ("ap_1", "tr_1"),
        (("enabled", None),),
        TypeError,
    ),
    TriggerValidationCase("trigger_update", ("ap_1", "tr_1")),
    TriggerValidationCase("trigger_delete", ("", "tr_1")),
    TriggerValidationCase("trigger_delete", ("ap_1", "")),
)


def test_direct_trigger_add_uses_exact_schedule_argv_and_decodes_response() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.return_value = command_result(
        b'{"id":"tr1","autopilot_id":"a1","kind":"schedule","enabled":true,'
        b'"cron_expression":"*/30 * * * *","timezone":"Europe/Minsk",'
        b'"label":"half-hour"}',
        "autopilot",
        "trigger-add",
        "a1",
        "--kind",
        "schedule",
        "--cron",
        "*/30 * * * *",
        "--timezone",
        "Europe/Minsk",
        "--label",
        "half-hour",
        "--output",
        "json",
    )
    resource = autopilot_resource(transport)

    command = resource.trigger_add_command(
        "a1",
        cron_expression="*/30 * * * *",
        timezone="Europe/Minsk",
        label="half-hour",
    )

    assert command.commands == (
        "multica autopilot trigger-add a1 --kind schedule --cron '*/30 * * * *' "
        "--timezone Europe/Minsk --label half-hour --output json",
    )
    transport.run_bytes.assert_not_called()
    trigger = command.run()
    assert trigger.kind == "schedule"
    assert trigger.cron_expression == "*/30 * * * *"
    assert trigger.timezone == "Europe/Minsk"
    assert trigger.label == "half-hour"

    eager = resource.trigger_add(
        "a1",
        cron_expression="*/30 * * * *",
        timezone="Europe/Minsk",
        label="half-hour",
    )
    assert eager == trigger


@pytest.mark.parametrize(
    ("kind", "cron_expression", "timezone", "label", "expected"),
    (
        (
            "webhook",
            None,
            None,
            None,
            "multica autopilot trigger-add a1 --kind webhook --output json",
        ),
        (
            "webhook",
            "",
            "",
            "",
            "multica autopilot trigger-add a1 --kind webhook --output json",
        ),
        (
            "",
            "0 */3 * * *",
            "",
            "",
            "multica autopilot trigger-add a1 --kind schedule --cron '0 */3 * * *' --output json",
        ),
    ),
)
def test_direct_trigger_add_preserves_presence_semantics(
    kind: str,
    cron_expression: str | None,
    timezone: str | None,
    label: str | None,
    expected: str,
) -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    resource = autopilot_resource(transport)

    command = resource.trigger_add_command(
        "a1",
        kind=kind,
        cron_expression=cron_expression,
        timezone=timezone,
        label=label,
    )

    assert command.commands == (expected,)
    transport.run_bytes.assert_not_called()


@pytest.mark.parametrize(
    ("kind", "cron_expression", "timezone", "expected_error"),
    (
        (None, "*/30 * * * *", None, TypeError),
        ("unknown", "*/30 * * * *", None, ValueError),
        ("schedule", None, None, ValueError),
        ("schedule", "", None, ValueError),
        ("webhook", "*/30 * * * *", None, ValueError),
        ("webhook", None, "Europe/Minsk", ValueError),
    ),
)
def test_direct_trigger_add_rejects_invalid_inputs_before_transport(
    kind: object,
    cron_expression: object,
    timezone: object,
    expected_error: type[Exception],
) -> None:
    transport = MagicMock(spec=CliTransport)
    resource = autopilot_resource(transport)

    with pytest.raises(expected_error):
        resource.trigger_add_command(
            "a1",
            kind=kind,  # type: ignore[arg-type]
            cron_expression=cron_expression,  # type: ignore[arg-type]
            timezone=timezone,  # type: ignore[arg-type]
        )

    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


def test_direct_trigger_update_emits_patch_presence_and_inline_boolean() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.return_value = command_result(
        b'{"id":"tr1","autopilot_id":"a1","kind":"schedule","enabled":false, '
        b'"cron_expression":"","timezone":"","label":""}',
        "autopilot",
        "trigger-update",
        "a1",
        "tr1",
        "--cron",
        "",
        "--timezone",
        "",
        "--label",
        "",
        "--enabled=false",
        "--output",
        "json",
    )
    resource = autopilot_resource(transport)

    command = resource.trigger_update_command(
        "a1",
        "tr1",
        cron_expression="",
        timezone="",
        label="",
        enabled=False,
    )

    assert command.commands == (
        "multica autopilot trigger-update a1 tr1 --cron '' --timezone '' --label '' "
        "--enabled=false --output json",
    )
    transport.run_bytes.assert_not_called()
    trigger = command.run()
    assert trigger.enabled is False
    assert trigger.cron_expression == ""
    assert trigger.timezone == ""
    assert trigger.label == ""

    eager = resource.trigger_update("a1", "tr1", enabled=False)
    assert eager == trigger


def test_direct_trigger_update_omits_unset_fields() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    resource = autopilot_resource(transport)

    command = resource.trigger_update_command(
        "a1", "tr1", cron_expression="0 */3 * * *", enabled=True
    )

    assert command.commands == (
        "multica autopilot trigger-update a1 tr1 --cron '0 */3 * * *' --enabled=true --output json",
    )
    transport.run_bytes.assert_not_called()


@pytest.mark.parametrize(
    "kwargs",
    (
        {"cron_expression": None},
        {"timezone": None},
        {"label": None},
        {"enabled": None},
        {"cron_expression": 1},
        {"timezone": 1},
        {"label": 1},
        {"enabled": 1},
        {},
    ),
)
def test_direct_trigger_update_rejects_invalid_inputs_before_transport(
    kwargs: dict[str, object],
) -> None:
    transport = MagicMock(spec=CliTransport)
    resource = autopilot_resource(transport)
    expected_error = ValueError if not kwargs else TypeError

    with pytest.raises(expected_error):
        resource.trigger_update_command(
            "a1",
            "tr1",
            **kwargs,  # type: ignore[arg-type]
        )

    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


def test_bound_trigger_commands_match_direct_argv_without_io() -> None:
    client = MulticaClient(ClientConfig())
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
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

    add = entity.trigger_add_command(cron_expression="0 * * * *", timezone="UTC", label="hourly")
    update = entity.trigger_update_command(
        "tr1", cron_expression="", timezone="", label="", enabled=False
    )

    assert add.commands == (
        "multica autopilot trigger-add a1 --kind schedule --cron '0 * * * *' "
        "--timezone UTC --label hourly --output json",
    )
    assert update.commands == (
        "multica autopilot trigger-update a1 tr1 --cron '' --timezone '' --label '' "
        "--enabled=false --output json",
    )
    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


@pytest.mark.parametrize(
    ("method", "kwargs", "expected_error"),
    (
        ("trigger_add", {"kind": "schedule"}, ValueError),
        ("trigger_add", {"kind": "webhook", "timezone": "UTC"}, ValueError),
        ("trigger_update", {"trigger_id": "tr1"}, ValueError),
        ("trigger_update", {"trigger_id": "tr1", "enabled": None}, TypeError),
    ),
)
def test_bound_trigger_local_failures_do_not_use_transport(
    method: str, kwargs: dict[str, object], expected_error: type[Exception]
) -> None:
    client = MulticaClient(ClientConfig())
    transport = MagicMock(spec=CliTransport)
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

    with pytest.raises(expected_error):
        getattr(entity, method)(**kwargs)

    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


def test_autopilot_trigger_uses_only_supported_command_spelling() -> None:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    transport.run_bytes.return_value = command_result(
        b'{"id":"run1","autopilot_id":"a1","source":"manual","status":"running"}',
        "autopilot",
        "trigger",
        "a1",
        "--output",
        "json",
    )
    resource = autopilot_resource(transport)

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

    with pytest.raises(case.expected_error):
        getattr(resource, f"{case.method}_command")(*case.args, **dict(case.kwargs))

    transport.run_bytes.assert_not_called()
    transport.run_text.assert_not_called()


@dataclasses.dataclass(frozen=True)
class TriggerSignatureCase:
    owner: type[object]
    method: str
    parameters: tuple[tuple[str, inspect._ParameterKind, object, object], ...]
    return_annotation: object


TRIGGER_SIGNATURE_CASES = (
    TriggerSignatureCase(
        AutopilotResource,
        "trigger_add",
        (
            ("autopilot_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str, inspect.Parameter.empty),
            ("kind", inspect.Parameter.KEYWORD_ONLY, str, "schedule"),
            ("cron_expression", inspect.Parameter.KEYWORD_ONLY, str | None, None),
            ("timezone", inspect.Parameter.KEYWORD_ONLY, str | None, None),
            ("label", inspect.Parameter.KEYWORD_ONLY, str | None, None),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None, None),
        ),
        AutopilotTrigger,
    ),
    TriggerSignatureCase(
        AutopilotResource,
        "trigger_add_command",
        (
            ("autopilot_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str, inspect.Parameter.empty),
            ("kind", inspect.Parameter.KEYWORD_ONLY, str, "schedule"),
            ("cron_expression", inspect.Parameter.KEYWORD_ONLY, str | None, None),
            ("timezone", inspect.Parameter.KEYWORD_ONLY, str | None, None),
            ("label", inspect.Parameter.KEYWORD_ONLY, str | None, None),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None, None),
        ),
        Command[AutopilotTrigger],
    ),
    TriggerSignatureCase(
        AutopilotResource,
        "trigger_update",
        (
            ("autopilot_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str, inspect.Parameter.empty),
            ("trigger_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str, inspect.Parameter.empty),
            ("cron_expression", inspect.Parameter.KEYWORD_ONLY, str | UnsetType, Unset),
            ("timezone", inspect.Parameter.KEYWORD_ONLY, str | UnsetType, Unset),
            ("label", inspect.Parameter.KEYWORD_ONLY, str | UnsetType, Unset),
            ("enabled", inspect.Parameter.KEYWORD_ONLY, bool | UnsetType, Unset),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None, None),
        ),
        AutopilotTrigger,
    ),
    TriggerSignatureCase(
        AutopilotResource,
        "trigger_update_command",
        (
            ("autopilot_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str, inspect.Parameter.empty),
            ("trigger_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str, inspect.Parameter.empty),
            ("cron_expression", inspect.Parameter.KEYWORD_ONLY, str | UnsetType, Unset),
            ("timezone", inspect.Parameter.KEYWORD_ONLY, str | UnsetType, Unset),
            ("label", inspect.Parameter.KEYWORD_ONLY, str | UnsetType, Unset),
            ("enabled", inspect.Parameter.KEYWORD_ONLY, bool | UnsetType, Unset),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None, None),
        ),
        Command[AutopilotTrigger],
    ),
    TriggerSignatureCase(
        Autopilot,
        "trigger_add",
        (
            ("kind", inspect.Parameter.KEYWORD_ONLY, str, "schedule"),
            ("cron_expression", inspect.Parameter.KEYWORD_ONLY, str | None, None),
            ("timezone", inspect.Parameter.KEYWORD_ONLY, str | None, None),
            ("label", inspect.Parameter.KEYWORD_ONLY, str | None, None),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None, None),
        ),
        AutopilotTrigger,
    ),
    TriggerSignatureCase(
        Autopilot,
        "trigger_add_command",
        (
            ("kind", inspect.Parameter.KEYWORD_ONLY, str, "schedule"),
            ("cron_expression", inspect.Parameter.KEYWORD_ONLY, str | None, None),
            ("timezone", inspect.Parameter.KEYWORD_ONLY, str | None, None),
            ("label", inspect.Parameter.KEYWORD_ONLY, str | None, None),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None, None),
        ),
        Command[AutopilotTrigger],
    ),
    TriggerSignatureCase(
        Autopilot,
        "trigger_update",
        (
            ("trigger_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str, inspect.Parameter.empty),
            ("cron_expression", inspect.Parameter.KEYWORD_ONLY, str | UnsetType, Unset),
            ("timezone", inspect.Parameter.KEYWORD_ONLY, str | UnsetType, Unset),
            ("label", inspect.Parameter.KEYWORD_ONLY, str | UnsetType, Unset),
            ("enabled", inspect.Parameter.KEYWORD_ONLY, bool | UnsetType, Unset),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None, None),
        ),
        AutopilotTrigger,
    ),
    TriggerSignatureCase(
        Autopilot,
        "trigger_update_command",
        (
            ("trigger_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str, inspect.Parameter.empty),
            ("cron_expression", inspect.Parameter.KEYWORD_ONLY, str | UnsetType, Unset),
            ("timezone", inspect.Parameter.KEYWORD_ONLY, str | UnsetType, Unset),
            ("label", inspect.Parameter.KEYWORD_ONLY, str | UnsetType, Unset),
            ("enabled", inspect.Parameter.KEYWORD_ONLY, bool | UnsetType, Unset),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None, None),
        ),
        Command[AutopilotTrigger],
    ),
    TriggerSignatureCase(
        AutopilotResource,
        "trigger_delete",
        (
            ("autopilot_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str, inspect.Parameter.empty),
            ("trigger_id", inspect.Parameter.POSITIONAL_OR_KEYWORD, str, inspect.Parameter.empty),
            ("options", inspect.Parameter.KEYWORD_ONLY, OperationOptions | None, None),
        ),
        ActionResult[None],
    ),
)


@pytest.mark.parametrize("case", TRIGGER_SIGNATURE_CASES, ids=lambda case: case.method)
def test_trigger_public_signatures(
    case: TriggerSignatureCase,
) -> None:
    signature = inspect.signature(getattr(case.owner, case.method), eval_str=True)
    actual = tuple(signature.parameters.values())[1:]

    assert (
        tuple((item.name, item.kind, item.annotation, item.default) for item in actual)
        == case.parameters
    )
    assert signature.return_annotation == case.return_annotation


def test_autopilot_trigger_typecheck_fixtures() -> None:
    fixture_root = pathlib.Path(__file__).parents[2] / "typecheck"
    positive_stdout, positive_stderr, positive_status = mypy_api.run(
        [
            "--strict",
            "--python-version",
            "3.12",
            str(fixture_root / "autopilot_trigger_usage.py"),
        ]
    )
    assert positive_status == 0, positive_stdout + positive_stderr

    negative_stdout, negative_stderr, negative_status = mypy_api.run(
        [
            "--strict",
            "--python-version",
            "3.12",
            str(fixture_root / "autopilot_trigger_obsolete.py.txt"),
        ]
    )
    assert negative_status != 0
    assert 'Unexpected keyword argument "title"' in negative_stdout
    assert 'Unexpected keyword argument "kind"' in negative_stdout
    assert not negative_stderr
