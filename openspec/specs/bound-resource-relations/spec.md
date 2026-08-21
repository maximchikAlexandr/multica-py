# bound-resource-relations Specification

## Purpose
TBD - created by archiving change resource-relations-lazy-loading. Update Purpose after archive.

## Requirements

### Requirement: Bound entity data boundary
Participating resource operations MUST return typed entities that privately
retain their originating `MulticaClient` view, while scalar data remains available as an
immutable typed snapshot that excludes runtime context and relations.

#### Scenario: Resource result is bound
- **WHEN** a participating list, get, create, update, or aggregate operation returns an entity
- **THEN** its relations use the exact configuration and services of the originating client view and its shared process semaphore

#### Scenario: Passive entity operations perform no I/O
- **WHEN** a consumer reads scalar fields or uses `to_data()`, repr, equality, hashing, logging, or supported serialization
- **THEN** zero subprocess calls occur and runtime context is not serialized

#### Scenario: Autopilot run JSON snapshots remain immutable
- **WHEN** a consumer reads `AutopilotRun.trigger_payload` or `result`
- **THEN** JSON object nodes are immutable `Mapping[str, JsonValue]` values
  and arrays are immutable tuples; `to_dict()` / `to_json()` materialize
  standard JSON containers for compatible serialization

#### Scenario: Relation entry points expose command forms

- **WHEN** a CLI-loading relation entry point is inspected
- **THEN** `all_command()`, `refresh_command()`, and (where applicable)
  `page_command()` exist and return `Command[...]`, while `invalidate()`
  has no command variant

#### Scenario: Dunder loading routes through the command plan

- **WHEN** a consumer iterates a `LazyCollection`, calls `len()` on it,
  tests containment, or looks up a `LazyMapping` key
- **THEN** the load is performed through `all_command().run()` and the
  same plan-derived argv reaches the transport as the eager `all()`
  would produce

#### Scenario: Command construction performs no I/O

- **WHEN** `relation.all_command()`, `refresh_command()`, or
  `page_command()` is constructed
- **THEN** no `CliTransport` method is called and no subprocess is
  spawned

#### Scenario: Concurrent command runs coalesce

- **WHEN** multiple threads call `all_command().run()` on the same
  lazy object concurrently
- **THEN** one loader sequence runs and all waiters observe its result
  or error, matching the existing coalescing behavior

#### Scenario: Resource result is bound to the same executor
- **WHEN** a participating list, get, create, update, or aggregate operation returns an entity under a non-local executor
- **THEN** its relations use the exact configuration, the same executor, and the shared process semaphore of the originating client view
### Requirement: Relation load points are explicit
Reading a relation property or query view MUST perform no I/O. I/O MAY begin
only through iteration, length, containment, mapping lookup, `all()`, `page()`, `refresh()`, or explicit
`prefetch()`.

#### Scenario: Property access is lazy
- **WHEN** a consumer stores `relation = entity.relation`
- **THEN** transport call count remains zero and `relation.loaded` is false

#### Scenario: Complete load is cached
- **WHEN** iteration or `all()` completes successfully
- **THEN** the immutable complete result is cached and repeated complete access performs zero additional subprocess calls until invalidation

#### Scenario: Command construction is lazy

- **WHEN** a consumer stores `command = relation.all_command()`
- **THEN** transport call count remains zero and `relation.loaded` is
  unchanged
### Requirement: Normative relation inventory
The implementation MUST provide exactly the following 38 relation contracts. Operation IDs and public signatures in this table are normative; unlisted relations are outside this change. Issue-list relations return bound `Issue` entities constructed from their governed list rows and originating client without additional `issues.get` calls.

