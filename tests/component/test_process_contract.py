from __future__ import annotations

import datetime
import pathlib
import sys

import pytest

from multica_py._internal.processes import CancellationToken, run_with_timeout
from multica_py.exceptions import CommandTimeoutError
from tests.fixtures.process_state import ProcessState

pytestmark = [pytest.mark.process, pytest.mark.serial]

_CHILD_PROCESS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "child_process.py"


def _child_argv() -> tuple[str, ...]:
    return (sys.executable, str(_CHILD_PROCESS))


def _read_pid(path: pathlib.Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None


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
