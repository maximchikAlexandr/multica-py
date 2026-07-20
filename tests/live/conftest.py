from __future__ import annotations

import json
import os
import pathlib
import subprocess
import time
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import cast

import pytest

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy
from multica_py.exceptions import CommandExecutionError
from multica_py.models.labels import Label
from scripts.resolve_multica_target import ResolvedTarget, build_version_report, resolve_target
from tests.live.backend import ComposeLifecycle, allocate_loopback_port, setup_sandbox_session
from tests.live.diagnostics import DiagnosticCollector
from tests.live.environment import (
    AgentSandboxSettings,
    LiveContext,
    LiveRunContext,
    LiveSettings,
    LiveSetupError,
    LiveTestEnvironment,
    LiveTestRun,
    OpenCodeCanarySettings,
    TestIdentity,
    WorkspaceContext,
    create_live_run_context,
    create_live_test_run,
    ensure_temp_home,
    label_name,
    load_agent_sandbox_settings,
    load_live_settings,
    load_opencode_canary_settings,
    profile_name_for_run,
    remove_temp_home,
    resource_prefix,
    skip_if_canary_environment_incomplete,
    validate_not_real_home,
    write_cli_profile,
)
from tests.live.oracle import DirectApiOracle
from tests.live.resources import (
    AgentSandboxOutcome,
    ResourceRegistry,
    execute_agent_sandbox_workflow,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMP_HOME_BASE = REPO_ROOT / "tests" / "live" / ".live-home"
INVALID_PAT_TOKEN = "mpy-live-invalid-pat-token"
MISSING_RESOURCE_ID = "00000000-0000-0000-0000-000000000000"


def _session_includes_canary(request: pytest.FixtureRequest) -> bool:
    for item in request.session.items:
        if item.get_closest_marker("live_opencode_canary") is not None:
            return True
    return False


@pytest.fixture(scope="session")
def canary_environment_gate(request: pytest.FixtureRequest) -> None:
    """Skip canary tests before infrastructure when configuration is incomplete."""
    if _session_includes_canary(request):
        skip_if_canary_environment_incomplete()


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    """Bootstrap outputs for one live session."""

    identity: TestIdentity
    primary: WorkspaceContext
    secondary: WorkspaceContext


@pytest.fixture(scope="session")
def live_settings(
    pytestconfig: pytest.Config,
    canary_environment_gate: None,
) -> LiveSettings:
    """Load validated live settings from the environment."""
    settings = load_live_settings(repo_root=REPO_ROOT)
    pytestconfig._live_diagnostic_collector = None  # type: ignore[attr-defined]
    return settings


@pytest.fixture(scope="session")
def compatibility_target(live_settings: LiveSettings) -> ResolvedTarget:
    """Resolve and verify the compatibility target manifest."""
    return resolve_target(
        live_settings.target_file,
        live_settings.cli_executable,
        upstream_dir=live_settings.upstream_dir,
    )


@pytest.fixture(scope="session")
def live_test_run(live_settings: LiveSettings, compatibility_target: ResolvedTarget) -> LiveTestRun:
    """Create session run metadata after target verification."""
    run_id = os.environ.get("MULTICA_LIVE_RUN_ID")
    return create_live_test_run(
        compatibility_target.target,
        live_settings,
        run_id=run_id,
    )


@pytest.fixture(scope="session")
def diagnostic_collector(
    live_test_run: LiveTestRun,
    pytestconfig: pytest.Config,
) -> DiagnosticCollector:
    """Create the session diagnostic collector."""
    collector = DiagnosticCollector(live_test_run.artifact_dir, live_test_run.run_id)
    pytestconfig._live_diagnostic_collector = collector  # type: ignore[attr-defined]
    return collector


@pytest.fixture(scope="session")
def resource_registry() -> ResourceRegistry:
    """Return the session resource registry."""
    return ResourceRegistry()


@pytest.fixture(scope="session")
def live_environment(
    live_settings: LiveSettings,
    compatibility_target: ResolvedTarget,
    live_test_run: LiveTestRun,
    diagnostic_collector: DiagnosticCollector,
    resource_registry: ResourceRegistry,
    pytestconfig: pytest.Config,
    canary_environment_gate: None,
) -> Generator[LiveTestEnvironment, None, None]:
    """Start or attach to the live backend environment."""
    lifecycle = ComposeLifecycle(
        live_settings,
        compatibility_target.target,
        live_test_run,
        diagnostic_collector,
    )
    managed_compose = live_settings.existing_url is None
    home_dir = ensure_temp_home(TEMP_HOME_BASE, live_test_run.run_id)
    validate_not_real_home(home_dir)
    profile_name = profile_name_for_run(live_test_run.run_id)
    compose_files: tuple[pathlib.Path, ...] = ()
    environment_ready_seconds: float | None = None
    diagnostic_collector.write_json(
        "target.json",
        cast("dict[str, object]", build_version_report(compatibility_target)),
    )
    server_url = live_settings.existing_url or lifecycle.server_url
    try:
        if managed_compose:
            env_start = time.monotonic()
            lifecycle.start()
            compose_files = (lifecycle.compose_file,)
            lifecycle.wait_ready()
            environment_ready_seconds = time.monotonic() - env_start
        run_payload = {
            "run_id": live_test_run.run_id,
            "suite_profile": live_test_run.suite_profile,
            "compose_project": live_test_run.compose_project,
            "session_started_at": time.time(),
        }
        if environment_ready_seconds is not None:
            run_payload["environment_ready_seconds"] = round(environment_ready_seconds, 2)
        diagnostic_collector.write_json("run.json", run_payload)
        environment = LiveTestEnvironment(
            server_url=server_url,
            compose_project=live_test_run.compose_project,
            compose_files=compose_files,
            home_dir=home_dir,
            profile_name=profile_name,
            cli_executable=compatibility_target.cli_executable,
            readiness_endpoint=f"{server_url}/readyz",
            readiness_timeout_seconds=live_settings.ready_timeout_seconds,
            managed_compose=managed_compose,
        )
        yield environment
    finally:
        cleanup_failures = resource_registry.cleanup_all()
        cleanup_failures.extend(lifecycle.teardown())
        if not live_settings.keep_env:
            remove_temp_home(home_dir)
            try:
                audit_postconditions(live_test_run, home_dir, managed_compose)
            except LiveSetupError as exc:
                cleanup_failures.append({"key": exc.stage, "message": str(exc)})
        if cleanup_failures:
            diagnostic_collector.record_cleanup({"failures": cleanup_failures})
        oracle = getattr(pytestconfig, "_live_api_oracle", None)
        if oracle is not None:
            oracle.close()
            pytestconfig._live_api_oracle = None  # type: ignore[attr-defined]


@pytest.fixture(scope="session")
def bootstrap_result(
    live_environment: LiveTestEnvironment,
    live_test_run: LiveTestRun,
    diagnostic_collector: DiagnosticCollector,
) -> BootstrapResult:
    """Bootstrap authenticated test identity and workspaces."""
    secret_values: list[str] = []
    session = setup_sandbox_session(
        server_url=live_environment.server_url,
        run_id=live_test_run.run_id,
        cli_executable=live_environment.cli_executable,
        home_dir=live_environment.home_dir,
        profile_name=live_environment.profile_name,
        secret_values=secret_values,
    )
    diagnostic_collector.register_secrets(secret_values)
    assert session.secondary_workspace is not None
    return BootstrapResult(
        identity=session.identity,
        primary=session.workspace,
        secondary=session.secondary_workspace,
    )


@pytest.fixture(scope="session")
def test_identity(bootstrap_result: BootstrapResult) -> TestIdentity:
    """Return the authenticated test identity."""
    return bootstrap_result.identity


@pytest.fixture(scope="session")
def primary_workspace(bootstrap_result: BootstrapResult) -> WorkspaceContext:
    """Return the primary bootstrap workspace."""
    return bootstrap_result.primary


@pytest.fixture(scope="session")
def secondary_workspace(bootstrap_result: BootstrapResult) -> WorkspaceContext:
    """Return the secondary bootstrap workspace."""
    return bootstrap_result.secondary


@pytest.fixture(scope="session")
def api_oracle(
    live_environment: LiveTestEnvironment,
    test_identity: TestIdentity,
    primary_workspace: WorkspaceContext,
    pytestconfig: pytest.Config,
) -> Generator[DirectApiOracle, None, None]:
    """Yield the direct HTTP oracle bound to the primary workspace.

    The client is closed after resource registry cleanup in ``live_environment``
    so delete callbacks can still use the oracle HTTP session.
    """
    oracle = DirectApiOracle(
        live_environment.server_url,
        workspace_id=primary_workspace.id,
        pat=test_identity.pat.reveal(),
    )
    pytestconfig._live_api_oracle = oracle  # type: ignore[attr-defined]
    yield oracle


def _build_client(
    live_environment: LiveTestEnvironment,
    workspace: WorkspaceContext,
) -> MulticaClient:
    config = ClientConfig(
        executable=str(live_environment.cli_executable),
        server_url=live_environment.server_url,
        workspace_id=workspace.id,
        profile=workspace.profile_name,
        environment=(("HOME", str(live_environment.home_dir)),),
    )
    return MulticaClient(config)


@pytest.fixture(scope="session")
def live_client(
    live_environment: LiveTestEnvironment,
    primary_workspace: WorkspaceContext,
) -> MulticaClient:
    """Return the primary SDK client."""
    return _build_client(live_environment, primary_workspace)


@pytest.fixture(scope="session")
def secondary_live_client(
    live_environment: LiveTestEnvironment,
    secondary_workspace: WorkspaceContext,
) -> MulticaClient:
    """Return the secondary SDK client."""
    return _build_client(live_environment, secondary_workspace)


@pytest.fixture
def resource_name(live_test_run: LiveTestRun, request: pytest.FixtureRequest) -> str:
    """Return a unique resource prefix for the current test."""
    fragment = request.node.name.replace("[", "-").replace("]", "")
    return resource_prefix(live_test_run.run_id, fragment)


@pytest.fixture
def register_resource(resource_registry: ResourceRegistry) -> Callable[..., None]:
    """Convenience wrapper for resource registration."""

    def _register(*, key: str, cleanup: Callable[[], None]) -> None:
        resource_registry.defer(key=key, cleanup=cleanup)

    return _register


@pytest.fixture
def live_ctx(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource: Callable[..., None],
    test_identity: TestIdentity,
) -> LiveContext:
    """Return a LiveContext bundling client, oracle, register, and identity."""
    return LiveContext(
        client=live_client,
        oracle=api_oracle,
        register_resource=register_resource,
        identity=test_identity,
    )


@pytest.fixture(scope="session")
def missing_resource_id() -> str:
    """Return a stable missing resource identifier for not-found tests."""
    return MISSING_RESOURCE_ID


@pytest.fixture(scope="session")
def closed_port_server_url() -> str:
    """Return a loopback URL whose port has no listening backend."""
    return f"http://127.0.0.1:{allocate_loopback_port()}"


@pytest.fixture(scope="session")
def invalid_pat_client(
    live_environment: LiveTestEnvironment,
    primary_workspace: WorkspaceContext,
    live_test_run: LiveTestRun,
) -> MulticaClient:
    """Return an SDK client configured with an invalid personal access token."""
    invalid_profile = f"invalid-{live_test_run.run_id}"
    write_cli_profile(
        live_environment.home_dir,
        invalid_profile,
        server_url=live_environment.server_url,
        app_url=live_environment.server_url,
        workspace_id=primary_workspace.id,
        token=INVALID_PAT_TOKEN,
    )
    config = ClientConfig(
        executable=str(live_environment.cli_executable),
        server_url=live_environment.server_url,
        workspace_id=primary_workspace.id,
        profile=invalid_profile,
        environment=(("HOME", str(live_environment.home_dir)),),
        compatibility=CompatibilityPolicy.ignore,
    )
    return MulticaClient(config)


@pytest.fixture(scope="session")
def closed_port_client(
    live_environment: LiveTestEnvironment,
    primary_workspace: WorkspaceContext,
    closed_port_server_url: str,
) -> MulticaClient:
    """Return an SDK client pointed at a closed loopback port."""
    config = ClientConfig(
        executable=str(live_environment.cli_executable),
        server_url=closed_port_server_url,
        workspace_id=primary_workspace.id,
        profile=primary_workspace.profile_name,
        environment=(("HOME", str(live_environment.home_dir)),),
        compatibility=CompatibilityPolicy.ignore,
    )
    return MulticaClient(config)


@pytest.fixture
def primary_workspace_label(
    live_client: MulticaClient,
    resource_name: str,
    register_resource: Callable[..., None],
) -> Label:
    """Create one label in the primary workspace for access-collapse tests."""
    label = live_client.labels.create(label_name(resource_name, "pri"), color="#336699")
    register_resource(
        key=f"label-{label.id}",
        cleanup=lambda: live_client.labels.delete(label.id),
    )
    return label


@pytest.fixture
def assert_no_secret_leak(
    diagnostic_collector: DiagnosticCollector,
) -> Callable[[], None]:
    """Assert that diagnostics contain no registered secret values."""

    def _assert() -> None:
        diagnostic_collector.assert_no_secret_leak()

    return _assert


@pytest.fixture(scope="session")
def agent_sandbox_settings() -> AgentSandboxSettings:
    """Return validated deterministic agent sandbox settings."""
    return load_agent_sandbox_settings(repo_root=REPO_ROOT)


@pytest.fixture
def agent_sandbox_run_context(
    live_test_run: LiveTestRun,
    live_settings: LiveSettings,
) -> LiveRunContext:
    """Create isolated temp paths for one agent sandbox run."""
    return create_live_run_context(
        run_id=live_test_run.run_id,
        artifact_root=live_settings.artifact_dir,
        temp_parent=REPO_ROOT / "tests" / "live" / ".sandbox-temp",
    )


@pytest.fixture
def agent_sandbox_target_report(compatibility_target: ResolvedTarget) -> dict[str, object]:
    """Return pinned target metadata for sandbox diagnostics."""
    return cast("dict[str, object]", build_version_report(compatibility_target))


@pytest.fixture
def run_agent_sandbox(
    live_environment: LiveTestEnvironment,
    live_test_run: LiveTestRun,
    agent_sandbox_run_context: LiveRunContext,
    agent_sandbox_settings: AgentSandboxSettings,
    diagnostic_collector: DiagnosticCollector,
    agent_sandbox_target_report: dict[str, object],
) -> Callable[..., AgentSandboxOutcome]:
    """Execute the agent sandbox workflow with optional overrides."""
    return _make_sandbox_runner(
        live_environment=live_environment,
        live_test_run=live_test_run,
        run_context=agent_sandbox_run_context,
        default_settings=agent_sandbox_settings,
        diagnostic_collector=diagnostic_collector,
        target_report=agent_sandbox_target_report,
    )


@pytest.fixture(scope="session")
def opencode_canary_settings(canary_environment_gate: None) -> OpenCodeCanarySettings:
    """Return validated real OpenCode canary settings."""
    return load_opencode_canary_settings()


@pytest.fixture
def run_opencode_canary(
    live_environment: LiveTestEnvironment,
    live_test_run: LiveTestRun,
    agent_sandbox_run_context: LiveRunContext,
    opencode_canary_settings: OpenCodeCanarySettings,
    diagnostic_collector: DiagnosticCollector,
    agent_sandbox_target_report: dict[str, object],
) -> Callable[[], AgentSandboxOutcome]:
    """Execute the real OpenCode canary workflow."""
    return _make_sandbox_runner(
        live_environment=live_environment,
        live_test_run=live_test_run,
        run_context=agent_sandbox_run_context,
        default_settings=opencode_canary_settings.to_sandbox_settings(),
        diagnostic_collector=diagnostic_collector,
        target_report=agent_sandbox_target_report,
        canary_settings=opencode_canary_settings,
    )


def _make_sandbox_runner(
    *,
    live_environment: LiveTestEnvironment,
    live_test_run: LiveTestRun,
    run_context: LiveRunContext,
    default_settings: AgentSandboxSettings,
    diagnostic_collector: DiagnosticCollector,
    target_report: dict[str, object],
    canary_settings: OpenCodeCanarySettings | None = None,
) -> Callable[..., AgentSandboxOutcome]:
    def _run(
        *,
        settings: AgentSandboxSettings | None = None,
        inject_cleanup_failure: str | None = None,
        expect_success: bool = True,
    ) -> AgentSandboxOutcome:
        return execute_agent_sandbox_workflow(
            live_environment=live_environment,
            run_context=run_context,
            sandbox_settings=settings or default_settings,
            diagnostics=diagnostic_collector,
            target_report=target_report,
            compose_project=live_test_run.compose_project,
            compose_files=live_environment.compose_files,
            inject_cleanup_failure=inject_cleanup_failure,
            expect_success=expect_success,
            canary_settings=canary_settings,
        )

    return _run


def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]) -> None:
    """Classify setup, test, and teardown failures for diagnostics."""
    collector = getattr(item.config, "_live_diagnostic_collector", None)
    if collector is None:
        return
    if call.excinfo is None:
        return
    excinfo = call.excinfo
    exc_type = excinfo.type.__name__ if excinfo.type is not None else "Exception"
    message = str(excinfo.value)
    failure_stage: str = call.when
    operation: str | None = None
    exit_code: int | None = None
    resource: str | None = None
    if excinfo.errisinstance(LiveSetupError):
        setup_error = excinfo.value
        assert isinstance(setup_error, LiveSetupError)
        failure_stage = setup_error.stage
    if excinfo.errisinstance(CommandExecutionError):
        command_error = excinfo.value
        assert isinstance(command_error, CommandExecutionError)
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
    oracle = getattr(session.config, "_live_api_oracle", None)
    if oracle is not None:
        oracle.close()
        session.config._live_api_oracle = None  # type: ignore[attr-defined]
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


def audit_postconditions(
    run: LiveTestRun,
    home_dir: pathlib.Path,
    managed_compose: bool,
) -> None:
    """Verify compose and temp HOME cleanup postconditions."""
    validate_not_real_home(home_dir)
    if home_dir.exists():
        msg = f"temporary HOME still exists after cleanup: {home_dir}"
        raise LiveSetupError("profile", msg)
    if not managed_compose:
        return
    ps = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={run.compose_project}", "--format", "{{.Names}}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    names = [line for line in ps.stdout.splitlines() if line.strip()]
    if names:
        raise LiveSetupError("compose", f"compose containers remain: {names}")
    volumes = subprocess.run(
        [
            "docker",
            "volume",
            "ls",
            "--filter",
            f"name={run.compose_project}",
            "--format",
            "{{.Name}}",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    volume_names = [line for line in volumes.stdout.splitlines() if line.strip()]
    if volume_names:
        raise LiveSetupError("compose", f"compose volumes remain: {volume_names}")
