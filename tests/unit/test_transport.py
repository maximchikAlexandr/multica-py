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
    ConflictError,
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


@dataclass(frozen=True)
class LegacyErrorCase:
    id: str
    exit_code: int
    stderr: bytes
    expected_exc: type[Exception]
    reported_exit_code: int


@dataclass(frozen=True)
class MarkerCase:
    id: str
    diagnostic: str
    expected_exc: type[Exception]


@dataclass(frozen=True)
class DetailCase:
    id: str
    stdout: bytes
    stderr: bytes
    expected_exc: type[CommandExecutionError]
    expected_exit_code: int
    expected_message: str


@dataclass(frozen=True)
class EnvironmentSecretCase:
    id: str
    env_key: str


@dataclass(frozen=True)
class UrlSecretCase:
    id: str
    server_url: str
    secret: str


@dataclass(frozen=True)
class CompatibilityPolicyCase:
    id: str
    policy: CompatibilityPolicy


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

_LEGACY_ERROR_CASES: tuple[LegacyErrorCase, ...] = (
    LegacyErrorCase(
        "http-409", 1, b"Error: GET /api/skills returned 409: already exists", ConflictError, 1
    ),
    LegacyErrorCase(
        "http-404", 1, b"Error: GET /api/labels/x returned 404: missing", NotFoundError, 4
    ),
    LegacyErrorCase(
        "http-401",
        1,
        b"Error: GET /api/workspaces returned 401: unauthorized",
        AuthenticationError,
        3,
    ),
    LegacyErrorCase(
        "http-400", 1, b"Error: POST /api/agents returned 400: invalid", ValidationError, 5
    ),
    LegacyErrorCase(
        "http-422", 1, b"Error: POST /api/labels returned 422: invalid", ValidationError, 5
    ),
    LegacyErrorCase(
        "conflict-english",
        1,
        b"Request conflict: a skill with this name already exists",
        ConflictError,
        1,
    ),
    LegacyErrorCase(
        "conflict-chinese", 1, "请求冲突\uff1a该名称的 skill 已存在".encode(), ConflictError, 1
    ),
    LegacyErrorCase(
        "conflict-fallback-english",
        1,
        b"The request conflicts with the current state of the resource "
        b"(it may already exist or have changed since you last fetched it). "
        b"Re-fetch the latest state and try again.",
        ConflictError,
        1,
    ),
    LegacyErrorCase(
        "conflict-fallback-chinese",
        1,
        "请求与资源的当前状态冲突（可能已存在，或自上次获取后已被修改）。请重新获取最新状态后再试。".encode(),  # noqa: RUF001
        ConflictError,
        1,
    ),
    LegacyErrorCase(
        "validation-english",
        1,
        b"Invalid request: thinking level is unsupported",
        ValidationError,
        5,
    ),
    LegacyErrorCase(
        "validation-chinese",
        1,
        "请求无效\uff1athinking level 不受支持".encode(),
        ValidationError,
        5,
    ),
    LegacyErrorCase(
        "validation-fallback-english",
        1,
        b"The request was invalid. Check the values you provided; run the command with "
        b"--help to see the expected format.",
        ValidationError,
        5,
    ),
    LegacyErrorCase(
        "validation-fallback-chinese",
        1,
        "请求无效。请检查所填写的参数；可用 --help 查看期望的格式。".encode(),  # noqa: RUF001
        ValidationError,
        5,
    ),
    LegacyErrorCase(
        "local-concurrency",
        1,
        b"--max-concurrent-tasks must be between 1 and 50 (got 51)",
        ValidationError,
        5,
    ),
    LegacyErrorCase(
        "network", 1, b"dial tcp 127.0.0.1:58553: connect: connection refused", NetworkError, 2
    ),
    LegacyErrorCase(
        "unrelated", 1, b"command failed for an unrelated reason", CommandExecutionError, 1
    ),
)

