# Data Model: Versioned Upstream CLI Contract and SDK Upgrade Workflow

## UpstreamState

Represents the repository's view of upstream Multica releases.

**Fields**:

- `supported`: SupportedBaseline used by blocking offline gates.
- `observed`: Latest ObservedRelease found by non-blocking observer.
- `candidate`: Optional CandidateBaseline under review.

**Validation Rules**:

- `observed` may be newer than `supported` without failing offline gates.
- `candidate` cannot replace `supported` without a PromotionDecision.
- State changes must be idempotent for the same release identity.

## SupportedBaseline

Represents the upstream CLI contract currently supported by the SDK.

**Fields**:

- `version`: Human-readable Multica release version.
- `tag`: Upstream release tag when available.
- `commit`: Full 40-character source commit.
- `semantic_hash`: Hash of canonical semantic contract content.
- `contract_ref`: Path to checked-in SemanticCLIContract artifact.

**Validation Rules**:

- `commit` must be a 40-character hexadecimal string.
- `semantic_hash` excludes volatile observation metadata.
- The supported contract must pass the offline coverage gate.

## ObservedRelease

Represents a release discovered by scheduled or manual observation.

**Fields**:

- `version`: Release version.
- `tag`: Release tag.
- `release_id`: Upstream release identity when available.
- `published_at`: Release publication timestamp when known.
- `asset_refs`: Candidate downloadable artifacts and checksum references.
- `status`: Informational status such as new, already-supported, superseded, or candidate-prepared.

**Validation Rules**:

- Observation alone must not change supported baseline.
- Re-observing the same release must not create duplicate tracking work.

## CandidateBaseline

Represents a reproducible contract prepared for review.

**Fields**:

- `baseline`: Version, tag, full commit, and source identity.
- `contract_ref`: Candidate SemanticCLIContract artifact.
- `trust_level`: `verified`, `binary`, `source`, or `single-source-degraded`.
- `diff_ref`: UpstreamContractDiff against supported.
- `impact_map_ref`: SDK impact analysis.
- `unresolved_items`: Review items that block promotion when breaking or incomplete.

**Validation Rules**:

- Candidate promotion requires full provenance and no unresolved breaking items.
- Source/binary mismatch prevents `verified` trust level.

## SemanticCLIContract

Represents normalized command behavior for one upstream baseline.

**Fields**:

- `schema_version`: Contract schema version.
- `baseline`: Supported/candidate baseline metadata.
- `artifact`: Generator name, generator version, generator commit, collection method, semantic hash.
- `binary`: Optional binary artifact identity, platform, digest, and normalized version output.
- `source`: Optional source commit, repository, and extractor evidence summary.
- `commands`: Stable list of CommandContract entries.
- `observation`: Detached collection timestamp and run metadata.
- `json_schema_ref`: Optional generated schema reference for validating the artifact.

**Validation Rules**:

- Canonical contract serialization is deterministic.
- Volatile observation metadata is excluded from semantic hash.
- Unknown schema versions are rejected with actionable errors.
- JSON Schema may be generated from the same typed models for external validation.
- Tag-to-commit relation must be verified when release metadata is available.
- Absolute local executable paths must not be stored in checked-in artifacts;
  store asset identity, basename, digest, platform, and normalized version output.

## CommandContract

Represents one upstream CLI command path.

**Fields**:

- `path`: Command path as ordered tokens.
- `use`: Command usage token or grammar summary.
- `aliases`: Cobra aliases or detected compatibility spellings.
- `hidden`: Whether the command is hidden.
- `deprecated`: Deprecation message or null.
- `args`: ArgumentContract.
- `flags`: Stable list of FlagContract entries.
- `execution`: ExecutionContract.
- `output`: OutputContract.
- `source`: SourceReference for file, symbol, and line range when known.
- `contract_hash`: Hash of normalized command semantics.

**Validation Rules**:

- Path and flags are normalized in stable order.
- Description-only changes are classified as documentation-only.
- Hidden/deprecated state is semantic and participates in diff classification.

## ArgumentContract

Represents positional argument rules.

**Fields**:

- `min`: Minimum accepted argument count.
- `max`: Maximum accepted argument count or unbounded marker.
- `grammar`: Human-readable grammar when exact count is insufficient.
- `validators`: Known declarative validators.
- `review_items`: Imperative or unknown validators requiring review.

