from __future__ import annotations

import datetime
import os
import pathlib
import stat
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from subprocess import CompletedProcess

import pytest

from multica_py._internal.redaction import (
    MAX_SECRET_FILE_BYTES,
    MIN_ENV_SECRET_VALUE_LEN,
    collect_diagnostic_secret_bytes,
    collect_secret_values,
    collect_secret_values_from_environment,
    redact_argv,
    redact_diagnostic_argv,
    redact_text,
)
from multica_py._internal.specs import RawCommandResult
from multica_py._internal.transport import CliTransport, classify_cli_failure
from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy
from multica_py.exceptions import (
    AuthenticationError,
    CommandExecutionError,
    CommandTimeoutError,
    ConflictError,
    ExecutableNotFoundError,
    ExecutableNotRunnableError,
    NetworkError,
    NotFoundError,
    UnsupportedCliVersionError,
    ValidationError,
)
from multica_py.execution import ExecutionRequest, ExecutionResult, LocalExecutor
from multica_py.execution.local import LocalProcessHandle
from multica_py.process import ManagedProcess
from tests.unit.resources.execution_cases import (
    FILE_SECRET_SURFACE_CASES,
    PROCESS_FILE_SECRET_CASES,
    FileSecretSurfaceCase,
    ProcessFileSecretCase,
    file_secret_args,
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
class ShortEnvSecretCase:
    """Secret values from env keys whose short value must NOT corrupt diagnostics."""

    id: str
    env_key: str
    short_value: str
    diagnostic: str


@dataclass(frozen=True)
class EnvSecretCollectCase:
    id: str
    env: tuple[tuple[str, str], ...]
    expected: tuple[str, ...]


@dataclass(frozen=True)
class ExplicitShortSecretCase:
    id: str
    argv: tuple[str, ...]
    stdin: bytes | None
    expected: tuple[str, ...]


@dataclass(frozen=True)
class UrlSecretCase:
    id: str
    server_url: str
    secret: str


@dataclass(frozen=True)
class CompatibilityPolicyCase:
    id: str
    policy: CompatibilityPolicy


@dataclass(frozen=True)
class SecretRedactionCase:
    id: str
    option: str
    payload: bytes
    secret: str
    partial: str
    stdin: bool


@dataclass(frozen=True)
class RedactTextCase:
    id: str
    text: str
    secret: str
    expected: str


@dataclass(frozen=True)
class ProcessLifecycleCase:
    id: str
    file_secret: ProcessFileSecretCase
    command: str
    consume: Callable[[ManagedProcess], str | None]
    expected_output: str | None


_SECRET_REDACTION_CASES: tuple[SecretRedactionCase, ...] = (
    SecretRedactionCase(
        "credential-stdin",
        "--credential-stdin",
        b"credential-token",
        "credential-token",
        "credential-token",
        True,
    ),
    SecretRedactionCase(
        "credential-stdin-opaque",
        "--credential-stdin",
        b"opaque-stdin\x00\xff-secret",
        "opaque-stdin\x00\ufffd-secret",
        "opaque-stdin",
        True,
    ),
    SecretRedactionCase(
        "server-config-stdin-nested-json",
        "--server-config-stdin",
        b'{"headers":{"X-API-Key":"nested-token"}}',
        '{"headers":{"X-API-Key":"nested-token"}}',
        "nested-token",
        True,
    ),
    SecretRedactionCase(
        "server-config-inline-nested-json",
        "--server-config",
        b'{"headers":{"Authorization":"Bearer inline-token"}}',
        '{"headers":{"Authorization":"Bearer inline-token"}}',
        "inline-token",
        False,
    ),
    SecretRedactionCase(
        "auth-header-bearer",
        "--auth-header",
        b"Authorization: Bearer header-token",
        "Authorization: Bearer header-token",
        "header-token",
        False,
    ),
    SecretRedactionCase(
        "auth-header-basic",
        "--auth-header",
        b"Basic basic-token",
        "Basic basic-token",
        "basic-token",
        False,
    ),
)


_REDACT_TEXT_CASES: tuple[RedactTextCase, ...] = (
    RedactTextCase(
        "ascii-below-limit",
        f"prefix {'S' * 4095} suffix",
        "s" * 4095,
        "prefix *** suffix",
    ),
    RedactTextCase(
        "ascii-mixed-case-at-limit",
        f"prefix {'aB' * 2048} suffix",
        "Ab" * 2048,
        "prefix *** suffix",
    ),
    RedactTextCase(
        "ascii-two-occurrences-at-limit",
        f"left {'X' * 4096} middle {'x' * 4096} right",
        "x" * 4096,
        "left *** middle *** right",
    ),
    RedactTextCase(
        "unicode-case-variant-at-limit",
        f"prefix {'Ä' * 4096} suffix",
        "ä" * 4096,
        "prefix *** suffix",
    ),
)


class _EchoExecutor(LocalExecutor):
    def __init__(self, echoed: bytes, *, exit_code: int) -> None:
        self.echoed = echoed
        self.exit_code = exit_code
        self.requests: list[ExecutionRequest] = []

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        self.requests.append(request)
        output = b"stdout " + self.echoed
        error = b"stderr " + self.echoed
        return ExecutionResult(self.exit_code, output, error)


class _SnapshotExecutor(LocalExecutor):
    def __init__(
        self,
        *,
        exit_code: int = 0,
        mutate_path: pathlib.Path | None = None,
        replacement: bytes = b"",
    ) -> None:
        self.exit_code = exit_code
        self.mutate_path = mutate_path
        self.replacement = replacement
        self.requests: list[ExecutionRequest] = []
        self.snapshot_path: pathlib.Path | None = None
        self.snapshot_payload: bytes | None = None
        self.snapshot_mode: int | None = None

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        self.requests.append(request)
        for index, argument in enumerate(request.argv):
            if not argument.startswith(("--credential-file", "--server-config-file")):
                continue
            snapshot = argument.partition("=")[2] if "=" in argument else request.argv[index + 1]
            if self.mutate_path is not None:
                self.mutate_path.write_bytes(self.replacement)
            self.snapshot_path = pathlib.Path(snapshot)
            self.snapshot_payload = self.snapshot_path.read_bytes()
            self.snapshot_mode = stat.S_IMODE(self.snapshot_path.stat().st_mode)
            break
        else:
            raise AssertionError("test executor did not receive a file secret channel")
        return ExecutionResult(
            self.exit_code,
            b"stdout " + self.snapshot_payload,
            b"stderr " + self.snapshot_payload,
        )


class _SpawnStageExecutor(LocalExecutor):
    def __init__(self, *, fail_spawn: bool = False) -> None:
        self.fail_spawn = fail_spawn
        self.requests: list[ExecutionRequest] = []
        self.entered_paths: list[pathlib.Path] = []
        self.cleaned_paths: list[pathlib.Path] = []

    @contextmanager
    def stage(self, label: str, content: bytes) -> Iterator[str]:
        with super().stage(label, content) as path:
            staged_path = pathlib.Path(path)
            self.entered_paths.append(staged_path)
            try:
                yield path
            finally:
                self.cleaned_paths.append(staged_path)

    def spawn(self, request: ExecutionRequest) -> LocalProcessHandle:
        self.requests.append(request)
        if self.fail_spawn:
            raise RuntimeError("spawn failed")
        return super().spawn(request)


def _wait_for_stream_process_completion(process: ManagedProcess) -> None:
    deadline = time.monotonic() + 5
    while process.poll() is None:
        if time.monotonic() >= deadline:
            raise AssertionError("stream process did not report completion")
        time.sleep(0.01)


def _consume_result(process: ManagedProcess) -> str:
    return process.result().stdout


def _consume_close(process: ManagedProcess) -> None:
    process.close()


def _consume_stdout(process: ManagedProcess) -> str:
    lines = list(process.stdout_lines())
    _wait_for_stream_process_completion(process)
    return lines[0]


def _consume_stderr(process: ManagedProcess) -> str:
    lines = list(process.stderr_lines())
    _wait_for_stream_process_completion(process)
    return lines[0]


_SPAWN_CODE = (
    "import pathlib,sys; "
    "file_arg=next(value for value in sys.argv if value.startswith('--credential-file') "
    "or value.startswith('--server-config-file')); "
    "path=file_arg.partition('=')[2] if '=' in file_arg else "
    "sys.argv[sys.argv.index(file_arg)+1]; "
    "data=pathlib.Path(path).read_bytes(); "
    "sys.stdout.write('stdout:'+data.hex()); sys.stdout.flush(); "
    "sys.stderr.write('stderr:'+data.hex()); sys.stderr.flush()"
)
_SPAWN_CLOSE_CODE = _SPAWN_CODE + "; import time; time.sleep(10)"
_CREDENTIAL_FILE_CASE = PROCESS_FILE_SECRET_CASES[0]
_SERVER_CONFIG_FILE_CASE = PROCESS_FILE_SECRET_CASES[1]
_CREDENTIAL_FILE_EQUALS_CASE = PROCESS_FILE_SECRET_CASES[2]
_SERVER_CONFIG_FILE_EQUALS_CASE = PROCESS_FILE_SECRET_CASES[3]


_PROCESS_LIFECYCLE_CASES: tuple[ProcessLifecycleCase, ...] = (
    ProcessLifecycleCase(
        "credential-result",
        _CREDENTIAL_FILE_CASE,
        _SPAWN_CODE,
        _consume_result,
        "stdout:" + _CREDENTIAL_FILE_CASE.payload.hex(),
    ),
    ProcessLifecycleCase(
        "credential-close", _CREDENTIAL_FILE_CASE, _SPAWN_CLOSE_CODE, _consume_close, None
    ),
    ProcessLifecycleCase(
        "credential-stdout",
        _CREDENTIAL_FILE_CASE,
        _SPAWN_CODE,
        _consume_stdout,
        "stdout:" + _CREDENTIAL_FILE_CASE.payload.hex(),
    ),
    ProcessLifecycleCase(
        "credential-stderr",
        _CREDENTIAL_FILE_CASE,
        _SPAWN_CODE,
        _consume_stderr,
        "stderr:" + _CREDENTIAL_FILE_CASE.payload.hex(),
    ),
    ProcessLifecycleCase(
        "server-config-result",
        _SERVER_CONFIG_FILE_CASE,
        _SPAWN_CODE,
        _consume_result,
        "stdout:" + _SERVER_CONFIG_FILE_CASE.payload.hex(),
    ),
    ProcessLifecycleCase(
        "server-config-close", _SERVER_CONFIG_FILE_CASE, _SPAWN_CLOSE_CODE, _consume_close, None
    ),
    ProcessLifecycleCase(
        "server-config-stdout",
        _SERVER_CONFIG_FILE_CASE,
        _SPAWN_CODE,
        _consume_stdout,
        "stdout:" + _SERVER_CONFIG_FILE_CASE.payload.hex(),
    ),
    ProcessLifecycleCase(
        "server-config-stderr",
        _SERVER_CONFIG_FILE_CASE,
        _SPAWN_CODE,
        _consume_stderr,
        "stderr:" + _SERVER_CONFIG_FILE_CASE.payload.hex(),
    ),
    ProcessLifecycleCase(
        "credential-equals-result",
        _CREDENTIAL_FILE_EQUALS_CASE,
        _SPAWN_CODE,
        _consume_result,
        "stdout:" + _CREDENTIAL_FILE_EQUALS_CASE.payload.hex(),
    ),
    ProcessLifecycleCase(
        "credential-equals-close",
        _CREDENTIAL_FILE_EQUALS_CASE,
        _SPAWN_CLOSE_CODE,
        _consume_close,
        None,
    ),
    ProcessLifecycleCase(
        "credential-equals-stdout",
        _CREDENTIAL_FILE_EQUALS_CASE,
        _SPAWN_CODE,
        _consume_stdout,
        "stdout:" + _CREDENTIAL_FILE_EQUALS_CASE.payload.hex(),
    ),
    ProcessLifecycleCase(
        "credential-equals-stderr",
        _CREDENTIAL_FILE_EQUALS_CASE,
        _SPAWN_CODE,
        _consume_stderr,
        "stderr:" + _CREDENTIAL_FILE_EQUALS_CASE.payload.hex(),
    ),
    ProcessLifecycleCase(
        "server-config-equals-result",
        _SERVER_CONFIG_FILE_EQUALS_CASE,
        _SPAWN_CODE,
        _consume_result,
        "stdout:" + _SERVER_CONFIG_FILE_EQUALS_CASE.payload.hex(),
    ),
    ProcessLifecycleCase(
        "server-config-equals-close",
        _SERVER_CONFIG_FILE_EQUALS_CASE,
        _SPAWN_CLOSE_CODE,
        _consume_close,
        None,
    ),
    ProcessLifecycleCase(
        "server-config-equals-stdout",
        _SERVER_CONFIG_FILE_EQUALS_CASE,
        _SPAWN_CODE,
        _consume_stdout,
        "stdout:" + _SERVER_CONFIG_FILE_EQUALS_CASE.payload.hex(),
    ),
    ProcessLifecycleCase(
        "server-config-equals-stderr",
        _SERVER_CONFIG_FILE_EQUALS_CASE,
        _SPAWN_CODE,
        _consume_stderr,
        "stderr:" + _SERVER_CONFIG_FILE_EQUALS_CASE.payload.hex(),
    ),
)


def _staged_path_from_argv(argv: tuple[str, ...], case: ProcessFileSecretCase) -> str:
    for index, argument in enumerate(argv):
        if argument.startswith(f"{case.option}="):
            return argument.partition("=")[2]
        if argument == case.option:
            return argv[index + 1]
    raise AssertionError(f"missing staged {case.option} in argv: {argv!r}")


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
    MarkerCase("bare-http-status", "upstream payload: returned 404", CommandExecutionError),
    MarkerCase("quoted-http-status", "issue body says returned 401 here", CommandExecutionError),
    MarkerCase(
        "misaligned-error-prefix", "Error: returned 404 (no method/path)", CommandExecutionError
    ),
)

