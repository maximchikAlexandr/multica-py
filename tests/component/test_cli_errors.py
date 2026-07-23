"""Component error round-trip tests for every ErrorCase.

Each :class:`ErrorCase` configures the mock transport to raise the SDK
exception the upstream CLI maps to, invokes the SDK method, and asserts the
right exception is raised (optionally with an expected message and exit
code).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from multica_py.client import MulticaClient
from tests.cases.errors import ERROR_CASES
from tests.cases.execution import configure_mock_transport, invoke_client_operation
from tests.cases.models import ErrorCase
from tests.component.conftest import install_transport

pytestmark = [pytest.mark.component]


@pytest.mark.parametrize("case", list(ERROR_CASES), ids=lambda c: c.id)
def test_cli_error_round_trip(
    case: ErrorCase,
    client_factory: object,
    transport: MagicMock,
) -> None:
    """Single failure executor for all ErrorCases."""
    configure_mock_transport(transport, case)

    client: MulticaClient = client_factory()  # type: ignore[operator]
    install_transport(client, transport)

    op = case.operation
    with pytest.raises(case.exception_type) as exc_info:
        invoke_client_operation(client, op.sdk_method, *op.args, **dict(op.kwargs))

    if case.assert_exception:
        case.assert_exception(exc_info.value)