_MARKER_LOOKALIKE_CASES: tuple[MarkerCase, ...] = (
    MarkerCase("lowercase-conflict", "request conflict: lower-case marker", CommandExecutionError),
    MarkerCase(
        "unreviewed-conflict", "request conflict: not a pinned formatter", CommandExecutionError
    ),
    MarkerCase(
        "unreviewed-validation", "invalid request: not a pinned formatter", CommandExecutionError
    ),
    MarkerCase("unreviewed-word", "conflict happened while processing", CommandExecutionError),
)

_ENVIRONMENT_SECRET_CASES: tuple[EnvironmentSecretCase, ...] = (
    EnvironmentSecretCase("multica-token", "MULTICA_TOKEN"),
    EnvironmentSecretCase("api-key", "THIRD_PARTY_API_KEY"),
)

_URL_SECRET_CASES: tuple[UrlSecretCase, ...] = (
    UrlSecretCase("query", "https://example.com/api?access_token=query-secret", "query-secret"),
    UrlSecretCase("fragment", "https://example.com/api#fragment-secret", "fragment-secret"),
)

_POLICY_CASES: tuple[CompatibilityPolicyCase, ...] = (
    CompatibilityPolicyCase("strict", CompatibilityPolicy.strict),
    CompatibilityPolicyCase("warn", CompatibilityPolicy.warn),
)

