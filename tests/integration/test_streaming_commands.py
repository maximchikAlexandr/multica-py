from __future__ import annotations

import datetime
import subprocess
import sys

from multica_py._internal.processes import run_with_timeout
from multica_py.exceptions import CommandTimeoutError
from multica_py.process import ManagedProcess


def test_managed_process_poll():
    proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(42)"])
    proc.wait()
    mp = ManagedProcess(proc)
    assert mp.poll() == 42
    mp.close()


def test_managed_process_argv():
    proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(0)"])
    proc.wait()
    mp = ManagedProcess(proc, argv=("multica", "issue", "list"))
    assert mp.argv == ("multica", "issue", "list")
    mp.close()


def test_timeout_terminates_process():
    try:
        run_with_timeout(
            (sys.executable, "-c", "import time; time.sleep(60)"),
            timeout=datetime.timedelta(seconds=1),
        )
        assert False, "Expected CommandTimeoutError"
    except CommandTimeoutError:
        pass


def test_managed_process_stdout_lines():
    proc = subprocess.Popen(
        [sys.executable, "-c", "print('line1'); print('line2'); print('line3')"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, _ = proc.communicate()
    lines = stdout.decode("utf-8").strip().split("\n")
    assert len(lines) == 3
    assert lines == ["line1", "line2", "line3"]


def test_managed_process_consumes_partial_output():
    proc = subprocess.Popen(
        [sys.executable, "-c", "import sys; sys.stdout.write('partial'); sys.stdout.flush()"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    proc.wait()
    out = proc.stdout.read().decode("utf-8") if proc.stdout else ""
    assert out == "partial"
    if proc.stdout:
        proc.stdout.close()
    if proc.stderr:
        proc.stderr.close()
