## ADDED Requirements

### Requirement: LazyRef public contract
The SDK SHALL expose `LazyRef[T]` from `multica_py.models.relations` with passive `loaded` and `value` properties and explicit `get()`, `get_command()`, `refresh()`, `refresh_command()`, and `invalidate()` operations. Property access and command inspection SHALL perform no transport I/O. `value` SHALL return the cached value, including `None` for a loaded optional absence, and SHALL raise `UnloadedReferenceError` while unloaded.

#### Scenario: Reference property is passive
- **WHEN** a consumer stores a bound entity's reference property and inspects `loaded`
- **THEN** transport call count remains zero and an unseeded handle reports `loaded is False`

#### Scenario: Unloaded value is explicit
- **WHEN** a consumer reads `value` before a reference has loaded
- **THEN** `UnloadedReferenceError` is raised without transport access

#### Scenario: Loaded optional absence is observable
- **WHEN** an optional source reference is explicitly null
- **THEN** its handle reports `loaded is True`, `value is None`, and `get()` performs zero transport calls

#### Scenario: Command path matches eager path
- **WHEN** `get_command()` or `refresh_command()` is inspected and run
- **THEN** it uses the same governed typed-resource plan, result typing, cache transition, and error behavior as `get()` or `refresh()` respectively

#### Scenario: Loaded optional absence cannot be refreshed remotely
- **WHEN** `refresh()` is called or `refresh_command()` is inspected and run for a handle seeded from an explicitly null optional source field
- **THEN** it returns cached `None` through a no-step command, remains loaded, and performs zero transport calls because no target ID exists

### Requirement: Normative singular-reference inventory
The SDK SHALL expose exactly the reference members in the following table. Each loadable discriminator SHALL dispatch through the listed governed direct operation using the source wrapper's originating client view. Unlisted singular IDs and embedded snapshots SHALL NOT acquire a lazy-reference property.

| Public member | Type | Governed lookup | Supported source values |
|---|---|---|---|
| `Issue.parent` | `LazyRef[Issue | None]` | `issues.get` | `parent_id` string; explicit null is absent |
| `Issue.project` | `LazyRef[Project | None]` | `projects.get` | `project_id` string; explicit null is absent |
| `Issue.assignee_ref` | `LazyRef[Agent | Squad | None]` | `agents.get` / `squads.get` | embedded type `agent` or `squad`; explicit null is absent |
| `Autopilot.project` | `LazyRef[Project | None]` | `projects.get` | `project_id` string; explicit null is absent |
| `Autopilot.assignee` | `LazyRef[Agent | Squad]` | `agents.get` / `squads.get` | `assignee_type` equal to `agent` or `squad` |
| `AutopilotRun.autopilot` | `LazyRef[Autopilot]` | `autopilots.get` | required `autopilot_id` |
| `AutopilotRun.issue` | `LazyRef[Issue | None]` | `issues.get` | `issue_id` string; explicit null is absent |
| `TaskRun.issue` | `LazyRef[Issue]` | `issues.get` | inherited `issue_id` |
| `TaskRun.agent` | `LazyRef[Agent | None]` | `agents.get` | `agent_id` string; explicit null is absent |

#### Scenario: Inventory is exact
- **WHEN** public `LazyRef` members on bound entities are discovered
- **THEN** they correspond one-to-one with the nine table rows and every loadable variant has a governed lookup

#### Scenario: Discriminated assignee dispatch is governed
- **WHEN** an issue or autopilot assignee reference has type `agent` or `squad`
- **THEN** `get()` invokes exactly one `agents.get` or `squads.get` operation for its ID and returns the matching bound type

#### Scenario: Unsupported singular edges remain snapshots
- **WHEN** creator/member, autopilot trigger, task, squad leader, comment author, or workspace-user edges are inspected
- **THEN** no lazy-reference member exists because the pinned SDK has no discriminator-safe governed direct lookup for that edge

### Requirement: Scalar and snapshot compatibility
Existing scalar reference IDs SHALL remain passive public fields with their current meanings. Existing `Issue.assignee` SHALL remain the immutable embedded `IssueAssignee | None` snapshot, while `Issue.assignee_ref` SHALL be the separate lazy handle. Lazy handles, targets, loaders, locks, errors, and state SHALL NOT appear in `to_dict()`, `to_json()`, equality, hashing, or representation.

