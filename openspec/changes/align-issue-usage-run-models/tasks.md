## 1. Approved contract and fixtures

- [x] 1.1 Record verified CLI 0.4.32 binary metadata separately from the pinned source target, default 0.4.28–0.4.32 bounds, and reviewed issue get/usage/runs response mappings in `contracts/sdk-contract.json`
- [x] 1.2 Add provenance-backed legacy/current JSON fixtures for assignee, usage, and task-run envelopes without live identifiers or secrets

## 2. Typed decoding

- [x] 2.1 Decode nested and scalar assignee projections through one adapter, preserving matching forms and raising `OutputShapeError` for partial or conflicting projections
- [x] 2.2 Extend `IssueUsage` with exact task/run, token-category, cost, and uncosted projections while documenting legacy total semantics
- [x] 2.3 Extend private task-run decoding and public `TaskRun` with reviewed runtime, worktree, result, and failure fields using immutable JSON values

## 3. Verification and documentation

- [x] 3.1 Add table-driven contract/unit coverage for legacy/current, omission/null, matching, conflicting, and silent-default regressions
- [x] 3.2 Add or update gated CLI 0.4.32 live smoke coverage for typed issue usage and run context
- [x] 3.3 Update API, migration, compatibility, and changelog documentation for the expanded models and supported CLI range

## 4. Gates

- [x] 4.1 Render/check the approved contract and validate the OpenSpec change strictly
- [x] 4.2 Run focused tests, Ruff, mypy for source and tests, and the complete offline pytest gate
- [x] 4.3 Attempt the gated live smoke and record a backend/network blocker separately if the authorized environment is unavailable

Live verification note: the gated smoke was attempted on 2026-08-27, but the
authorized live fixture was unavailable because `MULTICA_LIVE_CLI` and the
remaining `MULTICA_LIVE_*` environment were not configured. A direct CLI read
also timed out before this implementation, so no live acceptance is claimed.

PR-gate note: all lint, type, offline test/coverage, compatibility, contract,
and packaging stages passed. The mutation harness initially hit a `mutmut`
child-accounting `KeyError`; the CI repair excludes the unrelated execution
provider tests from mutation selection while retaining them in the complete
offline/coverage gate, and a clean 1443-mutant run now completes.
