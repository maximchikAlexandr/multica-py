from __future__ import annotations

import datetime
from collections.abc import Iterator
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from multica_py.exceptions import MulticaError


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
class CommandExecutor(Protocol):
    def run(self, request: ExecutionRequest) -> ExecutionResult: ...

    def spawn(self, request: ExecutionRequest) -> ProcessHandle: ...

    def stage(self, label: str, content: bytes) -> AbstractContextManager[str]: ...

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
