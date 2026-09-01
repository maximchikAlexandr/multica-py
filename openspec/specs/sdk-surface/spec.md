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

#### Scenario: Domain methods delegate to resources
- **WHEN** a unified-class instance method (e.g. `Issue.add_comment`,
  `Issue.set_status`, `Project.add_local_directory`) is called on an attached
  instance
- **THEN** it delegates to the originating client's resource method and does
  not construct CLI argv or invoke the transport directly

#### Scenario: Every CLI-executing operation has a command sibling

- **WHEN** the public resource surface is discovered
- **THEN** every CLI-executing public resource method has a typed
  `*_command()` sibling whose arguments and validation match the eager
  operation, and the eager method delegates through
  `*_command(...).run()`

#### Scenario: No preview flag or mirrored namespace

- **WHEN** the public surface is inspected
- **THEN** no `preview=True` parameter, no union return type on eager
  operations, no `client.commands.*` namespace, no callable proxy, and no
  generic workflow/DAG API exists

#### Scenario: No command variant for local-only methods

- **WHEN** the public surface is inspected
- **THEN** methods that perform no CLI subprocess (e.g. `invalidate()`)
  have no `*_command()` variant and no fake command is constructed for
  them

#### Scenario: Default client is local
- **WHEN** `MulticaClient(config)` is constructed without an executor
- **THEN** it behaves equivalently to `MulticaClient(config, executor=LocalExecutor())` and uses local execution

#### Scenario: Executor is separate from config
- **WHEN** `MulticaClient(config, executor=SshExecutor(...))` is constructed
- **THEN** `config` remains the immutable CLI-invocation description and the executor is the live runtime execution backend

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

#### Scenario: One public class per concept
- **WHEN** a consumer imports a full domain concept
- **THEN** exactly one public class represents it (e.g. `Issue`, `Project`,
  `Agent`) and no separate `*Data`, `*Entity`, or passive DTO class for that
  concept is exported from `multica_py` or its submodules

#### Scenario: Public domain fields are declared once and frozen
- **WHEN** the unified class is inspected
- **THEN** each public domain field is declared exactly once on the class and
  the class is `msgspec.Struct, frozen=True, kw_only=True`

#### Scenario: Runtime state is private and excluded
- **WHEN** a unified instance is compared, printed, or serialized
- **THEN** `_client`, lazy-relation caches, locks, and loaders are excluded
  from equality, `repr`, `to_json`, and `to_dict`

#### Scenario: No public ResourceEntity base
- **WHEN** the public surface is inspected
- **THEN** `ResourceEntity` is absent from `multica_py.__all__` and from
  `multica_py.models.__all__`; a private `_BoundEntity` helper may exist but
  is not exported

#### Scenario: Request and filter models stay separate
- **WHEN** a create, update, assignment, reorder, or list-filter operation is
  inspected
- **THEN** its request/filter model (`IssueCreateRequest`,
  `IssueUpdateRequest`, `IssueAssignmentRequest`, `IssueReorderRequest`,
  `IssueListFilter`, ...) remains a distinct public class and is not merged
  into the unified domain class

#### Scenario: IssueSummary stays a distinct partial response
- **WHEN** `issues.list` or a list-backed relation returns rows
- **THEN** the rows are `IssueSummary` values and the SDK does not construct a
  full `Issue` with empty defaults for fields the list response omitted

#### Scenario: JSON values have immutable public snapshots
- **WHEN** a consumer reads an `AutopilotRun.trigger_payload` or `result`
  value
- **THEN** object nodes are typed as `Mapping[str, JsonValue]`, arrays are
  tuples, and recursively mutating the original input cannot change the run

#### Scenario: JSON values serialize through the SDK boundary
- **WHEN** a consumer calls `AutopilotRun.to_dict()` or `to_json()`
- **THEN** immutable Mapping/tuple snapshots are materialized as standard
  JSON dict/list containers and the result is directly serializable

