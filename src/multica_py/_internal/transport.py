from __future__ import annotations

import datetime
import os

from multica_py._internal.argv import build_global_args
from multica_py._internal.compat import check_version_from_config, parse_cli_version
from multica_py._internal.concurrency import ProcessSemaphore
from multica_py._internal.decoders import decode_text
from multica_py._internal.processes import (
    create_process,
    run_with_timeout,
)
from multica_py._internal.redaction import collect_secret_values, redact_argv, redact_text
from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py.config import ClientConfig
from multica_py.exceptions import (
    AuthenticationError,
    CommandExecutionError,
    CommandTimeoutError,
    ExecutableNotFoundError,
    ExecutableNotRunnableError,
    NetworkError,
    NotFoundError,
    ValidationError,
)
from multica_py.process import ManagedProcess


class CliTransport:
    def __init__(self, config: ClientConfig, semaphore: ProcessSemaphore | None = None) -> None:
        self._config = config
        self._semaphore = semaphore
        self._version_checked = False

    def _build_full_argv(self, command_args: tuple[str, ...]) -> tuple[str, ...]:
        executable = str(self._config.executable)
        global_args = build_global_args(self._config)
        return (executable, *global_args, *command_args)

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
        if self._version_checked or self._config.compatibility.value == "ignore":
            self._version_checked = True
            return
        result = self._execute(("version",), check_compat=False)
        raw = decode_text(result.stdout, command=" ".join(result.argv))
        parsed = parse_cli_version(raw)
        check_version_from_config(parsed, self._config)
        self._version_checked = True

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
        redacted_argv = redact_argv(argv)
        secret_values = collect_secret_values(argv)
        cwd = str(self._config.cwd) if self._config.cwd else None
        env = dict(os.environ)
        env.update(dict(self._config.environment))
        effective_timeout = timeout if timeout is not None else self._config.timeout

        sem_acquired = False
        if self._semaphore is not None:
            self._semaphore.acquire()
            sem_acquired = True

        t0 = datetime.datetime.now(tz=datetime.UTC)
        try:
            try:
                completed = run_with_timeout(
                    argv,
                    stdin=stdin,
                    timeout=effective_timeout,
                    cwd=cwd,
                    env=env,
                )
            except CommandTimeoutError:
                raise
            except FileNotFoundError:
                raise ExecutableNotFoundError(f"Executable not found: {self._config.executable!s}")
            except PermissionError:
                raise ExecutableNotRunnableError(
                    f"Executable not runnable: {self._config.executable!s}"
                )

            duration = datetime.datetime.now(tz=datetime.UTC) - t0
            return RawCommandResult(
                argv=redacted_argv,
                exit_code=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                duration=duration,
                secret_values=secret_values,
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
            decode_text(result.stdout, command=command),
            secret_values=result.secret_values,
        )
        stderr_text = redact_text(
            decode_text(result.stderr, command=command),
            secret_values=result.secret_values,
        )
        message = f"Command failed with exit code {result.exit_code} [command: {command}]"
        exc_class = {
            2: NetworkError,
            3: AuthenticationError,
            4: NotFoundError,
            5: ValidationError,
        }.get(result.exit_code, CommandExecutionError)
        raise exc_class(
            message,
            exit_code=result.exit_code,
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
        cwd = str(self._config.cwd) if self._config.cwd else None
        env = dict(os.environ)
        env.update(dict(self._config.environment))

        if self._semaphore is not None:
            self._semaphore.acquire()

        try:
            proc = create_process(argv, cwd=cwd, env=env)
        except FileNotFoundError:
            if self._semaphore is not None:
                self._semaphore.release()
            raise ExecutableNotFoundError(f"Executable not found: {self._config.executable!s}")
        except PermissionError:
            if self._semaphore is not None:
                self._semaphore.release()
            raise ExecutableNotRunnableError(
                f"Executable not runnable: {self._config.executable!s}"
            )

        return ManagedProcess(proc, argv=redact_argv(argv), semaphore=self._semaphore)
