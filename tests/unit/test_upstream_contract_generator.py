from __future__ import annotations

import argparse
import pathlib

import msgspec
import pytest

from multica_py._internal.upstream_contract.cli import cmd_generate
from multica_py._internal.upstream_contract.generator import contract as approved
from multica_py._internal.upstream_contract.generator import schema as v2schema
from multica_py._internal.upstream_contract.generator import validation as v2
from multica_py._internal.upstream_contract.generator.renderer import (
    GeneratedOutput,
    render_outputs,
)
from multica_py._internal.upstream_contract.generator.writer import check_outputs


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


SEED_PATH = pathlib.Path(__file__).resolve().parents[2] / "contracts/sdk-contract.json"


def _load_contract_v2() -> v2schema.ApprovedContractV2:
    return v2.load_approved_contract_v2(SEED_PATH)


def test_approved_v2_validate_passes_on_seed() -> None:
    contract = _load_contract_v2()
    assert contract.schema_version == 2
    assert len(contract.operations) == 16
    assert v2.validate_approved_v2(contract) is contract


def test_approved_v2_rejects_wrong_target() -> None:
    contract = _load_contract_v2()
    bad = v2schema.ApprovedContractV2(
        schema_version=2,
        target=v2schema.TargetMetadata(
            version="9.9.9",
            tag="v9.9.9",
            commit="0" * 40,
            release_id="0",
            release_provenance_ref="x",
        ),
        catalogs=contract.catalogs,
        source_refs=contract.source_refs,
        test_refs=contract.test_refs,
        scope=contract.scope,
        operations=contract.operations,
        traceability=contract.traceability,
    )
    with pytest.raises(ValueError):
        v2.validate_approved_v2(bad)


def test_approved_v2_requires_16_operations() -> None:
    contract = _load_contract_v2()
    bad = v2schema.ApprovedContractV2(
        schema_version=2,
        target=contract.target,
        catalogs=contract.catalogs,
        source_refs=contract.source_refs,
        test_refs=contract.test_refs,
        scope=contract.scope,
        operations=(),
        traceability=contract.traceability,
    )
    with pytest.raises(ValueError):
        v2.validate_approved_v2(bad)


def test_approved_v2_rejects_unknown_top_level_field() -> None:
    data = SEED_PATH.read_bytes().replace(
        b'"schema_version"',
        b'"schema_version": 2, "bogus_field": null, "//": "',
    )
    with pytest.raises((msgspec.ValidationError, ValueError)):
        msgspec.json.decode(data, type=v2schema.ApprovedContractV2, strict=True)


def test_approved_v2_rejects_unknown_catalog_key() -> None:
    data = SEED_PATH.read_bytes().replace(
        b'"types"',
        b'"types": {}, "bogus_cat": {}, "//": "',
    )
    with pytest.raises((msgspec.ValidationError, ValueError)):
        msgspec.json.decode(data, type=v2schema.ApprovedContractV2, strict=True)


CONTRACT_PATH = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "sdk-contract.json"
GOLDEN_DIR = (
    pathlib.Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "upstream_contract" / "v2"
)
EXPECTED_OUTPUT_PATHS: tuple[str, ...] = (
    "src/multica_py/_generated/approved_sdk_contract.json",
    "src/multica_py/_generated/approved_sdk_bindings.py",
    "src/multica_py/_generated/approved_sdk_enums.py",
    "src/multica_py/_generated/approved_sdk_validators.py",
    "src/multica_py/_generated/approved_sdk_compatibility.json",
    "tests/cases/generated/approved_sdk_cases.py",
    "tests/fixtures/provenance/approved-sdk-v0.4.9.json",
)


def _load_contract() -> v2schema.ApprovedContractV2:
    return v2.load_approved_contract_v2(CONTRACT_PATH)


def test_renderer_fixed_order() -> None:
    contract = _load_contract()
    outputs = render_outputs(contract)
    assert tuple(str(output.path) for output in outputs) == EXPECTED_OUTPUT_PATHS


def test_renderer_byte_comparison() -> None:
    contract = _load_contract()
    outputs = render_outputs(contract)
    for out in outputs:
        if "provenance" in str(out.path):
            continue
        flat_name = str(out.path).replace("/", "_") + ".golden"
        golden_path = GOLDEN_DIR / flat_name
        assert golden_path.is_file(), f"missing golden: {golden_path}"
        assert golden_path.read_bytes() == out.content, f"content mismatch: {out.path}"


def test_generate_check_reports_match(tmp_path: pathlib.Path) -> None:
    contract = _load_contract()
    outputs = render_outputs(contract)
    checked: list[GeneratedOutput] = []
    for out in outputs:
        if "provenance" in str(out.path):
            continue
        dest = tmp_path / out.path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(out.content)
        checked.append(out)
    result = check_outputs(tuple(checked), tmp_path)
    assert result == 0


def test_generate_check_allows_unmaterialized_outputs(tmp_path: pathlib.Path) -> None:
    contract = _load_contract()
    assert check_outputs(render_outputs(contract), tmp_path) == 0


def test_generate_check_reports_mismatch(tmp_path: pathlib.Path) -> None:
    contract = _load_contract()
    outputs = render_outputs(contract)
    for out in outputs:
        dest = tmp_path / out.path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(out.content)
    # Modify a file
    bad = tmp_path / "src/multica_py/_generated/approved_sdk_contract.json"
    bad.write_bytes(b"{}\n")
    result = check_outputs(outputs, tmp_path)
    assert result == 1


def test_generate_rejects_evidence_input() -> None:
    for bad_path in ("contracts/candidate/foo.json", "evidence/bar.json", "suggestion/baz.json"):
        ns = argparse.Namespace(approved=bad_path, check=True, repo_root=".")
        result = cmd_generate(ns)
        assert result == 1, f"expected rejection for {bad_path}"
