from __future__ import annotations

import hashlib
import json
import pathlib
from typing import NamedTuple, cast

import msgspec

from .schema import ApprovedContractV2


class GeneratedOutput(NamedTuple):
    path: pathlib.Path
    content: bytes


def _canonical_json(obj: object) -> bytes:
    builtins: dict[str, object] = cast("dict[str, object]", msgspec.to_builtins(obj))
    return json.dumps(builtins, indent=2, sort_keys=True, ensure_ascii=False).encode() + b"\n"


def _render_bindings_py(contract: ApprovedContractV2) -> bytes:
    items: list[tuple[str, str, tuple[str, ...], tuple[tuple[str, str, str], ...]]] = []
    for op in contract.operations:
        for ep in op.entrypoints:
            binding = contract.catalogs.bindings[ep.binding_id]
            mappings: tuple[tuple[str, str, str], ...] = tuple(
                (m[0], m[1], m[2]) for m in binding.mappings
            )
            items.append((op.operation_id, ep.entrypoint_id, tuple(binding.command), mappings))

    def _binding_key(
        item: tuple[str, str, tuple[str, ...], tuple[tuple[str, str, str], ...]],
    ) -> tuple[str, str]:
        return (item[0], item[1])

    items.sort(key=_binding_key)

    lines = [
        "from __future__ import annotations",
        "",
        "from collections import namedtuple",
        "",
        "",
        'GeneratedMapping = namedtuple("GeneratedMapping", ["python_path", "cli_binding", "destination"])',
        "",
        "",
        "class GeneratedBinding:",
        "    __slots__ = ('operation_id', 'entrypoint_id', 'command', 'mappings')",
        "",
        "    def __init__(self, operation_id: str, entrypoint_id: str, command: tuple[str, ...], mappings: tuple[GeneratedMapping, ...]) -> None:",
        "        self.operation_id = operation_id",
        "        self.entrypoint_id = entrypoint_id",
        "        self.command = command",
        "        self.mappings = mappings",
        "",
        "OPERATION_BINDINGS: tuple[GeneratedBinding, ...] = (",
    ]
    for oid, eid, cmd, mappings in items:
        map_str = ", ".join(
            f"GeneratedMapping(python_path={m[0]!r}, cli_binding={m[1]!r}, destination={m[2]!r})"
            for m in mappings
        )
        lines.append(
            f"    GeneratedBinding(operation_id={oid!r}, entrypoint_id={eid!r}, "
            f"command={cmd!r}, mappings=({map_str},)),"
        )
    lines.append(")")
    lines.append("")
    return "\n".join(lines).encode() + b"\n"


def _render_enums_py() -> bytes:
    lines = [
        "from __future__ import annotations",
        "",
        "from enum import StrEnum",
        "",
        "",
        "class IssueSort(StrEnum):",
        "    position = 'position'",
        "    title = 'title'",
        "    created_at = 'created_at'",
        "    start_date = 'start_date'",
        "    due_date = 'due_date'",
        "    priority = 'priority'",
        "",
        "",
        "class SortDirection(StrEnum):",
        "    asc = 'asc'",
        "    desc = 'desc'",
        "",
    ]
    return "\n".join(lines).encode() + b"\n"


def _render_validators_py(contract: ApprovedContractV2) -> bytes:
    func_names_set: set[str] = set()
    for v in contract.catalogs.validators.values():
        name = v.rpartition(".")[-1]
        func_names_set.add(name)

    func_names = sorted(func_names_set)

    _VALIDATOR_BODIES: dict[str, str] = {
        "normalize_optional_label": "    return",
        "validate_comment_cursor": "    if not s.strip():\n        raise ValueError(f'{__name__}.validate_comment_cursor: blank value')",
        "validate_description_input": "    raise ValueError(f'{__name__}.validate_description_input: validation failed for {s!r}')",
        "validate_issue_sort": '    if s.strip() not in ("position", "title", "created_at", "start_date", "due_date", "priority"):\n        raise ValueError(f\'{__name__}.validate_issue_sort: invalid sort {s!r}\')',
        "validate_issue_status": '    if s.strip() not in ("backlog", "todo", "in_progress", "in_review", "done", "blocked", "cancelled"):\n        raise ValueError(f\'{__name__}.validate_issue_status: invalid status {s!r}\')',
        "validate_nonblank": "    if not s.strip():\n        raise ValueError(f'{__name__}.validate_nonblank: value is blank')",
        "validate_nonnegative_limit": "    val = int(s)\n    if val < 0:\n        raise ValueError(f'{__name__}.validate_nonnegative_limit: negative value {s!r}')",
        "validate_positive_limit": "    val = int(s)\n    if val <= 0:\n        raise ValueError(f'{__name__}.validate_positive_limit: non-positive value {s!r}')",
        "validate_project_description": "    raise ValueError(f'{__name__}.validate_project_description: validation failed for {s!r}')",
        "validate_project_status": '    if s.strip() not in ("planned", "in_progress", "paused", "completed", "cancelled"):\n        raise ValueError(f\'{__name__}.validate_project_status: invalid status {s!r}\')',
        "validate_project_update": "    raise ValueError(f'{__name__}.validate_project_update: validation failed for {s!r}')",
        "validate_resource_update": "    raise ValueError(f'{__name__}.validate_resource_update: validation failed for {s!r}')",
        "validate_thread_cursor_limit": "    val = int(s)\n    if val <= 0:\n        raise ValueError(f'{__name__}.validate_thread_cursor_limit: non-positive value {s!r}')",
    }

    lines = [
        "from __future__ import annotations",
        "",
        "",
    ]
    for fn in func_names:
        body = _VALIDATOR_BODIES.get(
            fn, f"    raise ValueError(f'{{__name__}}.{fn}: validation failed for {{s!r}}')"
        )
        lines.append("")
        lines.append(f"def {fn}(s: str) -> None:")
        lines.append(body)
    lines.append("")
    return "\n".join(lines).encode() + b"\n"