_ENVIRONMENT_SECRET_CASES: tuple[EnvironmentSecretCase, ...] = (
    EnvironmentSecretCase("multica-token", "MULTICA_TOKEN"),
    EnvironmentSecretCase("api-key", "THIRD_PARTY_API_KEY"),
    EnvironmentSecretCase("prefixed-access-key", "SERVICE_ACCESS_KEY"),
    EnvironmentSecretCase("suffixed-passwd", "PASSWD_SUFFIX"),
    EnvironmentSecretCase("camel-client-secret", "clientSecret"),
    EnvironmentSecretCase("whitespace-api-key", "api key"),
)

_SHORT_ENV_SECRET_CASES: tuple[ShortEnvSecretCase, ...] = (
    ShortEnvSecretCase(
        "one-char-api-key",
        "API_KEY",
        "1",
        "failed to open /home/1user/project: no such file",
    ),
    ShortEnvSecretCase(
        "three-char-auth-token",
        "AUTH_TOKEN",
        "dev",
        "failed to connect to dev-server.example.com: connection refused",
    ),
    ShortEnvSecretCase(
        "seven-char-secret",
        "MULTICA_SECRET",
        "abcdefg",
        "config path /tmp/abcdefg/config.yaml not found",
    ),
)

_ENV_SECRET_COLLECT_CASES: tuple[EnvSecretCollectCase, ...] = (
    EnvSecretCollectCase("one-char", (("API_KEY", "1"),), ()),
    EnvSecretCollectCase("three-char", (("AUTH_TOKEN", "dev"),), ()),
    EnvSecretCollectCase(
        "below-threshold",
        (("MULTICA_SECRET", "x" * (MIN_ENV_SECRET_VALUE_LEN - 1)),),
        (),
    ),
    EnvSecretCollectCase(
        "at-threshold",
        (("API_KEY", "x" * MIN_ENV_SECRET_VALUE_LEN),),
        ("x" * MIN_ENV_SECRET_VALUE_LEN,),
    ),
    EnvSecretCollectCase(
        "non-secret-key",
        (("HOME", "x" * MIN_ENV_SECRET_VALUE_LEN),),
        (),
    ),
    EnvSecretCollectCase(
        "mixed",
        (("API_KEY", "1"), ("MULTICA_TOKEN", "x" * MIN_ENV_SECRET_VALUE_LEN)),
        ("x" * MIN_ENV_SECRET_VALUE_LEN,),
    ),
)

