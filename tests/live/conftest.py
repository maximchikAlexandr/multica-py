from __future__ import annotations

import json
import pathlib
import time
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any, cast

import pytest

from multica_py.exceptions import CommandExecutionError
from tests.live._bootstrap import audit_postconditions, bootstrap_live_environment
from tests.live.session import LiveCase, LiveEnvironment, LiveSession, SandboxSession
from tools.live_support.environment import LiveSetupError

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _session_includes_canary(request: pytest.FixtureRequest) -> bool:
    for item in request.session.items:
        if item.get_closest_marker("live_opencode_canary") is not None:
            return True
    return False


@pytest.fixture(scope="session")
def canary_environment_gate(request: pytest.FixtureRequest) -> None:
    """Skip canary tests when configuration is incomplete."""
    if _session_includes_canary(request):
        from tests.live._live_helpers import skip_if_canary_environment_incomplete

        skip_if_canary_environment_incomplete()


@pytest.fixture(scope="session")
def live_environment(
    canary_environment_gate: None,
    pytestconfig: pytest.Config,
) -> Any:
    """Session-scoped live environment: backend, identity, workspaces, diagnostics, helpers."""
    env, lifecycle, settings, home_dir, managed_compose, diagnostics = bootstrap_live_environment(
        REPO_ROOT, pytestconfig
    )
    compose_project = env.compose_project
    run = SimpleNamespace(compose_project=compose_project)
    cleanup_failures: list[dict[str, str]] = []
    try:
        yield env
    finally:
        cleanup_failures.extend(lifecycle.teardown())
        if env.oracle is not None:
            env.oracle.close()
        if not settings.keep_env:
            from tests.live._live_helpers import remove_temp_home

            remove_temp_home(home_dir)
            try:
                audit_postconditions(run, home_dir, managed_compose)
            except LiveSetupError as exc:
                cleanup_failures.append({"key": exc.stage, "message": str(exc)})
        if cleanup_failures:
            diagnostics.record_cleanup({"failures": cleanup_failures})


@pytest.fixture
def live_session(live_environment: LiveEnvironment) -> Any:
    """Function-scoped session with shared API client and convenience accessors."""
    with LiveSession(live_environment) as session:
        yield session


@pytest.fixture
def live_case(request: pytest.FixtureRequest) -> Iterator[LiveCase]:
    """Per-test data with a unique name and the resolved profile marker."""
    profile = "live_smoke"
    if request.node.get_closest_marker("live_extended") is not None:
        profile = "live_extended"
    if request.node.get_closest_marker("live_opencode_canary") is not None:
        profile = "live_opencode_canary"
    with LiveCase(unique_name=f"live-{request.node.name}", profile=profile) as lc:
        yield lc


@pytest.fixture
def sandbox_session(
    live_environment: LiveEnvironment,
    tmp_path: pathlib.Path,
) -> Any:
    """Sandbox session with a per-test workspace under tmp_path."""
    workspace = tmp_path / "sandbox-workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    with SandboxSession(live_environment, workspace) as session:
        yield session


def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]) -> None:
    """Classify setup, test, and teardown failures for diagnostics."""
    collector = getattr(item.config, "_live_diagnostic_collector", None)
    if collector is None or call.excinfo is None:
        return
    excinfo = call.excinfo
    exc_type = excinfo.type.__name__ if excinfo.type is not None else "Exception"
    message = str(excinfo.value)
    failure_stage: str = call.when
    operation: str | None = None
    exit_code: int | None = None
    resource: str | None = None
    if excinfo.errisinstance(LiveSetupError):
        failure_stage = cast("LiveSetupError", excinfo.value).stage
    if excinfo.errisinstance(CommandExecutionError):
        command_error = cast("CommandExecutionError", excinfo.value)
        exit_code = command_error.exit_code
        if command_error.argv:
            operation = " ".join(command_error.argv)
            if len(command_error.argv) >= 2:
                resource = command_error.argv[1]
    collector.record_failure(
        stage=failure_stage,
        exc_type=exc_type,
        message=message,
        operation=operation,
        exit_code=exit_code,
        resource=resource,
    )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Record test-phase timing metadata and enforce cleanup/secret gates."""
    collector = getattr(session.config, "_live_diagnostic_collector", None)
    if collector is None:
        return
    run_path = collector.artifact_dir / "run.json"
    if run_path.is_file():
        payload = json.loads(run_path.read_text(encoding="utf-8"))
        started_at = payload.get("session_started_at")
        if isinstance(started_at, (int, float)):
            payload["test_phase_seconds"] = round(time.time() - float(started_at), 2)
            collector.write_json("run.json", payload)
    collector.write_secret_scan_report()
    if collector.scan_artifact_dir() > 0:
        session.exitstatus = 1
    if collector.cleanup_failed:
        session.exitstatus = 1