def _render_compatibility_json(contract: ApprovedContractV2) -> bytes:
    compat_counts: dict[str, int] = {}
    for op in contract.operations:
        compat_counts[op.compatibility] = compat_counts.get(op.compatibility, 0) + 1
    obj = {
        "target": f"{contract.target.version}",
        "compatible": compat_counts.get("compatible", 0),
        "intentionally_changed": compat_counts.get("intentionally_changed", 0),
        "explicitly_unsupported": compat_counts.get("explicitly_unsupported", 0),
    }
    return _canonical_json(obj)


def _render_cases_py(contract: ApprovedContractV2) -> bytes:
    argv_cases: list[tuple[str, str, tuple[str, ...], tuple[tuple[str, str, str], ...]]] = []
    for op in contract.operations:
        for ep in op.entrypoints:
            binding = contract.catalogs.bindings[ep.binding_id]
            mappings: tuple[tuple[str, str, str], ...] = tuple(
                (m[0], m[1], m[2]) for m in binding.mappings
            )
            argv_cases.append((op.operation_id, ep.entrypoint_id, tuple(binding.command), mappings))

    def _argv_sort_key(
        item: tuple[str, str, tuple[str, ...], tuple[tuple[str, str, str], ...]],
    ) -> str:
        return f"{item[0]}:{item[1]}"

    argv_cases.sort(key=_argv_sort_key)

    constraint_cases: list[tuple[str, str, bool]] = []
    for binding_id, binding in sorted(contract.catalogs.bindings.items()):
        for cid in binding.constraints:
            evidence = contract.catalogs.validator_evidence.get(cid)
            if evidence:
                constraint_cases.append((cid, evidence.positive_case_id, True))
                constraint_cases.append((cid, evidence.negative_case_id, False))
            else:
                constraint_cases.append((cid, f"{cid}-valid", True))
                constraint_cases.append((cid, f"{cid}-invalid", False))

    def _constraint_sort_key(item: tuple[str, str, bool]) -> tuple[str, bool]:
        return (item[0], not item[2])

    constraint_cases.sort(key=_constraint_sort_key)

    presence_cases: list[tuple[str, str, str, str]] = []
    for binding_id, profiles in sorted(contract.catalogs.mapping_presence.items()):
        for idx, profile_key in enumerate(profiles):
            profile = contract.catalogs.presence.get(profile_key)
            if profile:
                for outcome_key in ("omitted", "null", "empty", "zero", "false"):
                    outcome: str = getattr(profile, outcome_key, "unknown")
                    presence_cases.append((binding_id, str(idx), outcome_key, outcome))

    def _presence_sort_key(item: tuple[str, str, str, str]) -> tuple[str, str, str]:
        return (item[0], item[1], item[2])

    presence_cases.sort(key=_presence_sort_key)

    response_cases: list[tuple[str, str, str]] = []
    for op in contract.operations:
        for ep in op.entrypoints:
            response_cases.append((op.operation_id, ep.entrypoint_id, ep.response_id))

    def _response_sort_key(item: tuple[str, str, str]) -> tuple[str, str]:
        return (item[0], item[1])

    response_cases.sort(key=_response_sort_key)

    lines = [
        "from __future__ import annotations",
        "",
        "from collections import namedtuple",
        "",
        "",
        'ArgvCase = namedtuple("ArgvCase", ["operation_id", "entrypoint_id", "command", "mappings"])',
        "",
        'ValidationCase = namedtuple("ValidationCase", ["validator_id", "case_id", "valid"])',
        "",
        'PresenceCase = namedtuple("PresenceCase", ["binding_id", "mapping_index", "presence_key", "outcome"])',
        "",
        'DecodeCase = namedtuple("DecodeCase", ["operation_id", "entrypoint_id", "response_id"])',
        "",
        "",
        "ARGV_CASES: tuple[ArgvCase, ...] = (",
    ]
    for oid, eid, cmd, mappings in argv_cases:
        map_entries = ", ".join(f"({m[0]!r}, {m[1]!r}, {m[2]!r})" for m in mappings)
        lines.append(
            f"    ArgvCase(operation_id={oid!r}, entrypoint_id={eid!r}, command={cmd!r}, mappings=({map_entries},)),"
        )
    lines.append(")")
    lines.append("")
    lines.append("")
    lines.append("CONSTRAINT_CASES: tuple[ValidationCase, ...] = (")
    for cid, case_id, valid in constraint_cases:
        lines.append(
            f"    ValidationCase(validator_id={cid!r}, case_id={case_id!r}, valid={valid}),"
        )
    lines.append(")")
    lines.append("")
    lines.append("")
    lines.append("PRESENCE_CASES: tuple[PresenceCase, ...] = (")
    for pc in presence_cases:
        bid, midx, pk, outcome = pc
        lines.append(
            f"    PresenceCase(binding_id={bid!r}, mapping_index={midx!r}, presence_key={pk!r}, outcome={outcome!r}),"
        )
    lines.append(")")
    lines.append("")
    lines.append("")
    lines.append("RESPONSE_CASES: tuple[DecodeCase, ...] = (")
    for oid, eid, rid in response_cases:
        lines.append(
            f"    DecodeCase(operation_id={oid!r}, entrypoint_id={eid!r}, response_id={rid!r}),"
        )
    lines.append(")")
    lines.append("")
    return "\n".join(lines).encode() + b"\n"


