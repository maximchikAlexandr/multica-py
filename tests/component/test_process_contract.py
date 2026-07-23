from __future__ import annotations

import datetime
import os
import pathlib
import subprocess
import sys
import threading
import time

import pytest

from multica_py._internal.processes import CancellationToken, run_with_timeout
from multica_py.exceptions import CommandCancelledError, CommandTimeoutError
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


def _run_with_cancel(env: dict[str, str]) -> CommandCancelledError:
    token = CancellationToken()
    exc: list[BaseException] = []

    def _target() -> None:
        try:
            run_with_timeout(_child_argv(), cancel=token, env=env)
        except BaseException as e:
            exc.append(e)

    t = threading.Thread(target=_target, daemon=True)
    t.start()

    for _ in range(100):
        if token.process is not None:
            break
        time.sleep(0.02)
    token.cancel()
    t.join(timeout=10)

    assert len(exc) == 1
    error = exc[0]
    assert isinstance(error, CommandCancelledError)
    return error


@pytest.mark.timeout(20)
@pytest.mark.parametrize(
    "contract_id",
    ["cancellation", "timeout", "sigterm-escalation", "descendant-cleanup"],
)
def test_process_contract(contract_id: str, tmp_path: pathlib.Path) -> None:
    ps = ProcessState()
    env = os.environ.copy()
    env["MULTICA_CHILD_READY_FILE"] = str(tmp_path / "ready")
    env["MULTICA_CHILD_RELEASE_FILE"] = str(tmp_path / "release")
    env["MULTICA_CHILD_PID_FILE"] = str(tmp_path / "parent.pid")
    env["MULTICA_CHILD_CHILD_PID_FILE"] = str(tmp_path / "child.pid")

    release = tmp_path / "release"
    parent_pid_file = tmp_path / "parent.pid"
    child_pid_file = tmp_path / "child.pid"

    parent_pid: int | None = None
    child_pid: int | None = None

    try:
        if contract_id == "cancellation":
            env["MULTICA_CHILD_MODE"] = "default"
            _run_with_cancel(env)

        elif contract_id == "timeout":
            env["MULTICA_CHILD_MODE"] = "sleep"
            with pytest.raises(CommandTimeoutError):
                run_with_timeout(
                    _child_argv(),
                    timeout=datetime.timedelta(seconds=1),
                    env=env,
                )

        elif contract_id == "sigterm-escalation":
            env["MULTICA_CHILD_MODE"] = "sigterm-ignore"
            _run_with_cancel(env)

        elif contract_id == "descendant-cleanup":
            env["MULTICA_CHILD_MODE"] = "descendant"
            with pytest.raises(CommandTimeoutError):
                run_with_timeout(
                    _child_argv(),
                    timeout=datetime.timedelta(seconds=1),
                    env=env,
                )

        parent_pid = _read_pid(parent_pid_file)
        child_pid = _read_pid(child_pid_file)

    finally:
        if not release.exists():
            release.write_text("release")
        if parent_pid is not None:
            ps.wait_absent(parent_pid)
        if child_pid is not None:
            ps.wait_absent(child_pid)
