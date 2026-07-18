from __future__ import annotations

import typing as _t

import msgspec

T = _t.TypeVar("T")

JsonScalar = str | int | float | bool | None
DiffValue = JsonScalar | list[str] | dict[str, JsonScalar | list[str]]


class SourceRef(msgspec.Struct, frozen=True, kw_only=True):
    path: str | None = None
    symbol: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    commit: str | None = None
    repository: str | None = None


class BinaryRef(msgspec.Struct, frozen=True, kw_only=True):
    asset_name: str
    sha256: str
    os: str
    arch: str
    version_output: str


class Baseline(msgspec.Struct, frozen=True, kw_only=True):
    state: str
    version: str
    tag: str | None = None
    commit: str


class ArtifactMeta(msgspec.Struct, frozen=True, kw_only=True):
    semantic_hash: str
    generator_name: str
    generator_version: str
    generator_commit: str
    collection_method: str
    trust_level: str = "release-binary"


class ObservationMeta(msgspec.Struct, frozen=True, kw_only=True):
    generated_at: str
    run_id: str | None = None
    run_metadata: dict[str, str] = msgspec.field(default_factory=dict)


class ArgumentContract(msgspec.Struct, frozen=True, kw_only=True):
    min: int = 0
    max: int = 0
    grammar: str | None = None
    validators: tuple[str, ...] = ()
    review_items: tuple[str, ...] = ()


class FlagContract(msgspec.Struct, frozen=True, kw_only=True):
    name: str
    shorthand: str | None = None
    type: str = "string"
    required: bool = False
    repeatable: bool = False
    default: str | None = None
    enum: tuple[str, ...] = ()
    inherited: bool = False
    deprecated: str | None = None
    source: SourceRef | None = None


class ExecutionContract(msgspec.Struct, frozen=True, kw_only=True):
    interactive: bool = False
    streaming: bool = False
    managed_process: bool = False
    requires_server: bool = True
    exit_behavior: str | None = None


class OutputContract(msgspec.Struct, frozen=True, kw_only=True):
    mode: str = "none"
    schema_ref: str | None = None
    model: str | None = None
    fixture_ref: str | None = None
    decoder_policy: str = "text-only"
    confidence: str = "low"
    negative_fixture_ref: str | None = None
    field_change_policy: str = "permissive-extra-fields"


class CommandContract(msgspec.Struct, frozen=True, kw_only=True):
    path: tuple[str, ...]
    use: str
    aliases: tuple[str, ...] = ()
    hidden: bool = False
    deprecated: str | None = None
    args: ArgumentContract = msgspec.field(default_factory=ArgumentContract)
    flags: tuple[FlagContract, ...] = ()
    execution: ExecutionContract = msgspec.field(default_factory=ExecutionContract)
    output: OutputContract = msgspec.field(default_factory=OutputContract)
    source: SourceRef | None = None
    contract_hash: str = ""


class SemanticCLIContract(msgspec.Struct, frozen=True, kw_only=True):
    schema_version: int
    baseline: Baseline
    artifact: ArtifactMeta
    binary: BinaryRef | None = None
    source: SourceRef | None = None
    commands: tuple[CommandContract, ...] = ()
    observation: ObservationMeta = msgspec.field(
        default_factory=lambda: ObservationMeta(generated_at="")
    )
    json_schema_ref: str | None = None

    def command_paths(self) -> tuple[tuple[str, ...], ...]:
        return tuple(c.path for c in self.commands)


class SupportedBaseline(msgspec.Struct, frozen=True, kw_only=True):
    version: str
    tag: str | None = None
    commit: str
    semantic_hash: str
    contract_ref: str
    state: str = "supported"


class ObservedRelease(msgspec.Struct, frozen=True, kw_only=True):
    version: str
    tag: str | None = None
    release_id: str | None = None
    published_at: str | None = None
    asset_refs: tuple[str, ...] = ()
    status: str = "new"
    state: str = "observed"


class CandidateBaseline(msgspec.Struct, frozen=True, kw_only=True):
    version: str
    tag: str | None = None
    commit: str
    semantic_hash: str
    contract_ref: str
    trust_level: str
    unresolved_items: tuple[str, ...] = ()
    state: str = "candidate"


class UpstreamState(msgspec.Struct, frozen=True, kw_only=True):
    schema_version: int
    supported: SupportedBaseline | None = None
    observed: ObservedRelease | None = None
    candidate: CandidateBaseline | None = None

    @classmethod
    def empty(cls) -> UpstreamState:
        return cls(schema_version=1)


class OperationBinding(msgspec.Struct, frozen=True, kw_only=True):
    command_path: tuple[str, ...]
    kind: str = "primary"
    since: str | None = None
    until: str | None = None


class CoverageDecision(msgspec.Struct, frozen=True, kw_only=True):
    operation_id: str
    coverage_level: str
    bindings: tuple[OperationBinding, ...] = ()
    input_contract_ref: str | None = None
    output_contract_ref: str | None = None
    test_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    reason: str | None = None
    raw_argv_policy: str | None = None
    shares_implementation_with: tuple[str, ...] = ()


class CoverageManifest(msgspec.Struct, frozen=True, kw_only=True):
    schema_version: int
    decisions: tuple[CoverageDecision, ...] = ()


