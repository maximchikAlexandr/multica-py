from __future__ import annotations

import asyncio
import datetime
import importlib
import threading
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import cast

import pytest

from multica_py.exceptions import ExecutableNotFoundError, ExecutableNotRunnableError
from multica_py.execution import (
    ExecutionConnectionError,
    ExecutionRequest,
    ExecutionResult,
    ExecutionTargetNotFoundError,
    ExecutionUnavailableError,
)
from multica_py.execution.microsandbox import (
    MicrosandboxExecutor,
    _MicrosandboxBindings,
    _MicrosandboxErrorTypes,
    _SandboxFactory,
)


@dataclass(frozen=True)
class _Output:
    exit_code: int = 0
    stdout_bytes: bytes = b"stdout"
    stderr_bytes: bytes = b"stderr"


@dataclass(frozen=True)
class _Event:
    event_type: str
    data: bytes = b""
    code: int = 0


@dataclass
class _Exec:
    output: _Output = field(default_factory=_Output)
    events: deque[_Event] = field(
        default_factory=lambda: deque(
            [_Event("stdout", b"one\n"), _Event("stderr", b"two\n"), _Event("exited")]
        )
    )
    signals: list[int] = field(default_factory=list)
    killed: bool = False

    @property
    def id(self) -> str:
        return "exec-42"

    def __aiter__(self) -> _Exec:
        return self

    async def __anext__(self) -> _Event:
        if not self.events:
            raise StopAsyncIteration
        return self.events.popleft()

    async def wait(self) -> tuple[int, bool]:
        return self.output.exit_code, self.output.exit_code == 0

    async def collect(self) -> _Output:
        return self.output

    async def signal(self, sig: int) -> None:
        self.signals.append(sig)

    async def kill(self) -> None:
        self.killed = True


@dataclass
class _Fs:
    files: dict[str, bytes] = field(default_factory=dict)
    written: dict[str, bytes] = field(default_factory=dict)
    removed: list[str] = field(default_factory=list)
    mkdir_error: Exception | None = None
    write_error: Exception | None = None
    write_partial: bytes | None = None

    async def write(self, path: str, data: bytes) -> None:
        self.files[path] = data if self.write_partial is None else self.write_partial
        if self.write_error is not None:
            raise self.write_error

    async def remove(self, path: str) -> None:
        self.removed.append(path)
        if path in self.files:
            self.written[path] = self.files[path]
        self.files.pop(path, None)

    async def read(self, path: str) -> bytes:
        return self.files[path]

    async def mkdir(self, path: str) -> None:
        if self.mkdir_error is not None:
            raise self.mkdir_error

    async def remove_dir(self, path: str) -> None:
        return None

    async def stat(self, path: str) -> object:
        return type("Metadata", (), {"kind": "file"})()

    async def list(self, path: str) -> list[object]:
        return [
            type("Entry", (), {"path": file_path})()
            for file_path in self.files
            if file_path.startswith(path)
        ]


@dataclass(frozen=True)
class _StageEntryFailureCase:
    id: str
    configure: Callable[[_Fs], None]
    expected_error: str
    expected_written: bytes


def _configure_partial_fs_write_failure(fs: _Fs) -> None:
    fs.write_error = RuntimeError("write failed")
    fs.write_partial = b"part"


_STAGE_ENTRY_FAILURE_CASES: tuple[_StageEntryFailureCase, ...] = (
    _StageEntryFailureCase(
        "partial-fs-write",
        _configure_partial_fs_write_failure,
        "write failed",
        b"part",
    ),
)


@dataclass
class _Sandbox:
    fs: _Fs = field(default_factory=_Fs)
    output: _Output = field(default_factory=_Output)
    exec_handle: _Exec = field(default_factory=_Exec)
    calls: list[tuple[str, object]] = field(default_factory=list)
    caller_threads: list[int] = field(default_factory=list)
    detached: bool = False
    run_error: Exception | None = None

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
    ) -> _Output:
        if self.run_error is not None:
            raise self.run_error
        self.caller_threads.append(threading.get_ident())
        self.calls.append(("exec", (cmd, args, cwd, dict(env), timeout, stdin, tty)))
        return self.output

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
    ) -> _Exec:
        self.caller_threads.append(threading.get_ident())
        self.calls.append(("exec_stream", (cmd, args, cwd, dict(env), timeout, stdin, tty)))
        return self.exec_handle

    async def detach(self) -> None:
        self.detached = True

    async def stop(self) -> None:
        raise AssertionError("executor must not stop the sandbox")

    async def kill(self) -> None:
        raise AssertionError("executor must not kill the sandbox")

    async def remove(self) -> None:
        raise AssertionError("executor must not remove the sandbox")


