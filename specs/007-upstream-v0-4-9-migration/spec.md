# Feature Specification: Upstream v0.4.9 Migration

**Feature Branch**: `binta/upstream-v0-4-9-migration`

**Created**: 2026-07-24

**Status**: Draft

**Input**: Migrate the supported upstream Multica CLI baseline from `v0.3.10`
at `be32e5af00c74cda60c2fe8c47d31402bc62b3a6` to `v0.4.9` at
`ecbdbda09e7b2be56cd9ccc55cee1ee360222d18` while preserving the existing
public SDK, reconciling its approved contract and provenance, and accepting
only source-confirmed behavior.

## Overview

`multica-py` is a Python SDK wrapper over the upstream `multica-ai/multica`
CLI. The supported live target is pinned to `v0.3.10`, while repository
compatibility metadata currently reports supported `v0.4.2`. A verified
evidence package describes the target `v0.4.9`, including 35 new command paths,
changes to existing issue, comment, project, and project-resource commands,
and shared timeout/error behavior.

This feature defines the conditions for a safe migration to `v0.4.9`. The
migration preserves the 16 existing approved operation IDs unless an explicit
compatibility decision states otherwise, corrects source-confirmed command and
parameter mappings, and makes every supported-version claim agree with the
approved contract and verified release provenance. It does not approve the 35
new command paths as public SDK operations.

## Goal

After this migration, maintainers and SDK consumers can rely on every existing
approved SDK operation having an explicit, source-backed compatibility outcome
for upstream `v0.4.9`; generated public behavior and all supported-version
metadata describe that same approved outcome; and offline and live evidence
distinguishes product regressions from infrastructure failures.

## Actors and Stakeholders

- **SDK consumer**: Uses the existing public operation IDs and expects compatible
  behavior, stable validation, and predictable presence semantics after the
  upstream migration.
- **SDK maintainer**: Reviews target-source evidence, approves contract changes,
  classifies upstream additions, and decides whether a public compatibility
  change is intentional.
- **Migration reviewer**: Verifies traceability, mappings, constraints,
  provenance, and acceptance evidence before declaring `v0.4.9` supported.
- **Release operator**: Uses an exact release, CLI checksum, and backend image
  digest and needs an unambiguous supported target.
- **Test operator**: Runs offline and live acceptance gates and needs failures to
  identify product, environment, authentication, or test-harness causes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preserve the Existing Public SDK (Priority: P1)

As an SDK consumer, I can continue using all 16 approved operation IDs against
upstream `v0.4.9`, or receive a deliberate and documented unsupported outcome,
without silent command remapping or changed omission behavior.

**Why this priority**: Existing public behavior is the compatibility boundary.
A migration that adds upstream coverage but breaks an approved operation is not
acceptable.

**Independent Test**: Classify all 16 operation IDs against exact target source,
then exercise their accepted command construction, validation, and response
behavior with positive and negative cases. The story passes only when no
operation remains unclassified.

**Acceptance Scenarios**:

1. **Given** the 16 unique operation IDs in the approved contract, **When** the
   target review is completed, **Then** every ID is classified as `compatible`,
   `intentionally changed`, or `explicitly unsupported`, with a reason and
   target-source evidence.
2. **Given** an operation classified as compatible, **When** a consumer supplies
   an input supported before the migration, **Then** the operation reaches the
   target command using the approved argument/flag mapping and produces the
   expected public outcome.
3. **Given** an operation classified as intentionally changed, **When** a
   consumer encounters the changed behavior, **Then** the approved contract
   states the compatibility impact and acceptance evidence demonstrates the
   intended result.
4. **Given** an operation classified as explicitly unsupported, **When** it is
   invoked for the target, **Then** it fails through a deliberate public outcome
   rather than an unknown-command, accidental fallback, or silently different
   operation.

---

### User Story 2 - Approve Source-Backed Contract Changes (Priority: P1)

As an SDK maintainer, I can approve only mappings and constraints traced from
the exact `v0.4.9` source, including the correct destination and presence
semantics of each accepted parameter.

**Why this priority**: Name similarity and degraded help output cannot prove
behavior. Incorrect destinations or omission rules can silently mutate user
data.

