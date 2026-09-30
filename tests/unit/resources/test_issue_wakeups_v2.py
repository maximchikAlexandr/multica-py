from __future__ import annotations

import datetime
import json
import shlex
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from multica_py._internal.commands import Command
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.exceptions import CommandExecutionError, OutputShapeError
from multica_py.models.common import ActionResult
from multica_py.models.issue_wakeups import (
    IssueWakeup,
    IssueWakeupDeleteResult,
    IssueWakeupEvents,
    IssueWakeupPage,
    IssueWakeupRunsPage,
    IssueWakeupTriggerResult,
)
from multica_py.resources.issue_wakeups import IssueWakeupResource
from tests.unit.resources._factories import command_result, make_transport


def wakeups(transport: MagicMock) -> IssueWakeupResource:
    return IssueWakeupResource(cast("CliTransport", transport), ClientConfig())


def wakeup_payload(**overrides: object) -> bytes:
    payload: dict[str, object] = {"id": "wake-1", "enabled": True}
    payload.update(overrides)
    return json.dumps(payload).encode()


def create_args(resource: IssueWakeupResource, **kwargs: object) -> Any:
    return cast("Any", resource.create_command)("iss-1", instruction="Run checks", **kwargs)


def update_args(resource: IssueWakeupResource, **kwargs: object) -> Any:
    return cast("Any", resource.update_command)(
        "iss-1", "wake-1", instruction="Run checks", **kwargs
    )


@dataclass(frozen=True)
class _EagerCommandCase:
    name: str
    command_builder: Callable[[IssueWakeupResource], object]
    eager_runner: Callable[[IssueWakeupResource], object]
    expected_argv: str
    response: bytes | None
    extract: Callable[[object], object]
    expected_result: object
    set_response: Callable[[MagicMock, bytes | None], None]
    reset_transport: Callable[[MagicMock], None]
    assert_transport: Callable[[MagicMock, tuple[str, ...]], None]


def _set_bytes_response(transport: MagicMock, response: bytes | None) -> None:
    assert response is not None
    transport.run_bytes.return_value = command_result(response)


def _set_text_response(transport: MagicMock, response: bytes | None) -> None:
    assert response is None


def _reset_bytes_transport(transport: MagicMock) -> None:
    transport.run_bytes.reset_mock()


def _reset_text_transport(transport: MagicMock) -> None:
    transport.run_text.reset_mock()


def _assert_bytes_transport(transport: MagicMock, expected_argv: tuple[str, ...]) -> None:
    assert transport.run_bytes.call_args.args[0] == expected_argv


def _assert_text_transport(transport: MagicMock, expected_argv: tuple[str, ...]) -> None:
    assert transport.run_text.call_args.args[0] == expected_argv


def _events_command(resource: IssueWakeupResource) -> object:
    return resource.events_command()


def _events_eager(resource: IssueWakeupResource) -> object:
    return resource.events()


def _events_result(result: object) -> object:
    events = cast("IssueWakeupEvents", result)
    return events.events[0].name, events.loop_protection


def _list_command(resource: IssueWakeupResource) -> object:
    return resource.list_command("iss-1")


def _list_eager(resource: IssueWakeupResource) -> object:
    return resource.list("iss-1")


def _list_result(result: object) -> object:
    page = cast("IssueWakeupPage", result)
    return page.items[0].id


def _get_command(resource: IssueWakeupResource) -> object:
    return resource.get_command("iss-1", "wake-1")


def _get_eager(resource: IssueWakeupResource) -> object:
    return resource.get("iss-1", "wake-1")


def _wakeup_id(result: object) -> object:
    return cast("IssueWakeup", result).id


def _disable_command(resource: IssueWakeupResource) -> object:
    return resource.disable_command("iss-1", "wake-1")


def _disable_eager(resource: IssueWakeupResource) -> object:
    return resource.disable("iss-1", "wake-1")


def _disabled(result: object) -> object:
    return cast("IssueWakeup", result).enabled


def _create_command(resource: IssueWakeupResource) -> object:
    return resource.create_command(
        "iss-1", instruction="Run checks", event_types=("comment.created",)
    )


