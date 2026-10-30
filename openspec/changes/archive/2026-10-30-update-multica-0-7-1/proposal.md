## Why

Multica `0.7.1` changes retained CLI behavior beyond the SDK's reviewed `0.7.0` ceiling while keeping the 209-node command tree stable. The SDK needs one direct, evidence-backed `0.7.0` to `0.7.1` contract refresh so supported wakeup, agent, autopilot, issue, project-resource, skill, and task-run behavior remains typed, deterministic, and forward-compatible.

## What Changes

- Advance the approved upstream target to exact Multica `0.7.1` release `425269384` at commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`, retain exact `0.7.0` baseline commit `dbdbb299164347586e2650bb67684a490726a798`, preserve the existing `0.6.2` minimum, and move the exclusive compatibility ceiling to `0.7.2` with `0.7.1` as maximum tested.
- Reconcile all 209 target command nodes, every positional/local/inherited flag, the four changed help nodes, and all 196 supported response entrypoints against pinned old and target source with no pending verdict.
- Extend issue-wakeup conditions with open state `blocked` across create, update, get, list, and events while preserving dependency and mutual-exclusion validation.
- Align agent `custom_args` validation with provider-reserved values while preserving omission, empty-array, retained-argument, and standard error behavior.
- Preserve `AutopilotRun.task_id` nullability while representing create-issue settlement through successful task completion, blocked issue completion, and failure/retry chains.
- Add regressions for issue-search int4 overflow text, workflow-resolved assignee preservation, concurrent project-resource partial updates, portable and atomic skill bundles, and forward-compatible task process-cleanup outcomes.
- Regenerate only from `contracts/sdk-contract.json`, extend existing table-driven fixtures/tests and documentation, and run the repository's offline, typing, lint, contract, packaging, source-link, and release gates.
- Keep upstream-only Devin ACP, AppConfig, claim-only, workflow-prompt, Lark, UI, i18n, and analytics changes outside the public SDK surface.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: Pin the direct `0.7.0` to `0.7.1` provenance, complete CLI/response reconciliation, compatibility interval, reviewed mappings, and deterministic projection.
- `sdk-surface`: Adapt retained public agent, issue, project-resource, skill, and task-run contracts without adding operations for upstream-only internals.
- `issue-wakeup-resource`: Accept and round-trip the `blocked` issue condition with complete positive and negative validation.
- `autopilot-resource`: Preserve nullable run/task identity while specifying corrected create-issue task settlement and retry behavior.
- `verification-and-release`: Require table-driven regression coverage, independent exact-revision evidence, documentation, packaging, source-link, and release gates.

## Impact

- Approved contract and generated projection: `contracts/sdk-contract.json`, `src/multica_py/_generated/approved_sdk.py`, contract validation/render/check tooling, and exact source/test references.
- Existing public models and adapters for agents, issue wakeups, autopilot runs, issue search/update, project resources, skills, and task-run results; no new top-level SDK resource or dependency.
- Existing unit, contract, component, packaging, and CI fixtures; verification adds no task-specific live script or infrastructure, and generated evidence remains untracked and is published only in Multica.
- Compatibility, API, service-usage, migration, coverage, changelog, packaging, and release documentation.