**Independent Test**: For every changed contract row, follow the parameter from
command input to its source-confirmed destination and verify positive and
negative cases for its accepted constraints and presence states.

**Acceptance Scenarios**:

1. **Given** a new or changed argument or flag, **When** it is proposed for an
   approved operation, **Then** evidence identifies its destination as path,
   query, JSON body, header, multipart body, or local control.
2. **Given** matching names such as a CLI flag and SDK field, **When** no target
   source trace proves their relationship, **Then** the mapping remains
   unapproved.
3. **Given** an update-style value, **When** omitted, explicitly null, empty,
   zero, or false are meaningful states, **Then** each accepted state has an
   explicit contract outcome and a corresponding acceptance scenario.
4. **Given** a declarative or imperative target constraint, **When** it affects
   an approved operation, **Then** the contract records the normalized rule and
   both a valid and invalid case demonstrate it.

---

### User Story 3 - Resolve Status and Provenance Conflicts (Priority: P1)

As a migration reviewer, I can determine exactly which issue-status command and
which upstream release the SDK supports, without contradictory contract,
generated, or live-target metadata.

**Why this priority**: The approved `issues.set_status` binding and supported
version records currently contradict target source or each other.

**Independent Test**: Compare the approved status binding and every supported
version/commit/checksum/digest record with exact target evidence, then verify
that all accepted artifacts identify the same target and contract decision.

**Acceptance Scenarios**:

1. **Given** the approved `issues.set_status` binding `issue set-status` and the
   target declaration `issue status`, **When** the operation is reviewed,
   **Then** exactly one source-backed target binding and compatibility outcome
   is approved before generation or release acceptance.
2. **Given** the live target at `v0.3.10` and generated supported state at
   `v0.4.2`, **When** migration provenance is approved, **Then** the historical
   states remain auditable and the new supported state consistently identifies
   exact target `v0.4.9`.
3. **Given** candidate-state evidence that points to a missing or differently
   named candidate contract, **When** provenance is checked, **Then** the
   reference is rejected until it resolves to the exact reviewed artifact.

---

### User Story 4 - Classify New Upstream Command Families (Priority: P2)

As an SDK maintainer, I can separate additions needed to preserve the existing
API from optional future SDK growth and local-only behavior, without
accidentally expanding the public surface.

**Why this priority**: The target adds 35 command paths, but migration scope and
new feature scope are different approval decisions.

**Independent Test**: Account for every family in the manual source delta using
the classification rules below. Verify that no unapproved family creates a new
operation ID or alters public generated behavior.

**Acceptance Scenarios**:

1. **Given** the 11 source-delta families, **When** migration scope is reviewed,
   **Then** every family is assigned one primary classification and any
   compatibility-relevant subset is explicitly identified.
2. **Given** a new command with high-confidence source evidence, **When** no
   explicit public operation decision exists, **Then** it remains outside the
   approved public SDK.
3. **Given** the help-degraded bundle's 107 `command_removed` rows, **When**
   migration requirements are derived, **Then** none is treated as a removal
   unless exact target source confirms it.

---

### User Story 5 - Obtain Interpretable Acceptance Evidence (Priority: P2)

As a test operator, I can run migration gates whose results distinguish SDK
compatibility from environment readiness, authentication limits, and broken
test execution.

**Why this priority**: Current baseline and candidate live failures are not
target-isolating, and the mutation check reports success even though its tests
never start.

**Independent Test**: Run offline gates and target live checks with validated
prerequisites and categorized diagnostics. Deliberately change each protected
target assumption and prove that the mutation check starts the intended tests
and detects the mutation for the expected reason.

**Acceptance Scenarios**:

1. **Given** baseline and candidate smoke have the same runtime-readiness
   failure shape, **When** results are compared, **Then** the shared failure is
   not automatically classified as a `v0.4.9` regression.
2. **Given** authentication rate limiting or unavailable runtime infrastructure,
   **When** a live gate cannot exercise compatibility behavior, **Then** the
   result is reported as an infrastructure/authentication limitation rather
   than a false product pass or failure.
3. **Given** mutation-check prerequisites are absent, **When** the check is
   invoked, **Then** it fails as an invalid test run and cannot satisfy
   migration acceptance.