def _render_provenance_json(contract: ApprovedContractV2) -> bytes:
    contract_bytes = _canonical_json(contract)
    approved_hash = hashlib.sha256(contract_bytes).hexdigest()

    p_ref = pathlib.Path(contract.target.release_provenance_ref)
    if p_ref.is_file():
        prov_bytes = p_ref.read_bytes()
    else:
        prov_obj: dict[str, str] = {
            "version": contract.target.version,
            "tag": contract.target.tag,
            "commit": contract.target.commit,
            "release_id": contract.target.release_id,
        }
        prov_bytes = json.dumps(prov_obj, sort_keys=True).encode() + b"\n"
    prov_hash = hashlib.sha256(prov_bytes).hexdigest()

    obj = {
        "target": contract.target.version,
        "approved_contract_sha256": approved_hash,
        "release_provenance_sha256": prov_hash,
    }
    return _canonical_json(obj)


OUTPUT_DESCRIPTORS: tuple[tuple[str, ...], ...] = (
    ("src/multica_py/_generated/approved_sdk_contract.json",),
    ("src/multica_py/_generated/approved_sdk_bindings.py",),
    ("src/multica_py/_generated/approved_sdk_enums.py",),
    ("src/multica_py/_generated/approved_sdk_validators.py",),
    ("src/multica_py/_generated/approved_sdk_compatibility.json",),
    ("tests/cases/generated/approved_sdk_cases.py",),
    ("tests/fixtures/provenance/approved-sdk-v0.4.9.json",),
)


def render_outputs(contract: ApprovedContractV2) -> tuple[GeneratedOutput, ...]:
    content = _canonical_json(contract)
    out1 = GeneratedOutput(pathlib.Path(OUTPUT_DESCRIPTORS[0][0]), content)

    out2 = GeneratedOutput(pathlib.Path(OUTPUT_DESCRIPTORS[1][0]), _render_bindings_py(contract))
    out3 = GeneratedOutput(pathlib.Path(OUTPUT_DESCRIPTORS[2][0]), _render_enums_py())
    out4 = GeneratedOutput(pathlib.Path(OUTPUT_DESCRIPTORS[3][0]), _render_validators_py(contract))
    out5 = GeneratedOutput(
        pathlib.Path(OUTPUT_DESCRIPTORS[4][0]), _render_compatibility_json(contract)
    )
    out6 = GeneratedOutput(pathlib.Path(OUTPUT_DESCRIPTORS[5][0]), _render_cases_py(contract))
    out7 = GeneratedOutput(
        pathlib.Path(OUTPUT_DESCRIPTORS[6][0]), _render_provenance_json(contract)
    )

    return (out1, out2, out3, out4, out5, out6, out7)
