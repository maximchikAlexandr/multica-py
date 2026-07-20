from __future__ import annotations

import subprocess
import sys

from multica_py.process import ManagedProcess


def test_managed_process_poll():
    proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(42)"])
    proc.wait()
    mp = ManagedProcess(proc)
    assert mp.poll() == 42
    mp.close()
