## Context

The suite has broad aggregate statement thresholds, but no branch thresholds and no dedicated gates for process lifecycle or individual critical resources. The canonical operation runner directly instantiates resources, while three dynamic-path operations opt out of exact argv comparison. The change is test- and verification-only; the three approved real-process cases and public SDK behavior remain fixed.

## Goals / Non-Goals

**Goals:**

- Make critical statement and branch regressions fail the existing coverage gate.
- Cover process lifecycle branches deterministically without adding real-process case IDs.
- Prove canonical public operation paths are reachable through `MulticaClient`.
- Compare complete argv even when one element is a temporary path.

**Non-Goals:**

- Changing runtime behavior, public signatures, generated contracts, or dependencies.
- Raising whole-project coverage to an arbitrary global percentage.
- Expanding the live suite or the three-case real-process contract.

## Decisions

### Keep scalar statement thresholds and add a parallel branch-threshold table

`scripts/check_coverage.py` will continue to accept the existing scalar `[tool.coverage.thresholds]` table and will read a new `[tool.coverage.branch_thresholds]` table. The same named regex zones aggregate covered and missing branches. This is smaller and more backward-compatible than replacing every threshold with a nested object.

Dedicated zones will cover `_internal/processes.py`, `process.py`, `resources/issues.py`, and `resources/runtimes.py`; broad existing zones remain as regression guards. Initial thresholds will be set at or below the improved measured baseline so that the gate prevents regression without manufacturing low-value tests.

### Preserve exactly three real-process cases

Uncovered cancellation, escalation, pipe, and managed-process lifecycle branches will be exercised with autospecced subprocess/semaphore test doubles. Existing process-contract cases remain the authority for operating-system integration. This avoids slow or timing-dependent additions to the serial suite.

### Add routing proof instead of duplicating every operation assertion

The existing canonical table remains the exhaustive exact-transport authority. A compact parametrized component contract will resolve representative top-level and nested canonical paths from `MulticaClient`, invoke them through the public client, and assert the expected transport. Public discovery continues to prove set completeness, while the component rows prove client wiring.

### Normalize only declared dynamic argv positions

`OperationCase` will declare dynamic argv positions rather than disabling comparison. The runner will replace those actual positions with the case placeholders and then compare the entire tuple. Operation-specific callbacks remain responsible for file content and cleanup assertions.

## Risks / Trade-offs

- **Coverage thresholds can encourage assertion-free execution** → New tests must assert lifecycle outcomes, exception types, and interactions rather than merely execute lines.
- **Mocked process tests cannot prove OS cleanup** → Keep `timeout-tree-cleanup` as the real-process authority and use mocks only for narrow branches.
- **A second routing table can drift** → Keep it representative and derive expected methods/argv from existing `OperationCase` objects where practical.
- **Dynamic normalization can hide the wrong value** → Normalize only the explicitly declared index and retain semantic path/filename assertions in callbacks.

## Migration Plan

Land the delta spec, test infrastructure, focused tests, and thresholds together. Verify focused tests first, then the parallel plus serial coverage workflow and OpenSpec validation. Rollback is a single test/config change because there is no persisted or runtime migration.

## Open Questions

None.
