from __future__ import annotations

from multica_py._internal.upstream_contract import coverage
from multica_py._internal.upstream_contract.coverage import _decision_is_complete
from multica_py._internal.upstream_contract.models import (
    CommandContract,
    CoverageDecision,
    CoverageManifest,
    ExecutionContract,
    ObservationMeta,
    OutputContract,
    SemanticCLIContract,
)


def _make_contract() -> SemanticCLIContract:
    from multica_py._internal.upstream_contract.models import ArtifactMeta, Baseline

    return SemanticCLIContract(
        schema_version=2,
        baseline=Baseline(state="supported", version="0.4.2", tag=None, commit="0" * 40),
        artifact=ArtifactMeta(
            semantic_hash="sha256:0",
            generator_name="x",
            generator_version="0",
            generator_commit="0" * 40,
            collection_method="legacy",
        ),
        commands=(
            CommandContract(
                path=("auth", "login"),
                use="login",
                execution=ExecutionContract(),
                output=OutputContract(),
            ),
        ),
        observation=ObservationMeta(generated_at="2026-01-01T00:00:00Z"),
    )


def test_raw_coverage_requires_argv_policy() -> None:
    manifest = CoverageManifest(
        schema_version=1,
        decisions=(
            CoverageDecision(
                operation_id="auth.legacy_login",
                coverage_level="raw",
                raw_argv_policy="Sequence[str]",
            ),
        ),
    )
    assert _decision_is_complete(manifest.decisions[0]) is True


def test_raw_coverage_rejects_shell_string() -> None:
    from multica_py._internal.upstream_contract.coverage import _decision_is_complete

    bad = CoverageDecision(
        operation_id="auth.legacy_login",
        coverage_level="raw",
        raw_argv_policy="shell=True; command interpolation allowed",
    )
    assert _decision_is_complete(bad) is False


def test_raw_coverage_rejects_empty_policy() -> None:
    from multica_py._internal.upstream_contract.coverage import _decision_is_complete

    assert (
        _decision_is_complete(
            CoverageDecision(
                operation_id="auth.legacy_login",
                coverage_level="raw",
                raw_argv_policy=None,
            )
        )
        is False
    )
    assert (
        _decision_is_complete(
            CoverageDecision(
                operation_id="auth.legacy_login",
                coverage_level="raw",
                raw_argv_policy="",
            )
        )
        is False
    )


def test_raw_coverage_is_separate_from_typed_counts() -> None:
    manifest = CoverageManifest(
        schema_version=1,
        decisions=(
            CoverageDecision(
                operation_id="auth.legacy_login",
                coverage_level="raw",
                raw_argv_policy="Sequence[str]",
            ),
            CoverageDecision(
                operation_id="auth.status",
                coverage_level="typed",
                input_contract_ref="x",
                output_contract_ref="y",
                test_refs=("z",),
                source_refs=("w",),
            ),
        ),
    )
    counts = coverage.coverage_counts(manifest)
    assert counts["raw"] == 1
    assert counts["typed"] == 1


def test_raw_coverage_decision_with_wrong_policy_does_not_satisfy_typed_count() -> None:
    contract = _make_contract()
    manifest = CoverageManifest(
        schema_version=1,
        decisions=(
            CoverageDecision(
                operation_id="auth.legacy_login",
                coverage_level="raw",
                raw_argv_policy="Sequence[str]",
            ),
        ),
    )
    report = coverage.build_coverage_report(contract=contract, manifest=manifest)
    assert report.coverage["typed"] == 0
    assert report.coverage["raw"] == 1