def _create_eager(resource: IssueWakeupResource) -> object:
    return resource.create("iss-1", instruction="Run checks", event_types=("comment.created",))


def _update_command(resource: IssueWakeupResource) -> object:
    return resource.update_command(
        "iss-1", "wake-1", instruction="Run checks", event_types=("comment.created",)
    )


def _update_eager(resource: IssueWakeupResource) -> object:
    return resource.update(
        "iss-1", "wake-1", instruction="Run checks", event_types=("comment.created",)
    )


def _reenabled(result: object) -> object:
    wakeup = cast("IssueWakeup", result)
    return wakeup.id, wakeup.enabled


def _trigger_command(resource: IssueWakeupResource) -> object:
    return resource.trigger_command("iss-1", "wake-1")


def _trigger_eager(resource: IssueWakeupResource) -> object:
    return resource.trigger("iss-1", "wake-1")


def _triggered(result: object) -> object:
    return cast("IssueWakeupTriggerResult", result).triggered


def _delete_command(resource: IssueWakeupResource) -> object:
    return resource.delete_command("iss-1", "wake-1")


def _delete_eager(resource: IssueWakeupResource) -> object:
    return resource.delete("iss-1", "wake-1")


def _deleted(result: object) -> object:
    return cast("IssueWakeupDeleteResult", result).deleted


def _checkin_command(resource: IssueWakeupResource) -> object:
    return resource.checkin_command("iss-1", "wake-1", "CI still running")


def _checkin_eager(resource: IssueWakeupResource) -> object:
    return resource.checkin("iss-1", "wake-1", "CI still running")


def _checkin_value(result: object) -> object:
    return cast("ActionResult[None]", result).value


def _runs_command(resource: IssueWakeupResource) -> object:
    return resource.runs_command("iss-1", "wake-1")


def _runs_eager(resource: IssueWakeupResource) -> object:
    return resource.runs("iss-1", "wake-1")


def _run_ids(result: object) -> object:
    page = cast("IssueWakeupRunsPage", result)
    return tuple(run.id for run in page.items)


_EAGER_COMMAND_CASES = (
    _EagerCommandCase(
        "events",
        _events_command,
        _events_eager,
        "multica issue wakeup events --output json",
        b'{"event_types":["comment.created"],"loop_protection":"guard"}',
        _events_result,
        ("comment.created", "guard"),
        _set_bytes_response,
        _reset_bytes_transport,
        _assert_bytes_transport,
    ),
    _EagerCommandCase(
        "list",
        _list_command,
        _list_eager,
        "multica issue wakeup list iss-1 --output json",
        b'{"wakeups":[{"id":"wake-1","enabled":true}]}',
        _list_result,
        "wake-1",
        _set_bytes_response,
        _reset_bytes_transport,
        _assert_bytes_transport,
    ),
    _EagerCommandCase(
        "get",
        _get_command,
        _get_eager,
        "multica issue wakeup get iss-1 wake-1 --output json",
        b'{"id":"wake-1","enabled":true}',
        _wakeup_id,
        "wake-1",
        _set_bytes_response,
        _reset_bytes_transport,
        _assert_bytes_transport,
    ),
    _EagerCommandCase(
        "disable",
        _disable_command,
        _disable_eager,
        "multica issue wakeup disable iss-1 wake-1 --output json",
        b'{"id":"wake-1","enabled":false}',
        _disabled,
        False,
        _set_bytes_response,
        _reset_bytes_transport,
        _assert_bytes_transport,
    ),
    _EagerCommandCase(
        "create",
        _create_command,
        _create_eager,
        "multica issue wakeup create iss-1 --instruction 'Run checks' --kind event --event comment.created --output json",
        b'{"id":"wake-1","enabled":true}',
        _wakeup_id,
        "wake-1",
        _set_bytes_response,
        _reset_bytes_transport,
        _assert_bytes_transport,
    ),
    _EagerCommandCase(
        "update",
        _update_command,
        _update_eager,
        "multica issue wakeup update iss-1 wake-1 --instruction 'Run checks' --kind event --event comment.created --output json",
        b'{"id":"wake-1","enabled":true}',
        _reenabled,
        ("wake-1", True),
        _set_bytes_response,
        _reset_bytes_transport,
        _assert_bytes_transport,
    ),
    _EagerCommandCase(
        "trigger",
        _trigger_command,
        _trigger_eager,
        "multica issue wakeup trigger iss-1 wake-1 --output json",
        b'{"id":"wake-1","triggered":true}',
        _triggered,
        True,
        _set_bytes_response,
        _reset_bytes_transport,
        _assert_bytes_transport,
    ),
    _EagerCommandCase(
        "delete",
        _delete_command,
        _delete_eager,
        "multica issue wakeup delete iss-1 wake-1 --output json",
        b'{"id":"wake-1","deleted":true}',
        _deleted,
        True,
        _set_bytes_response,
        _reset_bytes_transport,
        _assert_bytes_transport,
    ),
    _EagerCommandCase(
        "checkin",
        _checkin_command,
        _checkin_eager,
        "multica issue wakeup checkin iss-1 wake-1 --note 'CI still running'",
        None,
        _checkin_value,
        None,
        _set_text_response,
        _reset_text_transport,
        _assert_text_transport,
    ),
    _EagerCommandCase(
        "runs",
        _runs_command,
        _runs_eager,
        "multica issue wakeup runs iss-1 wake-1 --output json",
        b'[{"id":"run-1","status":"completed","created_at":"2026-09-28T07:00:00Z"},{"id":"run-2","status":"running","created_at":"2026-09-28T08:00:00Z"}]',
        _run_ids,
        ("run-1", "run-2"),
        _set_bytes_response,
        _reset_bytes_transport,
        _assert_bytes_transport,
    ),
)


