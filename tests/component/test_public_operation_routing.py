from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import pytest

from multica_py._internal.specs import RawCommandResult, TextResult
from multica_py.client import MulticaClient
from tests.cases.operations import OPERATION_CASES, OperationCase
from tests.component.conftest import install_transport
from tests.component.resources.cases import ROUTING_CASES, RoutingCase


def _operation(operation_id: str) -> OperationCase:
    return next(case for case in OPERATION_CASES if case.id == operation_id)


def _configure_transport(transport: MagicMock, case: OperationCase) -> None:
    if case.transport_method == "run_bytes":
        transport.run_bytes.return_value = RawCommandResult(
            argv=case.expected_argv,
            exit_code=0,
            stdout=case.stdout or b"{}",
            stderr=b"",
            duration=datetime.timedelta(),
        )
    elif case.transport_method == "run_text":
        transport.run_text.return_value = TextResult(
            text=(case.stdout or b"{}").decode(), stderr="", exit_code=0
        )


@pytest.mark.parametrize("routing", ROUTING_CASES, ids=lambda case: case.id)
def test_canonical_operation_routes_through_public_client(
    routing: RoutingCase, client: MulticaClient, transport: MagicMock
) -> None:
    case = _operation(routing.operation_id)
    _configure_transport(transport, case)
    install_transport(client, transport)
    resource: object = client
    for attribute in case.sdk_method.split(".")[:-1]:
        resource = getattr(resource, attribute)
    getattr(resource, case.method)(*case.args, **dict(case.kwargs))
    transport_call = getattr(transport, case.transport_method)
    transport_call.assert_called_once()
    assert transport_call.call_args.args == (case.expected_argv,)
    if case.transport_method == "run_bytes":
        assert transport_call.call_args.kwargs == {"stdin": case.stdin, "timeout": None}
