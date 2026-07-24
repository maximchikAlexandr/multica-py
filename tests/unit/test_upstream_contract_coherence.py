from __future__ import annotations

import pathlib

import msgspec
import pytest

from multica_py._internal.upstream_contract.generator.renderer import render_outputs
from multica_py._internal.upstream_contract.generator.validation import (
    load_approved_contract_v2,
    validate_approved_v2,
)
from multica_py._internal.upstream_contract.models import CoverageManifest
from multica_py._internal.upstream_contract.state import load_state

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "contracts/sdk-contract.json"
STATE_PATH = ROOT / "src/multica_py/_generated/upstream_state.json"
COVERAGE_PATH = ROOT / "src/multica_py/_generated/upstream_coverage.json"

EXPECTED_16: tuple[str, ...] = (
    "issues.comments.add",
    "issues.comments.delete",
    "issues.comments.list",
    "issues.create",
    "issues.labels.add",
    "issues.labels.list",
    "issues.labels.remove",
    "issues.list",
    "issues.set_status",
    "projects.create",
    "projects.resources.add_local_directory",
    "projects.resources.list",
    "projects.resources.remove",
    "projects.resources.update_local_directory",
    "projects.set_status",
    "projects.update",
)


def test_107_help_degraded_removed() -> None:
    contract = load_approved_contract_v2(CONTRACT_PATH)
    assert len(contract.operations) == 16
    op_ids = {op.operation_id for op in contract.operations}
    assert op_ids == set(EXPECTED_16)


def test_no_removed_family_dispositions_in_supported() -> None:
    contract = load_approved_contract_v2(CONTRACT_PATH)
    for fd in contract.scope.family_dispositions:
        assert fd.disposition != "command_removed", (
            f"family {fd.family}: removed family cannot be classified as supported"
        )


def test_unknown_family_disposition_is_rejected() -> None:
    contract = load_approved_contract_v2(CONTRACT_PATH)
    fake_fd = msgspec.structs.replace(
        contract.scope.family_dispositions[0],
        family="issues_removed_negative_case",
        disposition="command_removed",
        rationale="negative-case fixture",
    )
    mutated = msgspec.structs.replace(
        contract,
        scope=msgspec.structs.replace(
            contract.scope,
            family_dispositions=(fake_fd, *contract.scope.family_dispositions[1:]),
        ),
    )
    with pytest.raises(ValueError, match="unknown disposition"):
        validate_approved_v2(mutated)


def test_exact_16_id_equality_across_artifacts() -> None:
    contract = load_approved_contract_v2(CONTRACT_PATH)
    expected = set(contract.scope.operation_ids)
    assert len(expected) == 16

    op_ids = {op.operation_id for op in contract.operations}
    assert op_ids == expected

    outputs = {str(output.path): output.content for output in render_outputs(contract)}
    ids_from_bindings: set[str] = set()
    text = outputs["src/multica_py/_generated/approved_sdk_bindings.py"].decode()
    for line in text.splitlines():
        stripped = line.strip()
        if "GeneratedBinding(operation_id=" in stripped:
            for oid in EXPECTED_16:
                if f"operation_id={oid!r}" in stripped:
                    ids_from_bindings.add(oid)
                    break
    assert ids_from_bindings == expected, (
        f"bindings.py IDs mismatch: missing {expected - ids_from_bindings}, "
        f"extra {ids_from_bindings - expected}"
    )

    raw_cov = COVERAGE_PATH.read_bytes()
    manifest: CoverageManifest = msgspec.json.decode(raw_cov, type=CoverageManifest)
    coverage_ids: set[str] = {d.operation_id for d in manifest.decisions}
    missing_in_coverage = expected - coverage_ids
    assert len(missing_in_coverage) <= 4, (
        f"coverage manifest missing {len(missing_in_coverage)} governed ops: {missing_in_coverage}"
    )

    compat: dict[str, object] = msgspec.json.decode(
        outputs["src/multica_py/_generated/approved_sdk_compatibility.json"]
    )
    assert compat.get("compatible") == 15
    assert compat.get("intentionally_changed") == 1

    state = load_state(STATE_PATH, repo_root=ROOT)
    assert state.supported is not None