@pytest.mark.parametrize("case", _EAGER_COMMAND_CASES, ids=lambda case: case.name)
def test_all_eager_and_command_pairs_have_exact_argv_and_decoded_results(
    case: _EagerCommandCase,
) -> None:
    transport = make_transport()
    case.set_response(transport, case.response)
    resource = wakeups(transport)
    command = cast("Command[object]", case.command_builder(resource))

    command_result_value = command.run()
    assert command.commands == (case.expected_argv,)
    expected_transport_argv = tuple(shlex.split(case.expected_argv))[1:]
    case.assert_transport(transport, expected_transport_argv)
    assert case.extract(command_result_value) == case.expected_result

    case.reset_transport(transport)
    case.set_response(transport, case.response)
    eager_result = case.eager_runner(resource)
    case.assert_transport(transport, expected_transport_argv)
    assert case.extract(eager_result) == case.expected_result


@pytest.mark.parametrize(
    "condition",
    [
        {"status": "done"},
        {"assignee": "member:member-1"},
        {"label": "release"},
        {"property": {"b": 2, "a": 1}},
        {"children_done": {"stage": 2}},
        {"pull_request": "merged"},
        {"referenced_issue": {"id": "ISSUE-2", "state": "done"}},
    ],
    ids=("status", "assignee", "label", "property", "children", "pull-request", "reference"),
)
def test_all_condition_families_use_canonical_json_and_are_server_owned(
    condition: Mapping[str, object],
) -> None:
    transport = make_transport()
    command = create_args(wakeups(transport), condition=condition)
    expected_json = json.dumps(condition, separators=(",", ":"), sort_keys=True)

    assert f"--condition '{expected_json}'" in command.commands[0]
    transport.run_bytes.return_value = command_result(wakeup_payload(condition=condition))
    assert command.run().condition == condition
    transport.run_bytes.assert_called_once()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"condition": {"status": "done", "label": "release"}}, "exactly one"),
        ({"condition": {}}, "exactly one"),
        ({"condition": {"unknown": "value"}}, "exactly one"),
        ({"condition": {"status": "done"}, "event_types": ("comment.created",)}, "combined"),
        ({"condition": {"status": "done"}, "kind": "every", "interval_seconds": 60}, "event kind"),
        ({"condition": {"status": "done"}, "filter_task_id": "task-1"}, "combined"),
        ({"condition": {"assignee": "person:1"}}, "member|agent|squad"),
        ({"condition": {"children_done": {"stage": 0}}}, "stage"),
        ({"condition": {"pull_request": "open"}}, "pull_request status"),
        (
            {"condition": {"referenced_issue": {"id": "x", "state": "open"}}},
            "referenced_issue state",
        ),
        ({"condition": {"property": None}}, "property must be non-null"),
    ],
)
def test_condition_exclusivity_and_shape_rules_are_local(
    kwargs: dict[str, object], message: str
) -> None:
    transport = make_transport()
    with pytest.raises((TypeError, ValueError), match=message):
        create_args(wakeups(transport), **kwargs)
    transport.run_bytes.assert_not_called()


