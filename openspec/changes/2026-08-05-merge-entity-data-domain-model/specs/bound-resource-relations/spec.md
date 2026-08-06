## MODIFIED Requirements

### Requirement: Bound entity data boundary

Participating resource operations MUST return typed unified domain entities
that privately retain their originating `MulticaClient` view, while scalar
fields remain available as immutable typed values on the same class and
exclude runtime context and relations. The unified class SHALL NOT expose a
separate `*Data` snapshot type; `to_json()` / `to_dict()` / `detach()` provide
the client-free serialized or detached view explicitly.

#### Scenario: Resource result is bound
- **WHEN** a participating list, get, create, update, or aggregate operation returns an entity
- **THEN** it returns the unified domain class (e.g. `Issue`, `Project`,
  `Agent`) and its relations use the exact configuration and services of the
  originating client view and its shared process semaphore

#### Scenario: Passive entity operations perform no I/O
- **WHEN** a consumer reads scalar fields or uses `to_json()`, `to_dict()`,
  `detach()`, repr, equality, hashing, logging, or supported serialization
- **THEN** zero subprocess calls occur and runtime context (`_client`, lazy
  caches, locks, loaders) is not serialized

#### Scenario: Autopilot run JSON snapshots remain immutable
- **WHEN** a consumer reads `AutopilotRun.trigger_payload` or `result`
- **THEN** JSON object nodes are immutable `Mapping[str, JsonValue]` values
  and arrays are immutable tuples; `to_dict()` / `to_json()` materialize
  standard JSON containers for compatible serialization

### Requirement: Immutable wrapper replacement

Every resource response MUST create a new unified domain instance over a
frozen public-field snapshot. The SDK MUST NOT maintain an identity map or
enrich an existing instance. Structural equality, repr, and serialization
MUST operate on public fields only and MUST exclude `_client` and lazy caches.

#### Scenario: List then get returns replacement
- **WHEN** list returns a compact summary and get later returns fuller data for the same ID
- **THEN** get returns a distinct unified instance and the original list
  summary remains unchanged

#### Scenario: Structural comparison uses public fields
- **WHEN** callers need structural equality or serialization
- **THEN** they compare or encode `entity.to_dict()` / `entity.to_json()` (or
  use `entity.detach()`) rather than relying on instance identity, and
  `_client`/caches are excluded

### Requirement: Normative relation inventory

The implementation MUST provide exactly the following 33 relation contracts.
Operation IDs and public signatures in this table are normative; unlisted
relations are outside this change. Issue-list relations return immutable
summaries because their governed operation is `issues.list`; they MUST NOT
fabricate full bound issues from partial rows. Entity types referenced in the
relation inventory are the unified domain classes (`Issue`, `Agent`,
`Autopilot`, `AutopilotRun`, `Skill`, `Squad`, `Workspace`,
`WorkspaceMember`, `Project`, `Comment`, `CommentThread`, `TaskRun`).

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
- **THEN** they correspond one-to-one with the 33 rows above, each row uses the
  unified domain class names, and each row has one approved operation and one
  behavior case

#### Scenario: Workspace autopilots has one chosen strategy
- **WHEN** `Workspace.autopilots` loads
- **THEN** it performs exactly one `autopilots.list` page call and is not implemented as offset traversal or get aggregate

### Requirement: Unsupported inverse and singular relations stay explicit

The SDK MUST NOT expose a lazy collection when the pinned CLI lacks a
server-side list/filter, would require a hidden workspace scan/N+1, or the
relationship is singular and requires `LazyRef` semantics. A passive immutable
snapshot embedded in an already-fetched unified entity is not a lazy relation.

#### Scenario: Unsupported collections are absent
- **WHEN** the public bound surface is inspected
- **THEN** it has no `Project.autopilots`, agent/squad autopilots, `Label.issues`, `Skill.agents`, `Runtime.agents`, `Repository.projects`, lazy attachment relation on `Issue`, or `Workspace.users` relation; passive `Issue.attachments` is only the embedded `issue get` tuple

#### Scenario: Singular references are deferred
- **WHEN** issue, autopilot, or run parent/project/assignee/creator references are inspected
- **THEN** this change does not misrepresent them as `ManyRelation` collections
