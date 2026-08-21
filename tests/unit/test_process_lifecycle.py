from __future__ import annotations

import datetime
import io
import signal
import subprocess
import warnings
from dataclasses import dataclass
from unittest.mock import MagicMock, call, patch

import msgspec
import pytest

import multica_py
from multica_py._internal.processes import (
    CancellationToken,
    _child_pids,
    close_process_pipes,
    kill_process,
    kill_process_immediate,
    run_with_timeout,
    terminate_process,
)
from multica_py.exceptions import (
    CommandCancelledError,
    CommandTimeoutError,
    EncodingError,
    MulticaError,
    ProcessOutputCaptureError,
    ProcessOutputModeError,
    ProcessTimeoutError,
)
from multica_py.execution.local import LocalProcessHandle
from multica_py.process import ManagedProcess, ProcessResult


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


@dataclass(frozen=True)
class ResultCase:
    exit_code: int
    stdout: bytes
    stderr: bytes
    ok: bool


@pytest.mark.parametrize(
    ("catch_type", "raised_type"),
    (
        (TimeoutError, ProcessTimeoutError),
        (CommandTimeoutError, ProcessTimeoutError),
        (MulticaError, ProcessTimeoutError),
        (MulticaError, ProcessOutputCaptureError),
    ),
    ids=(
        "process-timeout-as-timeout",
        "process-timeout-as-command-timeout",
        "process-timeout-as-multica",
        "output-capture-as-multica",
    ),
)
def test_spawn_path_errors_remain_catchable(
    catch_type: type[BaseException],
    raised_type: type[Exception],
) -> None:
    with pytest.raises(catch_type):
        raise raised_type("spawn failure")


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


def test_kill_process_immediate_skips_descendant_discovery() -> None:
    process = _process(poll=None)
    with (
        patch("multica_py._internal.processes._descendant_pids") as descendants,
        patch("multica_py._internal.processes._signal_process_group") as signal_group,
    ):
        kill_process_immediate(process)
    descendants.assert_not_called()
    signal_group.assert_called_once_with(process, signal.SIGKILL)


def test_kill_process_immediate_ignores_an_exited_process() -> None:
    process = _process(poll=0)
    with patch("multica_py._internal.processes._signal_process_group") as signal_group:
        kill_process_immediate(process)
    signal_group.assert_not_called()


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
    process.communicate.side_effect = subprocess.TimeoutExpired(("multica",), 1)
    semaphore = MagicMock()
    managed = ManagedProcess(LocalProcessHandle(process), ("multica",), semaphore)
    with pytest.raises(ProcessTimeoutError, match="wait timed out"):
        managed.wait(datetime.timedelta(seconds=1))
    semaphore.release.assert_not_called()
    process.communicate.side_effect = None
    process.poll.return_value = 0
    managed.close()


def test_managed_process_del_warns_and_kills_without_grace_for_live_process() -> None:
    process = _process(poll=None)
    semaphore = MagicMock()
    managed = ManagedProcess(LocalProcessHandle(process), ("multica", "run"), semaphore)
    with (
        patch("multica_py.execution.local.kill_process_immediate") as kill,
        patch("multica_py.execution.local.kill_process") as kill_full,
        patch("multica_py.execution.local.terminate_process") as terminate,
        patch("multica_py._internal.processes._descendant_pids") as descendants,
        patch("multica_py.execution.local.close_process_pipes") as close_pipes,
        pytest.warns(ResourceWarning, match="never closed"),
    ):
        managed.__del__()
    kill.assert_called_once_with(process)
    kill_full.assert_not_called()
    terminate.assert_not_called()
    descendants.assert_not_called()
    close_pipes.assert_called_once_with(process)
    semaphore.release.assert_called_once_with()


def test_managed_process_del_finalizes_quietly_for_exited_process() -> None:
    process = _process(poll=0)
    semaphore = MagicMock()
    managed = ManagedProcess(LocalProcessHandle(process), ("multica", "run"), semaphore)
    with (
        patch("multica_py.execution.local.kill_process_immediate") as kill,
        patch("multica_py.execution.local.terminate_process") as terminate,
        warnings.catch_warnings(),
    ):
        warnings.simplefilter("error")
        managed.__del__()
    kill.assert_not_called()
    terminate.assert_not_called()
    semaphore.release.assert_called_once_with()


def test_managed_process_del_skips_already_closed() -> None:
    process = _process(poll=0)
    semaphore = MagicMock()
    managed = ManagedProcess(LocalProcessHandle(process), semaphore=semaphore)
    managed.close()
    semaphore.reset_mock()
    managed.__del__()
    semaphore.release.assert_not_called()


