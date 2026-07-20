from __future__ import annotations

import pathlib

import msgspec
import pytest

from multica_py._internal.upstream_contract.generator import contract as approved


def test_validate_approved_accepts_minimal_contract() -> None:
    contract = approved.ApprovedContract(
        schema_version=1,
        operations=(
            approved.ApprovedOperation(
                operation_id="agents.create",
                binding_command_path=("agent", "create"),
                python_parameter="name",
                cli_argument="--name",
                required=True,
                presence_semantics="omitted",
                enum_policy="strict",
                approved_enum=(),
                constraints=(),
                test_refs=("tests/contract/test_full_cli_coverage.py",),
            ),
        ),
    )
    assert approved.validate_approved(contract) is contract


def test_validate_approved_rejects_presence_semantic() -> None:
    contract = approved.ApprovedContract(
        schema_version=1,
        operations=(
            approved.ApprovedOperation(
                operation_id="agents.create",
                binding_command_path=("agent", "create"),
                python_parameter="name",
                cli_argument="--name",
                presence_semantics="some-other",
            ),
        ),
    )
    with pytest.raises(ValueError):
        approved.validate_approved(contract)


def test_validate_approved_rejects_enum_policy() -> None:
    contract = approved.ApprovedContract(
        schema_version=1,
        operations=(
            approved.ApprovedOperation(
                operation_id="agents.create",
                binding_command_path=("agent", "create"),
                python_parameter="name",
                cli_argument="--name",
                enum_policy="none",
            ),
        ),
    )
    with pytest.raises(ValueError):
        approved.validate_approved(contract)


def test_validate_approved_accepts_constraint_categories() -> None:
    contract = approved.ApprovedContract(
        schema_version=1,
        operations=(
            approved.ApprovedOperation(
                operation_id="agents.create",
                binding_command_path=("agent", "create"),
                python_parameter="name",
                cli_argument="--name",
                constraints=(
                    {"category": "requires", "target": "--name"},
                    {"category": "conflicts_with", "target": "--anonymous"},
                ),
            ),
        ),
    )
    approved.validate_approved(contract)


def test_validate_approved_rejects_constraint_category() -> None:
    contract = approved.ApprovedContract(
        schema_version=1,
        operations=(
            approved.ApprovedOperation(
                operation_id="agents.create",
                binding_command_path=("agent", "create"),
                python_parameter="name",
                cli_argument="--name",
                constraints=({"category": "made-up", "target": "x"},),
            ),
        ),
    )
    with pytest.raises(ValueError):
        approved.validate_approved(contract)


def test_load_approved_contract_rejects_unknown_schema(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "sdk-contract.json"
    path.write_text('{"schema_version": 999, "operations": []}')
    with pytest.raises((ValueError, msgspec.ValidationError)):
        approved.load_approved_contract(path)


def test_load_approved_contract_rejects_unknown_fields(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "sdk-contract.json"
    path.write_text('{"schema_version": 1, "operations": [], "review_status": "placeholder"}')
    with pytest.raises((ValueError, msgspec.ValidationError)):
        approved.load_approved_contract(path)


def test_load_approved_contract_parses_real_json() -> None:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    json_path = repo_root / "contracts" / "sdk-contract.json"
    contract = approved.load_approved_contract(json_path)
    assert contract.schema_version == 1
    assert len(contract.operations) == 22
    approved.validate_approved(contract)
