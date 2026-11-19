## Context

The repository currently pins an approved Multica `0.7.1` contract at SDK base
`b268e3bec0436fe51727fda50583344f57663284`. `MYL-668` provides verified
`0.11.0` release, binary, source, command, and response evidence for a direct
upgrade: `256` target help nodes, four source-only names, and `196`
supported response work items with no pending review. The repository already
has the necessary seams: a human-approved JSON contract, deterministic renderer,
typed model/resource/transport layers, frozen case tables, an isolated live
verifier, and an exact-PR-head trusted workflow.

## Goals / Non-Goals

**Goals:**

- Make the approved contract and generated projection describe exact Multica
  `0.11.0` while preserving explicit human control of public SDK coverage.
- Implement only approved adaptations, including task-identity rerun, target
  presence/constraint semantics, and typed safety errors.
- Close the change with table-driven offline evidence, a minimal isolated live
  gap check, compatible documentation, package verification, and exact-SHA
  publication.

**Non-Goals:**

- Publishing every new CLI family discovered by extraction.
- Replacing the contract/generator architecture, test framework, E2E runner, or
  trusted workflow.
- Backend provisioning, direct HTTP verification, production deployment,
  automatic release, or intermediate-version delivery steps.

## Decisions

### 1. Reconcile the direct range in the approved contract

`contracts/sdk-contract.json` remains the sole production source. Reviewers
will replace its provenance, command/response registries, mappings,
compatibility metadata, source links, and canonical references using the exact
`0.11.0` evidence. The renderer then updates the existing committed generated
module, and a second render proves byte equality.

Alternative considered: generate public behavior from collector output. Rejected
because source extraction cannot decide naming, presence, enum, compatibility,
or public-value policy.

### 2. Reuse current typed seams and remove legacy rerun

Changed wire fields enter existing models/wires/decoders and immutable entities;
changed commands enter existing resources and command builders; status/error
shapes enter the current transport and exception mapping. The public issue-rerun
mapping is removed and replaced with an explicit task-id rerun operation and
typed result. No compatibility alias is retained because it would preserve the
wrong identity model and make removal unverifiable.

Alternative considered: add broad target-specific wrappers or a second model
layer. Rejected because the current seams already encode presence, exact argv,
decoding, and typed errors.

### 3. Keep new families deferred by default

Only contract rows explicitly marked `adapt` become public. Chat wakeups,
inbox, batch/delete/linking, issue-status, view/workflow, and other new families
remain absent. Unknown enum values survive only where the approved policy is
open; extractor candidates never define public enum names.

Alternative considered: mirror the complete target CLI. Rejected because command
existence does not establish a stable Python API or compatibility policy.

### 4. Grow existing frozen test tables

Repeated argv, command, decoding, operation-completeness, and payload regression
coverage is added to existing frozen tables and fixtures. Focused tests are
reserved for lifecycle, privacy, cancellation, destructive safety, and
deterministic-render invariants that cannot be represented clearly as rows.
No dependency or parallel test framework is added.

Alternative considered: one test module per upstream feature. Rejected because
it duplicates setup and weakens the repository's closed operation inventory.

### 5. Use one minimal live verifier extension

The existing verifier proves the remaining real integration gaps: inline/file
text persistence, escaped metadata-key round-trip, and archived-project conflict
with restore-before-delete cleanup. Deterministic or unsafe cases remain in
offline fake-CLI/transport coverage. The trusted workflow checks an open
same-repository PR head, exact candidate SHA, protected credentials, observed
`0.11.0`, and sanitized evidence before and after the run.

Alternative considered: a second target-specific runner or broader live sweep.
Rejected because lower-level checks prove most contracts more safely and
deterministically.

## Risks / Trade-offs

- [A deferred family is valuable to users] → Preserve complete dispositions and
  source evidence so a later focused OpenSpec can approve it without widening
  this migration.
- [Direct-range changes interact across releases] → Validate all `256` command
  nodes and all `196` response rows against exact endpoints instead of
  composing intermediate assumptions.
- [Presence or enum policy regresses legacy payloads] → Require omitted, null,
  malformed, unknown-token, and frozen legacy fixtures at the decoder boundary.
- [Live verification mutates shared state] → Use wrapper-owned isolation,
  disposable registered resources, readiness before mutation, and
  restore/delete cleanup on every exit path.
- [A long local suite exceeds the workspace limit] → Stop only the owned process
  at ten minutes and run the unsplit suite in CI at the published exact SHA.

## Migration Plan

1. Approve the exact target contract and deterministic generated projection.
2. Adapt models/decoders/exports, then command builders/resources/transport.
3. Extend consolidated tests, the existing verifier/workflow, and documentation.
4. Run focused and repository-wide gates on one consolidated candidate.
5. Publish normally, prove remote/local SHA equality, and perform independent
   exact-revision verification before any release decision.

Rollback before release is a normal revert of the implementation commits and
restoration of the prior approved contract/projection. No database or deployed
state migration is introduced.

## Open Questions

None. New-family support, enum naming, and any future deprecation window are
explicitly outside this change rather than delegated to implementation.
