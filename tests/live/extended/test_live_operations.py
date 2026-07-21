from __future__ import annotations

import pytest

from tests._manifest_coverage import assert_manifest_coverage
from tests._manifest_support import guard_eligible_operations
from tests.live.environment import LiveContext
from tests.live.resources import LIVE_OPERATIONS, LiveOperation

pytestmark = [pytest.mark.live, pytest.mark.live_extended, pytest.mark.serial]


@pytest.mark.parametrize("op", LIVE_OPERATIONS, ids=lambda o: o.sdk_method)
def test_live_operation_executes(op: LiveOperation, live_ctx: LiveContext) -> None:
    """Execute one non-CRUD operation against the real backend."""
    op.invoke(live_ctx)