#### Scenario: Existing issue assignee meaning is preserved
- **WHEN** issue data contains an embedded assignee
- **THEN** `issue.assignee` returns the unchanged snapshot and `issue.assignee_ref` returns a distinct passive handle

#### Scenario: Snapshot operations remain passive
- **WHEN** a reference is unloaded and the source entity is represented, compared, hashed, or serialized
- **THEN** no load occurs and output includes only the source entity's established public data fields

### Requirement: Source presence is distinct from optional absence
Wire decoders SHALL retain private presence for every optional source ID or embedded discriminator used by the inventory. An explicitly present null SHALL seed a loaded absent optional reference; an omitted field SHALL remain unloaded and fail `get()` with `MissingRelationContextError`; a present non-null ID SHALL remain unloaded until explicitly loaded. Public scalar compatibility SHALL remain unchanged.

The immutable private presence seed SHALL survive `detach()` because detach removes operation context rather than wire provenance. `to_dict()` and `to_json()` SHALL continue to omit that seed; consequently `from_dict(to_dict(entity))` SHALL reconstruct from public data only and SHALL treat a public optional `None` as missing context, not as proof of explicit null. Direct/manual construction SHALL follow the same conservative rule: non-null public IDs are loadable when bound, while defaulted or explicitly supplied public `None` without decoder provenance is missing context.

#### Scenario: Omitted optional ID is not absent
- **WHEN** a partial issue payload omits `project_id`
- **THEN** `issue.project.loaded` is false and `issue.project.get()` raises `MissingRelationContextError` before transport access

#### Scenario: Explicit null ID is loaded absence
- **WHEN** a full issue payload explicitly contains `parent_issue_id: null`
- **THEN** `issue.parent` is loaded with `None` and no lookup is performed

#### Scenario: Present ID is initially unloaded
- **WHEN** an autopilot run contains a non-null `issue_id`
- **THEN** `run.issue.loaded` is false until `get()`, `refresh()`, or prefetch explicitly loads it

#### Scenario: Detach preserves wire presence without relation cache
- **WHEN** a decoded entity with an omitted, explicitly null, or non-null optional source field is detached
- **THEN** the detached wrapper preserves that field's missing/absent/loadable classification, discards its originating client and mutable relation handles, and any loadable detached reference raises `DetachedEntityError` before I/O

#### Scenario: Public serialization cannot assert explicit-null provenance
- **WHEN** an entity whose public optional source field is `None` is reconstructed by `from_dict(entity.to_dict())` or by direct construction without a decoder seed
- **THEN** its reference is unloaded and `get()` raises `MissingRelationContextError` before I/O, regardless of whether the original decoded wire field was omitted or explicit null

### Requirement: Unsupported discriminator fails before I/O
If a declared discriminated reference contains an unknown or unsupported target kind, its handle SHALL remain passive and SHALL raise `UnsupportedReferenceTargetError` when loading is requested. The error SHALL identify the source entity, reference name, discriminator, and value, and SHALL occur before transport access.

#### Scenario: Member assignee is not scanned
- **WHEN** `Issue.assignee_ref.get()` is called for an embedded assignee whose type is `member`
- **THEN** `UnsupportedReferenceTargetError` is raised and no workspace-member list or other transport call occurs

#### Scenario: Unknown autopilot assignee kind fails closed
- **WHEN** an autopilot has an unrecognized `assignee_type`
- **THEN** loading its assignee raises `UnsupportedReferenceTargetError` rather than guessing a resource service

### Requirement: Wrapper-local loading lifecycle
Each `LazyRef` SHALL own its source wrapper's state and reuse the existing private generation-state implementation for `UNLOADED`, `LOADING`, and `LOADED` transitions. Successful loads SHALL cache immutable values per handle; failed first loads, including target `NotFoundError`, SHALL return to unloaded and remain retryable; concurrent callers SHALL observe one coherent generation. No global identity map or persistent cross-wrapper cache SHALL be introduced.

#### Scenario: Successful first load is cached
- **WHEN** `get()` succeeds for an unloaded handle
- **THEN** one direct lookup runs, `loaded` becomes true, `value` is the returned bound target, and repeated `get()` performs no I/O

#### Scenario: Failed first load retries
- **WHEN** the first `get()` raises a transport, not-found, decode, or protocol error
- **THEN** the handle remains unloaded and a later `get()` starts a new governed lookup

