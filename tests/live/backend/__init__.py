"""Backend lifecycle, compose orchestration, and bootstrap for live tests."""

import subprocess
import time

import httpx

from tests.live.backend.client import BootstrapApiClient, SandboxSession, setup_sandbox_session
from tests.live.backend.compose import (
    READINESS_INTERVALS,
    ComposeLifecycle,
    ImagePolicy,
    ReadinessResult,
    allocate_loopback_port,
    capture_compose_diagnostics,
    compose_argv,
    compose_down_argv,
    compose_up_argv,
    is_ready,
    probe_readiness,
)
from tests.live.backend.lifecycle import (
    DAEMON_READY_TIMEOUT_SECONDS,
    RUNTIME_DEREGISTER_TIMEOUT_SECONDS,
    RUNTIME_POLL_INTERVAL_SECONDS,
    RUNTIME_READY_TIMEOUT_SECONDS,
    TERMINAL_RUN_STATUSES,
    DaemonLifecycle,
    daemon_status_payload_is_running,
    poll_runtime_deregistered,
    poll_runtime_online,
)

__all__ = [
    "DAEMON_READY_TIMEOUT_SECONDS",
    "READINESS_INTERVALS",
    "RUNTIME_DEREGISTER_TIMEOUT_SECONDS",
    "RUNTIME_POLL_INTERVAL_SECONDS",
    "RUNTIME_READY_TIMEOUT_SECONDS",
    "TERMINAL_RUN_STATUSES",
    "BootstrapApiClient",
    "ComposeLifecycle",
    "DaemonLifecycle",
    "ImagePolicy",
    "ReadinessResult",
    "SandboxSession",
    "allocate_loopback_port",
    "capture_compose_diagnostics",
    "compose_argv",
    "compose_down_argv",
    "compose_up_argv",
    "daemon_status_payload_is_running",
    "is_ready",
    "poll_runtime_deregistered",
    "poll_runtime_online",
    "probe_readiness",
    "setup_sandbox_session",
]
