from __future__ import annotations

from multica_py.exceptions import OutputShapeError
from tests.cases.models import BehaviorDimension, ErrorCase, FakeCliResponse, OperationCase
from tests.cases.operations import OPERATION_CASES

_BY_METHOD: dict[str, OperationCase] = {c.sdk_method: c for c in OPERATION_CASES}

ERROR_CASES: tuple[ErrorCase, ...] = (
    ErrorCase(
        id="agents.list.shape",
        operation=_BY_METHOD["agents.list"],
        response=FakeCliResponse(stdout=b"{}"),
        exception_type=OutputShapeError,
        dimensions=frozenset({BehaviorDimension.MALFORMED_OUTPUT}),
    ),
)
