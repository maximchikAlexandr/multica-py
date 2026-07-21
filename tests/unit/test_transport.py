from __future__ import annotations

import datetime
import sys
from dataclasses import dataclass

import pytest

from multica_py._internal.redaction import redact_argv, redact_text
from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport, classify_cli_failure
from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy
from multica_py.exceptions import (
    AuthenticationError,
    CommandExecutionError,
    NetworkError,
    NotFoundError,
    UnsupportedCliVersionError,
    ValidationError,
)


@dataclass(frozen=True)
class TransportErrorCase:
    exit_code: int
    stderr: bytes
    expected_exc: type[Exception]
    id: str


_TRANSPORT_ERROR_CASES: tuple[TransportErrorCase, ...] = (
    TransportErrorCase(
        exit_code=2, stderr=b"error", expected_exc=NetworkError, id="exit-2-network"
    ),
    TransportErrorCase(
        exit_code=3, stderr=b"error", expected_exc=AuthenticationError, id="exit-3-auth"
    ),
    TransportErrorCase(
        exit_code=4, stderr=b"error", expected_exc=NotFoundError, id="exit-4-notfound"
    ),
    TransportErrorCase(
        exit_code=5, stderr=b"error", expected_exc=ValidationError, id="exit-5-validation"
    ),
    TransportErrorCase(
        exit_code=99, stderr=b"error", expected_exc=CommandExecutionError, id="exit-99-generic"
    ),
)

_LEGACY_ERROR_CASES: tuple[tuple[int, bytes, type[Exception], int], ...] = (
    (1, b"Error: GET /api/labels/x returned 404: missing", NotFoundError, 4),
    (1, b"Error: GET /api/workspaces returned 401: unauthorized", AuthenticationError, 3),
    (1, b"Error: POST /api/labels returned 422: invalid", ValidationError, 5),
    (1, b"dial tcp 127.0.0.1:58553: connect: connection refused", NetworkError, 2),
)


def test_transport_builds_correct_argv():
    config = ClientConfig(
        executable="/usr/local/bin/multica",
        server_url="https://example.com",
        workspace_id="ws_001",
    )
    transport = CliTransport(config)
    argv = transport._build_full_argv(("issue", "list"))
    assert argv == (
        "/usr/local/bin/multica",
        "--server-url",
        "https://example.com",
        "--workspace-id",
        "ws_001",
        "issue",
        "list",
    )


def test_transport_redacts_token():
    redacted = redact_argv(("multica", "auth", "login", "--token=secret123"))
    assert "secret123" not in " ".join(redacted)
    assert "***" in " ".join(redacted)


def test_transport_redacts_split_token_args():
    redacted = redact_argv(("multica", "auth", "login", "--token", "secret123"))
    assert "secret123" not in " ".join(redacted)
    assert redacted[-1] == "***"


def test_transport_environment_isolation():
    config = ClientConfig(executable=sys.executable, environment=(("MULTICA_TOKEN", "test"),))
    transport = CliTransport(config)
    code = "import os; print(os.environ.get('MULTICA_TOKEN', 'NOT_SET'))"
    result = transport.run_text(("-c", code))
    assert result.text.strip() == "test"


@pytest.mark.parametrize(
    "case",
    _TRANSPORT_ERROR_CASES,
    ids=lambda c: c.id,
)
def test_exit_code_maps_to_exception(case: TransportErrorCase) -> None:
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config)
    transport._execute = lambda *args, **kwargs: RawCommandResult(  # type: ignore[method-assign]
        argv=("multica", "project", "get", "missing"),
        exit_code=case.exit_code,
        stdout=b"",
        stderr=case.stderr,
        duration=datetime.timedelta(),
    )
    with pytest.raises(case.expected_exc) as excinfo:
        transport.run_text(("project", "get", "missing"))
    exc = excinfo.value
    assert isinstance(exc, CommandExecutionError)
    assert exc.exit_code == case.exit_code


@pytest.mark.parametrize(
    ("exit_code", "stderr", "expected_exc", "reported_exit_code"),
    _LEGACY_ERROR_CASES,
)
def test_legacy_exit_code_one_classifies_from_stderr(
    exit_code: int,
    stderr: bytes,
    expected_exc: type[Exception],
    reported_exit_code: int,
) -> None:
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config)
    transport._execute = lambda *args, **kwargs: RawCommandResult(  # type: ignore[method-assign]
        argv=("multica", "label", "get", "missing"),
        exit_code=exit_code,
        stdout=b"",
        stderr=stderr,
        duration=datetime.timedelta(),
    )
    with pytest.raises(expected_exc) as excinfo:
        transport.run_text(("label", "get", "missing"))
    exc = excinfo.value
    assert isinstance(exc, CommandExecutionError)
    assert exc.exit_code == reported_exit_code


def test_classify_cli_failure_maps_http_status() -> None:
    exc_class, reported = classify_cli_failure(
        exit_code=1,
        stdout="",
        stderr="Error: GET /api/labels/x returned 404: missing",
    )
    assert exc_class is NotFoundError
    assert reported == 4


def test_exit_code_mapping_preserves_context() -> None:
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config)
    transport._execute = lambda *args, **kwargs: RawCommandResult(  # type: ignore[method-assign]
        argv=("multica", "auth", "status"),
        exit_code=3,
        stdout=b"unauthorized",
        stderr=b"forbidden",
        duration=datetime.timedelta(),
    )
    with pytest.raises(AuthenticationError) as excinfo:
        transport.run_text(("auth", "status"))
    exc = excinfo.value
    assert exc.stdout == "unauthorized"
    assert exc.stderr == "forbidden"
    assert exc.argv == ("multica", "auth", "status")


def test_transport_stdout_stderr_capture():
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config)
    code = "import sys; sys.stdout.write('out'); sys.stderr.write('err')"
    result = transport.run_text(("-c", code))
    assert result.text == "out"
    assert result.stderr == "err"


def test_transport_redacts_secret_values_from_exception_streams():
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config)
    transport._execute = lambda *args, **kwargs: RawCommandResult(  # type: ignore[method-assign]
        argv=("multica", "auth", "login", "--token", "***"),
        exit_code=2,
        stdout=b"token=secret123",
        stderr=b"--token secret123",
        duration=datetime.timedelta(),
        secret_values=("secret123",),
    )
    with pytest.raises(NetworkError) as excinfo:
        transport.run_text(("auth", "login", "--token", "secret123"))
    exc = excinfo.value
    assert "secret123" not in exc.stdout
    assert "secret123" not in exc.stderr
    assert "***" in exc.stdout
    assert "***" in exc.stderr
    assert exc.argv[-1] == "***"


def test_transport_warn_policy_rejects_unparseable_version_output_from_check():
    config = ClientConfig(executable=sys.executable, compatibility=CompatibilityPolicy.warn)
    transport = CliTransport(config)
    with pytest.warns(UserWarning, match="Failed to parse CLI version output"):
        transport._check_compat()


def test_transport_strict_policy_rejects_unparseable_version_output_from_check():
    config = ClientConfig(executable=sys.executable, compatibility=CompatibilityPolicy.strict)
    transport = CliTransport(config)
    with pytest.raises(UnsupportedCliVersionError, match="Failed to parse CLI version output"):
        transport._check_compat()


def test_redact_text_redacts_embedded_token_value():
    redacted = redact_text("token: secret123", secret_values=("secret123",))
    assert "secret123" not in redacted
    assert "***" in redacted
