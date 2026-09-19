## Why

The approved SDK contract and generated compatibility ceiling stop at Multica
`0.4.44`, while stable `0.5.0` adds five public CLI nodes and changes label,
task-run, agent-validation, runtime-delete, and skill-list contracts. A direct,
source-pinned `0.4.44` to `0.5.0` update is required so the SDK can expose the
reviewed additions without treating collector evidence as public API approval.

## What Changes

- Promote the approved target to Multica `0.5.0`, tag commit
  `2df765a3c8f39789c9fb76316378bcffc20d22d9`, and a reviewed compatibility
  interval `[0.4.42,0.5.1)` with operation-level `0.5.0` gates for new surface.
- Add `issues.comments.update(comment_id, body, expected_revision=...)` while
  keeping the SDK content API text-only, requiring a positive revision, and
  preserving optimistic-conflict, unchanged-attachment, and mention-retrigger
  semantics.
- Add `skills.labels.list/add/remove` and expose `Skill.labels` consistently as
  `LazyCollection[Label]`; skill-list responses preload it while skill detail
  keeps its established wire contract and leaves the relation unloaded.
- Extend label creation/list/update with reviewed `issue|skill` resource types
  and description semantics; update uses the existing unset sentinel so an
  empty description explicitly clears it.
- Adapt task-run issue-state deltas, open failure reasons including
  `runtime_access_denied`, OMP model/thinking validation, and structured
  runtime-delete conflicts without unsafe retry or cascade.
- Reconcile all 189 baseline and 194 target public CLI nodes and all 163
  supported response entrypoints; preserve exact-equality evidence for the 157
  unchanged responses and targeted fixtures for the six changed responses.
- Update the human-reviewed contract first, render deterministically only from
  that contract, extend existing frozen table-driven fixtures, document the
  direct migration, and require strict offline, typing, lint, source-link,
  packaging, and clean-tree gates. Review evidence and transient renders stay
  untracked.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `upstream-contract`: Pin exact `0.5.0` authority, compatibility bounds,
  complete command/response reconciliation, reviewed input/presence mappings,
  and non-SDK dispositions.
- `sdk-surface`: Add comment update and skill-label APIs and adapt label,
  skill-list, task-run, agent-validation, and runtime-conflict models.
- `bound-resource-relations`: Add the typed `Skill.labels` collection and
  invalidate it after supported skill-label mutations.
- `subprocess-transport`: Preserve optimistic update failures and structured or
  legacy runtime-delete conflicts through the centralized error boundary.
- `verification-and-release`: Require provenance, 194-node and 163-entrypoint
  audits, deterministic generation, table-driven matrices, offline quality,
  packaging, and clean-tree evidence.

## Impact

Implementation will update `contracts/sdk-contract.json`, generated runtime
metadata, comment/skill/label/agent/task/runtime resources and wire adapters,
bound skill relations, existing operation/response fixture tables, public API
and migration documentation, compatibility claims, and package assertions. It
adds no dependency and does not change production code, the approved contract,
tests, docs, or main specs until a human explicitly approves implementation.