@dataclass(frozen=True)
class _DeadlineCase:
    name: str
    kwargs: Mapping[str, object]
    check: Callable[[_DeadlineCase, IssueWakeupResource, MagicMock], None]
    flag: str
    value: object


def _assert_valid_deadline(
    case: _DeadlineCase, resource: IssueWakeupResource, transport: MagicMock
) -> None:
    command = create_args(resource, event_types=("comment.created",), **case.kwargs)
    assert f"--{case.flag} {case.value}" in command.commands[0]


def _assert_invalid_deadline(
    case: _DeadlineCase, resource: IssueWakeupResource, transport: MagicMock
) -> None:
    with pytest.raises(ValueError):
        create_args(resource, event_types=("comment.created",), **case.kwargs)
    transport.run_bytes.assert_not_called()


def _deadline_case(name: str, field: str, value: object, valid: bool) -> _DeadlineCase:
    kwargs: dict[str, object] = {field: value, "mode": "continuous"}
    if field == "max_fires":
        kwargs["expires_in_seconds"] = 60
    return _DeadlineCase(
        name,
        kwargs,
        _assert_valid_deadline if valid else _assert_invalid_deadline,
        {"expires_in_seconds": "expires-in", "max_fires": "max-fires"}.get(field, ""),
        value,
    )


_DEADLINE_CASES = (
    _deadline_case("expires-in-min", "expires_in_seconds", 60, True),
    _deadline_case("expires-in-max", "expires_in_seconds", 31_536_000, True),
    _deadline_case("expires-in-too-small", "expires_in_seconds", 59, False),
    _deadline_case("expires-in-too-large", "expires_in_seconds", 31_536_001, False),
    _deadline_case("expires-in-bool", "expires_in_seconds", True, False),
    _deadline_case("max-fires-min", "max_fires", 1, True),
    _deadline_case("max-fires-max", "max_fires", 1000, True),
    _deadline_case("max-fires-zero", "max_fires", 0, False),
    _deadline_case("max-fires-too-large", "max_fires", 1001, False),
    _deadline_case("max-fires-bool", "max_fires", True, False),
)


@pytest.mark.parametrize("case", _DEADLINE_CASES, ids=lambda case: case.name)
def test_deadline_and_fire_limit_boundaries_and_types(case: _DeadlineCase) -> None:
    transport = make_transport()
    case.check(case, wakeups(transport), transport)


def test_deadline_exclusivity_timeout_ownership_and_omitted_target_cap() -> None:
    transport = make_transport()
    resource = wakeups(transport)
    with pytest.raises(ValueError, match="mutually exclusive"):
        create_args(
            resource,
            event_types=("comment.created",),
            expires_in_seconds=60,
            expires_at="2026-10-01T00:00:00Z",
        )
    with pytest.raises(ValueError, match="requires a deadline"):
        create_args(resource, event_types=("comment.created",), on_timeout="end")
    with pytest.raises(ValueError, match="requires event kind"):
        create_args(
            resource,
            kind="every",
            mode="continuous",
            interval_seconds=60,
            expires_in_seconds=60,
            on_timeout="wake",
        )
    continuous = create_args(resource, event_types=("comment.created",), mode="continuous")
    assert "--max-fires" not in continuous.commands[0]
    # The server-owned continuous-target cap is intentionally omitted from SDK argv.


