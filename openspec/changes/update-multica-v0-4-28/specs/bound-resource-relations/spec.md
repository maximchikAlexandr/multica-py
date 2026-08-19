## MODIFIED Requirements

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