@dataclass
class _SandboxHandle:
    sandbox: _Sandbox
    connected: bool = False

    async def connect(self, timeout: float | None = None) -> _Sandbox:
        self.connected = True
        return self.sandbox


@dataclass
class _Factory:
    sandbox: _Sandbox = field(default_factory=_Sandbox)
    names: list[str] = field(default_factory=list)
    handle: _SandboxHandle = field(init=False)

    def __post_init__(self) -> None:
        self.handle = _SandboxHandle(self.sandbox)

    async def get(self, name: str) -> _SandboxHandle:
        self.names.append(name)
        return self.handle


def _factory_type(factory: _Factory) -> type[_SandboxFactory]:
    class Factory:
        @staticmethod
        async def get(name: str) -> _SandboxHandle:
            return await factory.get(name)

    return cast("type[_SandboxFactory]", Factory)


def _bindings(
    factory: _Factory | type[_SandboxFactory], provider_module: object | None = None
) -> _MicrosandboxBindings:
    sandbox_factory = factory if isinstance(factory, type) else _factory_type(factory)
    return _MicrosandboxBindings(
        sandbox_factory,
        _MicrosandboxErrorTypes(provider_module if provider_module is not None else object()),
    )


def _request() -> ExecutionRequest:
    return ExecutionRequest(
        argv=("multica", "issue", "get", "MYL-42"),
        cwd="/srv/multica",
        environment=(("MULTICA_TOKEN", "target-only"),),
        stdin=b"request",
        timeout=datetime.timedelta(seconds=2),
    )


def test_connects_existing_sandbox_and_maps_run_on_private_loop() -> None:
    factory = _Factory()
    executor = MicrosandboxExecutor("existing", _bindings=_bindings(factory))

    result = executor.run(_request())

    assert factory.names == ["existing"]
    assert factory.handle.connected is True
    assert result == ExecutionResult(0, b"stdout", b"stderr")
    assert factory.sandbox.calls == [
        (
            "exec",
            (
                "multica",
                ["issue", "get", "MYL-42"],
                "/srv/multica",
                {"MULTICA_TOKEN": "target-only"},
                2.0,
                b"request",
                False,
            ),
        )
    ]
    assert factory.sandbox.caller_threads != [threading.get_ident()]
    executor.close()


def test_capture_output_rejects_path_traversal() -> None:
    factory = _Factory()
    executor = MicrosandboxExecutor("existing", _bindings=_bindings(factory))
    with executor.capture_output("download") as artifact, pytest.raises(ValueError):
        artifact.read("../outside")
    executor.close()


def test_capture_output_mkdir_failure_preserves_original_error_without_cleanup() -> None:
    factory = _Factory()
    factory.sandbox.fs.mkdir_error = RuntimeError("mkdir failed")
    executor = MicrosandboxExecutor("existing", _bindings=_bindings(factory))
    with (
        pytest.raises(ExecutionUnavailableError, match="mkdir failed"),
        executor.capture_output("download"),
    ):
        pass
    assert factory.sandbox.fs.removed == []
    executor.close()


def test_spawn_uses_native_collect_streaming_and_per_command_signals() -> None:
    factory = _Factory()
    executor = MicrosandboxExecutor("existing", _bindings=_bindings(factory))

    buffered = executor.spawn(_request())
    assert buffered.id == "exec-42"
    assert buffered.collect() == ExecutionResult(0, b"stdout", b"stderr")

    streaming = executor.spawn(_request())
    assert list(streaming.stdout_lines()) == ["one\n"]
    assert list(streaming.stderr_lines()) == ["two\n"]
    assert streaming.poll() == 0
    with pytest.raises(RuntimeError):
        streaming.collect()
    streaming.terminate()
    streaming.kill()
    assert factory.sandbox.exec_handle.signals == [15]
    assert factory.sandbox.exec_handle.killed is True
    executor.close()


class _Errors:
    class SandboxNotFoundError(Exception): ...

    class SandboxNotRunningError(Exception): ...

    class CloudHttpError(Exception): ...


@pytest.mark.parametrize(
    ("exit_code", "expected"),
    [(127, ExecutableNotFoundError), (126, ExecutableNotRunnableError)],
)
def test_posix_executable_exit_statuses_are_mapped_for_run_and_collect(
    exit_code: int, expected: type[Exception]
) -> None:
    factory = _Factory()
    factory.sandbox.output = _Output(exit_code, b"provider stdout", b"provider stderr")
    factory.sandbox.exec_handle.output = _Output(exit_code, b"provider stdout", b"provider stderr")
    executor = MicrosandboxExecutor("existing", _bindings=_bindings(factory))

    with pytest.raises(expected, match="multica"):
        executor.run(_request())
    with pytest.raises(expected, match="multica"):
        executor.spawn(_request()).collect()
    executor.close()


