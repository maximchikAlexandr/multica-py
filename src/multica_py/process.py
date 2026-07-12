from __future__ import annotations

import contextlib
import datetime
import subprocess
from collections.abc import Iterator
from typing import BinaryIO, cast

from multica_py._internal.concurrency import ProcessSemaphore
from multica_py._internal.processes import kill_process, terminate_process


def _stdin_pipe(process: subprocess.Popen[bytes]) -> BinaryIO | None:
    return cast("BinaryIO | None", process.stdin)


def _stdout_pipe(process: subprocess.Popen[bytes]) -> BinaryIO | None:
    return cast("BinaryIO | None", process.stdout)


def _stderr_pipe(process: subprocess.Popen[bytes]) -> BinaryIO | None:
    return cast("BinaryIO | None", process.stderr)


class ManagedProcess:
    def __init__(
        self,
        process: subprocess.Popen[bytes],
        argv: tuple[str, ...] = (),
        semaphore: ProcessSemaphore | None = None,
    ) -> None:
        self._process = process
        self._argv = argv
        self._semaphore = semaphore
        self._closed = False

    def _finalize(self) -> None:
        if self._closed:
            return
        self._closed = True
        stdout_pipe = _stdout_pipe(self._process)
        stderr_pipe = _stderr_pipe(self._process)
        stdin_pipe = _stdin_pipe(self._process)
        for pipe in (stdout_pipe, stderr_pipe, stdin_pipe):
            if pipe is not None:
                with contextlib.suppress(OSError):
                    pipe.close()
        if self._semaphore is not None:
            self._semaphore.release()

    @property
    def pid(self) -> int:
        return self._process.pid or 0

    @property
    def argv(self) -> tuple[str, ...]:
        return self._argv

    def poll(self) -> int | None:
        return self._process.poll()

    def wait(self, timeout: datetime.timedelta | None = None) -> int:
        try:
            timeout_sec = timeout.total_seconds() if timeout else None
            rc = self._process.wait(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            raise TimeoutError("Process wait timed out")
        self._finalize()
        return rc

    def terminate(self) -> None:
        terminate_process(self._process)

    def kill(self) -> None:
        kill_process(self._process)

    def stdout_lines(self) -> Iterator[str]:
        stdout_pipe = _stdout_pipe(self._process)
        assert stdout_pipe is not None
        try:
            for line in stdout_pipe:
                yield line.decode("utf-8").rstrip("\n")
        finally:
            if self._process.poll() is not None:
                self._finalize()

    def stderr_lines(self) -> Iterator[str]:
        stderr_pipe = _stderr_pipe(self._process)
        assert stderr_pipe is not None
        try:
            for line in stderr_pipe:
                yield line.decode("utf-8").rstrip("\n")
        finally:
            if self._process.poll() is not None:
                self._finalize()

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        if self._closed:
            return
        if self._process.poll() is None:
            self.terminate()
            try:
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.kill()
                self._process.wait(timeout=3)
        self._finalize()

    def __enter__(self) -> ManagedProcess:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
