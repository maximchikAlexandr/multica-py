## Why

Collection and mapping relations retain their originating client and provide explicit, cached loading, but singular resource edges still force callers to keep a client and manually dispatch through scalar IDs. This leaves common traversals such as issue-to-project without the SDK's established lifecycle, context, retry, refresh, and bounded-prefetch guarantees.

The reviewed baseline is the accepted Multica CLI compatibility interval `[0.4.28, 0.4.29)`. Its new plugin/property/MCP records and five new collection/mapping relations do not add a bound-entity singular edge to this change; the governed singular inventory below remains exact for that baseline.

## What Changes

- Add a typed `LazyRef[T]` container for passive singular handles with explicit `get()`, cached `value`, atomic `refresh()`, and `invalidate()` behavior.
- Add an evidence-backed singular-reference inventory and expose only references whose target has a governed direct get operation: issue parent/project and supported assignee kinds; autopilot project/assignee; autopilot-run autopilot/issue; and task-run issue/agent.
- Preserve scalar IDs and the existing `Issue.assignee` embedded snapshot; use `Issue.assignee_ref` for the new relation to avoid silently changing that field's meaning.
- Distinguish unloaded, loaded value, loaded optional absence, detached source, missing/omitted source context, and failed load states; preserve wire-presence provenance across detach and prefetch fan-out while keeping serialization/manual construction conservative, without adding a global cache or identity map.
- Extend the existing bounded `MulticaClient.prefetch()` workflow to singular handles while preserving shared-semaphore admission and collection/mapping identity behavior; singular duplicate target IDs coalesce only within one exact command-execution/decode scope, otherwise run as separate bounded jobs, and each independent target retains its destination handle's own originating client view.
- Keep creator/member, trigger, task, and v0.4.28 immutable-record IDs (property/plugin/MCP records) outside the bound-entity lazy-reference surface when they lack a supported bound source/target pair in this scope.
- Document the new API, compatibility boundary, and runnable optional-reference/refresh/prefetch workflow.

## Capabilities

### New Capabilities

- `singular-resource-references`: Defines the `LazyRef` API, exact supported-reference inventory, presence and seed policy, loading lifecycle, errors, invalidation, serialization, and bounded prefetch behavior.

### Modified Capabilities

- `bound-resource-relations`: Generalizes bounded prefetch from collection/mapping containers to singular lazy references and replaces the blanket deferral of singular relations with the governed inventory.

## Impact

- Public API: `multica_py.models.relations.LazyRef`, new bound-entity reference properties, and a typed error for reading an unloaded value; existing scalar IDs and snapshots remain available.
- Internals: relation generation state, source-presence decoding, typed resource command loaders, bound-entity private runtime fields, and prefetch job selection/deduplication.
- Verification: focused state/concurrency/presence/invalidation/prefetch tests, public-surface and type-check contracts, offline suite, static checks, docs, and an example.
- Dependencies and upstream behavior: targets the reviewed Multica CLI interval `[0.4.28, 0.4.29)` with no new dependency, raw argv path, asynchronous API, server operation, identity map, or persistent cache.
