from __future__ import annotations

import datetime
import json
import os
import re
from collections.abc import Mapping
from contextlib import ExitStack
from copy import copy
from dataclasses import dataclass
from typing import cast

from multica_py._internal.argv import build_global_args
from multica_py._internal.compat import check_version_from_config, parse_cli_version
from multica_py._internal.concurrency import ProcessSemaphore
from multica_py._internal.decoders import decode_text
from multica_py._internal.redaction import (
    collect_diagnostic_secret_bytes,
    collect_diagnostic_secret_values,
    iter_secret_file_arguments,
    redact_bytes,
    redact_diagnostic_argv,
    redact_text,
    snapshot_secret_files,
)
from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py.compatibility import CliVersion
from multica_py.config import ClientConfig
from multica_py.exceptions import (
    AuthenticationError,
    AuthorizationError,
    CommandExecutionError,
    ConflictError,
    NetworkError,
    NotFoundError,
    ValidationError,
)
from multica_py.execution import CommandExecutor, ExecutionRequest, LocalExecutor
from multica_py.process import ManagedProcess

_EXIT_CODE_EXCEPTIONS: dict[int, type[CommandExecutionError]] = {
    2: NetworkError,
    3: AuthenticationError,
    4: NotFoundError,
    5: ValidationError,
}
# ponytail: anchored to the CLI's pinned error-line prefix so echoed user
# content (e.g. an upstream payload quoting "returned 404") cannot drive
# classification. The CLI emits failures as "Error: <METHOD> <path>
# returned <NNN>: ..."; matching the full prefix avoids false positives.
_HTTP_STATUS_PATTERN = re.compile(r"(?:^|\n)Error: \S+ \S+ returned (\d{3})\b")
_NETWORK_MARKERS = (
    "connection refused",
    "dial tcp",
    "no such host",
    "i/o timeout",
    "connection reset",
    "network is unreachable",
    "tls:",
)
_CONFLICT_MARKERS = (
    "Request conflict: ",
    "请求冲突：",  # noqa: RUF001
    "The request conflicts with the current state of the resource "
    "(it may already exist or have changed since you last fetched it). "
    "Re-fetch the latest state and try again.",
    "请求与资源的当前状态冲突（可能已存在，或自上次获取后已被修改）。请重新获取最新状态后再试。",  # noqa: RUF001
)

_VALIDATION_MARKERS = (
    "Invalid request: ",
    "请求无效：",  # noqa: RUF001
    "The request was invalid. Check the values you provided; run the command with "
    "--help to see the expected format.",
    "请求无效。请检查所填写的参数；可用 --help 查看期望的格式。",  # noqa: RUF001
    "--max-concurrent-tasks must be between 1 and 50",
)
_AUTHORIZATION_DIAGNOSTICS = (
    "You do not have permission to access this resource. Check that you are in the right "
    "workspace, or ask an administrator to grant access.",
    "无权访问该资源。请确认当前 workspace 是否正确，或联系管理员授予权限。",  # noqa: RUF001
)


def _structured_error_payload(stderr: str) -> dict[str, object] | None:
    """Decode only a JSON object carried by the CLI error diagnostic."""
    candidate = stderr.strip()
    if not candidate.startswith("{"):
        candidate = candidate[candidate.find("{") :] if "{" in candidate else ""
    if not candidate:
        return None
    try:
        payload = cast("object", json.loads(candidate))
    except json.JSONDecodeError:
        return None
    return cast("dict[str, object]", payload) if isinstance(payload, dict) else None


def _reviewed_error_fields(stderr: str) -> dict[str, object]:
    payload = _structured_error_payload(stderr)
    if payload is None:
        return {}
    fields: dict[str, object] = {}
    code = payload.get("code")
    if isinstance(code, str) and code:
        fields["code"] = code
    counts: dict[str, int] = {}
    for key in ("active_agent_count", "undrained_task_count"):
        value = payload.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            counts[key] = value
    if counts:
        fields["blocker_counts"] = counts
    identity: dict[str, str] = {}
    for key in ("profile_id", "profile_name", "runtime_status", "last_seen_at"):
        value = payload.get(key)
        if isinstance(value, str):
            identity[key] = value
    if identity:
        fields["profile_identity"] = identity
    ttl = payload.get("auto_cleanup_after_days")
    if isinstance(ttl, int) and not isinstance(ttl, bool) and ttl >= 0:
        fields["auto_cleanup_after_days"] = ttl
    guidance = payload.get("cleanup_guidance")
    if isinstance(guidance, str) and guidance:
        fields["cleanup_guidance"] = guidance
    message = payload.get("error", payload.get("message"))
    if isinstance(message, str) and message.strip():
        fields["message"] = message.strip()
    return fields


