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
from multica_py.enums import CompatibilityPolicy
from multica_py.exceptions import (
    CommandExecutionError,
    ExecutableNotFoundError,
    MulticaError,
    NetworkError,
)
from multica_py.execution import (
    CommandExecutor,
    ExecutionConnectionError,
    ExecutionError,
    ExecutionRequest,
    ExecutionResult,
    ExecutionTargetNotFoundError,
    ExecutionUnavailableError,
    LocalExecutor,
    OutputArtifact,
    ProcessHandle,
)
from multica_py.execution.microsandbox import MicrosandboxExecutor
from multica_py.execution.ssh import SshExecutor
from tests.unit.execution.test_microsandbox import _bindings, _Event, _Factory, _Output
from tests.unit.execution.test_ssh import _Client as _SshClient
from tests.unit.execution.test_ssh import _Paramiko
from tests.unit.resources.execution_cases import (
    PROCESS_FILE_SECRET_CASES,
    REMOTE_FILE_SECRET_CASES,
    ProcessFileSecretCase,
    RemoteFileSecretCase,
    file_secret_args,
)


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
    write_output: Callable[[str, bytes], object]
    assert_spawn_request: Callable[[CommandExecutor], None]


class _RecordingExecutor:
    def __init__(self, inner: CommandExecutor) -> None:
        self.inner = inner
        self.requests: list[ExecutionRequest] = []

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        self.requests.append(request)
        return self.inner.run(request)

    def spawn(self, request: ExecutionRequest) -> ProcessHandle:
        self.requests.append(request)
        return self.inner.spawn(request)

    def stage(self, label: str, content: bytes) -> AbstractContextManager[str]:
        return self.inner.stage(label, content)

    def capture_output(self, label: str) -> AbstractContextManager[OutputArtifact]:
        return self.inner.capture_output(label)

    def close(self) -> None:
        self.inner.close()

    def __enter__(self) -> _RecordingExecutor:
        self.inner.__enter__()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


@dataclass(frozen=True)
class _RemoteStagingObservation:
    executor: _RecordingExecutor
    current_files: Callable[[], dict[str, bytes]]
    written_files: Callable[[], dict[str, bytes]]
    removed_paths: Callable[[], list[str]]


@dataclass(frozen=True)
class RemoteStageFailureCase:
    id: str
    file_secret: ProcessFileSecretCase
    factory: Callable[[], _RemoteStagingObservation]
    expected_error: type[Exception]
    error_match: str
    expected_written: bytes


def _assert_local_spawn_request(executor: CommandExecutor) -> None:
    timed = executor.spawn(
        ExecutionRequest(
            argv=(
                sys.executable,
                "-c",
                "import sys,time; sys.stdout.buffer.write(sys.stdin.buffer.read()); time.sleep(1)",
            ),
            stdin=b"exact\x00stdin",
            timeout=datetime.timedelta(milliseconds=1),
        )
    )
    with pytest.raises(TimeoutError):
        timed.collect()
    timed.kill()
    assert timed.wait(datetime.timedelta(seconds=3)) != 0
    timed.close()


def _local_runtime() -> _ConformanceRuntime:
    cwd = os.fspath(Path.cwd())

    class TrackingLocalExecutor(LocalExecutor):
        closed = False

        def close(self) -> None:
            self.closed = True

    executor = TrackingLocalExecutor()
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
        closed=lambda: executor.closed,
        missing_executable=lambda: LocalExecutor().run(
            ExecutionRequest(argv=("multica-py-conformance-not-found",))
        ),
        write_output=lambda path, content: Path(path).write_bytes(content),
        assert_spawn_request=_assert_local_spawn_request,
    )


def _microsandbox_runtime() -> _ConformanceRuntime:
    factory = _Factory()
    factory.sandbox.output = _Output(0, b"stdin|/target|explicit", b"")
    factory.sandbox.exec_handle.output = _Output(0, b"out\n", b"err\n")
    factory.sandbox.exec_handle.events = deque(
        [_Event("stdout", b"out\n"), _Event("stderr", b"err\n"), _Event("exited")]
    )
    executor = MicrosandboxExecutor("existing", _bindings=_bindings(factory))

    missing_factory = _Factory()
    missing_factory.sandbox.run_error = FileNotFoundError("multica")

    def missing_executable() -> None:
        missing_executor = MicrosandboxExecutor("existing", _bindings=_bindings(missing_factory))
        try:
            missing_executor.run(ExecutionRequest(argv=("multica",)))
        finally:
            missing_executor.close()

    def write_output(path: str, content: bytes) -> None:
        factory.sandbox.fs.files[path] = content

    def assert_spawn_request(executor: CommandExecutor) -> None:
        executor.spawn(
            ExecutionRequest(
                argv=("multica", "logs"),
                stdin=b"exact\x00stdin",
                timeout=datetime.timedelta(seconds=7),
            )
        )
        assert factory.sandbox.calls[-1] == (
            "exec_stream",
            ("multica", ["logs"], None, {}, 7.0, b"exact\x00stdin", False),
        )

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
        write_output=write_output,
        assert_spawn_request=assert_spawn_request,
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

    def write_output(path: str, content: bytes) -> None:
        client.sftp.files[path] = content

    def assert_spawn_request(executor: CommandExecutor) -> None:
        executor.spawn(
            ExecutionRequest(
                argv=("multica", "logs"),
                stdin=b"exact\x00stdin",
                timeout=datetime.timedelta(seconds=7),
            )
        )
        assert client.calls[-1] == ("multica logs", 7.0, False)
        assert client.stdin.written == b"exact\x00stdin"

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
        write_output=write_output,
        assert_spawn_request=assert_spawn_request,
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
        runtime.assert_spawn_request(runtime.executor)
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


