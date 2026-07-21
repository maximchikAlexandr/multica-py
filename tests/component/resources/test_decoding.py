from __future__ import annotations

import pytest

from multica_py.client import MulticaClient
from tests.component.command_cases import SUCCESS_COMMAND_CASES
from tests.component.conftest import COMMAND_CHECKS
from tests.component.resource_support import CommandCase


@pytest.mark.parametrize("case", SUCCESS_COMMAND_CASES, ids=lambda item: item.id)
def test_decoding(case: CommandCase, fake_cli_client: MulticaClient) -> None:
    COMMAND_CHECKS[case.check](case.invoke(fake_cli_client))