| # | Public member | Operation ID | Request / strategy | Result and context | Invalidation |
|---:|---|---|---|---|---|
| relation:R01 (1) | `Workspace.members: LazyCollection[WorkspaceMember]` | `workspaces.members.list` | `workspace_id`; one call | bound members | none |
| relation:R02 (2) | `Workspace.agents: LazyCollection[Agent]` | `agents.list` | scoped workspace; one call | bound agents | explicit refresh |
| relation:R03 (3) | `Workspace.skills: LazyCollection[Skill]` | `skills.list` | scoped workspace; one call | bound skills | explicit refresh |
| relation:R04 (4) | `Workspace.projects: LazyCollection[Project]` | `projects.list` | scoped workspace; one call | bound projects | explicit refresh |
| relation:R05 (5) | `Workspace.issues: OffsetLazyCollection[Issue]` | `issues.list` | scoped workspace; default limit 50 | bound partial issues; page metadata | explicit refresh |
| relation:R06 (6) | `Workspace.labels: LazyCollection[Label]` | `labels.list` | scoped workspace; one call | bound labels | explicit refresh |
| relation:R07 (7) | `Workspace.autopilots: LazyCollection[Autopilot]` | `autopilots.list` | scoped workspace; exactly one list-page call | bound autopilots; `metadata.total` | explicit refresh |
| relation:R08 (8) | `Workspace.repositories: LazyCollection[RepositoryRecord]` | `repositories.list` | scoped workspace; one call | immutable URL/ref records | explicit refresh |
| relation:R09 (9) | `Workspace.runtimes: LazyCollection[RuntimeDefinition]` | `runtimes.list` | scoped workspace; one call | immutable runtime records | explicit refresh |
| relation:R10 (10) | `Workspace.squads: LazyCollection[Squad]` | `squads.list` | scoped workspace; one call | bound squads | explicit refresh |
| relation:R11 (11) | `Agent.skills: LazyCollection[AgentSkill]` | `agents.skills.list` | `agent_id`; one call | immutable assigned-skill records | `agents.skills.set` |
| relation:R12 (12) | `Agent.tasks: LazyCollection[AgentTask]` | `agents.tasks` | `agent_id`; one call | immutable task records | none |
| relation:R13 (13) | `Agent.issues: OffsetLazyCollection[Issue]` | `issues.list` | `assignee_id=agent.id`; limit 50 | bound partial issues | explicit refresh |
| relation:R14 (14) | `Skill.files: LazyCollection[SkillFile]` | `skills.files.list` | `skill_id`; one call | immutable file records | skill file create/update/delete |
| relation:R15 (15) | `Squad.members: LazyCollection[SquadMember]` | `squads.members.list` | `squad_id`; one call | immutable member records | squad member add/remove |
| relation:R16 (16) | `Squad.issues: OffsetLazyCollection[Issue]` | `issues.list` | `assignee_id=squad.id`; limit 50 | bound partial issues | explicit refresh |
| relation:R17 (17) | `WorkspaceMember.issues: OffsetLazyCollection[Issue]` | `issues.list` | `assignee_id=member.id`; limit 50 | bound partial issues | explicit refresh |
| relation:R18 (18) | `Project.resources: LazyCollection[ProjectResourceRecord]` | `projects.resources.list` | `project_id`; one call | immutable records | project resource add/update/remove |
| relation:R19 (19) | `Project.issues: ProjectIssueCollection` | `issues.list` / `issues.create` | `project_id=project.id`; limit 50 | bound partial issues; scoped create | explicit refresh and successful scoped create |
| relation:R20 (20) | `Issue.comments: LazyCollection[Comment]` | `issues.comments.list` | flat mode, `issue_id`; one call | bound comments | add with issue ID; delete/resolve require refresh |
| relation:R21 (21) | `Issue.recent_comment_threads(limit: int = 10, *, cursor: CommentCursor | None = None) -> CursorLazyCollection[CommentThread]` | `issues.comments.list` | recent mode; fixed collection page limit; opaque atomic cursor | bound threads; next cursor | add with issue ID; delete/resolve require refresh |
| relation:R22 (22) | `CommentThread.comments: CursorLazyCollection[Comment]` | `issues.comments.list` | thread mode; inherited `issue_id`; default page limit 50; opaque atomic cursor | bound comments | parent-addressed add only; delete/resolve require refresh |
| relation:R23 (23) | `Issue.labels: LazyCollection[Label]` | `issues.labels.list` | `issue_id`; one call | bound labels | label add/remove |
| relation:R24 (24) | `Issue.subscribers: LazyCollection[Subscriber]` | `issues.subscribers.list` | `issue_id`; one call | immutable subscriber records | subscriber add/remove |
| relation:R25 (25) | `Issue.metadata: LazyMapping[str, MetadataValue]` | `issues.metadata.list` | `issue_id`; JSON object | immutable mapping | metadata set/delete |
| relation:R26 (26) | `Issue.pull_requests: LazyCollection[LinkedPullRequest]` | `issues.pull_requests` | `issue_id`; aggregate wrapper | immutable records | none |
| relation:R27 (27) | `Issue.children: LazyCollection[Issue]` | `issues.children` | `issue_id`; grouped aggregate | bound issues; `metadata.total/child_stages/unstaged` | explicit refresh |
| relation:R28 (28) | `Issue.runs: LazyCollection[TaskRun]` | `issues.runs` | `issue_id`; one call | bound runs with issue context | explicit refresh |
| relation:R29 (29) | `TaskRun.messages: LazyCollection[RunMessage]` | `issues.run_messages` | `task_run_id`, optional inherited `issue_id`; one call | immutable messages | none |
| relation:R30 (30) | `Autopilot.runs: OffsetLazyCollection[AutopilotRun]` | `autopilots.history` | `autopilot_id`; limit 20 | bound runs; `metadata.total` | explicit refresh |
| relation:R31 (31) | `Autopilot.triggers: LazyCollection[AutopilotTrigger]` | `autopilots.get` | get-envelope seed/read | immutable trigger records | trigger add/update/delete |
| relation:R32 (32) | `Autopilot.subscribers: LazyCollection[AutopilotSubscriber]` | `autopilots.get` | get-envelope seed/read | immutable subscriber records | autopilot subscriber update |
| relation:R33 (33) | `AutopilotRun.messages: LazyCollection[RunMessage]` | `issues.run_messages` | required `task_id`, optional `issue_id`; one call | immutable messages | none |
| relation:R34 (34) | `Workspace.plugins: LazyCollection[Plugin]` | `plugins.list` | scoped workspace via `with_workspace(self.id)`; one call; command argv has no required `--workspace` | immutable `Plugin` rows | explicit refresh and successful install |
| relation:R35 (35) | `Workspace.properties: LazyCollection[PropertyDefinition]` | `properties.list` | scoped workspace; one call | immutable property definitions | create/update/archive/unarchive |
| relation:R36 (36) | `Workspace.mcp_servers: LazyCollection[WorkspaceMcpServer]` | `workspaces.mcp.list` | scoped workspace via `with_workspace(self.id)`; one call; command argv is `workspace mcp list --output json` | public MCP identity rows without config secrets | add/update/remove |
| relation:R37 (37) | `Agent.mcp_servers: LazyCollection[AgentMcpBinding]` | `agents.mcp.list` | `agent_id`; one call | assigned MCP bindings | add/enable/disable/remove |
| relation:R38 (38) | `Issue.properties: LazyMapping[str, PropertyValue]` | `issues.properties.list` | `issue_id`; JSON object or reviewed list | mapping distinct from metadata | set/unset |