_EXPLICIT_SHORT_SECRET_CASES: tuple[ExplicitShortSecretCase, ...] = (
    ExplicitShortSecretCase("token-one-char", ("--token", "1"), None, ("1",)),
    ExplicitShortSecretCase("token-three-char", ("--token", "dev"), None, ("dev",)),
    ExplicitShortSecretCase(
        "credential-stdin-three-char",
        ("--credential-stdin",),
        b"dev",
        ("dev",),
    ),
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


@pytest.mark.parametrize("case", _SECRET_REDACTION_CASES, ids=lambda case: case.id)
def test_secret_channels_preserve_transport_bytes_and_redact_error_surfaces(
    case: SecretRedactionCase,
) -> None:
    value = "" if case.stdin else case.payload.decode("utf-8")
    args = (
        "plugin",
        "remote-mcp",
        "configure",
        "inst_001",
        "remote-mcp",
        case.option,
        *(() if case.stdin else (value,)),
    )
    config = ClientConfig(compatibility=CompatibilityPolicy.ignore)
    executor = _EchoExecutor(case.payload, exit_code=0)
    result = CliTransport(config, executor=executor).run_bytes(
        args, stdin=case.payload if case.stdin else None
    )

    assert executor.requests[0].stdin == (case.payload if case.stdin else None)
    assert result.stdout == b"stdout " + case.payload
    assert result.stderr == b"stderr " + case.payload
    assert case.secret not in " ".join(result.argv)

    failing = _EchoExecutor(case.payload, exit_code=2)
    transport = CliTransport(config, executor=failing)
    with pytest.raises(NetworkError) as excinfo:
        transport.run_bytes(args, stdin=case.payload if case.stdin else None)
    exc = excinfo.value
    for diagnostic in (str(exc), exc.stdout, exc.stderr, exc.argv, repr(exc)):
        rendered_text = repr(diagnostic)
        assert case.secret not in rendered_text
        assert case.partial not in rendered_text
    assert failing.requests[0].stdin == (case.payload if case.stdin else None)


@pytest.mark.parametrize("case", FILE_SECRET_SURFACE_CASES, ids=lambda case: case.id)
def test_file_secret_channels_preserve_transport_bytes_and_redact_error_surfaces(
    tmp_path: pathlib.Path,
    case: FileSecretSurfaceCase,
) -> None:
    path = tmp_path / "secret-input"
    path.write_bytes(case.payload)
    args = (
        *case.command_prefix,
        *file_secret_args(case.file_secret, path),
    )
    config = ClientConfig(compatibility=CompatibilityPolicy.ignore)
    executor = _EchoExecutor(case.payload, exit_code=0)
    result = CliTransport(config, executor=executor).run_bytes(args)
    assert result.stdout == b"stdout " + case.payload
    assert result.stderr == b"stderr " + case.payload
    assert case.partial not in " ".join(result.argv)
    assert any(str(path) in argument for argument in result.argv)
    staged_path = _staged_path_from_argv(executor.requests[0].argv, case.file_secret)
    assert executor.requests[0].argv == (
        "multica",
        *case.command_prefix,
        *file_secret_args(case.file_secret, staged_path),
    )

    failing = _EchoExecutor(case.payload, exit_code=2)
    with pytest.raises(NetworkError) as excinfo:
        CliTransport(config, executor=failing).run_bytes(args)
    exc = excinfo.value
    for diagnostic in (str(exc), exc.stdout, exc.stderr, exc.argv, repr(exc)):
        rendered_text = repr(diagnostic)
        assert case.payload.decode("utf-8", errors="replace") not in rendered_text
        assert case.partial not in rendered_text


@pytest.mark.parametrize("case", PROCESS_FILE_SECRET_CASES, ids=lambda case: case.id)
def test_process_file_secret_channels_preserve_success_bytes_and_redact_failures(
    case: ProcessFileSecretCase, tmp_path: pathlib.Path
) -> None:
    path = tmp_path / f"{case.id}.bin"
    path.write_bytes(case.payload)
    code = (
        "import pathlib, sys; "
        "file_arg = next(value for value in sys.argv if value.startswith('--credential-file') "
        "or value.startswith('--server-config-file')); "
        "path = file_arg.partition('=')[2] if '=' in file_arg else sys.argv[sys.argv.index(file_arg) + 1]; "
        "data = pathlib.Path(path).read_bytes(); "
        "sys.stdout.buffer.write(b'stdout ' + data); "
        "sys.stderr.buffer.write(b'stderr ' + data); "
        "sys.exit(int(sys.argv[-1]))"
    )
    file_args = file_secret_args(case, path)
    args = ("-c", code, *file_args, "2")
    config = ClientConfig(executable=sys.executable, compatibility=CompatibilityPolicy.ignore)
    transport = CliTransport(config)

    result = transport.run_bytes(("-c", code, *file_args, "0"))
    assert result.stdout == b"stdout " + case.payload
    assert result.stderr == b"stderr " + case.payload

    with pytest.raises(NetworkError) as excinfo:
        transport.run_bytes(args)
    exc = excinfo.value
    assert case.payload.decode("utf-8", errors="replace") not in repr(exc)
    assert case.payload.decode("utf-8", errors="replace") not in exc.stdout
    assert case.payload.decode("utf-8", errors="replace") not in exc.stderr
    assert "***" in exc.stdout
    assert "***" in exc.stderr


@pytest.mark.parametrize("case", PROCESS_FILE_SECRET_CASES, ids=lambda case: case.id)
def test_exact_limit_file_failure_redacts_every_exception_surface(
    tmp_path: pathlib.Path,
    case: ProcessFileSecretCase,
) -> None:
    payload = b"x" * MAX_SECRET_FILE_BYTES
    payload_text = payload.decode("ascii")
    path = tmp_path / f"{case.id}-exact.bin"
    path.write_bytes(payload)
    code = (
        "import pathlib, sys; "
        "file_arg = next(value for value in sys.argv if value.startswith('--credential-file') "
        "or value.startswith('--server-config-file')); "
        "path = file_arg.partition('=')[2] if '=' in file_arg else "
        "sys.argv[sys.argv.index(file_arg) + 1]; "
        "data = pathlib.Path(path).read_bytes(); "
        "sys.stdout.buffer.write(data); sys.stderr.buffer.write(data); sys.exit(2)"
    )
    config = ClientConfig(executable=sys.executable, compatibility=CompatibilityPolicy.ignore)

    with pytest.raises(NetworkError) as excinfo:
        CliTransport(config).run_bytes(("-c", code, *file_secret_args(case, path)))

    exc = excinfo.value
    for diagnostic in (str(exc), exc.stdout, exc.stderr, exc.argv, repr(exc)):
        assert payload_text not in repr(diagnostic)
    assert exc.stdout.count("***") == 1
    assert exc.stderr.count("***") == 1


@pytest.mark.parametrize("case", _PROCESS_LIFECYCLE_CASES, ids=lambda case: case.id)
def test_spawn_file_staging_lives_until_each_managed_process_finalizer(
    tmp_path: pathlib.Path,
    case: ProcessLifecycleCase,
) -> None:
    source = tmp_path / "spawn-source.bin"
    source.write_bytes(case.file_secret.payload)
    file_args = file_secret_args(case.file_secret, source)
    executor = _SpawnStageExecutor()
    transport = CliTransport(
        ClientConfig(executable=sys.executable, compatibility=CompatibilityPolicy.ignore),
        executor=executor,
    )

    process = transport.spawn(("-c", case.command, *file_args))
    assert len(executor.entered_paths) == 1
    staged_path = executor.entered_paths[0]
    assert staged_path.read_bytes() == case.file_secret.payload
    assert str(source) not in executor.requests[0].argv

    expected_file_args = file_secret_args(case.file_secret, staged_path)
    assert executor.requests[0].argv == (sys.executable, "-c", case.command, *expected_file_args)
    assert case.consume(process) == case.expected_output
    assert not staged_path.exists()
    assert executor.cleaned_paths == [staged_path]
    process.close()
    process.close()

    assert not staged_path.exists()
    assert executor.cleaned_paths == [staged_path]


@pytest.mark.parametrize("case", PROCESS_FILE_SECRET_CASES, ids=lambda case: case.id)
def test_spawn_file_staging_cleans_up_when_executor_spawn_fails(
    tmp_path: pathlib.Path,
    case: ProcessFileSecretCase,
) -> None:
    source = tmp_path / "spawn-failure-source.bin"
    source.write_bytes(case.payload)
    file_args = file_secret_args(case, source)
    executor = _SpawnStageExecutor(fail_spawn=True)
    transport = CliTransport(
        ClientConfig(compatibility=CompatibilityPolicy.ignore), executor=executor
    )

    with pytest.raises(RuntimeError, match="spawn failed"):
        transport.spawn(("workspace", "mcp", "add", "server-1", *file_args))

    assert len(executor.entered_paths) == 1
    staged_path = executor.entered_paths[0]
    assert not staged_path.exists()
    assert executor.cleaned_paths == [staged_path]


@pytest.mark.parametrize("case", PROCESS_FILE_SECRET_CASES, ids=lambda case: case.id)
def test_file_snapshot_is_owner_only_and_cleaned(
    tmp_path: pathlib.Path,
    case: ProcessFileSecretCase,
) -> None:
    source = tmp_path / "secret.bin"
    payload = case.payload
    source.write_bytes(payload)
    file_args = file_secret_args(case, source)
    executor = _SnapshotExecutor()
    result = CliTransport(
        ClientConfig(compatibility=CompatibilityPolicy.ignore), executor=executor
    ).run_bytes(("workspace", "mcp", "add", "server-1", *file_args))

    assert result.stdout == b"stdout " + payload
    assert executor.snapshot_payload == payload
    assert executor.snapshot_mode == 0o600
    assert executor.snapshot_path is not None
    assert executor.snapshot_path != source
    assert not executor.snapshot_path.exists()
    assert any(str(source) in argument for argument in result.argv)


@pytest.mark.parametrize("case", PROCESS_FILE_SECRET_CASES, ids=lambda case: case.id)
def test_file_snapshot_accepts_exact_limit_and_rejects_oversize(
    tmp_path: pathlib.Path,
    case: ProcessFileSecretCase,
) -> None:
    config = ClientConfig(compatibility=CompatibilityPolicy.ignore)

    exact_path = tmp_path / "exact.bin"
    exact_payload = b"x" * MAX_SECRET_FILE_BYTES
    exact_path.write_bytes(exact_payload)
    exact_args = file_secret_args(case, exact_path)
    exact_executor = _SnapshotExecutor()
    CliTransport(config, executor=exact_executor).run_bytes(
        ("workspace", "mcp", "add", "server-1", *exact_args)
    )
    assert exact_executor.snapshot_payload == exact_payload

    oversize_path = tmp_path / "oversize.bin"
    oversize_path.write_bytes(b"x" * (MAX_SECRET_FILE_BYTES + 1))
    oversize_args = file_secret_args(case, oversize_path)
    oversize_executor = _SnapshotExecutor()
    with pytest.raises(ValidationError, match="exceeds"):
        CliTransport(config, executor=oversize_executor).run_bytes(
            ("workspace", "mcp", "add", "server-1", *oversize_args)
        )
    assert oversize_executor.requests == []


@pytest.mark.parametrize("case", PROCESS_FILE_SECRET_CASES, ids=lambda case: case.id)
def test_file_snapshot_rejects_fifo_without_blocking(
    tmp_path: pathlib.Path, case: ProcessFileSecretCase
) -> None:
    fifo = tmp_path / "secret.fifo"
    os.mkfifo(fifo)
    executor = _SnapshotExecutor()
    file_args = file_secret_args(case, fifo)
    with pytest.raises(ValidationError, match=r"regular file|readable"):
        CliTransport(
            ClientConfig(compatibility=CompatibilityPolicy.ignore), executor=executor
        ).run_bytes(("workspace", "mcp", "add", "server-1", *file_args))
    assert executor.requests == []


@pytest.mark.parametrize("case", PROCESS_FILE_SECRET_CASES, ids=lambda case: case.id)
def test_file_snapshot_redaction_uses_one_mutation_stable_byte_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    case: ProcessFileSecretCase,
) -> None:
    import multica_py._internal.redaction as redaction

    source = tmp_path / "secret.bin"
    original = b"original-opaque-secret\x00\xff"
    replacement = b"replacement-secret"
    source.write_bytes(original)
    reads: list[str] = []
    reader = redaction.read_secret_file_bytes

    def read_once(path: str) -> bytes:
        reads.append(path)
        content = reader(path)
        source.write_bytes(replacement)
        return content

    monkeypatch.setattr(redaction, "read_secret_file_bytes", read_once)
    file_args = file_secret_args(case, source)
    executor = _SnapshotExecutor(exit_code=2)
    with pytest.raises(NetworkError) as excinfo:
        CliTransport(
            ClientConfig(compatibility=CompatibilityPolicy.ignore), executor=executor
        ).run_bytes(("plugin", "remote-mcp", "configure", *file_args))

    assert reads == [str(source)]
    assert executor.snapshot_payload == original
    assert original.decode("utf-8", errors="replace") not in repr(excinfo.value)
    assert replacement not in excinfo.value.stdout.encode("utf-8", errors="replace")
    assert collect_diagnostic_secret_bytes(
        ("plugin", "remote-mcp", "configure", *file_args), file_contents={str(source): original}
    ) == (original,)
    assert collect_secret_values(
        ("plugin", "remote-mcp", "configure", *file_args),
        file_contents={str(source): original},
    )


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

    monkeypatch.setattr("multica_py.execution.local.run_with_timeout", fake_run_with_timeout)
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
    config = ClientConfig(executable=sys.executable, environment=(("CUSTOM_VALUE", "test"),))
    transport = CliTransport(config)
    code = "import os; print(os.environ.get('CUSTOM_VALUE', 'NOT_SET'))"
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


