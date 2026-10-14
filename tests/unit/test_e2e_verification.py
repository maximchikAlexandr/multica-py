from __future__ import annotations

from pathlib import Path

import pytest

from scripts.e2e.verify_multica_test import _prepare_output, _sanitize

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "live-smoke.yml"
SCRIPT = ROOT / "scripts" / "e2e" / "verify_multica_test.py"


def test_sanitize_removes_secrets_urls_and_target_overrides() -> None:
    value = _sanitize(
        "token=secret password=hunter2 server_url=https://private.example.test/workspace"
    )
    assert "secret" not in value
    assert "hunter2" not in value
    assert "private.example.test" not in value


def test_artifact_output_rejects_git_checkout(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside the Git checkout"):
        _prepare_output(ROOT / ".artifacts" / "e2e")
    assert _prepare_output(tmp_path / "e2e").is_dir()


def test_walkthrough_uses_fixed_wrapper_without_target_overrides() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert '_WRAPPER_EXECUTABLE = "multica-test"' in source
    assert "executable=_WRAPPER_EXECUTABLE" in source
    assert "profile=" not in source
    assert "server_url=" not in source
    assert "workspace_id=" not in source
    assert "MULTICA_TOKEN" not in source


def test_live_workflow_authorizes_exact_same_repository_head_before_protected_job() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "candidate_sha" in workflow
    assert "head.repo.full_name" in workflow
    assert 'head_sha" != "$CANDIDATE_SHA"' in workflow
    assert "persist-credentials: false" in workflow
    assert "ref: ${{ needs.authorize.outputs.head_sha }}" in workflow
    assert "MULTICA_LIVE_EXPECTED_VERSION: 0.6.2" in workflow
    assert "environment: multica-live" in workflow
    assert '"credentials":"not recorded"' in workflow
