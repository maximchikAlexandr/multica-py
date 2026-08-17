from __future__ import annotations

import contextlib
import datetime
import importlib
import re
import shlex
import time
from collections.abc import Iterator, Sequence
from typing import Protocol, cast

from multica_py.exceptions import ExecutableNotFoundError, ExecutableNotRunnableError
from multica_py.execution.base import (
    ExecutionConnectionError,
    ExecutionError,
    ExecutionRequest,
    ExecutionResult,
    ExecutionTargetNotFoundError,
    ExecutionUnavailableError,
)

_ENVIRONMENT_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_STAGING_COMMAND = "mktemp /tmp/multica-py.XXXXXXXX"
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

    def close(self) -> None: ...


class _Sftp(Protocol):
    def open(self, path: str, mode: str = "r") -> _RemoteFile: ...

    def remove(self, path: str) -> None: ...

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
    ) -> None:
        self._executor = executor
        self._argv = argv
        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr
        self._channel = stdout.channel
        self._exit_code: int | None = None
        self._output_mode: str | None = None

    @property
    def id(self) -> None:
        return None

    def poll(self) -> int | None:
        if self._exit_code is None and self._channel.exit_status_ready():
            self._exit_code = self._channel.recv_exit_status()
        return self._exit_code

    def wait(self, timeout: datetime.timedelta | None = None) -> int:
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
        self._claim_output("buffered")
        try:
            self._channel.settimeout(_seconds(timeout))
            stdout = self._stdout.read()
            stderr = self._stderr.read()
            self._exit_code = self._channel.recv_exit_status()
            return self._executor._result_or_executable_error(
                ExecutionResult(self._exit_code, stdout, stderr), self._argv
            )
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
        self._claim_output("streaming")
        yield from (line.decode("utf-8") for line in self._stdout)

    def stderr_lines(self) -> Iterator[str]:
        self._claim_output("streaming")
        yield from (line.decode("utf-8") for line in self._stderr)

    def close(self) -> None:
        self._stdin.close()
        self._channel.close()

    def _claim_output(self, mode: str) -> None:
        if self._output_mode is None:
            self._output_mode = mode
        elif self._output_mode != mode:
            raise RuntimeError("Process output is already owned by another consumer")


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
            return _SshProcessHandle(self, request.argv, stdin, stdout, stderr)
        except Exception as error:
            raise self._map_error(error) from error

    @contextlib.contextmanager
    def stage(self, label: str, content: bytes) -> Iterator[str]:
        sftp: _Sftp | None = None
        path: str | None = None
        body_error: BaseException | None = None
        try:
            path = self._new_staging_path()
            sftp = self._client.open_sftp()
            remote = sftp.open(path, "wb")
            try:
                remote.write(content)
            finally:
                remote.close()
            yield path
        except BaseException as error:
            body_error = error
            raise
        finally:
            if sftp is not None:
                try:
                    if path is not None:
                        sftp.remove(path)
                except Exception:
                    if body_error is None:
                        raise
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

    def _new_staging_path(self) -> str:
        try:
            stdin, stdout, stderr = self._client.exec_command(
                _STAGING_COMMAND, timeout=None, get_pty=False
            )
            stdin.close()
            path = stdout.read().decode("utf-8").strip()
            error = stderr.read().decode("utf-8")
        except Exception as error:
            raise self._map_error(error) from error
        if stdout.channel.recv_exit_status() != 0 or not path:
            raise ExecutionUnavailableError(error or "SSH target could not create a staging path")
        return path

    @staticmethod
    def _result_or_executable_error(
        result: ExecutionResult, argv: tuple[str, ...]
    ) -> ExecutionResult:
        if result.exit_code == 127:
            raise ExecutableNotFoundError(f"Executable not found: {argv[0]}")
        if result.exit_code == 126:
            raise ExecutableNotRunnableError(f"Executable not runnable: {argv[0]}")
        return result

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
        if type(error).__name__ == "gaierror":
            return ExecutionTargetNotFoundError(str(error))
        name = type(error).__name__
        if name in {"BadHostKeyException", "NoValidConnectionsError", "AuthenticationException"}:
            return ExecutionConnectionError(str(error))
        if name in {"HostNotFoundError", "ChannelException"}:
            return ExecutionTargetNotFoundError(str(error))
        if name in {"SSHException", "EOFError"}:
            return ExecutionUnavailableError(str(error))
        return ExecutionConnectionError(str(error))
