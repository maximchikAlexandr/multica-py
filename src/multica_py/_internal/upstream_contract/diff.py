from __future__ import annotations

import msgspec

from .models import (
    CommandContract,
    DiffEntry,
    FlagContract,
    JsonScalar,
    SemanticCLIContract,
    UpstreamContractDiff,
)
from .schema import DIFF_SCHEMA_VERSION, SEVERITIES, SEVERITY_BY_KIND

__all__ = ["SEVERITIES", "SEVERITY_BY_KIND", "diff_contracts", "resolve_affected_operations"]


def diff_contracts(
    before: SemanticCLIContract,
    after: SemanticCLIContract,
) -> UpstreamContractDiff:
    before_cmds = {c.path: c for c in before.commands}
    after_cmds = {c.path: c for c in after.commands}
    changes: list[DiffEntry] = []
    for path, before_cmd in before_cmds.items():
        after_cmd = after_cmds.get(path)
        if after_cmd is None:
            changes.append(
                DiffEntry(
                    kind="command_removed",
                    severity=SEVERITY_BY_KIND["command_removed"],
                    command_path=path,
                    before=_command_summary(before_cmd),
                    after=None,
                    message=f"command {' '.join(path)} removed",
                )
            )
            continue
        changes.extend(_diff_command(before_cmd, after_cmd))
    for path, after_cmd in after_cmds.items():
        if path in before_cmds:
            continue
        changes.append(
            DiffEntry(
                kind="command_added",
                severity=SEVERITY_BY_KIND["command_added"],
                command_path=path,
                before=None,
                after=_command_summary(after_cmd),
                message=f"new command {' '.join(path)}",
            )
        )
    changes = _apply_rename_heuristics(changes, before_cmds, after_cmds)
    summary = _summary(changes)
    unresolved = any(c.severity in ("breaking", "mismatch") for c in changes)
    return UpstreamContractDiff(
        schema_version=DIFF_SCHEMA_VERSION,
        changes=tuple(changes),
        summary=summary,
        semantic_hash_before=before.artifact.semantic_hash,
        semantic_hash_after=after.artifact.semantic_hash,
        unresolved_breaking=unresolved,
    )


def resolve_affected_operations(
    diff: UpstreamContractDiff,
    bindings_index: dict[tuple[str, ...], tuple[str, ...]],
) -> UpstreamContractDiff:
    new_changes: list[DiffEntry] = []
    for change in diff.changes:
        if change.affected_operations:
            new_changes.append(change)
            continue
        op_ids = bindings_index.get(change.command_path, ())
        if not op_ids:
            new_changes.append(msgspec.structs.replace(change, affected_operations=("unresolved",)))
        else:
            new_changes.append(msgspec.structs.replace(change, affected_operations=op_ids))
    return msgspec.structs.replace(diff, changes=tuple[DiffEntry, ...](new_changes))


def _apply_rename_heuristics(
    changes: list[DiffEntry],
    before_cmds: dict[tuple[str, ...], CommandContract],
    after_cmds: dict[tuple[str, ...], CommandContract],
) -> list[DiffEntry]:
    removed_indices = [idx for idx, change in enumerate(changes) if change.kind == "command_removed"]
    added_indices = [idx for idx, change in enumerate(changes) if change.kind == "command_added"]
    if not removed_indices or not added_indices:
        return changes
    paired_removed: set[int] = set()
    paired_added: set[int] = set()
    rename_entries: list[DiffEntry] = []
    for r_idx in removed_indices:
        removed_entry = changes[r_idx]
        before_cmd = before_cmds[removed_entry.command_path]
        best_score = 0
        best_a_idx = -1
        for a_idx in added_indices:
            if a_idx in paired_added:
                continue
            added_entry = changes[a_idx]
            score = _rename_similarity(before_cmd, after_cmds[added_entry.command_path])
            if score > best_score:
                best_score = score
                best_a_idx = a_idx
        if best_score >= 3 and best_a_idx >= 0:
            added_entry = changes[best_a_idx]
            after_cmd = after_cmds[added_entry.command_path]
            rename_entries.append(
                DiffEntry(
                    kind="command_moved_or_renamed",
                    severity=SEVERITY_BY_KIND["command_moved_or_renamed"],
                    command_path=removed_entry.command_path,
                    before=_command_summary(before_cmd),
                    after=_command_summary(after_cmd),
                    suggested_action="review",
                    message=(
                        f"possible rename from {' '.join(removed_entry.command_path)} "
                        f"to {' '.join(added_entry.command_path)} (heuristic; confirm binding)"
                    ),
                )
            )
            paired_removed.add(r_idx)
            paired_added.add(best_a_idx)
    if not rename_entries:
        return changes
    skip = paired_removed | paired_added
    kept = [change for idx, change in enumerate(changes) if idx not in skip]
    return kept + rename_entries


