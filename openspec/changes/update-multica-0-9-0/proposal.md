## Why

Multica `0.9.0` is the latest stable release, while `multica-py` is approved and tested only through `0.7.1`. The SDK needs one direct, evidence-backed `0.7.1` to `0.9.0` contract refresh so retained public operations decode the new response shapes and preserve proven error, cancellation, compatibility, and migration behavior without automatically exposing every new CLI command.

## What Changes

- Advance the approved upstream target from exact Multica `0.7.1` commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0` to stable `0.9.0` release `444052572` at commit `8cd8a2db978d532d8627c78cd29f05deab6c6f17`, including verified archive and executable identities.
- Reconcile the complete command-tree change from 209 to 236 nodes: 28 additions, one removal, 18 changed nodes, and every source-only command name, while keeping unsupported, destructive, hidden, UI, and process-control candidates out of the public SDK.
- Reconcile all 196 baseline response entrypoints with source-pinned verdicts and adapt retained models for issue requester/creator fields, project visibility and creator fields, task credits/redaction, attachment dimensions, comment resolution, runtime capacity/usage, user profile, workspace pinning, and project-inherited subscribers.
- **BREAKING** Replace the removed public `issue rerun` mapping with the reviewed run-targeted `issue rerun-task` resume/fresh contract and document migration; do not preserve a command that no longer exists upstream.
- Preserve private-project 404/omission/redaction behavior, fail closed before create/update relationship mutation, decode cancellation as HTTP-like status 499 with no body, and surface non-zero runtime-update failure without false success.
- Update only the reviewed approved contract and deterministic generated projection, extend existing table-driven fixtures/tests and documentation, and apply the existing offline, typing, lint, source-link, packaging, release, and independent exact-revision evidence gates.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: Pin the direct `0.7.1` to `0.9.0` provenance, complete command/response reconciliation, reviewed dispositions, compatibility interval, and deterministic projection rules.
- `sdk-surface`: Adapt retained typed request/response models and migrate issue rerun behavior to the reviewed run-targeted command without exposing deferred candidates.
- `subprocess-transport`: Preserve no-body cancellation, process exit, literal argv/file handling, and local error semantics for changed retained operations.
- `bound-resource-relations`: Preserve authorization-safe lazy relationships, project-inherited subscriber provenance, and fail-closed create/update relationship binding.
- `verification-and-release`: Require table-driven present/omitted/null/malformed coverage, compatibility and migration documentation, repository gates, exact-SHA publication, and independent evidence.

## Impact

- Approved contract and generation: `contracts/sdk-contract.json`, `src/multica_py/_generated/approved_sdk.py`, validation/render/check tooling, source-link references, and compatibility metadata.
- Existing issue, comment, attachment, project, task/run, runtime, user, workspace, and subscriber models/resources, shared decoders and transport, operation tables, fake-CLI fixtures, and public exports/documentation.
- Existing unit, contract, component, packaging, CI, and protected live-smoke facilities; no new runtime dependency, public top-level resource family, generator, or test framework.
- Collector output, archives, binaries, raw review evidence, diagnostic JSON, images, and transient renders remain untracked and are not generator inputs.
