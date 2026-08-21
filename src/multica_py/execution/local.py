from __future__ import annotations

import contextlib
import datetime
import io
import os
import queue
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
        self._stream_lock = threading.Lock()
        self._stream_queues: dict[str, queue.SimpleQueue[bytes | None]] = {}
        self._stream_threads: list[threading.Thread] = []

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

    def _pipe(self, name: str) -> BinaryIO | None:
        return cast("BinaryIO | None", cast("object", getattr(self._process, name)))

    def _pump_pipe(self, pipe: BinaryIO, chunks: queue.SimpleQueue[bytes | None]) -> None:
        try:
            while True:
                chunk = pipe.read(4096)
                if not chunk:
                    break
                chunks.put(chunk)
        except (OSError, ValueError):
            pass
        finally:
            chunks.put(None)

    def _ensure_stream_pumps(self) -> None:
        with self._stream_lock:
            if self._stream_queues:
                return
            for name in ("stdout", "stderr"):
                chunks: queue.SimpleQueue[bytes | None] = queue.SimpleQueue()
                self._stream_queues[name] = chunks
                pipe = self._pipe(name)
                if pipe is None or not isinstance(pipe, io.IOBase):
                    chunks.put(None)
                    continue
                thread = threading.Thread(
                    target=self._pump_pipe,
                    args=(pipe, chunks),
                    name=f"multica-py-stream-{name}",
                    daemon=True,
                )
                self._stream_threads.append(thread)
                thread.start()

    def _stream_lines(self, name: str) -> Iterator[str]:
        self._output.claim("streaming")
        pipe = self._pipe(name)
        if pipe is None:
            raise RuntimeError(f"Process {name} was not captured")
        if not isinstance(pipe, io.IOBase):
            for line in pipe:
                yield line.decode("utf-8")
            return
        self._ensure_stream_pumps()
        leftover = b""
        while True:
            chunk = self._stream_queues[name].get()
            if chunk is None:
                if leftover:
                    yield leftover.decode("utf-8")
                return
            leftover += chunk
            *lines, leftover = leftover.split(b"\n")
            for line in lines:
                yield line.decode("utf-8") + "\n"

    def stdout_lines(self) -> Iterator[str]:
        return self._stream_lines("stdout")

    def stderr_lines(self) -> Iterator[str]:
        return self._stream_lines("stderr")

    def close(self) -> None:
        close_process_pipes(self._process)
        with self._stream_lock:
            threads = list(self._stream_threads)
        for thread in threads:
            thread.join(timeout=5.0)


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