#### Scenario: Command is the only new public type

- **WHEN** the public surface is inspected after this change
- **THEN** `Command` is exported from `multica_py`, is a generic with no
  public mutable state, and no other new public type is added

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

#### Scenario: Explicit configuration and executor remain available
- **WHEN** a caller passes a `ClientConfig` and an executor to `MulticaClient`
- **THEN** that exact immutable configuration remains the base layer and that executor is the execution backend

#### Scenario: Scoped clients preserve the executor
- **WHEN** `remote.with_workspace("ws_123")` is created from a client configured with a non-local executor
- **THEN** the scoped client uses the same non-local executor and does not silently fall back to local execution

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

#### Scenario: Executors leave root autocomplete
- **WHEN** `multica_py.__all__` is inspected
- **THEN** every optional provider executor (including `MicrosandboxExecutor` and `SshExecutor`) and provider-specific configuration is absent from the root namespace and documentation gives its `multica_py.execution.<provider>` location

### Requirement: Natural issue and project operation inputs
Project and issue creation SHALL accept ordinary Python text, path, identifier, and appropriate entity-reference values without restoring one-operation request DTOs. `ProjectResource.create` and `create_command` SHALL expose matching `description: str | None` and `description_file: str | os.PathLike[str] | None` keywords. `IssueResource.create` and `create_command` SHALL expose matching ordinary `description`, `description_file`, and `project: str | Project | None` keywords while retaining `description_input: IssueDescriptionInput | None` for the semantically distinct `InlineDescription`, `FileDescription`, `StdinDescription`, and `NoDescription` variants. The existing `project_id` keyword MAY remain as a compatibility spelling, but documentation SHALL use `project`; callers SHALL NOT provide both. Project-scoped issue creation SHALL expose the same description forms while continuing to supply its bound project implicitly. Normalization SHALL preserve the approved argv, `OperationOptions`, eager/command parity, result decoding, and client binding.

#### Scenario: Project file description is passive and inspectable
- **WHEN** a caller builds `client.projects.create_command(name="Backend", description_file=path)` with a string or `os.PathLike[str]`
- **THEN** the plan contains `project create --title Backend --description-file <lexically-absolute-path> --output json`, construction does not open, stat, or require the path to exist, and the eager method exposes the same operation parameters

#### Scenario: Issue inline description uses the governed flag
- **WHEN** a caller creates an issue with `description="Investigate the login failure"`
- **THEN** normalization emits the existing `--description` argv mapping and does not construct an `IssueDescriptionInput` request DTO

#### Scenario: Issue file description preserves semantic alternatives
- **WHEN** a caller supplies a path through `description_file` or a `FileDescription`, inline text through `description` or `InlineDescription`, or explicit stdin through `StdinDescription`
- **THEN** exactly the existing approved `--description-file`, `--description`, or `--description-stdin` mapping is emitted and `NoDescription`/omission emits none of those flags

#### Scenario: Project entity normalizes to its identifier
- **WHEN** `client.issues.create(title="Fix authentication", project=project)` receives a `Project` entity
- **THEN** it emits the same `--project <project.id>` mapping as an identifier string and performs no lookup or other implicit I/O

#### Scenario: Invalid or conflicting natural forms fail locally
- **WHEN** a caller supplies more than one description form, both `project` and `project_id`, a bytes path, a blank file path or identifier, an incompatible entity type, or another unsupported natural value
- **THEN** construction raises `TypeError` or `ValueError` before filesystem or transport I/O and never leaks an implementation `AttributeError`

