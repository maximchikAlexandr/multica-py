## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Normative relation inventory
The implementation MUST provide exactly the following 33 relation contracts. Operation IDs and public signatures in this table are normative; unlisted relations are outside this change. Issue-list relations return bound `Issue` entities constructed from their governed list rows and originating client without additional `issues.get` calls.

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

#### Scenario: Inventory is exact
- **WHEN** public bound relation members are discovered
- **THEN** they correspond one-to-one with the 33 rows above and each row has approved operation and behavior coverage

#### Scenario: Issue rows are bound without extra gets
- **WHEN** any of rows R05, R13, R16, R17, or R19 loads N issues
- **THEN** the relation yields N bound `Issue` entities and performs only its governed list-page calls

#### Scenario: Workspace autopilots has one chosen strategy
- **WHEN** `Workspace.autopilots` loads
- **THEN** it performs exactly one `autopilots.list` page call and is not implemented as offset traversal or get aggregate

### Requirement: Workspace relation graph
A bound `Workspace` MUST expose `members`, `agents`, `skills`, `projects`, `issues`, `labels`, `autopilots`, `repositories`, `runtimes`, and `squads` using the workspace identifier as server-side scope and the original client runtime. `Workspace.issues` MUST yield bound `Issue` entities.

#### Scenario: Workspace unpaged relations use one scoped call
- **WHEN** `members`, `agents`, `skills`, `projects`, `labels`, `repositories`, `runtimes`, or `squads` is completely loaded
- **THEN** exactly one governed workspace-scoped list operation runs and typed entities are returned in response order

#### Scenario: Workspace issues traverse offset pages
- **WHEN** `workspace.issues` is completely loaded
- **THEN** governed `issues.list` requests preserve workspace scope, yield bound issues, and advance offsets until `has_more` is false without per-item gets

#### Scenario: Workspace autopilots preserve aggregate metadata
- **WHEN** `workspace.autopilots` loads the governed list response
- **THEN** its entities are available through the relation and upstream total metadata remains accessible

### Requirement: Agent skill squad and member graph
Bound `Agent`, `Skill`, `Squad`, and `WorkspaceMember` entities MUST expose the relations `Agent.skills`, `Agent.tasks`, `Agent.issues`, `Skill.files`, `Squad.members`, `Squad.issues`, and `WorkspaceMember.issues` through governed server-side operations. The three issue relations MUST yield bound `Issue` entities. `WorkspaceMember.issues` MUST use the membership `id` as the assignee filter while `user_id` remains available for user reconciliation.

#### Scenario: Agent and skill nested commands are plural
- **WHEN** `Agent.skills` or `Skill.files` loads
- **THEN** argv uses upstream `agent skills ...` or `skill files ...` command groups and returns typed children

#### Scenario: Agent tasks and squad members are unpaged
- **WHEN** `Agent.tasks` or `Squad.members` completely loads
- **THEN** one parent-addressed list operation runs and the result is cached

#### Scenario: Assignee issue relations are server filtered
- **WHEN** `Agent.issues`, `Squad.issues`, or `WorkspaceMember.issues` loads
- **THEN** every issue-list page uses `--assignee-id <parent-id>`, yields bound issues, uses `WorkspaceMember.id` for member scope, and performs no broad client-side scan or per-item get

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