def _rename_similarity(before: CommandContract, after: CommandContract) -> int:
    score = 0
    if before.use == after.use:
        score += 3
    if before.aliases and after.aliases and set(before.aliases) & set(after.aliases):
        score += 2
    before_flags = {flag.name for flag in before.flags}
    after_flags = {flag.name for flag in after.flags}
    if before_flags and after_flags:
        overlap = len(before_flags & after_flags)
        union = len(before_flags | after_flags)
        if union and overlap / union >= 0.5:
            score += 2
    return score


def _diff_command(
    before: CommandContract,
    after: CommandContract,
) -> list[DiffEntry]:
    entries: list[DiffEntry] = []
    if before.use != after.use:
        entries.append(
            DiffEntry(
                kind="doc_only_changed",
                severity=SEVERITY_BY_KIND["doc_only_changed"],
                command_path=after.path,
                before=before.use,
                after=after.use,
                message="use string changed (documentation only)",
            )
        )
    if before.aliases != after.aliases:
        added = tuple(sorted(set(after.aliases) - set(before.aliases)))
        removed = tuple(sorted(set(before.aliases) - set(after.aliases)))
        if added and not removed:
            entries.append(
                DiffEntry(
                    kind="alias_added",
                    severity=SEVERITY_BY_KIND["alias_added"],
                    command_path=after.path,
                    before=list(before.aliases),
                    after=list(after.aliases),
                    message=f"aliases added: {', '.join(added)}",
                )
            )
        if removed and not added:
            entries.append(
                DiffEntry(
                    kind="alias_removed",
                    severity=SEVERITY_BY_KIND["alias_removed"],
                    command_path=after.path,
                    before=list(before.aliases),
                    after=list(after.aliases),
                    message=f"aliases removed: {', '.join(removed)}",
                )
            )
        if added and removed:
            entries.append(
                DiffEntry(
                    kind="alias_changed",
                    severity=SEVERITY_BY_KIND["alias_changed"],
                    command_path=after.path,
                    before=list(before.aliases),
                    after=list(after.aliases),
                    message="aliases changed",
                )
            )
    if before.hidden != after.hidden:
        kind = "command_hidden" if after.hidden else "command_visible"
        entries.append(
            DiffEntry(
                kind=kind,
                severity=SEVERITY_BY_KIND[kind],
                command_path=after.path,
                before=before.hidden,
                after=after.hidden,
                message=f"hidden state changed to {after.hidden}",
            )
        )
    if (before.deprecated or None) != (after.deprecated or None):
        kind = "deprecation_added" if after.deprecated else "deprecation_removed"
        entries.append(
            DiffEntry(
                kind=kind,
                severity=SEVERITY_BY_KIND[kind],
                command_path=after.path,
                before=before.deprecated,
                after=after.deprecated,
                message="deprecation message changed",
            )
        )
    entries.extend(_diff_execution(before, after))
    entries.extend(_diff_args(before, after))
    entries.extend(_diff_flags(before, after))
    entries.extend(_diff_output(before, after))
    if not entries and _command_provenance_changed(before, after):
        entries.append(
            DiffEntry(
                kind="provenance_only_changed",
                severity=SEVERITY_BY_KIND["provenance_only_changed"],
                command_path=after.path,
                before=_provenance_summary(before),
                after=_provenance_summary(after),
                message="command provenance changed without semantic differences",
            )
        )
    return entries


