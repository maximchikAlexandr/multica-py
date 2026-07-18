from __future__ import annotations

import msgspec

from ..diff import diff_contracts
from ..models import DiffEntry, SemanticCLIContract, UpstreamContractDiff


def exporter_help_agree(
    exporter: SemanticCLIContract,
    help_contract: SemanticCLIContract,
) -> bool:
    """Return whether exporter and help-parser inventories agree semantically.

    Verified trust requires complete parity: no additive, breaking,
    potentially_breaking, or mismatch differences. Doc-only and
    provenance-only deltas are ignored.
    """
    diff = diff_contracts(exporter, help_contract)
    blocking = ("mismatch", "breaking", "additive", "potentially_breaking")
    return not any(c.severity in blocking for c in diff.changes)


def classify_exporter_help_mismatch(
    exporter: SemanticCLIContract,
    help: SemanticCLIContract,
) -> UpstreamContractDiff:
    """Classify the diff between exporter output and help-parser fallback.

    Per SC-017, this is reported as a `mismatch` and never as a coverage gap.
    """
    diff = diff_contracts(exporter, help)
    return msgspec.structs.replace(
        diff,
        changes=tuple[DiffEntry, ...](_as_mismatch(c) for c in diff.changes),
    )


def _as_mismatch(change: DiffEntry) -> DiffEntry:
    if change.severity in ("doc_only", "provenance_only"):
        return change
    return msgspec.structs.replace(
        change,
        kind="source_exporter_help_mismatch",
        severity="mismatch",
        message=f"exporter/help disagreement: {change.message}",
    )
