from __future__ import annotations

import datetime
from typing import cast
from unittest.mock import MagicMock

import msgspec
import pytest

from multica_py._internal.commands import Command
from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.exceptions import JsonOutputError, NetworkError
from multica_py.models.common import ActionResult
from multica_py.models.system import (
    RepositoryMutationResult,
    RepositoryRecord,
    RuntimeUpdate,
    RuntimeUpdateResult,
)
from multica_py.resources._base import BaseResource
from multica_py.resources.auth import AuthResource
from multica_py.resources.repositories import RepositoryResource
from multica_py.resources.runtimes import RuntimeResource


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
            RuntimeResource(transport, ClientConfig()).update_command(
                "r1", RuntimeUpdate(target_version="1.2.3")
            ),
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


def test_action_case_table_contains_all_approved_void_surfaces() -> None:
    from tests.cases.operations import OPERATION_CASES

    approved = {
        "agents.archive",
        "agents.avatar",
        "agents.restore",
        "agents.skills.set",
        "autopilots.delete",
        "autopilots.trigger_delete",
        "configuration.set",
        "issues.cancel_task",
        "issues.comments.delete",
        "issues.comments.resolve",
        "issues.comments.unresolve",
        "issues.metadata.delete",
        "issues.rerun",
        "issues.subscribers.add",
        "issues.subscribers.remove",
        "labels.delete",
        "projects.delete",
        "projects.resources.remove",
        "runtimes.delete",
        "skills.delete",
        "skills.files.delete",
        "squads.members.add",
        "squads.members.remove",
        "workspaces.switch",
        "workspaces.watch",
        "workspaces.unwatch",
    }
    covered = {case.sdk_method for case in OPERATION_CASES if case.sdk_method in approved}
    assert covered == approved