@pytest.mark.parametrize("case", _ENV_SECRET_COLLECT_CASES, ids=lambda case: case.id)
def test_collect_secret_values_from_environment_skips_short_values(
    case: EnvSecretCollectCase,
) -> None:
    assert collect_secret_values_from_environment(dict(case.env)) == case.expected


@pytest.mark.parametrize("case", _EXPLICIT_SHORT_SECRET_CASES, ids=lambda case: case.id)
def test_collect_secret_values_keeps_short_explicit_channels(
    case: ExplicitShortSecretCase,
) -> None:
    assert collect_secret_values(case.argv, stdin=case.stdin) == case.expected


@pytest.mark.parametrize("case", _SHORT_ENV_SECRET_CASES, ids=lambda case: case.id)
def test_transport_short_env_secret_does_not_corrupt_diagnostics(
    case: ShortEnvSecretCase,
) -> None:
    config = ClientConfig(
        executable=sys.executable,
        environment=((case.env_key, case.short_value),),
    )
    transport = CliTransport(config)
    code = f"import sys; sys.stderr.write({case.diagnostic!r}); sys.exit(1)"

    with pytest.raises(CommandExecutionError) as excinfo:
        transport.run_text(("-c", code))

    assert excinfo.value.stderr == case.diagnostic


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