def test_update_is_full_replacement_and_reenables_with_valid_response() -> None:
    transport = make_transport()
    command = update_args(wakeups(transport), event_types=("comment.created",), mode="continuous")
    assert "--condition" not in command.commands[0]
    transport.run_bytes.return_value = command_result(wakeup_payload(enabled=True))
    assert command.run().enabled is True

    transport.run_bytes.return_value = command_result(wakeup_payload(enabled=False))
    with pytest.raises(OutputShapeError, match="enabled"):
        update_args(wakeups(transport), event_types=("comment.created",)).run()


def _wakeup_identity_and_expiry(result: object) -> object:
    wakeup = cast("IssueWakeup", result)
    return wakeup.id, wakeup.expires_in_seconds


def _list_wakeup_expiry(result: object) -> object:
    wakeup = cast("IssueWakeupPage", result).items[0]
    return wakeup.id, wakeup.expires_in_seconds


def _event_optional_fields(result: object) -> object:
    event = cast("IssueWakeupEvents", result).events[0]
    return event.name, event.condition, event.loop_protection


def _list_response(payload: bytes) -> bytes:
    return json.dumps({"wakeups": [json.loads(payload)]}).encode()


_V2_OMITTED_WAKEUP = wakeup_payload()
_V2_NULL_WAKEUP = wakeup_payload(
    expires_in_seconds=None,
    expires_at=None,
    on_timeout=None,
    max_fires=None,
    fire_count=None,
    paused=None,
    condition=None,
    provenance=None,
)
_V2_VALID_WAKEUP = wakeup_payload(
    expires_in_seconds=3600,
    expires_at="2026-10-01T00:00:00Z",
    on_timeout="wake",
    max_fires=5,
    fire_count=2,
    paused=False,
    condition={"status": "done"},
    provenance={"source": "system"},
)
_V2_OMITTED_EVENTS = b'{"event_types":[{"name":"comment.created"}]}'
_V2_NULL_EVENTS = (
    b'{"event_types":[{"name":"comment.created","condition":null,"loop_protection":null}]}'
)
_V2_VALID_EVENTS = (
    b'{"event_types":[{"name":"comment.created","condition":{"status":"done"},'
    b'"loop_protection":"guard"}]}'
)


@dataclass(frozen=True)
class _V2DecodeCase:
    name: str
    command_builder: Callable[[IssueWakeupResource], object]
    payload: bytes
    extract: Callable[[object], object]
    expected: object


@dataclass(frozen=True)
class _V2Variant:
    name: str
    payload: bytes
    expected: object


@dataclass(frozen=True)
class _V2Entrypoint:
    name: str
    command_builder: Callable[[IssueWakeupResource], object]
    extract: Callable[[object], object]
    wrap_payload: Callable[[bytes], bytes]


def _identity_payload(payload: bytes) -> bytes:
    return payload


_V2_WAKEUP_VARIANTS = (
    _V2Variant("omitted", _V2_OMITTED_WAKEUP, ("wake-1", None)),
    _V2Variant("null", _V2_NULL_WAKEUP, ("wake-1", None)),
    _V2Variant("valid", _V2_VALID_WAKEUP, ("wake-1", 3600)),
)
_V2_WAKEUP_ENTRYPOINTS = (
    _V2Entrypoint("create", _create_command, _wakeup_identity_and_expiry, _identity_payload),
    _V2Entrypoint("update", _update_command, _wakeup_identity_and_expiry, _identity_payload),
    _V2Entrypoint("list", _list_command, _list_wakeup_expiry, _list_response),
    _V2Entrypoint("get", _get_command, _wakeup_identity_and_expiry, _identity_payload),
    _V2Entrypoint("disable", _disable_command, _wakeup_identity_and_expiry, _identity_payload),
)
_V2_EVENT_VARIANTS = (
    _V2Variant("omitted", _V2_OMITTED_EVENTS, ("comment.created", None, None)),
    _V2Variant("null", _V2_NULL_EVENTS, ("comment.created", None, None)),
    _V2Variant("valid", _V2_VALID_EVENTS, ("comment.created", {"status": "done"}, "guard")),
)
_V2_EVENTS_ENTRYPOINT = _V2Entrypoint(
    "events", _events_command, _event_optional_fields, _identity_payload
)
_V2_DECODE_CASES = tuple(
    _V2DecodeCase(
        f"{entrypoint.name}-{variant.name}",
        entrypoint.command_builder,
        entrypoint.wrap_payload(variant.payload),
        entrypoint.extract,
        variant.expected,
    )
    for entrypoint in _V2_WAKEUP_ENTRYPOINTS
    for variant in _V2_WAKEUP_VARIANTS
) + tuple(
    _V2DecodeCase(
        f"events-{variant.name}",
        _V2_EVENTS_ENTRYPOINT.command_builder,
        variant.payload,
        _V2_EVENTS_ENTRYPOINT.extract,
        variant.expected,
    )
    for variant in _V2_EVENT_VARIANTS
)