@dataclass(slots=True)
class _CompatibilityState:
    checked: bool = False
    detected: CliVersion | None = None


def _semantic_exit_code_for_http_status(status: int) -> int | None:
    if status in (401, 403):
        return 3
    if status == 404:
        return 4
    if status in (400, 422):
        return 5
    return None


def _effective_environment(config: ClientConfig) -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(dict(config.environment))
    return environment


def classify_cli_failure(
    *,
    exit_code: int,
    stdout: str,
    stderr: str,
) -> tuple[type[CommandExecutionError], int]:
    """Map CLI process failure to a public exception and reported exit code.

    Classification reads only ``stderr``: the CLI writes its diagnostic
    lines there, while ``stdout`` may echo arbitrary upstream payloads (issue
    bodies, quoted API responses) that must not influence the error type or
    the reported exit code.
    """
    status_match = _HTTP_STATUS_PATTERN.search(stderr)
    status = int(status_match.group(1)) if status_match is not None else None
    if status == 409:
        return ConflictError, exit_code
    if status == 403:
        return AuthorizationError, 3
    if status == 404:
        return NotFoundError, 4
    semantic_exit = None if status is None else _semantic_exit_code_for_http_status(status)
    if semantic_exit is not None:
        return _EXIT_CODE_EXCEPTIONS[semantic_exit], semantic_exit

    # The target deliberately shares exit 3 between 401 and 403.  Its
    # localized formatter is the only reviewed distinction available to the
    # SDK, so recognize the exact permission diagnostics before falling back
    # to the stable authentication mapping.
    if exit_code == 3 and any(stderr.startswith(marker) for marker in _AUTHORIZATION_DIAGNOSTICS):
        return AuthorizationError, 3

    exc_class = _EXIT_CODE_EXCEPTIONS.get(exit_code)
    reported_exit_code = exit_code
    if exc_class is not None:
        return exc_class, reported_exit_code

    if any(marker in stderr for marker in _CONFLICT_MARKERS):
        return ConflictError, exit_code
    if any(marker in stderr for marker in _VALIDATION_MARKERS):
        return ValidationError, 5

    lowered = stderr.lower()
    if any(marker in lowered for marker in _NETWORK_MARKERS):
        return NetworkError, 2

    return CommandExecutionError, exit_code