### Requirement: Public status inputs normalize exact enum values
Issue status inputs on direct list fields, `IssueListFilter`, issue resource
`set_status`, and bound `Issue.set_status` SHALL accept `IssueStatus | str`.
Canonical `IssueStatus` members remain the seven values `backlog`, `todo`,
`in_progress`, `in_review`, `done`, `blocked`, and `cancelled`. List, filter,
and `set_status` construction SHALL pass the enum value or string through to
argv without a local enum membership check for unknown custom names; invalid
names fail at the CLI after construction. Non-str/non-enum values SHALL raise
`TypeError` before transport. Documentation SHALL use real values such as
`"todo"`, `"in_progress"`, and `"done"`. `"open"` SHALL remain a documentation
anti-example of a non-status spelling and SHALL NOT be a local `ValueError`
oracle for unknown issue status strings. Get/list/`Issue.status` /
`_IssueWire.status` decoding SHALL use `IssueStatus | str` and SHALL preserve
unknown status names without a constructor crash. This change SHALL NOT add
workspace-status CRUD. Whether tagged CLI accepts custom names is a source
mapping note, not a second SDK construction rule.

`ProjectResource.set_status` SHALL continue to accept a `ProjectStatus` member
or its exact case-sensitive string value. Unknown project status strings SHALL
raise `ValueError` before transport. `Project` has no `set_status[_command]`
bound-entity surface, and this change SHALL NOT add one.

#### Scenario: Exact issue status string is accepted
- **WHEN** a caller uses `issues.list(status="todo")` or `issue.set_status("done")`
- **THEN** the command contains the same governed status value as the corresponding `IssueStatus` member

#### Scenario: Exact project resource status string is accepted
- **WHEN** a caller uses `client.projects.set_status(project_id, "in_progress")`
- **THEN** the command contains the same governed status value as `ProjectStatus.in_progress`

#### Scenario: Unknown issue status strings pass through on set_status
- **WHEN** a caller passes a non-canonical status string to resource or bound `set_status`
- **THEN** construction emits that string in argv and does not raise `ValueError` for unknown membership; invalid names fail at the CLI

#### Scenario: Unknown issue status strings pass through on list and IssueListFilter
- **WHEN** a caller passes a non-canonical status string to `issues.list(status=...)` or `IssueListFilter`
- **THEN** construction emits that string in argv and does not raise `ValueError` for unknown membership; invalid names fail at the CLI

#### Scenario: Incompatible issue status types fail locally
- **WHEN** a caller passes a non-string/non-enum value to an issue status input
- **THEN** construction raises `TypeError` before transport and does not raise `AttributeError`

#### Scenario: Unknown status fails with a typed local error
- **WHEN** a caller passes a non-string/non-enum value to any public status input, or passes `"open"`, a differently cased spelling, or another unknown string to `ProjectResource.set_status`
- **THEN** construction raises `TypeError` for incompatible types or `ValueError` for unknown project status strings before transport and does not raise `AttributeError`

### Requirement: Workspace and agent MCP libraries are public operations

The SDK SHALL expose tagged `v0.4.28` MCP library commands as eager/command
pairs on nested resource classes: `workspace mcp list|add|update|remove` and
`agent mcp list|add|enable|disable|remove`. Those nested surfaces SHALL register
in `RESOURCE_SPECS` / `_NESTED_RESOURCE_ATTRS` (and `__init__` / docs exports)
the same way `issues.metadata` does, so discovery tests see the methods. Workspace add and update SHALL
accept exactly one of `server_config_file`, `server_config_stdin`, or an inline
`server_config` string. File and stdin SHALL be the documented default channels.
When an inline JSON string is accepted, it SHALL be redacted from preview,
diagnostics, and exception attributes. Workspace MCP list decoding SHALL use
only reviewed public fields and SHALL NOT claim to return stored server
config or tokens. Agent MCP mutations SHALL take `agent_id` and `server_id`
only. Workspace and agent MCP mutations SHALL emit `--output json` unless
source proves a given command is non-JSON.
`workspace mcp remove` is source-proven text output and SHALL return
`ActionResult[None]` without JSON decoding. Bound Agent and Workspace MCP
mutations SHALL invalidate an already-loaded `mcp_servers` relation after a
successful run.