def _ssh_remote_staging_factory(
    exit_code: int = 0,
    configure: Callable[[_SshClient], None] | None = None,
) -> _RemoteStagingObservation:
    client = _SshClient()
    client.exec_exit_code = exit_code
    if configure is not None:
        configure(client)
    inner = SshExecutor(host="vps.example", username="root", _paramiko_module=_Paramiko(client))
    executor = _RecordingExecutor(inner)
    return _RemoteStagingObservation(
        executor,
        lambda: dict(client.sftp.files),
        lambda: dict(client.sftp.written),
        lambda: list(client.sftp.removed),
    )


def _microsandbox_remote_staging_factory(
    exit_code: int = 0,
    configure: Callable[[_Factory], None] | None = None,
) -> _RemoteStagingObservation:
    factory = _Factory()
    factory.sandbox.output = _Output(exit_code, b"stdout", b"stderr")
    factory.sandbox.exec_handle.output = _Output(exit_code, b"stdout", b"stderr")
    if configure is not None:
        configure(factory)
    inner = MicrosandboxExecutor("existing", _bindings=_bindings(factory))
    executor = _RecordingExecutor(inner)
    return _RemoteStagingObservation(
        executor,
        lambda: dict(factory.sandbox.fs.files),
        lambda: dict(factory.sandbox.fs.written),
        lambda: list(factory.sandbox.fs.removed),
    )


_REMOTE_FACTORY_BY_PROVIDER: dict[str, Callable[[int], _RemoteStagingObservation]] = {
    "ssh": _ssh_remote_staging_factory,
    "microsandbox": _microsandbox_remote_staging_factory,
}


def _run_remote_success(
    observation: _RemoteStagingObservation,
    transport: CliTransport,
    args: tuple[str, ...],
) -> str:
    transport.run_bytes(args)
    return observation.removed_paths()[0]


def _spawn_remote_success(
    observation: _RemoteStagingObservation,
    transport: CliTransport,
    args: tuple[str, ...],
) -> str:
    process = transport.spawn(args)
    staged_path = next(iter(observation.current_files()))
    assert process.result().exit_code == 0
    assert observation.current_files() == {}
    assert observation.removed_paths() == [staged_path]
    process.close()
    process.close()
    assert observation.removed_paths() == [staged_path]
    return staged_path


def _run_remote_nonzero(
    observation: _RemoteStagingObservation,
    transport: CliTransport,
    args: tuple[str, ...],
) -> str:
    with pytest.raises(NetworkError):
        transport.run_bytes(args)
    return observation.removed_paths()[0]


def _spawn_remote_nonzero(
    observation: _RemoteStagingObservation,
    transport: CliTransport,
    args: tuple[str, ...],
) -> str:
    process = transport.spawn(args)
    staged_path = next(iter(observation.current_files()))
    assert process.result().exit_code == 2
    assert observation.current_files() == {}
    assert observation.removed_paths() == [staged_path]
    process.close()
    process.close()
    assert observation.removed_paths() == [staged_path]
    return staged_path


def _execute_remote_case(
    case: RemoteFileSecretCase,
    observation: _RemoteStagingObservation,
    transport: CliTransport,
    args: tuple[str, ...],
) -> str:
    action = {
        "run-success": _run_remote_success,
        "spawn-success": _spawn_remote_success,
        "run-nonzero": _run_remote_nonzero,
        "spawn-nonzero": _spawn_remote_nonzero,
    }[case.phase]
    return action(observation, transport, args)


_PROCESS_FILE_SECRET_BY_ID = {case.id: case for case in PROCESS_FILE_SECRET_CASES}
_CREDENTIAL_FILE = _PROCESS_FILE_SECRET_BY_ID["credential-file"]
_SERVER_CONFIG_FILE = _PROCESS_FILE_SECRET_BY_ID["server-config-file"]
_CREDENTIAL_FILE_EQUALS = _PROCESS_FILE_SECRET_BY_ID["credential-file-equals"]
_SERVER_CONFIG_FILE_EQUALS = _PROCESS_FILE_SECRET_BY_ID["server-config-file-equals"]


def _ssh_open_failure_factory() -> _RemoteStagingObservation:
    def configure(client: _SshClient) -> None:
        client.sftp.open_error = RuntimeError("open failed")

    return _ssh_remote_staging_factory(configure=configure)