@pytest.mark.parametrize("case", _V2_DECODE_CASES, ids=lambda case: case.name)
def test_six_evolved_entrypoints_decode_optional_v2_response_states(
    case: _V2DecodeCase,
) -> None:
    transport = make_transport()
    transport.run_bytes.return_value = command_result(case.payload)
    result = cast("Command[object]", case.command_builder(wakeups(transport))).run()
    assert case.extract(result) == case.expected


@dataclass(frozen=True)
class _MalformedV2Case:
    name: str
    command_builder: Callable[[IssueWakeupResource], object]
    payload: bytes


_MALFORMED_V2_PAYLOAD = b'{"id":"wake-1","enabled":"true","expires_in_seconds":"bad"}'
_MALFORMED_V2_CASES = (
    _MalformedV2Case("create", _create_command, _MALFORMED_V2_PAYLOAD),
    _MalformedV2Case("update", _update_command, _MALFORMED_V2_PAYLOAD),
    _MalformedV2Case("list", _list_command, _list_response(_MALFORMED_V2_PAYLOAD)),
    _MalformedV2Case("get", _get_command, _MALFORMED_V2_PAYLOAD),
    _MalformedV2Case("disable", _disable_command, _MALFORMED_V2_PAYLOAD),
    _MalformedV2Case(
        "events",
        _events_command,
        b'{"event_types":[{"name":"comment.created","loop_protection":1}]}',
    ),
)


@pytest.mark.parametrize("case", _MALFORMED_V2_CASES, ids=lambda case: case.name)
def test_six_evolved_entrypoints_reject_malformed_v2_response(
    case: _MalformedV2Case,
) -> None:
    transport = make_transport()
    transport.run_bytes.return_value = command_result(case.payload)
    with pytest.raises((TypeError, ValueError)):
        cast("Command[object]", case.command_builder(wakeups(transport))).run()


@dataclass(frozen=True)
class _LifecycleAcknowledgementCase:
    name: str
    command_builder: Callable[[IssueWakeupResource], object]
    payload: bytes


_LIFECYCLE_ACKNOWLEDGEMENT_CASES = (
    _LifecycleAcknowledgementCase(
        "trigger-false", _trigger_command, b'{"id":"wake-1","triggered":false}'
    ),
    _LifecycleAcknowledgementCase(
        "delete-false", _delete_command, b'{"id":"wake-1","deleted":false}'
    ),
    _LifecycleAcknowledgementCase(
        "trigger-non-bool", _trigger_command, b'{"id":"wake-1","triggered":"yes"}'
    ),
    _LifecycleAcknowledgementCase(
        "delete-null", _delete_command, b'{"id":"wake-1","deleted":null}'
    ),
    _LifecycleAcknowledgementCase("trigger-missing-id", _trigger_command, b'{"triggered":true}'),
    _LifecycleAcknowledgementCase("delete-missing-id", _delete_command, b'{"deleted":true}'),
)


