from __future__ import annotations

import datetime
import os
import sys
from collections import deque
from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import pytest

from multica_py._internal.transport import CliTransport
from multica_py.config import ClientConfig
from multica_py.exceptions import CommandExecutionError, ExecutableNotFoundError, MulticaError
from multica_py.execution import (
    CommandExecutor,
    ExecutionConnectionError,
    ExecutionError,
    ExecutionRequest,
    ExecutionResult,
    ExecutionTargetNotFoundError,
    ExecutionUnavailableError,
    LocalExecutor,
    ProcessHandle,
)
from multica_py.execution.microsandbox import MicrosandboxExecutor
from multica_py.execution.ssh import SshExecutor
from tests.unit.execution.test_microsandbox import _Event, _Factory, _factory_type, _Output
from tests.unit.execution.test_ssh import _Client as _SshClient
from tests.unit.execution.test_ssh import _Paramiko


@dataclass(frozen=True)
class ExecutorFactoryCase:
    id: str
    factory: Callable[[], _ConformanceRuntime]


@dataclass
class _ConformanceRuntime:
    executor: CommandExecutor
    run_request: ExecutionRequest
    run_result: ExecutionResult
    buffered_request: ExecutionRequest
    buffered_result: ExecutionResult
    streaming_request: ExecutionRequest
    streaming_stdout: list[str]
    staged_contains: Callable[[str, bytes], bool]
    staged_cleaned: Callable[[str], bool]
    closed: Callable[[], bool]
    missing_executable: Callable[[], object]


def _local_runtime() -> _ConformanceRuntime:
    cwd = os.fspath(Path.cwd())
    executor = LocalExecutor()
    return _ConformanceRuntime(
        executor=executor,
        run_request=ExecutionRequest(
            argv=(
                sys.executable,
                "-c",
                "import os,sys; sys.stdout.buffer.write(sys.stdin.buffer.read()+os.getcwd().encode()+b'|'+os.environb[b'EXECUTOR_CASE'])",
            ),
            cwd=cwd,
            environment=(("EXECUTOR_CASE", "explicit"),),
            stdin=b"stdin|",
            timeout=datetime.timedelta(seconds=2),
        ),
        run_result=ExecutionResult(0, b"stdin|" + os.fsencode(Path.cwd()) + b"|explicit", b""),
        buffered_request=ExecutionRequest(
            argv=(sys.executable, "-c", "import sys; print('out'); print('err', file=sys.stderr)")
        ),
        buffered_result=ExecutionResult(0, b"out\n", b"err\n"),
        streaming_request=ExecutionRequest(argv=(sys.executable, "-c", "print('out')")),
        streaming_stdout=["out\n"],
        staged_contains=lambda path, content: Path(path).read_bytes() == content,
        staged_cleaned=lambda path: not Path(path).exists(),
        closed=lambda: True,
        missing_executable=lambda: LocalExecutor().run(
            ExecutionRequest(argv=("multica-py-conformance-not-found",))
        ),
    )


def _microsandbox_runtime() -> _ConformanceRuntime:
    factory = _Factory()
    factory.sandbox.output = _Output(0, b"stdin|/target|explicit", b"")
    factory.sandbox.exec_handle.output = _Output(0, b"out\n", b"err\n")
    factory.sandbox.exec_handle.events = deque(
        [_Event("stdout", b"out\n"), _Event("stderr", b"err\n"), _Event("exited")]
    )
    executor = MicrosandboxExecutor("existing", _sandbox_factory=_factory_type(factory))

    missing_factory = _Factory()
    missing_factory.sandbox.run_error = FileNotFoundError("multica")

    def missing_executable() -> None:
        missing_executor = MicrosandboxExecutor(
            "existing", _sandbox_factory=_factory_type(missing_factory)
        )
        try:
            missing_executor.run(ExecutionRequest(argv=("multica",)))
        finally:
            missing_executor.close()

    return _ConformanceRuntime(
        executor=executor,
        run_request=ExecutionRequest(
            argv=("multica", "issue", "get", "MYL-42"),
            cwd="/target",
            environment=(("EXECUTOR_CASE", "explicit"),),
            stdin=b"stdin|",
            timeout=datetime.timedelta(seconds=2),
        ),
        run_result=ExecutionResult(0, b"stdin|/target|explicit", b""),
        buffered_request=ExecutionRequest(argv=("multica", "logs")),
        buffered_result=ExecutionResult(0, b"out\n", b"err\n"),
        streaming_request=ExecutionRequest(argv=("multica", "logs", "--follow")),
        streaming_stdout=["out\n"],
        staged_contains=lambda path, content: factory.sandbox.fs.files.get(path) == content,
        staged_cleaned=lambda path: path not in factory.sandbox.fs.files,
        closed=lambda: factory.sandbox.detached,
        missing_executable=missing_executable,
    )


