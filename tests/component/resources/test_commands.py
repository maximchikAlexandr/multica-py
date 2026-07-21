from __future__ import annotations

import pytest

from multica_py.client import MulticaClient
from tests._manifest_coverage import assert_manifest_coverage
from tests._manifest_support import guard_eligible_operations
from tests.component.command_cases import PROJECT_RESOURCE_COMMAND_CASES, SUCCESS_COMMAND_CASES
from tests.component.conftest import assert_command_argv
from tests.component.resource_support import CommandCase

KNOWN_FIXTURE_GAPS: frozenset[str] = frozenset()


@pytest.mark.parametrize("case", SUCCESS_COMMAND_CASES, ids=lambda item: item.id)
def test_command_argv(case: CommandCase, fake_cli_client: MulticaClient) -> None:
    assert_command_argv(case, fake_cli_client)


def test_every_guard_eligible_operation_has_command_case() -> None:
    eligible = guard_eligible_operations()
    covered = frozenset(
        case.sdk_method for case in (*SUCCESS_COMMAND_CASES, *PROJECT_RESOURCE_COMMAND_CASES)
    )
    assert_manifest_coverage(
        eligible,
        covered,
        KNOWN_FIXTURE_GAPS,
        missing_label="Missing CommandCase rows for",
        stale_label="Stale KNOWN_FIXTURE_GAPS entries (now have rows)",
    )
