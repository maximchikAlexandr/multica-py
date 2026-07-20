from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

from multica_py.client import MulticaClient
from scripts.resolve_multica_target import ResolvedTarget, build_version_report, resolve_target
from tests.live.backend import ComposeLifecycle, is_ready, probe_readiness
from tests.live.diagnostics import DiagnosticCollector
from tests.live.environment import (
    LiveSetupError,
    LiveTestEnvironment,
    LiveTestRun,
    WorkspaceContext,
    create_live_test_run,
    load_live_settings,
    profile_config_path,
    validate_not_real_home,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]


def test_readyz_reports_backend_ready(
    live_environment: LiveTestEnvironment,
    compatibility_target: ResolvedTarget,
    diagnostic_collector: DiagnosticCollector,
) -> None:
    """Smoke-test readiness, verified target, and CLI version reporting."""
    result = probe_readiness(live_environment.readiness_endpoint)
    assert is_ready(result)
    assert (
        compatibility_target.cli_version_actual == compatibility_target.target.cli_version_expected
    )
    target_path = diagnostic_collector.artifact_dir / "target.json"
    assert target_path.is_file()
    report = json.loads(target_path.read_text(encoding="utf-8"))
    expected = build_version_report(compatibility_target)
    assert report["cli_version_actual"] == expected["cli_version_actual"]
    assert report["cli_version_expected"] == expected["cli_version_expected"]
    assert report["upstream_ref"] == compatibility_target.target.upstream_ref


def test_workspaces_list_includes_primary_bootstrap_workspace(
    live_client: MulticaClient,
    primary_workspace: WorkspaceContext,
) -> None:
    """Smoke-test SDK workspace list includes the primary bootstrap workspace."""
    workspaces = live_client.workspaces.list()
    workspace_ids = {workspace.id for workspace in workspaces}
    assert primary_workspace.id in workspace_ids


def test_cli_profile_is_isolated_from_user_home(live_environment: LiveTestEnvironment) -> None:
    """Smoke-test that the session uses a temp HOME and not the user profile."""
    validate_not_real_home(live_environment.home_dir)
    assert live_environment.home_dir.resolve() != pathlib.Path.home().resolve()
    profile_path = profile_config_path(live_environment.home_dir, live_environment.profile_name)
    assert profile_path.is_file()
    real_profile = (
        pathlib.Path.home()
        / ".multica"
        / "profiles"
        / live_environment.profile_name
        / "config.json"
    )
    assert not real_profile.exists()


def _stop_compose_service(
    lifecycle: ComposeLifecycle,
    compose_project: str,
    service: str,
) -> None:
    argv = [
        "docker",
        "compose",
        "-f",
        str(lifecycle.compose_file),
        "-p",
        compose_project,
        "stop",
        service,
    ]
    completed = subprocess.run(
        argv,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise LiveSetupError("compose", f"docker compose stop failed: {detail}")


def _run_not_ready_setup(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[LiveTestRun, DiagnosticCollector, ComposeLifecycle]:
    monkeypatch.setenv("MULTICA_LIVE_READY_TIMEOUT", "10")
    settings = load_live_settings(repo_root=REPO_ROOT)
    resolved = resolve_target(settings.target_file, settings.cli_executable)
    run = create_live_test_run(resolved.target, settings)
    diagnostics = DiagnosticCollector(run.artifact_dir, run.run_id)
    lifecycle = ComposeLifecycle(settings, resolved.target, run, diagnostics)
    return run, diagnostics, lifecycle


@pytest.mark.destructive
def test_not_ready_backend_raises_live_setup_error_with_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Negative setup: stopped backend must fail readiness with diagnostics."""
    run, _diagnostics, lifecycle = _run_not_ready_setup(monkeypatch)
    try:
        lifecycle.start()
        _stop_compose_service(lifecycle, run.compose_project, "backend")
        with pytest.raises(LiveSetupError) as exc_info:
            lifecycle.wait_ready()
        assert exc_info.value.stage == "readyz"
        assert "last status" in str(exc_info.value)
        assert (run.artifact_dir / "compose-ps.txt").is_file()
        assert (run.artifact_dir / "backend.log").is_file()
    finally:
        lifecycle.teardown()
