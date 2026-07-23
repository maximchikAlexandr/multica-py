from __future__ import annotations

import platform
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from tests.fixtures.process_state import ProcessState


@dataclass(frozen=True)
class _LinuxStatCase:
    stat_content: str | None
    expected_running: bool | None
    expected_zombie: bool | None
    expected_absent: bool | None


@dataclass(frozen=True)
class _MacOsPsCase:
    ps_output: str | None
    ps_rc: int
    expected_running: bool | None
    expected_zombie: bool | None
    expected_absent: bool | None


_LINUX_CASES: tuple[_LinuxStatCase, ...] = (
    _LinuxStatCase(
        stat_content="12345 (test) S 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50",
        expected_running=True,
        expected_zombie=False,
        expected_absent=False,
    ),
    _LinuxStatCase(
        stat_content="12345 (test) Z 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50",
        expected_running=False,
        expected_zombie=True,
        expected_absent=False,
    ),
    _LinuxStatCase(
        stat_content=None,
        expected_running=False,
        expected_zombie=False,
        expected_absent=True,
    ),
    _LinuxStatCase(
        stat_content="12345 (test) R 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50",
        expected_running=True,
        expected_zombie=False,
        expected_absent=False,
    ),
)

_MACOS_CASES: tuple[_MacOsPsCase, ...] = (
    _MacOsPsCase(
        ps_output="R",
        ps_rc=0,
        expected_running=True,
        expected_zombie=False,
        expected_absent=False,
    ),
    _MacOsPsCase(
        ps_output="Z",
        ps_rc=0,
        expected_running=False,
        expected_zombie=True,
        expected_absent=False,
    ),
    _MacOsPsCase(
        ps_output="",
        ps_rc=1,
        expected_running=False,
        expected_zombie=False,
        expected_absent=True,
    ),
)


@dataclass(frozen=True)
class _WaitAbsentCase:
    absent_results: list[bool | None]
    expect_timeout: bool


_WAIT_ABSENT_CASES: tuple[_WaitAbsentCase, ...] = (
    _WaitAbsentCase(absent_results=[True], expect_timeout=False),
    _WaitAbsentCase(absent_results=[None, True], expect_timeout=False),
    _WaitAbsentCase(absent_results=[False, False], expect_timeout=True),
)


@pytest.mark.parametrize("case", _LINUX_CASES)
def test_linux_stat_parsing(case: _LinuxStatCase, monkeypatch: Any) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    if case.stat_content is not None:

        def _mock_read(*args: Any, **kwargs: Any) -> str:
            return case.stat_content  # type: ignore[return-value]

        monkeypatch.setattr(Path, "read_text", _mock_read)
    else:

        def _mock_read_missing(*args: Any, **kwargs: Any) -> str:
            raise FileNotFoundError

        monkeypatch.setattr(Path, "read_text", _mock_read_missing)

    ps = ProcessState()
    assert ps.running(12345) == case.expected_running
    assert ps.zombie(12345) == case.expected_zombie
    assert ps.absent(12345) == case.expected_absent


@pytest.mark.parametrize("case", _MACOS_CASES)
def test_macos_ps_parsing(case: _MacOsPsCase, monkeypatch: Any) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Darwin")

    class _MockCompletedProcess:
        stdout: str
        returncode: int

        def __init__(self, stdout: str, returncode: int) -> None:
            self.stdout = stdout
            self.returncode = returncode

    def _mock_run(*args: Any, **kwargs: Any) -> _MockCompletedProcess:
        return _MockCompletedProcess(stdout=case.ps_output or "", returncode=case.ps_rc)

    monkeypatch.setattr(subprocess, "run", _mock_run)

    ps = ProcessState()
    assert ps.running(12345) == case.expected_running
    assert ps.zombie(12345) == case.expected_zombie
    assert ps.absent(12345) == case.expected_absent


def test_unknown_platform_returns_none(monkeypatch: Any) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Windows")
    ps = ProcessState()
    assert ps.running(12345) is None
    assert ps.zombie(12345) is None
    assert ps.absent(12345) is None


@pytest.mark.parametrize("case", _WAIT_ABSENT_CASES)
def test_wait_absent(case: _WaitAbsentCase, monkeypatch: Any) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    call_count: int = 0
    orig_results = list(case.absent_results)

    def _mock_read(*args: Any, **kwargs: Any) -> str:
        nonlocal call_count
        if call_count < len(orig_results):
            result = orig_results[call_count]
            call_count += 1
            if result is True:
                raise FileNotFoundError
            return "12345 (test) S ..."
        return "12345 (test) S ..."

    monkeypatch.setattr(Path, "read_text", _mock_read)

    ps = ProcessState()
    if case.expect_timeout:
        with pytest.raises(TimeoutError):
            ps.wait_absent(12345, deadline=0.5, interval=0.05)
    else:
        ps.wait_absent(12345, deadline=0.5, interval=0.05)