#### Scenario: Inventory is exact
- **WHEN** public bound relation members are discovered
- **THEN** they correspond one-to-one with the 38 rows above and each row has approved operation and behavior coverage

#### Scenario: Issue rows are bound without extra gets
- **WHEN** any of rows R05, R13, R16, R17, or R19 loads N issues
- **THEN** the relation yields N bound `Issue` entities and performs only its governed list-page calls

#### Scenario: Workspace autopilots has one chosen strategy
- **WHEN** `Workspace.autopilots` loads
- **THEN** it performs exactly one `autopilots.list` page call and is not implemented as offset traversal or get aggregate

#### Scenario: New v0.4.28 relations use one parent-addressed call
- **WHEN** `Workspace.plugins`, `Workspace.properties`, `Workspace.mcp_servers`, `Agent.mcp_servers`, or `Issue.properties` completely loads
- **THEN** exactly one governed list operation runs and the result is cached until the documented invalidation

### Requirement: Workspace relation graph
A bound `Workspace` MUST expose `members`, `agents`, `skills`, `projects`, `issues`, `labels`, `autopilots`, `repositories`, `runtimes`, `squads`, `plugins`, `properties`, and `mcp_servers` using the workspace identifier as server-side scope and the original client runtime. `Workspace.issues` MUST yield bound `Issue` entities.

