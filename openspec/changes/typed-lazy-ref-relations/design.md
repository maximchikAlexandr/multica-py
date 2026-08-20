## Context

The bound-resource work established immutable entities, private originating-client context, per-wrapper lazy caches, a shared `_GenerationState`, typed command plans, and bounded `MulticaClient.prefetch()`. Singular edges were deliberately deferred because their state and presence semantics differ from collections. Today `Issue.parent_id`/`project_id`, `Autopilot.project_id`/assignee fields, and run IDs require callers to carry the correct client and manually choose a service.

The current code already supplies the important primitives:

- `_BoundEntity` separates public snapshot fields from private runtime state and provides detached-entity errors.
- `models/relations.py` coalesces concurrent generations and restores the previous value after failed refresh.
- typed resource `get_command()` methods exist for issues, projects, agents, squads, and autopilots.
- `MulticaClient.prefetch()` uses a thread pool plus the shared `ProcessSemaphore`.

No governed direct get exists for workspace memberships, users by arbitrary ID, task runs, autopilot triggers, or comment authors. Those edges cannot be safely promoted merely because a payload contains an ID.

## Goals / Non-Goals

**Goals:**

- Provide one typed singular handle with passive access and explicit I/O.
- Preserve originating profile, workspace, server, executor, and process-semaphore context.
- Make omitted, explicit null, unloaded, loaded, failed, detached, and unsupported-discriminator cases testably different.
- Reuse the existing state machine and prefetch entry point.
- Define an exact, operation-backed inventory and a closed embedded-seed policy.
- Preserve immutable source and target snapshots.

**Non-Goals:**

- A descriptor/registry framework shared by every relation.
- Global identity, cross-call caching, TTLs, async APIs, or server changes.
- Invented `get_many` methods or workspace-wide scans.
- Creator/member, task, trigger, leader, author, or user relations without governed direct lookup support.
- Retargeting an old immutable source wrapper after a mutation.

## Decisions

### 1. Add one small `LazyRef[T]` beside existing relation containers

`LazyRef` lives in `models/relations.py` and is imported from that dedicated module, consistent with the deliberately small package root. Its public surface is:

- `loaded: bool`
- `value: T` (raises `UnloadedReferenceError` while unloaded)
- `get() -> T`
- `get_command() -> Command[T]`
- `refresh() -> T`
- `refresh_command() -> Command[T]`
- `invalidate() -> None`

`get()` is chosen over `load()`/`resolve()` because every accepted edge delegates to a typed resource `get`, and it is the shortest spelling already used in the issue examples. `.value` remains useful for post-prefetch reads; raising while unloaded prevents it from conflating that state with an optional `None`. No iterator, truthiness, descriptor, or separate optional container is added.

`get_command()` mirrors relation command inspection: when cached it returns a no-step cached command; otherwise it wraps the governed typed service command and installs the result only after successful execution. `refresh_command()` constructs the governed request whenever the handle has a target ID. Explicit optional absence has no target ID, so `refresh()` and `refresh_command()` use the same no-step cached-`None` path as `get()` and perform no I/O.

Alternative considered: only `get()` and `loaded`. Rejected because it would leave no passive post-prefetch read and no inspectable command equivalent to the rest of the SDK.

### 2. Reuse `_GenerationState` with an explicit initial-presence sentinel

`LazyRef` normalizes values, while `_GenerationState[T]` continues to own locking, generation numbers, waiter outcomes, retry, refresh restoration, and invalidation. Its constructor must distinguish “no initial value” from an initial `None`; use the repository's existing explicit sentinel pattern rather than `None` as the initialization signal.

This yields:

| State/input | `loaded` | `value` | `get()` |
|---|---:|---|---|
| non-null ID, not loaded | false | raises `UnloadedReferenceError` | governed lookup |
| explicit optional null | true | `None` | cached `None`, no I/O |
| omitted required context | false | raises `UnloadedReferenceError` | raises `MissingRelationContextError` pre-I/O |
| detached source with loadable ID | false | raises `UnloadedReferenceError` | raises `DetachedEntityError` pre-I/O |
| failed first load | false | raises `UnloadedReferenceError` | retries next time |
| failed refresh after loaded target | true | prior target | later get returns prior cache |

Target `NotFoundError` is a retryable load failure, not optional absence. Only source payload presence can establish legitimate absence; a temporarily missing remote target must not be cached forever as `None`.

Alternative considered: a public state enum. Rejected because `loaded` plus typed exceptions and nullable `value` fully distinguish the required observable states without another API.

### 3. Keep the inventory exact and dispatch assignees by proven discriminator