class CliTransport:
    def __init__(
        self,
        config: ClientConfig,
        semaphore: ProcessSemaphore | None = None,
        executor: CommandExecutor | None = None,
    ) -> None:
        self._config = config
        self._semaphore = semaphore
        self._executor = executor or LocalExecutor()
        self._compatibility_state = _CompatibilityState()

    def __enter__(self) -> CliTransport:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        """Release transport-owned resources after subprocess calls."""

    @property
    def executor(self) -> CommandExecutor:
        return self._executor

    def _snapshot(self, config: ClientConfig) -> CliTransport:
        view = copy(self)
        view._config = config
        return view

    def build_full_argv(self, command_args: tuple[str, ...]) -> tuple[str, ...]:
        executable = os.fspath(self._config.executable)
        global_args = build_global_args(self._config)
        return (executable, *global_args, *command_args)

    def _build_full_argv(self, command_args: tuple[str, ...]) -> tuple[str, ...]:
        return self.build_full_argv(command_args)

    def run_bytes(
        self,
        command_args: tuple[str, ...],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
        minimum_cli_version: str | None = None,
    ) -> RawCommandResult:
        if minimum_cli_version is None:
            return self._run(command_args, stdin=stdin, timeout=timeout)
        return self._run(
            command_args,
            stdin=stdin,
            timeout=timeout,
            minimum_cli_version=minimum_cli_version,
        )

    def run_text(
        self,
        command_args: tuple[str, ...],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
        minimum_cli_version: str | None = None,
    ) -> TextResult:
        if minimum_cli_version is None:
            result = self._run(command_args, stdin=stdin, timeout=timeout)
        else:
            result = self._run(
                command_args,
                stdin=stdin,
                timeout=timeout,
                minimum_cli_version=minimum_cli_version,
            )
        command = " ".join(result.argv)
        return TextResult(
            text=decode_text(result.stdout, command=command),
            stderr=decode_text(result.stderr, command=command),
            exit_code=result.exit_code,
        )

    def _check_compat(self, minimum_cli_version: str | None = None) -> None:
        state = self._compatibility_state
        if state.checked or self._config.compatibility.value == "ignore":
            if state.detected is not None and minimum_cli_version is not None:
                check_version_from_config(
                    state.detected,
                    self._config,
                    operation_min_version=minimum_cli_version,
                )
            state.checked = True
            return
        result = self._execute(("version", "--output", "json"), check_compat=False)
        if result.exit_code != 0:
            self._raise_command_error(result)
        raw = decode_text(result.stdout, command=" ".join(result.argv))
        parsed = parse_cli_version(raw)
        check_version_from_config(parsed, self._config)
        if parsed is None:
            return
        if minimum_cli_version is not None:
            check_version_from_config(
                parsed,
                self._config,
                operation_min_version=minimum_cli_version,
            )
        state.detected = parsed
        state.checked = True

    def _execute(
        self,
        command_args: tuple[str, ...],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
        minimum_cli_version: str | None = None,
        check_compat: bool = True,
    ) -> RawCommandResult:
        if check_compat:
            self._check_compat(minimum_cli_version)

        argv = self._build_full_argv(command_args)
        cwd = os.fspath(self._config.cwd) if self._config.cwd is not None else None
        environment = tuple(self._config.environment)
        effective_timeout = timeout if timeout is not None else self._config.timeout

        sem_acquired = False
        if self._semaphore is not None:
            self._semaphore.acquire()
            sem_acquired = True

        t0 = datetime.datetime.now(tz=datetime.UTC)
        try:
            with ExitStack() as staging:
                execution_argv, file_contents = self._prepare_secret_files(argv, staging)
                secret_values = collect_diagnostic_secret_values(
                    argv,
                    _effective_environment(self._config),
                    stdin=stdin,
                    file_contents=file_contents,
                )
                secret_bytes = collect_diagnostic_secret_bytes(
                    argv, stdin=stdin, file_contents=file_contents
                )
                diagnostic_argv = redact_diagnostic_argv(argv, secret_values=secret_values)
                completed = self._executor.run(
                    ExecutionRequest(
                        argv=execution_argv,
                        cwd=cwd,
                        environment=environment,
                        stdin=stdin,
                        timeout=effective_timeout,
                    )
                )

            duration = datetime.datetime.now(tz=datetime.UTC) - t0
            return RawCommandResult(
                argv=diagnostic_argv,
                exit_code=completed.exit_code,
                stdout=completed.stdout,
                stderr=completed.stderr,
                duration=duration,
                secret_values=secret_values,
                secret_bytes=secret_bytes,
            )
        finally:
            if sem_acquired and self._semaphore is not None:
                self._semaphore.release()

    def _run(
        self,
        command_args: tuple[str, ...],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
        minimum_cli_version: str | None = None,
    ) -> RawCommandResult:
        if minimum_cli_version is None:
            result = self._execute(command_args, stdin=stdin, timeout=timeout)
        else:
            result = self._execute(
                command_args,
                stdin=stdin,
                timeout=timeout,
                minimum_cli_version=minimum_cli_version,
            )
        if result.exit_code != 0:
            self._raise_command_error(result)
        return result

    def _raise_command_error(self, result: RawCommandResult) -> None:
        command = " ".join(result.argv)
        stdout_text = redact_text(
            decode_text(
                redact_bytes(
                    result.stdout,
                    secret_values=result.secret_values,
                    secret_bytes=result.secret_bytes,
                ),
                command=command,
            ),
            secret_values=result.secret_values,
        )
        stderr_text = redact_text(
            decode_text(
                redact_bytes(
                    result.stderr,
                    secret_values=result.secret_values,
                    secret_bytes=result.secret_bytes,
                ),
                command=command,
            ),
            secret_values=result.secret_values,
        )
        exc_class, reported_exit_code = classify_cli_failure(
            exit_code=result.exit_code,
            stdout=stdout_text,
            stderr=stderr_text,
        )
        detail = stderr_text.strip() or stdout_text.strip()
        structured = _reviewed_error_fields(stderr_text)
        message = cast("str", structured.get("message", detail)) or (
            f"Command failed with exit code {result.exit_code} [command: {command}]"
        )
        raise exc_class(
            message,
            exit_code=reported_exit_code,
            stdout=stdout_text,
            stderr=stderr_text,
            argv=result.argv,
            code=cast("str | None", structured.get("code")),
            blocker_counts=cast("Mapping[str, int] | None", structured.get("blocker_counts")),
            profile_identity=cast("Mapping[str, str] | None", structured.get("profile_identity")),
            cleanup_guidance=cast("str | None", structured.get("cleanup_guidance")),
            auto_cleanup_after_days=cast("int | None", structured.get("auto_cleanup_after_days")),
        )

    def spawn(
        self,
        command_args: tuple[str, ...],
    ) -> ManagedProcess:
        self._check_compat()
        argv = self._build_full_argv(command_args)
        cwd = os.fspath(self._config.cwd) if self._config.cwd is not None else None
        environment = tuple(self._config.environment)

        if self._semaphore is not None:
            self._semaphore.acquire()

        staging = ExitStack()
        try:
            execution_argv, file_contents = self._prepare_secret_files(argv, staging)
            secret_values = collect_diagnostic_secret_values(
                argv, _effective_environment(self._config), file_contents=file_contents
            )
            diagnostic_argv = redact_diagnostic_argv(argv, secret_values=secret_values)
            handle = self._executor.spawn(
                ExecutionRequest(
                    argv=execution_argv,
                    cwd=cwd,
                    environment=environment,
                    timeout=self._config.timeout,
                )
            )
        except BaseException:
            staging.close()
            if self._semaphore is not None:
                self._semaphore.release()
            raise

        return ManagedProcess(
            handle,
            argv=diagnostic_argv,
            semaphore=self._semaphore,
            cleanup=staging.close,
        )

    def terminal(self, command_args: tuple[str, ...]) -> ManagedProcess:
        """Start an interactive process through the executor boundary."""
        self._check_compat()
        argv = self._build_full_argv(command_args)
        cwd = os.fspath(self._config.cwd) if self._config.cwd is not None else None
        environment = tuple(self._config.environment)
        if self._semaphore is not None:
            self._semaphore.acquire()
        staging = ExitStack()
        try:
            execution_argv, file_contents = self._prepare_secret_files(argv, staging)
            secret_values = collect_diagnostic_secret_values(
                argv, _effective_environment(self._config), file_contents=file_contents
            )
            handle = self._executor.terminal(
                ExecutionRequest(
                    argv=execution_argv,
                    cwd=cwd,
                    environment=environment,
                    timeout=self._config.timeout,
                )
            )
        except BaseException:
            staging.close()
            if self._semaphore is not None:
                self._semaphore.release()
            raise
        return ManagedProcess(
            handle,
            argv=redact_diagnostic_argv(argv, secret_values=secret_values),
            semaphore=self._semaphore,
            cleanup=staging.close,
        )

    def _prepare_secret_files(
        self, argv: tuple[str, ...], staging: ExitStack
    ) -> tuple[tuple[str, ...], dict[str, bytes]]:
        source_argv, file_contents = staging.enter_context(snapshot_secret_files(argv))
        rewritten = list(source_argv)
        target_paths: dict[str, str] = {}
        for argument in iter_secret_file_arguments(source_argv):
            target_path = target_paths.get(argument.path)
            if target_path is None:
                target_path = staging.enter_context(
                    self._executor.stage(
                        f"secret-{len(target_paths)}.bin", file_contents[argument.path]
                    )
                )
                target_paths[argument.path] = target_path
            if argument.value_index is None:
                name = source_argv[argument.option_index].partition("=")[0]
                rewritten[argument.option_index] = f"{name}={target_path}"
            else:
                rewritten[argument.value_index] = target_path
        return tuple(rewritten), dict(file_contents)
