from __future__ import annotations

import pathlib
import subprocess
import threading

import pytest

from multica_py.client import MulticaClient
from multica_py.config import ClientConfig
from multica_py.enums import CompatibilityPolicy
from multica_py.exceptions import NotFoundError
from scripts.resolve_multica_target import resolve_target
from tests.live._bootstrap import audit_postconditions
from tests.live._live_helpers import (
    LiveTestRun,
    WorkspaceContext,
    create_live_test_run,
    ensure_temp_home,
    label_name,
    remove_temp_home,
    validate_not_real_home,
)
from tests.live.backend import ComposeLifecycle
from tests.live.diagnostics import DiagnosticCollector
from tests.live.session import LiveCase, LiveEnvironment, LiveSession
from tools.live_support.environment import LiveSetupError, load_live_settings

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMP_HOME_BASE = REPO_ROOT / "tests" / "live" / ".live-home"

pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]


def test_primary_label_is_invisible_from_secondary_workspace(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """Primary workspace labels must not appear in secondary workspace list/get."""
    label = live_session.client.labels.create(
        label_name(live_case.unique_name, "iso"), color="#abcdef"
    )
    live_case.defer_cleanup(lambda: live_session.client.labels.delete(label.id))
    secondary_ids = {item.id for item in live_session.client_secondary.labels.list()}
    assert label.id not in secondary_ids
    with pytest.raises(NotFoundError):
        live_session.client_secondary.labels.get(label.id)


def test_primary_project_is_invisible_from_secondary_workspace(
    live_session: LiveSession,
    live_case: LiveCase,
) -> None:
    """Primary workspace projects must not appear in secondary workspace list/get."""
    project = live_session.oracle.create_project(f"{live_case.unique_name}-iso-project")
    project_id = str(project["id"])
    live_case.defer_cleanup(
        live_session.oracle.delete_callback(f"/api/projects/{project_id}", "project"),
    )
    secondary_ids = {item.id for item in live_session.client_secondary.projects.list()}
    assert project_id not in secondary_ids
    with pytest.raises(NotFoundError):
        live_session.client_secondary.projects.get(project_id)


def test_parallel_read_only_calls_keep_workspace_context(
    live_session: LiveSession,
) -> None:
    """Concurrent workspace-scoped label lists must not mix primary/secondary resources."""
    primary_workspace: WorkspaceContext = live_session.primary_workspace
    secondary_workspace: WorkspaceContext = live_session.secondary_workspace
    primary_label = live_session.client.labels.create(
        label_name(primary_workspace.id, "p"),
        color="#111111",
    )
    secondary_label = live_session.client_secondary.labels.create(
        label_name(secondary_workspace.id, "s"),
        color="#222222",
    )
    primary_result: list[str] = []
    secondary_result: list[str] = []
    errors: list[BaseException] = []

    def _read_primary() -> None:
        try:
            primary_result.extend(label.id for label in live_session.client.labels.list())
        except BaseException as exc:
            errors.append(exc)

    def _read_secondary() -> None:
        try:
            secondary_result.extend(
                label.id for label in live_session.client_secondary.labels.list()
            )
        except BaseException as exc:
            errors.append(exc)

    primary_thread = threading.Thread(target=_read_primary)
    secondary_thread = threading.Thread(target=_read_secondary)
    primary_thread.start()
    secondary_thread.start()
    primary_thread.join(timeout=30)
    secondary_thread.join(timeout=30)
    assert not errors
    assert primary_label.id in primary_result
    assert secondary_label.id in secondary_result
    assert primary_label.id not in secondary_result
    assert secondary_label.id not in primary_result
    live_session.client.labels.delete(primary_label.id)
    live_session.client_secondary.labels.delete(secondary_label.id)


def test_primary_client_scope_does_not_break_secondary_client(
    live_environment: LiveEnvironment,
    live_session: LiveSession,
) -> None:
    """Releasing a scoped primary client must not break the secondary client."""
    primary_workspace = live_environment.primary_workspace
    secondary_workspace = live_environment.secondary_workspace
    config = ClientConfig(
        executable=str(live_environment.cli_executable),
        server_url=live_environment.server_url,
        workspace_id=primary_workspace.id,
        profile=primary_workspace.profile_name,
        environment=(("HOME", str(live_environment.home_dir)),),
        compatibility=CompatibilityPolicy.ignore,
    )
    with MulticaClient(config) as scoped_client:
        scoped_client.workspaces.list()
    secondary_ids = {workspace.id for workspace in live_session.client_secondary.workspaces.list()}
    assert secondary_workspace.id in secondary_ids


def _run_failed_session(monkeypatch: pytest.MonkeyPatch) -> tuple[LiveTestRun, pathlib.Path]:
    monkeypatch.setenv("MULTICA_LIVE_READY_TIMEOUT", "10")
    settings = load_live_settings(repo_root=REPO_ROOT)
    resolved = resolve_target(settings.target_file, settings.cli_executable)
    run = create_live_test_run(resolved.target, settings)
    diagnostics = DiagnosticCollector(run.artifact_dir, run.run_id)
    lifecycle = ComposeLifecycle(settings, resolved.target, run, diagnostics)
    home_dir = ensure_temp_home(TEMP_HOME_BASE, f"fail-{run.run_id}")
    validate_not_real_home(home_dir)
    try:
        lifecycle.start()
        subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(lifecycle.compose_file),
                "-p",
                run.compose_project,
                "stop",
                "backend",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        try:
            lifecycle.wait_ready()
        except LiveSetupError:
            pass
        else:
            pytest.fail("expected LiveSetupError when backend is stopped")
    finally:
        lifecycle.teardown()
        remove_temp_home(home_dir)
        audit_postconditions(run, home_dir, managed_compose=True)
    return run, home_dir


def test_failed_run_leaves_no_compose_or_profile_artifacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Forced setup failure must still remove compose resources and temp profile artifacts."""
    run, home_dir = _run_failed_session(monkeypatch)
    ps = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={run.compose_project}", "--format", "{{.Names}}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    names = [line for line in ps.stdout.splitlines() if line.strip()]
    assert names == []
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
    assert volume_names == []
    assert not home_dir.exists()