#### Scenario: Concurrent first load is coalesced
- **WHEN** multiple callers load the same handle concurrently
- **THEN** one lookup generation runs and all callers observe that generation's same success or exception

#### Scenario: Equal source wrappers do not share caches
- **WHEN** two wrappers represent the same source ID and each accesses the same reference
- **THEN** each owns an independent handle and loading one outside a common prefetch invocation does not load the other

### Requirement: Refresh and invalidation are atomic
`refresh()` SHALL force a governed lookup when a target ID exists, even when loaded. A handle seeded as loaded optional absence has no target ID: its `refresh()` and `refresh_command()` SHALL return cached `None` without I/O. During load, refresh, or invalidation, operations on the same handle SHALL synchronize on its generation state. A successful live refresh SHALL atomically publish a replacement bound target; a failed live refresh SHALL retain the prior loaded target; invalidation SHALL wait for an active transition and leave the handle unloaded.

#### Scenario: Successful refresh replaces the target
- **WHEN** refresh succeeds for a loaded reference
- **THEN** the old target object remains immutable and the handle atomically publishes the newly bound target

#### Scenario: Failed refresh preserves prior value
- **WHEN** refresh fails after a reference loaded successfully
- **THEN** the exception is raised while `loaded` remains true and `value` remains the previous target

#### Scenario: Refresh of loaded absence is a cached operation
- **WHEN** `refresh()` or `refresh_command().run()` targets an explicitly null optional reference
- **THEN** it returns `None`, remains loaded with `None`, and creates no governed lookup or transport I/O

#### Scenario: Invalidation waits for transition
- **WHEN** `invalidate()` races a load or refresh
- **THEN** it completes after that generation and leaves the handle unloaded with no partial value

### Requirement: Immutable source mutation semantics
Reference-changing source mutations SHALL continue to return a new bound entity wrapper. The returned wrapper's reference handles SHALL be derived from the returned wire presence and IDs; the original wrapper, its scalar snapshot, and its handle caches SHALL remain unchanged. No source mutation SHALL retarget a handle whose source snapshot still contains the old ID.

For `Issue`, the normative reference-changing matrix is: `update(parent_id=...)` changes `parent`; `update(project_id=...)` changes `project`; `update(assignee_id=...)`, `assign(...)`, and `unassign()` change `assignee_ref`. Each successful operation SHALL derive all three handles from the complete returned wire snapshot, including omitted versus explicit-null presence. A failed operation SHALL publish no replacement and SHALL change no state on the original wrapper.

#### Scenario: Issue project change returns a coherent replacement
- **WHEN** `issue.update(project_id=...)` succeeds
- **THEN** the returned issue's `project_id` and `project` handle describe the new response while the original issue and its project handle retain their prior snapshot state

#### Scenario: Failed mutation changes no reference state
- **WHEN** a reference-changing mutation fails
- **THEN** the original wrapper and all of its handle states are unchanged

#### Scenario: Every Issue reference-changing operation returns a coherent replacement
- **WHEN** any row in the Issue mutation matrix succeeds with a changed or cleared reference
- **THEN** the returned Issue's scalar/snapshot field, private presence, and corresponding handle agree with the response, while the original Issue and all original handle caches remain unchanged

#### Scenario: Successful no-change mutation still creates independent state
- **WHEN** any of `update(parent_id=...)`, `update(project_id=...)`, `update(assignee_id=...)`, `assign(...)`, or `unassign()` succeeds and the response retains the same reference ID or absence as the source Issue
- **THEN** a new Issue wrapper and fresh unloaded-or-absence handle state are derived solely from that response, the original wrapper and cache remain unchanged, and no loaded target or relation cache is transferred to the replacement merely because the reference value is equal

### Requirement: Closed embedded seed catalog
No current embedded singular target snapshot SHALL seed a loaded entity value because none is contract-proven complete for its governed target type. An explicit null for an optional inventory row MAY seed loaded absence; omitted fields SHALL not seed; partial embedded assignee data SHALL remain available only through `Issue.assignee` and SHALL not seed `Issue.assignee_ref`.

#### Scenario: Partial assignee does not seed target
- **WHEN** issue get returns assignee ID, name, and type
- **THEN** the snapshot remains available but a supported `assignee_ref` stays unloaded until its typed resource lookup runs

#### Scenario: Field-name match does not seed
- **WHEN** a source payload embeds an object whose field name resembles a target resource
- **THEN** the reference remains unloaded unless a future delta adds that exact operation and field to the closed catalog

