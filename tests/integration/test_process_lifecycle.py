from __future__ import annotations

import sys

from multica_py._internal.processes import run_with_timeout


def test_process_exit_code_preserved():
    completed = run_with_timeout((sys.executable, "-c", "exit(42)"))
    assert completed.returncode == 42


def test_process_stdout_capture():
    completed = run_with_timeout((sys.executable, "-c", "print('hello world')"))
    assert completed.stdout.strip() == b"hello world"


def test_process_stderr_capture():
    code = "import sys; sys.stderr.write('error message')"
    completed = run_with_timeout((sys.executable, "-c", code))
    assert completed.stderr.strip() == b"error message"


def test_run_with_timeout_success():
    completed = run_with_timeout((sys.executable, "-c", "import sys; sys.exit(0)"))
    assert completed.returncode == 0
