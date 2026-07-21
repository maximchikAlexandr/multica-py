from __future__ import annotations

import pathlib
from collections.abc import Callable

import pytest

from tests.live.environment import load_agent_sandbox_settings
from tests.live.resources import AgentSandboxOutcome

pytestmark = [pytest.mark.live, pytest.mark.live_extended, pytest.mark.serial]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    ("case_id", "agent_mode", "cleanup_inject", "expect_cancelled", "expect_file_failure"),
    [
        ("agent-error", "error", None, False, False),
        ("agent-timeout", "timeout", None, True, False),
        ("wrong-edit", "wrong-edit", None, False, True),
        ("cleanup-failure", "success", "remove-resource", False, False),
    ],
    ids=["agent-error", "agent-timeout", "wrong-edit", "cleanup-failure"],
)
def test_agent_sandbox_failure_cases(
    case_id: str,
    agent_mode: str,
    cleanup_inject: str | None,
    expect_cancelled: bool,
    expect_file_failure: bool,
    run_agent_sandbox: Callable[..., AgentSandboxOutcome],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Observe expected failure behavior for extended sandbox variants."""
    monkeypatch.setenv("MULTICA_TEST_AGENT_MODE", agent_mode)
    settings = load_agent_sandbox_settings(repo_root=REPO_ROOT)
    outcome = run_agent_sandbox(
        settings=settings,
        inject_cleanup_failure=cleanup_inject,
    )
    if case_id == "agent-error":
        assert outcome.run_status == "failed"
        assert not outcome.file_assertion_failed
    elif case_id == "agent-timeout":
        assert outcome.cancelled
        assert not outcome.file_assertion_failed
    elif case_id == "wrong-edit":
        assert outcome.run_status == "completed"
        assert outcome.file_assertion_failed
        assert outcome.primary_error is not None
    elif case_id == "cleanup-failure":
        assert outcome.run_status == "completed"
        assert any("remove-resource" in error for error in outcome.cleanup_errors)
    assert outcome.cancelled is expect_cancelled
    assert outcome.file_assertion_failed is expect_file_failure
