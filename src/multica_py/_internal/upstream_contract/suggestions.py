from __future__ import annotations

from .models import (
    CoverageDecision,
    CoverageManifest,
    ManifestSuggestion,
    OperationBinding,
    UpstreamContractDiff,
)


def generate_manifest_suggestions(
    diff: UpstreamContractDiff,
    manifest: CoverageManifest,
) -> tuple[ManifestSuggestion, ...]:
    out: list[ManifestSuggestion] = []
    for change in diff.changes:
        if change.severity in ("doc_only", "provenance_only"):
            continue
        if not change.affected_operations:
            continue
        for op_id in change.affected_operations:
            if op_id == "unresolved":
                continue
            out.append(
                ManifestSuggestion(
                    operation_id=op_id,
                    command_path=change.command_path,
                    change_kind=change.kind,
                    severity=change.severity,
                    coverage_level="incomplete",
                    reason="applied suggestions remain incomplete until maintainer decides",
                )
            )
    return tuple(out)


def generate_changelog_fragment(diff: UpstreamContractDiff) -> str:
    breaking = sum(1 for c in diff.changes if c.severity == "breaking")
    additive = sum(1 for c in diff.changes if c.severity == "additive")
    potentially = sum(1 for c in diff.changes if c.severity == "potentially_breaking")
    return (
        "## Upstream compatibility\n"
        f"- breaking: {breaking}\n"
        f"- potentially breaking: {potentially}\n"
        f"- additive: {additive}\n"
        "- See candidate contract, upstream diff, and impact map for details.\n"
    )


def generate_implementation_tasks(
    diff: UpstreamContractDiff,
) -> tuple[str, ...]:
    out: list[str] = []
    for change in diff.changes:
        if change.severity in ("doc_only", "provenance_only"):
            continue
        out.append(f"- [{change.severity}] {' '.join(change.command_path)}: {change.kind}")
    if not out:
        out.append("- No new implementation tasks required.")
    return tuple(out)


def apply_manifest_suggestions(
    manifest: CoverageManifest,
    suggestions: tuple[ManifestSuggestion, ...],
) -> CoverageManifest:
    """Apply manifest suggestions as ``coverage_level=incomplete`` rows."""
    by_id: dict[str, CoverageDecision] = {
        decision.operation_id: decision for decision in manifest.decisions
    }
    for suggestion in suggestions:
        binding = OperationBinding(command_path=suggestion.command_path)
        existing = by_id.get(suggestion.operation_id)
        if existing is None:
            by_id[suggestion.operation_id] = CoverageDecision(
                operation_id=suggestion.operation_id,
                coverage_level="incomplete",
                bindings=(binding,),
                reason=suggestion.reason,
            )
            continue
        bindings = existing.bindings
        if binding not in bindings:
            bindings = bindings + (binding,)
        by_id[suggestion.operation_id] = CoverageDecision(
            operation_id=existing.operation_id,
            coverage_level="incomplete",
            bindings=bindings,
            input_contract_ref=existing.input_contract_ref,
            output_contract_ref=existing.output_contract_ref,
            test_refs=existing.test_refs,
            source_refs=existing.source_refs,
            reason=suggestion.reason,
            raw_argv_policy=existing.raw_argv_policy,
            shares_implementation_with=existing.shares_implementation_with,
        )
    return CoverageManifest(schema_version=manifest.schema_version, decisions=tuple(by_id.values()))
