## Why

Collection and mapping relations retain their originating client and provide explicit, cached loading, but singular resource edges still force callers to keep a client and manually dispatch through scalar IDs. This leaves common traversals such as issue-to-project without the SDK's established lifecycle, context, retry, refresh, and bounded-prefetch guarantees.

## What Changes

- Add a typed `LazyRef[T]` container for passive singular handles with explicit `get()`, cached `value`, atomic `refresh()`, and `invalidate()` behavior.
- Add an evidence-backed singular-reference inventory and expose only references whose target has a governed direct get operation: issue parent/project and supported assignee kinds; autopilot project/assignee; autopilot-run autopilot/issue; and task-run issue/agent.
- Preserve scalar IDs and the existing `Issue.assignee` embedded snapshot; use `Issue.assignee_ref` for the new relation to avoid silently changing that field's meaning.
- Distinguish unloaded, loaded value, loaded optional absence, detached source, missing/omitted source context, and failed load states without adding a global cache or identity map.
- Extend the existing bounded `MulticaClient.prefetch()` workflow to singular handles and coalesce duplicate target IDs within one call while retaining per-wrapper caches.
- Keep creator/member, trigger, and task references without a governed direct lookup out of the lazy-reference surface.
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
- Dependencies and upstream behavior: no new dependency, raw argv path, asynchronous API, server operation, identity map, or persistent cache.