def _diff_execution(
    before: CommandContract,
    after: CommandContract,
) -> list[DiffEntry]:
    before_exec = before.execution
    after_exec = after.execution
    if (
        before_exec.interactive == after_exec.interactive
        and before_exec.streaming == after_exec.streaming
        and before_exec.managed_process == after_exec.managed_process
        and before_exec.requires_server == after_exec.requires_server
        and (before_exec.exit_behavior or None) == (after_exec.exit_behavior or None)
    ):
        return []
    return [
        DiffEntry(
            kind="execution_mode_changed",
            severity=SEVERITY_BY_KIND["execution_mode_changed"],
            command_path=after.path,
            before={
                "interactive": before_exec.interactive,
                "streaming": before_exec.streaming,
                "managed_process": before_exec.managed_process,
                "requires_server": before_exec.requires_server,
                "exit_behavior": before_exec.exit_behavior,
            },
            after={
                "interactive": after_exec.interactive,
                "streaming": after_exec.streaming,
                "managed_process": after_exec.managed_process,
                "requires_server": after_exec.requires_server,
                "exit_behavior": after_exec.exit_behavior,
            },
            message="execution mode changed",
        )
    ]


def _command_provenance_changed(before: CommandContract, after: CommandContract) -> bool:
    return before.source != after.source or before.contract_hash != after.contract_hash


def _provenance_summary(cmd: CommandContract) -> dict[str, JsonScalar | list[str] | None]:
    source = cmd.source
    return {
        "contract_hash": cmd.contract_hash,
        "source_path": source.path if source else None,
        "source_symbol": source.symbol if source else None,
    }


def _diff_args(
    before: CommandContract,
    after: CommandContract,
) -> list[DiffEntry]:
    entries: list[DiffEntry] = []
    if before.args.validators != after.args.validators:
        entries.append(
            DiffEntry(
                kind="argument_changed",
                severity=SEVERITY_BY_KIND["argument_changed"],
                command_path=after.path,
                before=list(before.args.validators),
                after=list(after.args.validators),
                message="argument validators changed",
            )
        )
    if before.args.min == after.args.min and before.args.max == after.args.max:
        return entries
    severity = "breaking" if after.args.min > before.args.min else "additive"
    kind = "argument_added_required" if severity == "breaking" else "argument_changed"
    entries.append(
        DiffEntry(
            kind=kind,
            severity=SEVERITY_BY_KIND.get(kind, severity),
            command_path=after.path,
            before={"min": before.args.min, "max": before.args.max},
            after={"min": after.args.min, "max": after.args.max},
            message="argument count changed",
        )
    )
    return entries


def _diff_flags(
    before: CommandContract,
    after: CommandContract,
) -> list[DiffEntry]:
    before_flags = {f.name: f for f in before.flags}
    after_flags = {f.name: f for f in after.flags}
    entries: list[DiffEntry] = []
    for name, before_flag in before_flags.items():
        after_flag = after_flags.get(name)
        if after_flag is None:
            entries.append(
                DiffEntry(
                    kind="flag_removed",
                    severity=SEVERITY_BY_KIND["flag_removed"],
                    command_path=after.path,
                    flag_name=name,
                    before=_flag_summary(before_flag),
                    after=None,
                    message=f"flag --{name} removed",
                )
            )
            continue
        entries.extend(_diff_flag(before.path, before_flag, after_flag))
    for name, after_flag in after_flags.items():
        if name in before_flags:
            continue
        kind = "flag_added_required" if after_flag.required else "flag_added_optional"
        entries.append(
            DiffEntry(
                kind=kind,
                severity=SEVERITY_BY_KIND[kind],
                command_path=after.path,
                flag_name=name,
                before=None,
                after=_flag_summary(after_flag),
                message=f"flag --{name} added",
            )
        )
    entries.extend(_diff_inherited_flags(before, after, before_flags, after_flags))
    return entries


def _diff_inherited_flags(
    before: CommandContract,
    after: CommandContract,
    before_flags: dict[str, FlagContract],
    after_flags: dict[str, FlagContract],
) -> list[DiffEntry]:
    entries: list[DiffEntry] = []
    for name in sorted(set(before_flags) | set(after_flags)):
        before_flag = before_flags.get(name)
        after_flag = after_flags.get(name)
        if before_flag is None or after_flag is None:
            continue
        if before_flag.inherited == after_flag.inherited:
            continue
        entries.append(
            DiffEntry(
                kind="flag_changed_type",
                severity=SEVERITY_BY_KIND["flag_changed_type"],
                command_path=after.path,
                flag_name=name,
                before=before_flag.inherited,
                after=after_flag.inherited,
                message=f"--{name} inherited state changed",
            )
        )
    return entries