4. **Given** valid mutation-check prerequisites, **When** each expected
   target/version mutation is applied, **Then** the intended tests start and
   fail for the changed invariant rather than for missing test tooling.
5. **Given** target smoke has completed successfully and repeat prerequisites
   are valid, **When** stability testing begins, **Then** ten consecutive smoke
   repetitions complete successfully before stability is claimed.

## Existing Operation Acceptance Matrix

Every row is mandatory migration scope. Classification values are assigned
during contract approval; no blank or inferred outcome is acceptable.

| Existing operation ID | Target behavior to prove | Minimum acceptance coverage |
| --- | --- | --- |
| `issues.create` | Target `issue create` grammar, required title, accepted optional fields, attachment handling boundary, and input-channel conflicts | Required-input success/failure; optional omission; accepted empty/null behavior; conflicting input channels |
| `issues.list` | Target filters plus `--sort`/`--direction` relationship and accepted status values | Default/list success; valid direction with non-position sort; direction rejection without valid sort; invalid enum |
| `issues.set_status` | Source-backed resolution of `issue set-status` versus target `issue status`, positional status mapping, and status enum | Approved path success; legacy-path compatibility outcome; invalid/omitted status |
| `issues.comments.add` | Target issue/comment identifiers, content destination, attachment/input-channel behavior | Valid add; omitted content; empty-content policy; conflicting content channels |
| `issues.comments.delete` | Target comment identifier and delete response/error behavior | Valid delete; missing/invalid identifier; not-found outcome |
| `issues.comments.list` | Target issue identifier, roots/summary/full and paging behavior relevant to the existing surface | Default list; accepted optional filter; conflicting or invalid paging/output input |
| `issues.labels.add` | Target issue and label identifiers and unchanged/changed command binding | Valid add; omitted/invalid label; duplicate/already-present outcome |
| `issues.labels.list` | Target issue identifier and output decoding | Valid list including empty result; invalid issue; malformed target response |
| `issues.labels.remove` | Target issue and label identifiers and delete behavior | Valid remove; omitted/invalid label; absent-label outcome |
| `projects.create` | Target `project create`, title mapping, accepted new fields only when approved, and required values | Minimal create; omitted required value; invalid enum/reference; optional omission |
| `projects.update` | Target changed-field mapping and omitted/null/empty behavior for every exposed update field | Omitted field unchanged; accepted explicit clear; valid update; empty update rejection if target rejects it |
| `projects.set_status` | Target command binding, status destination, and approved enum | Valid status; omitted status; invalid status; unchanged public outcome |
| `projects.resources.list` | Target project identifier and list response mapping | Valid non-empty and empty list; invalid project; malformed response |
| `projects.resources.add_local_directory` | Target resource type, local-path, daemon, label mappings and cross-field constraints | Valid add; each required field absent; incompatible type/ref; optional label omitted/empty |
| `projects.resources.update_local_directory` | Target project/resource identifiers and presence-sensitive local path/label changes | Valid update; omitted change; explicit clear where accepted; invalid reference combination |
| `projects.resources.remove` | Target project/resource identifiers and removal behavior | Valid remove; omitted/invalid identifier; absent-resource outcome |

## New Upstream Family Classification

Classification controls migration scope; it does not itself approve a contract
row or public operation ID.