#### Scenario: Workspace MCP list omits secrets
- **WHEN** `workspace.mcp_servers.all()` loads
- **THEN** argv is `workspace mcp list --output json` (command tokens only; workspace scope is client `--workspace-id`, not a required command `--workspace`) and decoded rows contain reviewed public identity fields without config JSON or credentials

#### Scenario: Workspace MCP add prefers a config file
- **WHEN** add is called with `server_config_file=path`
- **THEN** argv contains `--server-config-file <path>` and does not contain `--server-config` or `--server-config-stdin`

#### Scenario: Workspace MCP add rejects mixed config channels
- **WHEN** more than one of inline JSON, file, and stdin is present
- **THEN** construction raises `ValueError` before transport

#### Scenario: Inline MCP JSON is redacted
- **WHEN** add is called with inline `server_config` containing a token
- **THEN** preview and exception diagnostics omit the token while the executed argv still carries the JSON flag if that channel is used

#### Scenario: Agent MCP enable is a distinct command
- **WHEN** `agents.mcp.enable(agent_id, server_id)` runs
- **THEN** argv is `agent mcp enable <agent-id> <server-id> --output json` unless source proves enable is non-JSON, and is not implemented as add or update

#### Scenario: Workspace MCP remove is a text action
- **WHEN** `workspaces.mcp.remove(server_id)` succeeds
- **THEN** the SDK consumes the tagged CLI text result as `ActionResult[None]` and does not attempt to decode an MCP-server JSON page

#### Scenario: Bound MCP mutations invalidate loaded relations
- **WHEN** a bound Agent or Workspace MCP mutation succeeds after `mcp_servers` has loaded
- **THEN** the cached relation is invalidated and its next load observes the server-side state

### Requirement: Skill refresh is a governed operation

`SkillResource` SHALL expose `refresh` / `refresh_command` mapping to
`skill refresh <id> --output json`. The method SHALL validate a nonblank skill
id before transport and SHALL decode the reviewed JSON result into the existing
`Skill` model or the reviewed action envelope, whichever source returns.

#### Scenario: Skill refresh emits exact argv
- **WHEN** `client.skills.refresh(skill_id)` runs
- **THEN** argv is `skill refresh <skill-id> --output json` and construction performs no subprocess I/O until `run()`

### Requirement: Issue status and assignee follow tagged CLI semantics

`IssueStatus` SHALL retain the seven canonical values `backlog`, `todo`,
`in_progress`, `in_review`, `done`, `blocked`, and `cancelled`. Get/list,
`Issue.status`, and `_IssueWire.status` decoding SHALL accept `IssueStatus | str`
and SHALL preserve unknown names without a constructor crash. Issue list,
filter, and `set_status` SHALL accept `IssueStatus | str` and SHALL pass the
value through to argv without a local enum membership check; invalid names
fail at the CLI after construction. The SDK SHALL NOT invent a
workspace-status CRUD API. Source-trace of whether tagged CLI accepts custom
names is a mapping note, not a second SDK rule. Any reviewed category
field SHALL be an optional open string on issue models and SHALL default to
`None` when omitted.

`--assignee` SHALL remain a single string flag. When source resolves email
addresses through that flag, canonical vectors MAY use an email value; the SDK
SHALL NOT add a separate `assignee_email` parameter.

#### Scenario: Canonical statuses still construct
- **WHEN** `set_status(issue_id, IssueStatus.in_review)` runs
- **THEN** argv is `issue status <issue-id> in_review`

#### Scenario: Unknown status strings pass through on set_status
- **WHEN** a caller passes a non-canonical status string to `set_status`
- **THEN** construction emits that string in argv and does not raise `ValueError` for unknown membership; invalid names fail at the CLI

