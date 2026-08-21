from __future__ import annotations

import datetime
import warnings
from collections.abc import Callable, Iterator

import msgspec

from multica_py._internal.concurrency import ProcessSemaphore
from multica_py.exceptions import ProcessOutputModeError
from multica_py.execution import ExecutionResult, ProcessHandle
from multica_py.execution.base import OutputOwnership


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


# ponytail: MUST be closed (use `with`) to release the process semaphore; __del__ is a backstop, not a primary path
class ManagedProcess:
    def __init__(
        self,
        handle: ProcessHandle,
        argv: tuple[str, ...] = (),
        semaphore: ProcessSemaphore | None = None,
        cleanup: Callable[[], None] | None = None,
    ) -> None:
        self._handle = handle
        self._argv = argv
        self._semaphore = semaphore
        self._cleanup = cleanup
        self._closed = False
        self._output = OutputOwnership()
        self._result: ProcessResult | None = None
        self._active_streams: set[str] = set()

    def _claim_mode(self, mode: str, consumer: str) -> None:
        if self._output.mode is None:
            self._output.claim(mode, lambda owner: ProcessOutputModeError(owner, consumer))
            return
        if self._output.mode == mode:
            return
        raise ProcessOutputModeError(self._output.mode or "discarded", consumer)

    def _claim_buffered(self, consumer: str = "buffered result") -> None:
        self._claim_mode("buffered", consumer)

    def _claim_streaming(self, consumer: str) -> None:
        self._claim_mode("streaming", consumer)

    def _make_result(self, result: ExecutionResult) -> ProcessResult:
        return ProcessResult(
            self._argv,
            result.exit_code,
            result.stdout.decode("utf-8"),
            result.stderr.decode("utf-8"),
        )

    def _finalize(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._handle.close()
        finally:
            try:
                if self._cleanup is not None:
                    cleanup = self._cleanup
                    self._cleanup = None
                    cleanup()
            finally:
                if self._semaphore is not None:
                    self._semaphore.release()

    def _maybe_finalize(self, *, exit_code: int | None = None) -> None:
        if self._closed or self._output.mode != "streaming" or self._active_streams:
            return
        if exit_code is None:
            exit_code = self._handle.poll()
        if exit_code is not None:
            self._finalize()

    @property
    def id(self) -> str | int | None:
        return self._handle.id

    @property
    def pid(self) -> int | None:
        handle_id = self._handle.id
        return handle_id if isinstance(handle_id, int) else None

    @property
    def argv(self) -> tuple[str, ...]:
        return self._argv

    def poll(self) -> int | None:
        exit_code = self._handle.poll()
        self._maybe_finalize(exit_code=exit_code)
        return exit_code

    def wait(self, timeout: datetime.timedelta | None = None) -> int:
        return self.result(timeout).exit_code

    def result(self, timeout: datetime.timedelta | None = None) -> ProcessResult:
        self._claim_buffered()
        if self._result is not None:
            return self._result

        try:
            execution_result = self._handle.collect(timeout)
        except TimeoutError:
            raise TimeoutError("Process wait timed out")

        try:
            result = self._make_result(execution_result)
        except BaseException:
            self._output.discard()
            self._finalize()
            raise

        self._result = result
        self._finalize()
        return result

    def terminate(self) -> None:
        self._handle.terminate()

    def kill(self) -> None:
        self._handle.kill()

    def stdout_lines(self) -> Iterator[str]:
        self._claim_streaming("stdout stream")
        self._active_streams.add("stdout")
        try:
            for line in self._handle.stdout_lines():
                yield line.rstrip("\n")
        finally:
            self._active_streams.discard("stdout")
            self._maybe_finalize()

    def stderr_lines(self) -> Iterator[str]:
        self._claim_streaming("stderr stream")
        self._active_streams.add("stderr")
        try:
            for line in self._handle.stderr_lines():
                yield line.rstrip("\n")
        finally:
            self._active_streams.discard("stderr")
            self._maybe_finalize()

    def _kill_immediate(self) -> None:
        self._handle.kill_immediate()

    def __del__(self) -> None:
        if self._closed:
            return
        live = self._handle.poll() is None
        if live:
            warnings.warn(
                f"{type(self).__name__} for {self._argv} was never closed; killing process without grace period",
                ResourceWarning,
                stacklevel=2,
            )
        self._output.discard()
        try:
            if live:
                self._kill_immediate()
        finally:
            self._finalize()

    def close(self) -> None:
        if self._closed:
            return
        self._output.discard()
        if self._handle.poll() is None:
            self.terminate()
            try:
                self._handle.wait(datetime.timedelta(seconds=3))
            except TimeoutError:
                self.kill()
                self._handle.wait(datetime.timedelta(seconds=3))
        self._finalize()

    def __enter__(self) -> ManagedProcess:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
