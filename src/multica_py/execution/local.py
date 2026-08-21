from __future__ import annotations

import contextlib
import datetime
import io
import os
import stat
import subprocess
import tempfile
import threading
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
from multica_py.execution.base import ExecutionRequest, ExecutionResult, OutputOwnership


class LocalProcessHandle:
    def __init__(
        self, process: subprocess.Popen[bytes], *, default_timeout: datetime.timedelta | None = None
    ) -> None:
        self._process = process
        self._default_timeout = default_timeout
        self._output = OutputOwnership()
        self._drain_lock = threading.Lock()
        self._drained: set[str] = set()
        self._drain_thread: threading.Thread | None = None

    @property
    def id(self) -> int:
        return self._process.pid

    def poll(self) -> int | None:
        return self._process.poll()

    def wait(self, timeout: datetime.timedelta | None = None) -> int:
        try:
            effective_timeout = timeout if timeout is not None else self._default_timeout
            return self._process.wait(
                None if effective_timeout is None else effective_timeout.total_seconds()
            )
        except subprocess.TimeoutExpired as error:
            raise TimeoutError("Process wait timed out") from error

    def collect(self, timeout: datetime.timedelta | None = None) -> ExecutionResult:
        self._output.claim("buffered")
        effective_timeout = timeout if timeout is not None else self._default_timeout
        try:
            stdout, stderr = self._process.communicate(
                timeout=None if effective_timeout is None else effective_timeout.total_seconds()
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

    def _drain_other(self, consumed: str) -> None:
        other = "stderr" if consumed == "stdout" else "stdout"
        with self._drain_lock:
            if other in self._drained:
                return
            self._drained.add(other)
        pipe = cast("BinaryIO | None", cast("object", getattr(self._process, other)))
        if pipe is None or not isinstance(pipe, io.IOBase):
            return
        reader: BinaryIO = pipe

        def _drain() -> None:
            with contextlib.suppress(OSError, ValueError):
                while True:
                    chunk = reader.read(4096)
                    if not chunk:
                        break

        thread = threading.Thread(target=_drain, name=f"multica-py-drain-{other}", daemon=True)
        with self._drain_lock:
            self._drain_thread = thread
        thread.start()

    def stdout_lines(self) -> Iterator[str]:
        self._output.claim("streaming")
        self._drain_other("stdout")
        stdout = cast("BinaryIO | None", cast("object", self._process.stdout))
        if stdout is None:
            raise RuntimeError("Process stdout was not captured")
        for line in stdout:
            yield line.decode("utf-8")

    def stderr_lines(self) -> Iterator[str]:
        self._output.claim("streaming")
        self._drain_other("stderr")
        stderr = cast("BinaryIO | None", cast("object", self._process.stderr))
        if stderr is None:
            raise RuntimeError("Process stderr was not captured")
        for line in stderr:
            yield line.decode("utf-8")

    def close(self) -> None:
        with self._drain_lock:
            thread = self._drain_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=5.0)
        close_process_pipes(self._process)


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
            process = create_process(request.argv, cwd=request.cwd, env=self._environment(request))
            if request.stdin is not None:
                stdin = cast("BinaryIO | None", cast("object", process.stdin))
                if stdin is None:
                    raise RuntimeError("Process stdin was not captured")
                stdin.write(request.stdin)
                stdin.close()
                process.stdin = None
            return LocalProcessHandle(process, default_timeout=request.timeout)
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
            os.chmod(path, 0o600)
            yield path

    @contextlib.contextmanager
    def capture_output(self, label: str) -> Iterator[_LocalOutputArtifact]:
        with tempfile.TemporaryDirectory(prefix=f"multica-py-output-{label}-") as directory:
            yield _LocalOutputArtifact(directory)

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


class _LocalOutputArtifact:
    def __init__(self, path: str) -> None:
        self.path = path

    def read(self, returned_path: str) -> bytes:
        output_path = _output_path(self.path, returned_path)
        flags = os.O_RDONLY | os.O_NONBLOCK
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(output_path, flags)
        except OSError as error:
            raise ValueError(
                "downloaded path must be a regular file in the temporary output directory"
            ) from error
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ValueError(
                    "downloaded path must be a regular file in the temporary output directory"
                )
            with os.fdopen(descriptor, "rb", closefd=False) as output:
                return output.read()
        finally:
            os.close(descriptor)


def _output_path(root: str, returned_path: str) -> str:
    candidate = returned_path if os.path.isabs(returned_path) else os.path.join(root, returned_path)
    if (
        os.path.dirname(candidate) != root
        or os.path.basename(candidate) in {"", ".", ".."}
        or os.path.islink(candidate)
        or os.path.dirname(os.path.realpath(candidate)) != os.path.realpath(root)
    ):
        raise ValueError("downloaded path must stay in the temporary output directory")
    return candidate