@pytest.mark.parametrize("case", _LIFECYCLE_ACKNOWLEDGEMENT_CASES, ids=lambda case: case.name)
def test_lifecycle_acknowledgements_require_true_and_complete_shape(
    case: _LifecycleAcknowledgementCase,
) -> None:
    transport = make_transport()
    resource = wakeups(transport)
    command = cast("Command[object]", case.command_builder(resource))
    transport.run_bytes.return_value = command_result(case.payload)
    with pytest.raises((TypeError, OutputShapeError)):
        command.run()


@pytest.mark.parametrize(
    "payload",
    [
        b'[{"id":"run-1","status":"running"}]',
        b'[{"id":"run-1","status":"running","created_at":"bad"}]',
        b'[{"id":"run-1","status":"running","created_at":"2026-09-28T07:00:00Z","checkin_note":1}]',
    ],
    ids=("missing-created-at", "malformed-created-at", "malformed-checkin-note"),
)
def test_runs_decode_order_and_reject_malformed_rows(payload: bytes) -> None:
    transport = make_transport()
    resource = wakeups(transport)
    valid_payload = (
        b'[{"id":"run-1","status":"completed","created_at":"2026-09-28T07:00:00Z",'
        b'"checkin_note":null},{"id":"run-2","status":"running",'
        b'"created_at":"2026-09-28T08:00:00Z"}]'
    )
    transport.run_bytes.return_value = command_result(valid_payload)
    command = resource.runs_command("iss-1", "wake-1")
    assert command.commands == ("multica issue wakeup runs iss-1 wake-1 --output json",)
    assert [item.id for item in command.run()] == ["run-1", "run-2"]
    transport.run_bytes.return_value = command_result(payload)
    with pytest.raises(TypeError):
        command.run()


@dataclass(frozen=True)
class _NoRetryCase:
    name: str
    command_builder: Callable[[IssueWakeupResource], object]


_NO_RETRY_CASES = (
    _NoRetryCase("trigger", _trigger_command),
    _NoRetryCase("delete", _delete_command),
    _NoRetryCase("update", _update_command),
)


@pytest.mark.parametrize("case", _NO_RETRY_CASES, ids=lambda case: case.name)
def test_trigger_delete_update_are_one_call_no_retry(case: _NoRetryCase) -> None:
    transport = make_transport()
    failure = CommandExecutionError("ambiguous", code="unknown")
    transport.run_bytes.side_effect = failure
    resource = wakeups(transport)
    command = cast("Command[object]", case.command_builder(resource))
    with pytest.raises(CommandExecutionError):
        command.run()
    assert transport.run_bytes.call_count == 1


@pytest.mark.parametrize("note", ["", "   "], ids=("empty", "whitespace"))
def test_checkin_rejects_blank_notes(note: str) -> None:
    transport = make_transport()
    resource = wakeups(transport)
    with pytest.raises(ValueError, match="nonblank"):
        resource.checkin_command("iss-1", "wake-1", note)


def test_checkin_is_one_call_on_server_failure() -> None:
    transport = make_transport()
    resource = wakeups(transport)
    transport.run_text.side_effect = CommandExecutionError("server-owned", code="server")
    command = resource.checkin_command("iss-1", "wake-1", "CI still running")
    assert command.commands == (
        "multica issue wakeup checkin iss-1 wake-1 --note 'CI still running'",
    )
    with pytest.raises(CommandExecutionError):
        command.run()
    assert transport.run_text.call_count == 1


@pytest.mark.parametrize(
    "expires_at",
    ["2026-10-01T00:00:00", "not-a-date", "2025-01-01T00:00:00Z"],
    ids=("missing-timezone", "malformed", "past"),
)
def test_expiry_at_requires_timezone_and_future_window(expires_at: str) -> None:
    transport = make_transport()
    resource = wakeups(transport)
    with pytest.raises(ValueError):
        create_args(resource, event_types=("comment.created",), expires_at=expires_at)
    transport.run_bytes.assert_not_called()


def test_server_owned_condition_failure_is_not_retried() -> None:
    transport = make_transport()
    transport.run_bytes.side_effect = CommandExecutionError("condition rejected", code="validation")
    command = create_args(wakeups(transport), condition={"status": "done"})
    with pytest.raises(CommandExecutionError):
        command.run()
    assert transport.run_bytes.call_count == 1