#### Scenario: Workspace unpaged relations use one scoped call
- **WHEN** `members`, `agents`, `skills`, `projects`, `labels`, `repositories`, `runtimes`, `squads`, `plugins`, `properties`, or `mcp_servers` is completely loaded
- **THEN** exactly one governed workspace-scoped list operation runs and typed entities are returned in response order

#### Scenario: Workspace issues traverse offset pages
- **WHEN** `workspace.issues` is completely loaded
- **THEN** governed `issues.list` requests preserve workspace scope, yield bound issues, and advance offsets until `has_more` is false without per-item gets

#### Scenario: Workspace autopilots preserve aggregate metadata
- **WHEN** `workspace.autopilots` loads the governed list response
- **THEN** its entities are available through the relation and upstream total metadata remains accessible

### Requirement: Agent skill squad and member graph
Bound `Agent`, `Skill`, `Squad`, and `WorkspaceMember` entities MUST expose the relations `Agent.skills`, `Agent.tasks`, `Agent.issues`, `Agent.mcp_servers`, `Skill.files`, `Squad.members`, `Squad.issues`, and `WorkspaceMember.issues` through governed server-side operations. The three issue relations MUST yield bound `Issue` entities. `WorkspaceMember.issues` MUST use the membership `id` as the assignee filter while `user_id` remains available for user reconciliation.

#### Scenario: Agent and skill nested commands are plural
- **WHEN** `Agent.skills` or `Skill.files` loads
- **THEN** argv uses upstream `agent skills ...` or `skill files ...` command groups and returns typed children

#### Scenario: Agent tasks and squad members are unpaged
- **WHEN** `Agent.tasks` or `Squad.members` completely loads
- **THEN** one parent-addressed list operation runs and the result is cached

#### Scenario: Assignee issue relations are server filtered
- **WHEN** `Agent.issues`, `Squad.issues`, or `WorkspaceMember.issues` loads
- **THEN** every issue-list page uses `--assignee-id <parent-id>`, yields bound issues, uses `WorkspaceMember.id` for member scope, and performs no broad client-side scan or per-item get

#### Scenario: Agent MCP bindings load from agent mcp list
- **WHEN** `Agent.mcp_servers` completely loads
- **THEN** argv is `agent mcp list <agent-id> --output json` and enable/disable/remove invalidate the cache

### Requirement: Project relation graph
A bound `Project` MUST expose unpaged `resources` and a domain-specific offset-paged `issues` relation through governed operations. `Project.issues` MUST yield bound `Issue` entities and provide project-scoped issue creation.

#### Scenario: Project resources load once
- **WHEN** `Project.resources` first completely loads
- **THEN** `project resource list <project-id> --output json` runs exactly once and returns typed records

#### Scenario: Project issues are server filtered
- **WHEN** `Project.issues` loads
- **THEN** every issue-list page includes `--project <project-id>`, yields bound issues, and advances without a broad client-side scan or per-item get

#### Scenario: Project issues exposes scoped creation
- **WHEN** the project issue relation surface is inspected
- **THEN** read/page/refresh behavior remains compatible and `create`/`create_command` are available without a public `project_id` argument

### Requirement: Issue activity relation graph
A bound `Issue` MUST expose `comments`, `recent_comment_threads`, `labels`,
`subscribers`, `metadata`, `properties`, `pull_requests`, `children`, and `runs`; bound
`CommentThread` MUST expose `comments`; bound `TaskRun` MUST expose `messages`.

#### Scenario: Default comments are a flat relation
- **WHEN** `Issue.comments` completely loads
- **THEN** the governed flat comment-list mode returns typed comments and caches the complete default view

#### Scenario: Recent threads are parameterized
- **WHEN** a consumer requests recent comment threads with a limit and optional cursor pair
- **THEN** the query view passes the limit and complete `before`/`before_id` cursor semantics without pretending to be an unbounded property

#### Scenario: Thread comments inherit issue context
- **WHEN** `CommentThread.comments` loads
- **THEN** the loader uses both the thread identifier and inherited parent issue identifier required by the governed command

#### Scenario: Issue labels and subscribers are unpaged typed relations
- **WHEN** `Issue.labels` or `Issue.subscribers` loads
- **THEN** one governed nested list call returns typed entities rather than eager names or detached values