_DETAIL_CASES: tuple[DetailCase, ...] = (
    DetailCase(
        "stderr-preferred",
        b"stdout detail",
        b"stderr detail",
        CommandExecutionError,
        99,
        "stderr detail",
    ),
    DetailCase(
        "stdout-fallback",
        b"stdout detail",
        b"",
        CommandExecutionError,
        99,
        "stdout detail",
    ),
    DetailCase(
        "empty-generic",
        b"",
        b"",
        CommandExecutionError,
        99,
        "Command failed with exit code 99 [command: multica auth status]",
    ),
    DetailCase(
        "conflict-reason-before-retry-boilerplate",
        b"",
        b"Request conflict: the skill name is already in use.\n"
        b"The request conflicts with the current state of the resource "
        b"(it may already exist or have changed since you last fetched it). "
        b"Re-fetch the latest state and try again.",
        ConflictError,
        1,
        "Request conflict: the skill name is already in use.\n"
        "The request conflicts with the current state of the resource "
        "(it may already exist or have changed since you last fetched it). "
        "Re-fetch the latest state and try again.",
    ),
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


def test_command_plan_repr_never_exposes_secret_bearing_state() -> None:
    from multica_py.client import MulticaClient

    client = MulticaClient(
        ClientConfig(environment=(("MULTICA_TOKEN", "env-secret"),)),
    )
    command = client.auth.login_command("argv-secret")

    rendered = " ".join((repr(command), repr(command._plan), repr(command._plan.steps[0])))
    assert "argv-secret" not in rendered
    assert "env-secret" not in rendered


def test_environment_secret_in_positional_argv_is_redacted_in_preview() -> None:
    from multica_py.client import MulticaClient

    short_secret = "overlap-secret"
    environment_secret = f"{short_secret}-environment-suffix"
    config = ClientConfig(
        executable=sys.executable,
        environment=(
            ("MULTICA_TOKEN", environment_secret),
            ("THIRD_PARTY_API_KEY", short_secret),
        ),
    )
    command = MulticaClient(config).issues.search_command(environment_secret)

    rendered = " ".join((command.commands[0], repr(command), repr(command._plan)))
    assert environment_secret not in rendered
    assert short_secret not in rendered
    assert "environment-suffix" not in rendered
    assert "***" in command.commands[0]


def test_environment_secret_in_positional_argv_is_redacted_across_execution_surfaces() -> None:
    short_secret = "overlap-secret"
    environment_secret = f"{short_secret}-environment-suffix"
    config = ClientConfig(
        executable=sys.executable,
        environment=(
            ("MULTICA_TOKEN", environment_secret),
            ("THIRD_PARTY_API_KEY", short_secret),
        ),
    )
    code = (
        "import os, sys; "
        "value = os.environ['MULTICA_TOKEN'] + '|' + sys.argv[1] + '|' + sys.argv[-1]; "
        "sys.stdout.write(value); sys.stderr.write(value); sys.exit(1)"
    )
    transport = CliTransport(config)
    command_args = ("-c", code, environment_secret, "--token", short_secret)

    with pytest.raises(CommandExecutionError) as excinfo:
        transport.run_text(command_args)

    exc = excinfo.value
    for rendered in (str(exc), exc.stdout, exc.stderr, exc.argv, repr(exc)):
        assert environment_secret not in rendered
        assert short_secret not in rendered
        assert "environment-suffix" not in rendered
    assert exc.stdout == "***|***|***"
    assert exc.stderr == "***|***|***"

    with transport.spawn(("-c", code, environment_secret, "--token", short_secret)) as managed:
        assert environment_secret not in managed.argv
        assert short_secret not in managed.argv
        assert "environment-suffix" not in managed.argv
        assert environment_secret not in repr(managed)
        assert short_secret not in repr(managed)


def test_client_config_rejects_server_url_userinfo() -> None:
    with pytest.raises(ValueError, match="must not contain username or password"):
        ClientConfig(server_url="https://alice:s3cr3t@example.com")


@pytest.mark.parametrize(
    "case",
    _URL_SECRET_CASES,
    ids=lambda case: case.id,
)
def test_client_config_rejects_server_url_query_or_fragment(case: UrlSecretCase) -> None:
    with pytest.raises(ValueError, match="must not contain query or fragment") as excinfo:
        ClientConfig(server_url=case.server_url)
    assert case.secret not in str(excinfo.value)


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


@pytest.mark.parametrize("case", _ENVIRONMENT_SECRET_CASES, ids=lambda case: case.id)
def test_transport_redacts_environment_only_secrets_from_exception_diagnostics(
    case: EnvironmentSecretCase,
) -> None:
    secret = f"{case.id}-environment-secret"
    config = ClientConfig(
        executable=sys.executable,
        environment=((case.env_key, secret),),
    )
    transport = CliTransport(config)
    code = (
        "import os, sys; "
        f"value = os.environ[{case.env_key!r}]; "
        "sys.stdout.write(value); sys.stderr.write(value); sys.exit(1)"
    )

    with pytest.raises(CommandExecutionError) as excinfo:
        transport.run_text(("-c", code))

    exc = excinfo.value
    rendered = repr(exc)
    assert secret not in str(exc)
    assert secret not in exc.stdout
    assert secret not in exc.stderr
    assert secret not in exc.argv
    assert secret not in rendered
    assert "***" in exc.stdout
    assert "***" in exc.stderr


def test_transport_redacts_overlapping_argv_and_environment_secrets_without_suffix() -> None:
    argv_secret = "overlap-secret"
    environment_secret = f"{argv_secret}-environment-suffix"
    config = ClientConfig(
        executable=sys.executable,
        environment=(("MULTICA_TOKEN", environment_secret),),
    )
    transport = CliTransport(config)
    code = (
        "import os, sys; "
        "value = os.environ['MULTICA_TOKEN'] + '|' + sys.argv[-1]; "
        "sys.stdout.write(value); sys.stderr.write(value); sys.exit(1)"
    )

    with pytest.raises(CommandExecutionError) as excinfo:
        transport.run_text(("-c", code, "--token", argv_secret))

    exc = excinfo.value
    for rendered in (str(exc), exc.stdout, exc.stderr, exc.argv, repr(exc)):
        assert argv_secret not in rendered
        assert environment_secret not in rendered
        assert "environment-suffix" not in rendered
    assert exc.stdout == "***|***"
    assert exc.stderr == "***|***"


def test_transport_redacts_inherited_environment_secret_with_empty_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "inherited-only-environment-secret"
    monkeypatch.setenv("MULTICA_TOKEN", secret)
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config)
    code = (
        "import os, sys; "
        "value = os.environ['MULTICA_TOKEN']; "
        "sys.stdout.write(value); sys.stderr.write(value); sys.exit(1)"
    )

    with pytest.raises(CommandExecutionError) as excinfo:
        transport.run_text(("-c", code))

    exc = excinfo.value
    for rendered in (str(exc), exc.stdout, exc.stderr, exc.argv, repr(exc)):
        assert secret not in rendered
    assert exc.stdout == "***"
    assert exc.stderr == "***"


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
    "case",
    _LEGACY_ERROR_CASES,
    ids=lambda case: case.id,
)
def test_legacy_exit_code_one_classifies_from_stderr(
    case: LegacyErrorCase,
) -> None:
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config)
    transport._execute = lambda *args, **kwargs: RawCommandResult(  # type: ignore[method-assign]
        argv=("multica", "label", "get", "missing"),
        exit_code=case.exit_code,
        stdout=b"",
        stderr=case.stderr,
        duration=datetime.timedelta(),
    )
    with pytest.raises(case.expected_exc) as excinfo:
        transport.run_text(("label", "get", "missing"))
    exc = excinfo.value
    assert isinstance(exc, CommandExecutionError)
    assert exc.exit_code == case.reported_exit_code


