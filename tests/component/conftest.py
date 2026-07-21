from __future__ import annotations

import os
import pathlib
from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import IssueStatus, ProjectStatus
from tests.component.resource_support import CommandCase


@pytest.fixture
def fake_cli_client(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> MulticaClient:
    """Return a client whose PATH resolves to the fake multica executable."""
    fake_dir = str(pathlib.Path(request.config.rootpath) / "tests" / "fixtures")
    monkeypatch.setenv("PATH", fake_dir + ":" + os.environ.get("PATH", ""))
    config = ClientConfig(executable="fake_multica.py")
    return MulticaClient(config)


def patch_client_transport(client: MulticaClient, transport: MagicMock) -> None:
    """Replace transport instances on the client resource tree."""
    for name in dir(client):
        if name.startswith("_"):
            continue
        resource = getattr(client, name)
        if hasattr(resource, "_transport"):
            object.__setattr__(resource, "_transport", transport)
        for child_name in dir(resource):
            if child_name.startswith("_"):
                continue
            child = getattr(resource, child_name, None)
            if child is not None and hasattr(child, "_transport"):
                object.__setattr__(child, "_transport", transport)


def _transport_error(case: CommandCase, argv: tuple[str, ...]) -> BaseException:
    from multica_py.exceptions import (
        AuthenticationError,
        CommandExecutionError,
        NetworkError,
        NotFoundError,
        ValidationError,
    )

    exc_map = {
        2: NetworkError,
        3: AuthenticationError,
        4: NotFoundError,
        5: ValidationError,
    }
    exc_type = exc_map.get(case.exit_code, CommandExecutionError)
    return exc_type(
        f"exit {case.exit_code}",
        exit_code=case.exit_code,
        stdout=case.stdout,
        stderr=case.stderr,
        argv=argv,
    )


def configure_mock_transport(case: CommandCase, transport: MagicMock) -> None:
    """Configure transport mocks for one command case."""
    import datetime

    stdout_bytes = case.stdout.encode("utf-8")
    stderr_bytes = case.stderr.encode("utf-8")

    def run_bytes(
        argv: tuple[str, ...],
        stdin: bytes | None = None,
        timeout: object | None = None,
    ) -> RawCommandResult:
        if case.exit_code != 0:
            raise _transport_error(case, argv)
        return RawCommandResult(
            argv=argv,
            exit_code=case.exit_code,
            stdout=stdout_bytes,
            stderr=stderr_bytes,
            duration=datetime.timedelta(),
        )

    def run_text(argv: tuple[str, ...]) -> TextResult:
        if case.exit_code != 0:
            raise _transport_error(case, argv)
        return TextResult(text=case.stdout, stderr=case.stderr, exit_code=case.exit_code)

    transport.run_bytes.side_effect = run_bytes
    transport.run_text.side_effect = run_text
    transport.spawn.side_effect = lambda argv: MagicMock()


def assert_command_argv(case: CommandCase, client: MulticaClient) -> None:
    """Invoke one case and assert exact argv sent to transport."""
    mock = MagicMock(spec=CliTransport)
    configure_mock_transport(case, mock)
    patch_client_transport(client, mock)
    case.invoke(client)
    if mock.run_bytes.called:
        assert mock.run_bytes.call_args.args[0] == case.expected_argv
    elif mock.run_text.called:
        assert mock.run_text.call_args.args[0] == case.expected_argv
    else:
        mock.spawn.assert_called_once_with(case.expected_argv)


def _nonempty(result: object) -> None:
    assert result is not None
    assert len(result) > 0  # type: ignore[arg-type]


def _labels(result: object) -> None:
    _nonempty(result)
    assert result[0].id == "lbl_001"  # type: ignore[index]


def _not_none(result: object) -> None:
    assert result is not None


def _none(result: object) -> None:
    assert result is None


def _auth_login(result: object) -> None:
    assert result == "Login successful"


def _auth_status(result: object) -> None:
    assert result.authenticated is True  # type: ignore[attr-defined]


def _auth_logout(result: object) -> None:
    assert result.authenticated is False  # type: ignore[attr-defined]


def _daemon_status(result: object) -> None:
    assert result.running is True  # type: ignore[attr-defined]


def _issue_done(result: object) -> None:
    assert result.status == IssueStatus.done  # type: ignore[attr-defined]


def _deprioritized(result: object) -> None:
    assert "deprioritized" in result  # type: ignore[operator]


def _project_completed(result: object) -> None:
    assert result.status == ProjectStatus.completed  # type: ignore[attr-defined]


def _maintenance_version(result: object) -> None:
    assert result.version == "0.1.0"  # type: ignore[attr-defined]


COMMAND_CHECKS: dict[str, Callable[[object], None]] = {
    "nonempty": _nonempty,
    "not_none": _not_none,
    "none": _none,
    "labels": _labels,
    "auth_login": _auth_login,
    "auth_status": _auth_status,
    "auth_logout": _auth_logout,
    "daemon_status": _daemon_status,
    "issue_done": _issue_done,
    "deprioritized": _deprioritized,
    "project_completed": _project_completed,
    "maintenance_version": _maintenance_version,
}
