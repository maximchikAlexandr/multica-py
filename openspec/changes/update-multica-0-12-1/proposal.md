## Why

The SDK is contractually capped at the verified Multica `0.7.1` surface while the latest stable release is `0.12.1`. A direct, evidence-backed upgrade is required so existing typed operations remain correct across the accumulated CLI and response changes without treating newly discovered upstream commands as automatically public SDK API.

## What Changes

- Advance the approved upstream target from exact Multica `0.7.1` to exact `0.12.1` release `455946845` at commit `fc8028d761707b506cec498385f31fcebbbff598`, preserving the current `0.6.2` compatibility floor and setting `0.12.1` as maximum tested.
- Reconcile the complete `209` to `276` CLI-node inventory (`68` added, `1` removed, `34` changed), all positional arguments and flags, and the eight reviewed source-only names with explicit support, adaptation, removal, deferral, or non-SDK-surface decisions.
- Reconcile all `196` supported response work items, including the `118` changed rows, against exact old and target source and encode required model, adapter, fixture, error, and documentation actions.
- Support public `issue rerun-task` as the replacement for removed `issue rerun`; remove the obsolete public rerun mapping under the documented direct-upgrade policy.
- Adapt existing operations for issue description revisions, project progress, skill revisions and conflicts, workspace guests, comment replay/idempotency, configuration limits, daemon log controls, and every other approved changed response while retaining forward-compatible open values and typed errors.
- Keep `chat wakeup`, Inbox, issue batch/status management, project member/overview/progress/workflow management, quick actions, Views, Workflows, and ungrouped `doc`/`environment` families deferred until separate public-API proposals approve them.
- Regenerate deterministically only from `contracts/sdk-contract.json`; extend existing frozen unit/contract/component/live tables and fixtures instead of adding another generator or test framework.
- Verify the narrow cross-component revision, replay, progress, and redaction risks on the isolated project stand, while keeping actual outputs, logs, images, hashes, and diagnostic evidence in Multica rather than Git.
- Update compatibility, API, migration, coverage, changelog, packaging, and release documentation for one direct `0.7.1` to `0.12.1` migration and atomic rollback.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: Pin exact `0.7.1`/`0.12.1` provenance, complete the 276-node and 196-response reconciliation, and retain the approved contract as the sole generator input.
- `public-cli-parity`: Replace the removed public rerun mapping with the reviewed `rerun-task` operation and record explicit dispositions for every added, removed, changed, hidden, and source-only command.
- `sdk-surface`: Adapt existing typed operations and models for the approved `0.12.1` request/response semantics without exposing deferred families.
- `subprocess-transport`: Preserve exact argv/body/presence mappings and typed 400/409/413/499 failure behavior for changed operations.
- `verification-and-release`: Require deterministic lower-level coverage, isolated live evidence for the remaining integration gaps, exact-SHA publication, documentation, packaging, and rollback gates.

## Impact

- Approved contract and generated projection: `contracts/sdk-contract.json`, `src/multica_py/_generated/approved_sdk.py`, and existing contract validation/render/check tooling.
- Existing issue, comment, project, skill, workspace/member, autopilot, configuration, daemon, runtime, agent, and related models/resources/adapters; one replacement issue operation and no new top-level resource family.
- Existing frozen operation/response tables, contract and fake-CLI component fixtures, targeted live tests, source-link audit, CI jobs, package checks, and user documentation.
- Review-only collector output, archives, binaries, response manifests, screenshots, logs, and transient renders remain untracked.