def test_classify_cli_failure_maps_http_status() -> None:
    exc_class, reported = classify_cli_failure(
        exit_code=1,
        stdout="",
        stderr="Error: GET /api/labels/x returned 404: missing",
    )
    assert exc_class is NotFoundError
    assert reported == 4


@pytest.mark.parametrize(
    "case",
    _MARKER_LOOKALIKE_CASES,
    ids=lambda case: case.id,
)
def test_classify_cli_failure_rejects_unreviewed_marker_lookalikes(
    case: MarkerCase,
) -> None:
    exc_class, reported = classify_cli_failure(
        exit_code=1,
        stdout="",
        stderr=case.diagnostic,
    )
    assert exc_class is case.expected_exc
    assert reported == 1


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
    assert str(exc) == "forbidden"


@pytest.mark.parametrize(
    "case",
    _DETAIL_CASES,
    ids=lambda case: case.id,
)
def test_transport_error_message_prefers_redacted_stderr_then_stdout(
    case: DetailCase,
) -> None:
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config)
    transport._execute = lambda *args, **kwargs: RawCommandResult(  # type: ignore[method-assign]
        argv=("multica", "auth", "status"),
        exit_code=case.expected_exit_code,
        stdout=case.stdout,
        stderr=case.stderr,
        duration=datetime.timedelta(),
    )
    with pytest.raises(case.expected_exc) as excinfo:
        transport.run_text(("auth", "status"))
    assert str(excinfo.value) == case.expected_message


def test_transport_error_message_redacts_detail_and_keeps_actual_subprocess_argv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "argv-secret"
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
        return CompletedProcess(argv, 1, stdout=b"", stderr=f"Request conflict: {secret}".encode())

    monkeypatch.setattr("multica_py._internal.transport.run_with_timeout", fake_run_with_timeout)
    transport = CliTransport(ClientConfig())
    with pytest.raises(ConflictError) as excinfo:
        transport.run_text(("auth", "login", "--token", secret))

    exc = excinfo.value
    assert executed == [("multica", "auth", "login", "--token", secret)]
    assert secret not in str(exc)
    assert secret not in exc.stdout
    assert secret not in exc.stderr
    assert secret not in exc.argv
    assert "***" in str(exc)
    assert "***" in exc.stderr
    assert exc.argv[-1] == "***"


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


@pytest.mark.parametrize("case", _POLICY_CASES, ids=lambda case: case.id)
def test_snapshot_transports_share_compatibility_preflight_cache(
    case: CompatibilityPolicyCase,
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
        compatibility=case.policy,
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