#### Scenario: Issue metadata is a mapping
- **WHEN** `Issue.metadata` loads from the upstream JSON object
- **THEN** it behaves as `LazyMapping[str, MetadataValue]` and preserves keys and typed values without converting them into artificial list entries

#### Scenario: Issue properties are a distinct mapping
- **WHEN** `Issue.properties` loads
- **THEN** it behaves as `LazyMapping[str, PropertyValue]` from `issue property list` and does not reuse metadata types or loaders

#### Scenario: Pull requests adapt their wrapper
- **WHEN** `Issue.pull_requests` loads
- **THEN** the adapter extracts the governed `pull_requests` envelope and returns typed linked pull requests

#### Scenario: Children expose full issues and grouping
- **WHEN** `Issue.children` loads the grouped upstream envelope
- **THEN** it returns full bound child issues while total, stage grouping, done counts, and unstaged grouping remain separately accessible

#### Scenario: Runs and messages preserve addressing
- **WHEN** `Issue.runs` then `TaskRun.messages` loads
- **THEN** messages use the task-run identifier plus inherited issue identifier where required, not the legacy positional issue plus `--run-id` form

### Requirement: Autopilot relation graph
A bound `Autopilot` MUST expose offset-paged `runs` and aggregate
`triggers`/`subscribers`; a bound `AutopilotRun` MUST expose `messages` when a
task identifier is available.

#### Scenario: Autopilot runs traverse pages
- **WHEN** `Autopilot.runs` completely loads
- **THEN** governed `autopilot runs <id>` requests advance limit/offset until complete and retain total metadata

#### Scenario: Autopilot get seeds aggregate relations
- **WHEN** governed autopilot get returns complete `autopilot`, `triggers`, and subscriber data
- **THEN** trigger and subscriber relations are seeded without a second read subprocess

#### Scenario: Trigger mutations use upstream commands
- **WHEN** an autopilot trigger is added, updated, or deleted
- **THEN** the governed `trigger-add`, `trigger-update`, or `trigger-delete` command runs and invalidates the matching trigger relation

#### Scenario: Autopilot run messages require task context
- **WHEN** `AutopilotRun.messages` loads with a non-null `task_id`
- **THEN** it reuses the governed task-run message operation and inherited issue ID when present

#### Scenario: Autopilot run without task cannot load messages
- **WHEN** an autopilot run has no `task_id`
- **THEN** message loading raises a typed relation-context error before transport access

### Requirement: Five relation loading strategies
The SDK MUST implement `Unpaged`, `OffsetPagination`, `CursorPagination`,
`AggregateEnvelope`, and `Mapping` with strategy-specific completion and
metadata behavior.

#### Scenario: Offset traversal detects no progress
- **WHEN** an offset page reports more data but is empty or repeats a requested offset
- **THEN** a typed pagination error is raised without an unbounded call sequence or partial complete-cache entry

#### Scenario: Cursor traversal preserves cursor pairs
- **WHEN** a cursor-paged relation returns its next cursor
- **THEN** the complete cursor state is passed to the next governed request and repeated cursors fail as no progress

#### Scenario: Aggregate metadata remains available
- **WHEN** an aggregate envelope is adapted into child entities
- **THEN** non-item metadata and grouping required by the public response contract are retained

### Requirement: Presence-aware cache seeding
Embedded relation data MUST seed cache only when the wire field is explicitly
present and the approved contract proves the embedded set is complete.
Only `autopilots.get.triggers → Autopilot.triggers` and
`autopilots.get.autopilot.subscribers → Autopilot.subscribers` are seedable;
all other embedded fields MUST NOT seed relations in this change.

#### Scenario: Missing field is not empty
- **WHEN** a compact response omits an embedded relation field
- **THEN** the relation remains unloaded rather than being seeded as an empty collection

#### Scenario: Explicit complete empty field seeds cache
- **WHEN** a governed full response explicitly provides an empty complete relation field
- **THEN** the relation is loaded as empty and subsequent access performs zero subprocess calls

### Requirement: Immutable wrapper replacement
Every resource response MUST create a new bound wrapper over a frozen snapshot.
The SDK MUST NOT maintain an identity map or enrich an existing wrapper.

#### Scenario: List then get returns replacement
- **WHEN** list returns a compact entity and get later returns fuller data for the same ID
- **THEN** get returns a distinct bound wrapper and the original list wrapper and snapshot remain unchanged

