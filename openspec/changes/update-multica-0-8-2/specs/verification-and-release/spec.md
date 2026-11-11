## ADDED Requirements

### Requirement: Every 0.8.2 decision has table-driven evidence
Each approved presence rule, range, enum, conflict, authorization/not-found behavior, malformed payload, and response-field omission SHALL have named positive and negative coverage in the existing shared case tables or a justified contract-level assertion.

#### Scenario: Canonical public method coverage is complete
- **WHEN** discovery compares public eager and command methods with canonical operation cases
- **THEN** the sets are equal and every approved operation has exactly one canonical vector plus required noncanonical boundary rows

#### Scenario: Malformed payload fails deterministically
- **WHEN** a required field has the wrong type or a prohibited closed value
- **THEN** the relevant table-driven decoder case fails with the reviewed SDK exception and does not silently drop the malformed value

### Requirement: Contract generation is offline and byte-stable
Validation, render, check, source-link audit, and regeneration SHALL run without service credentials; the approved contract SHALL be the only production generator input.

#### Scenario: Repeated render is stable
- **WHEN** the same approved contract is rendered twice in clean transient directories
- **THEN** relative file sets and bytes are identical and committed generated output matches the render

#### Scenario: Evidence changes alone have no effect
- **WHEN** downloaded evidence or extractor suggestions change while the approved contract is unchanged
- **THEN** generated production bytes and public method discovery remain unchanged

### Requirement: Independent live verification uses the isolated test target
The final candidate SHALL be checked through the project-described `multica-test` target using an independent agent, isolated test-owned resources, strict `0.8.2` preflight, and failure-safe cleanup; this live check SHALL not use the primary Multica profile or daemon.

#### Scenario: Live public boundary succeeds
- **WHEN** the candidate executes the selected read/create/update/list/delete workflows against the isolated target
- **THEN** the evidence identifies the exact product revision, public SDK calls, test-owned resource IDs, assertions, exit status, and cleanup result without recording credentials or private host data in Git

#### Scenario: Readiness gate fails
- **WHEN** the prepared CLI is not exact `0.8.2`, the isolated target is unavailable, or required runner configuration is missing
- **THEN** no live attempt is consumed and verification remains incomplete rather than being reported as passed

### Requirement: Visible CLI changes have authentic before and after evidence
Changed rerun, issue-status, workflow/view, and error output selected by the verification plan SHALL have baseline and candidate text plus PNG captures produced by a confirmed renderer on macOS with equivalent fixtures, width, locale, and output mode.

#### Scenario: Capture is comparable
- **WHEN** independent verification captures a selected visible path
- **THEN** baseline and candidate artifacts identify their exact CLI revisions and preserve the tested output language while agent-authored explanation remains English

#### Scenario: Renderer is unavailable
- **WHEN** the readiness gate cannot confirm the renderer or equivalent baseline fixtures
- **THEN** mandatory image evidence remains missing and the verifier cannot report complete acceptance

### Requirement: Release gates prove one exact candidate revision
The candidate SHALL pass strict OpenSpec validation, contract/source checks, lint, types, offline tests, compatibility, package tests, independent live evidence, and exact-SHA CI/PR read-back before release approval.

#### Scenario: Planning artifacts remain immutable during implementation
- **WHEN** the final candidate is compared with the independently verified planning SHA
- **THEN** `openspec/changes/update-multica-0-8-2/` is byte-identical and all implementation tasks map to the approved delivery contract

#### Scenario: Evidence is published outside Git
- **WHEN** the independent verifier completes the candidate assessment
- **THEN** commands, exit codes, assertions, SHA/PR/CI/file links, logs, PNGs, limitations, and cleanup are attached to Multica with successful read-back while transient evidence remains untracked

