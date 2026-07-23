from __future__ import annotations

import os
import platform
import subprocess
import time
from collections.abc import Callable
from pathlib import Path


def _linux_categorize(pid: int) -> str | None:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
    except FileNotFoundError:
        return "absent"
    last_paren = stat.rfind(")")
    if last_paren == -1:
        return None
    after = stat[last_paren + 1 :].strip()
    if not after:
        return None
    state = after[0]
    if state == "Z":
        return "zombie"
    if state in ("X", "x"):
        return "absent"
    return "running"


def _macos_categorize(pid: int) -> str | None:
    try:
        result = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    output = result.stdout.strip()
    if not output:
        return "absent"
    state = output[0]
    if state == "Z":
        return "zombie"
    return "running"


class ProcessState:
    def __init__(self) -> None:
        system = platform.system()
        if system == "Linux":
            self._categorize: Callable[[int], str | None] = _linux_categorize
        elif system == "Darwin":
            self._categorize = _macos_categorize
        else:
            self._categorize = lambda pid: None

    def running(self, pid: int) -> bool | None:
        cat = self._categorize(pid)
        if cat is None:
            return None
        return cat == "running"

    def zombie(self, pid: int) -> bool | None:
        cat = self._categorize(pid)
        if cat is None:
            return None
        return cat == "zombie"

    def absent(self, pid: int) -> bool | None:
        cat = self._categorize(pid)
        if cat is None:
            return None
        return cat == "absent"

    def wait_absent(self, pid: int, deadline: float = 2.0, interval: float = 0.02) -> None:
        start = time.monotonic()
        while time.monotonic() - start < deadline:
            if self.absent(pid) is True:
                return
            time.sleep(interval)
        raise TimeoutError(f"Process {pid} did not disappear within {deadline}s")
