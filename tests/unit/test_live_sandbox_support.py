from __future__ import annotations

import pathlib
from collections.abc import Callable

import pytest

from tests.live.backend import DaemonLifecycle, daemon_status_payload_is_running
from tests.live.diagnostics import DiagnosticCollector
from tests.live.environment import (
    LiveSetupError,
    create_live_run_context,
    load_agent_sandbox_settings,
)
from tests.live.resources import (
    CleanupRegistry,
    LiveCleanupError,
    assert_manifest_policy,
    build_file_manifest,
    write_initial_sandbox_files,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_create_live_run_context_paths(tmp_path: pathlib.Path) -> None:
    run_id = "a" * 32
    context = create_live_run_context(
        run_id=run_id,
        artifact_root=tmp_path / "artifacts",
        temp_parent=tmp_path,
    )
    assert context.prefix == f"multica-py-live-{run_id}"
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


def test_file_manifest_and_policy_success(tmp_path: pathlib.Path) -> None:
    run_id = "b" * 32
    sandbox = tmp_path / "sandbox"
    write_initial_sandbox_files(sandbox, run_id)
    before = build_file_manifest(sandbox)
    target = sandbox / "target.txt"
    target.write_text(f"after:{run_id}\n", encoding="utf-8")
    after = build_file_manifest(sandbox)
    assert_manifest_policy(before, after, run_id, expect_target_change=True)


def test_file_manifest_rejects_control_change(tmp_path: pathlib.Path) -> None:
    run_id = "c" * 32
    sandbox = tmp_path / "sandbox"
    write_initial_sandbox_files(sandbox, run_id)
    before = build_file_manifest(sandbox)
    (sandbox / "control.txt").write_text("changed\n", encoding="utf-8")
    after = build_file_manifest(sandbox)
    with pytest.raises(AssertionError, match=r"control\.txt"):
        assert_manifest_policy(before, after, run_id, expect_target_change=False)


def test_cleanup_registry_fixed_order_and_idempotence() -> None:
    registry = CleanupRegistry()
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
    registry = CleanupRegistry()
    primary = AssertionError("primary failure")
    registry.set_primary_failure(primary)
    registry.set_primary_failure(RuntimeError("secondary"))
    assert registry.primary_failure is primary


def test_cleanup_registry_injected_failure_continues() -> None:
    registry = CleanupRegistry()
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


def test_load_agent_sandbox_settings_rejects_unknown_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MULTICA_TEST_AGENT_MODE", "unknown")
    with pytest.raises(LiveSetupError, match="MULTICA_TEST_AGENT_MODE"):
        load_agent_sandbox_settings(repo_root=REPO_ROOT)


def test_manifest_allows_agents_and_provider_context_paths(tmp_path: pathlib.Path) -> None:
    run_id = "d" * 32
    sandbox = tmp_path / "sandbox"
    write_initial_sandbox_files(sandbox, run_id)
    before = build_file_manifest(sandbox)
    (sandbox / "AGENTS.md").write_text("notes", encoding="utf-8")
    multica_dir = sandbox / ".multica" / "cache"
    multica_dir.mkdir(parents=True)
    (multica_dir / "state.json").write_text("{}", encoding="utf-8")
    opencode_skill = sandbox / ".opencode" / "skills" / "demo"
    opencode_skill.mkdir(parents=True)
    (opencode_skill / "SKILL.md").write_text("skill", encoding="utf-8")
    agent_context = sandbox / ".agent_context"
    agent_context.mkdir(parents=True)
    (agent_context / "issue_context.md").write_text("issue", encoding="utf-8")
    after = build_file_manifest(sandbox)
    assert_manifest_policy(before, after, run_id, expect_target_change=False)
    assert after["AGENTS.md"].kind == "file"
    assert after[".multica/cache/state.json"].kind == "file"
    assert after[".opencode/skills/demo/SKILL.md"].kind == "file"
    assert after[".agent_context/issue_context.md"].kind == "file"


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
