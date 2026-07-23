from __future__ import annotations

import pathlib

import pytest

from tests.live._live_helpers import load_agent_sandbox_settings
from tests.live.sandbox import (
    Assignment,
    prepare_sandbox,
    run_assignment,
    verify_sandbox,
)
from tests.live.session import LiveCase, LiveEnvironment, SandboxSession

pytestmark = [pytest.mark.live, pytest.mark.live_extended, pytest.mark.serial]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    ("agent_mode", "cleanup_inject", "expect_cancelled", "expect_file_failure"),
    [
        ("error", None, False, False),
        ("timeout", None, True, False),
        ("wrong-edit", None, False, True),
        ("success", "remove-resource", False, False),
    ],
    ids=["agent-error", "agent-timeout", "wrong-edit", "cleanup-failure"],
)
def test_agent_sandbox_failure_cases(
    agent_mode: str,
    cleanup_inject: str | None,
    expect_cancelled: bool,
    expect_file_failure: bool,
    sandbox_session: SandboxSession,
    live_environment: LiveEnvironment,
    live_case: LiveCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Observe expected failure behavior for extended sandbox variants."""
    monkeypatch.setenv("MULTICA_TEST_AGENT_MODE", agent_mode)
    settings = load_agent_sandbox_settings(repo_root=REPO_ROOT)
    assignment = Assignment(
        settings=settings,
        inject_cleanup_failure=cleanup_inject,
    )
    prepared = prepare_sandbox(
        sandbox_session,
        sandbox_session.workspace,
        run_id=live_environment.run_id,
    )
    completed = run_assignment(
        live_environment,
        prepared,
        assignment,
        diagnostics=live_environment.diagnostics,
    )
    if agent_mode == "error":
        assert completed.run_status == "failed"
        assert not completed.file_assertion_failed
    elif agent_mode == "timeout":
        assert completed.cancelled
        assert not completed.file_assertion_failed
    elif agent_mode == "wrong-edit":
        assert completed.run_status == "completed"
        assert completed.file_assertion_failed
        assert completed.primary_error is not None
    elif agent_mode == "success":
        assert completed.run_status == "completed"
        if cleanup_inject is not None:
            assert any("remove-resource" in error for error in completed.cleanup_errors)
    assert completed.cancelled is expect_cancelled
    assert completed.file_assertion_failed is expect_file_failure
    assert live_case.unique_name  # case context honored
