from __future__ import annotations

import pathlib

import msgspec

from .models import (
    CandidateSummary,
    CoverageDecision,
    CoverageManifest,
    CoverageReport,
    ObservedSummary,
    ReportFailure,
    SemanticCLIContract,
    SupportedSummary,
    UpstreamContractDiff,
    UpstreamState,
)
from .reporting import add_failure, empty_report

COVERAGE_LEVELS: tuple[str, ...] = (
    "typed",
    "raw",
    "process",
    "unsupported",
    "legacy",
    "incomplete",
)

RAW_ARGV_POLICY_TOKENS: tuple[str, ...] = (
    "Sequence[str]",
    "List[str]",
    "args",
    "argv",
    "command",
    "tokens",
    "shell",
    "string",
)


def coverage_counts(manifest: CoverageManifest) -> dict[str, int]:
    counts = dict.fromkeys(COVERAGE_LEVELS, 0)
    for decision in manifest.decisions:
        level = decision.coverage_level
        if level in counts:
            counts[level] += 1
        else:
            counts["incomplete"] += 1
    counts["manifest_rows"] = len(manifest.decisions)
    return counts


def build_coverage_report(
    *,
    contract: SemanticCLIContract,
    manifest: CoverageManifest,
    diff: UpstreamContractDiff | None = None,
    state: UpstreamState | None = None,
    repo_root: pathlib.Path | None = None,
) -> CoverageReport:
    report = empty_report(status="clean")
    counts = coverage_counts(manifest)
    report = msgspec.structs.replace(report, coverage=counts)
    report = msgspec.structs.replace(
        report,
        supported=SupportedSummary(
            version=contract.baseline.version,
            tag=contract.baseline.tag,
            commit=contract.baseline.commit,
            semantic_hash=contract.artifact.semantic_hash,
            command_count=len(contract.commands),
        ),
    )
    if state is not None and state.observed is not None:
        observed = state.observed
        report = msgspec.structs.replace(
            report,
            observed=ObservedSummary(
                version=observed.version,
                tag=observed.tag,
                release_id=observed.release_id,
                published_at=observed.published_at,
                status=observed.status,
            ),
        )
    if state is not None and state.candidate is not None:
        candidate = state.candidate
        report = msgspec.structs.replace(
            report,
            candidate=CandidateSummary(
                version=candidate.version,
                tag=candidate.tag,
                commit=candidate.commit,
                semantic_hash=candidate.semantic_hash,
                trust_level=candidate.trust_level,
            ),
        )
    if diff is not None:
        report = msgspec.structs.replace(report, upstream_diff=dict(diff.summary))
    report = _evaluate(report, contract, manifest, state=state, repo_root=repo_root)
    if diff is not None and diff.unresolved_breaking:
        report = add_failure(
            report,
            ReportFailure(
                code="UNRESOLVED_BREAKING_DIFF",
                severity="breaking",
                resolution="unresolved",
                message="candidate diff contains unresolved breaking changes",
            ),
        )
        report = msgspec.structs.replace(report, status="unresolved-breaking")
    return _finalize_status(report)


def _finalize_status(report: CoverageReport) -> CoverageReport:
    if not report.failures:
        return msgspec.structs.replace(report, status="clean")
    if report.status == "invalid" or any(
        failure.severity == "invalid"
        or failure.code in ("SEMANTIC_HASH_MISMATCH", "INVALID_ARTIFACT")
        for failure in report.failures
    ):
        return msgspec.structs.replace(report, status="invalid")
    if report.status == "unresolved-breaking" or any(
        failure.severity == "breaking" for failure in report.failures
    ):
        return msgspec.structs.replace(report, status="unresolved-breaking")
    return msgspec.structs.replace(report, status="gaps")