The nine public members in the specification are the complete first release. Each property builds a handle without I/O and its private loader calls the existing typed service:

- issue → parent issue, project, agent/squad assignee;
- autopilot → project, agent/squad assignee;
- autopilot run → owning autopilot, created issue;
- task run → owning issue, executing agent.

`Issue.assignee` remains the existing `IssueAssignee` snapshot. The handle is named `assignee_ref` to avoid a breaking semantic replacement. For `agent` and `squad`, the loader dispatches to `client.agents.get_command()` or `client.squads.get_command()`. `member` and unknown strings raise `UnsupportedReferenceTargetError` with no scan. The same fail-closed rule applies to `Autopilot.assignee`.

Creator references are excluded even when a particular payload happens to say `agent`: the field is open-string data and the capability should not present a partially reliable creator relation until the upstream contract proves all supported kinds and direct lookups. Task/trigger IDs are excluded because no direct target service exists.

Alternative considered: expose every scalar ID and fail for most values. Rejected because property existence would overstate supported graph coverage.

### 4. Preserve wire presence privately; do not broaden public snapshots

Optional reference-bearing wire fields used by the inventory change from a defaulted `None` decoder to `str | None | msgspec.UnsetType` (and equivalent treatment for embedded assignee). Conversion records a private presence bit/seed on the bound entity while preserving the current public scalar or snapshot value (`None` when omitted or null).

Reference construction follows three rules:

1. non-null ID is an unloaded loadable reference;
2. explicit null is a loaded optional absence;
3. omitted ID/discriminator is an unloaded handle whose loader raises `MissingRelationContextError`.

The private presence seed is immutable provenance excluded by `_EntityPolicy` from `to_dict()`, `to_json()`, repr, equality, and hashing. `detach()` must therefore stop using a lossy `from_dict(to_dict())` reconstruction for this provenance: it copies public fields plus immutable presence seeds, clears the originating client, and creates fresh mutable runtime/relation state. Serialization remains intentionally public-only, so `from_dict(to_dict(entity))` cannot distinguish an original omitted field from explicit null; either public `None` is reconstructed conservatively as missing context. Direct/manual construction follows that same rule. A manually constructed entity with a non-null scalar can load normally once bound; a defaulted or explicitly supplied `None` without a decoder seed is missing context, not proven absence.

No embedded entity snapshot currently qualifies as complete. `IssueAssignee` remains display/snapshot data and never seeds an `Agent` or `Squad`; explicit null may seed absence because it does not assert target completeness.

Alternative considered: infer absence from public `None`. Rejected because current partial responses collapse omitted fields to `None`, which would incorrectly mark missing context as loaded absence.

### 5. Source properties remain passive even when detached or invalid

Every property can construct its `LazyRef` from snapshot data without requiring a client. The loader/command-loader closure performs validation in this order before transport:

1. missing source ID or discriminator → `MissingRelationContextError`;
2. unsupported discriminator → `UnsupportedReferenceTargetError`;
3. missing originating client → `DetachedEntityError`;
4. otherwise construct/run the governed typed resource command.

An explicit-null optional handle needs no client and remains loaded with `None`, including on a detached snapshot. Its refresh path is also a cached no-op because there is no target ID from which to build a governed lookup. This preserves passive property access and gives errors only at explicit load points.

Alternative considered: raise on property access, as some older collection paths do. Rejected because it makes a supposedly passive handle impossible to inspect and conflicts with the required detached state model.

### 6. Refresh replaces handle state, not previously returned entities

`refresh()` forces a new typed get through the same `_GenerationState` only when the handle has a target ID. Readers of the same handle wait during the generation. Success atomically publishes the new immutable bound wrapper; failure restores the previous loaded target. Loaded optional absence cannot address a target, so eager and command refresh return cached `None` through a no-step command with zero I/O. `invalidate()` waits for an active generation and then removes the handle cache.

Source mutations keep the repository's immutable replacement rule. The complete Issue matrix is `update(parent_id=...)` → `parent`, `update(project_id=...)` → `project`, and `update(assignee_id=...)` / `assign(...)` / `unassign()` → `assignee_ref`. Every successful command returns a newly decoded Issue whose scalar/snapshot, wire-presence seed, and handles come from the response; clearing a reference therefore uses the response's explicit-null/omitted semantics rather than mutating local state. This also applies to a successful no-change response: equal old/new IDs do not justify transferring a loaded handle or cache, so the replacement receives fresh state derived only from its response. The original issue and every old handle remain a coherent historical snapshot. Retargeting or invalidating an old handle would make it disagree with the old public scalar/snapshot, so no mutation does that. A failed mutation publishes no replacement and changes no original handle.

