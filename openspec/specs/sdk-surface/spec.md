## Purpose

Define the public synchronous SDK surface, its type guarantees, and its
distribution boundary.
## Requirements
### Requirement: Synchronous resource client
The SDK MUST expose one synchronous `MulticaClient` with stateless domain resources and immutable typed models.
#### Scenario: Resource calls remain stateless
- **WHEN** a consumer calls a resource method
- **THEN** no model performs hidden I/O or Active Record persistence.
<!-- Source IDs: 001:FR-001,FR-002,FR-003,FR-004,FR-005 -->

### Requirement: Public resource surface
The SDK MUST retain every public resource method present in the canonical operation table.
#### Scenario: Public methods have canonical rows
- **WHEN** a public resource method exists
- **THEN** one canonical operation row covers it.
<!-- Source IDs: 001:FR-018–FR-031,005:FR-019–FR-025 -->
<!-- Modified by attachment-bytes: `attachments.upload_bytes` and
     `attachments.download_bytes` are added as canonical public methods with
     `manual:attachments.upload_bytes:canonical` and
     `manual:attachments.download_bytes:canonical` rows; the discovered
     canonical method set grows from 117 to 119. The byte methods are
     ungoverned convenience wrappers (no contract operation), mirroring
     `autopilots.get_run` and `issues.search`. -->

### Requirement: Closed public types
The SDK MUST use immutable `msgspec` models and closed public enums or primitive unions without public `Any`.
#### Scenario: Structured output stays closed and typed
- **WHEN** structured output is decoded
- **THEN** it is a typed model or documented closed primitive.
<!-- Source IDs: 001:FR-033–FR-039 -->
<!-- Modified by issue-list-pagination: `IssueListPage` is a frozen `msgspec.Struct`
     with typed `issues: tuple[IssueSummary, ...]` and closed-scalar pagination
     fields; no public `Any`. -->

### Requirement: Distribution boundary
The distribution MUST remain `multica-py`, import as `multica_py`, include `py.typed`, and import without a CLI.
#### Scenario: Clean installation imports without a CLI
- **WHEN** installed cleanly
- **THEN** `import multica_py` succeeds before a CLI invocation.
<!-- Source IDs: 001:FR-006A–FR-006D,FR-047–FR-050B -->

### Requirement: Executor fields and squad member decoding
The SDK SHALL decode upstream executor fields and squad members. `AgentData`
SHALL expose `skill_refs: tuple[AgentSkill, ...]`, not eager `skills`;
`Agent.skills` SHALL be `LazyCollection[AgentSkill]` backed by governed plural
`agent skills list`. `AgentData.archived_at`, `SquadData.leader_id`, and
`SquadData.archived_at` remain optional typed fields. `Squad.members` SHALL be
`LazyCollection[SquadMember]` backed by `squad member list`.

#### Scenario: Agent skills decode as typed AgentSkill objects
- **WHEN** agent get/list contains assigned skill objects
- **THEN** `AgentData.skill_refs` preserves typed `AgentSkill` values and `Agent.skills` remains the lazy relation name

#### Scenario: Agent with no skills decodes to empty tuple
- **WHEN** agent get/list omits embedded skills
- **THEN** `AgentData.skill_refs == ()` and no relation cache is seeded

#### Scenario: Agent archived_at null decodes to None
- **WHEN** `archived_at` is null or omitted
- **THEN** `AgentData.archived_at` is `None`

#### Scenario: Agent archived_at RFC3339 decodes to datetime
- **WHEN** `archived_at` is a valid RFC3339 value
- **THEN** `AgentData.archived_at` is the corresponding timezone-aware `datetime`

#### Scenario: Assigned skills read returns typed AgentSkill
- **WHEN** `Agent.skills.all()` loads
- **THEN** `agent skills list <agent-id> --output json` returns `tuple[AgentSkill, ...]`

#### Scenario: Squad leader_id decodes
- **WHEN** a squad response contains `leader_id`
- **THEN** `SquadData.leader_id` preserves it

