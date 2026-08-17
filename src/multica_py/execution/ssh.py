from __future__ import annotations

import contextlib
import datetime
import importlib
import re
import shlex
import stat
import time
from collections.abc import Iterator, Sequence
from pathlib import PurePosixPath
from typing import Protocol, TypeGuard, cast

from multica_py.exceptions import ExecutableNotFoundError, ExecutableNotRunnableError
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

_ENVIRONMENT_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_STAGING_COMMAND = "mktemp /tmp/multica-py.XXXXXXXX"
_OUTPUT_DIRECTORY_COMMAND = "mktemp -d /tmp/multica-py-output.XXXXXXXX"
_DISABLED_ALGORITHMS: dict[str, list[str]] = {"keys": ["ssh-rsa"], "pubkeys": ["ssh-rsa"]}
_monotonic = time.monotonic
_sleep = time.sleep


class _Channel(Protocol):
    def exit_status_ready(self) -> bool: ...

    def recv_exit_status(self) -> int: ...

    def close(self) -> None: ...

    def settimeout(self, timeout: float | None) -> None: ...


class _Input(Protocol):
    def write(self, data: bytes) -> int: ...

    def flush(self) -> None: ...

    def close(self) -> None: ...


class _Output(Protocol):
    @property
    def channel(self) -> _Channel: ...

    def read(self) -> bytes: ...

    def __iter__(self) -> Iterator[bytes]: ...


class _RemoteFile(Protocol):
    def write(self, data: bytes) -> int: ...

    def read(self) -> bytes: ...

    def close(self) -> None: ...


class _Sftp(Protocol):
    def open(self, path: str, mode: str = "r") -> _RemoteFile: ...

    def remove(self, path: str) -> None: ...

    def rmdir(self, path: str) -> None: ...

    def lstat(self, path: str) -> object: ...

    def listdir(self, path: str) -> Sequence[str]: ...

    def close(self) -> None: ...


class _SshClient(Protocol):
    def load_system_host_keys(self) -> None: ...

    def set_missing_host_key_policy(self, policy: object) -> None: ...

    def connect(
        self,
        hostname: str,
        port: int = 22,
        username: str | None = None,
        password: str | None = None,
        pkey: object | None = None,
        key_filename: str | Sequence[str] | None = None,
        timeout: float | None = None,
        allow_agent: bool = True,
        look_for_keys: bool = True,
        passphrase: str | None = None,
        disabled_algorithms: dict[str, list[str]] | None = None,
    ) -> None: ...

    def exec_command(
        self, command: str, bufsize: int = -1, timeout: float | None = None, get_pty: bool = False
    ) -> tuple[_Input, _Output, _Output]: ...

    def open_sftp(self) -> _Sftp: ...

    def close(self) -> None: ...


class _Paramiko(Protocol):
    class RejectPolicy:
        def __init__(self) -> None: ...

    class AutoAddPolicy:
        def __init__(self) -> None: ...

    def SSHClient(self) -> _SshClient: ...


def _load_paramiko() -> _Paramiko:
    try:
        return cast("_Paramiko", importlib.import_module("paramiko"))
    except ImportError as error:
        raise ImportError(
            "SSH execution requires the optional 'paramiko' dependency. "
            'Install it with: pip install "multica-py[vps]"'
        ) from error


def _seconds(timeout: datetime.timedelta | None) -> float | None:
    return None if timeout is None else timeout.total_seconds()


def _serialize_ssh_command(
    cwd: str | None, environment: tuple[tuple[str, str], ...], argv: tuple[str, ...]
) -> str:
    """Render a POSIX-shell command without exposing any component to parsing."""
    if not argv:
        raise ValueError("argv must not be empty")
    prefix: list[str] = []
    if cwd is not None:
        if not cwd:
            raise ValueError("cwd must not be empty")
        prefix.extend(("cd", shlex.quote(cwd), "&&"))
    for name, value in environment:
        if _ENVIRONMENT_NAME.fullmatch(name) is None:
            raise ValueError(f"Invalid environment variable name: {name!r}")
        prefix.append(f"{name}={shlex.quote(value)}")
    prefix.append(shlex.join(argv))
    return " ".join(prefix)


