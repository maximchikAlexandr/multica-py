from __future__ import annotations

import datetime
import inspect
import typing
from typing import cast
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.commands import Command
from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.entities.projects import Project as BoundProject
from multica_py.enums import ProjectStatus
from multica_py.exceptions import JsonOutputError, NetworkError
from multica_py.models.common import ActionResult
from multica_py.models.system import (
    RepositoryMutationResult,
    RepositoryRecord,
    RuntimeUpdateResult,
)
from multica_py.resources._base import BaseResource
from multica_py.resources.auth import AuthResource
from multica_py.resources.configuration import ConfigurationResource
from multica_py.resources.repositories import RepositoryResource
from multica_py.resources.runtimes import RuntimeResource
from tests.cases.operations import OPERATION_CASES, RESOURCE_SPECS

APPROVED_ACTION_METHODS = frozenset(
    {
        "agents.archive",
        "agents.avatar",
        "agents.restore",
        "agents.skills.set",
        "autopilots.delete",
        "autopilots.trigger_delete",
        "auth.login",
        "configuration.set",
        "issues.cancel_task",
        "issues.comments.delete",
        "issues.comments.resolve",
        "issues.comments.unresolve",
        "issues.deprioritize",
        "issues.metadata.delete",
        "issues.properties.unset",
        "issues.rerun",
        "plugins.init",
        "issues.subscribers.add",
        "issues.subscribers.remove",
        "labels.delete",
        "projects.delete",
        "projects.resources.remove",
        "repositories.add",
        "repositories.remove",
        "runtimes.delete",
        "runtimes.update",
        "skills.delete",
        "skills.files.delete",
        "squads.members.add",
        "squads.members.remove",
        "workspaces.switch",
        "workspaces.watch",
        "workspaces.unwatch",
    }
)


def _transport() -> MagicMock:
    transport = MagicMock(spec=CliTransport)
    transport.build_full_argv.side_effect = lambda args: ("multica", *args)
    return transport


def test_void_adapter_wraps_success_once_and_redacts_public_message() -> None:
    transport = _transport()
    transport.run_text.return_value = TextResult("completed token: secret-value", "", 0)
    result = BaseResource(transport, ClientConfig())._action_command(("demo", "delete")).run()

    assert result == ActionResult(success=True, value=None, message="completed token: ***")
    assert not isinstance(result.value, ActionResult)


@pytest.mark.parametrize(
    ("key", "secret"),
    (
        ("third_party_api_key", "opaque-secret-7Yp9"),
        ("openai.api_key", "opaque-config-secret-5Mz7"),
    ),
)
def test_configuration_set_redacts_bare_secret_from_preview_and_message(
    key: str, secret: str
) -> None:
    transport = _transport()
    transport.run_text.return_value = TextResult(f"stored {secret}", "", 0)

    command = ConfigurationResource(transport, ClientConfig()).set_command(key, secret)

    assert secret not in command.commands[0]
    assert secret not in repr(command)
    assert "***" in command.commands[0]

    result = command.run()

    assert result.message == "stored ***"
    assert secret not in (result.message or "")


@pytest.mark.parametrize(
    ("operation", "expected_type"),
    (
        ("repository", RepositoryMutationResult),
        ("runtime", RuntimeUpdateResult),
    ),
)
def test_payload_adapters_preserve_decoded_value(
    operation: str, expected_type: type[object]
) -> None:
    transport = _transport()
    if operation == "repository":
        payload: object = RepositoryMutationResult(
            workspace_id="w1",
            added=(RepositoryRecord(url="https://example.test/repo.git"),),
            repos=(),
        )
        command = cast(
            "Command[object]",
            RepositoryResource(transport, ClientConfig()).add_command(
                ("https://example.test/repo.git",)
            ),
        )
    else:
        payload = RuntimeUpdateResult(id="r1", status="updated")
        command = cast(
            "Command[object]",
            RuntimeResource(transport, ClientConfig()).update_command("r1", target_version="1.2.3"),
        )
    transport.run_bytes.return_value = RawCommandResult(
        argv=tuple(command.commands[0].split()[1:]),
        exit_code=0,
        stdout=msgspec.json.encode(payload),
        stderr=b"",
        duration=datetime.timedelta(),
    )

    result = command.run()

    assert isinstance(result, ActionResult)
    assert result.success
    assert isinstance(result.value, expected_type)
    assert result.value == payload


def test_token_login_wraps_scalar_and_interactive_login_stays_process() -> None:
    transport = _transport()
    auth = AuthResource(transport, ClientConfig())
    transport.run_text.return_value = TextResult("login successful", "", 0)

    token_result = auth.login("secret-token")

    assert token_result == ActionResult(value="login successful")
    assert auth.login_command(None).commands == ("multica auth login",)
    assert auth.login_command("secret-token").commands == ("multica auth login --token '***'",)