def test_classify_cli_failure_prefers_stderr_over_stdout_noise() -> None:
    exc_class, reported = classify_cli_failure(
        exit_code=1,
        stdout=(
            "returned 404\n"
            "Request conflict: already exists\n"
            "Invalid request: bad value\n"
            "dial tcp: connection refused"
        ),
        stderr="Error: GET /api/workspaces returned 401: unauthorized",
    )
    assert exc_class is AuthenticationError
    assert reported == 3


@pytest.mark.parametrize(
    "stdout_payload",
    [
        "returned 404",
        "Error: GET /api/x returned 404: missing",
        "Request conflict: already exists",
        "Invalid request: bad value",
        "dial tcp: connection refused",
    ],
    ids=lambda payload: payload.split(":")[0][:24],
)
def test_classify_cli_failure_ignores_stdout_echoed_content(stdout_payload: str) -> None:
    exc_class, reported = classify_cli_failure(
        exit_code=1,
        stdout=stdout_payload,
        stderr="command failed for an unrelated reason",
    )
    assert exc_class is CommandExecutionError
    assert reported == 1


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

    monkeypatch.setattr("multica_py.execution.local.run_with_timeout", fake_run_with_timeout)
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


@pytest.mark.parametrize("case", _REDACT_TEXT_CASES, ids=lambda case: case.id)
def test_redact_text_bounded_long_secrets_preserve_case_insensitive_semantics(
    case: RedactTextCase,
) -> None:
    redacted = redact_text(case.text, secret_values=(case.secret,))
    preview = redact_diagnostic_argv(("multica", case.text), secret_values=(case.secret,))

    assert redacted == case.expected
    assert preview == ("multica", case.expected)
    assert case.secret not in redacted
    assert redacted.count("***") == case.expected.count("***")


