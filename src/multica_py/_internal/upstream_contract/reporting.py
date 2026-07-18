from __future__ import annotations

import msgspec

from .models import CoverageReport, ReportFailure, UpstreamContractDiff
from .schema import REPORT_SCHEMA_VERSION

EXIT_CLEAN = 0
EXIT_COVERAGE_GAP = 2
EXIT_INVALID_ARTIFACT = 3
EXIT_COLLECTOR_FAILURE = 4
EXIT_SOURCE_MISMATCH = 5
EXIT_UNRESOLVED_BREAKING = 6
EXIT_USAGE = 64


def empty_report(status: str = "clean") -> CoverageReport:
    return CoverageReport(schema_version=REPORT_SCHEMA_VERSION, status=status)


def add_failure(report: CoverageReport, failure: ReportFailure) -> CoverageReport:
    return msgspec.structs.replace(report, failures=report.failures + (failure,))


def format_human_summary(report: CoverageReport) -> str:
    """Render the four-line human summary oracle from a coverage report."""
    supported = report.supported
    cov = report.coverage
    manifest_rows = cov.get("manifest_rows", (len(cov) and sum(cov.values())) or 0)
    fail_total = len(report.failures)
    cov_fail = sum(
        1
        for failure in report.failures
        if failure.code.startswith("MISSING")
        or failure.code == "INCOMPLETE_BINDING"
        or failure.code == "COVERAGE_INCOMPLETE"
        or failure.code == "ORPHAN_MANIFEST_ROW"
        or failure.code == "DUPLICATE_OWNERSHIP"
    )
    invalid = sum(1 for failure in report.failures if failure.code == "INVALID_ARTIFACT")
    unresolved = sum(1 for failure in report.failures if failure.severity == "breaking")
    tag = supported.tag if supported.tag is not None else "none"
    lines = [
        f"Multica upstream coverage: {report.status}",
        (
            f"Supported: version={supported.version or '?'} "
            f"tag={tag} "
            f"commit={supported.commit or '?'} "
            f"semantic_hash={supported.semantic_hash or '?'}"
        ),
        (
            f"Inventory: commands={supported.command_count} "
            f"manifest_rows={manifest_rows} "
            f"typed={cov.get('typed', 0)} raw={cov.get('raw', 0)} "
            f"process={cov.get('process', 0)} unsupported={cov.get('unsupported', 0)} "
            f"legacy={cov.get('legacy', 0)} incomplete={cov.get('incomplete', 0)}"
        ),
        (
            f"Failures: total={fail_total} coverage={cov_fail} "
            f"invalid={invalid} unresolved_breaking={unresolved}"
        ),
    ]
    if report.failures:
        lines.append("")
        lines.append("Failure details:")
        for failure in report.failures:
            target = failure.command or failure.operation_id or failure.path or ""
            lines.append(f"  - {failure.code}: {target} ({failure.severity})")
    return "\n".join(lines) + "\n"


def exit_code_for_diff_severity(diff: UpstreamContractDiff) -> int:
    if diff.unresolved_breaking:
        return EXIT_UNRESOLVED_BREAKING
    if any(change.severity == "potentially_breaking" for change in diff.changes):
        return EXIT_COVERAGE_GAP
    if any(change.severity == "breaking" for change in diff.changes):
        return EXIT_UNRESOLVED_BREAKING
    if any(change.severity == "mismatch" for change in diff.changes):
        return EXIT_SOURCE_MISMATCH
    return EXIT_CLEAN