### Requirement: Bounded duplicate-aware prefetch
`MulticaClient.prefetch()` SHALL accept selectors returning `LazyRef` as well as collection and mapping containers. Within one invocation it SHALL skip loaded handles, deduplicate identical handles, coalesce unloaded references with the same exact originating scope, target service/type, and target ID into one lookup, and publish independent bound target wrappers to each source handle. One private scope-key helper SHALL derive the exact originating scope from the effective normalized `ClientConfig` values that affect command execution or decoding: executable, server URL, profile, workspace ID, cwd, sorted environment entries, timeout, debug, encoding, compatibility policy, minimum CLI version, and maximum CLI version; it SHALL also include executor identity and process-semaphore identity. Path-like values SHALL use their post-`os.fspath` strings, environment SHALL use its normalized sorted tuple, timeout SHALL use its normalized `timedelta`, and URLs/identifiers/policies SHALL use their validated config values. Display-only app URL and workspace slug SHALL NOT affect the key; `max_processes` SHALL be represented by the actual process-semaphore identity. Mixed originating-scope keys SHALL fail validation before any I/O. Distinct target keys SHALL use the existing `ThreadPoolExecutor`, `max_parallel`, shared process semaphore, validation, and fail-fast rules.

Fan-out SHALL copy the primary target's immutable public snapshot plus immutable private wire-presence/operation provenance required to construct its nested references. For each destination handle, including the primary, the published target SHALL be an independent clone bound to that destination handle's own source `_client`; structurally equal scope keys SHALL permit one lookup but SHALL NOT replace a destination client object with the lookup owner's client object. Each clone SHALL create fresh mutable runtime state, including every nested relation handle, `_GenerationState`, loader closure, lock, and cached success/failure, so no target wrapper or nested relation cache is shared.

#### Scenario: Duplicate target IDs load once
- **WHEN** several source wrappers in one prefetch invocation reference the same project ID
- **THEN** one `projects.get` call runs and every selected handle becomes loaded with its own bound project wrapper

#### Scenario: Fan-out preserves nested-reference semantics without shared state
- **WHEN** a coalesced lookup returns a target with omitted, explicit-null, or non-null nested reference fields
- **THEN** primary and secondary target wrappers expose the same nested-reference presence and originating-scope semantics, but loading or invalidating a nested reference on one wrapper does not change the other

#### Scenario: Structurally equal client views retain destination identity
- **WHEN** equal target keys originate from distinct client objects whose complete scope-key components are equal
- **THEN** one lookup runs, each destination receives an independent target whose `_client` is that destination handle's own source client, and every nested reference uses that same destination-specific client without shared mutable state

#### Scenario: Different target kinds do not collide
- **WHEN** equal ID strings refer to different governed resource types or originating scopes
- **THEN** prefetch treats them as distinct keys and does not share their result

#### Scenario: Exact scope controls coalescing
- **WHEN** selected references have the same target type and ID under identical normalized execution/decode config, executor identity, and semaphore identity
- **THEN** they coalesce into one lookup; if any component differs, mixed-scope validation raises `ValueError` before transport I/O

#### Scenario: Optional absence needs no job
- **WHEN** selected references are already loaded with `None`
- **THEN** prefetch performs no transport call for them

#### Scenario: Prefetch remains bounded
- **WHEN** multiple distinct reference keys are prefetched with `max_parallel=N`
- **THEN** no more than `N` lookup jobs and no more than the shared runtime process limit execute concurrently

### Requirement: Documentation and verification surface
The SDK SHALL document imports, passive versus explicit load points, optional absence, refresh, unsupported edges, and duplicate-aware bounded prefetch. A runnable example SHALL demonstrate optional issue references, refresh, and prefetch. Tests SHALL cover public typing, exact inventory and governed dispatch, omitted/null/present fields, detached and missing context, unsupported discriminators, caching, retry, refresh, concurrency, serialization passivity, and duplicate-key prefetch.

#### Scenario: Example has no implicit loading
- **WHEN** the singular-reference example is inspected or run with its documented setup
- **THEN** every possible transport call occurs only at `get()`, `refresh()`, command execution, or `prefetch()`

#### Scenario: Static public types are closed
- **WHEN** `mypy` checks source, tests, and usage examples
- **THEN** required and optional `LazyRef` values narrow without public `Any` or casts in normal consumer code
