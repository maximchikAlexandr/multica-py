from __future__ import annotations

import pathlib

import pytest

from multica_py.client import MulticaClient
from tests._coverage_guard import assert_manifest_coverage
from tests._manifest_support import guard_eligible_operations

from .fake_cli_cases import FAKE_CLI_CASES, FakeCliCase

FAKE_CLI_FIXTURE_DIR = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "json"


def _all_json_fixtures() -> frozenset[str]:
    return frozenset(
        str(p.relative_to(FAKE_CLI_FIXTURE_DIR)) for p in FAKE_CLI_FIXTURE_DIR.rglob("*.json")
    )


def _referenced_fixtures() -> frozenset[str]:
    return frozenset(c.fixture for c in FAKE_CLI_CASES)


def _covered_sdk_methods() -> frozenset[str]:
    return frozenset(c.sdk_method for c in FAKE_CLI_CASES)


KNOWN_FIXTURE_GAPS: frozenset[str] = frozenset()


@pytest.mark.parametrize("case", FAKE_CLI_CASES, ids=lambda c: c.id)
def test_fake_cli_operation(case: FakeCliCase, fake_cli_client: MulticaClient) -> None:
    result = case.sdk_call(fake_cli_client)
    case.check(result)


def test_every_json_fixture_is_referenced() -> None:
    all_fixtures = _all_json_fixtures()
    referenced = _referenced_fixtures()
    unreferenced = all_fixtures - referenced
    assert not unreferenced, (
        f"Fixtures not referenced by any FakeCliCase row: {sorted(unreferenced)}"
    )


def test_every_guard_eligible_operation_has_fixture_or_gap() -> None:
    assert_manifest_coverage(
        guard_eligible_operations(),
        _covered_sdk_methods(),
        KNOWN_FIXTURE_GAPS,
        missing_label="Missing rows for",
        stale_label="Stale KNOWN_FIXTURE_GAPS entries (now have rows)",
    )
