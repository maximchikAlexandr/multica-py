from __future__ import annotations

import datetime
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from multica_py.exceptions import ExecutableNotFoundError, ExecutableNotRunnableError, MulticaError


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    argv: tuple[str, ...]
    cwd: str | None = None
    environment: tuple[tuple[str, str], ...] = ()
    stdin: bytes | None = None
    timeout: datetime.timedelta | None = None


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    exit_code: int
    stdout: bytes
    stderr: bytes


@runtime_checkable
class ProcessHandle(Protocol):
    @property
    def id(self) -> str | int | None: ...

    def poll(self) -> int | None: ...

    def wait(self, timeout: datetime.timedelta | None = None) -> int: ...

    def collect(self, timeout: datetime.timedelta | None = None) -> ExecutionResult: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...

    def stdout_lines(self) -> Iterator[str]: ...

    def stderr_lines(self) -> Iterator[str]: ...

    def close(self) -> None: ...


@runtime_checkable
class OutputArtifact(Protocol):
    """One SDK-owned target file whose bytes can be retrieved before cleanup."""

    @property
    def path(self) -> str: ...

    def read(self, returned_path: str) -> bytes: ...


@runtime_checkable
class CommandExecutor(Protocol):
    def run(self, request: ExecutionRequest) -> ExecutionResult: ...

    def spawn(self, request: ExecutionRequest) -> ProcessHandle: ...

    def stage(self, label: str, content: bytes) -> AbstractContextManager[str]: ...

    def capture_output(self, label: str) -> AbstractContextManager[OutputArtifact]: ...

    def close(self) -> None: ...

    def __enter__(self) -> CommandExecutor: ...

    def __exit__(self, *args: object) -> None: ...


class ExecutionError(MulticaError):
    """An execution target failed before the Multica CLI could run."""


class ExecutionConnectionError(ExecutionError):
    """The execution target could not be reached."""


class ExecutionTargetNotFoundError(ExecutionError):
    """The requested execution target does not exist."""


class ExecutionUnavailableError(ExecutionError):
    """The execution provider cannot currently execute commands."""


class OutputOwnership:
    """Small shared single-owner guard for buffered versus streamed output."""

    def __init__(self) -> None:
        self._mode: str | None = None

    def claim(self, mode: str, error: Callable[[str], Exception] | None = None) -> None:
        if self._mode is None or self._mode == mode:
            self._mode = mode
            return
        if error is None:
            raise RuntimeError("Process output is already owned by another consumer")
        raise error(self._mode)

    @property
    def mode(self) -> str | None:
        return self._mode

    def discard(self) -> None:
        self._mode = "discarded"


def executable_result(result: ExecutionResult, argv: tuple[str, ...]) -> ExecutionResult:
    """Turn POSIX shell executable statuses into the SDK's typed errors."""
    if result.exit_code == 127:
        raise ExecutableNotFoundError(f"Executable not found: {argv[0]}")
    if result.exit_code == 126:
        raise ExecutableNotRunnableError(f"Executable not runnable: {argv[0]}")
    return result


@contextmanager
def _cleanup_after(cleanup: Callable[[], None]) -> Iterator[None]:
    """Run cleanup without hiding an exception raised by the managed body."""
    body_error: BaseException | None = None
    try:
        yield
    except BaseException as error:
        body_error = error
        raise
    finally:
        try:
            cleanup()
        except Exception:
            if body_error is None:
                raise