def test_token_login_redacts_echoed_bare_token_from_action_value() -> None:
    transport = _transport()
    secret = "opaque-login-secret-4Qx8"
    auth = AuthResource(transport, ClientConfig())
    transport.run_text.return_value = TextResult(f"authenticated {secret}", "", 0)

    command = auth.login_command(secret)

    assert secret not in command.commands[0]
    assert secret not in repr(command)

    result = command.run()

    assert result.value == "authenticated ***"
    assert secret not in (result.value or "")


def test_interactive_login_runs_as_managed_process() -> None:
    transport = _transport()
    process = MagicMock()
    transport.spawn.return_value = process

    result = AuthResource(transport, ClientConfig()).login()

    assert result is process
    transport.spawn.assert_called_once_with(("auth", "login"))


def test_action_transport_and_decode_failures_are_not_wrapped() -> None:
    transport = _transport()
    auth = AuthResource(transport, ClientConfig())
    transport.run_text.side_effect = NetworkError("transport failed")
    with pytest.raises(NetworkError, match="transport failed"):
        auth.login("secret-token")

    transport.run_text.side_effect = None
    transport.run_bytes.return_value = RawCommandResult(
        argv=("multica", "repo", "add"),
        exit_code=0,
        stdout=b"not-json",
        stderr=b"",
        duration=datetime.timedelta(),
    )
    with pytest.raises(JsonOutputError):
        RepositoryResource(transport, ClientConfig()).add_command(
            ("https://example.test/repo.git",)
        ).run()


@pytest.mark.parametrize("success", (True, False), ids=("success", "unsuccessful"))
def test_bound_action_mapper_preserves_identity_and_gates_invalidation(success: bool) -> None:
    transport = _transport()
    expected = ActionResult[None](success=success, value=None)
    child = BaseResource(transport, ClientConfig())._plan(
        steps=(), finalize=lambda _results: expected
    )
    client = MagicMock()
    client.projects._remove_resource_command.side_effect = lambda *_args, invalidate, **_kwargs: (
        child._map(invalidate)
    )
    entity = BoundProject(
        id="p1",
        name="Project",
        status=ProjectStatus.planned,
        _client=client,
    )
    relation = MagicMock()
    entity._set_runtime("_resources", relation)

    result = entity.remove_resource("r1")

    assert result is expected
    if success:
        relation.invalidate.assert_called_once_with()
    else:
        relation.invalidate.assert_not_called()


def test_action_case_table_contains_all_approved_void_surfaces() -> None:
    approved = APPROVED_ACTION_METHODS - {
        "auth.login",
        "issues.deprioritize",
        "repositories.add",
        "repositories.remove",
        "runtimes.update",
    }
    covered = {case.sdk_method for case in OPERATION_CASES if case.sdk_method in approved}
    assert covered == approved


def test_contract_manual_natural_categories_do_not_use_action_results() -> None:
    import pathlib

    from tools.upstream_contract.contract import validate_contract

    raw = validate_contract(pathlib.Path("contracts/sdk-contract.json")).raw
    catalogs = cast("dict[str, object]", raw["catalogs"])
    signatures = cast("dict[str, object]", catalogs["signatures"])
    for signature_id in (
        "auth_logout_manual",
        "daemon_restart_manual",
        "daemon_stop_manual",
        "issues_assign_manual",
        "issues_metadata_set_typed_manual",
        "issues_reorder_manual",
    ):
        assert "action_result" not in str(signatures[signature_id])


def _contains_action_result(annotation: object) -> bool:
    if typing.get_origin(annotation) is ActionResult or annotation is ActionResult:
        return True
    return any(_contains_action_result(argument) for argument in typing.get_args(annotation))


def test_action_response_matrix_excludes_natural_categories_and_bare_none() -> None:
    canonical_cases = {case.sdk_method: case for case in OPERATION_CASES if case.is_canonical}
    assert set(canonical_cases) >= APPROVED_ACTION_METHODS

    for resource_attr, resource_type in RESOURCE_SPECS:
        for method_name, member in resource_type.__dict__.items():
            if method_name.startswith("_") or method_name.endswith("_command"):
                continue
            function = (
                member.__func__ if isinstance(member, (classmethod, staticmethod)) else member
            )
            if not inspect.isfunction(function):
                continue
            sdk_method = next(
                (
                    case.sdk_method
                    for case in canonical_cases.values()
                    if case.resource_attr == resource_attr and case.method == method_name
                ),
                None,
            )
            if sdk_method is None:
                continue
            overloads = typing.get_overloads(function) or (function,)
            returns = tuple(typing.get_type_hints(overload)["return"] for overload in overloads)
            assert all(return_type is not type(None) for return_type in returns), sdk_method
            has_action_result = any(_contains_action_result(return_type) for return_type in returns)
            if has_action_result:
                assert sdk_method in APPROVED_ACTION_METHODS, sdk_method