def test_managed_process_close_escalates_and_finalizes_once() -> None:
    process = _process()
    process.wait.side_effect = (subprocess.TimeoutExpired(("multica",), 3), 0)
    semaphore = MagicMock()
    managed = ManagedProcess(LocalProcessHandle(process), ("multica", "run"), semaphore)
    with (
        patch("multica_py.execution.local.terminate_process") as terminate,
        patch("multica_py.execution.local.kill_process") as kill,
        patch("multica_py.execution.local.close_process_pipes") as close_pipes,
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
    managed = ManagedProcess(LocalProcessHandle(process), semaphore=semaphore)
    lines = managed.stdout_lines() if case.stream_name == "stdout" else managed.stderr_lines()
    assert list(lines) == case.expected
    semaphore.release.assert_called_once_with()


@pytest.mark.parametrize("stream_name", ("stdout", "stderr"))
def test_managed_process_stream_completion_finalizes_on_poll_once(stream_name: str) -> None:
    process = _process(poll=None)
    setattr(process, stream_name, io.BytesIO(b"line\n"))
    semaphore = MagicMock()
    cleanup = MagicMock()
    managed = ManagedProcess(LocalProcessHandle(process), semaphore=semaphore, cleanup=cleanup)

    lines = managed.stdout_lines() if stream_name == "stdout" else managed.stderr_lines()
    assert list(lines) == ["line"]

    cleanup.assert_not_called()
    semaphore.release.assert_not_called()
    process.poll.return_value = 0
    assert managed.poll() == 0
    cleanup.assert_called_once_with()
    semaphore.release.assert_called_once_with()
    assert managed.poll() == 0
    managed.close()
    cleanup.assert_called_once_with()
    semaphore.release.assert_called_once_with()


@pytest.mark.parametrize("stream_name", ("stdout", "stderr"))
def test_managed_process_poll_preserves_active_stream_output(stream_name: str) -> None:
    process = _process(poll=None)
    setattr(process, stream_name, io.BytesIO(b"first\nremaining\n"))
    semaphore = MagicMock()
    cleanup = MagicMock()
    managed = ManagedProcess(LocalProcessHandle(process), semaphore=semaphore, cleanup=cleanup)
    stream = managed.stdout_lines() if stream_name == "stdout" else managed.stderr_lines()

    assert next(stream) == "first"
    process.poll.return_value = 0
    assert managed.poll() == 0
    assert not managed._closed
    assert next(stream) == "remaining"
    with pytest.raises(StopIteration):
        next(stream)
    cleanup.assert_called_once_with()
    semaphore.release.assert_called_once_with()


def test_process_result_is_frozen_and_closed_with_status_properties() -> None:
    result = ProcessResult(
        ("multica", "version"),
        0,
        "Multica 1.0\n",
        "",
    )

    assert ProcessResult.__struct_fields__ == ("argv", "exit_code", "stdout", "stderr")
    assert multica_py.ProcessResult is ProcessResult
    assert result.ok
    assert not result.failed
    with pytest.raises((AttributeError, TypeError)):
        setattr(result, "exit_code", 1)
    with pytest.raises(msgspec.ValidationError):
        msgspec.json.decode(
            b'{"argv":["multica"],"exit_code":0,"stdout":"","stderr":"","extra":"value"}',
            type=ProcessResult,
        )


def test_process_output_mode_error_identifies_current_and_requested_consumers() -> None:
    error = ProcessOutputModeError("streaming", "buffered result")

    assert error.current_mode == "streaming"
    assert error.requested_consumer == "buffered result"
    assert "streaming" in str(error)
    assert "buffered result" in str(error)


def test_managed_process_claims_streaming_only_when_iteration_begins() -> None:
    process = _process(poll=0)
    process.stdout = io.BytesIO(b"one\n")
    managed = ManagedProcess(LocalProcessHandle(process))

    stream = managed.stdout_lines()
    managed._claim_buffered("buffered result")

    with pytest.raises(ProcessOutputModeError, match="stdout stream"):
        next(stream)
    assert process.stdout.tell() == 0


def test_managed_process_rejects_buffered_mode_after_streaming_claim() -> None:
    process = _process(poll=0)
    process.stdout = io.BytesIO(b"one\n")
    managed = ManagedProcess(LocalProcessHandle(process))

    stream = managed.stdout_lines()
    assert next(stream) == "one"

    with pytest.raises(ProcessOutputModeError, match="streaming"):
        managed._claim_buffered("buffered result")


def test_managed_process_marks_closed_output_as_discarded() -> None:
    process = _process(poll=0)
    managed = ManagedProcess(LocalProcessHandle(process))

    managed.close()

    with pytest.raises(ProcessOutputModeError, match="discarded"):
        managed._claim_buffered("buffered result")


@pytest.mark.parametrize(
    "case",
    (
        ResultCase(0, b"stdout\n", b"stderr\n", True),
        ResultCase(7, b"failed stdout\n", b"failed stderr\n", False),
    ),
    ids=("zero", "nonzero"),
)
def test_managed_process_result_drains_both_pipes_caches_and_finalizes_once(
    case: ResultCase,
) -> None:
    process = _process()
    process.returncode = case.exit_code
    process.communicate.return_value = (case.stdout, case.stderr)
    semaphore = MagicMock()
    managed = ManagedProcess(LocalProcessHandle(process), ("multica", "run"), semaphore)

    result = managed.result(datetime.timedelta(seconds=2))
    repeated = managed.result()

    assert result is repeated
    assert result.argv == ("multica", "run")
    assert result.exit_code == case.exit_code
    assert result.stdout == case.stdout.decode()
    assert result.stderr == case.stderr.decode()
    assert result.ok is case.ok
    assert result.failed is not case.ok
    process.communicate.assert_called_once_with(timeout=2.0)
    process.wait.assert_not_called()
    semaphore.release.assert_called_once_with()


def test_managed_process_wait_delegates_to_result_and_preserves_output() -> None:
    process = _process()
    process.returncode = 0
    process.communicate.return_value = (b"out", b"err")
    managed = ManagedProcess(LocalProcessHandle(process))

    assert managed.wait() == 0
    result = managed.result()

    assert result.stdout == "out"
    assert result.stderr == "err"
    process.communicate.assert_called_once_with(timeout=None)
    process.wait.assert_not_called()


def test_managed_process_result_timeout_is_retryable_without_cleanup_or_cache() -> None:
    process = _process()
    process.communicate.side_effect = (
        subprocess.TimeoutExpired(("multica", "run"), 1.0),
        (b"before\nafter", b"warning"),
    )
    semaphore = MagicMock()
    managed = ManagedProcess(LocalProcessHandle(process), semaphore=semaphore)

    with pytest.raises(ProcessTimeoutError, match="wait timed out") as raised:
        managed.result(datetime.timedelta(seconds=1))
    assert isinstance(raised.value.__cause__, subprocess.TimeoutExpired)
    assert not isinstance(raised.value.__cause__, ProcessTimeoutError)
    assert managed._result is None
    semaphore.release.assert_not_called()
    process.stdout.close.assert_not_called()
    process.stderr.close.assert_not_called()

    result = managed.result()

    assert result.stdout == "before\nafter"
    assert result.stderr == "warning"
    assert process.communicate.call_args_list == [call(timeout=1.0), call(timeout=None)]
    semaphore.release.assert_called_once_with()


def test_managed_process_result_zero_timeout_is_forwarded_and_retryable() -> None:
    process = _process()
    process.communicate.side_effect = (
        subprocess.TimeoutExpired(("multica", "run"), 0.0),
        (b"out", b"err"),
    )
    semaphore = MagicMock()
    managed = ManagedProcess(LocalProcessHandle(process), semaphore=semaphore)

    with pytest.raises(ProcessTimeoutError, match="wait timed out"):
        managed.result(datetime.timedelta(0))

    assert managed._result is None
    assert managed._output.mode == "buffered"
    assert not managed._closed
    semaphore.release.assert_not_called()
    process.stdout.close.assert_not_called()
    process.stderr.close.assert_not_called()

    assert managed.result().stdout == "out"
    assert process.communicate.call_args_list == [call(timeout=0.0), call(timeout=None)]
    semaphore.release.assert_called_once_with()


def test_managed_process_communicate_exception_preserves_live_process_ownership() -> None:
    process = _process(poll=None)
    process.returncode = None
    calls = 0

    def communicate(*, timeout: float | None) -> tuple[bytes, bytes]:
        nonlocal calls
        assert timeout is None
        calls += 1
        if calls == 1:
            raise KeyboardInterrupt
        process.returncode = 0
        return b"out", b"err"

    process.communicate.side_effect = communicate
    semaphore = MagicMock()
    managed = ManagedProcess(LocalProcessHandle(process), semaphore=semaphore)

    with pytest.raises(KeyboardInterrupt):
        managed.result()

    assert managed._result is None
    assert managed._output.mode == "buffered"
    assert not managed._closed
    semaphore.release.assert_not_called()
    process.stdin.close.assert_not_called()
    process.stdout.close.assert_not_called()
    process.stderr.close.assert_not_called()

    assert managed.result().stderr == "err"
    semaphore.release.assert_called_once_with()


def test_managed_process_result_rejects_streaming_before_communicate() -> None:
    process = _process(poll=0)
    process.stdout = io.BytesIO(b"one\n")
    managed = ManagedProcess(LocalProcessHandle(process))
    stream = managed.stdout_lines()
    assert next(stream) == "one"

    with pytest.raises(ProcessOutputModeError, match="streaming"):
        managed.result()
    process.communicate.assert_not_called()


def test_managed_process_rejects_stream_after_buffered_collection_before_pipe_read() -> None:
    process = _process(poll=0)
    process.communicate.side_effect = subprocess.TimeoutExpired(("multica",), 1)
    process.stdout = io.BytesIO(b"one\n")
    managed = ManagedProcess(LocalProcessHandle(process))
    with pytest.raises(ProcessTimeoutError, match="wait timed out"):
        managed.result(datetime.timedelta(seconds=1))

    stream = managed.stdout_lines()
    with pytest.raises(ProcessOutputModeError, match="buffered"):
        next(stream)
    assert process.stdout.tell() == 0
    managed.close()


def test_managed_process_close_blocks_result_and_stream_without_refinalizing() -> None:
    process = _process(poll=0)
    process.stdout = io.BytesIO(b"one\n")
    process.stderr = io.BytesIO(b"warning\n")
    managed = ManagedProcess(LocalProcessHandle(process))

    with patch("multica_py.execution.local.close_process_pipes") as close_pipes:
        managed.close()
        with pytest.raises(ProcessOutputModeError, match="discarded"):
            managed.result()
        stream = managed.stdout_lines()
        with pytest.raises(ProcessOutputModeError, match="discarded"):
            next(stream)
        managed.close()

    close_pipes.assert_called_once_with(process)
    process.communicate.assert_not_called()


def test_managed_process_decode_failure_finalizes_without_caching() -> None:
    process = _process()
    process.communicate.return_value = (b"\xff", b"")
    semaphore = MagicMock()
    managed = ManagedProcess(LocalProcessHandle(process), semaphore=semaphore)

    with pytest.raises(EncodingError):
        managed.result()

    assert managed._result is None
    semaphore.release.assert_called_once_with()
    process.communicate.assert_called_once_with(timeout=None)
    with pytest.raises(ProcessOutputModeError, match="discarded"):
        managed.result()
    process.communicate.assert_called_once_with(timeout=None)


def test_managed_process_signals_without_finalizing_before_result() -> None:
    process = _process()
    process.communicate.return_value = (b"out", b"")
    semaphore = MagicMock()
    managed = ManagedProcess(LocalProcessHandle(process), semaphore=semaphore)
    with (
        patch("multica_py.execution.local.terminate_process") as terminate,
        patch("multica_py.execution.local.kill_process") as kill,
    ):
        managed.terminate()
        managed.kill()
        assert managed.result().stdout == "out"

    assert terminate.call_args_list.count(call(process)) == 1
    assert kill.call_args_list.count(call(process)) == 1
    semaphore.release.assert_called_once_with()


@pytest.mark.parametrize("stream_name", ("stdout", "stderr"))
def test_managed_process_stream_decode_failure_raises_encoding_error(stream_name: str) -> None:
    process = _process(poll=0)
    setattr(process, stream_name, io.BytesIO(b"\xff\xfe\n"))
    managed = ManagedProcess(LocalProcessHandle(process))

    stream = managed.stdout_lines() if stream_name == "stdout" else managed.stderr_lines()
    with pytest.raises(EncodingError):
        next(stream)


@pytest.mark.parametrize(
    ("method_name", "pipe_name"),
    (
        ("stdout_lines", "stdout"),
        ("stderr_lines", "stderr"),
    ),
)
def test_managed_process_missing_stream_pipe_raises_capture_error(
    method_name: str,
    pipe_name: str,
) -> None:
    process = _process(poll=0)
    setattr(process, pipe_name, None)
    managed = ManagedProcess(LocalProcessHandle(process))
    stream = getattr(managed, method_name)()
    with pytest.raises(ProcessOutputCaptureError, match=f"{pipe_name} was not captured"):
        next(stream)


def test_managed_process_collect_missing_output_pipes_raises_capture_error() -> None:
    process = _process()
    process.communicate.return_value = (None, None)
    process.returncode = 0
    managed = ManagedProcess(LocalProcessHandle(process))
    with pytest.raises(ProcessOutputCaptureError, match="output pipes were not captured"):
        managed.result()
