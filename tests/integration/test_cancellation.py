from __future__ import annotations

import contextlib
import datetime
import os
import signal
import sys
import threading
import time

import pytest

from multica_py._internal.processes import (
    CancellationToken,
    create_process,
    run_with_timeout,
    terminate_process,
)
from multica_py.exceptions import CommandCancelledError


def _close_pipes(proc: object) -> None:
    for attr in ("stdout", "stderr", "stdin"):
        pipe = getattr(proc, attr, None)
        if pipe is not None:
            with contextlib.suppress(OSError):
                pipe.close()


def test_run_with_timeout_raises_cancelled_for_real_process() -> None:
    token = CancellationToken()
    exc: list[BaseException] = []

    def target() -> None:
        try:
            run_with_timeout(
                (sys.executable, "-c", "import time; time.sleep(30)"),
                timeout=datetime.timedelta(seconds=10),
                cancel=token,
            )
        except BaseException as e:
            exc.append(e)

    t = threading.Thread(target=target, daemon=True)
    t.start()

    for _ in range(100):
        if token.process is not None and token.process.poll() is None:
            break
        time.sleep(0.02)

    token.cancel()
    t.join(timeout=10)

    assert len(exc) == 1
    assert isinstance(exc[0], CommandCancelledError)
    assert str(exc[0]) == "Command was cancelled"


def test_precancelled_token_raises_immediately() -> None:
    token = CancellationToken()
    token.cancel()
    with pytest.raises(CommandCancelledError, match="Command was cancelled"):
        run_with_timeout(
            (sys.executable, "-c", "import sys; sys.exit(0)"),
            cancel=token,
        )


def test_uncancelled_token_does_not_raise() -> None:
    result = run_with_timeout(
        (sys.executable, "-c", "print('ok')"),
        cancel=CancellationToken(),
    )
    assert result.returncode == 0


def test_terminate_process_kills_descendants() -> None:
    """Spawn a parent that spawns a child; terminate via _killpg, verify both dead."""
    parent = create_process(
        (
            sys.executable,
            "-c",
            "import subprocess, sys, time;"
            "c = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']);"
            "print(c.pid, flush=True);"
            "time.sleep(60)",
        )
    )
    assert parent.poll() is None
    time.sleep(0.5)

    assert parent.stdout is not None
    child_pid_line = parent.stdout.readline()
    child_pid = int(child_pid_line.strip())

    terminate_process(parent)
    parent.wait(timeout=5)
    assert parent.poll() is not None
    assert parent.returncode == -signal.SIGTERM  # terminated by signal

    try:
        os.kill(child_pid, 0)
        assert False, "child process still alive after parent was killed"
    except OSError:
        pass

    _close_pipes(parent)


def test_cancelled_process_escalates_after_sigterm_is_ignored() -> None:
    token = CancellationToken()
    exc: list[BaseException] = []

    def target() -> None:
        try:
            run_with_timeout(
                (
                    sys.executable,
                    "-c",
                    "import signal, time;"
                    "signal.signal(signal.SIGTERM, lambda *_: None);"
                    "time.sleep(30)",
                ),
                timeout=datetime.timedelta(seconds=10),
                cancel=token,
            )
        except BaseException as e:
            exc.append(e)

    t = threading.Thread(target=target, daemon=True)
    t.start()

    for _ in range(100):
        if token.process is not None and token.process.poll() is None:
            break
        time.sleep(0.02)

    token.cancel()
    t.join(timeout=10)

    assert len(exc) == 1
    assert isinstance(exc[0], CommandCancelledError)
