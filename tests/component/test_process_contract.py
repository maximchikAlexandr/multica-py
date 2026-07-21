from __future__ import annotations

import datetime
import os
import pathlib
import sys
from dataclasses import dataclass

import pytest

from multica_py._internal.processes import run_with_timeout
from multica_py.exceptions import CommandTimeoutError

pytestmark = [pytest.mark.serial, pytest.mark.process]

_CHILD_PROCESS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "child_process.py"


@dataclass(frozen=True)
class _ProcessCase:
    exit_code: str
    stdout: str
    stderr: str
    mode: str
    expect_timeout: bool


_PROCESS_CASES: tuple[_ProcessCase, ...] = (
    _ProcessCase(exit_code="0", stdout="", stderr="", mode="", expect_timeout=False),
    _ProcessCase(exit_code="42", stdout="", stderr="", mode="", expect_timeout=False),
    _ProcessCase(
        exit_code="0",
        stdout="hello world",
        stderr="",
        mode="",
        expect_timeout=False,
    ),
    _ProcessCase(
        exit_code="0",
        stdout="",
        stderr="error message",
        mode="",
        expect_timeout=False,
    ),
    _ProcessCase(exit_code="0", stdout="", stderr="", mode="child", expect_timeout=True),
)


def _child_argv() -> tuple[str, ...]:
    return (sys.executable, str(_CHILD_PROCESS))


def _process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


@pytest.mark.parametrize(
    "case",
    _PROCESS_CASES,
    ids=["success", "non-zero-exit", "stdout", "stderr", "timeout"],
)
def test_process_lifecycle_contract(
    case: _ProcessCase,
    tmp_path: pathlib.Path,
) -> None:
    """Exercise run_with_timeout against the deterministic child-process harness."""
    env = os.environ.copy()
    env["MULTICA_CHILD_EXIT_CODE"] = case.exit_code
    env["MULTICA_CHILD_STDOUT"] = case.stdout
    env["MULTICA_CHILD_STDERR"] = case.stderr
    env["MULTICA_CHILD_MODE"] = case.mode
    parent_pid_file = tmp_path / "parent.pid"
    child_pid_file = tmp_path / "child.pid"
    env["MULTICA_CHILD_PID_FILE"] = str(parent_pid_file)
    if case.mode == "child":
        env["MULTICA_CHILD_CHILD_PID_FILE"] = str(child_pid_file)

    if case.expect_timeout:
        with pytest.raises(CommandTimeoutError) as exc_info:
            run_with_timeout(
                _child_argv(),
                timeout=datetime.timedelta(seconds=1),
                env=env,
            )
        assert exc_info.type is CommandTimeoutError
        assert parent_pid_file.is_file()
        parent_pid = int(parent_pid_file.read_text(encoding="utf-8"))
        assert not _process_is_alive(parent_pid)
        assert child_pid_file.is_file()
        child_pid = int(child_pid_file.read_text(encoding="utf-8"))
        assert not _process_is_alive(child_pid)
        return

    completed = run_with_timeout(_child_argv(), env=env)
    assert completed.returncode == int(case.exit_code)
    if case.stdout:
        assert completed.stdout.strip() == case.stdout.encode("utf-8")
    if case.stderr:
        assert completed.stderr.strip() == case.stderr.encode("utf-8")
