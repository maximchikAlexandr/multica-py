## MODIFIED Requirements

### Requirement: Normative relation inventory
The implementation MUST provide exactly the following 33 relation contracts.
Operation IDs and public signatures in this table are normative; unlisted
relations are outside this change. Issue-list relations return immutable
summaries because their governed operation is `issues.list`; they MUST NOT
fabricate full bound issues from partial rows.

| # | Public member | Operation ID | Request / strategy | Result and context | Invalidation |
|---:|---|---|---|---|---|
| relation:R01 (1) | `Workspace.members: LazyCollection[WorkspaceMember]` | `workspaces.members.list` | `workspace_id`; one call | bound members | none |
| relation:R02 (2) | `Workspace.agents: LazyCollection[Agent]` | `agents.list` | scoped workspace; one call | bound agents | explicit refresh |
| relation:R03 (3) | `Workspace.skills: LazyCollection[Skill]` | `skills.list` | scoped workspace; one call | bound skills | explicit refresh |
| relation:R04 (4) | `Workspace.projects: LazyCollection[Project]` | `projects.list` | scoped workspace; one call | bound projects | explicit refresh |
| relation:R05 (5) | `Workspace.issues: OffsetLazyCollection[IssueSummary]` | `issues.list` | scoped workspace; default limit 50 | immutable summaries; page metadata | explicit refresh |
| relation:R06 (6) | `Workspace.labels: LazyCollection[Label]` | `labels.list` | scoped workspace; one call | bound labels | explicit refresh |
| relation:R07 (7) | `Workspace.autopilots: LazyCollection[Autopilot]` | `autopilots.list` | scoped workspace; exactly one list-page call | bound autopilots; `metadata.total` | explicit refresh |
| relation:R08 (8) | `Workspace.repositories: LazyCollection[RepositoryRecord]` | `repositories.list` | scoped workspace; one call | immutable URL/ref records | explicit refresh |
| relation:R09 (9) | `Workspace.runtimes: LazyCollection[RuntimeDefinition]` | `runtimes.list` | scoped workspace; one call | immutable runtime records | explicit refresh |
| relation:R10 (10) | `Workspace.squads: LazyCollection[Squad]` | `squads.list` | scoped workspace; one call | bound squads | explicit refresh |
| relation:R11 (11) | `Agent.skills: LazyCollection[AgentSkill]` | `agents.skills.list` | `agent_id`; one call | immutable assigned-skill records | `agents.skills.set` |
| relation:R12 (12) | `Agent.tasks: LazyCollection[AgentTask]` | `agents.tasks` | `agent_id`; one call | immutable task records | none |
| relation:R13 (13) | `Agent.issues: OffsetLazyCollection[IssueSummary]` | `issues.list` | `assignee_id=agent.id`; limit 50 | immutable summaries | explicit refresh |
| relation:R14 (14) | `Skill.files: LazyCollection[SkillFile]` | `skills.files.list` | `skill_id`; one call | immutable file records | skill file create/update/delete |
| relation:R15 (15) | `Squad.members: LazyCollection[SquadMember]` | `squads.members.list` | `squad_id`; one call | immutable member records | squad member add/remove |
| relation:R16 (16) | `Squad.issues: OffsetLazyCollection[IssueSummary]` | `issues.list` | `assignee_id=squad.id`; limit 50 | immutable summaries | explicit refresh |
| relation:R17 (17) | `WorkspaceMember.issues: OffsetLazyCollection[IssueSummary]` | `issues.list` | `assignee_id=member.id`; limit 50 | immutable summaries | explicit refresh |
| relation:R18 (18) | `Project.resources: LazyCollection[ProjectResourceRecord]` | `projects.resources.list` | `project_id`; one call | immutable records | project resource add/update/remove |
| relation:R19 (19) | `Project.issues: OffsetLazyCollection[IssueSummary]` | `issues.list` | `project_id=project.id`; limit 50 | immutable summaries | explicit refresh |
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
`Workspace.issues` MUST yield immutable `IssueSummary` values.

#### Scenario: Workspace unpaged relations use one scoped call
- **WHEN** `members`, `agents`, `skills`, `projects`, `labels`, `repositories`, `runtimes`, or `squads` is completely loaded
- **THEN** exactly one governed workspace-scoped list operation runs and typed entities are returned in response order

#### Scenario: Workspace issues traverse offset pages
- **WHEN** `workspace.issues` is completely loaded
- **THEN** governed `issues.list` requests preserve the workspace scope, yield summaries, and advance offsets until `has_more` is false

#### Scenario: Workspace autopilots preserve aggregate metadata
- **WHEN** `workspace.autopilots` loads the governed list response
- **THEN** its entities are available through the relation and upstream total metadata remains accessible

### Requirement: Agent skill squad and member graph
Bound `Agent`, `Skill`, `Squad`, and `WorkspaceMember` entities MUST expose the
relations `Agent.skills`, `Agent.tasks`, `Agent.issues`, `Skill.files`,
`Squad.members`, `Squad.issues`, and `WorkspaceMember.issues` through governed
server-side operations. The three issue relations MUST yield immutable
`IssueSummary` values. `WorkspaceMember.issues` MUST use the membership `id` as
the assignee filter while `user_id` remains available for user reconciliation.

#### Scenario: Agent and skill nested commands are plural
- **WHEN** `Agent.skills` or `Skill.files` loads
- **THEN** argv uses upstream `agent skills ...` or `skill files ...` command groups and returns typed children

#### Scenario: Agent tasks and squad members are unpaged
- **WHEN** `Agent.tasks` or `Squad.members` completely loads
- **THEN** one parent-addressed list operation runs and the result is cached

#### Scenario: Assignee issue relations are server filtered
- **WHEN** `Agent.issues`, `Squad.issues`, or `WorkspaceMember.issues` loads
- **THEN** every issue-list page uses `--assignee-id <parent-id>`, with `WorkspaceMember.id` as its parent ID, and no workspace-wide client filter

### Requirement: Project relation graph
A bound `Project` MUST expose unpaged `resources` and offset-paged `issues`
relations through governed operations. `Project.issues` MUST yield immutable
`IssueSummary` values.

#### Scenario: Project resources load once
- **WHEN** `Project.resources` first completely loads
- **THEN** `project resource list <project-id> --output json` runs exactly once and returns typed records

#### Scenario: Project issues are server filtered
- **WHEN** `Project.issues` loads
- **THEN** every issue-list page includes `--project <project-id>`, yields summaries, and advances without a broad client-side scan

### Requirement: Unsupported inverse and singular relations stay explicit
The SDK MUST NOT expose a lazy collection when the pinned CLI lacks a
server-side list/filter, would require a hidden workspace scan/N+1, or the
relationship is singular and requires `LazyRef` semantics. A passive immutable
snapshot embedded in an already-fetched entity is not a lazy relation.

#### Scenario: Unsupported collections are absent
- **WHEN** the public bound surface is inspected
- **THEN** it has no `Project.autopilots`, agent/squad autopilots, `Label.issues`, `Skill.agents`, `Runtime.agents`, `Repository.projects`, lazy attachment relation on `IssueEntity`, or `Workspace.users` relation; passive `IssueEntity.attachments` is only the embedded `issue get` tuple

#### Scenario: Singular references are deferred
- **WHEN** issue, autopilot, or run parent/project/assignee/creator references are inspected
- **THEN** this change does not misrepresent them as `ManyRelation` collections
