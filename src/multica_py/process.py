from __future__ import annotations

import datetime
import subprocess
from collections.abc import Iterator
from typing import BinaryIO, Literal, cast

import msgspec

from multica_py._internal.concurrency import ProcessSemaphore
from multica_py._internal.processes import close_process_pipes, kill_process, terminate_process
from multica_py.exceptions import ProcessOutputModeError


class ProcessResult(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    argv: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    @property
    def failed(self) -> bool:
        return not self.ok


_OutputMode = Literal["unclaimed", "buffered", "streaming", "discarded"]


def _stdin_pipe(process: subprocess.Popen[bytes]) -> BinaryIO | None:
    return cast("BinaryIO | None", process.stdin)


def _stdout_pipe(process: subprocess.Popen[bytes]) -> BinaryIO | None:
    return cast("BinaryIO | None", process.stdout)


def _stderr_pipe(process: subprocess.Popen[bytes]) -> BinaryIO | None:
    return cast("BinaryIO | None", process.stderr)


# ponytail: MUST be closed (use `with`) to release the process semaphore; __del__ is a backstop, not a primary path
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
        self._output_mode: _OutputMode = "unclaimed"
        self._result: ProcessResult | None = None

    def _claim_mode(self, mode: Literal["buffered", "streaming"], consumer: str) -> None:
        if self._output_mode == "unclaimed":
            self._output_mode = mode
            return
        if self._output_mode == mode:
            return
        raise ProcessOutputModeError(self._output_mode, consumer)

    def _claim_buffered(self, consumer: str = "buffered result") -> None:
        self._claim_mode("buffered", consumer)

    def _claim_streaming(self, consumer: str) -> None:
        self._claim_mode("streaming", consumer)

    def _make_result(
        self,
        stdout_data: bytes | None,
        stderr_data: bytes | None,
    ) -> ProcessResult:
        exit_code = self._process.returncode
        if exit_code is None:
            exit_code = self._process.poll()
        if exit_code is None:
            raise RuntimeError("Process completed without an exit code")
        if stdout_data is None or stderr_data is None:
            raise RuntimeError("Process output pipes were not captured")
        return ProcessResult(
            self._argv,
            exit_code,
            stdout_data.decode("utf-8"),
            stderr_data.decode("utf-8"),
        )

    def _finalize(self) -> None:
        if self._closed:
            return
        self._closed = True
        close_process_pipes(self._process)
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
        return self.result(timeout).exit_code

    def result(self, timeout: datetime.timedelta | None = None) -> ProcessResult:
        self._claim_buffered()
        if self._result is not None:
            return self._result

        timeout_sec = timeout.total_seconds() if timeout is not None else None
        try:
            stdout_data, stderr_data = self._process.communicate(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            raise TimeoutError("Process wait timed out")

        try:
            result = self._make_result(stdout_data, stderr_data)
        except BaseException:
            self._output_mode = "discarded"
            self._finalize()
            raise

        self._result = result
        self._finalize()
        return result

    def terminate(self) -> None:
        terminate_process(self._process)

    def kill(self) -> None:
        kill_process(self._process)

    def stdout_lines(self) -> Iterator[str]:
        self._claim_streaming("stdout stream")
        stdout_pipe = _stdout_pipe(self._process)
        assert stdout_pipe is not None
        try:
            for line in stdout_pipe:
                yield line.decode("utf-8").rstrip("\n")
        finally:
            if self._process.poll() is not None:
                self._finalize()

    def stderr_lines(self) -> Iterator[str]:
        self._claim_streaming("stderr stream")
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
        self._output_mode = "discarded"
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
