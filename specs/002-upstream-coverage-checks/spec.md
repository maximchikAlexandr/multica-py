# Feature Specification: Versioned Upstream CLI Contract and SDK Upgrade Workflow

**Feature Branch**: `[002-upstream-coverage-checks]`

**Created**: 2026-07-17

**Status**: Draft

**Input**: User description: "Improve the Multica upstream coverage/drift checks around baseline state, semantic CLI contracts, smarter diffing, machine-readable reports, secure collection, and reviewable upgrade preparation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify Supported Upstream Baseline (Priority: P1)

As a package maintainer, I can run one offline quality gate that compares the supported upstream CLI contract against the SDK coverage decisions and tells me whether the current SDK still covers the baseline it claims to support.

**Why this priority**: This is the merge-blocking safety gate. Maintainers need a clear pass/fail result before accepting SDK changes.

**Independent Test**: Can be tested with checked-in artifacts only: supported contract, SDK coverage manifest, and synthetic fixtures for compatible and incompatible changes. Acceptance is determined by the command, summary, exit-code, and fixture matrix in `contracts/implementation-oracles.md`.

**Acceptance Scenarios**:

1. **Given** the supported contract and SDK manifest agree, **When** the maintainer runs the coverage gate, **Then** the gate exits successfully and reports supported version, commit, semantic hash, coverage counts, and zero failures.
2. **Given** an upstream command gains a required argument in the candidate contract, **When** the gate compares supported and candidate contracts, **Then** the change is classified as breaking and cannot be promoted without explicit resolution.
3. **Given** an SDK row is explicitly unsupported with a reason, **When** the gate validates coverage, **Then** that row is reported as unsupported and does not fail only because it lacks an SDK method.

---

### User Story 2 - Refresh a Candidate Contract for a New Multica Release (Priority: P1)

As a maintainer evaluating a new Multica release, I can collect a candidate semantic CLI contract from a selected release artifact and source commit so that upgrade work is reproducible, deterministic, and reviewable.

**Why this priority**: The SDK must detect behavior changes in existing commands, not only added or removed command names.

**Independent Test**: Can be tested by collecting from a controlled fixture executable/source snapshot and confirming that command paths, arguments, flags, aliases, defaults, deprecation state, execution mode, output metadata, provenance, trust level, and semantic hash match `contracts/implementation-oracles.md`.

**Acceptance Scenarios**:

1. **Given** a verified Multica executable and matching source commit, **When** the maintainer collects a candidate contract, **Then** the result records release version, tag, full commit, collection method, binary digest, platform, generator identity, schema version, and semantic hash.
2. **Given** the executable reports only a short commit in normal output but full build metadata is available, **When** the collector builds provenance, **Then** the checked-in candidate records the full commit.
3. **Given** one command help node times out or cannot be inspected, **When** collection completes, **Then** the inventory is marked incomplete and cannot be treated as a successful complete contract.

---

### User Story 3 - Understand Upstream Impact Before SDK Work (Priority: P1)

As a maintainer, I can compare supported and candidate upstream contracts and receive a semantic diff that classifies what changed and which SDK operations may be affected.

**Why this priority**: A new release can break an existing SDK method without adding a new command. Maintainers need the reason for the gap, not only a set difference of command names.

**Independent Test**: Can be tested with mutation fixtures that add optional flags, add required arguments, remove flags, change defaults, change aliases, and change output contracts; each expected severity and promotion-blocking result is defined in `contracts/implementation-oracles.md`.

**Acceptance Scenarios**:

1. **Given** a fixture where only command help text changes, **When** the diff is generated, **Then** the report classifies it as documentation-only and does not fail compatibility.
2. **Given** a fixture where a required flag is added, **When** the diff is generated, **Then** the report classifies the change as breaking, links affected SDK operations, and blocks candidate promotion.
3. **Given** a possible command rename, **When** the diff is generated, **Then** the rename is presented as a suggestion requiring maintainer confirmation rather than automatically changing operation identity.

---

### User Story 4 - Prepare a Reviewable Upgrade Bundle (Priority: P2)

As a maintainer responding to an upstream release, I can generate a deterministic upgrade bundle containing summary, semantic diff, impact map, incomplete manifest suggestions, and verification-task suggestions.

**Why this priority**: The highest-value automation is preparing context and repetitive work while leaving public SDK decisions to maintainers.

**Independent Test**: Can be tested by running upgrade preparation twice for the same inputs and verifying byte-identical output, no duplicate tracking artifacts, and the exact local directory layout defined in `contracts/implementation-oracles.md`.

**Acceptance Scenarios**:

