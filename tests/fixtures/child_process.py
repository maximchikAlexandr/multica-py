#!/usr/bin/env python3
"""Deterministic child-process harness for component process contract tests."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import BinaryIO, cast


def _write_text(path: str, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


def _wait_for_release(release_file: str) -> None:
    while not Path(release_file).exists():
        time.sleep(0.05)


def _emit_configured_output(
    stdout_name: str = "MULTICA_CHILD_STDOUT",
    stderr_name: str = "MULTICA_CHILD_STDERR",
) -> None:
    stdout_text = os.environ.get(stdout_name, "")
    if stdout_text:
        sys.stdout.write(stdout_text)
        sys.stdout.flush()

    stderr_text = os.environ.get(stderr_name, "")
    if stderr_text:
        sys.stderr.write(stderr_text)
        sys.stderr.flush()


def _exit_code() -> int:
    return int(os.environ.get("MULTICA_CHILD_EXIT_CODE", "0"))


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
    child_env.pop("MULTICA_CHILD_PID_FILE", None)
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
    _emit_configured_output()
    release_file = os.environ.get("MULTICA_CHILD_RELEASE_FILE", "")
    if release_file:
        _wait_for_release(release_file)
    else:
        while True:
            time.sleep(3600)
    return _exit_code()


def _run_delayed_output_mode() -> int:
    ready_file = os.environ.get("MULTICA_CHILD_READY_FILE", "")
    if ready_file:
        _write_text(ready_file, "ready")
    _emit_configured_output("MULTICA_CHILD_INITIAL_STDOUT", "MULTICA_CHILD_INITIAL_STDERR")
    release_file = os.environ.get("MULTICA_CHILD_RELEASE_FILE", "")
    if release_file:
        _wait_for_release(release_file)
    _emit_configured_output("MULTICA_CHILD_TRAILING_STDOUT", "MULTICA_CHILD_TRAILING_STDERR")
    return _exit_code()


def _run_interleaved_mode() -> int:
    chunk_size = int(os.environ.get("MULTICA_CHILD_CHUNK_SIZE", "4096"))
    chunks = int(os.environ.get("MULTICA_CHILD_CHUNKS", "64"))
    stdout_chunk = ("o" * chunk_size).encode("ascii")
    stderr_chunk = ("e" * chunk_size).encode("ascii")
    stdout = cast("BinaryIO", sys.stdout.buffer)
    stderr = cast("BinaryIO", sys.stderr.buffer)
    for _ in range(chunks):
        stdout.write(stdout_chunk)
        stdout.flush()
        stderr.write(stderr_chunk)
        stderr.flush()
    return _exit_code()


def _run_pipe_heavy_mode(heavy: str) -> int:
    filled = cast("BinaryIO", (sys.stderr if heavy == "stderr" else sys.stdout).buffer)
    other = cast("BinaryIO", (sys.stdout if heavy == "stderr" else sys.stderr).buffer)
    chunk = b"e" * int(os.environ.get("MULTICA_CHILD_CHUNK_SIZE", "4096"))
    for _ in range(int(os.environ.get("MULTICA_CHILD_CHUNKS", "64"))):
        filled.write(chunk)
        filled.flush()
    other.write(b"done\n")
    other.flush()
    return _exit_code()


def _run_descendant_mode() -> int:
    pid_file = os.environ.get("MULTICA_CHILD_PID_FILE", "")
    if pid_file:
        _write_text(pid_file, str(os.getpid()))
    child_env = os.environ.copy()
    child_env["MULTICA_CHILD_MODE"] = "sleep"
    child_env.pop("MULTICA_CHILD_PID_FILE", None)
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
    signal_log = os.environ.get("MULTICA_CHILD_SIGNAL_LOG", "")

    def _ignore_first_sigterm(*_: object) -> None:
        if signal_log:
            _write_text(signal_log, "SIGTERM")
        child.terminate()
        child.wait()

    signal.signal(signal.SIGTERM, _ignore_first_sigterm)
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


def _run_stdin_echo_mode() -> int:
    data: bytes = sys.stdin.buffer.read()  # type: ignore[misc]
    sys.stdout.buffer.write(data)  # type: ignore[misc]
    sys.stdout.buffer.flush()  # type: ignore[misc]
    return 0


def main() -> int:
    mode = os.environ.get("MULTICA_CHILD_MODE", "")
    if mode == "sleep":
        return _run_sleep_mode()
    if mode == "child":
        return _run_child_mode()
    if mode == "sigterm-ignore":
        return _run_sigterm_ignore_mode()
    if mode == "delayed-output":
        return _run_delayed_output_mode()
    if mode == "interleaved":
        return _run_interleaved_mode()
    if mode == "stderr-heavy":
        return _run_pipe_heavy_mode("stderr")
    if mode == "stdout-heavy":
        return _run_pipe_heavy_mode("stdout")
    if mode == "descendant":
        return _run_descendant_mode()
    if mode == "stdin-echo":
        return _run_stdin_echo_mode()

    pid_file = os.environ.get("MULTICA_CHILD_PID_FILE", "")
    if pid_file:
        _write_text(pid_file, str(os.getpid()))

    ready_file = os.environ.get("MULTICA_CHILD_READY_FILE", "")
    if ready_file:
        _write_text(ready_file, "ready")

    release_file = os.environ.get("MULTICA_CHILD_RELEASE_FILE", "")
    if release_file:
        _wait_for_release(release_file)

    _emit_configured_output()

    probe_file = os.environ.get("MULTICA_CHILD_PROBE_FILE", "")
    if probe_file:
        allowed = sorted(key for key in os.environ if key.startswith("MULTICA_"))
        _write_text(probe_file, "\n".join((*sys.argv[1:], "--", *allowed)))

    return _exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
