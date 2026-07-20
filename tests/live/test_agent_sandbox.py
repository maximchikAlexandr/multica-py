from __future__ import annotations

from collections.abc import Callable

import pytest

from tests.live.resources import AgentSandboxOutcome

pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]


def test_agent_executes_issue_in_local_directory(
    run_agent_sandbox: Callable[..., AgentSandboxOutcome],
) -> None:
    """Run the deterministic agent sandbox success workflow."""
    outcome = run_agent_sandbox()
    assert outcome.run_status == "completed"
    assert not outcome.file_assertion_failed
    assert outcome.primary_error is None
    assert not outcome.cleanup_errors