1. **Given** new upstream commands are missing from the SDK manifest, **When** upgrade preparation runs, **Then** each missing command receives an incomplete coverage suggestion and related test/documentation work item.
2. **Given** a release changes no semantic contract content, **When** upgrade preparation runs, **Then** the report identifies the release as provenance-only and does not create empty implementation work.
3. **Given** generated suggestions are produced, **When** the maintainer reviews the bundle, **Then** generated facts are separated from maintainer decisions.

---

### User Story 5 - Observe New Releases Without Breaking Offline CI (Priority: P2)

As a maintainer, I can run a scheduled observer that detects new upstream releases and prepares candidate information without changing the supported baseline or breaking ordinary pull-request validation.

**Why this priority**: Upstream may release frequently. Maintainers should learn about new releases automatically while preserving reproducible offline gates.

**Independent Test**: Can be tested with mocked release metadata and verified artifacts, confirming that repeated observer runs follow the state transition table in `contracts/implementation-oracles.md` and do not promote supported coverage.

**Acceptance Scenarios**:

1. **Given** a newer upstream release exists, **When** the scheduled observer runs, **Then** it reports observed release lag without changing supported baseline artifacts.
2. **Given** the same release is observed again, **When** the observer runs, **Then** it updates or reuses the same tracking artifact instead of creating duplicates.
3. **Given** the release asset checksum does not match, **When** the observer prepares collection, **Then** the binary is rejected before execution.

### Edge Cases

- A release is newer than supported but has the same semantic contract hash.
- A command path disappears while a compatibility command or Cobra alias still executes.
- Two upstream command bindings intentionally share one SDK operation implementation.
- The local executable reports only a short commit while build metadata contains the full commit.
- Binary and source collectors disagree on command tree, flags, or hidden/deprecated state.
- A source extractor encounters an unknown registration pattern or imperative validation rule.
- An update parameter distinguishes omitted, null, empty string, zero, and false values.
- A collector times out, emits oversized output, or would read user configuration.
- A release asset checksum fails validation.
- A checked-in artifact uses an unknown schema version.
- Upgrade preparation or observer state update fails after writing temporary files.
- A newer candidate supersedes an older candidate before the older one is promoted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST record the supported upstream baseline with both a human-readable Multica release version and a full immutable source commit.
- **FR-002**: The system MUST reject checked-in baseline records that use only a short commit when a full commit is required for reproducible source links.
- **FR-003**: Maintainers MUST be able to collect an upstream command inventory from a selected Multica executable without changing SDK coverage decisions automatically.
- **FR-004**: The collected inventory MUST include a stable command list, aliases or legacy command relationships when they can be detected, the upstream release version, the full source commit, and when the inventory was generated.
- **FR-005**: The coverage check MUST compare the checked-in upstream inventory with the SDK manifest and report separate categories for covered commands, missing manifest rows, manifest rows absent from the current inventory, unsupported rows, duplicate SDK ownership, and SDK mappings that do not resolve.
- **FR-006**: Unsupported commands MUST satisfy coverage only when they include an explicit status and reason; they MUST NOT fail only because they intentionally have no SDK method.
- **FR-007**: The coverage check MUST fail when any current upstream command lacks a mapped, process-oriented, or explicitly unsupported SDK coverage decision.
- **FR-008**: The coverage check MUST provide a concise summary with baseline version, full commit, inventory command count, manifest row count, unsupported count, and failure count before detailed command lists.
- **FR-009**: Maintainers MUST be able to request suggested manifest stubs for commands missing from the SDK manifest.
- **FR-010**: Suggested manifest stubs MUST be marked incomplete until a maintainer supplies SDK ownership, output behavior, unsupported status if applicable, and source provenance.
- **FR-011**: The default continuous quality gate MUST validate only checked-in baseline artifacts and MUST NOT depend on a live Multica account, server, or network connection.
- **FR-012**: Manual baseline refresh MUST make the selected Multica executable basename, digest, trust level, and recorded baseline visible in the result so reviewers can understand what changed; when a digest cannot be computed the refresh MUST fail with exit code `3`; absolute local executable paths MUST NOT be stored in checked-in artifacts.
- **FR-013**: The system MUST distinguish the supported upstream baseline, the latest observed upstream release, and a candidate baseline under review; observing a release MUST NOT change supported coverage automatically.
- **FR-014**: The upstream inventory MUST represent command arguments, flags, defaults, types, aliases, hidden/deprecated state, inherited options, execution mode, and output contract metadata in addition to command names.
- **FR-015**: The system MUST produce a semantic diff between supported and candidate upstream contracts and classify each change by type and compatibility severity.
- **FR-016**: Possible command renames or moves MUST be reported as suggestions and MUST require an explicit maintainer decision before operation identity changes.
- **FR-017**: Every checked-in contract artifact MUST include schema version, generator identity, collection method, full source commit, semantic hash, generated JSON Schema compatibility, and binary/source provenance fields required by `contracts/implementation-oracles.md`.
- **FR-018**: Canonical contract output MUST be deterministic; volatile observation metadata MUST NOT cause a semantic contract change.
- **FR-019**: Coverage decisions MUST distinguish typed, raw, process-oriented, unsupported, legacy, and incomplete states.
- **FR-020**: Typed coverage MUST require explicit input mapping, output contract provenance, and contract-test evidence in addition to an SDK method reference.
- **FR-021**: Maintainer commands MUST provide a versioned machine-readable report and documented exit codes that distinguish coverage gaps, invalid artifacts, collection failures, source/binary mismatches, unresolved breaking changes, and invalid CLI usage.
- **FR-022**: The blocking quality gate MUST remain offline; only the separate non-blocking scheduled observer is allowed to use the network to discover releases and prepare candidate artifacts without promoting them.
- **FR-023**: Network-based collection MUST verify official release checksums and execute the selected binary in an isolated environment without repository secrets or user configuration, including sanitized token-like environment variables, temporary config directories, bounded output, timeouts, and network restriction when supported by the runner; local manual binary collection MUST produce a non-promotable trust level unless reproduced from verified release/source evidence.
- **FR-024**: Upgrade preparation MUST be idempotent and MUST generate a reviewable impact report, incomplete manifest suggestions, and verification-task suggestions for every non-documentation contract change; failed writes or reruns MUST leave either the previous complete bundle or a clearly invalid temporary artifact that cannot be promoted.
- **FR-025**: The system MUST maintain an explicit compatibility policy between SDK releases and tested Multica CLI contracts.
- **FR-026**: Shared SDK implementations and command aliases MUST be declared explicitly and MUST NOT be treated as duplicate ownership solely because they resolve to the same implementation.
- **FR-027**: Source extraction MUST be limited to declared, versioned, reviewable patterns; unknown source patterns MUST create review items and MUST NOT automatically change public SDK behavior.
- **FR-028**: Parameter-to-API-field mapping, omitted/null/empty/zero/false semantics, dynamic enum policy, and imperative validation rules MUST require maintainer approval before becoming an approved SDK contract; approved constraints MUST be normalized into explicit categories such as `requires`, `conflicts_with`, `exactly_one`, `at_least_one`, or `required_together` with positive and negative test evidence.
- **FR-029**: Human-readable output MUST be rendered from the same machine-readable report model used by automation.
- **FR-030**: Candidate promotion MUST require full provenance, clean offline gates, no unresolved breaking changes, and an explicit maintainer decision recorded in a reviewable PromotionDecision artifact; promote and reject outcomes MUST be explicit and MUST NOT occur as a side effect of collection, observation, or upgrade preparation.
- **FR-031**: Raw coverage MUST accept only explicit argument sequences, MUST NOT use shell interpolation, and MUST be documented separately from typed support.
- **FR-032**: Contract collection MUST use the fixed collector order and trust-level promotion eligibility table in `contracts/implementation-oracles.md`: release asset contract, binary exporter, Go helper/exporter, then help parser fallback. Help parsing MUST be degraded mode with review items and non-promotable status unless cross-checked into a higher trust level.
- **FR-033**: Runtime compatibility diagnostics MUST read detected CLI version/build metadata at most once per client instance, show supported range, and avoid repeated warnings for the same client.