#### Scenario: Squad leader_id absent decodes to None
- **WHEN** a squad response omits `leader_id` or contains null
- **THEN** `SquadData.leader_id` is `None`

#### Scenario: Squad archived_at null decodes to None
- **WHEN** a squad response omits `archived_at` or contains null
- **THEN** `SquadData.archived_at` is `None`

#### Scenario: Squad archived_at RFC3339 decodes to datetime
- **WHEN** a squad response contains an RFC3339 `archived_at`
- **THEN** `SquadData.archived_at` is the corresponding timezone-aware `datetime`

#### Scenario: Existing minimal squad fixture still decodes
- **WHEN** a minimal legacy squad fixture omits optional fields
- **THEN** it decodes with the documented defaults

#### Scenario: Squad members remain typed
- **WHEN** `Squad.members.all()` loads
- **THEN** one `squad member list <squad-id> --output json` call returns typed `SquadMember` records preserving role and order

#### Scenario: Squad member list emits exact argv
- **WHEN** the squad member relation loads
- **THEN** transport receives `("squad", "member", "list", <squad-id>, "--output", "json")`

#### Scenario: Squad member list returns typed members
- **WHEN** the CLI returns squad member records
- **THEN** each item is a typed `SquadMember`

#### Scenario: Squad member list with multiple roles preserves each
- **WHEN** multiple squad members have distinct roles
- **THEN** identity, type, role, and response order are preserved

### Requirement: Autopilot resource governance and pagination
The SDK MUST govern `autopilots.list/get/create/update/delete/trigger/history`
and trigger mutation operations. `run` MUST be renamed to `trigger`;
unsupported `get_run` MUST be removed. Direct list/history page behavior
remains as specified by `autopilot-resource`, while bound `Workspace.autopilots`
and `Autopilot.runs/triggers/subscribers` provide the relation surface.

#### Scenario: Autopilot operation set is exact
- **WHEN** approved operations and discovered public methods are inspected
- **THEN** `trigger` replaces `run`, `get_run` is absent, and every supported operation has an intentionally changed rationale and canonical case

#### Scenario: Direct pages remain available
- **WHEN** direct list or history is called
- **THEN** it returns the documented typed page with total/limit/offset metadata while relations adapt those pages without changing direct behavior

#### Scenario: Autopilot list returns AutopilotListPage
- **WHEN** `autopilots.list()` succeeds
- **THEN** it returns the documented bound `AutopilotListPage`

#### Scenario: Autopilot history returns AutopilotRunListPage
- **WHEN** `autopilots.history()` succeeds
- **THEN** it returns the documented bound `AutopilotRunListPage`

#### Scenario: Autopilot operations are in the approved contract
- **WHEN** the approved contract is inspected
- **THEN** every supported autopilot operation has its governed binding and response contract

### Requirement: Corrected profile, repository, and runtime surfaces
The SDK MUST expose only source-governed D15–D17 surfaces. `users.profile_get`
returns immutable `UserProfile`; `users.profile_update(UserProfileUpdate)`
updates only a present description. `repositories.list/add/remove` use
immutable URL/description records and multi-URL mutation results.
`repositories.get` and `repositories.checkout` MUST be absent: checkout is a
daemon-task workflow, not a configured SDK server operation. `runtimes.get`
MUST be absent; usage/activity return immutable tuples, usage validates
`1 <= days <= 365`, update requires target-version with optional wait, rename
supports machine, and delete supports cascade. `runtimes.delete(...,
cascade=True)` SHALL mean that active dependent agents are unbound, their
queued/running tasks are cancelled, and the runtime is deleted; agent
configuration, chats, and task history SHALL remain preserved so the agents
can later be attached to another runtime. No SDK documentation SHALL describe
cascade deletion as destroying or archiving those agents.

