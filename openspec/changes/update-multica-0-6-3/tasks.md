## 1. Approved Contract and Deterministic Generation

- [ ] 1.1 Update `contracts/sdk-contract.json` from the exact 0.6.1 baseline to the verified 0.6.3 release identities, `[0.6.0,0.6.4)` compatibility policy, 209-node CLI inventory, and 196-item response dispositions with commit-pinned sources and explicit exclusions.
- [ ] 1.2 Extend the existing contract schema and validation only where required for multi-value property shapes, project workflow identity, daemon CLI commit, reviewed diagnostics, and their positive/negative evidence references.
- [ ] 1.3 Add source-linked mutation/table cases that reject stale provenance, incomplete node/response counts, unresolved dynamic `checkin`, unapproved workflow/autostart surface, invalid mappings, and missing test/documentation actions.
- [ ] 1.4 Render the existing approved generator twice to transient directories, prove byte equality, refresh the tracked approved runtime projection, and make generated freshness fail on manual drift.

## 2. Typed Runtime Adaptations

- [ ] 2.1 Extend the existing property value wire/public annotation and decoder for strict immutable string tuples while preserving scalar, null, empty, ordered, duplicate, raw-projection, and open property-type behavior.
- [ ] 2.2 Extend `IssuePropertyResource.set` and `set_command` with deterministic legacy-string and compact JSON-array encoding plus pre-transport rejection of non-string collection items.
- [ ] 2.3 Add nullable `workflow_id` to the existing project wire/entity and preserve named UUID, null, omitted legacy, binding, serialization, and partial-update behavior.
- [ ] 2.4 Keep workflow-aware issue create/status/update/project-move argv atomic and unchanged while decoding authoritative remap/assignee/run-handoff results and surfacing validation conflicts without retry.
- [ ] 2.5 Add nullable `cli_commit` to `DaemonStatus`, preserving full SHA and normalizing omitted/null/empty legacy output without adding a command or model hierarchy.
- [ ] 2.6 Align wakeup diagnostics, attachment upload failure, stable redacted 500 error, and partial-side-effect handling through existing exception/redaction paths without leaking backend detail.

## 3. Focused Automated Verification

- [ ] 3.1 Extend existing frozen unit/resource case tables for multi-value property definition/write/decode cases, including presence, order, duplicates, commas, null, empty, malformed arrays, complete argv, and zero-I/O validation.
- [ ] 3.2 Extend existing project/issue unit and component tables for workflow UUID/null/omission, create/status/update/move success and conflict, server status remap, assignee/run handoff, partial updates, exact call counts, and no retry.
- [ ] 3.3 Extend existing daemon, wakeup, transport, attachment, and redaction tables for full/legacy CLI commit, reviewed diagnostics, stable safe errors, upload partial effects, and unchanged retained responses.
- [ ] 3.4 Extend public discovery, signatures, canonical vectors, approved bindings, response closure, source-link, compatibility, and forbidden-content assertions so excluded surfaces remain absent and all 209/196 dispositions reconcile exactly.
- [ ] 3.5 Update the protected live-smoke controller and existing public-SDK smoke cases to require exact CLI 0.6.3 and cover only the cross-component workflow/property behavior not proven by offline tests; do not add a parallel E2E framework.
- [ ] 3.6 Add repository-owned `scripts/e2e/myl495_verify.sh` and `scripts/render_terminal.swift`: the shell driver SHALL acquire checksum-pinned baseline/target CLI archives, create isolated SDK checkouts/profiles/daemons/Compose state, provision and verify disposable property/workflow/project/issue fixtures through documented test-only server setup calls, run the approved C02-C04 walkthrough, and clean all disposable state on success or failure; the Swift renderer SHALL deterministically convert captured UTF-8 terminal text to PNG on macOS without an external repository or package.

## 4. Documentation and Release Coherence

- [ ] 4.1 Update README, API, CLI coverage, compatibility, migration, contributing, service-usage, and releasing guidance for the direct 0.6.1-to-0.6.3 migration, `[0.6.0,0.6.4)` interval, approved behavior, exclusions, evidence flow, and atomic rollback.
- [ ] 4.2 Update package/export/generated-documentation assertions and examples for multi-value properties, workflow identity, daemon commit, diagnostics, and compatible legacy output without advertising deferred or non-SDK surfaces.

## 5. Acceptance at One Candidate SHA

- [ ] 5.1 Run strict OpenSpec validation; source-aware approved-contract validation; deterministic double render and generated check; source-link audit; focused tests; Ruff format/check; mypy source/tests/scripts; complete non-live pytest and live-node exclusion; build; wheel/sdist package tests; and Git/package forbidden-content audits at one clean SHA.
- [ ] 5.2 After human approval, run the independent local/live verification contract against exact candidate and CLI 0.6.3 revisions, publish commands, exit codes, assertions, commit/file/MR links and required images only in Multica, and preserve the evidence branch/MR while cleaning the temporary stand.
