from __future__ import annotations

import datetime
import importlib
import stat
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

import pytest

import multica_py.execution.ssh as ssh_module
from multica_py.exceptions import ExecutableNotFoundError, ExecutableNotRunnableError
from multica_py.execution import (
    ExecutionConnectionError,
    ExecutionRequest,
    ExecutionResult,
    ExecutionTargetNotFoundError,
    ExecutionUnavailableError,
)
from multica_py.execution.ssh import SshExecutor, _serialize_ssh_command


@dataclass
class _Input:
    written: bytes = b""
    closed: bool = False

    def write(self, data: bytes) -> int:
        self.written += data
        return len(data)

    def flush(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


@dataclass
class _Channel:
    exit_code: int = 0
    closed: bool = False

    def recv_exit_status(self) -> int:
        return self.exit_code

    def exit_status_ready(self) -> bool:
        return False

    def close(self) -> None:
        self.closed = True

    def settimeout(self, timeout: float | None) -> None:
        return None


@dataclass
class _Output:
    data: bytes
    channel: _Channel
    lines: deque[bytes] = field(default_factory=deque)

    def read(self) -> bytes:
        return self.data

    def __iter__(self) -> _Output:
        return self

    def __next__(self) -> bytes:
        if not self.lines:
            raise StopIteration
        return self.lines.popleft()


@dataclass
class _RemoteFile:
    files: dict[str, bytes]
    path: str
    contents: bytes = b""
    closed: bool = False
    read_only: bool = False
    write_error: Exception | None = None
    write_partial: int | None = None
    close_error: Exception | None = None

    def write(self, data: bytes) -> int:
        self.contents += data if self.write_partial is None else data[: self.write_partial]
        self.files[self.path] = self.contents
        if self.write_error is not None:
            raise self.write_error
        return len(data)

    def read(self) -> bytes:
        return self.files[self.path]

    def close(self) -> None:
        self.closed = True
        if not self.read_only:
            self.files[self.path] = self.contents
        if self.close_error is not None:
            raise self.close_error


@dataclass
class _Sftp:
    files: dict[str, bytes] = field(default_factory=dict)
    written: dict[str, bytes] = field(default_factory=dict)
    removed: list[str] = field(default_factory=list)
    modes: dict[str, int] = field(default_factory=dict)
    closed: bool = False
    open_error: Exception | None = None
    write_error: Exception | None = None
    write_partial: int | None = None
    close_error: Exception | None = None
    chmod_error: Exception | None = None

    def open(self, path: str, mode: str) -> _RemoteFile:
        assert mode in {"wb", "rb"}
        if self.open_error is not None:
            raise self.open_error
        return _RemoteFile(
            self.files,
            path,
            read_only=mode == "rb",
            write_error=self.write_error,
            write_partial=self.write_partial,
            close_error=self.close_error,
        )

    def remove(self, path: str) -> None:
        self.removed.append(path)
        if path in self.files:
            self.written[path] = self.files[path]
        self.files.pop(path, None)

    def chmod(self, path: str, mode: int) -> None:
        self.modes[path] = mode
        if self.chmod_error is not None:
            raise self.chmod_error

    def rmdir(self, path: str) -> None:
        self.removed.append(path)

    def lstat(self, path: str) -> object:
        return type("Stat", (), {"st_mode": stat.S_IFREG})()

    def listdir(self, path: str) -> list[str]:
        prefix = f"{path}/"
        return [
            file_path.removeprefix(prefix)
            for file_path in self.files
            if file_path.startswith(prefix)
        ]

    def close(self) -> None:
        self.closed = True


@dataclass(frozen=True)
class _StageEntryFailureCase:
    id: str
    configure: Callable[[_Sftp], None]
    expected_error: str
    expected_written: bytes


def _configure_open_failure(sftp: _Sftp) -> None:
    sftp.open_error = RuntimeError("open failed")


def _configure_partial_write_failure(sftp: _Sftp) -> None:
    sftp.write_error = RuntimeError("write failed")
    sftp.write_partial = 4


def _configure_close_failure(sftp: _Sftp) -> None:
    sftp.close_error = RuntimeError("close failed")


def _configure_chmod_failure(sftp: _Sftp) -> None:
    sftp.chmod_error = RuntimeError("chmod failed")


_STAGE_ENTRY_FAILURE_CASES: tuple[_StageEntryFailureCase, ...] = (
    _StageEntryFailureCase("open", _configure_open_failure, "open failed", b""),
    _StageEntryFailureCase(
        "partial-write", _configure_partial_write_failure, "write failed", b"secr"
    ),
    _StageEntryFailureCase("close", _configure_close_failure, "close failed", b"secret-bytes"),
    _StageEntryFailureCase("chmod", _configure_chmod_failure, "chmod failed", b"secret-bytes"),
)


@dataclass
class _Client:
    stdin: _Input = field(default_factory=_Input)
    channel: _Channel = field(default_factory=_Channel)
    calls: list[tuple[str, float | None, bool]] = field(default_factory=list)
    host_keys_loaded: bool = False
    policy: object | None = None
    connect_args: dict[str, object] = field(default_factory=dict)
    closed: bool = False
    sftp: _Sftp = field(default_factory=_Sftp)
    error: Exception | None = None
    exec_error: Exception | None = None
    sftp_error: Exception | None = None
    exec_exit_code: int | None = None

    def load_system_host_keys(self) -> None:
        self.host_keys_loaded = True

    def set_missing_host_key_policy(self, policy: object) -> None:
        self.policy = policy

    def connect(self, **kwargs: object) -> None:
        self.connect_args = kwargs
        if self.error is not None:
            raise self.error

    def exec_command(
        self, command: str, *, timeout: float | None, get_pty: bool
    ) -> tuple[_Input, _Output, _Output]:
        self.calls.append((command, timeout, get_pty))
        if self.exec_error is not None:
            raise self.exec_error
        if command in {
            "mktemp /tmp/multica-py.XXXXXXXX",
            "mktemp -d /tmp/multica-py-output.XXXXXXXX",
        }:
            self.channel.exit_code = 0
            return self.stdin, _Output(b"/tmp/staged\n", self.channel), _Output(b"", self.channel)
        if self.exec_exit_code is not None:
            self.channel.exit_code = self.exec_exit_code
        return (
            self.stdin,
            _Output(b"stdout", self.channel, deque([b"one\n"])),
            _Output(b"stderr", self.channel, deque([b"two\n"])),
        )

    def open_sftp(self) -> _Sftp:
        if self.sftp_error is not None:
            raise self.sftp_error
        return self.sftp

    def close(self) -> None:
        self.closed = True


@dataclass
class _Paramiko:
    client: _Client

    class RejectPolicy: ...

    class AutoAddPolicy: ...

    class BadHostKeyException(Exception): ...

    class NoValidConnectionsError(Exception): ...

    class AuthenticationException(Exception): ...

    class SSHException(Exception): ...

    class ChannelException(Exception): ...

    def SSHClient(self) -> _Client:
        return self.client


def _request() -> ExecutionRequest:
    return ExecutionRequest(
        argv=("multica", "issue", "get", "MYL-42"),
        cwd="/srv/multica path",
        environment=(("MULTICA_TOKEN", "target only"),),
        stdin=b"request",
        timeout=datetime.timedelta(seconds=2),
    )


def _executor(
    client: _Client | None = None, *, allow_unknown_host_key: bool = False
) -> tuple[SshExecutor, _Client]:
    fake = client or _Client()
    executor = SshExecutor(
        host="vps.example",
        username="root",
        _paramiko_module=_Paramiko(fake),
        allow_unknown_host_key=allow_unknown_host_key,
    )
    return executor, fake


def test_connects_with_safe_host_key_verification_and_maps_run() -> None:
    executor, client = _executor()

    assert executor.run(_request()) == ExecutionResult(0, b"stdout", b"stderr")
    assert client.host_keys_loaded is True
    assert type(client.policy).__name__ == "RejectPolicy"
    assert client.connect_args == {
        "hostname": "vps.example",
        "port": 22,
        "username": "root",
        "password": None,
        "key_filename": None,
        "passphrase": None,
        "pkey": None,
        "allow_agent": True,
        "look_for_keys": True,
        "timeout": None,
        "disabled_algorithms": {"keys": ["ssh-rsa"], "pubkeys": ["ssh-rsa"]},
    }
    assert client.calls == [
        (
            "cd '/srv/multica path' && MULTICA_TOKEN='target only' multica issue get MYL-42",
            2.0,
            False,
        )
    ]
    assert client.stdin.written == b"request"
    assert client.stdin.closed is True
    executor.close()
    assert client.closed is True


def test_unknown_host_acceptance_requires_explicit_opt_in() -> None:
    executor, client = _executor(allow_unknown_host_key=True)

    assert type(client.policy).__name__ == "AutoAddPolicy"
    executor.close()


def test_connect_failure_closes_the_created_ssh_session() -> None:
    client = _Client(error=type("AuthenticationException", (Exception,), {})("denied"))

    with pytest.raises(ExecutionConnectionError):
        _executor(client)

    assert client.closed is True


@pytest.mark.parametrize("error", [FileNotFoundError("key"), PermissionError("key")])
def test_controller_connection_filesystem_errors_are_not_executable_errors(
    error: Exception,
) -> None:
    client = _Client(error=error)
    with pytest.raises(ExecutionConnectionError):
        _executor(client)


def test_controller_environment_is_not_serialized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "controller-secret")
    executor, client = _executor()

    executor.run(ExecutionRequest(argv=("multica", "version")))

    assert client.calls == [("multica version", None, False)]
    executor.close()