#### Scenario: D15–D17 discovery is exact
- **WHEN** public resources and the approved contract are inspected
- **THEN** every approved D15–D17 symbol resolves with its approved signature, no removed legacy or daemon-only checkout symbol resolves, and each supported method has exactly one canonical transport vector

#### Scenario: Runtime cascade preserves agents
- **WHEN** `runtimes.delete(runtime_id, cascade=True)` is executed against Multica `v0.4.20`
- **THEN** argv contains `runtime delete <runtime-id> --cascade`, the runtime is deleted after dependent agents are unbound and their active work is cancelled, and those agents retain configuration, chats, and task history

#### Scenario: Runtime delete without cascade preserves the refusal
- **WHEN** dependent active agents exist and `runtimes.delete(runtime_id)` omits cascade
- **THEN** the operation raises the classified upstream conflict and does not imply that retrying will delete or archive the agents

### Requirement: Workspace member identity is explicit
The SDK SHALL decode workspace membership identity and user identity as separate
fields. It SHALL add optional `user_id` and `email` fields directly to the
existing `models.workspaces.WorkspaceMember` and
`models.system.WorkspaceMemberData`; it SHALL NOT add a separate member wire
class. `WorkspaceMember.id` SHALL remain the workspace membership identifier,
`WorkspaceMember.user_id` SHALL expose the related user identifier, and
`WorkspaceMember.email` SHALL expose the member email when supplied by the
pinned upstream response. `WorkspaceMemberEntity` SHALL expose same-named
passive properties. The added fields SHALL default to `None` when absent for
backward-compatible decoding.

#### Scenario: Distinct member and user identifiers round-trip
- **WHEN** `workspace member list --output json` returns different `id` and `user_id` values plus an `email`
- **THEN** the decoded `WorkspaceMember` preserves all three values without aliasing either identifier

#### Scenario: Older member payload remains decodable
- **WHEN** a workspace-member payload contains `id`, `name`, and `role` but omits `user_id` and `email`
- **THEN** decoding succeeds with `user_id is None` and `email is None`

#### Scenario: Membership identifier remains the assignee identifier
- **WHEN** `WorkspaceMember.issues` constructs its issue-list filter
- **THEN** it uses `WorkspaceMember.id` as `assignee_id` and does not substitute `user_id`

#### Scenario: User identifier supports creator reconciliation
- **WHEN** a consumer compares an issue `creator_id` with workspace members
- **THEN** it can compare against `WorkspaceMember.user_id` without interpreting the membership identifier as a user identifier

### Requirement: Issue get exposes its embedded attachment snapshot
The SDK SHALL decode the `attachments` array embedded in `issue get --output
json` through `IssueWire.attachments: tuple[AttachmentResult, ...] |
msgspec.UnsetType`. One shared normalization SHALL populate both
`Issue.attachments` and `IssueData.attachments` as
`tuple[AttachmentResult, ...]`; `issue_from_wire` and `issue_data_from_wire`
SHALL use that normalization. `IssueEntity.attachments` SHALL expose the
`IssueData` tuple as a passive property. Decoding SHALL reuse the existing
attachment result type and preserve response order. An omitted field and an
explicit empty array SHALL both normalize to `()`.

#### Scenario: Embedded attachments decode in response order
- **WHEN** `issue get --output json` returns two attachment objects
- **THEN** `Issue.attachments`, `IssueData.attachments`, and the bound `IssueEntity.attachments` expose two `AttachmentResult` values in the same order

#### Scenario: Empty attachment array decodes as an empty tuple
- **WHEN** `issue get --output json` contains `"attachments": []`
- **THEN** `Issue.attachments == ()`, `IssueData.attachments == ()`, and `IssueEntity.attachments == ()`

#### Scenario: Omitted attachment field decodes as an empty tuple
- **WHEN** `issue get --output json` omits `attachments`
- **THEN** decoding succeeds and the `Issue`, `IssueData`, and `IssueEntity` attachment snapshots are `()`

#### Scenario: Passive attachment access performs no I/O
- **WHEN** `IssueEntity.attachments` is read repeatedly from a bound issue returned by `issues.get`
- **THEN** no additional CLI invocation occurs

