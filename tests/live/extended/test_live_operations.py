from __future__ import annotations

import pytest

from tests.cases.models import OperationCase
from tests.cases.operations import OPERATION_CASES

pytestmark = [
    pytest.mark.live,
    pytest.mark.live_extended,
    pytest.mark.serial,
    pytest.mark.skip(reason="DIRECT_EXECUTORS not implemented yet (T064)"),
]

_DIRECT_CASES = tuple(
    case
    for case in OPERATION_CASES
    if case.live.mode == "extended" and case.live.owner.startswith("direct:")
)


@pytest.mark.parametrize("case", _DIRECT_CASES, ids=lambda c: c.sdk_method)
def test_live_operation_executes(case: OperationCase) -> None:
    raise NotImplementedError(f"executor for {case.sdk_method} to be filled in T064")