def test_spawn_collect_streaming_and_channel_close_are_best_effort() -> None:
    executor, client = _executor()

    buffered = executor.spawn(_request())
    assert buffered.id is None
    assert buffered.collect() == ExecutionResult(0, b"stdout", b"stderr")

    streaming = executor.spawn(_request())
    assert list(streaming.stdout_lines()) == ["one\n"]
    assert list(streaming.stderr_lines()) == ["two\n"]
    with pytest.raises(RuntimeError):
        streaming.collect()
    streaming.terminate()
    assert client.channel.closed is True
    executor.close()


def test_wait_timeout_polls_without_busy_spinning(monkeypatch: pytest.MonkeyPatch) -> None:
    now = [0.0]
    waits: list[float] = []

    def monotonic() -> float:
        return now[0]

    def sleep(seconds: float) -> None:
        waits.append(seconds)
        now[0] += seconds

    monkeypatch.setattr(ssh_module, "_monotonic", monotonic)
    monkeypatch.setattr(ssh_module, "_sleep", sleep)
    executor, client = _executor()

    with pytest.raises(TimeoutError, match="channel was closed"):
        executor.spawn(_request()).wait(datetime.timedelta(seconds=0.02))

    assert waits == [0.01, 0.01]
    assert client.channel.closed is True
    executor.close()


