## Why

Two existing public contracts are implemented unsafely. An `Issue` decoded from the ordinary list/get UUID-to-value property projection can expose raw values through the typed `Issue.properties` relation, while local execution can block before timeout handling when stdin and output exceed pipe capacity.

## What Changes

- Keep the ordinary UUID-keyed issue property projection as raw issue data, but do not treat it as an already-loaded `LazyMapping[str, PropertyValue]`.
- Make `Issue.properties` load the authoritative name-keyed `PropertyValue` rows through `issues.properties.list`, including for issues returned by ordinary `issues.list` and `issues.get`.
- Make synchronous local execution service stdin, stdout, and stderr concurrently under the existing timeout and cancellation lifecycle.
- Make `LocalExecutor.spawn` return without synchronously writing a supplied stdin payload, while preserving the payload and both output streams for subsequent handle collection.
- Add public regression coverage for raw property projections and real-process coverage with data larger than OS pipe capacity, including timeout behavior.
- Preserve existing public APIs, raw issue projection compatibility, process cleanup semantics, and dependency set.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `property-resource`: Clarify that a raw UUID-keyed issue projection is not a loaded typed relation and that accessing `Issue.properties` loads authoritative name-keyed `PropertyValue` rows.
- `subprocess-transport`: Require concurrent stdin/output servicing for bounded local execution and non-blocking initial stdin delivery for spawned processes.

## Impact

- Affected implementation: `src/multica_py/entities/issues.py`, `src/multica_py/_internal/processes.py`, and `src/multica_py/execution/local.py`; closely related internal helpers may change if needed to preserve lifecycle ownership.
- Affected tests: issue resource/relation unit tests, local process lifecycle tests, component process-contract fixtures and cases.
- Public behavior becomes consistent with the existing typed relation and managed-process contracts; no breaking API, migration, new dependency, or CLI contract change is intended.
- Source finding: approved audit [MYL-422], items A1/P1 and P2. P3 remains out of scope.
