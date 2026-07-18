from __future__ import annotations

import datetime

import pytest

from multica_py.client import MulticaClient
from multica_py.models.issues import IssueCreateRequest, IssueUpdateRequest
from tests.live.oracle import DirectApiOracle

pytestmark = [pytest.mark.live, pytest.mark.live_extended]


def _parse_timestamp(value: object) -> datetime.datetime:
    if not isinstance(value, str) or not value:
        msg = f"expected non-empty timestamp string, got {value!r}"
        raise AssertionError(msg)
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        msg = f"expected timezone-aware timestamp, got {value!r}"
        raise AssertionError(msg)
    return parsed


def test_issue_timestamps_are_timezone_aware_and_monotonic(
    live_client: MulticaClient,
    api_oracle: DirectApiOracle,
    register_resource,
    resource_name: str,
) -> None:
    """Verify created_at/updated_at are timezone-aware and updated_at moves forward."""
    issue = live_client.issues.create(
        IssueCreateRequest(title=f"{resource_name}-timestamps", description="before")
    )
    register_resource(
        key=f"issue-{issue.id}",
        cleanup=api_oracle.delete_callback(f"/api/issues/{issue.id}", "issue"),
    )
    created_body = api_oracle.get_issue(issue.id)
    created_at = _parse_timestamp(created_body.get("created_at"))
    updated_at = _parse_timestamp(created_body.get("updated_at"))
    assert created_at <= updated_at

    live_client.issues.update(issue.id, IssueUpdateRequest(description="after"))
    updated_body = api_oracle.get_issue(issue.id)
    created_after = _parse_timestamp(updated_body.get("created_at"))
    updated_after = _parse_timestamp(updated_body.get("updated_at"))
    assert created_after == created_at
    assert updated_after >= created_at
