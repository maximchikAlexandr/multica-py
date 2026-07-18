from __future__ import annotations

import pathlib

from multica_py._internal.upstream_contract import coverage, schema
from multica_py._internal.upstream_contract.paths import COVERAGE_PATH, SUPPORTED_CONTRACT_PATH

FIXTURES = pathlib.Path(__file__).parent.parent / "fixtures" / "upstream_contract" / "golden"


def test_coverage_counts_by_level() -> None:
    manifest = schema.decode_coverage(FIXTURES / "coverage-manifest-mixed.json")
    counts = coverage.coverage_counts(manifest)
    assert counts["typed"] == 3
    assert counts["process"] == 1
    assert counts["raw"] == 1
    assert counts["unsupported"] == 1
    assert counts["legacy"] == 1
    assert counts["incomplete"] == 1


def test_coverage_report_clean_for_supported_fixture() -> None:
    contract = schema.decode_contract(SUPPORTED_CONTRACT_PATH)
    manifest = schema.decode_coverage(COVERAGE_PATH)
    report = coverage.build_coverage_report(contract=contract, manifest=manifest)
    assert report.status == "clean"
    assert all(f.code != "INCOMPLETE_BINDING" for f in report.failures)
    assert all(f.code != "MISSING_COVERAGE" for f in report.failures)


def test_coverage_report_gaps_when_command_missing() -> None:
    contract = schema.decode_contract(SUPPORTED_CONTRACT_PATH)
    manifest = schema.decode_coverage(COVERAGE_PATH)
    coverage.build_coverage_report(contract=contract, manifest=manifest)
    for cmd in contract.commands:
        assert cmd.path in {
            tuple(d.bindings[0].command_path) for d in manifest.decisions if d.bindings
        }


def test_coverage_report_marks_incomplete_binding() -> None:
    from multica_py._internal.upstream_contract.models import (
        CommandContract,
        ExecutionContract,
        ObservationMeta,
        OutputContract,
        SemanticCLIContract,
    )

    base = schema.decode_contract(SUPPORTED_CONTRACT_PATH)
    contract = SemanticCLIContract(
        schema_version=2,
        baseline=base.baseline,
        artifact=base.artifact,
        commands=(
            CommandContract(
                path=("agent", "list"),
                use="list",
                execution=ExecutionContract(),
                output=OutputContract(),
            ),
        ),
        observation=ObservationMeta(generated_at="2026-01-01T00:00:00Z"),
    )
    from multica_py._internal.upstream_contract.models import (
        CoverageDecision,
        CoverageManifest,
        OperationBinding,
    )

    manifest = CoverageManifest(
        schema_version=1,
        decisions=(
            CoverageDecision(
                operation_id="agents.list",
                coverage_level="incomplete",
                bindings=(OperationBinding(command_path=("agent", "list")),),
            ),
        ),
    )
    report = coverage.build_coverage_report(contract=contract, manifest=manifest)
    codes = {f.code for f in report.failures}
    assert "INCOMPLETE_BINDING" in codes
    assert report.status == "gaps"


def test_coverage_report_rejects_unsupported_without_reason() -> None:
    from multica_py._internal.upstream_contract.models import (
        CommandContract,
        CoverageDecision,
        CoverageManifest,
        ExecutionContract,
        ObservationMeta,
        OperationBinding,
        OutputContract,
        SemanticCLIContract,
    )

    base = schema.decode_contract(SUPPORTED_CONTRACT_PATH)
    contract = SemanticCLIContract(
        schema_version=2,
        baseline=base.baseline,
        artifact=base.artifact,
        commands=(
            CommandContract(
                path=("agent", "orphan"),
                use="orphan",
                execution=ExecutionContract(),
                output=OutputContract(),
            ),
        ),
        observation=ObservationMeta(generated_at="2026-01-01T00:00:00Z"),
    )
    manifest = CoverageManifest(
        schema_version=1,
        decisions=(
            CoverageDecision(
                operation_id="agents.orphan",
                coverage_level="unsupported",
                bindings=(OperationBinding(command_path=("agent", "orphan")),),
            ),
        ),
    )
    report = coverage.build_coverage_report(contract=contract, manifest=manifest)
    codes = {f.code for f in report.failures}
    assert "UNSUPPORTED_REASON_MISSING" in codes


def test_coverage_decision_is_complete_for_typed() -> None:
    from multica_py._internal.upstream_contract.coverage import _decision_is_complete
    from multica_py._internal.upstream_contract.models import CoverageDecision

    decision = CoverageDecision(
        operation_id="agents.create",
        coverage_level="typed",
        input_contract_ref="x",
        output_contract_ref="y",
        test_refs=("a",),
        source_refs=("b",),
    )
    assert _decision_is_complete(decision) is True


def test_coverage_decision_is_complete_for_typed_missing_fields() -> None:
    from multica_py._internal.upstream_contract.coverage import _decision_is_complete
    from multica_py._internal.upstream_contract.models import CoverageDecision

    decision = CoverageDecision(operation_id="x", coverage_level="typed")
    assert _decision_is_complete(decision) is False


def test_coverage_decision_raw_requires_argv_policy() -> None:
    from multica_py._internal.upstream_contract.coverage import _decision_is_complete
    from multica_py._internal.upstream_contract.models import CoverageDecision

    assert _decision_is_complete(CoverageDecision(operation_id="x", coverage_level="raw")) is False
    assert (
        _decision_is_complete(
            CoverageDecision(
                operation_id="x",
                coverage_level="raw",
                raw_argv_policy="Sequence[str]",
            )
        )
        is True
    )


def test_unresolved_breaking_diff_is_detected() -> None:
    from multica_py._internal.upstream_contract import diff as diff_module

    before = schema.decode_contract(SUPPORTED_CONTRACT_PATH)
    after = schema.decode_contract(FIXTURES / "candidate-cli-contract-v2.json")
    diff = diff_module.diff_contracts(before, after)
    assert diff.unresolved_breaking is True
