"""Bootstrap helper for the live conftest.

Keeps the heavy backend wiring out of ``conftest.py`` so the four public
fixtures plus the canary gate fit within the 300-logical-line budget.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import time
from dataclasses import asdict
from typing import Any, cast

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from scripts.resolve_multica_target import build_version_report, resolve_target
from tests.live._live_helpers import (
    LiveTestEnvironment,
    create_live_run_context,
    create_live_test_run,
    ensure_temp_home,
    load_agent_sandbox_settings,
    profile_name_for_run,
    validate_not_real_home,
)
from tests.live.backend import ComposeLifecycle, setup_sandbox_session
from tests.live.diagnostics import DiagnosticCollector
from tests.live.registry import ResourceRegistry
from tests.live.session import LiveEnvironment
from tools.live_support.environment import (
    LiveSetupError,
    load_live_settings,
    load_opencode_canary_settings,
    parse_environment,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMP_HOME_BASE = REPO_ROOT / "tests" / "live" / ".live-home"


def _build_live_client(
    *,
    cli_executable: pathlib.Path,
    server_url: str,
    home_dir: pathlib.Path,
    workspace: Any,
) -> MulticaClient:
    return MulticaClient(
        ClientConfig(
            executable=str(cli_executable),
            server_url=server_url,
            workspace_id=workspace.id,
            profile=workspace.profile_name,
            environment=(("HOME", str(home_dir)),),
        )
    )


def audit_postconditions(
    run: Any,
    home_dir: pathlib.Path,
    managed_compose: bool,
) -> None:
    """Verify compose and temp HOME cleanup postconditions."""
    validate_not_real_home(home_dir)
    if home_dir.exists():
        raise LiveSetupError("profile", f"temporary HOME still exists after cleanup: {home_dir}")
    if not managed_compose:
        return
    filter_arg = f"name={run.compose_project}"
    ps = subprocess.run(
        ["docker", "ps", "-a", "--filter", filter_arg, "--format", "{{.Names}}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    names = [line for line in ps.stdout.splitlines() if line.strip()]
    if names:
        raise LiveSetupError("compose", f"compose containers remain: {names}")
    volumes = subprocess.run(
        ["docker", "volume", "ls", "--filter", filter_arg, "--format", "{{.Name}}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    volume_names = [line for line in volumes.stdout.splitlines() if line.strip()]
    if volume_names:
        raise LiveSetupError("compose", f"compose volumes remain: {volume_names}")


def bootstrap_live_environment(
    repo_root: pathlib.Path,
    pytestconfig: Any,
) -> tuple[LiveEnvironment, ComposeLifecycle, Any, pathlib.Path, bool, DiagnosticCollector]:
    """Start the live backend, bootstrap identity, and assemble a LiveEnvironment."""
    settings = load_live_settings(repo_root=repo_root)
    target = resolve_target(
        settings.target_file,
        settings.cli_executable,
        upstream_dir=settings.upstream_dir,
    )
    run = create_live_test_run(
        target.target,
        settings,
        run_id=os.environ.get("MULTICA_LIVE_RUN_ID"),
    )
    diagnostics = DiagnosticCollector(run.artifact_dir, run.run_id)
    diagnostics.write_json("target.json", cast("dict[str, object]", build_version_report(target)))
    pytestconfig._live_diagnostic_collector = diagnostics
    lifecycle = ComposeLifecycle(settings, target.target, run, diagnostics)
    managed_compose = settings.existing_url is None
    home_dir = ensure_temp_home(TEMP_HOME_BASE, run.run_id)
    validate_not_real_home(home_dir)
    server_url = settings.existing_url or lifecycle.server_url
    compose_files: tuple[pathlib.Path, ...] = ()
    env_ready_seconds: float | None = None
    if managed_compose:
        env_start = time.monotonic()
        lifecycle.start()
        compose_files = (lifecycle.compose_file,)
        lifecycle.wait_ready()
        env_ready_seconds = round(time.monotonic() - env_start, 2)
    diagnostics.write_json(
        "run.json",
        {
            "run_id": run.run_id,
            "suite_profile": run.suite_profile,
            "compose_project": run.compose_project,
            "session_started_at": time.time(),
            **(
                {"environment_ready_seconds": env_ready_seconds}
                if env_ready_seconds is not None
                else {}
            ),
        },
    )
    live_test_env = LiveTestEnvironment(
        server_url=server_url,
        compose_project=run.compose_project,
        compose_files=compose_files,
        home_dir=home_dir,
        profile_name=profile_name_for_run(run.run_id),
        cli_executable=target.cli_executable,
        readiness_endpoint=f"{server_url}/readyz",
        readiness_timeout_seconds=settings.ready_timeout_seconds,
        managed_compose=managed_compose,
    )
    secret_values: list[str] = []
    session = setup_sandbox_session(
        server_url=live_test_env.server_url,
        run_id=run.run_id,
        cli_executable=live_test_env.cli_executable,
        home_dir=live_test_env.home_dir,
        profile_name=live_test_env.profile_name,
        secret_values=secret_values,
    )
    diagnostics.register_secrets(secret_values)
    assert session.secondary_workspace is not None
    env_parsed = parse_environment()
    try:
        canary_settings = load_opencode_canary_settings()
    except Exception:
        canary_settings = None
    env = LiveEnvironment(
        **asdict(live_test_env),
        api_key=env_parsed.api_key,
        workspace=env_parsed.workspace,
        profile=env_parsed.profile,
        extra=env_parsed.extra,
        base_url=server_url,
        canary=canary_settings is not None,
        run_id=run.run_id,
        target=target,
        diagnostics=diagnostics,
        resource_registry=ResourceRegistry(),
        identity=session.identity,
        primary_workspace=session.workspace,
        secondary_workspace=session.secondary_workspace,
        client=session.client,
        client_secondary=_build_live_client(
            cli_executable=live_test_env.cli_executable,
            server_url=server_url,
            home_dir=live_test_env.home_dir,
            workspace=session.secondary_workspace,
        ),
        oracle=session.oracle,
        agent_sandbox_settings=load_agent_sandbox_settings(repo_root=repo_root),
        agent_sandbox_run_context=create_live_run_context(
            run_id=run.run_id,
            artifact_root=settings.artifact_dir,
            temp_parent=repo_root / "tests" / "live" / ".sandbox-temp",
        ),
        agent_sandbox_target_report=cast("dict[str, object]", build_version_report(target)),
        canary_settings=canary_settings,
    )
    return env, lifecycle, settings, home_dir, managed_compose, diagnostics
