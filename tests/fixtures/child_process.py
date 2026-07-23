#!/usr/bin/env python3
"""Deterministic child-process harness for component process contract tests."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def _write_text(path: str, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


def _wait_for_release(release_file: str) -> None:
    while not Path(release_file).exists():
        time.sleep(0.05)


def _run_sleep_mode() -> int:
    pid_file = os.environ.get("MULTICA_CHILD_PID_FILE", "")
    if pid_file:
        _write_text(pid_file, str(os.getpid()))
    while True:
        time.sleep(3600)


def _run_child_mode() -> int:
    pid_file = os.environ.get("MULTICA_CHILD_PID_FILE", "")
    if pid_file:
        _write_text(pid_file, str(os.getpid()))
    child_env = os.environ.copy()
    child_env["MULTICA_CHILD_MODE"] = "sleep"
    child = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve())],
        env=child_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    child_pid_file = os.environ.get("MULTICA_CHILD_CHILD_PID_FILE", "")
    if child_pid_file:
        _write_text(child_pid_file, str(child.pid))
    release_file = os.environ.get("MULTICA_CHILD_RELEASE_FILE", "")
    if release_file:
        _wait_for_release(release_file)
    else:
        while True:
            time.sleep(3600)
    return int(os.environ.get("MULTICA_CHILD_EXIT_CODE", "0"))


def _run_sigterm_ignore_mode() -> int:
    import signal

    signal.signal(signal.SIGTERM, lambda *_: None)
    pid_file = os.environ.get("MULTICA_CHILD_PID_FILE", "")
    if pid_file:
        _write_text(pid_file, str(os.getpid()))
    ready_file = os.environ.get("MULTICA_CHILD_READY_FILE", "")
    if ready_file:
        _write_text(ready_file, "ready")
    release_file = os.environ.get("MULTICA_CHILD_RELEASE_FILE", "")
    if release_file:
        _wait_for_release(release_file)
    else:
        while True:
            time.sleep(3600)
    return int(os.environ.get("MULTICA_CHILD_EXIT_CODE", "0"))


def _run_descendant_mode() -> int:
    pid_file = os.environ.get("MULTICA_CHILD_PID_FILE", "")
    if pid_file:
        _write_text(pid_file, str(os.getpid()))
    child_env = os.environ.copy()
    child_env["MULTICA_CHILD_MODE"] = "sleep"
    child = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve())],
        env=child_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    child_pid_file = os.environ.get("MULTICA_CHILD_CHILD_PID_FILE", "")
    if child_pid_file:
        _write_text(child_pid_file, str(child.pid))
    ready_file = os.environ.get("MULTICA_CHILD_READY_FILE", "")
    if ready_file:
        _write_text(ready_file, "ready")
    release_file = os.environ.get("MULTICA_CHILD_RELEASE_FILE", "")
    if release_file:
        _wait_for_release(release_file)
    else:
        while True:
            time.sleep(3600)
    return int(os.environ.get("MULTICA_CHILD_EXIT_CODE", "0"))


def main() -> int:
    """Run the configured child-process scenario."""
    mode = os.environ.get("MULTICA_CHILD_MODE", "")
    if mode == "sleep":
        return _run_sleep_mode()
    if mode == "child":
        return _run_child_mode()
    if mode == "sigterm-ignore":
        return _run_sigterm_ignore_mode()
    if mode == "descendant":
        return _run_descendant_mode()

    pid_file = os.environ.get("MULTICA_CHILD_PID_FILE", "")
    if pid_file:
        _write_text(pid_file, str(os.getpid()))

    ready_file = os.environ.get("MULTICA_CHILD_READY_FILE", "")
    if ready_file:
        _write_text(ready_file, "ready")

    release_file = os.environ.get("MULTICA_CHILD_RELEASE_FILE", "")
    if release_file:
        _wait_for_release(release_file)

    stdout_text = os.environ.get("MULTICA_CHILD_STDOUT", "")
    if stdout_text:
        sys.stdout.write(stdout_text)
        sys.stdout.flush()

    stderr_text = os.environ.get("MULTICA_CHILD_STDERR", "")
    if stderr_text:
        sys.stderr.write(stderr_text)
        sys.stderr.flush()

    return int(os.environ.get("MULTICA_CHILD_EXIT_CODE", "0"))


if __name__ == "__main__":
    raise SystemExit(main())
