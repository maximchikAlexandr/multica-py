## Why

The typed SDK silently loses fields that Multica CLI 0.4.32 already returns for issue assignees, usage, and task runs. Consumers therefore receive false `None`/`0` defaults or must bypass the typed API, while the SDK does not declare a default compatibility range that explains the mismatch.

## What Changes

- Decode both nested and scalar issue-assignee projections and reject conflicting projections with `OutputShapeError`.
- Align `IssueUsage` with the reviewed CLI usage envelope, preserving task/run counts, input/output/cache token categories, cost, and uncosted projections without inventing an ambiguous total.
- Extend public `TaskRun` values with reviewed worktree, runtime, and result context needed to locate the active run directory.
- Record verified CLI 0.4.32 binary metadata separately from the pinned 0.4.28 source target, and enforce a reviewed default compatibility range covering 0.4.28 through 0.4.32.
- Add provenance-backed legacy/current fixtures, contract and live regressions, migration/API documentation, and full offline verification.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `sdk-surface`: Preserve reviewed issue assignee, usage, and task-run fields through the typed public API and fail closed on contradictory projections.
- `bound-resource-relations`: Make `Issue.runs` return task runs with sufficient typed worktree/runtime context while retaining binding and relation behavior.
- `upstream-contract`: Record the pinned source target, verified 0.4.32 binary, reviewed response-envelope mappings, and 0.4.28–0.4.32 compatibility decisions without falsely equating binary and source provenance.
- `verification-and-release`: Verify legacy/current envelopes, absence of silent defaulting, compatibility bounds, and live CLI 0.4.32 behavior.

## Impact

This affects issue/task-run public models, private wire models and decoders, the approved SDK contract and generated compatibility projection, issue fixtures/tests, live smoke coverage, and migration/API documentation. Existing supported legacy payloads remain decodable; contradictory or malformed known projections become explicit typed output errors.