#### Scenario: Unknown status strings pass through on list and IssueListFilter
- **WHEN** a caller passes a non-canonical status string to `issues.list(status=...)` or `IssueListFilter`
- **THEN** construction emits that string in argv and does not raise `ValueError` for unknown membership; invalid names fail at the CLI

#### Scenario: Unknown status strings decode
- **WHEN** issue get JSON contains a status name absent from the seven canonical values
- **THEN** decoding succeeds and `Issue.status` preserves that string

#### Scenario: Assignee email uses the existing flag
- **WHEN** create or assign is called with `assignee="user@example.com"` and source accepts email on `--assignee`
- **THEN** argv contains `--assignee user@example.com` and does not add a second email flag

### Requirement: Unified domain class serialization and detach

The unified class SHALL expose `to_json() -> str`, `from_json(payload: str |
bytes) -> Self`, `to_dict() -> dict[str, object]`, and `from_dict(data:
dict[str, object]) -> Self` covering only public domain fields. It SHALL
expose `detach() -> Self` returning the same class with `_client=None` and
relation caches reset to their unloaded state. The SDK SHALL NOT serialize
`_client`, lazy caches, locks, or loaders. `from_json` / `from_dict` SHALL
construct a detached instance (`_client=None`). The legacy
`ResourceEntity.to_data()` / `from_data()` boundary SHALL be removed.

#### Scenario: to_json round-trips public fields only
- **WHEN** `issue.to_json()` is decoded via `Issue.from_json(payload)`
- **THEN** the result equals `issue.detach()` on public fields and its
  `_client is None`

#### Scenario: to_dict excludes runtime state
- **WHEN** `issue.to_dict()` is inspected
- **THEN** the dict contains only public domain field keys and no `_client`,
  `_comments`, `_labels`, or other runtime-state keys

#### Scenario: detach clears client and caches
- **WHEN** `issue.detach()` is called on an attached issue
- **THEN** the result is an `Issue` with `_client is None` and any lazy
  relation caches reset to unloaded

#### Scenario: to_data and from_data are removed
- **WHEN** the public surface is inspected
- **THEN** no `to_data` or `from_data` method exists on any unified class and
  `ResourceEntity.to_data` / `from_data` are absent

### Requirement: Attached and detached instances use the same class

The same public unified class SHALL support both attached (constructed by a
resource with a client) and detached (constructed without a client)
instances. An operation requiring a client called on a detached instance SHALL
raise `DetachedEntityError` before any subprocess invocation. The SDK SHALL
NOT require a separate public `*Data` class to represent a detached instance.

#### Scenario: Attached instance delegates to resources
- **WHEN** `issue = client.issues.get("issue_123"); issue.add_comment("x")`
- **THEN** the call delegates to `client.issues.comments.add` and returns a
  bound `Comment`

#### Scenario: Detached instance raises on client-requiring operations
- **WHEN** `issue = Issue.from_json(payload); issue.add_comment("x")`
- **THEN** `DetachedEntityError` is raised before any subprocess invocation

#### Scenario: Detached instance scalar access works
- **WHEN** `issue = Issue.from_json(payload); print(issue.title)`
- **THEN** the public field is readable without a client and no I/O occurs

### Requirement: Wire models are private and retained only where they normalize

Wire models SHALL use private `_...Wire` names and SHALL be retained only
where they perform at least one of: field renaming, `UNSET` normalization,
nested object conversion, validation of CLI output, compatibility handling,
or isolation from an unstable external schema. Where the CLI output already
matches the public model, the SDK SHALL decode directly into the unified
class. Wire models SHALL NOT be exported from `multica_py` or its public
submodules.

#### Scenario: Wire models are private
- **WHEN** `_internal/wire_models.py` is inspected
- **THEN** every wire class is named with a leading underscore
  (`_IssueWire`, `_AutopilotWire`, `_ProjectWire`, `_CommentWire`, ...) and
  none is exported from `multica_py` or `multica_py.models`

