## Why

Bound domain entities currently share modules with CLI-backed resource services, so relation growth creates resource-to-resource import coupling and makes module ownership unclear. At the same time, `ManagedProcess` has no safe one-call completion API: callers must coordinate process waiting and two pipe iterators themselves, with no durable completed-output value.

## What Changes

- Add a dedicated `multica_py.entities` package and make it the canonical home of all 13 bound entity classes plus their private `_BoundEntity` base.
- Keep entity modules responsible for immutable fields, pure relation state, and entity-scoped domain actions; keep resources responsible for CLI command construction, transport execution, wire decoding, and service/collection operations. Pure relation-state adapters may live with entities or neutral relation/model infrastructure, while command-construction and wire-adaptation adapters remain private on the owning resource and are reached by attached entities through the client.
- Preserve the existing root imports and resource-module entity import identities while removing class definitions and avoidable entity-type dependency edges from `resources/*`.
- Add an immutable public `ProcessResult` containing `argv`, `exit_code`, `stdout`, `stderr`, `ok`, and `failed`.
- Add `ManagedProcess.result(timeout=...)` with simultaneous stdout/stderr capture, cached identity, deterministic cleanup, and retryable timeout semantics.
- Make `ManagedProcess.wait()` use buffered result collection so a successful wait does not discard completed output.
- Define buffered completion and direct streaming as mutually exclusive output-consumption modes, reported through a typed `ProcessOutputModeError` instead of silent data loss.
- Extend tests and documentation for package boundaries, import compatibility, buffered process completion, mode conflicts, timeout recovery, and resource accounting.
- Preserve the exact discovered public resource-method set; `tests/unit/resources/test_operations.py::test_discovered_public_methods` SHALL remain green with no method added or removed by this relocation/process change.

No existing supported public import, resource method, entity field, relation, domain action, or streaming entry point is removed.

## Capabilities

### New Capabilities

- `entity-package-boundaries`: Defines canonical entity ownership, resource/entity responsibility boundaries, dependency rules, and import compatibility for the new `multica_py.entities` package.

### Modified Capabilities

- `subprocess-transport`: Extends managed-process lifecycle requirements with structured buffered results, output-mode exclusivity, timeout recovery, and result-aware finalization.
- `sdk-surface`: Adds `ProcessResult` and `ProcessOutputModeError` to the deliberately small public root while preserving all existing root and resource-module entity imports.

## Impact

- Affected implementation areas: `src/multica_py/entities/` (new), every resource module that currently defines a `_BoundEntity` subclass, entity references in internal decoders/wire models, `src/multica_py/process.py`, `src/multica_py/exceptions.py`, and package exports.
- Affected verification areas: bound-public-surface and import-cycle contracts, entity relation/action tests, process lifecycle/component tests, typing, docs, and full offline quality gates.
- Runtime behavior remains synchronous and CLI-only. Buffered process completion intentionally stores stdout/stderr in memory; direct streaming remains available for unbounded/follow-style output.
- No new runtime dependency and no upstream CLI contract change are required.
