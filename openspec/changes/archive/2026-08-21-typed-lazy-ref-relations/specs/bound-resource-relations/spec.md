## MODIFIED Requirements

### Requirement: Bounded relation prefetch
`MulticaClient.prefetch(entities, selector, *, max_parallel=4) -> None` MUST
pre-load the lazy object returned by a typed selector for multiple bound
entities using `ThreadPoolExecutor`, deduplication, and explicit bounded
parallelism through the shared process semaphore. The selector MAY return a
`LazyCollection`, `OffsetLazyCollection`, `CursorLazyCollection`, `LazyMapping`,
or `LazyRef`. Collection and mapping behavior remains keyed by handle identity;
singular references additionally coalesce equal originating-scope, target-type,
and target-ID keys within that invocation and publish independent target
wrappers to each handle. One private helper MUST define singular coalescing
scope from the effective normalized executable, server URL, profile, workspace
ID, cwd, execution-ordered `tuple(config.environment)`, timeout, debug,
encoding, compatibility policy, minimum and maximum CLI versions, plus executor
and process-semaphore identities. Equal singular keys coalesce only when every
component matches; other full scopes produce distinct jobs. Display-only app
URL/workspace slug are excluded, and actual semaphore identity represents the
process limit. Environment order and duplicates MUST be preserved.
The v0.4.28 additions `Workspace.plugins`, `Workspace.properties`,
`Workspace.mcp_servers`, `Agent.mcp_servers`, and `Issue.properties` MUST retain
their established collection/mapping identity behavior under this extension.

#### Scenario: Prefetch does not fake server batching
- **WHEN** the CLI has no multi-parent or multi-ID filter
- **THEN** prefetch runs at most one loader/page chain per distinct uncached parent or singular target key and does not emit an invented batch command

#### Scenario: Duplicate singular targets are coalesced locally
- **WHEN** multiple selected `LazyRef` handles in one call address the same governed target key
- **THEN** one direct lookup runs and each handle receives an independent bound target wrapper with identical immutable public/private provenance, its own source client view, and fresh mutable relation state, without a persistent identity map

#### Scenario: Prefetch obeys max parallelism
- **WHEN** `prefetch(..., max_parallel=N)` loads multiple distinct keys
- **THEN** no more than `N` relation loaders and no more than the runtime process limit execute concurrently

#### Scenario: Prefetch validates before I/O
- **WHEN** `max_parallel < 1`, an entity originates from a different process-semaphore object, or the selector yields an unsupported lazy object
- **THEN** `ValueError` is raised before transport access

#### Scenario: Shared semaphore admits derived views
- **WHEN** root and derived client views have different workspace or other config but share the invoking client's process semaphore
- **THEN** the invocation is admitted; collection/mapping handles retain identity-only jobs, and equal singular targets with different full scopes run as separate bounded jobs

#### Scenario: Full singular scope controls only coalescing
- **WHEN** admitted singular references have equal target type and ID
- **THEN** fully equal execution/decode scopes coalesce, differing scopes (including reversed duplicate environment tuples) run separate lookups, and every destination retains its own client object

#### Scenario: Prefetch failure is fail-fast
- **WHEN** one loader fails
- **THEN** pending futures are cancelled, the earliest input failure is re-raised, and already completed successful loads remain cached

#### Scenario: v0.4.28 relation containers remain compatible
- **WHEN** prefetch selects any of the five plugin/property/MCP collection or mapping relations added for v0.4.28
- **THEN** it uses the existing handle-identity job, loading, and cache behavior and never enters singular target-ID coalescing

#### Scenario: Prefetch routes through relation command plans
- **WHEN** `prefetch` loads a selected relation
- **THEN** the load is performed through the relation's `all_command().run()` path and the same plan-derived argv reaches the transport as an eager `all()` would produce

#### Scenario: No prefetch command
- **WHEN** the public surface is inspected
- **THEN** no `prefetch_command()` method exists on `MulticaClient`

### Requirement: Unsupported inverse and singular relations stay explicit
The SDK MUST NOT expose a lazy collection when the pinned CLI lacks a
server-side list/filter or would require a hidden workspace scan/N+1. Singular
references MUST be exposed only through `LazyRef` rows in the
`singular-resource-references` normative inventory; every other singular ID or
snapshot MUST remain passive data.

#### Scenario: Unsupported collections are absent
- **WHEN** the public bound surface is inspected
- **THEN** it has no `Project.autopilots`, agent/squad autopilots, `Label.issues`, `Skill.agents`, `Runtime.agents`, `Repository.projects`, lazy attachment relation on `Issue`, or `Workspace.users` relation; passive `Issue.attachments` is only the embedded `issue get` tuple

#### Scenario: Supported singular references use LazyRef
- **WHEN** issue, autopilot, autopilot-run, or task-run reference members in the normative singular inventory are inspected
- **THEN** each is a passive `LazyRef` backed by its listed governed direct lookup and is not represented as a collection

#### Scenario: Unsupported singular references remain data
- **WHEN** a creator/member, trigger, task, leader, author, user, property-value, plugin-uploader, or MCP-record edge outside the nine-row singular inventory is inspected
- **THEN** its scalar ID or embedded snapshot remains available and no lazy relation performs a scan or invented lookup

#### Scenario: Singular references are deferred
- **WHEN** issue, autopilot, or run parent/project/assignee/creator references are inspected
- **THEN** they are not misrepresented as `ManyRelation` collections and only the nine-row inventory uses `LazyRef`