#### Scenario: Structural comparison uses snapshots
- **WHEN** callers need structural equality or serialization
- **THEN** they compare or encode `entity.to_data()` rather than relying on wrapper identity

#### Scenario: Structural comparison uses public fields
- **WHEN** callers need structural equality or serialization
- **THEN** they compare or encode `entity.to_dict()` / `entity.to_json()` (or
  use `entity.detach()`) rather than relying on instance identity, and
  `_client`/caches are excluded
### Requirement: Relation cache refresh and invalidation
Each bound entity MUST memoize one lazy object per relation and normalized query parameters. The lazy object owns its state and lock; failed loads remain retryable, refresh swaps only on success, and successful nested mutations call `invalidate()` only on proven-stale memoized relations. Automatic invalidation is local only when the successful mutation signature contains the exact parent ID used by the memoized relation: rows 11, 14, 15, 18, scoped create on row 19, parent-addressed comment add in 20–22, 23–25, and 31–32. Parentless comment delete/resolve, workspace-wide and filtered relations, and unrelated top-level mutations remain stale until explicit `refresh()`; no reverse index or global scan is introduced.

#### Scenario: Failed first load retries
- **WHEN** an initial relation load fails
- **THEN** no empty success is cached and a later load retries

#### Scenario: Failed refresh preserves prior success
- **WHEN** refresh fails after a successful cached load
- **THEN** the error is raised and the prior cached value remains available

#### Scenario: Concurrent first loads coalesce
- **WHEN** multiple threads load the same cache key concurrently
- **THEN** one loader sequence runs and all waiters observe its result or error

#### Scenario: Successful mutation targets invalidation
- **WHEN** project resources/issues, agent skills, skill files, squad members, issue labels/subscribers/metadata/comments, or autopilot triggers mutate successfully through their parent-bound surface
- **THEN** only matching affected cache keys are invalidated

#### Scenario: Cache-hit command is a no-op

- **WHEN** `all_command()` is constructed on an already-loaded relation
  and run
- **THEN** `command.commands == ()`, `command.run()` returns the cached
  value, and no `CliTransport` method is called

#### Scenario: Refresh command always carries a loader plan

- **WHEN** `refresh_command()` is constructed on a loaded or unloaded
  relation
- **THEN** `command.commands` contains the loader plan argv and
  `command.run()` performs the load with `force=True` semantics, updates
  the cache on success, and preserves the prior value on failure
### Requirement: Lazy state transitions
Every lazy object MUST use exactly `UNLOADED`, `LOADING`, and `LOADED` with one
`threading.Lock`. `loaded` MUST be true only for LOADED; page calls MUST not
change completeness; `all()`, blocking `refresh()`, and `invalidate()` MUST
hold the same lock for their full transition.

#### Scenario: First-load failure is shared and retryable
- **WHEN** concurrent callers wait on a failing UNLOADED→LOADING transition
- **THEN** all receive the same exception, state returns to UNLOADED, and the next caller retries

#### Scenario: Refresh is blocking and atomic
- **WHEN** refresh begins from LOADED
- **THEN** concurrent lazy-object operations wait for its lock, success replaces the value atomically, and failure retains the old LOADED value

#### Scenario: Invalidation waits for active transition
- **WHEN** invalidation races a load or refresh
- **THEN** it acquires the same lock after that transition and leaves the final state UNLOADED

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
### Requirement: Relation lifecycle errors
Detached entities and missing inherited relation context MUST fail with typed
errors before subprocess invocation. Client views otherwise retain existing
independent transport lifecycle behavior.

#### Scenario: Detached entity fails predictably
- **WHEN** a relation on an explicitly detached entity is consumed
- **THEN** `DetachedEntityError` instructs the consumer to fetch through `MulticaClient` and transport call count stays zero

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

### Requirement: Entity continuation actions use root command plans
Bound `Issue` and `Project` entities SHALL expose relevant refresh and mutation methods when their originating client is present. Each eager method SHALL delegate through an argument-identical `*_command()` method, bind fixed entity context without asking the caller to repeat the ID, and reuse the corresponding root resource plan, validation, `OperationOptions`, return type, and error behavior. Entities SHALL remain immutable: a successful refresh/mutation SHALL return a newly bound value rather than changing the original wrapper.

