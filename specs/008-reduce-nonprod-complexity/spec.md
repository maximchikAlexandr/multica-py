# Feature Specification: Reduce Non-Production Complexity

**Feature Branch**: `008-reduce-nonprod-complexity`  
**Created**: 2026-07-25  
**Status**: Draft  
**Input**: User description: "Reduce the non-production codebase using audit findings 1–6 and 8; preserve code generation for upstream API migration; replace historical Spec Kit material with OpenSpec-compatible specifications, while the full Spec Kit-to-OpenSpec migration follows this reduction."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintain a lean SDK verification suite (Priority: P1)

As an SDK maintainer, I can change a public SDK operation and receive focused
evidence that its externally observable behaviour remains covered, without
maintaining tests that merely enforce the internal shape, size, or file layout
of the test suite.

**Why this priority**: The primary outcome is a substantially smaller,
maintainable verification system while preserving confidence in the public SDK.

**Independent Test**: A maintainer can run the default offline verification on
any public-operation change and see complete command construction,
decoding, validation, transport, and package evidence without the removed
meta-governance checks.

**Acceptance Scenarios**:

1. **Given** a supported public SDK operation, **When** its command mapping is
   verified, **Then** one canonical case records its complete expected call and
   the operation cannot silently disappear from required command coverage.
2. **Given** a refactoring that changes only test organization, **When** the
   default verification runs, **Then** it is not rejected solely because of
   historic test node identifiers, registry names, file counts, or line-count
   budgets.
3. **Given** a generated public binding, **When** the package is built and
   installed in a clean environment, **Then** the binding is available and
   behaves according to the approved contract.

---

### User Story 2 - Migrate an upstream CLI release through approved generation (Priority: P1)

As a maintainer, I can assess and adopt a new upstream CLI release through a
human-reviewed contract and deterministic generation, without a second state
machine or checked-in duplicate outputs obscuring what changed.

**Why this priority**: Upstream migration is the core maintainer workflow and
must retain strong source evidence, review, and code generation despite the
reduction of surrounding infrastructure.

**Independent Test**: Starting with a pinned upstream release, a maintainer can
produce review evidence, update the approved contract in a reviewable change,
generate all supported projections, and verify reproducibility and package
contents.

**Acceptance Scenarios**:

1. **Given** pinned upstream source and release evidence, **When** extraction
   encounters an unknown or unresolved pattern, **Then** it produces a review
   item and cannot alter the approved SDK contract or public behaviour.
2. **Given** an approved contract update, **When** generation runs twice in
   clean work areas, **Then** the generated projections are identical and pass
   syntax and semantic validation.
3. **Given** a proposed release migration, **When** it is approved and merged,
   **Then** that reviewed change is the sole promotion decision; no parallel
   candidate/supported state, recovery journal, or automatic promotion is
   required.
4. **Given** generated runtime public code, **When** it is reviewed, **Then**
   there is at most one authoritative repository projection of it; generated
   fixtures are not maintained as duplicate golden copies.

---

### User Story 3 - Run focused live and CI assurance (Priority: P2)

As a release maintainer, I can confirm that the SDK works with a prepared real
target and that required CI jobs run, without owning an upstream backend control
plane or brittle tests of workflow text.

**Why this priority**: End-to-end confidence must remain, but the SDK repository
should not duplicate upstream backend and CI-platform responsibilities.

**Independent Test**: A prepared target can execute the compact release smoke
set, while pull-request checks demonstrate required outcomes without assertions
about workflow formatting or an SDK-managed backend sandbox.

**Acceptance Scenarios**:

1. **Given** a prepared target, credentials, workspace, and CLI release,
   **When** the compact live smoke suite runs, **Then** it verifies target
   identity, critical create/read/update/delete behaviour, one list-decoding,
   an error mapping, and a presence-semantics case.
2. **Given** backend provisioning or agent-sandbox lifecycle work, **When** it
   is needed for broader acceptance, **Then** it is owned by the upstream
   service environment rather than recreated by the SDK repository.
3. **Given** a pull request, **When** required CI jobs complete, **Then** their
   outcomes provide the acceptance signal and an equivalent workflow
   reorganization does not fail merely from textual workflow assertions.

---

### User Story 4 - Preserve useful project knowledge for OpenSpec (Priority: P2)

As a future OpenSpec user, I can find the current product requirements and
decisions in concise OpenSpec-compatible specifications after historical Spec
Kit feature records are removed.

**Why this priority**: Deleting stale process history must not discard active
product knowledge, and this prepares a separate, later migration to OpenSpec.

**Independent Test**: A reviewer can trace each retained active requirement
from the historical feature material to an OpenSpec-compatible requirement with
at least one concrete scenario, without needing the removed feature folders.

**Acceptance Scenarios**:

1. **Given** completed historical feature records 001–006, **When** the cleanup
   is complete, **Then** they are no longer active repository documentation and
   their retained requirements are represented as plain Markdown requirements
   with concrete scenarios in the format expected by OpenSpec.
2. **Given** the future framework migration has not started, **When** the
   cleanup feature is completed, **Then** no OpenSpec command installation,
   agent-integration replacement, or workflow migration is required by this
   feature.

### Edge Cases

- A legacy specification contains a requirement still relied on by an active
  contract, release policy, or verification flow; it must be retained in the
  OpenSpec-compatible baseline before the source record is removed.
- An extractor can read a new upstream pattern but cannot classify its public
  meaning; the release remains unapproved until a human records the decision.
- Generated runtime code is absent or stale in a working checkout; a clean
  verification or package build must generate and validate the required output
  rather than relying on cached files.