#### Scenario: Missing attachments are not an atomic completion signal
- **WHEN** a polling consumer observes `IssueEntity.attachments == ()` after `issues.get`
- **THEN** documentation explains that pinned upstream may omit the field after a best-effort attachment-read failure and the consumer can retry `issues.get`

### Requirement: Agent copy exposes portable upstream semantics

`AgentResource` SHALL expose eager `copy(...) -> Agent` and lazy
`copy_command(...) -> Command[Agent]` methods. Both methods SHALL accept a
required nonblank `source_agent_id` and the same keyword-only override surface:
`name`, `runtime_id`, `description`, `instructions`, `model`,
`thinking_level`, `service_tier`, `custom_args`, `max_concurrent_tasks`,
`permission_mode`, `public_to_workspace`, `public_to_member_ids`, and
`copy_skills`. Presence-sensitive string, tuple, integer, and permission
overrides SHALL use `Unset` as omission; a present `custom_args` SHALL be a
string-only `tuple[str, ...]`; `copy_skills` SHALL default to `True`. The eager
method SHALL delegate through the lazy command.

The operation SHALL emit `agent copy <source-agent-id>` and only the flags
represented by present overrides, plus `--no-skills` when `copy_skills=False`.
When `runtime_id` is present and `model` is omitted, the SDK SHALL emit
`--model ""` so the upstream cross-runtime guard selects the target runtime's
default model. This is the sole runtime-specific omission exception: omitted
`thinking_level` and `service_tier` SHALL remain absent and SHALL NOT be
invented. When `runtime_id` is omitted, omitted `model`, `thinking_level`, and
`service_tier` SHALL remain omitted so upstream preserves same-runtime state.
The SDK SHALL NOT expose or emit `custom_env`, `mcp_config`, or `runtime_config`
through this copy operation.

#### Scenario: Same-runtime copy keeps upstream defaults
- **WHEN** `client.agents.copy(source_agent_id)` is called without overrides
- **THEN** argv is `agent copy <source-agent-id> --output json`, the source remains unchanged, upstream creates a new agent on the source runtime, portable configuration and skills are copied, and machine-local or secret-bearing configuration is not copied

#### Scenario: Cross-runtime copy selects the target default model
- **WHEN** `client.agents.copy(source_agent_id, runtime_id=target_runtime_id)` is called without a model override
- **THEN** argv contains `--runtime-id <target-runtime-id> --model ""`, upstream creates the copy on the target runtime, and source model, thinking level, and service tier are not carried across the runtime boundary

#### Scenario: Cross-runtime runtime-specific values follow settled policy
- **WHEN** a target runtime is supplied with any combination of optional model,
  thinking-level, and service-tier overrides
- **THEN** each present value is emitted through its matching flag, an omitted
  model is emitted as `--model ""`, and omitted thinking-level and service-tier
  values remain absent

#### Scenario: Portable overrides preserve presence
- **WHEN** present overrides include an empty description or instructions, a
  string custom-argument tuple (`tuple[str, ...]`), max concurrency, invocation
  permissions, and `copy_skills=False`
- **THEN** exact argv preserves caller order and empty-string presence,
  serializes the string custom-argument tuple as a compact JSON array, emits
  permission flags and `--no-skills`, and does not emit any secret or
  machine-local flag

#### Scenario: Permission member order is stable
- **WHEN** `public_to_member_ids` contains multiple member IDs
- **THEN** argv contains repeatable `--public-to-member` flags in caller order

#### Scenario: Copy validation occurs before transport
- **WHEN** source ID or a present name is blank, max concurrency is outside `1..50`, or a present member ID is blank
- **THEN** construction raises `ValueError` naming the invalid input before command preview or subprocess execution

#### Scenario: Copy command preview is lazy and redacted
- **WHEN** `copy_command()` is constructed with valid overrides
- **THEN** no subprocess I/O occurs, `commands` shows the exact shell-rendered `agent copy` invocation, and `run()` executes that same plan and returns the bound copied `Agent`

