from __future__ import annotations

import json
import os
import pathlib
import subprocess
import textwrap
import time
from collections.abc import Callable
from dataclasses import dataclass

from tests.live._live_helpers import LiveTestRun
from tests.live.diagnostics import DiagnosticCollector
from tools.live_support.environment import LiveSetupError
from tools.live_support.oracle import DirectApiOracle

DAEMON_READY_TIMEOUT_SECONDS = 10.0
RUNTIME_READY_TIMEOUT_SECONDS = 60.0
RUNTIME_DEREGISTER_TIMEOUT_SECONDS = 30.0
RUNTIME_POLL_INTERVAL_SECONDS = 1.0
TERMINAL_RUN_STATUSES = frozenset({"completed", "failed", "cancelled", "timed_out", "canceled"})


def daemon_status_payload_is_running(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("running") is True:
        return True
    return payload.get("status") == "running"


@dataclass(slots=True)
class DaemonLifecycle:
    """Foreground daemon process lifecycle for agent sandbox tests."""

    cli_executable: pathlib.Path
    home_dir: pathlib.Path
    profile_name: str
    daemon_id: str
    workspaces_root: pathlib.Path
    opencode_path: pathlib.Path
    opencode_model: str
    agent_mode: str
    diagnostics: DiagnosticCollector
    _process: subprocess.Popen[str] | None = None
    _log_path: pathlib.Path | None = None

    def start(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return
        self.home_dir.mkdir(parents=True, exist_ok=True)
        self.workspaces_root.mkdir(parents=True, exist_ok=True)
        log_path = self.home_dir / "daemon.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_path = log_path
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(self.home_dir),
                "MULTICA_PROFILE": self.profile_name,
                "MULTICA_DAEMON_ID": self.daemon_id,
                "MULTICA_WORKSPACES_ROOT": str(self.workspaces_root),
                "MULTICA_OPENCODE_PATH": str(self.opencode_path.resolve()),
                "MULTICA_OPENCODE_MODEL": self.opencode_model,
                "MULTICA_DAEMON_POLL_INTERVAL": "1s",
                "MULTICA_DAEMON_HEARTBEAT_INTERVAL": "2s",
                "MULTICA_TEST_AGENT_MODE": self.agent_mode,
            }
        )
        log_handle = log_path.open("a", encoding="utf-8")
        try:
            self._process = subprocess.Popen(
                self._daemon_argv("daemon", "start", "--foreground"),
                env=env,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except OSError as exc:
            raise LiveSetupError("daemon", f"failed to start daemon subprocess: {exc}") from exc
        finally:
            log_handle.close()
        deadline = time.monotonic() + DAEMON_READY_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise LiveSetupError("daemon", self._daemon_start_failure_detail())
            if self._daemon_status_running():
                return
            time.sleep(0.5)
        raise LiveSetupError("daemon", self._daemon_start_failure_detail(timeout=True))

    def stop(self) -> None:
        self._run_daemon_cli(["daemon", "stop"], check=False)
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline:
            if self._process is None or self._process.poll() is not None:
                return
            if not self._daemon_status_running():
                self._terminate_process(timeout=5.0)
                return
            time.sleep(0.5)
        self._terminate_process(timeout=5.0)

    def capture_status(self) -> dict[str, object]:
        if self._process is not None and self._process.poll() is not None:
            return {
                "running": False,
                "exit_code": self._process.returncode,
                "pid": self._process.pid,
            }
        completed = self._run_daemon_cli(["daemon", "status", "--output", "json"], check=False)
        if completed.returncode == 0 and completed.stdout.strip():
            try:
                payload = json.loads(completed.stdout)
            except json.JSONDecodeError:
                payload = {"raw_stdout": completed.stdout}
            if isinstance(payload, dict):
                return payload
        return {
            "running": self._process is not None and self._process.poll() is None,
            "exit_code": None if self._process is None else self._process.returncode,
            "pid": None if self._process is None else self._process.pid,
            "status_exit_code": completed.returncode,
            "status_stderr": completed.stderr,
        }

    def daemon_log_tail(self, *, lines: int = 200) -> str:
        if self._log_path is None or not self._log_path.is_file():
            return ""
        content = self._log_path.read_text(encoding="utf-8", errors="replace")
        tail = content.splitlines()[-lines:]
        return "\n".join(tail) + ("\n" if tail else "")

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    @property
    def pid(self) -> int | None:
        return None if self._process is None else self._process.pid

    def _daemon_status_running(self) -> bool:
        completed = self._run_daemon_cli(["daemon", "status", "--output", "json"], check=False)
        if completed.returncode != 0 or not completed.stdout.strip():
            return False
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            return False
        return daemon_status_payload_is_running(payload)

    def _daemon_start_failure_detail(self, *, timeout: bool = False) -> str:
        parts: list[str] = []
        if timeout:
            parts.append("daemon status did not report running within 10 seconds")
        elif self._process is not None:
            parts.append(f"daemon exited before ready with code {self._process.returncode}")
        status = self._run_daemon_cli(["daemon", "status", "--output", "json"], check=False)
        if status.stdout.strip():
            parts.append(f"daemon status stdout={self.diagnostics.redact(status.stdout.strip())}")
        if status.stderr.strip():
            parts.append(f"daemon status stderr={self.diagnostics.redact(status.stderr.strip())}")
        if status.returncode not in {0, None}:
            parts.append(f"daemon status exit={status.returncode}")
        log_tail = self.daemon_log_tail(lines=50)
        if log_tail.strip():
            parts.append(f"daemon.log tail:\n{self.diagnostics.redact(log_tail.rstrip())}")
        return "; ".join(parts) if parts else "daemon failed to start"

    def _daemon_argv(self, *parts: str) -> list[str]:
        return [str(self.cli_executable), *parts, "--profile", self.profile_name]

    def _run_daemon_cli(self, args: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(self.home_dir)
        env["MULTICA_PROFILE"] = self.profile_name
        completed = subprocess.run(
            self._daemon_argv(*args),
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if check and completed.returncode != 0:
            detail = textwrap.shorten(
                (completed.stderr or completed.stdout or "").strip(),
                width=240,
                placeholder="...",
            )
            raise LiveSetupError("daemon", f"daemon command failed: {detail}")
        return completed

    def _terminate_process(self, *, timeout: float) -> None:
        if self._process is None or self._process.poll() is not None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=5.0)


def _poll_until(
    *,
    deadline_seconds: float,
    interval_seconds: float,
    ready: Callable[[], bool],
) -> bool:
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        if ready():
            return True
        time.sleep(interval_seconds)
    return False


def poll_runtime_online(
    oracle: DirectApiOracle,
    *,
    daemon_id: str,
    deadline_seconds: float = RUNTIME_READY_TIMEOUT_SECONDS,
) -> str:
    runtime_id: str | None = None

    def _ready() -> bool:
        nonlocal runtime_id
        runtime_id = oracle.find_online_opencode_runtime(daemon_id)
        if runtime_id is None:
            return False
        online_matches = [
            entry
            for entry in oracle.list_runtimes_raw()
            if str(entry.get("daemon_id")) == daemon_id
            and str(entry.get("status", "")).lower() in {"online", "ready", "active"}
        ]
        return len(online_matches) == 1

    if not _poll_until(
        deadline_seconds=deadline_seconds,
        interval_seconds=RUNTIME_POLL_INTERVAL_SECONDS,
        ready=_ready,
    ):
        raise LiveSetupError("runtime", f"runtime not ready within {deadline_seconds}s")
    assert runtime_id is not None
    return runtime_id


def poll_runtime_deregistered(
    oracle: DirectApiOracle,
    *,
    daemon_id: str,
    runtime_id: str | None,
    deadline_seconds: float = RUNTIME_DEREGISTER_TIMEOUT_SECONDS,
) -> None:
    if _poll_until(
        deadline_seconds=deadline_seconds,
        interval_seconds=RUNTIME_POLL_INTERVAL_SECONDS,
        ready=lambda: oracle.runtime_absent_or_non_routable(daemon_id, runtime_id),
    ):
        return
    raise LiveSetupError(
        "runtime",
        f"runtime still routable after {deadline_seconds}s for daemon {daemon_id}",
    )