| Source-delta family | Migration classification | Boundary |
| --- | --- | --- |
| `issue-existing-changes` | Required for compatibility | Review only behavior affecting `issues.create`, `issues.list`, `issues.comments.add`, and `issues.comments.list`; new fields and file behavior enter the public contract only when required to preserve or deliberately change those operations |
| `issue-new-commands` | Required subset plus extension candidates | Resolve `issues.set_status` and changed issue semantics in migration; pull requests, children, reorder, usage, and comment resolve/unresolve remain separate extension candidates |
| `project-and-root-registration` | Required subset plus CLI-only | Project and project-resource changes affecting existing operations are required; root flags are local configuration and not new public resource parameters |
| `attachments-and-client-transport` | Required subset plus deferred extension | Assess attachment behavior only where required by existing issue/comment operations; neither upload nor download is one of the 16 approved operation IDs, so both public surfaces require separate approval |
| `transport-error-contract` | Required compatibility review | Determine the public timeout/error compatibility outcome for all existing API-backed operations; local CLI implementation details do not automatically become SDK behavior |
| `chat-read` | Candidate for separate SDK extension | No migration operation ID is approved |
| `workspace-properties` | Candidate for separate SDK extension | Property definition/value models and public operations require separate scope and schema approval |
| `workspace-repository-management` | Deferred owner decision | Workspace repositories are not project resources; workspace create/invite and repo mutation cannot reuse project-resource operation IDs by name similarity |
| `runtime-and-local-control` | CLI-only/local-control plus deferred extension | Daemon probing and profile path overrides remain local control; runtime/profile mutations require separate public decision; existing runtime listing is reviewed only if shared behavior affects it outside the 16-operation contract |
| `agent-settings-and-skills` | Deferred owner decision | No approved agent mutation operation exists; presence-sensitive settings and skills changes do not enter this migration by default |
| `skills-squads-and-autopilots` | Deferred owner decision | Skill search, squad-role mutation, and subscriber replacement/clearing require separate public decisions; existing unrelated list behavior is not expanded |

## Edge Cases

- The exact target tag resolves to a commit different from the recorded target
  commit.
- The release archive checksum, executable checksum, reported CLI version, or
  backend digest disagrees with approved provenance.
- A command still exists but its path, alias, argument order, output mode,
  default, error, or validation behavior changed.
- A degraded help inventory reports removal while target source still declares
  the command.
- A target command is declared but a helper changes its actual path, query,
  body, header, multipart, or local-control destination.
- A parameter name matches an SDK field but the value lands in a different
  destination or is local-only.
- An update receives omitted, null, empty string, zero, or false and the target
  distinguishes them through value or flag presence.
- A repeatable flag is omitted, supplied once, supplied more than once, or
  supplied as an explicitly empty value.
- An imperative constraint is enforced only after parsing, including
  `requires`, `conflicts_with`, `exactly_one`, `at_least_one`,
  `required_together`, conditional enum/range, or custom validation.
- A source-confirmed enum is dynamic, open-ended, aliased, or deprecated and
  therefore cannot be safely promoted as a strict public enum automatically.
- An HTTP timeout or error classification changes globally but an existing
  operation wraps or exposes it differently.
- A live failure occurs before the operation under test is reached.
- Baseline and candidate fail with the same symptom but different underlying
  diagnostics.
- The mutation subprocess exits non-zero before collecting or executing the
  intended tests.
- A supported-state reference resolves to a missing file, a candidate artifact,
  or an artifact with a different semantic identity.
- An accepted migration artifact is regenerated from an unapproved evidence
  bundle instead of the approved contract.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The migration MUST use `v0.3.10` at
  `be32e5af00c74cda60c2fe8c47d31402bc62b3a6` as the historical live-target
  baseline and `v0.4.9` at
  `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18` as the target comparison.
- **FR-002**: The migration MUST classify each of the 16 existing approved
  operation IDs as `compatible`, `intentionally changed`, or `explicitly
  unsupported`.
- **FR-003**: An operation classification MUST include its target command path,
  compatibility rationale, target-source references, accepted input/output
  contract, and acceptance evidence.
- **FR-004**: Existing public operations classified as compatible MUST preserve
  their supported consumer-visible behavior on `v0.4.9`.
- **FR-005**: An intentionally changed operation MUST have an explicit approved
  compatibility decision and MUST NOT be introduced as an incidental generated
  change.
- **FR-006**: An explicitly unsupported operation MUST fail through a deliberate
  documented SDK outcome and MUST NOT silently invoke a different command.
- **FR-007**: The migration MUST resolve the `issues.set_status` binding conflict
  between approved `issue set-status` and target-source `issue status` before
  the target is accepted.
- **FR-008**: Every new or changed approved mapping MUST be traced through target
  command execution and called helpers; matching names alone MUST NOT establish
  a mapping.
- **FR-009**: Each accepted parameter MUST identify exactly one confirmed
  destination category: path, query, JSON body, header, multipart body, or local
  control.
- **FR-010**: Local-control inputs MUST NOT be represented as server-bound SDK
  parameters unless a separate approved public contract explicitly requires
  that behavior.
