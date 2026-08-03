from __future__ import annotations

import datetime
import io
import signal
import subprocess
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from multica_py._internal.processes import (
    CancellationToken,
    _child_pids,
    close_process_pipes,
    kill_process,
    run_with_timeout,
    terminate_process,
)
from multica_py.exceptions import CommandCancelledError, CommandTimeoutError
from multica_py.process import ManagedProcess


def _process(*, poll: int | None = None) -> MagicMock:
    process = MagicMock(spec=subprocess.Popen)
    process.pid = 42
    process.returncode = 0
    process.poll.return_value = poll
    process.stdin = MagicMock()
    process.stdout = MagicMock()
    process.stderr = MagicMock()
    return process


@dataclass(frozen=True)
class ChildPidCase:
    result: subprocess.CompletedProcess[str]
    expected: tuple[int, ...]


@dataclass(frozen=True)
class StreamCase:
    stream_name: str
    payload: bytes
    expected: list[str]


def test_cancellation_token_tracks_attached_process() -> None:
    token = CancellationToken()
    process = _process()
    token.attach(process)
    token.cancel()
    assert token.cancelled
    assert token.process is process


def test_close_process_pipes_closes_every_attached_pipe() -> None:
    process = _process()
    stdin = process.stdin
    close_process_pipes(process)
    stdin.close.assert_called_once_with()
    process.stdout.close.assert_called_once_with()
    process.stderr.close.assert_called_once_with()


@pytest.mark.parametrize(
    "case",
    (
        ChildPidCase(subprocess.CompletedProcess([], 0, "12\ninvalid\n34\n", ""), (12, 34)),
        ChildPidCase(subprocess.CompletedProcess([], 1, "", ""), ()),
        ChildPidCase(subprocess.CompletedProcess([], 2, "12\n", ""), ()),
    ),
)
def test_child_pids_handles_pgrep_results(case: ChildPidCase) -> None:
    with patch("multica_py._internal.processes.subprocess.run", return_value=case.result):
        assert _child_pids(42) == case.expected


def test_child_pids_treats_missing_pgrep_as_no_children() -> None:
    with patch("multica_py._internal.processes.subprocess.run", side_effect=OSError):
        assert _child_pids(42) == ()


def test_terminate_process_escalates_and_cleans_known_descendants() -> None:
    process = _process()
    process.poll.side_effect = (None, None, None)
    with (
        patch("multica_py._internal.processes._descendant_pids", return_value=(43,)),
        patch("multica_py._internal.processes._killpg") as kill_group,
        patch("multica_py._internal.processes.os.kill") as kill_pid,
        patch("multica_py._internal.processes.time.monotonic", side_effect=(0.0, 3.0)),
    ):
        terminate_process(process)
    assert kill_group.call_args_list[0].args == (process, signal.SIGTERM)
    assert kill_group.call_args_list[1].args == (process, signal.SIGKILL)
    kill_pid.assert_called_once_with(43, signal.SIGKILL)


def test_kill_process_ignores_an_exited_process() -> None:
    process = _process(poll=0)
    with patch("multica_py._internal.processes._killpg") as kill_group:
        kill_process(process)
    kill_group.assert_not_called()


def test_run_with_timeout_rejects_pre_cancelled_call_without_starting_process() -> None:
    token = CancellationToken()
    token.cancel()
    with (
        patch("multica_py._internal.processes.create_process") as create_process,
        pytest.raises(CommandCancelledError, match="cancelled"),
    ):
        run_with_timeout(("multica", "version"), cancel=token)
    create_process.assert_not_called()


def test_run_with_timeout_cancels_an_in_flight_process_and_cleans_up() -> None:
    token = CancellationToken()
    process = _process()
    stdin = process.stdin

    calls = 0

    def communicate(*, timeout: float) -> tuple[bytes, bytes]:
        nonlocal calls
        assert timeout == 0.1
        calls += 1
        if calls == 1:
            token.cancel()
            raise subprocess.TimeoutExpired(("multica", "version"), timeout)
        return b"", b""

    process.communicate.side_effect = communicate
    with (
        patch("multica_py._internal.processes.create_process", return_value=process),
        patch("multica_py._internal.processes.terminate_process") as terminate,
        pytest.raises(CommandCancelledError, match="cancelled"),
    ):
        run_with_timeout(("multica", "version"), cancel=token)
    terminate.assert_called_once_with(process)
    stdin.close.assert_called_once_with()
    process.stdout.close.assert_called_once_with()
    process.stderr.close.assert_called_once_with()


def test_run_with_timeout_times_out_an_in_flight_process_and_cleans_up() -> None:
    process = _process()
    stdin = process.stdin
    process.communicate.side_effect = (
        subprocess.TimeoutExpired(("multica", "version"), 0.1),
        (b"", b""),
    )
    with (
        patch("multica_py._internal.processes.create_process", return_value=process),
        patch("multica_py._internal.processes.terminate_process") as terminate,
        patch("multica_py._internal.processes.time.monotonic", side_effect=(0.0, 1.0)),
        pytest.raises(CommandTimeoutError, match="timed out"),
    ):
        run_with_timeout(("multica", "version"), timeout=datetime.timedelta(seconds=0.5))
    terminate.assert_called_once_with(process)
    stdin.close.assert_called_once_with()
    process.stdout.close.assert_called_once_with()
    process.stderr.close.assert_called_once_with()


def test_managed_process_wait_timeout_preserves_semaphore() -> None:
    process = _process()
    process.wait.side_effect = subprocess.TimeoutExpired(("multica",), 1)
    semaphore = MagicMock()
    managed = ManagedProcess(process, ("multica",), semaphore)
    with pytest.raises(TimeoutError, match="wait timed out"):
        managed.wait(datetime.timedelta(seconds=1))
    semaphore.release.assert_not_called()
    process.wait.side_effect = None
    process.poll.return_value = 0
    managed.close()


def test_managed_process_close_escalates_and_finalizes_once() -> None:
    process = _process()
    process.wait.side_effect = (subprocess.TimeoutExpired(("multica",), 3), 0)
    semaphore = MagicMock()
    managed = ManagedProcess(process, ("multica", "run"), semaphore)
    with (
        patch("multica_py.process.terminate_process") as terminate,
        patch("multica_py.process.kill_process") as kill,
        patch("multica_py.process.close_process_pipes") as close_pipes,
    ):
        managed.close()
        managed.close()
    terminate.assert_called_once_with(process)
    kill.assert_called_once_with(process)
    close_pipes.assert_called_once_with(process)
    semaphore.release.assert_called_once_with()


@pytest.mark.parametrize(
    "case",
    (
        StreamCase("stdout", b"one\ntwo\n", ["one", "two"]),
        StreamCase("stderr", b"warning\n", ["warning"]),
    ),
)
def test_managed_process_streams_decode_and_finalize(case: StreamCase) -> None:
    process = _process(poll=0)
    setattr(process, case.stream_name, io.BytesIO(case.payload))
    semaphore = MagicMock()
    managed = ManagedProcess(process, semaphore=semaphore)
    lines = managed.stdout_lines() if case.stream_name == "stdout" else managed.stderr_lines()
    assert list(lines) == case.expected
    semaphore.release.assert_called_once_with()