#### Scenario: Wire models retained only with a reason
- **WHEN** a wire model exists
- **THEN** it performs at least one normalization (rename, `UNSET`, nested
  conversion, validation, or schema isolation) and is documented in the
  change design

#### Scenario: Direct decode where no normalization is needed
- **WHEN** the CLI output for a concept already matches the public model
  (Agent, Workspace, Skill, Squad, WorkspaceMember, TaskRun, Label)
- **THEN** the resource decodes directly into the unified class and no wire
  model is introduced for that concept

### Requirement: Unified domain class naming and migration

The SDK SHALL rename each `*Entity` class to the canonical domain name and
absorb the `*Data` fields into it. Redundant passive DTOs between the wire
model and the data/entity pair SHALL be removed. The migration is a single
breaking change; the SDK SHALL NOT ship `*Data = <Unified>` aliases because
the unified class carries private runtime state and does not preserve the
old pure-client-free-data-container guarantee. `docs/migration.md` SHALL
record the full rename table and the `to_data() -> to_json()/to_dict()`
replacement.

#### Scenario: Canonical names replace Entity names
- **WHEN** the public surface is inspected
- **THEN** `IssueEntity` is renamed `Issue`, `AgentEntity` is renamed `Agent`,
  `SkillEntity` is renamed `Skill`, `SquadEntity` is renamed `Squad`,
  `WorkspaceEntity` is renamed `Workspace`,
  `WorkspaceMemberEntity` is renamed `WorkspaceMember`,
  `AutopilotEntity` is renamed `Autopilot`,
  `AutopilotRunEntity` is renamed `AutopilotRun`, and the `Project` /
  `Comment` / `CommentThread` / `TaskRun` / `Label` entities already bearing
  the canonical name keep it

#### Scenario: Data classes are removed
- **WHEN** the public surface is inspected
- **THEN** `IssueData`, `ProjectData`, `AgentData`, `WorkspaceData`,
  `SkillData`, `AutopilotData`, `AutopilotRunData`, `SquadData`,
  `WorkspaceMemberData`, `CommentData`, `CommentThreadData`, `TaskRunData`,
  and `LabelData` are removed from public exports and their fields move to
  the unified class

#### Scenario: Redundant passive DTOs are removed
- **WHEN** the `models` package is inspected
- **THEN** the passive DTOs `models.issues.Issue`, `models.projects.Project`,
  `models.agents.Agent`, `models.workspaces.Workspace`,
  `models.skills.Skill`, `models.autopilots.Autopilot`,
  `models.autopilots.AutopilotRun`, `models.system.Squad`,
  `models.system.WorkspaceMember`, `models.issue_activity.Comment`,
  `models.issue_activity.CommentThread`, `models.issue_activity.TaskRun` are
  removed and the canonical name is used only by the unified class

#### Scenario: No misleading aliases
- **WHEN** the public surface is inspected
- **THEN** no `IssueData = Issue`, `AgentData = Agent`, or similar alias
  exists in `multica_py.__all__` or in any public module

#### Scenario: Migration table is documented
- **WHEN** `docs/migration.md` is reviewed
- **THEN** it contains a rename table mapping each removed `*Data`/`*Entity`/
  passive DTO name to the unified class name and records the
  `to_data() -> to_json()`/`to_dict()` replacement

### Requirement: Command preview documentation default

The SDK documentation SHALL present the eager form as the default example
for every CLI-executing operation and SHALL document the `*_command()`
form as the inspectable alternative, explaining when command preview is
useful (debugging, scripting, audit, asserting CLI routing in tests). It
SHALL state that `commands` is always a tuple (empty for a no-op, one
item for one CLI call, ordered items/templates for a composite
operation), that preview construction performs no I/O, and that
`command.run()` executes the same immutable plan.

#### Scenario: Docs show eager form first

- **WHEN** the resource method documentation for a CLI-executing
  operation is reviewed
