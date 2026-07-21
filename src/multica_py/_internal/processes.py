from __future__ import annotations

import contextlib
import datetime
import os
import signal
import subprocess
import time
from typing import BinaryIO, cast

from multica_py.exceptions import CommandCancelledError, CommandTimeoutError


def _stdin_pipe(process: subprocess.Popen[bytes]) -> BinaryIO | None:
    return cast("BinaryIO | None", process.stdin)


def _stdout_pipe(process: subprocess.Popen[bytes]) -> BinaryIO | None:
    return cast("BinaryIO | None", process.stdout)


def _stderr_pipe(process: subprocess.Popen[bytes]) -> BinaryIO | None:
    return cast("BinaryIO | None", process.stderr)


class CancellationToken:
    def __init__(self) -> None:
        self._cancelled = False
        self._process: subprocess.Popen[bytes] | None = None

    def attach(self, process: subprocess.Popen[bytes]) -> None:
        self._process = process

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    @property
    def process(self) -> subprocess.Popen[bytes] | None:
        return self._process

    def cancel(self) -> None:
        self._cancelled = True


_TERMINATE_GRACE_SECONDS = 2.0


def close_process_pipes(process: subprocess.Popen[bytes]) -> None:
    """Close stdin/stdout/stderr pipes attached to *process*."""
    for pipe in (_stdin_pipe(process), _stdout_pipe(process), _stderr_pipe(process)):
        if pipe is not None:
            with contextlib.suppress(OSError):
                pipe.close()


def _child_pids(pid: int) -> tuple[int, ...]:
    """Return direct child PIDs of *pid* (best-effort via ``pgrep``)."""
    try:
        completed = subprocess.run(
            ["pgrep", "-P", str(pid)],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ()
    if completed.returncode not in (0, 1):
        return ()
    return tuple(int(line) for line in completed.stdout.splitlines() if line.strip().isdigit())


def _descendant_pids(pid: int) -> tuple[int, ...]:
    """Return all descendant PIDs of *pid* (depth-first, children before parents)."""
    descendants: list[int] = []
    for child_pid in _child_pids(pid):
        descendants.extend(_descendant_pids(child_pid))
        descendants.append(child_pid)
    return tuple(descendants)


def _killpg(process: subprocess.Popen[bytes], sig: int) -> None:
    """Signal a ``start_new_session`` process group and any descendants.

    ``os.killpg`` uses the session-leader pid as the process-group id. Descendants
    are collected before signaling so detached session children still receive
    an explicit signal when group delivery is incomplete.
    """
    pid = process.pid
    descendants = _descendant_pids(pid)
    with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
        os.killpg(pid, sig)
    for descendant_pid in reversed(descendants):
        with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
            os.kill(descendant_pid, sig)
    with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
        os.kill(pid, sig)


def create_process(
    argv: tuple[str, ...],
    *,
    stdout: int = subprocess.PIPE,
    stderr: int = subprocess.PIPE,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        list(argv),
        stdin=subprocess.PIPE,
        stdout=stdout,
        stderr=stderr,
        cwd=cwd,
        env=env,
        start_new_session=True,
    )


def terminate_process(process: subprocess.Popen[bytes]) -> None:
    """Terminate a process group with SIGTERM, escalating to SIGKILL if needed."""
    if process.poll() is not None:
        return
    descendants = _descendant_pids(process.pid)
    _killpg(process, signal.SIGTERM)
    deadline = time.monotonic() + _TERMINATE_GRACE_SECONDS
    while process.poll() is None and time.monotonic() < deadline:
        time.sleep(0.05)
    if process.poll() is None:
        _killpg(process, signal.SIGKILL)
    for descendant_pid in reversed(descendants):
        with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
            os.kill(descendant_pid, signal.SIGKILL)


def kill_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    _killpg(process, signal.SIGKILL)


def _communicate_until_exit(
    process: subprocess.Popen[bytes],
    *,
    poll_interval: float,
    timeout_deadline: float | None,
    cancel: CancellationToken | None,
) -> tuple[bytes, bytes, bool]:
    stdout_data = b""
    stderr_data = b""
    timeout_hit = False
    terminate_reason: str | None = None
    force_kill_at: float | None = None

    while True:
        try:
            stdout_data, stderr_data = process.communicate(timeout=poll_interval)
        except subprocess.TimeoutExpired:
            now = time.monotonic()
            cancel_hit = cancel is not None and cancel.cancelled
            timeout_due = timeout_deadline is not None and now >= timeout_deadline

            if terminate_reason is None and cancel_hit:
                terminate_reason = "cancel"
                terminate_process(process)
                force_kill_at = now + 2.0
                continue

            if terminate_reason is None and timeout_due:
                timeout_hit = True
                terminate_reason = "timeout"
                terminate_process(process)
                force_kill_at = now + 2.0
                continue

            if terminate_reason is not None and force_kill_at is not None and now >= force_kill_at:
                kill_process(process)
                force_kill_at = None
        else:
            return stdout_data, stderr_data, timeout_hit


def run_with_timeout(
    argv: tuple[str, ...],
    *,
    stdin: bytes | None = None,
    timeout: datetime.timedelta | None = None,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    cancel: CancellationToken | None = None,
) -> subprocess.CompletedProcess[bytes]:
    if cancel is not None and cancel.cancelled:
        raise CommandCancelledError("Command was cancelled")

    process = create_process(argv, cwd=cwd, env=env)

    if cancel is not None:
        cancel.attach(process)

    timeout_deadline = time.monotonic() + timeout.total_seconds() if timeout is not None else None

    try:
        stdin_pipe = _stdin_pipe(process)
        if stdin is not None and stdin_pipe is not None:
            stdin_pipe.write(stdin)
            stdin_pipe.close()
        stdout_data, stderr_data, timeout_hit = _communicate_until_exit(
            process,
            poll_interval=0.1,
            timeout_deadline=timeout_deadline,
            cancel=cancel,
        )
    finally:
        close_process_pipes(process)

    rc = process.returncode if process.returncode is not None else 0

    if cancel is not None and cancel.cancelled:
        raise CommandCancelledError("Command was cancelled")

    if timeout_hit:
        raise CommandTimeoutError(f"Command timed out after {timeout}")

    return subprocess.CompletedProcess(
        args=list(argv),
        returncode=rc,
        stdout=stdout_data or b"",
        stderr=stderr_data or b"",
    )