def test_staging_is_target_local_exact_and_cleaned() -> None:
    factory = _Factory()
    executor = MicrosandboxExecutor("existing", _bindings=_bindings(factory))

    with executor.stage("payload.bin", b"exact\x00bytes") as path:
        assert path.startswith("/tmp/multica-py-")
        assert factory.sandbox.fs.files[path] == b"exact\x00bytes"

    assert factory.sandbox.fs.files == {}
    assert factory.sandbox.fs.removed == [path]
    executor.close()


@pytest.mark.parametrize("case", _STAGE_ENTRY_FAILURE_CASES, ids=lambda case: case.id)
def test_staging_entry_failure_cleans_once_and_preserves_primary_error(
    case: _StageEntryFailureCase,
) -> None:
    factory = _Factory()
    case.configure(factory.sandbox.fs)
    executor = MicrosandboxExecutor("existing", _bindings=_bindings(factory))

    with (
        pytest.raises(ExecutionUnavailableError, match=case.expected_error),
        executor.stage("payload.bin", b"secret-bytes"),
    ):
        pass

    assert len(factory.sandbox.fs.removed) == 1
    path = factory.sandbox.fs.removed[0]
    assert factory.sandbox.fs.files == {}
    assert factory.sandbox.fs.written.get(path, b"") == case.expected_written
    executor.close()


def test_staging_preserves_write_or_body_failure_when_cleanup_also_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    factory = _Factory()
    executor = MicrosandboxExecutor("existing", _bindings=_bindings(factory))

    async def write_failure(path: str, data: bytes) -> None:
        raise RuntimeError("write failed")

    monkeypatch.setattr(factory.sandbox.fs, "write", write_failure)
    with (
        pytest.raises(ExecutionUnavailableError, match="write failed"),
        executor.stage("payload.bin", b"bytes"),
    ):
        pass

    async def write_ok(path: str, data: bytes) -> None:
        factory.sandbox.fs.files[path] = data

    async def remove_failure(path: str) -> None:
        raise RuntimeError("remove failed")

    monkeypatch.setattr(factory.sandbox.fs, "write", write_ok)
    monkeypatch.setattr(factory.sandbox.fs, "remove", remove_failure)
    with pytest.raises(ValueError, match="body failed"), executor.stage("payload.bin", b"bytes"):
        raise ValueError("body failed")
    with (
        pytest.raises(ExecutionUnavailableError, match="remove failed"),
        executor.stage("payload.bin", b"bytes"),
    ):
        pass
    executor.close()


def test_close_detaches_only_without_destroying_sandbox() -> None:
    factory = _Factory()
    executor = MicrosandboxExecutor("existing", _bindings=_bindings(factory))

    executor.close()
    executor.close()

    assert factory.sandbox.detached is True


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (_Errors.SandboxNotFoundError("missing"), ExecutionTargetNotFoundError),
        (_Errors.SandboxNotRunningError("stopped"), ExecutionUnavailableError),
        (_Errors.CloudHttpError("unreachable"), ExecutionConnectionError),
        (FileNotFoundError("multica"), ExecutableNotFoundError),
        (PermissionError("multica"), ExecutableNotRunnableError),
    ],
)
def test_provider_errors_use_execution_or_existing_executable_errors(
    error: Exception, expected: type[Exception]
) -> None:
    class BrokenFactory:
        @staticmethod
        async def get(name: str) -> _SandboxHandle:
            raise error

    with pytest.raises(expected):
        MicrosandboxExecutor(
            "existing",
            _bindings=_bindings(cast("type[_SandboxFactory]", BrokenFactory), _Errors),
        )


def test_missing_extra_guidance_is_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> object:
        raise ImportError(name)

    monkeypatch.setattr(importlib, "import_module", missing)

    with pytest.raises(ImportError) as error:
        MicrosandboxExecutor("existing")

    assert str(error.value) == (
        "Microsandbox execution requires the optional 'microsandbox' dependency. "
        'Install it with: pip install "multica-py[microsandbox]"'
    )


def test_executor_never_calls_asyncio_run_on_caller_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: object, **kwargs: object) -> object:
        raise AssertionError("asyncio.run must not be called")

    monkeypatch.setattr(asyncio, "run", fail)
    factory = _Factory()
    executor = MicrosandboxExecutor("existing", _bindings=_bindings(factory))

    assert executor.run(_request()).exit_code == 0
    executor.close()
