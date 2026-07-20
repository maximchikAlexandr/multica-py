from __future__ import annotations

from typing import get_args

import pytest

from tests._manifest_coverage import assert_manifest_coverage
from tests._manifest_support import guard_eligible_operations
from tests.live.resources import (
    KNOWN_LIVE_GAPS,
    LIVE_EXEC_EXCEPTIONS,
    LIVE_OPERATIONS,
    LiveExecReason,
    crud_sdk_methods,
)

pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]


def test_every_guard_eligible_operation_runs_live() -> None:
    """Guard (FR-021): each guard-eligible operation is covered, allowlisted, or a known gap."""
    eligible = guard_eligible_operations()
    covered = frozenset(op.sdk_method for op in LIVE_OPERATIONS) | crud_sdk_methods()
    allowlisted = KNOWN_LIVE_GAPS | frozenset(LIVE_EXEC_EXCEPTIONS)

    assert_manifest_coverage(
        eligible,
        covered,
        allowlisted,
        missing_label="uncovered, unallowlisted operations",
        stale_label="stale allowlist entries (also in T_live)",
    )

    exec_exceptions = set(LIVE_EXEC_EXCEPTIONS)
    both_buckets = exec_exceptions & KNOWN_LIVE_GAPS
    valid_reasons = get_args(LiveExecReason)
    invalid_reason = {k for k, v in LIVE_EXEC_EXCEPTIONS.items() if v not in valid_reasons}

    failures: list[str] = []
    if both_buckets:
        ops = ", ".join(sorted(both_buckets))
        failures.append(f"operations in both LIVE_EXEC_EXCEPTIONS and KNOWN_LIVE_GAPS: {ops}")
    if invalid_reason:
        ops = ", ".join(sorted(invalid_reason))
        failures.append(f"invalid LIVE_EXEC_EXCEPTIONS reason codes: {ops}")

    if failures:
        msg = "; ".join(failures)
        raise AssertionError(msg)
