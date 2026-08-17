from __future__ import annotations

import asyncio
import contextlib
import datetime
import importlib
import os
import signal
import threading
import uuid
from collections.abc import Coroutine, Iterator, Mapping
from typing import Protocol, TypeVar, cast

from multica_py.exceptions import ExecutableNotFoundError, ExecutableNotRunnableError
from multica_py.execution.base import (
    ExecutionConnectionError,
    ExecutionError,
    ExecutionRequest,
    ExecutionResult,
    ExecutionTargetNotFoundError,
    ExecutionUnavailableError,
)


class _ExecOutput(Protocol):
    @property
    def exit_code(self) -> int: ...

    @property
    def stdout_bytes(self) -> bytes: ...

    @property
    def stderr_bytes(self) -> bytes: ...


class _ExecEvent(Protocol):
    @property
    def event_type(self) -> str: ...

    @property
    def data(self) -> bytes: ...


class _ExecHandle(Protocol):
    @property
    def id(self) -> str: ...

    def __aiter__(self) -> _ExecHandle: ...

    async def __anext__(self) -> _ExecEvent: ...

    async def wait(self) -> tuple[int, bool]: ...

    async def collect(self) -> _ExecOutput: ...

    async def signal(self, sig: int) -> None: ...

    async def kill(self) -> None: ...


class _SandboxFs(Protocol):
    async def write(self, path: str, data: bytes) -> None: ...

    async def remove(self, path: str) -> None: ...


class _Sandbox(Protocol):
    @property
    def fs(self) -> _SandboxFs: ...

    async def exec(
        self,
        cmd: str,
        args: list[str],
        *,
        cwd: str | None,
        env: Mapping[str, str],
        timeout: float | None,
        stdin: bytes | None,
        tty: bool,
    ) -> _ExecOutput: ...

    async def exec_stream(
        self,
        cmd: str,
        args: list[str],
        *,
        cwd: str | None,
        env: Mapping[str, str],
        timeout: float | None,
        stdin: bytes | None,
        tty: bool,
    ) -> _ExecHandle: ...

    async def detach(self) -> None: ...


class _SandboxHandle(Protocol):
    async def connect(self, timeout: float | None = None) -> _Sandbox: ...


class _SandboxFactory(Protocol):
    @staticmethod
    async def get(name: str) -> _SandboxHandle: ...


_T = TypeVar("_T")


def _load_sandbox_factory() -> type[_SandboxFactory]:
    try:
        module = importlib.import_module("microsandbox")
    except ImportError as error:
        raise ImportError(
            "Microsandbox execution requires the optional 'microsandbox' dependency. "
            'Install it with: pip install "multica-py[microsandbox]"'
        ) from error
    return cast("type[_SandboxFactory]", getattr(module, "Sandbox"))


class _MicrosandboxProcessHandle:
    """Per-command controls do not guarantee cleanup of command descendants."""

    def __init__(
        self, executor: MicrosandboxExecutor, argv: tuple[str, ...], handle: _ExecHandle
    ) -> None:
        self._executor = executor
        self._argv = argv
        self._handle = handle
        self._exit_code: int | None = None
        self._output_mode: str | None = None
        self._stdout: list[bytes] = []
        self._stderr: list[bytes] = []

    @property
    def id(self) -> str:
        return self._handle.id

    def poll(self) -> int | None:
        return self._exit_code

    def wait(self, timeout: datetime.timedelta | None = None) -> int:
        try:
            exit_code, _success = self._executor._provider_call(
                self._handle.wait(), timeout=self._seconds(timeout)
            )
        except TimeoutError:
            self.kill()
            raise
        self._exit_code = exit_code
        return exit_code

    def collect(self, timeout: datetime.timedelta | None = None) -> ExecutionResult:
        self._claim_output("buffered")
        try:
            output = self._executor._provider_call(
                self._handle.collect(), timeout=self._seconds(timeout)
            )
        except TimeoutError:
            self.kill()
            raise
        result = _result(output)
        self._exit_code = result.exit_code
        return self._executor._result_or_executable_error(result, self._argv)

    def terminate(self) -> None:
        """Send SIGTERM to this command only; descendant cleanup is not guaranteed."""
        self._executor._provider_call(self._handle.signal(signal.SIGTERM))

    def kill(self) -> None:
        """Send native SIGKILL to this command only; descendant cleanup is not guaranteed."""
        self._executor._provider_call(self._handle.kill())

    def stdout_lines(self) -> Iterator[str]:
        self._claim_output("streaming")
        yield from self._lines("stdout")

    def stderr_lines(self) -> Iterator[str]:
        self._claim_output("streaming")
        yield from self._lines("stderr")

    def close(self) -> None:
        return None

    def _lines(self, stream: str) -> Iterator[str]:
        queued = self._stdout if stream == "stdout" else self._stderr
        while queued:
            yield queued.pop(0).decode("utf-8")
        while self._exit_code is None:
            event = self._executor._provider_call(_next_event(self._handle))
            if event is None:
                return
            if event.event_type == "exited":
                self._exit_code = _event_exit_code(event)
            elif event.event_type == "stdout":
                self._stdout.append(event.data)
            elif event.event_type == "stderr":
                self._stderr.append(event.data)
            while queued:
                yield queued.pop(0).decode("utf-8")

    def _claim_output(self, mode: str) -> None:
        if self._output_mode is None:
            self._output_mode = mode
        elif self._output_mode != mode:
            raise RuntimeError("Process output is already owned by another consumer")

    @staticmethod
    def _seconds(timeout: datetime.timedelta | None) -> float | None:
        return None if timeout is None else timeout.total_seconds()