- A prepared live target is unavailable; the default offline suite remains
  runnable and the live result is reported as unavailable rather than replaced
  with a backend emulator.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST remove completed historical Spec Kit feature
  records 001–006 from the active tree only after extracting every still-active
  product requirement, contract rule, and release requirement they contain.
- **FR-002**: The retained historical knowledge MUST be expressed as concise,
  OpenSpec-compatible baseline specifications: each requirement uses normative
  language and has at least one concrete `WHEN`/`THEN` scenario. These baseline
  specifications MUST be usable by the subsequent OpenSpec migration without
  reinterpreting the removed records.
- **FR-003**: This feature MUST NOT install, configure, or switch the project
  to OpenSpec; that framework migration is explicitly a subsequent feature.
- **FR-004**: The default verification suite MUST retain exact coverage of
  command construction, input presence semantics, validation constraints,
  distinct result decoding shapes, transport method/timeout/stdin behaviour,
  error mapping, redaction, and environment isolation for supported public SDK
  operations.
- **FR-005**: Each supported public operation MUST have one canonical required
  command-coverage record. Equivalent duplicate harnesses and metadata catalogs
  MUST NOT independently restate the same operation coverage obligation.
- **FR-006**: The project MUST replace architecture-baseline, historical-node,
  fixed-file-layout, fixed-registry-count, and line-count enforcement with
  focused completeness and outcome checks that protect public behaviour.
- **FR-007**: The live SDK verification scope MUST be limited to a prepared
  target and critical SDK round trips: release identity, simple resource CRUD,
  one list-decoding, one error mapping, and one presence-semantics case, plus a
  process timeout/cancellation case only when it cannot be proven offline.
- **FR-008**: The SDK repository MUST NOT provision, manage, or validate the
  full upstream backend, agent sandbox, direct backend API, or related control
  plane as part of its blocking SDK acceptance scope.
- **FR-009**: Upstream release adoption MUST retain a human-approved contract
  as the only input permitted to change generated public SDK behaviour.
- **FR-010**: Upstream extraction MUST produce review evidence only. Unknown
  source patterns, unresolved mappings, dynamic choices, and presence-sensitive
  behaviour MUST fail closed into review items and MUST NOT automatically
  promote a release or modify the approved contract.
- **FR-011**: One reviewed repository change MUST be the only promotion path
  for an upstream contract update. Parallel candidate/supported state, automatic
  promotion, promotion recovery journals, upgrade bundles, and heuristic rename
  promotion MUST be removed from the active workflow.
- **FR-012**: Deterministic generation MUST derive the maximum supported
  behaviour from the approved contract, including public bindings, choices,
  validators, operation metadata, documentation projections, and verification
  cases where the contract contains sufficient information.
- **FR-013**: Generated runtime public code MUST have at most one authoritative
  repository projection. Other generated projections, source evidence, review
  reports, and build outputs MUST not be kept as duplicate golden snapshots in
  version control.
- **FR-014**: Clean verification MUST prove deterministic generation, generated
  artifact validity, semantic contract completeness, and package availability
  without relying on a checked-in golden copy of the same generated output.
- **FR-015**: CI acceptance MUST be based on required job outcomes and product
  checks, not tests that freeze textual workflow layout, job naming, schedule
  wording, or equivalent CI configuration choices.

### Key Entities *(include if feature involves data)*

- **Approved contract**: The human-reviewed description of supported upstream
  SDK behaviour and the sole source allowed to drive public generation.
- **Source evidence**: Read-only facts and unresolved review items obtained from
  a pinned upstream release; it informs approval but never changes behaviour by
  itself.
- **Generated projection**: A deterministic derivative of the approved
  contract, either the single runtime projection or a transient verification,
  documentation, or build output.
- **Canonical operation coverage record**: The one required record proving the
  expected external command behaviour for a supported public operation.
- **OpenSpec-compatible baseline specification**: Concise requirements and
  concrete scenarios preserved from active historical project knowledge for the
  later OpenSpec migration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The default offline verification completes without a network,
  account, server, backend provisioner, or agent sandbox, and every supported
  public operation remains represented by exactly one canonical command-coverage
  record.
- **SC-002**: For a pinned upstream release update, maintainers can
  produce review evidence, approve the contract, generate all supported
  projections, and obtain a reproducible valid package using one reviewed
  repository change and no parallel promotion state.
- **SC-003**: No full generated-output golden fixture remains in version control;
  two clean generation runs for the same approved contract produce identical
  results and the resulting package exposes all expected generated public code.
- **SC-004**: The retained knowledge from completed features 001–006 is covered
  by OpenSpec-compatible baseline requirements and scenarios, with no active
  project reference pointing to a removed historical feature directory.
- **SC-005**: A prepared target can complete the compact live smoke scope, while
  lack of that target does not prevent offline pull-request verification.

## Assumptions

- The pinned upstream CLI source and release binary remain authoritative for
  public SDK contract decisions.
- Broad backend and agent-sandbox acceptance can be moved to, or explicitly
  accepted by, the upstream Multica environment owners before SDK-owned coverage
  is removed.
- Runtime generated code may remain as the single committed projection because
  it is part of the published SDK and makes the public API diff reviewable;
  other generated material is transient.
- The later OpenSpec migration will adopt the prepared baseline specifications
  and is outside this feature's implementation, tooling, and workflow scope.
- Audit items concerning mutation policy, packaging install modes, mypy scope,
  and local cache cleanup are out of scope for this feature.
