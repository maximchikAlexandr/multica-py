## Why

Async Python applications currently have to move every blocking SDK call into their own worker thread, duplicating wrappers and making concurrent Multica workflows awkward. The SDK should provide one first-class async execution style while preserving the existing commands, domain objects, validation, and errors.

## What Changes

- Add `Command.run_async()` to execute the same immutable command plan without blocking the caller's event loop.
- Add `<method>_async(...)` counterparts for every public I/O-bound resource method and bound entity action, with signatures and results equivalent to their synchronous forms; add explicit `list_messages()` / `list_messages_async()` actions where the backward-compatible `.messages` relation occupies the natural method name.
- Add async loading and refresh entry points for command-backed and loader-only lazy collections and mappings; keep local inspection, serialization, invalidation, and permalink helpers synchronous.
- Add async client prefetch with the synchronous `None` return contract, per-call `max_parallel` bound, shared process bound, and deterministic failure selection.
- Add async managed-process poll, wait, result, terminate, kill, and close operations over one thread-safe lifecycle state shared with synchronous callers, without holding its mutex across blocking provider I/O or cleanup.
- Preserve the existing synchronous API and `Command` abstraction unchanged apart from the additive async entry point.
- Derive async coverage from the merged v0.4.28 public/command inventory while leaving its 194-method synchronous canonical table, 321 cases, approved upstream contract, and generated descriptors unchanged.
- Document primary workflows in both execution styles and verify async concurrency, error parity, command parity, and backwards compatibility offline.

## Capabilities

### New Capabilities

- `async-api-parity`: Defines the async naming, execution, concurrency, cancellation boundary, and sync/async equivalence contract.

### Modified Capabilities

- `sdk-surface`: Extends public I/O-bound resources with async counterparts while retaining existing synchronous methods and public model types.
- `bound-resource-relations`: Extends bound entity actions and lazy relation loading with async counterparts.
- `subprocess-transport`: Allows an existing immutable command plan to run asynchronously without introducing a second command or transport contract.
- `verification-and-release`: Adds closed-inventory and offline behavioral gates for complete async coverage, concurrency, typing, docs, and compatibility.

## Impact

The additive API affects `Command`, all I/O-bearing resource classes in the merged v0.4.28 tree (including Plugin, Property, MCP, issue-property, and new Skill operations), bound entities and relations R01–R38, lazy relation types, managed-process lifecycle, public documentation, typing checks, and a separate derived async coverage inventory. It reuses the standard library and current executor backends; no runtime dependency, separate async client, duplicate request/result model, approved upstream operation, or breaking synchronous change is introduced. The compatibility interval remains `[0.4.28, 0.4.29)`.