### Requirement: Upstream-owned runtime and model values remain open

Public fields and inputs whose vocabulary is controlled by Multica runtimes or
providers SHALL use `str` or `str | None`, not a closed SDK enum. This includes
runtime/provider/model response fields and agent-copy model, thinking-level,
and service-tier overrides. Closed SDK workflow enums such as issue status are
unchanged.

#### Scenario: Unknown provider and model decode
- **WHEN** a valid upstream response contains provider and model strings unknown at SDK release time
- **THEN** the typed model decodes successfully and preserves both strings

#### Scenario: Future runtime-specific copy values pass through
- **WHEN** agent copy receives previously unknown model, thinking-level, or service-tier strings
- **THEN** command construction accepts and emits them verbatim for upstream validation

### Requirement: Default and layered client options
`MulticaClient` SHALL accept no argument and use `ClientConfig()` defaults, while continuing to accept one explicit `ClientConfig`. The SDK SHALL expose `with_options(...)` for immutable client views and `OperationOptions` for one-call overrides. The supported override fields SHALL be `profile`, `workspace_id`, `timeout`, `cwd`, and `environment`; omission SHALL inherit the lower layer, explicit `None` SHALL clear nullable scalar/path settings, and an explicit empty environment SHALL clear inherited SDK environment entries. Effective precedence SHALL be operation options over scoped-client options over base configuration. Numeric timeouts SHALL represent nonnegative finite seconds and normalize to `datetime.timedelta`; cwd SHALL accept `str` or `os.PathLike` and normalize to `pathlib.Path`.

#### Scenario: Default client is usable
- **WHEN** a caller constructs `MulticaClient()`
- **THEN** it behaves as `MulticaClient(ClientConfig())` and exposes the complete resource tree

#### Scenario: Explicit configuration remains available
- **WHEN** a caller passes a `ClientConfig` to `MulticaClient`
- **THEN** that exact immutable configuration remains the base layer

#### Scenario: Scoped options do not mutate their source
- **WHEN** `scoped = client.with_options(profile="automation", workspace_id="ws_1", timeout=30, cwd="./repo")` is created
- **THEN** `scoped` uses the normalized overrides, `client.config` is unchanged, and both clients share only the existing process semaphore

#### Scenario: Per-operation options win
- **WHEN** a command is constructed with `OperationOptions(timeout=5, workspace_id="ws_2")` from a client scoped to timeout 30 and workspace `ws_1`
- **THEN** its preview and execution use timeout 5 and workspace `ws_2` while inheriting every non-overridden setting

#### Scenario: Invalid execution values fail before I/O
- **WHEN** a timeout is negative, non-finite, or not a supported duration/number, or a non-`None` profile/workspace is blank
- **THEN** construction raises `TypeError` or `ValueError` before command or transport I/O

### Requirement: Direct typed parameters are the sole operation input
Affected eager and `*_command()` operations SHALL expose matching explicit typed parameters and SHALL NOT accept a one-operation request DTO, a generic `request | None` positional slot, or public `**kwargs: object`. The SDK SHALL remove exactly `AgentCreateRequest`, `AgentUpdateRequest`, `ProjectCreateRequest`, `ProjectUpdateRequest`, `SkillCreateRequest`, `SkillUpdateRequest`, `LabelUpdateRequest`, `IssueCreateRequest`, `IssueUpdateRequest`, `IssueAssignmentRequest`, `IssueReorderRequest`, `ProjectResourceAddLocalDirectoryRequest`, `ProjectResourceUpdateLocalDirectoryRequest`, `CommentListFlatRequest`, `CommentListThreadRequest`, `CommentListRecentRequest`, `MetadataListRequest`, `MetadataSetRequest`, `AutopilotUpdateRequest`, `AutopilotTriggerCreate`, `AutopilotTriggerUpdate`, `RuntimeUpdate`, and `UserProfileUpdate`. Validation formerly owned by those DTOs SHALL run in the public method or command-building layer before I/O.