def test_redact_text_redacts_embedded_token_value():
    redacted = redact_text("token: secret123", secret_values=("secret123",))
    assert "secret123" not in redacted
    assert "***" in redacted


def test_transport_redacts_long_unicode_case_variant_from_all_exception_surfaces() -> None:
    secret = "ä" * 4096
    case_variant = "Ä" * 4096
    config = ClientConfig(
        executable=sys.executable,
        compatibility=CompatibilityPolicy.ignore,
        environment=(("MULTICA_TOKEN", secret),),
    )
    code = (
        "import os, sys; "
        "sys.stdout.write(os.environ['MULTICA_TOKEN'].upper()); "
        "sys.stderr.write(sys.argv[-1]); sys.exit(2)"
    )

    with pytest.raises(NetworkError) as excinfo:
        CliTransport(config).run_bytes(("-c", code, case_variant))

    exc = excinfo.value
    for diagnostic in (str(exc), exc.stdout, exc.stderr, exc.argv, repr(exc)):
        rendered = repr(diagnostic)
        assert secret not in rendered
        assert case_variant not in rendered
    assert exc.stdout == "***"
    assert exc.stderr == "***"
    assert exc.argv[-1] == "***"


def test_transport_command_timeout_propagates() -> None:
    config = ClientConfig(executable=sys.executable)
    transport = CliTransport(config)

    def _raise_timeout(*args: object, **kwargs: object) -> object:
        raise CommandTimeoutError()

    transport._execute = _raise_timeout  # type: ignore[assignment,method-assign]
    with pytest.raises(CommandTimeoutError):
        transport.run_text(("issue", "list"))