### Key Entities *(include if feature involves data)*

- **SupportedBaseline**: The upstream CLI contract currently supported by the SDK and used by blocking offline gates.
- **ObservedRelease**: Latest upstream release identity discovered by an observer, informational until reviewed.
- **CandidateBaseline**: A reproducible upstream contract prepared for review and possible promotion.
- **PromotionDecision**: Explicit maintainer decision that moves a candidate into supported state.
- **SemanticCLIContract**: Normalized command tree including command paths, arguments, flags, defaults, aliases, hidden/deprecated state, execution mode, output metadata, provenance, and semantic hash.
- **SourceEvidence**: Declarative facts and review items extracted from upstream source without guessing behavioral semantics.
- **ApprovedSDKContract**: Maintainer-approved intermediate contract that may drive SDK generation, tests, and docs.
- **OperationIdentity**: Stable SDK-owned operation ID with versioned upstream bindings and explicit shared implementation metadata.
- **CoverageDecision**: SDK manifest decision with coverage level, input/output contracts, test references, source provenance, and version interval.
- **UpstreamContractDiff**: Semantic supported-to-candidate diff with change category, severity, before/after values, affected operations, and suggested action.
- **CoverageReport**: Machine-readable and human-rendered gate result.
- **UpgradeBundle**: Reviewable generated package containing summary, diff, impact map, candidate contract, manifest suggestions, tests/docs/task suggestions, and unresolved decisions.
- **CollectorSecurityPolicy**: Rules for verifying and isolating upstream binaries before collection.
- **CompatibilityPolicy**: Matrix connecting SDK versions to tested Multica CLI contracts and runtime warning/error behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can identify whether the SDK covers the checked-in upstream baseline in under 30 seconds from the summary output.
- **SC-002**: For an inventory with at least one new upstream command, 100% of missing commands are listed by name in the coverage gap report.
- **SC-003**: For an inventory with intentionally unsupported commands, 100% of unsupported rows with reasons are reported without being counted as missing SDK mappings.
- **SC-004**: A maintainer can refresh an upstream inventory for a new release and see the recorded release version plus full commit in the generated baseline artifacts.
- **SC-005**: Suggested manifest stubs are produced for 100% of missing commands when requested, and none of those stubs are considered complete coverage without maintainer-supplied decisions.
- **SC-006**: Given a fixture where an existing command gains a required argument, the system detects and classifies the change as breaking without relying on a new command name.
- **SC-007**: Given a fixture where only help text changes, the system produces no compatibility failure.
- **SC-008**: Two collections from the same verified binary and collector version produce byte-identical canonical contract content, excluding detached observation metadata.
- **SC-009**: A missing, timed-out, or partially inspected executable can never produce a successful complete-inventory result.
- **SC-010**: A new observed release is reported without changing the supported baseline or breaking the offline pull-request gate.
- **SC-011**: Every semantic upstream change appears exactly once in the machine-readable diff and is linked to zero or more affected SDK operations with an explicit unresolved state when no mapping exists.
- **SC-012**: Every typed coverage row resolves to a valid SDK method, at least one argv contract test, and a declared output contract or explicit non-structured-output policy.
- **SC-013**: Re-running upgrade preparation for unchanged inputs produces no working-tree diff and does not create duplicate tracking issues or pull requests.
- **SC-014**: A release asset with a checksum mismatch is rejected before execution.
- **SC-015**: A maintainer can determine from one report whether a release is provenance-only, additive, potentially breaking, or breaking and see the affected SDK operations.
- **SC-016**: A raw coverage row cannot be mistaken for typed support in reports, docs, or compatibility summaries.
- **SC-017**: Given an upstream contract exporter and a help-parser fallback for the same release, source/binary or exporter/fallback mismatches are reported separately from SDK coverage gaps.
- **SC-018**: Runtime compatibility diagnostics warn at most once per client instance for a newer untested CLI version and include an explicit override path for advanced users.