#### Scenario: Runtime signatures describe real inputs
- **WHEN** `inspect.signature` examines any affected eager or command method
- **THEN** it exposes the real typed operation fields plus the shared optional `options` keyword and contains no request slot or catch-all kwargs

#### Scenario: Eager and command signatures match
- **WHEN** an affected eager method and its `*_command()` sibling are normalized for their return annotation
- **THEN** their operation parameters, defaults, keyword-only boundaries, and `OperationOptions` parameter are identical

#### Scenario: Removed DTO imports fail
- **WHEN** a consumer imports any of the 23 removed names from `multica_py`, `multica_py.models`, or its former model module
- **THEN** the name is absent, while modules containing retained semantic/output models remain importable

#### Scenario: Empty request-only modules are deleted
- **WHEN** `models.projects` and `models.labels` contain no retained public model after migration
- **THEN** those files and all references to them are removed

#### Scenario: Validation survives DTO removal
- **WHEN** callers provide null non-nullable updates, blank identifiers/names, invalid pagination, multiple assignment modes, or zero/multiple reorder targets through retained low-level methods
- **THEN** equivalent typed errors occur before I/O and no invariant is weakened

#### Scenario: Semantic value objects remain
- **WHEN** public models are inspected after the cleanup
- **THEN** `IssueListFilter`, issue description variants, `MetadataPredicate`/`IssueMetadataItem`, `CommentCursor`, `LocalDirectoryResourceRef`, `ProjectResourceRecord`, `Unset`, enums, pages, entities, and output/result models remain available from their dedicated modules

### Requirement: Canonical bound Issue collections
`issues.list(...)` SHALL return `IssueListPage` whose `items`/compatibility `issues` alias contains bound `Issue` entities, and `issues.search(...)` SHALL return `Page[Issue]`. Workspace, workspace-member, project, agent, and squad issue relations SHALL yield bound `Issue` entities. Each decoder SHALL construct the canonical `Issue` from fields already present in the collection row, default unavailable fields safely, preserve optional open-string `match_source` on search-originated issues, and bind the originating client without issuing an automatic `issues.get`.

#### Scenario: List returns actionable issues
- **WHEN** a caller iterates `client.issues.list().items`
- **THEN** each value is a bound `Issue` that can immediately call entity actions and relations

#### Scenario: Search preserves match metadata
- **WHEN** search rows include a known or unknown future `match_source`
- **THEN** the returned bound `Issue.match_source` preserves that string and defaults to `None` when omitted

#### Scenario: Partial rows remain honest
- **WHEN** list, search, or relation rows omit fields only supplied by `issue get`
- **THEN** the corresponding optional/snapshot fields on `Issue` use documented defaults until explicit `refresh()`/`get()` and are not fabricated

#### Scenario: Collections avoid N plus one reads
- **WHEN** N issue rows are decoded from list, search, or a relation
- **THEN** exactly the collection command runs and zero per-row `issue get` commands run

#### Scenario: IssueSummary leaves the primary API
- **WHEN** public types, return annotations, contracts, docs, and examples are inspected
- **THEN** normal issue workflows use `Issue`; `IssueSummary` is absent or confined to a private compatibility decoder with no public export

### Requirement: Explicit issue domain actions
The canonical resource actions SHALL be `assign(issue_id, assignee)`, `unassign(issue_id)`, `move_to_top(issue_id)`, `move_to_bottom(issue_id)`, `move_before(issue_id, other_issue)`, and `move_after(issue_id, other_issue)`, each with an argument-identical `*_command()` sibling. Bound `Issue` SHALL expose the corresponding context-bound forms plus `refresh`, `update`, and `set_status`. Assignment and issue references SHALL accept a nonblank identifier or an appropriate bound entity and normalize to its ID. The low-level direct `reorder(...)` operation MAY remain for compatibility but SHALL retain its exactly-one-target validation and SHALL not be the documented default.