class _SshProcessHandle:
    """SSH channel control only closes transport; it cannot guarantee remote termination."""

    def __init__(
        self,
        executor: SshExecutor,
        argv: tuple[str, ...],
        stdin: _Input,
        stdout: _Output,
        stderr: _Output,
        default_timeout: datetime.timedelta | None,
    ) -> None:
        self._executor = executor
        self._argv = argv
        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr
        self._channel = stdout.channel
        self._default_timeout = default_timeout
        self._exit_code: int | None = None
        self._output = OutputOwnership()

    @property
    def id(self) -> None:
        return None

    def poll(self) -> int | None:
        if self._exit_code is None and self._channel.exit_status_ready():
            self._exit_code = self._channel.recv_exit_status()
        return self._exit_code

    def wait(self, timeout: datetime.timedelta | None = None) -> int:
        timeout = timeout if timeout is not None else self._default_timeout
        if timeout is not None:
            deadline = _monotonic() + timeout.total_seconds()
            while not self._channel.exit_status_ready():
                remaining = deadline - _monotonic()
                if remaining <= 0:
                    self.close()
                    raise TimeoutError("SSH process wait timed out; channel was closed")
                _sleep(min(0.01, remaining))
        try:
            self._exit_code = self._channel.recv_exit_status()
        except TimeoutError as error:
            self.close()
            raise TimeoutError("SSH process wait timed out; channel was closed") from error
        except Exception as error:
            raise self._executor._map_error(error) from error
        else:
            return self._exit_code

    def collect(self, timeout: datetime.timedelta | None = None) -> ExecutionResult:
        self._output.claim("buffered")
        try:
            timeout = timeout if timeout is not None else self._default_timeout
            self._channel.settimeout(_seconds(timeout))
            stdout = self._stdout.read()
            stderr = self._stderr.read()
            self._exit_code = self._channel.recv_exit_status()
            return executable_result(ExecutionResult(self._exit_code, stdout, stderr), self._argv)
        except TimeoutError as error:
            self.close()
            raise TimeoutError("SSH process collection timed out; channel was closed") from error
        except Exception as error:
            raise self._executor._map_error(error) from error

    def terminate(self) -> None:
        """Close the SSH channel; the remote process may continue running."""
        self.close()

    def kill(self) -> None:
        """Close the SSH channel; this does not guarantee a remote signal or cleanup."""
        self.close()

    def stdout_lines(self) -> Iterator[str]:
        self._output.claim("streaming")
        yield from (line.decode("utf-8") for line in self._stdout)

    def stderr_lines(self) -> Iterator[str]:
        self._output.claim("streaming")
        yield from (line.decode("utf-8") for line in self._stderr)

    def close(self) -> None:
        self._stdin.close()
        self._channel.close()


