from __future__ import annotations

import datetime
import os
import re
import sys
from copy import copy
from dataclasses import dataclass

from multica_py._internal.argv import build_global_args
from multica_py._internal.compat import check_version_from_config, parse_cli_version
from multica_py._internal.concurrency import ProcessSemaphore
from multica_py._internal.decoders import decode_text
from multica_py._internal.redaction import (
    collect_diagnostic_secret_bytes,
    collect_diagnostic_secret_values,
    redact_bytes,
    redact_diagnostic_argv,
    redact_text,
    snapshot_secret_files,
)
from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py.config import ClientConfig
from multica_py.exceptions import (
    AuthenticationError,
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
_HTTP_STATUS_PATTERN = re.compile(r"returned (\d{3})\b")
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


@dataclass(slots=True)
class _CompatibilityState:
    checked: bool = False


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
    """Map CLI process failure to a public exception and reported exit code."""
    exc_class = _EXIT_CODE_EXCEPTIONS.get(exit_code)
    reported_exit_code = exit_code
    if exc_class is not None:
        return exc_class, reported_exit_code

    combined = f"{stdout}\n{stderr}"
    status_match = _HTTP_STATUS_PATTERN.search(combined)
    if status_match is not None:
        status = int(status_match.group(1))
        if status == 409:
            return ConflictError, exit_code
        semantic_exit = _semantic_exit_code_for_http_status(status)
        if semantic_exit is not None:
            exc_class = _EXIT_CODE_EXCEPTIONS[semantic_exit]
            return exc_class, semantic_exit

    if any(marker in combined for marker in _CONFLICT_MARKERS):
        return ConflictError, exit_code
    if any(marker in combined for marker in _VALIDATION_MARKERS):
        return ValidationError, 5

    lowered = combined.lower()
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
    ) -> RawCommandResult:
        return self._run(command_args, stdin=stdin, timeout=timeout)

    def run_text(
        self,
        command_args: tuple[str, ...],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
    ) -> TextResult:
        result = self._run(command_args, stdin=stdin, timeout=timeout)
        command = " ".join(result.argv)
        return TextResult(
            text=decode_text(result.stdout, command=command),
            stderr=decode_text(result.stderr, command=command),
            exit_code=result.exit_code,
        )

    def _check_compat(self) -> None:
        state = self._compatibility_state
        if state.checked or self._config.compatibility.value == "ignore":
            state.checked = True
            return
        result = self._execute(("version",), check_compat=False)
        raw = decode_text(result.stdout, command=" ".join(result.argv))
        parsed = parse_cli_version(raw)
        check_version_from_config(parsed, self._config)
        state.checked = True

    def _execute(
        self,
        command_args: tuple[str, ...],
        *,
        stdin: bytes | None = None,
        timeout: datetime.timedelta | None = None,
        check_compat: bool = True,
    ) -> RawCommandResult:
        if check_compat:
            self._check_compat()

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
            with snapshot_secret_files(argv) as (execution_argv, file_contents):
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
    ) -> RawCommandResult:
        result = self._execute(command_args, stdin=stdin, timeout=timeout)
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
        message = detail or f"Command failed with exit code {result.exit_code} [command: {command}]"
        raise exc_class(
            message,
            exit_code=reported_exit_code,
            stdout=stdout_text,
            stderr=stderr_text,
            argv=result.argv,
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

        snapshots = snapshot_secret_files(argv)
        snapshots_entered = False
        try:
            execution_argv, file_contents = snapshots.__enter__()
            snapshots_entered = True
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
            if snapshots_entered:
                snapshots.__exit__(*sys.exc_info())
            if self._semaphore is not None:
                self._semaphore.release()
            raise

        def close_snapshots() -> None:
            snapshots.__exit__(None, None, None)

        return ManagedProcess(
            handle,
            argv=diagnostic_argv,
            semaphore=self._semaphore,
            cleanup=close_snapshots,
        )