def _ssh_write_failure_factory() -> _RemoteStagingObservation:
    def configure(client: _SshClient) -> None:
        client.sftp.write_error = RuntimeError("write failed")
        client.sftp.write_partial = 4

    return _ssh_remote_staging_factory(configure=configure)


def _ssh_chmod_failure_factory() -> _RemoteStagingObservation:
    def configure(client: _SshClient) -> None:
        client.sftp.chmod_error = RuntimeError("chmod failed")

    return _ssh_remote_staging_factory(configure=configure)


def _microsandbox_write_failure_factory() -> _RemoteStagingObservation:
    def configure(factory: _Factory) -> None:
        factory.sandbox.fs.write_error = RuntimeError("write failed")
        factory.sandbox.fs.write_partial = b"part"

    return _microsandbox_remote_staging_factory(configure=configure)


_REMOTE_STAGE_FAILURE_CASES: tuple[RemoteStageFailureCase, ...] = (
    RemoteStageFailureCase(
        "ssh-open-failure",
        _CREDENTIAL_FILE,
        _ssh_open_failure_factory,
        RuntimeError,
        "open failed",
        b"",
    ),
    RemoteStageFailureCase(
        "ssh-write-failure",
        _CREDENTIAL_FILE,
        _ssh_write_failure_factory,
        RuntimeError,
        "write failed",
        _CREDENTIAL_FILE.payload[:4],
    ),
    RemoteStageFailureCase(
        "ssh-chmod-failure",
        _SERVER_CONFIG_FILE,
        _ssh_chmod_failure_factory,
        RuntimeError,
        "chmod failed",
        _SERVER_CONFIG_FILE.payload,
    ),
    RemoteStageFailureCase(
        "microsandbox-write-failure",
        _CREDENTIAL_FILE,
        _microsandbox_write_failure_factory,
        ExecutionUnavailableError,
        "write failed",
        b"part",
    ),
)


@pytest.mark.parametrize("case", REMOTE_FILE_SECRET_CASES, ids=lambda case: case.id)
def test_cli_transport_stages_file_secrets_on_remote_targets(
    tmp_path: Path,
    case: RemoteFileSecretCase,
) -> None:
    observation = _REMOTE_FACTORY_BY_PROVIDER[case.provider](case.expected_exit_code)
    source = tmp_path / f"{case.file_secret.id}.bin"
    source.write_bytes(case.file_secret.payload)
    args = (
        "workspace",
        "mcp",
        "add",
        "server-1",
        *file_secret_args(case.file_secret, source),
    )
    transport = CliTransport(
        ClientConfig(executable="multica", compatibility=CompatibilityPolicy.ignore),
        executor=observation.executor,
    )
    try:
        staged_path = _execute_remote_case(case, observation, transport, args)
        assert observation.executor.requests[0].argv == case.expected_argv(
            staged_path, case.file_secret
        )
        assert observation.written_files() == {staged_path: case.file_secret.payload}
        assert len(observation.current_files()) == case.expected_current_files
        assert len(observation.removed_paths()) == case.expected_removed_paths
        assert observation.removed_paths() == [staged_path] * case.expected_removed_paths
    finally:
        observation.executor.close()


@pytest.mark.parametrize("case", _REMOTE_STAGE_FAILURE_CASES, ids=lambda case: case.id)
def test_cli_transport_cleans_remote_file_staging_on_staging_failure(
    tmp_path: Path,
    case: RemoteStageFailureCase,
) -> None:
    observation = case.factory()
    source = tmp_path / f"{case.file_secret.id}-failure.bin"
    source.write_bytes(case.file_secret.payload)
    args = (
        "workspace",
        "mcp",
        "add",
        "server-1",
        *file_secret_args(case.file_secret, source),
    )
    transport = CliTransport(
        ClientConfig(executable="multica", compatibility=CompatibilityPolicy.ignore),
        executor=observation.executor,
    )
    try:
        with pytest.raises(case.expected_error, match=case.error_match):
            transport.run_bytes(args)
        staged_path = observation.removed_paths()[0]
        assert observation.current_files() == {}
        assert observation.removed_paths() == [staged_path]
        assert observation.written_files().get(staged_path, b"") == case.expected_written
    finally:
        observation.executor.close()


@pytest.mark.parametrize("case", _EXECUTORS, ids=lambda case: case.id)
def test_executor_conformance_captures_sdk_owned_output(case: ExecutorFactoryCase) -> None:
    runtime = case.factory()
    try:
        with runtime.executor.capture_output("download") as artifact:
            output_path = f"{artifact.path}/result.bin"
            runtime.write_output(output_path, b"exact\x00bytes")
            assert artifact.read(output_path) == b"exact\x00bytes"
            with pytest.raises(ValueError):
                artifact.read("/outside/result.bin")
    finally:
        runtime.executor.close()


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

        def capture_output(self, label: str) -> AbstractContextManager[OutputArtifact]:
            raise AssertionError(f"unexpected output capture: {label}")

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