#### Scenario: Resource assignment reads as intent
- **WHEN** `client.issues.assign("MUL-123", agent)` is called with an agent entity or identifier
- **THEN** it emits the governed assignment argv and returns a bound `Issue`

#### Scenario: Unassignment has its own verb
- **WHEN** resource or bound-entity `unassign()` is called
- **THEN** the governed `--unassign` action runs without an `unassign=True` public mode flag

#### Scenario: Move methods encode one target
- **WHEN** any explicit top, bottom, before, or after method is called
- **THEN** it emits exactly one corresponding reorder target and cannot express an invalid mutually exclusive combination

#### Scenario: Bound issue continues a workflow
- **WHEN** an issue comes from get, list, search, or a relation
- **THEN** `refresh`, `update`, `assign`, `unassign`, `set_status`, and move methods delegate through the same root resource command plans and return newly bound immutable `Issue` values

### Requirement: Unified Python attachment upload
`attachments.upload(source, *, filename=None, task_id=None, options=None)` and `upload_command(...)` SHALL accept a filesystem path/path-like object, bytes-like content, or a binary file-like object. Path input SHALL use the existing file directly. In-memory input SHALL require a safe supplied filename unless a safe basename can be derived from the stream's `.name`; it SHALL be materialized only for command execution, cleaned after success/failure, and preserve exact bytes. `upload_bytes(...)` and `upload_bytes_command(...)` MAY remain as compatibility aliases that delegate to the unified API; documentation SHALL prefer `upload`.

#### Scenario: Path upload preserves governed behavior
- **WHEN** source is a path-like value
- **THEN** the existing `attachment upload <absolute-path> [--task <id>] --output json` plan and result contract are preserved without copying the file

#### Scenario: Bytes upload uses a safe filename
- **WHEN** source is bytes and `filename="report.txt"`
- **THEN** execution materializes those exact bytes under that basename, uploads it, and removes the temporary directory

#### Scenario: Stream upload is lazy and non-owning
- **WHEN** `upload_command` is constructed for an open binary stream
- **THEN** command construction performs no read, execution consumes the stream without closing it, and a closed/unreadable/text stream fails clearly

#### Scenario: Unsafe or missing filename fails before filesystem access
- **WHEN** in-memory input has no derivable filename or the filename is blank, absolute, contains path separators (including traversal forms such as `../report.txt`), or is exactly the dot-segment `.` or `..`
- **THEN** `ValueError` is raised before temporary filesystem or transport access

#### Scenario: Safe basename containing double dots remains valid
- **WHEN** in-memory input is uploaded with the safe basename `filename="report..txt"`
- **THEN** filename validation accepts it as a leaf name, and command construction preserves the filename without temporary filesystem or transport access

#### Scenario: Compatibility aliases are exact
- **WHEN** `upload_bytes(filename, payload, ...)` is used during the migration window
- **THEN** it delegates to `upload(payload, filename=filename, ...)` with identical preview, result, cleanup, and error behavior

### Requirement: Deliberately small package root
The `multica_py` root SHALL export only the default/configuration and operation option types, `Command`, common page/action/process contracts, primary bound entities, common workflow enums and `Unset`, and the public exception hierarchy. Relation implementations, JSON/metadata aliases, reusable filters and semantic value objects, compatibility page names, raw CLI result details, and resource-specific output models SHALL be imported from dedicated modules.

#### Scenario: Common imports remain obvious
- **WHEN** a normal user imports `MulticaClient`, `ClientConfig`, `OperationOptions`, `Issue`, `Project`, `Agent`, `IssueStatus`, or `MulticaError` from `multica_py`
- **THEN** each import succeeds

#### Scenario: Advanced names leave root autocomplete
- **WHEN** `multica_py.__all__` is inspected
- **THEN** request DTOs and advanced relation/wire/value/compatibility types are absent and documentation gives their dedicated-module locations when retained

