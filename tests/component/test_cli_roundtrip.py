"""Component round-trip tests for every OperationCase.

Each :class:`OperationCase` exercises one SDK method end-to-end through a
mocked transport: the test installs a programmable response, invokes the SDK
method via :func:`invoke_client_operation`, and asserts the call returns a
non-error result.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from multica_py.client import MulticaClient
from tests.cases.assertions import assert_result
from tests.cases.execution import configure_mock_transport, invoke_client_operation
from tests.cases.models import OperationCase
from tests.cases.operations import OPERATION_CASES
from tests.component.conftest import install_transport

pytestmark = [pytest.mark.component]


def _call_args(case: OperationCase) -> tuple[tuple[object, ...], dict[str, object]]:
    return case.args, dict(case.kwargs)


@pytest.mark.parametrize("case", list(OPERATION_CASES), ids=lambda c: c.operation_id)
def test_cli_round_trip(
    case: OperationCase,
    client_factory: object,
    transport: MagicMock,
) -> None:
    """Single success executor for all non-spawn OperationCases."""
    if "spawn" in case.tags:
        pytest.skip("spawn operation, tested separately")
    if not all(isinstance(a, (str, int, float, bool, type(None))) for a in case.args):
        pytest.skip(f"{case.operation_id}: args contain non-scalar public types")

    configure_mock_transport(transport, case)

    client: MulticaClient = client_factory()  # type: ignore[operator]
    install_transport(client, transport)

    args, kwargs = _call_args(case)
    result = invoke_client_operation(client, case.sdk_method, *args, **kwargs)
    assert_result(result, None)
