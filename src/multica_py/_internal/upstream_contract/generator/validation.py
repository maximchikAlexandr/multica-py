"""Load and validate an ApprovedContractV2 from JSON.

The approved SDK contract is the only valid production generator input.
"""

from __future__ import annotations

import pathlib

import msgspec

from .schema import (
    FAMILY_DISPOSITIONS,
    PRESENCE_OUTCOMES,
    ApprovedContractV2,
)

TARGET_LITERALS: dict[str, str] = {
    "version": "0.4.9",
    "tag": "v0.4.9",
    "commit": "ecbdbda09e7b2be56cd9ccc55cee1ee360222d18",
    "release_id": "358605496",
    "release_provenance_ref": ".devlocal/artifacts/upstream-upgrades/v0.3.10..v0.4.9/release-provenance.json",
}

CATALOG_KEYS: tuple[str, ...] = (
    "types",
    "signatures",
    "bindings",
    "binding_source_refs",
    "presence",
    "mapping_presence",
    "responses",
    "decoders",
    "validators",
    "validator_evidence",
)

PRESENCE_KEYS: tuple[str, ...] = ("omitted", "null", "empty", "zero", "false")

VALID_AUTHORITY_REFS_BASE: tuple[str, ...] = (
    "target",
    "scope",
    "generation",
    "coherence",
    "live",
)


def load_approved_contract_v2(path: pathlib.Path) -> ApprovedContractV2:
    contract = msgspec.json.decode(path.read_bytes(), type=ApprovedContractV2, strict=True)
    if contract.schema_version != 2:
        raise ValueError(
            "unsupported approved contract schema_version; expected 2, got "
            f"{contract.schema_version}"
        )
    return contract