def _event_exit_code(event: _ExecEvent) -> int:
    return cast("int", getattr(event, "code"))


def _result(output: _ExecOutput) -> ExecutionResult:
    return ExecutionResult(output.exit_code, output.stdout_bytes, output.stderr_bytes)


async def _next_event(handle: _ExecHandle) -> _ExecEvent | None:
    try:
        return await anext(handle)
    except StopAsyncIteration:
        return None


class MicrosandboxExecutor:
    """Run commands in an existing Microsandbox target through a private async loop."""

    def __init__(
        self,
        sandbox: str,
        *,
        connection_timeout: datetime.timedelta | None = None,
        _sandbox_factory: type[_SandboxFactory] | None = None,
    ) -> None:
        self._loop = asyncio.new_event_loop()
        self._ready = threading.Event()
        self._closed = False
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._ready.wait()
        try:
            factory = _sandbox_factory if _sandbox_factory is not None else _load_sandbox_factory()
            handle = self._call(factory.get(sandbox), timeout=_seconds(connection_timeout))
            self._sandbox = self._call(
                handle.connect(timeout=_seconds(connection_timeout)),
                timeout=_seconds(connection_timeout),
            )
        except Exception as error:
            self._shutdown_loop()
            raise self._map_error(error) from error

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        try:
            output = self._call(
                self._sandbox.exec(
                    request.argv[0],
                    list(request.argv[1:]),
                    cwd=request.cwd,
                    env=dict(request.environment),
                    timeout=_seconds(request.timeout),
                    stdin=request.stdin,
                    tty=False,
                ),
                timeout=_seconds(request.timeout),
            )
        except Exception as error:
            raise self._map_error(error) from error
        return self._result_or_executable_error(_result(output), request.argv)

    def spawn(self, request: ExecutionRequest) -> _MicrosandboxProcessHandle:
        try:
            handle = self._call(
                self._sandbox.exec_stream(
                    request.argv[0],
                    list(request.argv[1:]),
                    cwd=request.cwd,
                    env=dict(request.environment),
                    timeout=_seconds(request.timeout),
                    stdin=request.stdin,
                    tty=False,
                ),
                timeout=_seconds(request.timeout),
            )
        except Exception as error:
            raise self._map_error(error) from error
        return _MicrosandboxProcessHandle(self, request.argv, handle)

    @contextlib.contextmanager
    def stage(self, label: str, content: bytes) -> Iterator[str]:
        path = f"/tmp/multica-py-{uuid.uuid4().hex}-{os.path.basename(label)}"
        staged = False
        body_error: BaseException | None = None
        try:
            self._provider_call(self._sandbox.fs.write(path, content))
            staged = True
            yield path
        except BaseException as error:
            body_error = error
            raise
        finally:
            if staged:
                try:
                    self._provider_call(self._sandbox.fs.remove(path))
                except Exception:
                    if body_error is None:
                        raise

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._provider_call(self._sandbox.detach())
        finally:
            self._shutdown_loop()

    def __enter__(self) -> MicrosandboxExecutor:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._ready.set()
        self._loop.run_forever()

    def _call(
        self, coroutine: Coroutine[object, object, _T], *, timeout: float | None = None
    ) -> _T:
        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        try:
            return future.result(timeout)
        except TimeoutError:
            future.cancel()
            raise TimeoutError("Microsandbox operation timed out") from None

    def _provider_call(
        self, coroutine: Coroutine[object, object, _T], *, timeout: float | None = None
    ) -> _T:
        try:
            return self._call(coroutine, timeout=timeout)
        except Exception as error:
            raise self._map_error(error) from error

    def _shutdown_loop(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()
        self._loop.close()

    @staticmethod
    def _map_error(error: Exception) -> Exception:
        if isinstance(
            error,
            (
                ExecutableNotFoundError,
                ExecutableNotRunnableError,
                ExecutionError,
                ImportError,
                TimeoutError,
            ),
        ):
            return error
        if isinstance(error, FileNotFoundError):
            return ExecutableNotFoundError(str(error))
        if isinstance(error, PermissionError):
            return ExecutableNotRunnableError(str(error))
        name = type(error).__name__
        if name == "SandboxNotFoundError":
            return ExecutionTargetNotFoundError(str(error))
        if name in {"SandboxNotRunningError", "ExecFailedError"}:
            return ExecutionUnavailableError(str(error))
        if name in {"CloudHttpError", "IoError"}:
            return ExecutionConnectionError(str(error))
        return ExecutionUnavailableError(str(error))

    @staticmethod
    def _result_or_executable_error(
        result: ExecutionResult, argv: tuple[str, ...]
    ) -> ExecutionResult:
        if result.exit_code == 127:
            raise ExecutableNotFoundError(f"Executable not found: {argv[0]}")
        if result.exit_code == 126:
            raise ExecutableNotRunnableError(f"Executable not runnable: {argv[0]}")
        return result


def _seconds(timeout: datetime.timedelta | None) -> float | None:
    return None if timeout is None else timeout.total_seconds()
