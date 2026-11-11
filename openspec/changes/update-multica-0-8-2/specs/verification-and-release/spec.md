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
The delivery SHALL set `e2e_required=true`, and the final candidate SHALL be checked through the project-described `multica-test` target using an independent agent, isolated test-owned resources, strict `0.8.2` preflight, and failure-safe cleanup; this live check SHALL not use the primary Multica profile or daemon.

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

## MODIFIED Requirements

### Requirement: Existing lower-level checks prove the SDK corrections
The implementation SHALL use the repository's existing unit, contract,
fake-CLI component, lifecycle, concurrency, documentation, packaging, and CI
capabilities to prove deterministic command, model, error, generation, and
exclusion behavior. The isolated live and image checks required by this change
SHALL separately prove the service, process, file-binding, authorization, and
visible-output gaps that lower-level checks cannot close.

#### Scenario: Every deterministic scenario has sufficient lower-level coverage
- **WHEN** argv, presence, range, response, malformed payload, error,
  generation, compatibility, package, and exclusion coverage is reviewed
- **THEN** every deterministic scenario maps to an existing table-driven or
  focused assertion at the lowest sufficient layer without duplicating the live
  walkthrough

#### Scenario: Independent verification uses the exact revision
- **WHEN** the Tester verifies the delivery from a fresh checkout
- **THEN** the Tester confirms the exact published revision, inspects the
  scenario-to-test mapping, runs or reads the required lower-level and CI
  evidence, and performs the separately required isolated live walkthrough
  without representing one evidence layer as the other

#### Scenario: Live infrastructure is bounded and isolated
- **WHEN** verification artifacts and dependencies are inspected
- **THEN** the existing repository-native walkthrough, protected live workflow,
  wrapper-owned `multica-test`, project-provided isolated target, test-owned
  resources, and confirmed renderer are the only live infrastructure added or
  extended; no parallel runner framework or primary Multica profile, daemon,
  checkout, database, or container is used

#### Scenario: Changed visible output has authentic images
- **WHEN** verification covers rerun-task, issue-status, or workflow/view output
  changed by the `0.8.2` target
- **THEN** equivalent verified `0.7.1` baseline and `0.8.2` candidate actions
  produce actual UTF-8 text and the mandatory before/after PNGs defined by the
  delivery plan, with missing renderer or baseline readiness blocking complete
  verification

## REMOVED Requirements

### Requirement: Local E2E and image evidence are not required

**Reason**: The `0.8.2` change adds real service lifecycle, cross-identity
authorization, run-targeted task, file-binding, and visible CLI-output risks
that deterministic lower-level checks cannot fully prove.

**Migration**: Set `e2e_required=true` and follow the isolated target,
readiness, authentic text/PNG, Multica publication, and cleanup contract in
`delivery-plan.md`; retain lower-level checks for deterministic behavior.