class DiffEntry(msgspec.Struct, frozen=True, kw_only=True):
    kind: str
    severity: str
    command_path: tuple[str, ...] = ()
    flag_name: str | None = None
    before: DiffValue | None = None
    after: DiffValue | None = None
    affected_operations: tuple[str, ...] = ()
    suggested_action: str = "review"
    message: str = ""


class UpstreamContractDiff(msgspec.Struct, frozen=True, kw_only=True):
    schema_version: int
    changes: tuple[DiffEntry, ...] = ()
    summary: dict[str, int] = msgspec.field(default_factory=dict)
    semantic_hash_before: str = ""
    semantic_hash_after: str = ""
    unresolved_breaking: bool = False


class ReportFailure(msgspec.Struct, frozen=True, kw_only=True):
    code: str
    operation_id: str | None = None
    command: str | None = None
    path: str | None = None
    severity: str | None = None
    resolution: str = "unresolved"
    message: str = ""


class SupportedSummary(msgspec.Struct, frozen=True, kw_only=True):
    version: str = ""
    tag: str | None = None
    commit: str = ""
    semantic_hash: str = ""
    command_count: int = 0


class ObservedSummary(msgspec.Struct, frozen=True, kw_only=True):
    version: str = ""
    tag: str | None = None
    release_id: str | None = None
    published_at: str | None = None
    status: str = ""


class CandidateSummary(msgspec.Struct, frozen=True, kw_only=True):
    version: str = ""
    tag: str | None = None
    commit: str = ""
    semantic_hash: str = ""
    trust_level: str = ""


class CoverageReport(msgspec.Struct, frozen=True, kw_only=True):
    schema_version: int
    status: str
    supported: SupportedSummary = msgspec.field(default_factory=SupportedSummary)
    observed: ObservedSummary = msgspec.field(default_factory=ObservedSummary)
    candidate: CandidateSummary = msgspec.field(default_factory=CandidateSummary)
    upstream_diff: dict[str, int] = msgspec.field(default_factory=dict)
    coverage: dict[str, int] = msgspec.field(default_factory=dict)
    failures: tuple[ReportFailure, ...] = ()
    notes: tuple[str, ...] = ()


class ImpactEntry(msgspec.Struct, frozen=True, kw_only=True):
    change_kind: str
    severity: str
    command_path: tuple[str, ...]
    operation_id: str | None = None
    unresolved_reason: str | None = None
    candidate_method: str | None = None
    parameters_changed: tuple[str, ...] = ()


class ImpactMap(msgspec.Struct, frozen=True, kw_only=True):
    schema_version: int
    entries: tuple[ImpactEntry, ...] = ()


class TestSuggestions(msgspec.Struct, frozen=True, kw_only=True):
    argv_targets: tuple[str, ...] = ()
    output_fixture_targets: tuple[str, ...] = ()


class ManifestSuggestion(msgspec.Struct, frozen=True, kw_only=True):
    operation_id: str
    command_path: tuple[str, ...]
    change_kind: str
    severity: str
    coverage_level: str
    reason: str


class UpgradeBundle(msgspec.Struct, frozen=True, kw_only=True):
    schema_version: int
    summary: str
    upstream_diff: UpstreamContractDiff
    impact_map: ImpactMap
    candidate_contract_ref: str
    manifest_suggestions: tuple[ManifestSuggestion, ...]
    implementation_tasks: tuple[str, ...]
    test_suggestions: TestSuggestions
    changelog_fragment: str
    generated_at: str
    bundle_hash: str = ""


class PromotionDecision(msgspec.Struct, frozen=True, kw_only=True):
    schema_version: int
    candidate_version: str
    candidate_tag: str | None
    candidate_commit: str
    candidate_semantic_hash: str
    previous_supported_version: str
    previous_supported_commit: str
    clean_gate_ref: str
    reviewer: str
    review_ref: str | None = None
    resolutions: tuple[dict[str, str], ...] = ()


class SourceEvidenceFact(msgspec.Struct, frozen=True, kw_only=True):
    fact_type: str
    command_path: tuple[str, ...] = ()
    flag_name: str | None = None
    value: str | None = None
    source_ref: SourceRef | None = None
    review_required: bool = False


class SourceEvidence(msgspec.Struct, frozen=True, kw_only=True):
    schema_version: int
    facts: tuple[SourceEvidenceFact, ...] = ()
    review_items: tuple[str, ...] = ()
    confidence: str = "low"
    source_refs: tuple[SourceRef, ...] = ()


class ReleaseObservation(msgspec.Struct, frozen=True, kw_only=True):
    release_id: str
    version: str
    tag: str
    tracking_issue_id: str | None = None
    tracking_pr_id: int | None = None
    status: str = "new"
    superseded_by: str | None = None


class CliCompatMatrix(msgspec.Struct, frozen=True, kw_only=True):
    schema_version: int
    sdk_version: str
    min_cli_version: str
    max_cli_version: str
    contract_hashes: dict[str, str] = msgspec.field(default_factory=dict)
    runtime_policy: str = "warn-once"
    override_policy: str = "explicit"
    detection_policy: str = "lazy"
    documentation_ref: str | None = None