def _diff_flag(
    path: tuple[str, ...],
    before: FlagContract,
    after: FlagContract,
) -> list[DiffEntry]:
    entries: list[DiffEntry] = []
    if before.type != after.type:
        entries.append(
            DiffEntry(
                kind="flag_changed_type",
                severity=SEVERITY_BY_KIND["flag_changed_type"],
                command_path=path,
                flag_name=before.name,
                before=before.type,
                after=after.type,
                message=f"--{before.name} type changed",
            )
        )
    if before.required != after.required:
        kind = "flag_added_required" if after.required else "flag_made_optional"
        entries.append(
            DiffEntry(
                kind=kind,
                severity=SEVERITY_BY_KIND[kind],
                command_path=path,
                flag_name=before.name,
                before=before.required,
                after=after.required,
                message=f"--{before.name} required state changed",
            )
        )
    if (before.default or None) != (after.default or None):
        entries.append(
            DiffEntry(
                kind="flag_changed_default",
                severity=SEVERITY_BY_KIND["flag_changed_default"],
                command_path=path,
                flag_name=before.name,
                before=before.default,
                after=after.default,
                message=f"--{before.name} default changed",
            )
        )
    if before.enum != after.enum:
        before_set, after_set = set(before.enum), set(after.enum)
        kind = (
            "flag_enum_narrowed"
            if after_set.issubset(before_set) and after_set != before_set
            else "flag_enum_widened"
        )
        entries.append(
            DiffEntry(
                kind=kind,
                severity=SEVERITY_BY_KIND[kind],
                command_path=path,
                flag_name=before.name,
                before=list(before.enum),
                after=list(after.enum),
                message=f"--{before.name} enum changed",
            )
        )
    if before.shorthand != after.shorthand:
        entries.append(
            DiffEntry(
                kind="flag_renamed",
                severity=SEVERITY_BY_KIND["flag_renamed"],
                command_path=path,
                flag_name=before.name,
                before=before.shorthand,
                after=after.shorthand,
                message=f"--{before.name} shorthand changed",
            )
        )
    return entries


def _diff_output(
    before: CommandContract,
    after: CommandContract,
) -> list[DiffEntry]:
    entries: list[DiffEntry] = []
    if (
        before.output.mode == after.output.mode
        and before.output.schema_ref == after.output.schema_ref
    ):
        return entries
    if before.output.mode != after.output.mode:
        entries.append(
            DiffEntry(
                kind="output_contract_type_changed",
                severity=SEVERITY_BY_KIND["output_contract_type_changed"],
                command_path=after.path,
                before=before.output.mode,
                after=after.output.mode,
                message="output mode changed",
            )
        )
    if before.output.schema_ref != after.output.schema_ref:
        added = before.output.schema_ref is None and after.output.schema_ref is not None
        kind = "output_contract_added" if added else "output_contract_removed"
        entries.append(
            DiffEntry(
                kind=kind,
                severity=SEVERITY_BY_KIND[kind],
                command_path=after.path,
                before=before.output.schema_ref,
                after=after.output.schema_ref,
                message="output schema_ref changed",
            )
        )
    return entries


def _summary(changes: list[DiffEntry]) -> dict[str, int]:
    counts = dict.fromkeys(SEVERITIES, 0)
    counts["total"] = len(changes)
    for change in changes:
        counts[change.severity] = counts.get(change.severity, 0) + 1
    return counts


def _command_summary(cmd: CommandContract) -> dict[str, JsonScalar | list[str]]:
    return {
        "path": list(cmd.path),
        "use": cmd.use,
        "hidden": cmd.hidden,
        "deprecated": cmd.deprecated,
    }


def _flag_summary(flag: FlagContract) -> dict[str, JsonScalar | list[str]]:
    return {
        "name": flag.name,
        "type": flag.type,
        "required": flag.required,
        "default": flag.default,
        "enum": list(flag.enum),
        "inherited": flag.inherited,
    }