def _ssh_runtime() -> _ConformanceRuntime:
    client = _SshClient()
    executor = SshExecutor(host="vps.example", username="root", _paramiko_module=_Paramiko(client))

    def missing_executable() -> None:
        missing_client = _SshClient(exec_error=FileNotFoundError("multica"))
        missing_executor = SshExecutor(
            host="vps.example", username="root", _paramiko_module=_Paramiko(missing_client)
        )
        try:
            missing_executor.run(ExecutionRequest(argv=("multica",)))
        finally:
            missing_executor.close()

    return _ConformanceRuntime(
        executor=executor,
        run_request=ExecutionRequest(
            argv=("multica", "issue", "get", "MYL-42"),
            cwd="/target",
            environment=(("EXECUTOR_CASE", "explicit"),),
            stdin=b"stdin|",
            timeout=datetime.timedelta(seconds=2),
        ),
        run_result=ExecutionResult(0, b"stdout", b"stderr"),
        buffered_request=ExecutionRequest(argv=("multica", "logs")),
        buffered_result=ExecutionResult(0, b"stdout", b"stderr"),
        streaming_request=ExecutionRequest(argv=("multica", "logs", "--follow")),
        streaming_stdout=["one\n"],
        staged_contains=lambda path, content: client.sftp.files.get(path) == content,
        staged_cleaned=lambda path: path not in client.sftp.files,
        closed=lambda: client.closed,
        missing_executable=missing_executable,
    )


_EXECUTORS = (
    ExecutorFactoryCase("local", _local_runtime),
    ExecutorFactoryCase("microsandbox", _microsandbox_runtime),
    ExecutorFactoryCase("ssh", _ssh_runtime),
)


def test_execution_errors_are_multica_errors_but_not_cli_errors() -> None:
    for error_type in (
        ExecutionError,
        ExecutionConnectionError,
        ExecutionTargetNotFoundError,
        ExecutionUnavailableError,
    ):
        assert issubclass(error_type, MulticaError)
        assert not issubclass(error_type, CommandExecutionError)


@pytest.mark.parametrize("case", _EXECUTORS, ids=lambda case: case.id)
def test_executor_conformance_run_maps_request_and_result(case: ExecutorFactoryCase) -> None:
    runtime = case.factory()
    try:
        assert runtime.executor.run(runtime.run_request) == runtime.run_result
    finally:
        runtime.executor.close()


@pytest.mark.parametrize("case", _EXECUTORS, ids=lambda case: case.id)
def test_executor_conformance_spawn_owns_output_once_and_has_opaque_identity(
    case: ExecutorFactoryCase,
) -> None:
    runtime = case.factory()
    try:
        handle = runtime.executor.spawn(runtime.buffered_request)
        assert isinstance(handle.id, (int, str, type(None)))
        assert handle.poll() is None or isinstance(handle.poll(), int)
        assert handle.collect() == runtime.buffered_result

        streaming = runtime.executor.spawn(runtime.streaming_request)
        assert list(streaming.stdout_lines()) == runtime.streaming_stdout
        with pytest.raises(RuntimeError):
            streaming.collect()
        assert streaming.wait() == 0
        streaming.close()
    finally:
        runtime.executor.close()


@pytest.mark.parametrize("case", _EXECUTORS, ids=lambda case: case.id)
def test_executor_conformance_staging_is_exact_and_cleaned(case: ExecutorFactoryCase) -> None:
    runtime = case.factory()
    content = b"exact\x00bytes"
    try:
        with runtime.executor.stage("payload.bin", content) as path:
            assert path.startswith("/")
            assert runtime.staged_contains(path, content)
        assert runtime.staged_cleaned(path)
    finally:
        runtime.executor.close()
    assert runtime.closed()


@pytest.mark.parametrize("case", _EXECUTORS, ids=lambda case: case.id)
def test_executor_conformance_maps_reachable_target_missing_executable(
    case: ExecutorFactoryCase,
) -> None:
    runtime = case.factory()
    try:
        with pytest.raises(ExecutableNotFoundError):
            runtime.missing_executable()
    finally:
        runtime.executor.close()


def test_local_executor_supports_context_manager_cleanup() -> None:
    with LocalExecutor() as executor:
        assert isinstance(executor, LocalExecutor)


def test_target_paths_use_fspath_without_controller_normalization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class CapturingExecutor:
        request: ExecutionRequest | None = None

        def run(self, request: ExecutionRequest) -> ExecutionResult:
            self.request = request
            return ExecutionResult(0, b"", b"")

        def spawn(self, request: ExecutionRequest) -> ProcessHandle:
            raise AssertionError(f"unexpected spawn: {request!r}")

        def stage(self, label: str, content: bytes) -> AbstractContextManager[str]:
            return nullcontext(f"/target/{label}")

        def close(self) -> None:
            return None

        def __enter__(self) -> CapturingExecutor:
            return self

        def __exit__(self, *args: object) -> None:
            self.close()

    monkeypatch.setattr(os, "name", "nt")
    config = ClientConfig(executable=PurePosixPath("/opt/multica"), cwd=PurePosixPath("/srv/app"))
    executor = CapturingExecutor()
    transport = CliTransport(config, executor=executor)

    assert config.executable == "/opt/multica"
    assert transport.build_full_argv(("version",)) == ("/opt/multica", "version")
    transport._execute(("version",), check_compat=False)
    assert executor.request is not None
    assert config.cwd is not None
    assert executor.request.cwd == os.fspath(config.cwd)


def test_local_executor_accepts_pathlike_target_paths() -> None:
    config = ClientConfig(executable=Path(sys.executable), cwd=Path.cwd())
    result = LocalExecutor().run(
        ExecutionRequest(
            argv=(os.fspath(config.executable), "-c", "print('ok')"),
            cwd=os.fspath(config.cwd) if config.cwd is not None else None,
        )
    )

    assert result.stdout == b"ok\n"