@pytest.mark.parametrize(
    ("exit_code", "expected"),
    [(127, ExecutableNotFoundError), (126, ExecutableNotRunnableError)],
)
def test_posix_executable_exit_statuses_are_mapped_before_cli_classification(
    exit_code: int, expected: type[Exception]
) -> None:
    request = ExecutionRequest(argv=("multica", "version"))
    run_client = _Client(channel=_Channel(exit_code=exit_code))
    executor, _ = _executor(run_client)
    with pytest.raises(expected):
        executor.run(request)
    executor.close()

    spawn_client = _Client(channel=_Channel(exit_code=exit_code))
    executor, _ = _executor(spawn_client)
    with pytest.raises(expected):
        executor.spawn(request).collect()
    executor.close()


def test_sftp_stage_writes_exact_bytes_and_cleans_up() -> None:
    executor, client = _executor()

    with executor.stage("payload.bin", b"exact\x00bytes") as path:
        assert path == "/tmp/staged"
        assert client.sftp.files[path] == b"exact\x00bytes"
        assert client.sftp.modes[path] == 0o600

    assert client.sftp.removed == ["/tmp/staged"]
    assert client.sftp.closed is True
    executor.close()


@pytest.mark.parametrize("case", _STAGE_ENTRY_FAILURE_CASES, ids=lambda case: case.id)
def test_sftp_stage_entry_failures_cleanup_once_and_preserve_primary_error(
    case: _StageEntryFailureCase,
) -> None:
    client = _Client()
    case.configure(client.sftp)
    executor, _ = _executor(client)
    payload = b"secret-bytes"

    with (
        pytest.raises(RuntimeError, match=case.expected_error),
        executor.stage("payload.bin", payload),
    ):
        pass

    path = "/tmp/staged"
    assert client.sftp.removed == [path]
    assert client.sftp.files == {}
    assert client.sftp.written.get(path, b"") == case.expected_written
    executor.close()