- **FR-011**: For every accepted update/patch-style parameter, the approved
  behavior MUST distinguish omitted, null, empty string, zero, and false when
  the target source distinguishes those states.
- **FR-012**: The migration MUST preserve the difference between “not provided”
  and an explicit null whenever null has target meaning.
- **FR-013**: Every changed declarative or imperative constraint affecting an
  approved operation MUST be normalized into a reviewable rule and covered by
  at least one positive and one negative acceptance scenario.
- **FR-014**: Enum candidates MUST require explicit approval of public name,
  strict/open policy, aliases, deprecated values, and operation scope before
  becoming part of the public contract.
- **FR-015**: The migration MUST review target changes to existing issue,
  issue-comment, project, and project-resource commands wherever they affect
  the 16 approved operations.
- **FR-016**: The migration MUST define the compatibility outcome of the target's
  shared timeout and error behavior for each affected existing public operation.
- **FR-017**: The approved SDK contract MUST remain the sole authority for
  generated public SDK behavior and compatibility metadata.
- **FR-018**: Pipeline suggestions, evidence manifests, heuristic rename
  suggestions, and generated upgrade bundles MUST NOT automatically change the
  approved contract or public behavior.
- **FR-019**: Help-degraded `command_removed` records MUST be treated as
  unconfirmed proposals and MUST NOT become removal requirements without exact
  target-source confirmation.
- **FR-020**: The 35 new target command paths MUST NOT be automatically added to
  the public SDK.
- **FR-021**: A new public operation ID MUST require a separate explicit scope
  and contract approval decision.
- **FR-022**: Every source-delta family MUST be classified as compatibility
  required, separate extension candidate, CLI-only/local-control, or deferred
  owner decision, with mixed families identifying their subsets.
- **FR-023**: Workspace repository commands MUST NOT be mapped to existing
  project-resource operations solely because both concepts refer to resources
  or repositories.
- **FR-024**: Chat, property, runtime profile, daemon control, skill, squad,
  workspace invitation, and similar new operations MUST remain outside mandatory
  migration scope unless target-source evidence proves they are needed to
  preserve an existing public operation.
- **FR-025**: Target release provenance MUST retain the exact tag, full commit,
  release identity, CLI archive and executable checksums, reported version, and
  backend image manifest/platform digests used for acceptance.
- **FR-026**: The migration MUST reconcile the live target's `v0.3.10` state,
  generated supported `v0.4.2` state, and target `v0.4.9` state without erasing
  historical provenance.
- **FR-027**: The approved contract, generated public SDK, generated supported
  state, and live target metadata MUST identify one mutually consistent
  supported target and approved contract outcome.
- **FR-028**: Every generated-state contract reference MUST resolve to the exact
  reviewed artifact and MUST fail validation if the artifact is missing,
  differently named, candidate-only, or semantically inconsistent.
- **FR-029**: Offline acceptance MUST cover command construction, decoding,
  constraints, presence semantics, error classification, approved contract
  consistency, and provenance consistency without requiring a live service.
- **FR-030**: Offline quality gates MUST pass for the supported project
  platforms before migration acceptance.
- **FR-031**: Live smoke and extended results MUST identify whether a failure
  arises from the target behavior, runtime readiness, authentication/rate
  limiting, environment setup, cleanup, or test harness.
- **FR-032**: The same failure shape in baseline and candidate MUST NOT
  automatically be classified as a target regression; the conclusion MUST use
  operation reachability and diagnostic evidence.
- **FR-033**: A live run that does not reach the compatibility behavior under
  test MUST NOT count as a migration pass or a target-specific product failure.
- **FR-034**: Migration acceptance MUST be blocked while mutation-check is
  invalid or can interpret missing test dependencies as successful mutation
  detection.
- **FR-035**: A valid mutation-check MUST prove that the intended tests were
  collected and started, and that each expected mutation was detected for the
  changed invariant rather than for an unrelated startup failure.
- **FR-036**: Stability repeat MUST run only after a successful stable smoke
  result with valid infrastructure prerequisites.
- **FR-037**: Stability acceptance MUST require ten consecutive successful smoke
  repetitions against the exact target provenance.
