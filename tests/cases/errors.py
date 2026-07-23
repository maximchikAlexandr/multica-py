from __future__ import annotations

from multica_py.exceptions import (
    AuthenticationError,
    CommandExecutionError,
    NotFoundError,
    OutputShapeError,
)
from tests.cases.models import BehaviorDimension, ErrorCase, FakeCliResponse, OperationCase
from tests.cases.operations import OPERATION_CASES

_BY_METHOD: dict[str, OperationCase] = {c.sdk_method: c for c in OPERATION_CASES}


ERROR_CASES: tuple[ErrorCase, ...] = (
    ErrorCase(
        id="labels.get.missing-id",
        operation=_BY_METHOD["labels.get"],
        response=FakeCliResponse(exit_code=4),
        exception_type=NotFoundError,
        dimensions=frozenset({BehaviorDimension.ERROR_MAPPING}),
    ),
    ErrorCase(
        id="agents.list.shape",
        operation=_BY_METHOD["agents.list"],
        response=FakeCliResponse(stdout=b"not-json"),
        exception_type=OutputShapeError,
        dimensions=frozenset({BehaviorDimension.ERROR_MAPPING, BehaviorDimension.MALFORMED_OUTPUT}),
    ),
    ErrorCase(
        id="auth.login.credentials",
        operation=_BY_METHOD["auth.login"],
        response=FakeCliResponse(exit_code=3),
        exception_type=AuthenticationError,
        dimensions=frozenset({BehaviorDimension.ERROR_MAPPING, BehaviorDimension.SECRET_REDACTION}),
    ),
    ErrorCase(
        id="projects.resources.list.shape",
        operation=_BY_METHOD["projects.resources.list"],
        response=FakeCliResponse(stdout=b"not-json"),
        exception_type=OutputShapeError,
        dimensions=frozenset({BehaviorDimension.ERROR_MAPPING, BehaviorDimension.MALFORMED_OUTPUT}),
    ),
    ErrorCase(
        id="projects.resources.remove.missing",
        operation=_BY_METHOD["projects.resources.remove"],
        response=FakeCliResponse(exit_code=1),
        exception_type=CommandExecutionError,
        dimensions=frozenset({BehaviorDimension.ERROR_MAPPING}),
    ),
)
