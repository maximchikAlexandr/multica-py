from __future__ import annotations

from .coverage import build_bindings_index
from .models import (
    CoverageManifest,
    ImpactEntry,
    ImpactMap,
    UpstreamContractDiff,
)

IMPACT_SCHEMA_VERSION = 1


def build_impact(
    diff: UpstreamContractDiff,
    manifest: CoverageManifest,
) -> ImpactMap:
    index = build_bindings_index(manifest)
    entries: list[ImpactEntry] = []
    for change in diff.changes:
        if change.severity == "doc_only" or change.severity == "provenance_only":
            continue
        affected = _resolve(index, change.command_path)
        for op_id in affected:
            entries.append(
                ImpactEntry(
                    change_kind=change.kind,
                    severity=change.severity,
                    command_path=change.command_path,
                    operation_id=op_id,
                    parameters_changed=(change.flag_name,) if change.flag_name else (),
                )
            )
        if not affected:
            entries.append(
                ImpactEntry(
                    change_kind=change.kind,
                    severity=change.severity,
                    command_path=change.command_path,
                    operation_id=None,
                    unresolved_reason="no operation binding matches the changed command path",
                    parameters_changed=(change.flag_name,) if change.flag_name else (),
                )
            )
    return ImpactMap(schema_version=IMPACT_SCHEMA_VERSION, entries=tuple(entries))


def _resolve(
    index: dict[tuple[str, ...], tuple[str, ...]],
    path: tuple[str, ...],
) -> tuple[str, ...]:
    if path in index:
        return index[path]
    return ()
