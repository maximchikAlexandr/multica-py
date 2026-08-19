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
wrappers to each handle. One private helper MUST define originating scope from
the effective normalized executable, server URL, profile, workspace ID, cwd,
sorted environment, timeout, debug, encoding, compatibility policy, minimum
and maximum CLI versions, plus executor and process-semaphore identities; every
component MUST match. Display-only app URL/workspace slug are excluded, and the
actual semaphore identity represents the process limit.

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
- **WHEN** `max_parallel < 1`, entities have mixed origin scopes, or the selector yields an unsupported lazy object
- **THEN** `ValueError` is raised before transport access

#### Scenario: Client views define exact prefetch scope
- **WHEN** client views differ in executable, server, profile, workspace, cwd, environment, timeout, debug, encoding, compatibility/min/max policy, executor, or process semaphore
- **THEN** they are mixed origin scopes and validation raises before I/O; distinct client objects whose complete normalized scope components match may coalesce equal singular target keys while retaining each destination's client object

#### Scenario: Prefetch failure is fail-fast
- **WHEN** one loader fails
- **THEN** pending futures are cancelled, the earliest input failure is re-raised, and already completed successful loads remain cached

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
- **WHEN** a creator/member, trigger, task, leader, author, or user edge without a governed discriminator-safe direct lookup is inspected
- **THEN** its scalar ID or embedded snapshot remains available and no lazy relation performs a scan or invented lookup
