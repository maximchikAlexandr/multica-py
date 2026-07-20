from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from multica_py._internal.redaction import redact_argv
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.exceptions import (
    AuthenticationError,
    CommandExecutionError,
    NotFoundError,
    OutputShapeError,
)
from tests.component.conftest import configure_mock_transport, patch_client_transport
from tests.component.resource_support import CommandCase, ExpectedError

ERROR_COMMAND_CASES: tuple[CommandCase, ...] = (
    CommandCase(
        id="labels.get.not-found",
        invoke=lambda c: c.labels.get("missing-id"),
        expected_argv=("label", "get", "missing-id", "--output", "json"),
        stdout='{"error":"not found"}',
        exit_code=4,
        expected_error=ExpectedError(NotFoundError, 4),
        sdk_method="labels.get",
    ),
    CommandCase(
        id="agents.list.malformed-json",
        invoke=lambda c: c.agents.list(),
        expected_argv=("agent", "list", "--output", "json"),
        stdout="{not-json",
        expected_error=ExpectedError(OutputShapeError, None),
        sdk_method="agents.list",
    ),
    CommandCase(
        id="auth.login.secret-redaction",
        invoke=lambda c: c.auth.login("secret-token"),
        expected_argv=("auth", "login", "--token", "secret-token"),
        stderr="secret-token leaked",
        exit_code=3,
        expected_error=ExpectedError(AuthenticationError, 3),
        sdk_method="auth.login",
    ),
    CommandCase(
        id="projects.resources.list.malformed-json",
        invoke=lambda c: c.projects.resources.list("pr_001"),
        expected_argv=("project", "resource", "list", "pr_001", "--output", "json"),
        stdout="{not-json",
        expected_error=ExpectedError(OutputShapeError),
        sdk_method="projects.resources.list",
    ),
    CommandCase(
        id="projects.resources.remove.not-found",
        invoke=lambda c: c.projects.resources.remove("pr_001", "missing"),
        expected_argv=("project", "resource", "remove", "pr_001", "missing"),
        exit_code=4,
        expected_error=ExpectedError(CommandExecutionError),
        sdk_method="projects.resources.remove",
    ),
)


@pytest.mark.parametrize("case", ERROR_COMMAND_CASES, ids=lambda item: item.id)
def test_error_mapping(case: CommandCase, fake_cli_client: MulticaClient) -> None:
    mock = MagicMock(spec=CliTransport)
    configure_mock_transport(case, mock)
    patch_client_transport(fake_cli_client, mock)
    expected = case.expected_error
    assert isinstance(expected, ExpectedError)
    with pytest.raises(expected.exc_type) as exc_info:
        case.invoke(fake_cli_client)
    if expected.exit_code is not None:
        assert exc_info.value.exit_code == expected.exit_code  # type: ignore[attr-defined]


def test_secret_redaction_in_error_argv() -> None:
    redacted = redact_argv(("auth", "login", "--token", "secret-token"))
    assert "secret-token" not in " ".join(redacted)