def _evaluate(
    report: CoverageReport,
    contract: SemanticCLIContract,
    manifest: CoverageManifest,
    *,
    state: UpstreamState | None = None,
    repo_root: pathlib.Path | None = None,
) -> CoverageReport:
    if state is not None and state.supported is not None:
        if state.supported.semantic_hash != contract.artifact.semantic_hash:
            report = add_failure(
                report,
                ReportFailure(
                    code="SEMANTIC_HASH_MISMATCH",
                    severity="invalid",
                    message=(
                        "state.supported.semantic_hash does not match "
                        "contract.artifact.semantic_hash"
                    ),
                ),
            )
            report = msgspec.structs.replace(report, status="invalid")
    bindings_index = build_bindings_index(manifest)
    contract_paths = {command.path for command in contract.commands}
    for decision_entry in manifest.decisions:
        if not _decision_is_complete(decision_entry, repo_root=repo_root):
            report = add_failure(
                report,
                ReportFailure(
                    code="COVERAGE_INCOMPLETE",
                    operation_id=decision_entry.operation_id,
                    severity="gap",
                    resolution="incomplete",
                    message=f"decision {decision_entry.operation_id} is incomplete",
                ),
            )
        bound_paths = {binding.command_path for binding in decision_entry.bindings}
        if bound_paths and not bound_paths & contract_paths:
            if decision_entry.coverage_level not in ("legacy", "unsupported"):
                report = add_failure(
                    report,
                    ReportFailure(
                        code="ORPHAN_MANIFEST_ROW",
                        operation_id=decision_entry.operation_id,
                        severity="gap",
                        resolution="unresolved",
                        message=(
                            f"manifest row {decision_entry.operation_id} "
                            "has no binding to a supported command"
                        ),
                    ),
                )
    for path, op_ids in bindings_index.items():
        if len(op_ids) > 1 and not _duplicate_ownership_allowed(manifest, op_ids):
            report = add_failure(
                report,
                ReportFailure(
                    code="DUPLICATE_OWNERSHIP",
                    command=" ".join(path),
                    path=".".join(path),
                    severity="gap",
                    resolution="unresolved",
                    message=(
                        f"command {' '.join(path)} is owned by multiple operations "
                        f"without shares_implementation_with"
                    ),
                ),
            )
    for command in contract.commands:
        path = command.path
        op_ids = bindings_index.get(path, ())
        if not op_ids:
            report = add_failure(
                report,
                ReportFailure(
                    code="MISSING_COVERAGE",
                    command=" ".join(path),
                    path=".".join(path),
                    severity="gap",
                    resolution="unresolved",
                    message=f"no coverage decision for command {' '.join(path)}",
                ),
            )
            continue
        for op_id in op_ids:
            decision: CoverageDecision | None = _lookup(manifest, op_id)
            if decision is None:
                continue
            if decision.coverage_level == "incomplete":
                report = add_failure(
                    report,
                    ReportFailure(
                        code="INCOMPLETE_BINDING",
                        operation_id=op_id,
                        command=" ".join(path),
                        path=".".join(path),
                        severity="gap",
                        resolution="incomplete",
                    ),
                )
            elif decision.coverage_level == "unsupported" and not decision.reason:
                report = add_failure(
                    report,
                    ReportFailure(
                        code="UNSUPPORTED_REASON_MISSING",
                        operation_id=op_id,
                        command=" ".join(path),
                        path=".".join(path),
                        severity="gap",
                        resolution="unresolved",
                    ),
                )
    if (
        any(f.code == "MISSING_COVERAGE" for f in report.failures)
        or any(f.code == "INCOMPLETE_BINDING" for f in report.failures)
        or any(f.code == "COVERAGE_INCOMPLETE" for f in report.failures)
        or any(f.code == "ORPHAN_MANIFEST_ROW" for f in report.failures)
        or any(f.code == "DUPLICATE_OWNERSHIP" for f in report.failures)
    ):
        report = msgspec.structs.replace(report, status="gaps")
    return report


def _duplicate_ownership_allowed(manifest: CoverageManifest, op_ids: tuple[str, ...]) -> bool:
    if len(op_ids) <= 1:
        return True
    by_id = {decision.operation_id: decision for decision in manifest.decisions}
    for index, left in enumerate(op_ids):
        for right in op_ids[index + 1 :]:
            left_decision = by_id.get(left)
            right_decision = by_id.get(right)
            if left_decision is None or right_decision is None:
                return False
            if right not in left_decision.shares_implementation_with and left not in (
                right_decision.shares_implementation_with
            ):
                return False
    return True


def _decision_is_complete(
    decision: CoverageDecision,
    *,
    repo_root: pathlib.Path | None = None,
) -> bool:
    level = decision.coverage_level
    if level not in COVERAGE_LEVELS:
        return False
    if level == "incomplete":
        return False
    if level == "typed":
        if not (
            decision.input_contract_ref is not None
            and decision.output_contract_ref is not None
            and bool(decision.test_refs)
            and bool(decision.source_refs)
        ):
            return False
        if repo_root is not None:
            return _typed_refs_exist(decision, repo_root)
        return True
    if level == "raw":
        return _raw_argv_policy_valid(decision.raw_argv_policy)
    if level == "process":
        return True
    if level == "unsupported":
        return decision.reason is not None
    if level == "legacy":
        return decision.reason is not None
    return True


def _typed_refs_exist(decision: CoverageDecision, repo_root: pathlib.Path) -> bool:
    refs: list[str] = []
    if decision.input_contract_ref is not None:
        refs.append(decision.input_contract_ref)
    if decision.output_contract_ref is not None:
        refs.append(decision.output_contract_ref)
    refs.extend(decision.test_refs)
    root = repo_root.resolve()
    for ref in refs:
        ref_path = pathlib.Path(ref)
        if ref_path.is_absolute():
            return False
        if ".." in ref_path.parts:
            return False
        resolved = (root / ref_path).resolve()
        if not resolved.is_relative_to(root):
            return False
        if not resolved.is_file():
            return False
    return True


def _raw_argv_policy_valid(policy: str | None) -> bool:
    if not policy:
        return False
    if "shell" in policy.lower():
        return False
    return policy in RAW_ARGV_POLICY_TOKENS


def _lookup(manifest: CoverageManifest, op_id: str) -> CoverageDecision | None:
    for decision in manifest.decisions:
        if decision.operation_id == op_id:
            return decision
    return None


def build_bindings_index(
    manifest: CoverageManifest,
) -> dict[tuple[str, ...], tuple[str, ...]]:
    index: dict[tuple[str, ...], list[str]] = {}
    for decision in manifest.decisions:
        for binding in decision.bindings:
            index.setdefault(binding.command_path, []).append(decision.operation_id)
    return {path: tuple(ids) for path, ids in index.items()}


def collect_contract_review_items(contract: SemanticCLIContract) -> tuple[str, ...]:
    items: list[str] = []
    for command in contract.commands:
        for item in command.args.review_items:
            if item:
                items.append(item)
    return tuple(items)
