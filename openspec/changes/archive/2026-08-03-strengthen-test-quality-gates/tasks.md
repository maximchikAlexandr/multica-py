## 1. Coverage gate

- [x] 1.1 Add typed statement and branch aggregation to `scripts/check_coverage.py` with negative tests for missing and below-threshold critical zones.
- [x] 1.2 Configure dedicated process, managed-process, issues, and runtimes zones with measured statement and branch thresholds.

## 2. Process lifecycle coverage

- [x] 2.1 Add deterministic unit cases for cancellation, termination escalation, pipe cleanup, and managed-process finalization without adding real-process case IDs.
- [x] 2.2 Verify the three approved real-process case IDs remain exact and green.

## 3. Public operation contracts

- [x] 3.1 Add a table-driven component contract that invokes representative top-level and nested canonical operations through `MulticaClient`.
- [x] 3.2 Replace `argv_check="none"` with declared dynamic argv positions and full normalized comparisons for avatar and attachment byte operations.

## 4. Verification

- [x] 4.1 Run focused tests, Ruff, `mypy src`, and `mypy tests scripts`.
- [x] 4.2 Run parallel and serial offline coverage, the zonal coverage checker, packaging tests, and confirm live tests are excluded.
- [x] 4.3 Run strict OpenSpec validation and inspect the final diff for production-code or unrelated changes.
