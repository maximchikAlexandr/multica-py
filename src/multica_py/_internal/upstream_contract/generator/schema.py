"""Schema-v2 types for the approved SDK contract.

Every object is a frozen msgspec.Struct with kw_only=True and
forbid_unknown_fields=True.
"""

from __future__ import annotations

import msgspec

FR_IDS: int = 40
BC_IDS: int = 6
SC_IDS: int = 12
ET_IDS: int = 7
TOTAL_REQUIREMENT_IDS: int = 65

COMPATIBILITY_OUTCOMES: tuple[str, ...] = (
    "compatible",
    "intentionally_changed",
    "explicitly_unsupported",
)
OUTPUT_MODES: tuple[str, ...] = ("json", "text", "bytes", "none")
DESTINATION_KINDS: tuple[str, ...] = (
    "path",
    "query",
    "json_body",
    "header",
    "multipart",
    "local_control",
)
PRESENCE_OUTCOMES: tuple[str, ...] = (
    "not_applicable",
    "omit",
    "emit",
    "reject",
    "value",
)
FAMILY_DISPOSITIONS: tuple[str, ...] = (
    "required_compatibility",
    "required_subset_plus_extension_candidates",
    "required_subset_plus_cli_only",
    "required_subset_plus_deferred_extension",
    "separate_extension_candidate",
    "deferred_owner_decision",
    "cli_only_plus_deferred_extension",
)


class TargetMetadata(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    version: str
    tag: str
    commit: str
    release_id: str
    release_provenance_ref: str


class SourceRef(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    source_ref_id: str
    repository: str
    commit: str
    path: str
    symbol: str
    line_start: int
    line_end: int


class TestRef(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    test_ref_id: str
    path: str
    node_id: str | None = None


class FamilyDisposition(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    family: str
    disposition: str
    required_operation_ids: tuple[str, ...]
    source_ref_ids: tuple[str, ...]
    rationale: str


class Scope(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    operation_ids: tuple[str, ...]
    ungoverned_policy: str
    source_authority_ref: str
    family_disposition_ref: str
    family_dispositions: tuple[FamilyDisposition, ...]


class ApprovedEntrypoint(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    entrypoint_id: str
    public_symbol: str
    signature_id: str
    binding_id: str
    response_id: str
    errors: str


class ApprovedOperationV2(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    operation_id: str
    compatibility: str
    rationale: str
    entrypoints: tuple[ApprovedEntrypoint, ...]
    source_ref_ids: tuple[str, ...]
    test_ref_ids: tuple[str, ...]


class BindingProfile(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    command: tuple[str, ...]
    output: str
    mappings: tuple[tuple[str, str, str], ...]
    constraints: tuple[str, ...]


class PresenceProfile(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    omitted: str
    null_: str = msgspec.field(name="null")
    empty: str
    zero: str
    false: str


class ResponseContract(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    public_type_id: str
    wire_type_id: str | None
    decoder_id: str
    success_exit_codes: tuple[int, ...]
    malformed_output: str


class ValidatorEvidence(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    positive_case_id: str
    negative_case_id: str


class Catalogs(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    types: dict[str, str]
    signatures: dict[str, str]
    bindings: dict[str, BindingProfile]
    binding_source_refs: dict[str, tuple[str, ...]]
    presence: dict[str, PresenceProfile]
    mapping_presence: dict[str, tuple[str, ...]]
    responses: dict[str, ResponseContract]
    decoders: dict[str, str]
    validators: dict[str, str]
    validator_evidence: dict[str, ValidatorEvidence]


class RequirementTrace(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    requirement_id: str
    authority_ref: str
    test_ref_ids: tuple[str, ...]


class ApprovedContractV2(msgspec.Struct, frozen=True, kw_only=True, forbid_unknown_fields=True):
    schema_version: int
    target: TargetMetadata
    catalogs: Catalogs
    source_refs: tuple[SourceRef, ...]
    test_refs: tuple[TestRef, ...]
    scope: Scope
    operations: tuple[ApprovedOperationV2, ...]
    traceability: tuple[RequirementTrace, ...]
