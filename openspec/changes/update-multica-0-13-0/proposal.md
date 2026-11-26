## Why

The published SDK still approves Multica `0.7.1`, while stable Multica `0.13.0` changes retained commands and response contracts that SDK callers depend on. A direct, evidence-backed upgrade is required to preserve typed behavior without promoting every new upstream command into the public Python API.

## What Changes

- Advance the approved target directly from Multica `0.7.1` to stable `0.13.0`, release `457951728`, commit `35b54a3742bb51bdf5ffa688655367ec98044862`, while preserving the existing compatibility floor and setting an exclusive `0.13.1` ceiling.
- Reconcile all `277` target binary-help nodes plus the removed `issue rerun` node and all `196` supported response work items against exact old/target source references.
- Add typed issue blocker projections and mutations, including privacy-preserving hidden counts, manual/stage references, and local validation for self, cycle, cross-workspace, and maximum-count failures.
- **BREAKING** Remove the obsolete public `issue rerun` operation and document migration to `issue rerun-task`.
- Adapt task-run document attribution/kind and squad `handoff_mode`, preserving the reviewed `leader|direct` closed policy and legacy `leader` omission default while retaining open-value decoding only for reviewed blocker/document kinds.
- Preserve existing public surfaces for retained operations, explicitly defer unapproved command families including `squad briefs`, and keep delete side effects governed by the existing action-result boundary.
- Regenerate production artifacts only from `contracts/sdk-contract.json`; extend table-driven unit, contract, component, live verification, documentation, packaging, and release gates.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: Pin the direct `0.7.1` to `0.13.0` provenance, complete command/response dispositions, compatibility interval, and deterministic projection.
- `sdk-surface`: Add reviewed blocker, handoff, and task-run fields; remove legacy rerun; preserve field-specific omission, closed/open-value, privacy, and error behavior.
- `public-cli-parity`: Govern changed command mappings, the rerun replacement, deferred candidates, and exact transport vectors.
- `verification-and-release`: Require table-driven offline coverage, isolated live evidence for interaction-only behavior, documentation, packaging, CI, and exact-revision proof.

## Impact

- Contract/generation: `contracts/sdk-contract.json`, `src/multica_py/_generated/approved_sdk.py`, `scripts/upstream_contract.py`, and existing schema/generator checks.
- Runtime: issue, squad, agent-task/run models and private wires, resource adapters, exports, compatibility metadata, and typed errors.
- Verification: existing frozen operation/response cases, fake CLI fixtures, focused live script, CI jobs, source-link audit, package checks, and release documentation.
- No new runtime dependency, generator, transport, resource hierarchy, or public API for deferred upstream command families.