@pytest.mark.parametrize(
    ("process_error", "expected_error"),
    (
        (FileNotFoundError(), ExecutableNotFoundError),
        (PermissionError(), ExecutableNotRunnableError),
    ),
    ids=("not-found", "not-runnable"),
)
def test_transport_execution_maps_process_start_errors(
    monkeypatch: pytest.MonkeyPatch,
    process_error: OSError,
    expected_error: type[Exception],
) -> None:
    def fail_start(*args: object, **kwargs: object) -> CompletedProcess[bytes]:
        del args, kwargs
        raise process_error

    monkeypatch.setattr("multica_py.execution.local.run_with_timeout", fail_start)
    transport = CliTransport(ClientConfig(executable="missing-multica"))

    with pytest.raises(expected_error, match="missing-multica"):
        transport._execute(("issue", "list"), check_compat=False)


@pytest.mark.parametrize(
    ("process_error", "expected_error"),
    (
        (FileNotFoundError(), ExecutableNotFoundError),
        (PermissionError(), ExecutableNotRunnableError),
    ),
    ids=("not-found", "not-runnable"),
)
def test_transport_spawn_maps_process_start_errors(
    monkeypatch: pytest.MonkeyPatch,
    process_error: OSError,
    expected_error: type[Exception],
) -> None:
    def fail_start(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise process_error

    monkeypatch.setattr("multica_py.execution.local.create_process", fail_start)
    transport = CliTransport(
        ClientConfig(executable="missing-multica", compatibility=CompatibilityPolicy.ignore)
    )

    with pytest.raises(expected_error, match="missing-multica"):
        transport.spawn(("issue", "list"))