## FlagContract

Represents one command flag or inherited persistent option.

**Fields**:

- `name`: Long flag name.
- `shorthand`: Optional short flag.
- `type`: Normalized primitive or collection type.
- `required`: Whether the flag is required.
- `repeatable`: Whether multiple values are accepted.
- `default`: Normalized default value.
- `enum`: Candidate enum values when detected.
- `inherited`: Whether effective presence comes from a parent command.
- `deprecated`: Deprecation message or null.
- `source`: SourceReference.

**Validation Rules**:

- Required flag additions are breaking by default.
- Optional flag additions are additive by default.
- Unknown enum construction creates review items, not automatic SDK changes.

## ExecutionContract

Represents how the command runs.

**Fields**:

- `interactive`: Whether the command expects interactive input.
- `streaming`: Whether the command streams or tails output.
- `managed_process`: Whether the command is long-running or process-oriented.
- `requires_server`: Whether the command requires a server/account to complete normal execution.
- `exit_behavior`: Expected exit-code behavior when known.

## OutputContract

Represents command result behavior.

**Fields**:

- `mode`: Structured JSON, text, binary, streaming, process, or none.
- `schema_ref`: Optional schema or fixture reference.
- `model`: SDK decoder/model identity when typed.
- `fixture_ref`: Checked-in output fixture reference when available.
- `decoder_policy`: Strict, permissive-extra-fields, text-only, or custom.
- `confidence`: High, medium, low, or review-required.
- `negative_fixture_ref`: Optional fixture proving incompatible changes fail.
- `field_change_policy`: Handling for optional additions versus removals/type changes.

**Validation Rules**:

- JSON typed output requires at least one checked-in fixture.
- Strict decoders require negative fixtures for incompatible removed/type-changed fields.
- Optional added fields are tested separately from removed or type-changed fields.
- When a server-free schema cannot be collected automatically, curated fixtures
  and confidence level are required.

## SourceEvidence

Represents declarative facts extracted from upstream source.

**Fields**:

- `facts`: Extracted command, flag, enum, and constraint facts.
- `review_items`: Unknown helpers, imperative validation, presence-sensitive parameters, and unresolved mappings.
- `confidence`: Confidence per fact.
- `source_refs`: File/symbol/line evidence.

**Validation Rules**:

- Evidence is not an approved SDK contract.
- Unknown source patterns fail closed into review items.
- Evidence cannot directly change public SDK behavior.

## ApprovedSDKContract

Represents maintainer-approved SDK decisions derived from evidence and review.

**Fields**:

- `operation_id`: Stable operation identity.
- `bindings`: Versioned upstream command bindings.
- `input_contract`: Python parameter to CLI argument/flag mapping.
- `output_contract`: Output contract and decoder identity.
- `presence_semantics`: Omitted/null/empty/zero/false behavior for sensitive parameters.
- `enum_policy`: Strict or open policy with approved values.
- `constraints`: Declarative and approved imperative parameter rules.
- `review_status`: Approved, unresolved, or rejected.
- `generator_input`: Whether this approved contract is eligible for production generation.

**Validation Rules**:

- Parameter-to-API-field mapping requires source references and maintainer approval.
- Presence-sensitive parameters block promotion until semantics are explicit.
- Approved constraints require positive and negative tests.
- Approved SDK contract is the only valid input to production generators.
- Raw source evidence and upgrade bundle suggestions are never generator input.

## OperationIdentity

Represents SDK-owned operation identity independent of command spelling.

**Fields**:

- `operation_id`: Stable identifier such as `agents.avatar.upload`.
- `implementation`: SDK method or internal implementation reference.
- `bindings`: Upstream command bindings with kind, since, and until.
- `shares_implementation_with`: Explicit related operation IDs when sharing is intentional.

**Validation Rules**:

- Multiple bindings may share one operation.
- Duplicate implementation ownership is an error only without explicit shared identity.
- Alias cycles and overlapping conflicting intervals are invalid.

## CoverageDecision

Represents one SDK coverage row.

**Fields**:

- `operation_id`: Stable SDK operation.
- `coverage_level`: `typed`, `raw`, `process`, `unsupported`, `legacy`, or `incomplete`.
- `bindings`: Upstream command bindings.
- `input_contract_ref`: Required for typed coverage.
- `output_contract_ref`: Required for typed structured output.
- `test_refs`: Contract tests proving coverage.
- `source_refs`: Upstream source provenance.
- `reason`: Required for unsupported or legacy decisions.
- `raw_argv_policy`: For raw coverage, the safe argv contract accepted by the SDK.

**Validation Rules**:

- `typed` coverage requires SDK method, input/output contract, source provenance, and tests.
- `raw` and `process` are reported separately from typed support.
- `incomplete` never satisfies the gate.
- Raw coverage accepts only argument sequences and never shell-interpolated strings.
- Raw coverage is not typed public support and must be documented separately.

## UpstreamContractDiff

Represents semantic changes from supported to candidate contract.

**Fields**:

- `changes`: List of diff entries.
- `summary`: Counts by severity and change type.
- `semantic_hash_before`: Supported hash.
- `semantic_hash_after`: Candidate hash.

**Diff Entry Fields**:

- `kind`: Change type such as command_added, flag_changed, default_changed, output_contract_changed, doc_only_changed.
- `severity`: Provenance-only, documentation-only, additive, potentially-breaking, or breaking.
- `before`: Previous value when present.
- `after`: New value when present.
- `affected_operations`: Operation IDs impacted or unresolved marker.
- `suggested_action`: Maintainer action.

## CoverageReport

Represents the machine-readable result rendered for humans and automation.

**Fields**:

- `schema_version`: Report schema version.
- `status`: Clean, gaps, invalid, collection-failed, mismatch, or unresolved-breaking.
- `supported`: Supported baseline summary.
- `observed`: Observed release summary.
- `candidate`: Candidate baseline summary.
- `upstream_diff`: Diff severity counts.
- `coverage`: Coverage-level counts.
- `failures`: Machine-readable failure list.

**Validation Rules**:

- Human output is derived from this model.
- Exit code is derived from status and failure class.

## UpgradeBundle

Represents generated review context for a candidate upgrade.

**Fields**:

- `summary`: Maintainer-facing summary.
- `upstream_diff`: Machine-readable diff.
- `impact_map`: SDK operations affected by upstream changes.
- `candidate_contract`: Candidate semantic contract.
- `manifest_suggestions`: Incomplete coverage suggestions.
- `implementation_tasks`: Suggested tasks with unresolved decisions.
- `test_suggestions`: Suggested argv/output/contract tests.
- `changelog_fragment`: Draft compatibility note.

**Validation Rules**:

- Re-running unchanged inputs is idempotent.
- Generated suggestions do not change supported coverage automatically.
- Generated facts are separated from maintainer decisions.

## CollectorSecurityPolicy

Represents required controls for executing or inspecting upstream binaries.

**Fields**:

- `asset_source`: Official release asset or explicit local binary.
- `checksum`: Required digest for networked artifacts.
- `environment`: Sanitized variables and temporary config/home directories.
- `execution_limits`: Per-node timeout, total timeout, stdout/stderr limits, artifact size limits.
- `platform`: OS and architecture recorded in provenance.
- `network_policy`: Disabled or restricted when technically possible.

**Validation Rules**:

- Binary with checksum mismatch is never executed.
- Collector must not see repository secrets or user Multica profiles.
- Timeout or output limit creates collector failure, not partial success.

## CompatibilityPolicy

Represents SDK-to-Multica compatibility.

**Fields**:

- `sdk_version`: SDK version.
- `supported_cli`: Minimum, maximum tested, and contract hashes.
- `runtime_policy`: Older, newer-untested, unknown-commit warning/error behavior.
- `override_policy`: Explicit advanced-user bypass and diagnostics.
- `detection_policy`: When and how CLI version/build metadata is read.
- `documentation_ref`: Generated docs or README section derived from this matrix.

**Validation Rules**:

- Runtime diagnostics include detected CLI version and supported range.
- Warnings are not repeated on every method call.
- Documentation is generated from the same policy artifact.
- CLI version/build metadata is read once per client instance and cached.
- Advanced override is explicit and must keep the risk visible to the user.