- **FR-038**: Live acceptance MUST retain interpretable diagnostics and confirm
  that test-created resources are cleaned up.
- **FR-039**: Missing auxiliary checks or expected evidence, including the
  absent test-architecture check and baseline coverage artifact, MUST be
  reported as unresolved gate inputs rather than silently treated as passes.
- **FR-040**: Migration approval MUST retain a trace from each changed operation
  and requirement to its acceptance evidence.

### Backward Compatibility Requirements

- **BC-001**: All 16 existing operation IDs remain the initial public
  compatibility boundary; no operation disappears by omission from review.
- **BC-002**: Existing accepted inputs keep their meaning unless an intentional
  change is explicitly approved and documented.
- **BC-003**: Optional values do not become required, and omitted values do not
  become explicit empty/null/zero/false values, without an intentional approved
  compatibility change.
- **BC-004**: Existing response and error outcomes remain decodable and
  classifiable; target changes that prevent this require an explicit
  compatibility decision.
- **BC-005**: Existing operation IDs MUST NOT be rebound to semantically
  different workspace, repository, property, runtime, skill, squad, or chat
  commands.
- **BC-006**: Unsupported target behavior MUST fail closed rather than falling
  back to an unverified command path or heuristic mapping.

### Evidence and Trust Model

Evidence is evaluated in the following priority order:

1. **Exact target upstream source** at
   `ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`.
2. **Release provenance** in `release-provenance.json`, including verified CLI
   and backend identities.
3. **Current approved SDK contract** in `contracts/sdk-contract.json`.
4. **Manual source delta** in `source-delta.json` with its cited exact source
   locations.
5. **Live test results and diagnostics**, interpreted according to operation
   reachability and environment validity.
6. **Help-degraded pipeline bundle**, used only as unconfirmed suggestions.

When two sources disagree, the higher-priority source controls factual target
behavior, while changes to the public contract still require explicit approval.
The exact source may disprove a current mapping but does not by itself authorize
a new public operation. Source references are evidence for requirements, not an
implementation sequence.

- **ET-001**: Evidence MUST preserve the exact source commit to which a
  conclusion applies.
- **ET-002**: Lower-priority evidence MUST NOT override higher-priority evidence.
- **ET-003**: Unknown patterns, unresolved helpers, dynamic enums, imperative
  validation, and presence-sensitive behavior MUST fail closed into review.
- **ET-004**: Automated extraction MAY record recognized declarative facts but
  MUST NOT approve mappings, public enum policy, new operation IDs, or public
  compatibility changes.
- **ET-005**: No pipeline suggestion may directly modify the approved contract.
- **ET-006**: No mapping may be accepted solely from matching names.
- **ET-007**: The source delta's 35 additions and 11 families are review scope,
  while the degraded bundle's 107 removals are not accepted deletion facts.

### Key Entities

- **Approved SDK operation**: A stable public operation ID with command binding,
  parameters, constraints, presence behavior, source references, and test
  references.
- **Compatibility decision**: The reviewed outcome for an existing operation:
  compatible, intentionally changed, or explicitly unsupported.
- **Parameter mapping**: The evidence-backed relationship between an SDK input,
  CLI argument/flag, and its actual destination.
- **Presence contract**: The distinct outcomes for omitted, null, empty, zero,
  and false values.
- **Constraint**: A normalized declarative or imperative rule with positive and
  negative acceptance evidence.
- **Upstream family classification**: The scope decision applied to one of the
  11 source-delta families.
- **Provenance record**: Exact target release, source, CLI, and backend identity
  used for compatibility acceptance.
- **Acceptance run**: Offline or live evidence with valid prerequisites,
  operation reachability, categorized outcome, diagnostics, and cleanup status.

## Dependencies and Known Blockers

### Dependencies

- Exact base and target source snapshots and source references from the evidence
  package.
- Verified `v0.4.9` release, CLI checksum/version, and backend digest evidence.
- The current approved 16-operation SDK contract.
- Maintainer approval for every intentional compatibility change and every
  proposed new public operation.
- Valid target runtime and authentication access for interpretable live
  acceptance.

### Known Blockers

- The live target identifies `v0.3.10`, while generated supported state
  identifies `v0.4.2`.
