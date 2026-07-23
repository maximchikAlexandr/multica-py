from __future__ import annotations

import pytest

from tests.live.sandbox import (
    Assignment,
    prepare_sandbox,
    run_assignment,
    verify_sandbox,
)
from tests.live.session import LiveEnvironment, SandboxSession

pytestmark = [pytest.mark.live, pytest.mark.live_opencode_canary, pytest.mark.serial]


def test_real_opencode_executes_issue_in_local_directory(
    sandbox_session: SandboxSession,
    live_environment: LiveEnvironment,
) -> None:
    """Run the real OpenCode canary workflow once with cost verification."""
    assignment = Assignment(
        settings=live_environment.agent_sandbox_settings,
        canary_settings=live_environment.canary_settings,
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
    verification = verify_sandbox(prepared, completed)
    assert verification.verified, verification.primary_error
    assert completed.run_status == "completed"
    assert not completed.file_assertion_failed
    assert completed.primary_error is None
    assert not completed.cleanup_errors
    assert completed.cost_usd is not None
    assert completed.cost_usd <= 0.10