- **THEN** the primary example uses the eager form and a secondary
  example shows the `*_command()` form labeled as the inspectable
  alternative

#### Scenario: Docs explain the commands tuple shape

- **WHEN** the `Command` documentation is reviewed
- **THEN** it states that `commands` is always a tuple, explains the
  empty/one-item/ordered-items cases, and notes that preview performs no
  I/O while `run()` executes the same immutable plan

### Requirement: Executor lifecycle on the client
`MulticaClient` SHALL expose an explicit `close()` method in addition to
context-manager cleanup. `MulticaClient` owns the executor if and only if
it constructed it (the default `LocalExecutor()` when `executor is None`);
a user-supplied executor is NEVER owned by any client. `close()` on the
root client SHALL close the transport and SHALL close the executor only if
the client owns it. `close()` on a scoped `with_*()` client SHALL close
only the scoped transport and SHALL NEVER close the shared executor. Provider
executors SHALL create and own their sessions from connection parameters;
provider-client injection is outside this milestone. `close()` SHALL close
the session but SHALL NEVER destroy the execution
environment (sandbox or VM). Derived client views SHALL NOT
independently destroy a shared executor/session.

#### Scenario: Explicit close is available
- **WHEN** a caller calls `client.close()` or the context manager exits on a root client that used the default `LocalExecutor()`
- **THEN** the transport and the client-owned default executor are closed

#### Scenario: User-supplied executor survives a root client close
- **WHEN** the root client that was given a user-supplied executor is closed
- **THEN** the transport is closed and the executor is NOT closed (the user owns its lifecycle)

#### Scenario: User-supplied executor survives a scoped view close
- **WHEN** a scoped client view using a user-supplied executor is closed while the root client still uses it
- **THEN** only the scoped transport is closed, the executor is not closed, and the root client remains usable with that executor

#### Scenario: Executor closes its session without destroying the target
- **WHEN** a provider executor is closed
- **THEN** its provider session is closed and the underlying sandbox or VM remains intact

### Requirement: Raw run messages match the approved upstream payload
`multica_py.models.issue_activity.RunMessage` SHALL be an immutable keyword-only model with required `task_id: str`, `seq: int`, and `type: str`; optional `issue_id: str | None`, `tool: str | None`, `content: str | None`, `input: Mapping[str, JsonValue] | None`, `output: str | None`, and `created_at: datetime | None`; and no fabricated `id`, `run_id`, or `role` fields. Decoding SHALL preserve every type string, including blank, and recursively immutable structured tool input. A blank type SHALL remain a valid raw payload and SHALL convert losslessly to `RunUnknownEvent(message_type="")`; it SHALL NOT fail at the raw decode boundary.

#### Scenario: Complete upstream message decodes
- **WHEN** raw JSON contains every approved task-message field including nested tool input
- **THEN** `RunMessage` preserves each field, parses the timestamp, snapshots nested input immutably, and can be used as a stable raw event payload

#### Scenario: Sparse message decodes
- **WHEN** a valid text or error payload omits inapplicable tool, input, output, issue, and timestamp fields
- **THEN** those fields decode as `None` without inventing identifiers, roles, or empty structured values

#### Scenario: Blank type remains lossless
- **WHEN** a structurally valid raw message has `type=""`
- **THEN** `RunMessage` decoding succeeds with the blank string preserved and semantic conversion yields `RunUnknownEvent(message_type="")` retaining that raw message

#### Scenario: Legacy constructor fields are removed
- **WHEN** a caller constructs `RunMessage` with `id`, `run_id`, or `role`
- **THEN** construction fails and migration documentation directs the caller to `task_id`, `seq`, and `type`

