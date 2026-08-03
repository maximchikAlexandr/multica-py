## Why

The offline suite can remain green while critical process lifecycle branches and weakly covered resource modules regress, because current coverage thresholds aggregate broad zones. Canonical operation rows also bypass `MulticaClient`, and dynamic-path operations do not currently prove their complete argv.

## What Changes

- Add explicit statement and branch coverage gates for process lifecycle code and critical resource modules.
- Preserve the three approved real-process cases while adding deterministic unit coverage for uncovered timeout, cancellation, and managed-process branches.
- Add a compact table-driven component contract that resolves canonical public operations through `MulticaClient` instead of constructing resource classes directly.
- Normalize dynamic temporary paths and assert complete argv for avatar and attachment byte operations.
- Keep the public SDK API and production behavior unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `verification-and-release`: Require explicit critical-zone statement and branch coverage gates while preserving the existing offline, process-case, and exact-transport contracts.

## Impact

Affected areas are `pyproject.toml`, the coverage gate script, unit/component operation tests, and CI verification documentation. No runtime API, generated SDK contract, dependency, or production module changes are intended.
