from __future__ import annotations

import pytest

from tests.live.sandbox import (
    Assignment,
    prepare_sandbox,
    run_assignment,
    verify_sandbox,
)
from tests.live.session import LiveEnvironment, SandboxSession

pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]


def test_agent_executes_issue_in_local_directory(
    sandbox_session: SandboxSession,
    live_environment: LiveEnvironment,
) -> None:
    """Run the deterministic agent sandbox success workflow."""
    assignment = Assignment(settings=live_environment.agent_sandbox_settings)
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
    assert not completed.cleanup_errors, completed.cleanup_errors
