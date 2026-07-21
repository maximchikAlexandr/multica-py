from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from multica_py._internal.transport import CliTransport
from multica_py.client import MulticaClient
from tests.component.command_cases import PROJECT_RESOURCE_COMMAND_CASES
from tests.component.conftest import (
    COMMAND_CHECKS,
    configure_mock_transport,
    patch_client_transport,
)
from tests.component.resource_support import CommandCase


@pytest.mark.parametrize("case", PROJECT_RESOURCE_COMMAND_CASES, ids=lambda item: item.id)
def test_project_resource_contract(case: CommandCase, fake_cli_client: MulticaClient) -> None:
    mock = MagicMock(spec=CliTransport)
    configure_mock_transport(case, mock)
    patch_client_transport(fake_cli_client, mock)
    COMMAND_CHECKS[case.check](case.invoke(fake_cli_client))
    transport = mock.run_bytes if mock.run_bytes.called else mock.run_text
    assert transport.call_args.args[0] == case.expected_argv


@pytest.mark.compat
def test_project_resource_list_argv_compat(fake_cli_client: MulticaClient) -> None:
    case = PROJECT_RESOURCE_COMMAND_CASES[0]
    mock = MagicMock(spec=CliTransport)
    configure_mock_transport(case, mock)
    patch_client_transport(fake_cli_client, mock)
    fake_cli_client.projects.resources.list("pr_001")
    assert mock.run_bytes.call_args.args[0] == case.expected_argv