## Assumptions

- The existing pinned upstream source remains the authority for SDK coverage decisions until an explicit promotion decision changes it.
- The first implementation increment should prioritize the offline semantic gate and deterministic artifacts before scheduled observer automation.
- Networked observation is non-blocking and must never promote supported state automatically.
- Manual source review remains required for behavior that cannot be extracted from local declarative source patterns.
- A full source commit is required for final checked-in baseline records even when a release version, tag, or short commit is shown to users.
- Source provenance, input/output contracts, and test evidence are required before a typed row can count as complete coverage.
- US1 checks the supported offline baseline only; candidate diff behavior is validated in US3 and is consumed by the coverage gate only when candidate artifacts are explicitly provided (`--with-candidate` or equivalent). MVP-1a is US1, MVP-1b is US3 diff, and MVP-1c is explicit promotion. Blocking CI MUST NOT auto-diff a candidate merely because `state.candidate` is present.
- Checked-in approved SDK decisions live in `contracts/sdk-contract.yaml` as a placeholder until feature 003; the offline coverage gate source of truth in 002 is `src/multica_py/_generated/upstream_coverage.json`. Generated runtime/provenance artifacts live under `src/multica_py/_generated/` (supported contract: `upstream_supported_contract.json`). Test fixtures under `tests/fixtures/` are copies for tests only and MUST NOT be the production `contract_ref` for supported state.
- US5 in this feature increment is limited to non-promoting observation state updates and a dry-run scheduled workflow. Full download/verify/bundle/tracking-issue automation may remain incomplete without claiming US5/SC-014 complete.
- Generator production emit (Python signatures, enums, validators, docs, fixtures from approved contract) is deferred to feature 003. Feature 002 may validate approved-contract boundaries only.
- Collector method `go-helper` is not part of the active collection order until an implementation exists; trust maps MUST NOT advertise unimplemented methods as promotable paths.

## Out of Scope

- Automatically choosing public Python method names for newly discovered commands.
- Automatically approving renames, unsupported status, enum policy, API field mapping, or omitted/null/empty semantics.
- Implementing newly discovered Multica SDK resource methods as part of this feature.
- Publishing a new SDK release or changing supported baseline from a scheduled workflow.
- Building a general-purpose Go static analyzer for arbitrary data flow and control flow.
- Production SDK code generation from `contracts/sdk-contract.yaml` (deferred to feature 003).
- Single-source-of-truth merge of coverage manifest into approved YAML, structured landing zones, and argv-encoding oracles (deferred to feature 003).