#### Scenario: Bound Issue refreshes through get
- **WHEN** `issue.refresh_command()` is inspected and run
- **THEN** it previews/runs the same governed `issues.get(issue.id)` plan and returns a newly bound `Issue`

#### Scenario: Bound Issue mutates without repeated ID
- **WHEN** `issue.update(...)`, `issue.assign(...)`, `issue.unassign()`, `issue.set_status(...)`, or a move method is used
- **THEN** the bound ID is forwarded once to the root command method and all remaining arguments/options match the resource form

#### Scenario: Bound Project continues naturally
- **WHEN** `project.refresh()` or `project.update(...)` is used
- **THEN** the root project resource plan is reused and the returned `Project` remains bound to the same client scope

#### Scenario: Detached continuation fails before I/O
- **WHEN** a detached Issue or Project invokes a continuation action
- **THEN** the existing typed detached-entity error is raised before command construction or transport

### Requirement: Project-scoped issue creation
`Project.issues` SHALL be a domain-specific `ProjectIssueCollection` retaining all `OffsetLazyCollection[Issue]` read/page/refresh behavior and adding `create(...) -> Issue` and `create_command(...) -> Command[Issue]`. These methods SHALL expose the same typed issue-create fields and operation options as root `client.issues.create`, except `project_id` SHALL be omitted and automatically fixed to `project.id`. No generic relation `bind(...)` API SHALL be introduced.

#### Scenario: Project issue create binds context
- **WHEN** `project.issues.create(title="Fix login")` runs
- **THEN** it executes the root issue-create plan with `project_id=project.id` and returns a bound `Issue`

#### Scenario: Scoped command is equivalent and inspectable
- **WHEN** `project.issues.create_command(title="Fix login")` and the equivalent root command are compared
- **THEN** their rendered/executed plans, result, validation, options, and errors are identical after accounting for the relation-supplied project ID

#### Scenario: Mutation target values are not silently rebound
- **WHEN** an issue obtained through `project.issues` is later updated or moved to another project
- **THEN** no relation wrapper automatically forces its project ID back to the original project

#### Scenario: Successful create invalidates a loaded relation
- **WHEN** `project.issues` is loaded and scoped creation succeeds
- **THEN** that relation becomes `UNLOADED` so its next read cannot return the stale pre-create snapshot

#### Scenario: Failed create preserves prior relation state
- **WHEN** scoped creation fails before or during execution
- **THEN** no invalidation occurs and any previously loaded snapshot remains available

### Requirement: Direct issue children results retain origin binding
`IssueResource.children` and `children_command` SHALL return an `IssueChildrenResult` whose `children`/`items` and `unstaged` tuples contain `Issue` entities bound to the originating `MulticaClient`. Binding SHALL be a pure result-finalization step over the already decoded collection payload; it SHALL preserve all page and child-stage metadata, issue snapshots, command inspection, and lazy relation behavior and SHALL issue no per-row or follow-up CLI calls.

#### Scenario: Child rows are immediately actionable
- **WHEN** `client.issues.children(parent_id)` returns one or more values in `children`
- **THEN** every child can immediately construct and run entity actions and lazy relation commands through the originating client without `client.issues.get(child.id)`

#### Scenario: Unstaged rows are immediately actionable
- **WHEN** a direct children result contains values in `unstaged`
- **THEN** every unstaged issue has the same originating-client binding as values in `children`

#### Scenario: Command execution binds both collections
- **WHEN** a caller inspects and runs `client.issues.children_command(parent_id)`
- **THEN** the inspected plan remains the single governed `issue children` command and its final result binds both issue tuples

#### Scenario: Binding preserves the complete result envelope
- **WHEN** the upstream result includes `total`, `child_stages`, `limit`, `offset`, `has_more`, or `next_cursor`
- **THEN** the bound `IssueChildrenResult` preserves those values exactly while replacing only each issue's client reference

#### Scenario: N child rows do not cause N plus one reads
- **WHEN** a result contains any number of children and unstaged issues
- **THEN** exactly one `issue children` transport call executes and zero implicit `issue get` calls execute

