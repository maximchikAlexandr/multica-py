from __future__ import annotations

import datetime
import sys
from dataclasses import dataclass
from subprocess import CompletedProcess

import pytest

from multica_py._internal.redaction import redact_argv, redact_text
from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport, classify_cli_failure
from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy
from multica_py.exceptions import (
    AuthenticationError,
    CommandExecutionError,
    CommandTimeoutError,
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


def test_command_plan_uses_configuration_snapshot_after_profile_switch() -> None:
    from multica_py._internal.commands import _Step
    from multica_py.client import MulticaClient

    class RecordingTransport(CliTransport):
        def __init__(self, config: ClientConfig) -> None:
            super().__init__(config)
            self.calls: list[tuple[str, ...]] = []

        def run_bytes(
            self,
            command_args: tuple[str, ...],
            *,
            stdin: bytes | None = None,
            timeout: datetime.timedelta | None = None,
        ) -> RawCommandResult:
            del stdin, timeout
            self.calls.append(self.build_full_argv(command_args))
            return RawCommandResult(
                argv=self.build_full_argv(command_args),
                exit_code=0,
                stdout=b"{}",
                stderr=b"",
                duration=datetime.timedelta(),
            )

    profile_a = ClientConfig(profile="a")
    transport = RecordingTransport(profile_a)
    client = MulticaClient(profile_a)
    client.issues._transport = transport
    client.issues._config = profile_a
    command = client.issues._plan(
        steps=(_Step(("issue", "get", "issue_123"), "run_bytes"),),
        finalize=lambda results: results,
    )

    profile_b = client.with_profile("b").config
    client.issues._config = profile_b
    transport._config = profile_b

    assert command.commands == ("multica --profile a issue get issue_123",)
    command.run()
    assert transport.calls == [("multica", "--profile", "a", "issue", "get", "issue_123")]


def test_transport_redacts_token():
    redacted = redact_argv(("multica", "auth", "login", "--token=secret123"))
    assert "secret123" not in " ".join(redacted)
    assert "***" in " ".join(redacted)


def test_transport_redacts_split_token_args():
    redacted = redact_argv(("multica", "auth", "login", "--token", "secret123"))
    assert "secret123" not in " ".join(redacted)
    assert redacted[-1] == "***"


def test_command_plan_repr_never_exposes_secret_bearing_state() -> None:
    from multica_py.client import MulticaClient

    client = MulticaClient(
        ClientConfig(environment=(("MULTICA_TOKEN", "env-secret"),)),
    )
    command = client.auth.login_command("argv-secret")

    rendered = " ".join((repr(command), repr(command._plan), repr(command._plan.steps[0])))
    assert "argv-secret" not in rendered
    assert "env-secret" not in rendered


def test_client_config_rejects_server_url_userinfo() -> None:
    with pytest.raises(ValueError, match="must not contain username or password"):
        ClientConfig(server_url="https://alice:s3cr3t@example.com")


@pytest.mark.parametrize(
    ("server_url", "secret"),
    (
        ("https://example.com/api?access_token=query-secret", "query-secret"),
        ("https://example.com/api#fragment-secret", "fragment-secret"),
    ),
)
def test_client_config_rejects_server_url_query_or_fragment(server_url: str, secret: str) -> None:
    with pytest.raises(ValueError, match="must not contain query or fragment") as excinfo:
        ClientConfig(server_url=server_url)
    assert secret not in str(excinfo.value)


def test_server_url_query_secret_is_redacted_across_public_surfaces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import multica_py.config as config_module
    from multica_py.client import MulticaClient

    query_secret = "query-secret"
    server_url = f"https://example.com/api?access_token={query_secret}"
    monkeypatch.setattr(config_module, "_validate_server_url", lambda url: None)
    config = ClientConfig(server_url=server_url)
    command = MulticaClient(config).auth.status_command()

    assert query_secret not in " ".join(command.commands)
    assert query_secret not in repr(command)
    assert "access_token=***" in " ".join(command.commands)

    executed: list[tuple[str, ...]] = []

    def fake_run_with_timeout(
        argv: tuple[str, ...],
        *,
        stdin: bytes | None,
        timeout: datetime.timedelta | None,
        cwd: str | None,
        env: dict[str, str],
    ) -> CompletedProcess[bytes]:
        del stdin, timeout, cwd, env
        executed.append(argv)
        return CompletedProcess(
            argv,
            2,
            stdout=f"stdout {query_secret}".encode(),
            stderr=f"stderr {query_secret}".encode(),
        )

    monkeypatch.setattr("multica_py._internal.transport.run_with_timeout", fake_run_with_timeout)
    transport = CliTransport(config)
    with pytest.raises(NetworkError) as excinfo:
        transport.run_text(("auth", "status"))

    exc = excinfo.value
    assert executed == [("multica", "--server-url", server_url, "auth", "status")]
    assert query_secret not in exc.argv
    assert query_secret not in exc.stdout
    assert query_secret not in exc.stderr
    assert "***" in exc.argv[2]
    assert "***" in exc.stdout
    assert "***" in exc.stderr


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


@pytest.mark.parametrize("policy", (CompatibilityPolicy.strict, CompatibilityPolicy.warn))
def test_snapshot_transports_share_compatibility_preflight_cache(
    policy: CompatibilityPolicy,
) -> None:
    class RecordingTransport(CliTransport):
        def __init__(self, config: ClientConfig) -> None:
            super().__init__(config)
            self.commands: list[tuple[str, ...]] = []

        def _execute(
            self,
            command_args: tuple[str, ...],
            *,
            check_compat: bool = True,
            stdin: bytes | None = None,
            timeout: datetime.timedelta | None = None,
        ) -> RawCommandResult:
            del stdin, timeout
            if check_compat:
                self._check_compat()
            self.commands.append(command_args)
            stdout = b'{"version":"1.0.0"}' if command_args == ("version",) else b"{}"
            return RawCommandResult(
                argv=("multica", *command_args),
                exit_code=0,
                stdout=stdout,
                stderr=b"",
                duration=datetime.timedelta(),
            )

    config = ClientConfig(
        compatibility=policy,
        min_cli_version="0.0.0",
        max_cli_version="2.0.0",
    )
    transport = RecordingTransport(config)
    from multica_py.resources.auth import AuthResource

    auth = AuthResource(transport, config)
    auth.status()
    auth.logout()

    assert transport.commands == [
        ("version",),
        ("auth", "status", "--output", "json"),
        ("auth", "logout", "--output", "json"),
    ]


def test_transport_strict_policy_rejects_unparseable_version_output_from_check():
    config = ClientConfig(executable=sys.executable, compatibility=CompatibilityPolicy.strict)
    transport = CliTransport(config)
    with pytest.raises(UnsupportedCliVersionError, match="Failed to parse CLI version output"):
        transport._check_compat()


def test_redact_text_redacts_embedded_token_value():
    redacted = redact_text("token: secret123", secret_values=("secret123",))
    assert "secret123" not in redacted
    assert "***" in redacted


def test_transport_command_timeout_propagates() -> None:
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config)

    def _raise_timeout(*args: object, **kwargs: object) -> object:
        raise CommandTimeoutError()

    transport._execute = _raise_timeout  # type: ignore[assignment,method-assign]
    with pytest.raises(CommandTimeoutError):
        transport.run_text(("issue", "list"))
