from __future__ import annotations

import pathlib

import pytest

from multica_py._internal.upstream_contract.generator.schema import ApprovedContractV2
from multica_py._internal.upstream_contract.generator.validation import (
    load_approved_contract_v2,
    validate_approved_v2,
)

ROOT = pathlib.Path(__file__).resolve().parents[3]

pytestmark = [
    pytest.mark.contract,
    pytest.mark.serial,
]


def _load_contract() -> ApprovedContractV2:
    return load_approved_contract_v2(ROOT / "contracts" / "sdk-contract.json")


FR_IDS = tuple(f"FR-{i:03d}" for i in range(1, 41))
BC_IDS = tuple(f"BC-{i:03d}" for i in range(1, 7))
SC_IDS = tuple(f"SC-{i:03d}" for i in range(1, 13))
ET_IDS = tuple(f"ET-{i:03d}" for i in range(1, 8))
ALL_REQUIREMENT_IDS = FR_IDS + BC_IDS + SC_IDS + ET_IDS


def test_traceability_requirement_set_is_exact() -> None:
    contract = validate_approved_v2(_load_contract())
    assert {requirement.requirement_id for requirement in contract.traceability} == set(
        ALL_REQUIREMENT_IDS
    )
