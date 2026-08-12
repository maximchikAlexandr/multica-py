from __future__ import annotations

import datetime
import json
import os
import pathlib
import subprocess
import sys
import time
from collections.abc import Callable

import pytest

from multica_py._internal.processes import CancellationToken, run_with_timeout
from multica_py.client import MulticaClient
from multica_py.entities import Issue
from multica_py.exceptions import CommandTimeoutError, ProcessOutputModeError
from multica_py.process import ManagedProcess, ProcessResult
from tests.fixtures.fake_multica import FakeMultica
from tests.fixtures.process_state import ProcessState

pytestmark = [pytest.mark.process, pytest.mark.serial]

_CHILD_PROCESS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "child_process.py"


def _child_argv() -> tuple[str, ...]:
    return (sys.executable, str(_CHILD_PROCESS))


def _managed_child(env: dict[str, str]) -> tuple[ManagedProcess, subprocess.Popen[bytes]]:
    child_env = os.environ.copy()
    child_env.update(env)
    process = subprocess.Popen(
        list(_child_argv()),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=child_env,
    )
    return ManagedProcess(process, argv=_child_argv()), process


def _wait_for_file(path: pathlib.Path) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.01)
    raise AssertionError(f"child did not create {path} within five seconds")


def _read_pid(path: pathlib.Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None


@pytest.mark.parametrize(
    ("stdout", "stderr"),
    (("stdout only\n", ""), ("", "stderr only\n")),
    ids=("stdout-only", "stderr-only"),
)
def test_managed_process_result_captures_each_real_pipe(stdout: str, stderr: str) -> None:
    managed, _process = _managed_child(
        {
            "MULTICA_CHILD_STDOUT": stdout,
            "MULTICA_CHILD_STDERR": stderr,
        }
    )

    result = managed.result(datetime.timedelta(seconds=5))

    assert result.argv == _child_argv()
    assert result.exit_code == 0
    assert result.stdout == stdout
    assert result.stderr == stderr
    assert result.ok
    assert not result.failed


@pytest.mark.parametrize(
    ("exit_code", "ok"),
    (("0", True), ("9", False)),
    ids=("zero", "nonzero"),
)
def test_managed_process_real_result_preserves_exit_status(exit_code: str, ok: bool) -> None:
    managed, _process = _managed_child(
        {
            "MULTICA_CHILD_STDOUT": "output\n",
            "MULTICA_CHILD_STDERR": "warning\n",
            "MULTICA_CHILD_EXIT_CODE": exit_code,
        }
    )

    result = managed.result(datetime.timedelta(seconds=5))

    assert result.exit_code == int(exit_code)
    assert result.ok is ok
    assert result.failed is not ok


def test_managed_process_real_interleaved_pipe_capacity_output() -> None:
    chunk_size = 4096
    chunks = 64
    managed, _process = _managed_child(
        {
            "MULTICA_CHILD_MODE": "interleaved",
            "MULTICA_CHILD_CHUNK_SIZE": str(chunk_size),
            "MULTICA_CHILD_CHUNKS": str(chunks),
        }
    )

    result = managed.result(datetime.timedelta(seconds=10))

    assert result.stdout == "o" * chunk_size * chunks
    assert result.stderr == "e" * chunk_size * chunks


def test_managed_process_real_wait_then_result_preserves_output() -> None:
    managed, _process = _managed_child(
        {"MULTICA_CHILD_STDOUT": "out\n", "MULTICA_CHILD_STDERR": "err\n"}
    )

    assert managed.wait(datetime.timedelta(seconds=5)) == 0
    result = managed.result()

    assert result.stdout == "out\n"
    assert result.stderr == "err\n"


def test_managed_process_real_timeout_retry_keeps_complete_output(tmp_path: pathlib.Path) -> None:
    ready = tmp_path / "ready"
    release = tmp_path / "release"
    managed, process = _managed_child(
        {
            "MULTICA_CHILD_MODE": "delayed-output",
            "MULTICA_CHILD_READY_FILE": str(ready),
            "MULTICA_CHILD_RELEASE_FILE": str(release),
            "MULTICA_CHILD_INITIAL_STDOUT": "before\n",
            "MULTICA_CHILD_INITIAL_STDERR": "warning before\n",
            "MULTICA_CHILD_TRAILING_STDOUT": "after\n",
            "MULTICA_CHILD_TRAILING_STDERR": "warning after\n",
        }
    )
    _wait_for_file(ready)

    with pytest.raises(TimeoutError, match="wait timed out"):
        managed.result(datetime.timedelta(seconds=0.1))
    assert process.stdout is not None
    assert process.stderr is not None
    assert not process.stdout.closed
    assert not process.stderr.closed

    release.touch()
    result = managed.result(datetime.timedelta(seconds=5))

    assert result.stdout == "before\nafter\n"
    assert result.stderr == "warning before\nwarning after\n"


@pytest.mark.parametrize("operation", ("terminate", "kill"))
def test_managed_process_real_signal_then_result(operation: str, tmp_path: pathlib.Path) -> None:
    ready = tmp_path / f"{operation}-ready"
    managed, _process = _managed_child(
        {
            "MULTICA_CHILD_MODE": "sigterm-ignore",
            "MULTICA_CHILD_READY_FILE": str(ready),
            "MULTICA_CHILD_STDOUT": "captured before signal\n",
            "MULTICA_CHILD_STDERR": "diagnostic before signal\n",
        }
    )
    _wait_for_file(ready)

    getattr(managed, operation)()
    result = managed.result(datetime.timedelta(seconds=5))

    assert result.stdout == "captured before signal\n"
    assert result.stderr == "diagnostic before signal\n"
    assert result.exit_code != 0


def test_managed_process_real_close_discards_output(tmp_path: pathlib.Path) -> None:
    ready = tmp_path / "close-ready"
    managed, process = _managed_child(
        {
            "MULTICA_CHILD_MODE": "sigterm-ignore",
            "MULTICA_CHILD_READY_FILE": str(ready),
        }
    )
    _wait_for_file(ready)

    managed.close()

    with pytest.raises(ProcessOutputModeError, match="discarded"):
        managed.result()
    assert process.poll() is not None


def test_managed_process_real_streaming_remains_incremental() -> None:
    managed, _process = _managed_child({"MULTICA_CHILD_STDOUT": "one\ntwo\n"})

    assert list(managed.stdout_lines()) == ["one", "two"]


def test_resource_command_keeps_domain_result_type(
    client_factory: Callable[..., MulticaClient], tmp_path: pathlib.Path
) -> None:
    responses_dir = tmp_path / "responses"
    responses_dir.mkdir()
    response = FakeMultica(responses_dir=responses_dir).build_response(
        stdout='{"id":"i1","title":"Issue","status":"todo"}',
        argv=("fake_multica", "issue", "get", "i1", "--output", "json"),
    )
    (responses_dir / "issue.json").write_text(
        json.dumps(response.to_dict()),
        encoding="utf-8",
    )
    client = client_factory(environment=(("MULTICA_FAKE_RESPONSES", str(responses_dir)),))

    result = client.issues.get("i1")

    assert isinstance(result, Issue)
    assert not isinstance(result, ProcessResult)


@pytest.mark.timeout(20)
@pytest.mark.parametrize(
    "contract_id",
    ("bytes-env", "text-stdin", "timeout-tree-cleanup"),
)
def test_process_contract(contract_id: str, tmp_path: pathlib.Path) -> None:
    ps = ProcessState()

    if contract_id == "bytes-env":
        output = b'{"key":"value"}'
        probe = tmp_path / "probe"
        env = {
            "MULTICA_CHILD_STDOUT": output.decode(),
            "MULTICA_CHILD_STDERR": "error-output",
            "MULTICA_CHILD_PROBE_FILE": str(probe),
        }
        result = run_with_timeout(_child_argv(), cancel=CancellationToken(), env=env)
        assert result.stdout == output
        assert result.stderr == b"error-output"
        assert result.args == list(_child_argv())
        assert probe.read_text(encoding="utf-8").splitlines() == [
            "--",
            "MULTICA_CHILD_PROBE_FILE",
            "MULTICA_CHILD_STDERR",
            "MULTICA_CHILD_STDOUT",
        ]

    elif contract_id == "text-stdin":
        stdin_data = b"hello stdin"
        env = {"MULTICA_CHILD_MODE": "stdin-echo"}
        result = run_with_timeout(
            _child_argv(),
            cancel=CancellationToken(),
            env=env,
            stdin=stdin_data,
        )
        assert result.stdout == stdin_data
        assert result.stdout.decode("utf-8") == "hello stdin"
        assert result.returncode == 0

    elif contract_id == "timeout-tree-cleanup":
        signal_log = tmp_path / "signals"
        env = {
            "MULTICA_CHILD_READY_FILE": str(tmp_path / "ready"),
            "MULTICA_CHILD_PID_FILE": str(tmp_path / "parent.pid"),
            "MULTICA_CHILD_CHILD_PID_FILE": str(tmp_path / "child.pid"),
            "MULTICA_CHILD_MODE": "descendant",
            "MULTICA_CHILD_SIGNAL_LOG": str(signal_log),
        }
        with pytest.raises(CommandTimeoutError):
            run_with_timeout(
                _child_argv(),
                timeout=datetime.timedelta(seconds=1),
                env=env,
            )
        parent_pid = _read_pid(tmp_path / "parent.pid")
        child_pid = _read_pid(tmp_path / "child.pid")
        assert parent_pid is not None
        assert child_pid is not None
        assert parent_pid != child_pid
        assert signal_log.read_text(encoding="utf-8") == "SIGTERM"
        ps.wait_absent(parent_pid, deadline=8)
        ps.wait_absent(child_pid, deadline=8)
