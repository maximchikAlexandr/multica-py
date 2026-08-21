from __future__ import annotations

import asyncio
import contextlib
import datetime
import importlib
import os
import signal
import threading
import uuid
from collections.abc import Coroutine, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Protocol, TypeVar, cast

from multica_py._internal.decoders import decode_text
from multica_py.exceptions import (
    ExecutableNotFoundError,
    ExecutableNotRunnableError,
    ProcessTimeoutError,
)
from multica_py.execution.base import (
    ExecutionConnectionError,
    ExecutionError,
    ExecutionRequest,
    ExecutionResult,
    ExecutionTargetNotFoundError,
    ExecutionUnavailableError,
    OutputOwnership,
    _cleanup_after,
    executable_result,
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

    async def read(self, path: str) -> bytes: ...

    async def mkdir(self, path: str) -> None: ...

    async def remove_dir(self, path: str) -> None: ...

    async def stat(self, path: str) -> _FsMetadata: ...

    async def list(self, path: str) -> Sequence[_FsEntry]: ...


class _FsMetadata(Protocol):
    @property
    def kind(self) -> object: ...


class _FsEntry(Protocol):
    @property
    def path(self) -> str: ...


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


@dataclass(frozen=True, slots=True)
class _MicrosandboxBindings:
    factory: type[_SandboxFactory]
    errors: _MicrosandboxErrorTypes


def _load_microsandbox() -> _MicrosandboxBindings:
    try:
        module = importlib.import_module("microsandbox")
    except ImportError as error:
        raise ImportError(
            "Microsandbox execution requires the optional 'microsandbox' dependency. "
            'Install it with: pip install "multica-py[microsandbox]"'
        ) from error
    try:
        factory = cast("type[_SandboxFactory]", getattr(module, "Sandbox"))
    except AttributeError as error:
        raise ImportError("Installed microsandbox package does not expose Sandbox") from error
    return _MicrosandboxBindings(factory, _MicrosandboxErrorTypes(module))


class _MicrosandboxProcessHandle:
    """Per-command controls do not guarantee cleanup of command descendants."""

    def __init__(
        self,
        executor: MicrosandboxExecutor,
        argv: tuple[str, ...],
        handle: _ExecHandle,
        default_timeout: datetime.timedelta | None,
    ) -> None:
        self._executor = executor
        self._argv = argv
        self._handle = handle
        self._default_timeout = default_timeout
        self._exit_code: int | None = None
        self._output = OutputOwnership()
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
                self._handle.wait(),
                timeout=_seconds(timeout if timeout is not None else self._default_timeout),
            )
        except ProcessTimeoutError:
            self.kill()
            raise
        except TimeoutError as error:
            self.kill()
            raise ProcessTimeoutError("Microsandbox process wait timed out") from error
        self._exit_code = exit_code
        return exit_code

    def collect(self, timeout: datetime.timedelta | None = None) -> ExecutionResult:
        self._output.claim("buffered")
        try:
            output = self._executor._provider_call(
                self._handle.collect(),
                timeout=_seconds(timeout if timeout is not None else self._default_timeout),
            )
        except ProcessTimeoutError:
            self.kill()
            raise
        except TimeoutError as error:
            self.kill()
            raise ProcessTimeoutError("Microsandbox process collection timed out") from error
        result = _result(output)
        self._exit_code = result.exit_code
        return executable_result(result, self._argv)

    def terminate(self) -> None:
        """Send SIGTERM to this command only; descendant cleanup is not guaranteed."""
        self._executor._provider_call(self._handle.signal(signal.SIGTERM))

    def kill(self) -> None:
        """Send native SIGKILL to this command only; descendant cleanup is not guaranteed."""
        self._executor._provider_call(self._handle.kill())

    def kill_immediate(self) -> None:
        """Send native SIGKILL without extra provider-side cleanup work."""
        self.kill()

    def stdout_lines(self) -> Iterator[str]:
        self._output.claim("streaming")
        yield from self._lines("stdout")

    def stderr_lines(self) -> Iterator[str]:
        self._output.claim("streaming")
        yield from self._lines("stderr")

    def close(self) -> None:
        return None

    def _lines(self, stream: str) -> Iterator[str]:
        queued = self._stdout if stream == "stdout" else self._stderr
        while queued:
            yield decode_text(queued.pop(0))
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
                yield decode_text(queued.pop(0))


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
        _bindings: _MicrosandboxBindings | None = None,
    ) -> None:
        self._loop = asyncio.new_event_loop()
        self._ready = threading.Event()
        self._closed = False
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._ready.wait()
        try:
            bindings = _bindings if _bindings is not None else _load_microsandbox()
            self._provider_errors = bindings.errors
            handle = self._call(bindings.factory.get(sandbox), timeout=_seconds(connection_timeout))
            self._sandbox = self._call(
                handle.connect(timeout=_seconds(connection_timeout)),
                timeout=_seconds(connection_timeout),
            )
        except Exception as error:
            self._shutdown_loop()
            raise self._map_error(error) from error

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        output = self._provider_call(
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
        return executable_result(_result(output), request.argv)

    def spawn(self, request: ExecutionRequest) -> _MicrosandboxProcessHandle:
        handle = self._provider_call(
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
        return _MicrosandboxProcessHandle(self, request.argv, handle, request.timeout)

    @contextlib.contextmanager
    def stage(self, label: str, content: bytes) -> Iterator[str]:
        path = f"/tmp/multica-py-{uuid.uuid4().hex}-{os.path.basename(label)}"
        with _cleanup_after(lambda: self._provider_call(self._sandbox.fs.remove(path))):
            self._provider_call(self._sandbox.fs.write(path, content))
            yield path

    @contextlib.contextmanager
    def capture_output(self, label: str) -> Iterator[_MicrosandboxOutputArtifact]:
        path = f"/tmp/multica-py-output-{uuid.uuid4().hex}"
        self._provider_call(self._sandbox.fs.mkdir(path))
        artifact = _MicrosandboxOutputArtifact(self, path)
        with _cleanup_after(artifact.cleanup):
            yield artifact

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
        except TimeoutError as error:
            future.cancel()
            if isinstance(error, ProcessTimeoutError):
                raise
            raise ProcessTimeoutError("Microsandbox operation timed out") from error

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

    def _map_error(self, error: Exception) -> Exception:
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
        if isinstance(error, self._provider_errors.target):
            return ExecutionTargetNotFoundError(str(error))
        if isinstance(error, self._provider_errors.unavailable):
            return ExecutionUnavailableError(str(error))
        if isinstance(error, self._provider_errors.connection):
            return ExecutionConnectionError(str(error))
        return ExecutionUnavailableError(str(error))


class _MicrosandboxErrorTypes:
    def __init__(self, module: object) -> None:
        self.target = _provider_types(module, "SandboxNotFoundError", "PathNotFoundError")
        self.unavailable = _provider_types(module, "SandboxNotRunningError", "ExecFailedError")
        self.connection = _provider_types(module, "CloudHttpError", "IoError")


def _provider_types(module: object, *names: str) -> tuple[type[Exception], ...]:
    types: list[type[Exception]] = []
    for name in names:
        value = cast("object", getattr(module, name, None))
        if type(value) is type and issubclass(cast("type[object]", value), Exception):  # type: ignore[misc]
            types.append(cast("type[Exception]", value))
    return tuple(types)


def _seconds(timeout: datetime.timedelta | None) -> float | None:
    return None if timeout is None else timeout.total_seconds()


class _MicrosandboxOutputArtifact:
    def __init__(self, executor: MicrosandboxExecutor, path: str) -> None:
        self._executor = executor
        self.path = path

    def read(self, returned_path: str) -> bytes:
        candidate = PurePosixPath(returned_path)
        root = PurePosixPath(self.path)
        path = candidate if candidate.is_absolute() else root / candidate
        if path.parent != root or path.name in {"", ".", ".."}:
            raise ValueError("downloaded path must be in the SDK-owned target output directory")
        read_path = str(path)
        metadata = self._executor._provider_call(self._executor._sandbox.fs.stat(read_path))
        if getattr(metadata.kind, "value", metadata.kind) != "file":
            raise ValueError(
                "downloaded path must be a regular file in the SDK-owned target output directory"
            )
        return self._executor._provider_call(self._executor._sandbox.fs.read(read_path))

    def cleanup(self) -> None:
        for entry in self._executor._provider_call(self._executor._sandbox.fs.list(self.path)):
            self._executor._provider_call(self._executor._sandbox.fs.remove(entry.path))
        self._executor._provider_call(self._executor._sandbox.fs.remove_dir(self.path))
