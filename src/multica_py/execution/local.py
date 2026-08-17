from __future__ import annotations

import contextlib
import datetime
import os
import subprocess
import tempfile
from collections.abc import Iterator
from typing import BinaryIO, cast

from multica_py._internal.processes import (
    close_process_pipes,
    create_process,
    kill_process,
    run_with_timeout,
    terminate_process,
)
from multica_py.exceptions import ExecutableNotFoundError, ExecutableNotRunnableError
from multica_py.execution.base import ExecutionRequest, ExecutionResult


def _stdin_pipe(process: subprocess.Popen[bytes]) -> BinaryIO | None:
    return cast("BinaryIO | None", process.stdin)


def _stdout_pipe(process: subprocess.Popen[bytes]) -> BinaryIO | None:
    return cast("BinaryIO | None", process.stdout)


def _stderr_pipe(process: subprocess.Popen[bytes]) -> BinaryIO | None:
    return cast("BinaryIO | None", process.stderr)


class LocalProcessHandle:
    def __init__(self, process: subprocess.Popen[bytes]) -> None:
        self._process = process
        self._output_mode: str | None = None

    @property
    def id(self) -> int:
        return self._process.pid

    def poll(self) -> int | None:
        return self._process.poll()

    def wait(self, timeout: datetime.timedelta | None = None) -> int:
        try:
            return self._process.wait(None if timeout is None else timeout.total_seconds())
        except subprocess.TimeoutExpired as error:
            raise TimeoutError("Process wait timed out") from error

    def collect(self, timeout: datetime.timedelta | None = None) -> ExecutionResult:
        self._claim_output("buffered")
        try:
            stdout, stderr = self._process.communicate(
                timeout=None if timeout is None else timeout.total_seconds()
            )
        except subprocess.TimeoutExpired as error:
            raise TimeoutError("Process wait timed out") from error
        exit_code = self._process.returncode
        if exit_code is None:
            exit_code = self._process.poll()
        if exit_code is None:
            raise RuntimeError("Process completed without an exit code")
        if stdout is None or stderr is None:
            raise RuntimeError("Process output pipes were not captured")
        return ExecutionResult(exit_code, stdout, stderr)

    def terminate(self) -> None:
        terminate_process(self._process)

    def kill(self) -> None:
        kill_process(self._process)

    def stdout_lines(self) -> Iterator[str]:
        self._claim_output("streaming")
        stdout = _stdout_pipe(self._process)
        if stdout is None:
            raise RuntimeError("Process stdout was not captured")
        for line in stdout:
            yield line.decode("utf-8")

    def stderr_lines(self) -> Iterator[str]:
        self._claim_output("streaming")
        stderr = _stderr_pipe(self._process)
        if stderr is None:
            raise RuntimeError("Process stderr was not captured")
        for line in stderr:
            yield line.decode("utf-8")

    def close(self) -> None:
        close_process_pipes(self._process)

    def _claim_output(self, mode: str) -> None:
        if self._output_mode is None:
            self._output_mode = mode
        elif self._output_mode != mode:
            raise RuntimeError("Process output is already owned by another consumer")


class LocalExecutor:
    """Stdlib executor preserving the SDK's existing local process behavior."""

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        try:
            result = run_with_timeout(
                request.argv,
                stdin=request.stdin,
                timeout=request.timeout,
                cwd=request.cwd,
                env=self._environment(request),
            )
        except FileNotFoundError as error:
            raise ExecutableNotFoundError(f"Executable not found: {request.argv[0]}") from error
        except PermissionError as error:
            raise ExecutableNotRunnableError(
                f"Executable not runnable: {request.argv[0]}"
            ) from error
        return ExecutionResult(result.returncode, result.stdout, result.stderr)

    def spawn(self, request: ExecutionRequest) -> LocalProcessHandle:
        try:
            return LocalProcessHandle(
                create_process(request.argv, cwd=request.cwd, env=self._environment(request))
            )
        except FileNotFoundError as error:
            raise ExecutableNotFoundError(f"Executable not found: {request.argv[0]}") from error
        except PermissionError as error:
            raise ExecutableNotRunnableError(
                f"Executable not runnable: {request.argv[0]}"
            ) from error

    @contextlib.contextmanager
    def stage(self, label: str, content: bytes) -> Iterator[str]:
        with tempfile.TemporaryDirectory(prefix=f"multica-py-{label}-") as directory:
            path = os.path.join(directory, label)
            with open(path, "wb") as staged:
                staged.write(content)
            yield path

    def close(self) -> None:
        return None

    def __enter__(self) -> LocalExecutor:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _environment(self, request: ExecutionRequest) -> dict[str, str]:
        environment = dict(os.environ)
        environment.update(dict(request.environment))
        return environment