Alternative considered: invalidate the old source handle after mutation. Rejected because its loader is necessarily keyed by the old immutable scalar and would reload the wrong edge.

### 7. Extend existing prefetch with an internal singular key and clone fan-out

Collections and mappings keep current identity deduplication. `LazyRef` contributes a private prefetch key only when it has a supported, non-null target:

`(origin scope, target entity type/service, target ID)`. One private helper builds origin scope from the effective normalized command/decode-affecting config snapshot: `(executable, server URL, profile, workspace ID, cwd, tuple(config.environment), timeout timedelta, debug, encoding, compatibility policy, min CLI version, max CLI version, executor identity, process-semaphore identity)`. It consumes `ClientConfig` after its existing path/URL/timeout normalization but uses the stored environment tuple verbatim in execution order: it never sorts or deduplicates it, so reversed duplicate-name tuples with different last-value-wins results remain different. It excludes display-only `app_url`/`workspace_slug`, and semaphore identity subsumes configured `max_processes` for the actual execution view.

Admission remains the current process-semaphore identity check across all selected entities. A different semaphore rejects the invocation before I/O; root and derived views sharing that semaphore remain valid even when their config differs. Collections and mappings keep identity-only deduplication. For `LazyRef`, the full scope is part of the job key rather than admission: distinct client objects with an equal complete scope may coalesce, while any scope-component difference—including cwd or environment order—creates a separate bounded job without `ValueError`. After a coalesced lookup succeeds, every destination handle receives an independent target cloned and rebound by one private `_BoundEntity` helper rather than a public cache/registry. The clone copies immutable public target data and immutable private provenance needed by nested references (wire-presence/operation seeds), binds `_client` to that destination handle's own source client object rather than the lookup owner's client, and allocates fresh mutable runtime state: relation-handle maps, `_GenerationState` objects, loaders, locks, and cached outcomes. All wrappers thus interpret nested omitted/null/value fields consistently while nested commands preserve their destination origin and no caches are shared. Loaded absence schedules no job. Unsupported or missing-context handles remain ordinary jobs whose explicit pre-I/O error participates in existing earliest-input/fail-fast behavior.

Distinct keys use the existing `ThreadPoolExecutor(max_workers=max_parallel)` and transport semaphore. There is no approved batch operation for the accepted targets, so no `get_many` API is added.

Alternative considered: share one returned target wrapper among duplicate handles. Rejected because its nested lazy caches would then be shared across different source wrappers, violating wrapper-local ownership.

### 8. Verification follows existing table-driven layers

Add one focused relation-state test module/table set rather than per-property test files. Reuse existing fake transport, bound-entity factories, generation-state concurrency patterns, operation case tables, public-symbol discovery, and mypy usage fixtures. Verification covers exact argv/service dispatch and zero-I/O conditions, not private implementation shape.

Docs add `LazyRef` to the dedicated relation import list, a migration/inventory table, service-usage examples, and one runnable `examples/singular_references.py`. No dependency or test framework is added.

## Risks / Trade-offs

- [Open upstream discriminator strings can expand] → Fail closed with `UnsupportedReferenceTargetError`; add a target only with contract evidence and tests.
- [Presence-aware wire changes can accidentally alter scalar decoding] → Keep public defaults unchanged and test omitted/null/value cases at decoder and entity levels.
- [Duplicate prefetch fan-out could lose provenance or leak shared nested caches] → Copy immutable public data and private presence/operation seeds, then allocate fresh mutable runtime/relation state for every published wrapper.
- [A source mutation may surprise callers holding the old wrapper] → Document immutable replacement explicitly; the returned wrapper is authoritative and the old snapshot remains internally coherent.
- [Adding command methods enlarges the surface] → Reuse existing command transformations and expose only the get/refresh equivalents needed for SDK-wide inspectability.

## Migration Plan

1. Add presence-aware private decoding and `LazyRef`/error primitives without changing current public fields.
2. Add the exact bound-entity properties and typed service command loaders.
3. Generalize prefetch and add duplicate-key clone fan-out.
4. Update docs/examples and run focused, offline, typing, lint, format, package, and OpenSpec validation gates.

The change is additive: existing scalar-ID and `Issue.assignee` consumers require no migration. Rollback removes the new properties/container and private presence state; no server or persisted data migration is involved.

## Open Questions

None. New target kinds, embedded target seeds, or true server batch operations require later evidence-backed deltas rather than speculative hooks in this change.