- `issues.set_status` is approved against `issue set-status`, while target source
  declares `issue status`.
- Baseline and candidate smoke both report `31 passed, 1 failed` with a shared
  runtime-readiness failure.
- Candidate extended reports `74 passed, 5 failed, 1 deselected` with runtime
  readiness failures and auth rate-limit diagnostics.
- Mutation-check is invalid because intended subprocess tests reported
  `No module named pytest` and non-zero subprocess exit was mistaken for
  successful mutation detection.
- Stability repeat was not run because smoke and extended were not successful.
- Candidate generated-state evidence refers to a candidate filename that does
  not match the materialized bundle artifact; current generated state also
  contains candidate metadata that is not migration approval.
- The expected test-architecture check is absent, and one baseline check expects
  a missing coverage artifact.

These blockers prevent migration acceptance but do not prevent planning after
the specification is approved.

## Assumptions

- The 16 unique operation IDs listed by the current approved contract are the
  complete mandatory public compatibility boundary for this migration.
- No target command deletion is accepted in the reviewed CLI scope because the
  exact manual declaration comparison found none.
- The target remains `v0.4.9` at the recorded full commit; any replacement
  release or commit requires new provenance and compatibility review.
- New upstream command families default to non-public until explicitly approved.
- Compatibility-required subsets of mixed families may be migrated without
  approving the rest of that family.
- Existing operation behavior is preserved by default; explicit breakage is
  exceptional and requires maintainer approval.
- Live environment failures are resolved or isolated before live results become
  acceptance evidence.
- The migration reuses the repository's offline-by-default quality policy and
  supported platform scope.

## Out of Scope

- Implementing the migration in this specification phase.
- Editing the public SDK, approved contract, generated artifacts, supported
  state, or live target metadata in this specification phase.
- Running generation, promotion, rejection, manifest-suggestion application,
  planning, task generation, or implementation in this phase.
- Automatically exposing all 35 new target command paths.
- Approving new public operation IDs for chat, workspace/issue properties,
  issue pull requests/children/reorder/usage/comment resolution, workspace
  repositories/create/invite, runtime/profile mutations, daemon controls, agent
  settings/skills, skill search, squad roles, or autopilot subscriber mutation.
- Treating CLI-only local controls as server-backed SDK resource operations.
- Solving unrelated test-suite architecture or coverage-artifact gaps except
  where their absence makes a migration gate uninterpretable.
- Changing the upstream service or CLI implementation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the 16 existing approved operation IDs are classified as
  compatible, intentionally changed, or explicitly unsupported; zero remain
  unknown or implicitly dropped.
- **SC-002**: 100% of changed operation IDs identify exact target behavior,
  source evidence, parameter destinations, compatibility impact, and acceptance
  evidence.
- **SC-003**: 100% of accepted presence-sensitive parameters have verified
  outcomes for every applicable state among omitted, null, empty, zero, and
  false.
- **SC-004**: 100% of changed constraints affecting approved operations have at
  least one passing valid case and one passing rejection case.
- **SC-005**: The approved contract, generated public surface, supported state,
  and live target provenance have zero target version, commit, or contract
  contradictions.
- **SC-006**: All required offline quality gates complete successfully on every
  supported project platform without live backend or network access.
- **SC-007**: Target smoke and extended acceptance produce zero uncategorized
  failures and zero infrastructure false positives; every non-pass identifies
  operation reachability and a product, infrastructure, authentication,
  cleanup, or harness category.
- **SC-008**: Mutation acceptance shows that 100% of expected mutation cases
  collect and start their intended tests, and each expected mutation is detected
  for its protected invariant; missing test tooling can never yield a pass.
- **SC-009**: After a successful smoke prerequisite, 10 of 10 consecutive smoke
  repetitions pass against the same exact target provenance.
- **SC-010**: All 11 new/changed upstream families are classified, while zero new
  public operation IDs are introduced solely from help-parser output, manifest
  suggestions, heuristic name matching, or unapproved bundle artifacts.
- **SC-011**: Zero degraded `command_removed` suggestions are classified as
  confirmed removals without exact target-source evidence.
- **SC-012**: Every migration-created live resource is removed after acceptance
  runs, and diagnostics contain no exposed secret values.