def validate_approved_v2(contract: ApprovedContractV2) -> ApprovedContractV2:
    t = contract.target

    if t.version != TARGET_LITERALS["version"]:
        raise ValueError(
            f"target.version: expected {TARGET_LITERALS['version']!r}, got {t.version!r}"
        )
    if t.tag != TARGET_LITERALS["tag"]:
        raise ValueError(f"target.tag: expected {TARGET_LITERALS['tag']!r}, got {t.tag!r}")
    if t.commit != TARGET_LITERALS["commit"]:
        raise ValueError(f"target.commit: expected {TARGET_LITERALS['commit']!r}, got {t.commit!r}")
    if t.release_id != TARGET_LITERALS["release_id"]:
        raise ValueError(
            f"target.release_id: expected {TARGET_LITERALS['release_id']!r}, got {t.release_id!r}"
        )
    if t.release_provenance_ref != TARGET_LITERALS["release_provenance_ref"]:
        raise ValueError(
            "target.release_provenance_ref: expected "
            f"{TARGET_LITERALS['release_provenance_ref']!r}, got {t.release_provenance_ref!r}"
        )

    scope_ids = list(contract.scope.operation_ids)
    if len(scope_ids) != 16:
        raise ValueError(f"scope.operation_ids: expected 16 IDs, got {len(scope_ids)}")
    if len(set(scope_ids)) != 16:
        raise ValueError("scope.operation_ids: duplicate operation IDs found")

    if len(contract.operations) != 16:
        raise ValueError(f"operations: expected 16 operations, got {len(contract.operations)}")

    op_ids_in_ops = {op.operation_id for op in contract.operations}
    if set(scope_ids) != op_ids_in_ops:
        missing = set(scope_ids) - op_ids_in_ops
        extra = op_ids_in_ops - set(scope_ids)
        parts = []
        if missing:
            parts.append(f"missing from operations: {sorted(missing)}")
        if extra:
            parts.append(f"not in scope: {sorted(extra)}")
        raise ValueError("operation ID mismatch: " + "; ".join(parts))

    compat_counts: dict[str, int] = {}
    for op in contract.operations:
        compat_counts[op.compatibility] = compat_counts.get(op.compatibility, 0) + 1
    if compat_counts.get("compatible", 0) != 15:
        raise ValueError(
            f"expected 15 compatible operations, got {compat_counts.get('compatible', 0)}"
        )
    if compat_counts.get("intentionally_changed", 0) != 1:
        raise ValueError(
            "expected 1 intentionally_changed operation, got "
            f"{compat_counts.get('intentionally_changed', 0)}"
        )
    if "explicitly_unsupported" in compat_counts:
        raise ValueError(
            f"expected 0 explicitly_unsupported operations, got {compat_counts['explicitly_unsupported']}"
        )

    all_source_ref_ids = {sr.source_ref_id for sr in contract.source_refs}
    all_test_ref_ids = {tr.test_ref_id for tr in contract.test_refs}
    all_op_ids: set[str] = set()

    for op in contract.operations:
        if op.operation_id in all_op_ids:
            raise ValueError(f"duplicate operation_id: {op.operation_id}")
        all_op_ids.add(op.operation_id)

        ep_ids_in_op = set()
        for ep in op.entrypoints:
            if ep.entrypoint_id in ep_ids_in_op:
                raise ValueError(
                    f"duplicate entrypoint_id {ep.entrypoint_id!r} in operation {op.operation_id}"
                )
            ep_ids_in_op.add(ep.entrypoint_id)

            if ep.signature_id not in contract.catalogs.signatures:
                raise ValueError(
                    f"signature_id {ep.signature_id!r} in entrypoint "
                    f"{ep.entrypoint_id!r} not found in catalogs.signatures"
                )
            if ep.binding_id not in contract.catalogs.bindings:
                raise ValueError(
                    f"binding_id {ep.binding_id!r} in entrypoint "
                    f"{ep.entrypoint_id!r} not found in catalogs.bindings"
                )
            if ep.response_id not in contract.catalogs.responses:
                raise ValueError(
                    f"response_id {ep.response_id!r} in entrypoint "
                    f"{ep.entrypoint_id!r} not found in catalogs.responses"
                )

        for sid in op.source_ref_ids:
            if sid not in all_source_ref_ids:
                raise ValueError(f"source_ref_id {sid!r} in operation {op.operation_id} not found")
        for tid in op.test_ref_ids:
            if tid not in all_test_ref_ids:
                raise ValueError(f"test_ref_id {tid!r} in operation {op.operation_id} not found")

    for binding_id, binding in contract.catalogs.bindings.items():
        if binding.output not in ("json", "text", "bytes", "none"):
            raise ValueError(f"binding {binding_id}: unknown output mode {binding.output!r}")
        for constraint_id in binding.constraints:
            if constraint_id not in contract.catalogs.validators:
                raise ValueError(
                    f"constraint {constraint_id!r} in binding {binding_id} "
                    "not found in catalogs.validators"
                )

    for bsr_id, refs in contract.catalogs.binding_source_refs.items():
        if bsr_id not in contract.catalogs.bindings:
            raise ValueError(f"binding_source_refs key {bsr_id!r} has no matching binding")
        for ref in refs:
            if ref not in all_source_ref_ids:
                raise ValueError(f"binding_source_refs[{bsr_id!r}]: source_ref {ref!r} not found")

    for response_id, rc in contract.catalogs.responses.items():
        if rc.public_type_id not in contract.catalogs.types:
            raise ValueError(
                f"response {response_id}: public_type_id {rc.public_type_id!r} "
                "not in catalogs.types"
            )
        if rc.wire_type_id is not None and rc.wire_type_id not in contract.catalogs.types:
            raise ValueError(
                f"response {response_id}: wire_type_id {rc.wire_type_id!r} not in catalogs.types"
            )
        if rc.decoder_id not in contract.catalogs.decoders:
            raise ValueError(
                f"response {response_id}: decoder_id {rc.decoder_id!r} not in catalogs.decoders"
            )

    for presence_id, pp in contract.catalogs.presence.items():
        for val, json_key in (
            (pp.omitted, "omitted"),
            (pp.null_, "null"),
            (pp.empty, "empty"),
            (pp.zero, "zero"),
            (pp.false, "false"),
        ):
            if val not in PRESENCE_OUTCOMES:
                raise ValueError(f"presence {presence_id}.{json_key}: unknown outcome {val!r}")

    for mapping_id, profiles in contract.catalogs.mapping_presence.items():
        if mapping_id not in contract.catalogs.bindings:
            raise ValueError(f"mapping_presence key {mapping_id!r} has no matching binding")

    for validator_id in contract.catalogs.validators:
        if validator_id not in contract.catalogs.validator_evidence:
            raise ValueError(f"validator {validator_id!r} missing from validator_evidence")

    for evidence_id, ev in contract.catalogs.validator_evidence.items():
        if evidence_id not in contract.catalogs.validators:
            raise ValueError(f"validator_evidence key {evidence_id!r} has no matching validator")

    if len(contract.scope.family_dispositions) != 11:
        raise ValueError(
            f"expected 11 family dispositions, got {len(contract.scope.family_dispositions)}"
        )

    for fd in contract.scope.family_dispositions:
        if fd.disposition not in FAMILY_DISPOSITIONS:
            raise ValueError(f"family {fd.family}: unknown disposition {fd.disposition!r}")
        for op_id in fd.required_operation_ids:
            if op_id not in op_ids_in_ops:
                raise ValueError(
                    f"family {fd.family}: required_operation_id {op_id!r} not in scope"
                )

    for req in contract.traceability:
        for ref_id in req.test_ref_ids:
            if ref_id not in all_test_ref_ids:
                raise ValueError(
                    f"traceability {req.requirement_id}: test_ref_id {ref_id!r} not found"
                )

    fr_count = sum(1 for r in contract.traceability if r.requirement_id.startswith("FR-"))
    bc_count = sum(1 for r in contract.traceability if r.requirement_id.startswith("BC-"))
    sc_count = sum(1 for r in contract.traceability if r.requirement_id.startswith("SC-"))
    et_count = sum(1 for r in contract.traceability if r.requirement_id.startswith("ET-"))

    if fr_count != 40:
        raise ValueError(f"expected 40 FR traceability entries, got {fr_count}")
    if bc_count != 6:
        raise ValueError(f"expected 6 BC traceability entries, got {bc_count}")
    if sc_count != 12:
        raise ValueError(f"expected 12 SC traceability entries, got {sc_count}")
    if et_count != 7:
        raise ValueError(f"expected 7 ET traceability entries, got {et_count}")

    if len(contract.traceability) != 65:
        raise ValueError(f"expected 65 traceability entries, got {len(contract.traceability)}")

    valid_authority_refs = set(VALID_AUTHORITY_REFS_BASE) | {
        f"operation:{oid}" for oid in op_ids_in_ops
    }
    for req in contract.traceability:
        if req.authority_ref not in valid_authority_refs:
            raise ValueError(
                f"traceability {req.requirement_id}: invalid authority_ref {req.authority_ref!r}"
            )

    return contract