### Requirement: Semantic event types are public and narrowable
The root `multica_py` package SHALL export `RunEvent`, `RunTextEvent`, `RunThinkingEvent`, `RunToolStartedEvent`, `RunToolFinishedEvent`, `RunErrorEvent`, `RunStatusChangedEvent`, and `RunUnknownEvent`. These immutable keyword-only types SHALL support `isinstance`, structural pattern matching, and strict static type narrowing without `Any`; provider-controlled message and run-status strings SHALL remain open strings. Every message-backed concrete class SHALL narrow `sequence` to `int` and `raw_message` to `RunMessage`, while `RunStatusChangedEvent` SHALL narrow `sequence`, `created_at`, and `raw_message` to literal `None`. The concrete semantic fields SHALL be exactly `text: str | None`, `thinking: str | None`, `tool: str | None` with `input: Mapping[str, JsonValue] | None` or `output: str | None`, `error: str | None`, `message_type: str`, and status `previous_status: str | None`, `status: str`, `observed_at: datetime`; absent optional message payload fields SHALL remain `None`.

#### Scenario: Root imports support pattern matching
- **WHEN** a user imports semantic run events from `multica_py` and matches an event by concrete class
- **THEN** the class-specific fields are available with precise annotations and no raw dictionary parsing

#### Scenario: Message and status variants narrow shared fields
- **WHEN** static analysis narrows a `RunEvent` to a message-backed class or `RunStatusChangedEvent`
- **THEN** the message variant exposes `sequence: int` and `raw_message: RunMessage`, while the status variant exposes `sequence=None`, `created_at=None`, and `raw_message=None`

#### Scenario: Future strings remain accepted
- **WHEN** upstream returns a new message type or run status string
- **THEN** model decoding succeeds and the string is preserved rather than rejected by a closed enum

### Requirement: Async streaming follows the SDK execution model
This change SHALL NOT add `stream_events_async`, `run_async`, an async client, a thread bridge, or a second command transport. Documentation SHALL state that asynchronous event streaming becomes applicable only when the SDK adopts an end-to-end asynchronous command execution model.

#### Scenario: Public surface remains consistently synchronous
- **WHEN** the SDK public API is inspected after this change
- **THEN** `TaskRun.stream_events()` is present and no isolated async streaming method or hidden worker thread is present

### Requirement: Typed issue activity preserves reviewed CLI projections
The typed issue API SHALL preserve reviewed assignee, usage, and task-run projections returned by supported Multica CLI versions. Missing optional legacy fields SHALL retain documented compatibility defaults, while present reviewed fields SHALL NOT silently become `None` or `0`.

#### Scenario: Scalar issue assignee is preserved
- **WHEN** an issue response contains matching non-null `assignee_id` and `assignee_type` scalar fields without a nested assignee
- **THEN** the public issue assignee contains that identifier and type

#### Scenario: Nested legacy assignee is preserved
- **WHEN** an issue response contains the supported nested assignee projection without scalar assignee fields
- **THEN** the public issue assignee contains the nested identifier and type

#### Scenario: Matching assignee projections agree
- **WHEN** an issue response contains nested and scalar assignee projections with the same identifier and type
- **THEN** the public issue assignee contains that common value

#### Scenario: Conflicting assignee projections fail closed
- **WHEN** nested and scalar assignee projections disagree or only one member of the scalar pair is present
- **THEN** decoding raises `OutputShapeError` and does not select one projection silently

#### Scenario: Current issue usage categories are preserved
- **WHEN** issue usage JSON contains task or run count plus input, output, cache-read, and cache-write token counts
- **THEN** every present count is exposed separately with its exact integer value and cache-read is not silently folded into an undocumented total

#### Scenario: Legacy issue usage remains decodable
- **WHEN** a supported legacy usage response contains only legacy fields
- **THEN** those fields retain their documented values and absent current fields use documented optional compatibility defaults rather than fabricated measurements

#### Scenario: Current task-run context is preserved
- **WHEN** an issue run response contains reviewed runtime, work directory, privacy-safe relative work directory, result, or failure fields
- **THEN** the public typed task run exposes every present reviewed field without leaking a private wire model
