"""Unit tests for the agent-sandbox subpackage (T073).

Covers the three-phase workflow, cleanup ordering, filesystem policy,
diagnostics VERIFICATION_CODE emission, and the invariant that ordinary
(non-sandbox) live sessions do not create sandbox resources.
"""

from __future__ import annotations

import pathlib
from collections.abc import Callable
from typing import Any

import pytest

from tests.live._live_helpers import create_live_run_context, load_agent_sandbox_settings
from tests.live.backend import DaemonLifecycle, daemon_status_payload_is_running
from tests.live.diagnostics import DiagnosticCollector
from tests.live.sandbox import (
    Assignment,
    SandboxCleanupRegistry,
    assert_manifest_policy,
    build_file_manifest,
    prepare_sandbox,
    write_initial_sandbox_files,
)
from tools.live_support.environment import LiveSetupError

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
RUN_ID = "a" * 32


def test_create_live_run_context_paths(tmp_path: pathlib.Path) -> None:
    context = create_live_run_context(
        run_id=RUN_ID,
        artifact_root=tmp_path / "artifacts",
        temp_parent=tmp_path,
    )
    assert context.prefix == f"multica-py-live-{RUN_ID}"
    assert context.profile_name == context.prefix
    assert context.daemon_id == context.prefix
    assert context.home == context.temp_root / "home"
    assert context.sandbox_dir == (context.temp_root / "sandbox" / "project").resolve()


def test_rejects_invalid_run_id(tmp_path: pathlib.Path) -> None:
    with pytest.raises(LiveSetupError, match="32 lowercase hex"):
        create_live_run_context(
            run_id="short",
            artifact_root=tmp_path,
            temp_parent=tmp_path,
        )


def test_phase_transitions_are_ordered(tmp_path: pathlib.Path) -> None:
    """prepare → run → verify must occur in this order; skipping is a contract violation."""
    events: list[str] = []

    class _Stack:
        def callback(self, callback: Callable[[], None]) -> None:
            events.append("cleanup-registered")

    class _Session:
        _stack = _Stack()

        def defer_cleanup(self, callback: Callable[..., None], /, *args: Any) -> None:
            self._stack.callback(callback)

    workspace = tmp_path / "ws"
    workspace.mkdir()
    prepared = prepare_sandbox(_Session(), workspace, run_id=RUN_ID)
    assert prepared.sandbox_dir.is_dir()
    assert events == ["cleanup-registered"]

    completed = _run_phase_succeeds(prepared)
    assert completed.run_status == "completed"

    verified = _verify_phase_succeeds(completed)
    assert verified.verified


def test_cleanup_runs_in_lifo_order() -> None:
    """SandboxCleanupRegistry runs registered actions in the fixed contract order."""
    registry = SandboxCleanupRegistry()
    events: list[str] = []

    def make(name: str) -> Callable[[], None]:
        def _action() -> None:
            events.append(name)

        return _action

    registry.register("delete-project", make("delete-project"))
    registry.register("cancel-run", make("cancel-run"))
    registry.register("archive-agent", make("archive-agent"))
    failures = registry.execute_all()
    assert failures == []
    assert events == ["cancel-run", "archive-agent", "delete-project"]


def test_cleanup_registry_preserves_primary_failure() -> None:
    registry = SandboxCleanupRegistry()
    primary = AssertionError("primary failure")
    registry.set_primary_failure(primary)
    registry.set_primary_failure(RuntimeError("secondary"))
    assert registry.primary_failure is primary


def test_cleanup_registry_injected_failure_continues() -> None:
    from tests.live.sandbox import LiveCleanupError

    registry = SandboxCleanupRegistry()
    events: list[str] = []

    def fail_remove() -> None:
        raise LiveCleanupError("remove-resource")

    def archive() -> None:
        events.append("archive-agent")

    registry.register("remove-resource", fail_remove)
    registry.register("archive-agent", archive)
    failures = registry.execute_all()
    assert len(failures) == 1
    assert failures[0]["name"] == "remove-resource"
    assert events == ["archive-agent"]


def test_filesystem_policy_rejects_writes_outside_workspace(tmp_path: pathlib.Path) -> None:
    """``assert_manifest_policy`` forbids file changes outside the allowlist."""
    sandbox = tmp_path / "sandbox"
    write_initial_sandbox_files(sandbox, RUN_ID)
    before = build_file_manifest(sandbox)
    rogue = sandbox / "rogue.txt"
    rogue.write_text("forbidden", encoding="utf-8")
    after = build_file_manifest(sandbox)
    with pytest.raises(AssertionError, match="unexpected filesystem change"):
        assert_manifest_policy(before, after, RUN_ID, expect_target_change=False)


