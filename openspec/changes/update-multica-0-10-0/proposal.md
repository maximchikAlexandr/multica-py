## Why

Multica `0.10.0` changes supported CLI and response contracts beyond the SDK's reviewed `0.7.1` ceiling. The SDK needs one direct, evidence-backed `0.7.1` to `0.10.0` refresh so retained Python APIs decode the proven target behavior without automatically publishing every new upstream command.

## What Changes

- Advance the approved target from exact Multica `0.7.1` release commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0` to stable `0.10.0`, release `446890529`, commit `2fcb424b72b024f65161809081009063846ea44d`, using the verified Darwin/arm64 archives, checksums, executable identities, and direct comparison range.
- Reconcile the complete CLI inventories (`209` baseline nodes and `246` target nodes: `38` added, `1` removed, `26` changed) and all `196` supported response entrypoints, including dynamic `checkin`, hidden/source-only names, exact Cobra constraints, RunE/helper destinations, and explicit disposition for every node.
- Adapt retained models and operations for additive task, attachment, comment-resolution, project, runtime, user-profile, workspace, requester, subscriber, activity/archive, pagination, private-project, cancellation, text, metadata, webhook, and runtime-delete behavior while preserving older-server omissions and open upstream values.
- **BREAKING** replace the removed public CLI mapping `issue rerun` with the proven run-targeted `issue rerun-task` contract; provide migration guidance and do not preserve a command that no longer exists.
- Keep issue batch/delete, issue-status, workflow, project workflow/member/archive/restore, saved-view, runtime-concurrency, PR-link, and other new command families deferred until a separately approved public contract defines naming, presence, destructive confirmation, partial-success, and error policy.
- Regenerate only from reviewed `contracts/sdk-contract.json`, extend existing table-driven fixtures/tests and documentation, and run deterministic generation, source-link, offline, typing, lint, OpenSpec, packaging, and exact-revision delivery gates.
- Keep archives, binaries, collector output, audit JSON, and transient renders review-only and untracked.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: Pin the direct `0.7.1` to `0.10.0` provenance, complete CLI/response reconciliation, compatibility policy, reviewed mappings, and deterministic projection.
- `sdk-surface`: Adapt retained public resources/models, migrate issue rerun to run-targeted rerun-task, and preserve explicit defer/not-SDK-surface decisions.
- `subprocess-transport`: Preserve literal text and omission channels, typed `499` cancellation, strict metadata/webhook handling, and bounded destructive-error decoding.
- `verification-and-release`: Require table-driven positive/negative coverage, documentation, package gates, independent isolated-stand evidence, and exact-SHA publication without tracking diagnostics.

## Impact

- Approved contract and projection: `contracts/sdk-contract.json`, `src/multica_py/_generated/approved_sdk.py`, `scripts/upstream_contract.py`, and source/test references.
- Existing resource, entity, wire-model, decoder, transport, and exception seams for issues, projects, runtimes, users, workspaces, attachments, comments, subscribers, task runs, metadata, and autopilots.
- Existing operation case tables, fake-CLI component fixtures, contract tests, live-smoke workflow, compatibility/API/migration/coverage/changelog/release documentation, and packaging audits.
- No new runtime dependency, top-level SDK resource, generic E2E framework, or public method for deferred upstream command families.