class SshExecutor:
    """Run commands on an existing SSH host; close only the session it owns."""

    def __init__(
        self,
        host: str,
        *,
        username: str | None = None,
        port: int = 22,
        password: str | None = None,
        key_filename: str | Sequence[str] | None = None,
        passphrase: str | None = None,
        pkey: object | None = None,
        allow_agent: bool = True,
        look_for_keys: bool = True,
        allow_unknown_host_key: bool = False,
        connection_timeout: datetime.timedelta | None = None,
        _paramiko_module: object | None = None,
    ) -> None:
        self._closed = False
        client: _SshClient | None = None
        try:
            paramiko = (
                cast("_Paramiko", _paramiko_module)
                if _paramiko_module is not None
                else _load_paramiko()
            )
            self._provider_errors = _ProviderErrorTypes(paramiko)
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            policy = paramiko.AutoAddPolicy() if allow_unknown_host_key else paramiko.RejectPolicy()
            client.set_missing_host_key_policy(policy)
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                key_filename=key_filename,
                passphrase=passphrase,
                pkey=pkey,
                allow_agent=allow_agent,
                look_for_keys=look_for_keys,
                timeout=_seconds(connection_timeout),
                disabled_algorithms=_DISABLED_ALGORITHMS,
            )
        except Exception as error:
            if client is not None:
                client.close()
            raise self._map_error(error) from error
        self._client = client

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        handle = self.spawn(request)
        try:
            return handle.collect(request.timeout)
        finally:
            handle.close()

    def spawn(self, request: ExecutionRequest) -> _SshProcessHandle:
        try:
            stdin, stdout, stderr = self._client.exec_command(
                _serialize_ssh_command(request.cwd, request.environment, request.argv),
                timeout=_seconds(request.timeout),
                get_pty=False,
            )
            if request.stdin is not None:
                stdin.write(request.stdin)
                stdin.flush()
            stdin.close()
            return _SshProcessHandle(self, request.argv, stdin, stdout, stderr, request.timeout)
        except FileNotFoundError as error:
            # This path is reached only after a connected target accepts an exec request.
            raise ExecutableNotFoundError(f"Executable not found: {request.argv[0]}") from error
        except PermissionError as error:
            raise ExecutableNotRunnableError(
                f"Executable not runnable: {request.argv[0]}"
            ) from error
        except Exception as error:
            raise self._map_error(error) from error

    @contextlib.contextmanager
    def stage(self, label: str, content: bytes) -> Iterator[str]:
        sftp = self._client.open_sftp()
        try:
            path = self._new_target_path(_STAGING_COMMAND)
            remote = sftp.open(path, "wb")
            try:
                remote.write(content)
            finally:
                remote.close()
            with _cleanup_after(lambda: sftp.remove(path)):
                yield path
        finally:
            sftp.close()

    @contextlib.contextmanager
    def capture_output(self, label: str) -> Iterator[_SshOutputArtifact]:
        sftp = self._client.open_sftp()
        try:
            path = self._new_target_path(_OUTPUT_DIRECTORY_COMMAND)
            artifact = _SshOutputArtifact(sftp, path)
            with _cleanup_after(artifact.cleanup):
                yield artifact
        finally:
            sftp.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._client.close()

    def __enter__(self) -> SshExecutor:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _new_target_path(self, command: str) -> str:
        try:
            stdin, stdout, stderr = self._client.exec_command(command, timeout=None, get_pty=False)
            stdin.close()
            path = stdout.read().decode("utf-8").strip()
            error = stderr.read().decode("utf-8")
        except Exception as error:
            raise self._map_error(error) from error
        if stdout.channel.recv_exit_status() != 0 or not path:
            raise ExecutionUnavailableError(error or "SSH target could not create a staging path")
        return path

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
        if isinstance(error, (FileNotFoundError, PermissionError)):
            return ExecutionConnectionError(str(error))
        if isinstance(error, OSError) and error.errno is not None:
            return ExecutionTargetNotFoundError(str(error))
        if isinstance(error, self._provider_errors.connection):
            return ExecutionConnectionError(str(error))
        if isinstance(error, self._provider_errors.target):
            return ExecutionTargetNotFoundError(str(error))
        if isinstance(error, self._provider_errors.unavailable):
            return ExecutionUnavailableError(str(error))
        return ExecutionConnectionError(str(error))


class _ProviderErrorTypes:
    def __init__(self, module: object) -> None:
        self.connection = _types(
            module, "BadHostKeyException", "NoValidConnectionsError", "AuthenticationException"
        )
        self.target = _types(module, "ChannelException")
        self.unavailable = (*_types(module, "SSHException"), EOFError)


def _types(module: object, *names: str) -> tuple[type[Exception], ...]:
    result: list[type[Exception]] = []
    for name in names:
        value = cast("object", getattr(module, name, None))
        if _is_exception_type(value):
            result.append(value)
    return tuple(result)


def _is_exception_type(value: object) -> TypeGuard[type[Exception]]:
    return type(value) is type and issubclass(cast("type[object]", value), Exception)  # type: ignore[misc]


class _SshOutputArtifact:
    def __init__(self, sftp: _Sftp, path: str) -> None:
        self._sftp = sftp
        self.path = path

    def read(self, returned_path: str) -> bytes:
        path = _direct_child(self.path, returned_path)
        mode = cast("int", getattr(self._sftp.lstat(path), "st_mode"))
        if not stat.S_ISREG(mode):
            raise ValueError("downloaded path must be in the SDK-owned target output directory")
        remote = self._sftp.open(path, "rb")
        try:
            return remote.read()
        finally:
            remote.close()

    def cleanup(self) -> None:
        for name in self._sftp.listdir(self.path):
            self._sftp.remove(f"{self.path}/{name}")
        self._sftp.rmdir(self.path)


def _direct_child(root: str, returned_path: str) -> str:
    candidate = PurePosixPath(returned_path)
    root_path = PurePosixPath(root)
    path = candidate if candidate.is_absolute() else root_path / candidate
    if path.parent != root_path or path.name in {"", ".", ".."}:
        raise ValueError("downloaded path must be in the SDK-owned target output directory")
    return str(path)
