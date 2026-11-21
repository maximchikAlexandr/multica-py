## Why

Multica `0.11.1` is the latest verified stable release, while the SDK contract and compatibility ceiling remain pinned to `0.7.1`. A direct, evidence-backed refresh is required so the existing 196 supported entrypoints remain truthful across the 263-node target CLI without automatically promoting newly discovered commands, response fields, or enum policy.

## What Changes

- Advance the approved upstream target from exact Multica `0.7.1` release `425269384` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0` to exact `0.11.1` release `451169000` at `e1fe10d6694848e35dd1aa00e08cd11d93e545ac`, using the verified Darwin arm64 release archive and executable identities.
- Reconcile all 263 target help nodes and every positional argument, alias, local/inherited flag, default, constraint, and source-only name with one explicit `retain`, `adapt`, `remove`, `defer`, or `not_sdk_surface` decision.
- Reconcile all 196 existing supported response entrypoints with exact old/target source traces: adapt 102 changed contracts, retain 94 unchanged contracts, and leave zero pending decisions.
- Replace the legacy public `issue rerun` binding with `issue rerun-task` under the existing SDK operation and migration policy; do not retain an argv fallback that the target CLI removed.
- Adapt existing typed models, adapters, mappings, and tests for changed retained behavior, including squad assignees, webhook payload conditions, optional `run_outcome`, runtime `daemon_id`, issue text sanitization/presence, pagination, and reviewed 400/409/413 typed errors.
- Keep all other newly added command families deferred, including chat wakeups, inbox, issue batch/delete/PR linking, issue-status, view, workflow, project membership/workflow/archive, and runtime concurrency.
- Preserve the approved-contract-only deterministic generation boundary; collector evidence, reconciled manifests, audit JSON, binaries, and `.devlocal` output remain untracked review inputs.
- Extend existing table-driven unit, contract, component, compatibility, documentation, packaging, and CI checks for direct `0.7.1` to `0.11.1` migration and rollback.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: Pin the direct `0.7.1` to `0.11.1` provenance, complete CLI/response reconciliation, compatibility interval, source-link closure, and deterministic projection.
- `public-cli-parity`: Require a complete five-way decision for every target node and source-only name while promoting only the reviewed replacement for legacy issue rerun.
- `sdk-surface`: Adapt existing public operations, typed models, adapters, presence/error semantics, and migration behavior without publishing deferred command families.
- `verification-and-release`: Require complete table-driven coverage, exact-revision CI/package evidence, direct migration/rollback documentation, and independent verification without task-specific live infrastructure.

## Impact

- Approved contract and generation: `contracts/sdk-contract.json`, `tools/upstream_contract/`, `scripts/upstream_contract.py`, `scripts/audit_source_links.py`, and `src/multica_py/_generated/approved_sdk.py`.
- Existing public models/resources/entities and wire adapters for autopilots, issues, comments, projects, runtimes, runtime profiles, skills, users, workspaces, and shared pagination/error handling; no new top-level resource family or runtime dependency.
- Existing operation/canonical-vector fixtures plus unit, contract, component, type, compatibility, packaging, documentation, and CI coverage.
- Compatibility and migration documentation advances directly from `0.7.1` to `0.11.1`; no persistent data migration or automatic publication of extractor candidates is introduced.
