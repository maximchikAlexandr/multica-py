from __future__ import annotations

import pathlib

import msgspec

from multica_py._internal.upstream_contract.generator.schema import (
    ApprovedContractV2,
)
from multica_py._internal.upstream_contract.generator.validation import (
    load_approved_contract_v2,
)

ROOT = pathlib.Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / "contracts/sdk-contract.json"
SOURCE_AUTHORITY_PATH = ROOT / "specs/007-upstream-v0-4-9-migration/contracts/source-authority.json"

EXPECTED_FAMILIES: tuple[str, ...] = (
    "agent-settings-and-skills",
    "attachments-and-client-transport",
    "chat-read",
    "issue-existing-changes",
    "issue-new-commands",
    "project-and-root-registration",
    "runtime-and-local-control",
    "skills-squads-and-autopilots",
    "transport-error-contract",
    "workspace-properties",
    "workspace-repository-management",
)


def _load_contract() -> ApprovedContractV2:
    return load_approved_contract_v2(CONTRACT_PATH)


def test_family_dispositions_names() -> None:
    contract = _load_contract()
    names = tuple(fd.family for fd in contract.scope.family_dispositions)
    assert names == EXPECTED_FAMILIES


def test_family_disposition_required_operations() -> None:
    contract = _load_contract()
    scope_ids = set(contract.scope.operation_ids)
    for fd in contract.scope.family_dispositions:
        for op_id in fd.required_operation_ids:
            assert op_id in scope_ids, (
                f"family {fd.family}: required_operation_id {op_id!r} not in scope"
            )


def test_family_disposition_source_refs_resolve() -> None:
    contract = _load_contract()
    raw = SOURCE_AUTHORITY_PATH.read_bytes()
    authority: dict[str, object] = msgspec.json.decode(raw)
    refs_list = authority["refs"]
    assert isinstance(refs_list, list)
    authority_ids = set()
    for ref in refs_list:
        assert isinstance(ref, dict)
        rid = ref.get("id")
        assert isinstance(rid, str)
        authority_ids.add(rid)

    for fd in contract.scope.family_dispositions:
        for srid in fd.source_ref_ids:
            assert srid in authority_ids, (
                f"family {fd.family}: source_ref_id {srid!r} not in source-authority.json"
            )


def test_family_every_operation_in_at_least_one_family() -> None:
    contract = _load_contract()
    covered: set[str] = set()
    for fd in contract.scope.family_dispositions:
        covered.update(fd.required_operation_ids)
    for op_id in contract.scope.operation_ids:
        assert op_id in covered, f"operation {op_id!r} is not covered by any family disposition"
