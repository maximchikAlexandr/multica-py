## ADDED Requirements

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

### Requirement: Normative relation inventory
The implementation MUST provide exactly the following 33 relation contracts.
Operation IDs and public signatures in this table are normative; unlisted
relations are outside this change.

| # | Public member | Operation ID | Request / strategy | Result and context | Invalidation |
|---:|---|---|---|---|---|
| relation:R01 (1) | `Workspace.members: LazyCollection[WorkspaceMember]` | `workspaces.members.list` | `workspace_id`; one call | bound members | none |
| relation:R02 (2) | `Workspace.agents: LazyCollection[Agent]` | `agents.list` | scoped workspace; one call | bound agents | explicit refresh |
| relation:R03 (3) | `Workspace.skills: LazyCollection[Skill]` | `skills.list` | scoped workspace; one call | bound skills | explicit refresh |
| relation:R04 (4) | `Workspace.projects: LazyCollection[Project]` | `projects.list` | scoped workspace; one call | bound projects | explicit refresh |
| relation:R05 (5) | `Workspace.issues: OffsetLazyCollection[Issue]` | `issues.list` | scoped workspace; default limit 50 | compact bound issues; page metadata | explicit refresh |
| relation:R06 (6) | `Workspace.labels: LazyCollection[Label]` | `labels.list` | scoped workspace; one call | bound labels | explicit refresh |
| relation:R07 (7) | `Workspace.autopilots: LazyCollection[Autopilot]` | `autopilots.list` | scoped workspace; exactly one list-page call | bound autopilots; `metadata.total` | explicit refresh |
| relation:R08 (8) | `Workspace.repositories: LazyCollection[RepositoryRecord]` | `repositories.list` | scoped workspace; one call | immutable URL/ref records | explicit refresh |
| relation:R09 (9) | `Workspace.runtimes: LazyCollection[RuntimeDefinition]` | `runtimes.list` | scoped workspace; one call | immutable runtime records | explicit refresh |
| relation:R10 (10) | `Workspace.squads: LazyCollection[Squad]` | `squads.list` | scoped workspace; one call | bound squads | explicit refresh |
| relation:R11 (11) | `Agent.skills: LazyCollection[AgentSkill]` | `agents.skills.list` | `agent_id`; one call | immutable assigned-skill records | `agents.skills.set` |
| relation:R12 (12) | `Agent.tasks: LazyCollection[AgentTask]` | `agents.tasks` | `agent_id`; one call | immutable task records | none |
| relation:R13 (13) | `Agent.issues: OffsetLazyCollection[Issue]` | `issues.list` | `assignee_id=agent.id`; limit 50 | compact bound issues | explicit refresh |
| relation:R14 (14) | `Skill.files: LazyCollection[SkillFile]` | `skills.files.list` | `skill_id`; one call | immutable file records | skill file create/update/delete |
| relation:R15 (15) | `Squad.members: LazyCollection[SquadMember]` | `squads.members.list` | `squad_id`; one call | immutable member records | squad member add/remove |
| relation:R16 (16) | `Squad.issues: OffsetLazyCollection[Issue]` | `issues.list` | `assignee_id=squad.id`; limit 50 | compact bound issues | explicit refresh |
| relation:R17 (17) | `WorkspaceMember.issues: OffsetLazyCollection[Issue]` | `issues.list` | `assignee_id=member.id`; limit 50 | compact bound issues | explicit refresh |
| relation:R18 (18) | `Project.resources: LazyCollection[ProjectResourceRecord]` | `projects.resources.list` | `project_id`; one call | immutable records | project resource add/update/remove |
| relation:R19 (19) | `Project.issues: OffsetLazyCollection[Issue]` | `issues.list` | `project_id=project.id`; limit 50 | compact bound issues | explicit refresh |
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

#### Scenario: Inventory is exact
- **WHEN** public bound relation members are discovered
- **THEN** they correspond one-to-one with the 33 rows above and each row has one approved operation and one behavior case

#### Scenario: Workspace autopilots has one chosen strategy
- **WHEN** `Workspace.autopilots` loads
- **THEN** it performs exactly one `autopilots.list` page call and is not implemented as offset traversal or get aggregate

### Requirement: Workspace relation graph
A bound `Workspace` MUST expose `members`, `agents`, `skills`, `projects`,
`issues`, `labels`, `autopilots`, `repositories`, `runtimes`, and `squads` using
the workspace identifier as server-side scope and the original client runtime.

#### Scenario: Workspace unpaged relations use one scoped call
- **WHEN** `members`, `agents`, `skills`, `projects`, `labels`, `repositories`, `runtimes`, or `squads` is completely loaded
- **THEN** exactly one governed workspace-scoped list operation runs and typed entities are returned in response order

#### Scenario: Workspace issues traverse offset pages
- **WHEN** `workspace.issues` is completely loaded
- **THEN** governed `issues.list` requests preserve the workspace scope and advance offsets until `has_more` is false