### Requirement: Collection and mapping relations share generation state ownership
`LazyCollection` and `LazyMapping` SHALL delegate `UNLOADED`/`LOADING`/`LOADED` transitions, generation ownership, waiter registration and outcomes, retry, failure restoration, refresh, and invalidation to one private generic state object in `models/relations.py`. Collection tuple/metadata normalization and immutable mapping normalization SHALL remain owned by their respective containers. The shared object SHALL NOT become a public cache API, pluggable backend, inheritance hierarchy, or general event framework.

#### Scenario: Concurrent first-load success is coalesced for both containers
- **WHEN** concurrent callers first load the same `LazyCollection` or `LazyMapping`
- **THEN** one loader generation runs and every waiter receives the same successful generation value

#### Scenario: Concurrent first-load failure is shared and retryable
- **WHEN** the active first-load generation raises
- **THEN** all registered waiters receive that generation's exception, state returns to `UNLOADED`, and a later caller starts a new generation

#### Scenario: Failed refresh restores container-specific prior state
- **WHEN** refresh fails after a collection with metadata or an immutable mapping has loaded
- **THEN** the prior value and collection metadata remain atomically available and the refresh error is raised

#### Scenario: Invalidation waits for either container transition
- **WHEN** invalidation races an active collection or mapping load/refresh
- **THEN** it completes after the active generation and leaves the relation `UNLOADED` with no partial result

### Requirement: Relation commands compose through the command module
Relation code SHALL construct cached/no-step commands, coalesced run wrappers, aliased results, result-field references, and sequential offset/cursor continuations only through private transformations exported by `_internal.commands`. Relation code SHALL NOT access `command._plan`, instantiate or copy `_CommandPlan`/`_Step`/`_StepRef`, or depend on their dataclass fields. Relation code SHALL retain ownership of offset/cursor semantics, page and item limits, progress guards, result aggregation, metadata, and cache installation.

#### Scenario: Cached relation command performs no I/O
- **WHEN** `all_command()` is built for an already loaded relation
- **THEN** the command module returns an inspectable no-step command whose `run()` returns the cached container value with zero transport calls

#### Scenario: Offset continuation is previewable before execution
- **WHEN** an unloaded offset relation builds `all_command()`
- **THEN** `.commands`, `repr`, and `str` expose the exact first request and a `${page.next_offset}` continuation template without running the loader or transport

#### Scenario: Cursor continuation is previewable before execution
- **WHEN** an unloaded cursor relation builds `all_command()`
- **THEN** `.commands`, `repr`, and `str` expose the exact first request and complete `${page.next_cursor.before}`/`${page.next_cursor.before_id}` template without I/O

#### Scenario: Runtime traversal retains relation-owned guards
- **WHEN** the composed sequential command encounters an empty page with more data, a repeated offset/cursor, or the page/item limit
- **THEN** the existing typed pagination error and bounded subprocess count are preserved and no partial complete-cache entry is installed

#### Scenario: Command diagnostics remain safe
- **WHEN** cached, coalesced, offset, or cursor relation commands are previewed
- **THEN** command rendering uses the command snapshot and existing redaction rules and exposes no secret-bearing internal state

### Requirement: Lazy/entity follow-up operations preserve the execution scope
Bound entity mutation methods, lazy-relation loaders, `*_command()` siblings,
and follow-up operations SHALL preserve the originating `CommandExecutor`.
A bound entity returned by a client configured with a non-local executor
SHALL execute all of its follow-up operations and lazy relations through
that same executor and SHALL NOT fall back to local execution. Prefetch
SHALL continue to share the same executor and the same concurrency scope.
Closing a scoped client view SHALL NOT close a shared user-supplied executor.

#### Scenario: Bound entity follow-up uses the same executor
- **WHEN** an `Issue` returned by a client configured with an `SshExecutor` calls `issue.update(...)` or `issue.comments.all()`
- **THEN** the follow-up operation executes through the same SSH executor and does not fall back to local

#### Scenario: Lazy relations preserve the executor
- **WHEN** `workspace.agents.all()` loads on a workspace bound to a client using a `MicrosandboxExecutor`
- **THEN** the `agents.list` command executes inside that same Microsandbox VM

#### Scenario: Prefetch shares the executor
- **WHEN** relation prefetch runs on entities bound to a non-local executor
- **THEN** every relation load executes through that same executor and the shared concurrency scope