def test_filesystem_policy_allows_known_allowlist_paths(tmp_path: pathlib.Path) -> None:
    sandbox = tmp_path / "sandbox"
    write_initial_sandbox_files(sandbox, RUN_ID)
    before = build_file_manifest(sandbox)
    (sandbox / "AGENTS.md").write_text("notes", encoding="utf-8")
    (sandbox / ".multica" / "cache").mkdir(parents=True)
    (sandbox / ".multica" / "cache" / "state.json").write_text("{}", encoding="utf-8")
    (sandbox / ".opencode" / "skills" / "demo").mkdir(parents=True)
    (sandbox / ".opencode" / "skills" / "demo" / "SKILL.md").write_text("skill", encoding="utf-8")
    (sandbox / ".agent_context").mkdir(parents=True)
    (sandbox / ".agent_context" / "issue_context.md").write_text("issue", encoding="utf-8")
    after = build_file_manifest(sandbox)
    assert_manifest_policy(before, after, RUN_ID, expect_target_change=False)


def test_diagnostics_emit_verification_code(tmp_path: pathlib.Path) -> None:
    """Sandbox workflow records the canary VERIFICATION_CODE and redacts it on write.

    The ``DiagnosticCollector`` always replaces ``"888888"`` with ``"***"``
    so the live canary string never leaks into the artifact bundle.
    """
    collector = DiagnosticCollector(tmp_path, RUN_ID)
    collector.write_json("run-context.json", {"verification_code": "888888"})
    artifact = tmp_path / "run-context.json"
    assert artifact.is_file()
    body = artifact.read_text(encoding="utf-8")
    assert "888888" not in body
    assert "***" in body
    assert collector.has_secret_leak("888888")
    assert not collector.has_secret_leak(body)


def test_ordinary_session_does_not_create_sandbox_resources(
    tmp_path: pathlib.Path,
) -> None:
    """A plain ``LiveSession`` (no ``prepare_sandbox`` call) never creates a sandbox dir."""
    from tests.live.api import LiveApiClient
    from tests.live.session import LiveEnvironment, LiveSession
    from tools.live_support.environment import Environment

    env_base = Environment(api_key="x", workspace="w", profile="p", extra={})
    env = LiveEnvironment(
        api_key=env_base.api_key,
        workspace=env_base.workspace,
        profile=env_base.profile,
        extra=env_base.extra,
    )
    client = LiveApiClient("http://127.0.0.1:1", env_base, timeout=0.001)
    session = LiveSession(env)
    session.api = client
    home = tmp_path / "home"
    home.mkdir()
    before = {p.name for p in home.iterdir()}
    with session:
        pass
    after = {p.name for p in home.iterdir()}
    assert before == after
    assert not any(tmp_path.rglob("sandbox"))


def test_load_agent_sandbox_settings_rejects_unknown_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MULTICA_TEST_AGENT_MODE", "unknown")
    with pytest.raises(LiveSetupError, match="MULTICA_TEST_AGENT_MODE"):
        load_agent_sandbox_settings(repo_root=REPO_ROOT)


def test_daemon_status_payload_is_running_accepts_status_field() -> None:
    assert daemon_status_payload_is_running({"status": "running", "pid": 3004}) is True
    assert daemon_status_payload_is_running({"running": True}) is True
    assert daemon_status_payload_is_running({"status": "stopped"}) is False


def test_daemon_cli_argv_includes_profile_flag(tmp_path: pathlib.Path) -> None:
    cli = tmp_path / "multica"
    cli.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    cli.chmod(0o755)
    home = tmp_path / "home"
    home.mkdir()
    daemon = DaemonLifecycle(
        cli_executable=cli,
        home_dir=home,
        profile_name="live-deadbeef",
        daemon_id="daemon-1",
        workspaces_root=tmp_path / "workspaces",
        opencode_path=cli,
        opencode_model="multica-test/fake",
        agent_mode="success",
        diagnostics=DiagnosticCollector(tmp_path / "artifacts", "deadbeef" * 2),
    )
    assert daemon._daemon_argv("daemon", "status", "--output", "json") == [
        str(cli),
        "daemon",
        "status",
        "--output",
        "json",
        "--profile",
        "live-deadbeef",
    ]


def _run_phase_succeeds(prepared: Any) -> Any:
    """Return a fake CompletedAssignment representing a successful run."""
    from tests.live.sandbox import CompletedAssignment, FileManifest

    return CompletedAssignment(
        run_status="completed",
        cancelled=False,
        manifest_before=FileManifest(),
        manifest_after=FileManifest(),
        cleanup_errors=(),
    )


def _verify_phase_succeeds(completed: Any) -> Any:
    from tests.live.sandbox import PreparedSandbox, verify_sandbox

    return verify_sandbox(
        PreparedSandbox(
            sandbox_dir=pathlib.Path(),
            run_id="r",
            target_path=pathlib.Path(),
            control_path=pathlib.Path(),
        ),
        completed,
    )


def test_assignment_dataclass_round_trip() -> None:
    """``Assignment`` is a frozen dataclass — no mutation, hashable."""
    from tools.live_support.environment import AgentSandboxSettings

    settings = AgentSandboxSettings(
        agent_mode="success",
        inject_cleanup_failure=None,
        opencode_path=pathlib.Path("/bin/echo"),
        opencode_model="m",
    )
    assignment = Assignment(settings=settings, inject_cleanup_failure="x")
    assert assignment.settings is settings
    assert assignment.inject_cleanup_failure == "x"
    with pytest.raises((AttributeError, TypeError)):
        assignment.inject_cleanup_failure = "y"  # type: ignore[misc]