#### Scenario: Workspace autopilots preserve aggregate metadata
- **WHEN** `workspace.autopilots` loads the governed list response
- **THEN** its entities are available through the relation and upstream total metadata remains accessible

### Requirement: Agent skill squad and member graph
Bound `Agent`, `Skill`, `Squad`, and `WorkspaceMember` entities MUST expose the
relations `Agent.skills`, `Agent.tasks`, `Agent.issues`, `Skill.files`,
`Squad.members`, `Squad.issues`, and `WorkspaceMember.issues` through governed
server-side operations.

#### Scenario: Agent and skill nested commands are plural
- **WHEN** `Agent.skills` or `Skill.files` loads
- **THEN** argv uses upstream `agent skills ...` or `skill files ...` command groups and returns typed children

#### Scenario: Agent tasks and squad members are unpaged
- **WHEN** `Agent.tasks` or `Squad.members` completely loads
- **THEN** one parent-addressed list operation runs and the result is cached

#### Scenario: Assignee issue relations are server filtered
- **WHEN** `Agent.issues`, `Squad.issues`, or `WorkspaceMember.issues` loads
- **THEN** every issue-list page uses `--assignee-id <parent-id>` and no workspace-wide client filter

### Requirement: Project relation graph
A bound `Project` MUST expose unpaged `resources` and offset-paged `issues`
relations through governed operations.

#### Scenario: Project resources load once
- **WHEN** `Project.resources` first completely loads
- **THEN** `project resource list <project-id> --output json` runs exactly once and returns typed records

#### Scenario: Project issues are server filtered
- **WHEN** `Project.issues` loads
- **THEN** every issue-list page includes `--project <project-id>` and advances without a broad client-side scan

### Requirement: Issue activity relation graph
A bound `Issue` MUST expose `comments`, `recent_comment_threads`, `labels`,
`subscribers`, `metadata`, `pull_requests`, `children`, and `runs`; bound
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

### Requirement: Relation cache refresh and invalidation
Each bound entity MUST memoize one lazy object per relation and
normalized query parameters. The lazy object owns its state and lock; failed
loads remain retryable, refresh swaps only on success, and successful nested
mutations call `invalidate()` only on proven-stale memoized relations.
Automatic invalidation is local only when the successful mutation signature
contains the exact parent ID used by the memoized relation: rows 11, 14, 15,
18, parent-addressed comment add in 20–22, 23–25, and 31–32. Parentless comment
delete/resolve, workspace-wide and filtered relations, and top-level mutations
remain stale until explicit `refresh()`; no reverse index or global scan is
introduced.

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
- **WHEN** project resources, agent skills, skill files, squad members, issue labels/subscribers/metadata/comments, or autopilot triggers mutate successfully
- **THEN** only matching affected cache keys are invalidated

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
parallelism through the shared process semaphore.

#### Scenario: Prefetch does not fake server batching
- **WHEN** the CLI has no multi-parent filter
- **THEN** prefetch runs at most one loader/page chain per distinct uncached parent key and does not emit an invented multi-parent command

#### Scenario: Prefetch obeys max parallelism
- **WHEN** `prefetch(..., max_parallel=N)` loads multiple parents
- **THEN** no more than `N` relation loaders and no more than the runtime process limit execute concurrently

#### Scenario: Prefetch validates before I/O
- **WHEN** `max_parallel < 1`, entities have mixed origin scopes, or the selector yields inconsistent lazy-object types
- **THEN** `ValueError` is raised before transport access

#### Scenario: Prefetch failure is fail-fast
- **WHEN** one loader fails
- **THEN** pending futures are cancelled, the first loader exception is re-raised, and already completed successful loads remain cached

### Requirement: Relation lifecycle errors
Detached entities and missing inherited relation context MUST fail with typed
errors before subprocess invocation. Client views otherwise retain existing
independent transport lifecycle behavior.

#### Scenario: Detached entity fails predictably
- **WHEN** a relation on an explicitly detached entity is consumed
- **THEN** `DetachedEntityError` instructs the consumer to fetch through `MulticaClient` and transport call count stays zero


### Requirement: Unsupported inverse and singular relations stay explicit
The SDK MUST NOT expose a lazy collection when the pinned CLI lacks a
server-side list/filter, would require a hidden workspace scan/N+1, or the
relationship is singular and requires `LazyRef` semantics.

#### Scenario: Unsupported collections are absent
- **WHEN** the public bound surface is inspected
- **THEN** it has no `Project.autopilots`, agent/squad autopilots, `Label.issues`, `Skill.agents`, `Runtime.agents`, `Repository.projects`, `Issue.attachments`, or `Workspace.users` relation

#### Scenario: Singular references are deferred
- **WHEN** issue, autopilot, or run parent/project/assignee/creator references are inspected
- **THEN** this change does not misrepresent them as `ManyRelation` collections