def test_capture_output_rejects_traversal_and_symlink(monkeypatch: pytest.MonkeyPatch) -> None:
    executor, client = _executor()
    with executor.capture_output("download") as artifact:
        with pytest.raises(ValueError):
            artifact.read("../outside")
        monkeypatch.setattr(
            client.sftp,
            "lstat",
            lambda _path: type("Stat", (), {"st_mode": stat.S_IFLNK})(),
        )
        with pytest.raises(ValueError):
            artifact.read("result.bin")
    executor.close()


def test_capture_output_sftp_failure_happens_before_directory_creation() -> None:
    client = _Client(sftp_error=RuntimeError("sftp failed"))
    executor, _ = _executor(client)
    with pytest.raises(RuntimeError, match="sftp failed"), executor.capture_output("download"):
        pass
    assert client.calls == []
    executor.close()


def test_stage_preserves_body_exception_when_cleanup_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    executor, client = _executor()

    def cleanup_failure(path: str) -> None:
        raise RuntimeError("cleanup failed")

    monkeypatch.setattr(client.sftp, "remove", cleanup_failure)
    with pytest.raises(ValueError, match="body failed"), executor.stage("payload.bin", b"bytes"):
        raise ValueError("body failed")
    executor.close()


@pytest.mark.parametrize(
    ("cwd", "environment", "argv", "expected"),
    [
        (
            "/srv/a; rm -rf /",
            (("NAME", "$(whoami) `id`"),),
            ("tool", "a b", "'", "x\ny"),
            "cd '/srv/a; rm -rf /' && NAME='$(whoami) `id`' tool 'a b' ''\"'\"'' 'x\ny'",
        ),
        (
            "/路径 空间",
            (("UNICODE", "値"),),
            ("echo", "✓"),
            "cd '/路径 空间' && UNICODE='値' echo '✓'",
        ),
    ],
)
def test_serialize_ssh_command_quotes_every_component(
    cwd: str, environment: tuple[tuple[str, str], ...], argv: tuple[str, ...], expected: str
) -> None:
    assert _serialize_ssh_command(cwd, environment, argv) == expected


@pytest.mark.parametrize("environment", [(("BAD-NAME", "x"),), (("", "x"),), (("1NAME", "x"),)])
def test_serialize_ssh_command_rejects_invalid_environment_names(
    environment: tuple[tuple[str, str], ...],
) -> None:
    with pytest.raises(ValueError, match="Invalid environment variable name"):
        _serialize_ssh_command(None, environment, ("multica",))


def test_serialize_ssh_command_rejects_empty_argv_and_cwd() -> None:
    with pytest.raises(ValueError, match="argv must not be empty"):
        _serialize_ssh_command(None, (), ())
    with pytest.raises(ValueError, match="cwd must not be empty"):
        _serialize_ssh_command("", (), ("multica",))


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (_Paramiko.BadHostKeyException("changed"), ExecutionConnectionError),
        (_Paramiko.NoValidConnectionsError("refused"), ExecutionConnectionError),
        (_Paramiko.AuthenticationException("denied"), ExecutionConnectionError),
        (_Paramiko.SSHException("lost"), ExecutionUnavailableError),
        (_Paramiko.ChannelException("missing"), ExecutionTargetNotFoundError),
    ],
)
def test_provider_errors_are_mapped(error: Exception, expected: type[Exception]) -> None:
    client = _Client(error=error)
    with pytest.raises(expected):
        _executor(client)


def test_missing_extra_guidance_is_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> object:
        raise ImportError(name)

    monkeypatch.setattr(importlib, "import_module", missing)
    with pytest.raises(ImportError) as error:
        SshExecutor(host="vps.example")

    assert str(error.value) == (
        "SSH execution requires the optional 'paramiko' dependency. "
        'Install it with: pip install "multica-py[vps]"'
    )
