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

### Requirement: Issue list pagination and summary identity decoding
The SDK SHALL accept `offset`, `project_id`, and ordered typed `metadata`
predicates on `IssueListFilter`. It SHALL forward `offset` and `project_id` as
the upstream `--offset` and `--project` flags only when non-`None` (and `offset`
nonnegative). It SHALL forward each metadata predicate as a repeatable
`--metadata key=<json-scalar>` pair in caller order, using the existing
`IssueMetadataItem` and `MetadataValue` public types. The handwritten adapter
SHALL encode values with `json.dumps(value, ensure_ascii=False,
separators=(",", ":"), allow_nan=False)`. Predicate keys SHALL be nonblank,
unique within the filter, and SHALL NOT contain `=`. Invalid keys, duplicate
keys, and non-finite floats SHALL raise `ValueError` before transport.
`IssueSummaryWire` SHALL decode
`labels: tuple[LabelData, ...] | msgspec.UnsetType = msgspec.UNSET` and
`metadata: dict[str, MetadataValue] | msgspec.UnsetType = msgspec.UNSET`, mapping
them to `IssueSummary.label_names` and `IssueSummary.metadata_snapshot` with
omitted values normalized to `()`. The SDK SHALL return a typed `IssueListPage` from `IssueResource.list`, carrying
immutable `IssueSummary` values and the upstream pagination metadata
(`has_more`, `limit`, `offset`, `total`). Each summary SHALL expose identity and
hierarchy scalar fields (`created_at`, `parent_id` renamed from
`parent_issue_id`, `project_id`, `creator_id`, `creator_type`) plus authoritative
`label_names` and `metadata_snapshot` from the list response. The list path
SHALL NOT fabricate a full bound `IssueEntity`; callers SHALL use
`issues.get(summary.id)` when full state or bound behavior is required.

#### Scenario: List with offset emits --offset
- **WHEN** `IssueResource.list` is called with `IssueListFilter(offset=20)`
- **THEN** the CLI argv includes `--offset 20`.

#### Scenario: List without offset omits --offset
- **WHEN** `IssueResource.list` is called with `IssueListFilter()` (offset is `None`)
- **THEN** the CLI argv does not include `--offset`.

#### Scenario: List with project emits --project
- **WHEN** `IssueResource.list` is called with `IssueListFilter(project_id="pr_001")`
- **THEN** the CLI argv includes `--project pr_001`.

#### Scenario: List without project omits --project
- **WHEN** `IssueResource.list` is called with `IssueListFilter()` (project_id is `None`)
- **THEN** the CLI argv does not include `--project`.

#### Scenario: Negative offset is rejected before invocation
- **WHEN** `IssueResource.list` is called with `IssueListFilter(offset=-1)`
- **THEN** a `ValueError` is raised before any CLI invocation, naming `offset`.

#### Scenario: Pagination metadata round-trips into IssueListPage
- **WHEN** the upstream `issue list --output json` response contains `{"issues":[...],"has_more":true,"limit":50,"offset":20,"total":137}`
- **THEN** the decoded `IssueListPage` exposes `has_more == True`, `limit == 50`, `offset == 20`, `total == 137`, and `issues` is the decoded `tuple[IssueSummary, ...]`.

#### Scenario: Omitted pagination metadata decodes backward-compatibly
- **WHEN** an older CLI response omits `has_more`, `limit`, `offset`, and `total` (only `issues` present)
- **THEN** the decoded `IssueListPage` exposes `has_more == False`, `limit is None`, `offset is None`, `total is None`, and `issues` is decoded from the present array.

#### Scenario: Empty page decodes
- **WHEN** the upstream response is `{"issues":[],"has_more":false,"limit":50,"offset":0,"total":0}`
- **THEN** the decoded `IssueListPage.issues` is `()` and `has_more == False`.

#### Scenario: Summary scalar fields round-trip
- **WHEN** an issue in the `issues` array contains `created_at`, `parent_issue_id`, `project_id`, `creator_id`, `creator_type`
- **THEN** the decoded `IssueSummary` exposes `created_at` as `datetime.datetime | None`, `parent_id` (renamed from `parent_issue_id`), `project_id`, `creator_id`, and `creator_type`, each defaulting to `None` when absent.

#### Scenario: Summary without scalar fields decodes backward-compatibly
- **WHEN** an issue in the `issues` array omits `created_at`, `parent_issue_id`, `project_id`, `creator_id`, `creator_type`
- **THEN** the decoded `IssueSummary` exposes `created_at is None`, `parent_id is None`, `project_id is None`, `creator_id is None`, `creator_type is None`.

#### Scenario: IssueListPage is the public return type
- **WHEN** `IssueResource.list` is called
- **THEN** the returned object is an instance of `multica_py.models.issues.IssueListPage` and not a `BoundIssueListPage`.

#### Scenario: Metadata predicates emit exact repeated flags
- **WHEN** `IssueResource.list` receives metadata predicates `external_key="42"`, `ready=true`, `attempt=2`, and `finished_at=null`
- **THEN** argv contains ordered pairs `--metadata external_key="42"`, `--metadata ready=true`, `--metadata attempt=2`, and `--metadata finished_at=null`

#### Scenario: Metadata predicate order is preserved
- **WHEN** two valid metadata predicates are supplied in a defined tuple order
- **THEN** their repeatable `--metadata` pairs occur in that same order

#### Scenario: Metadata predicate keys are validated before transport
- **WHEN** a metadata predicate has a blank key or a key containing `=`
- **THEN** a `ValueError` names the invalid metadata key and no CLI invocation occurs

#### Scenario: Duplicate metadata predicate keys are rejected before transport
- **WHEN** two metadata predicates have the same key
- **THEN** a `ValueError` names the duplicate key and no CLI invocation occurs

#### Scenario: Non-finite metadata floats are rejected before transport
- **WHEN** a metadata predicate value is `nan`, `inf`, or `-inf`
- **THEN** `json.dumps(..., allow_nan=False)` causes a `ValueError` before any CLI invocation

#### Scenario: List summary preserves labels and metadata
- **WHEN** an issue-list row contains labels and metadata
- **THEN** its `IssueSummary.label_names` and `IssueSummary.metadata_snapshot` preserve those decoded values

#### Scenario: Omitted summary collections decode as empty tuples
- **WHEN** an issue-list row omits labels and metadata
- **THEN** its `IssueSummary.label_names == ()` and `IssueSummary.metadata_snapshot == ()`

#### Scenario: List never fabricates a full issue entity
- **WHEN** an issue-list row is decoded
- **THEN** no placeholder full-issue fields or bound relation state are constructed from the summary

### Requirement: Attachment byte-oriented upload and download
The SDK SHALL expose
`upload(path: Path, *, task_id: str | None = None) -> AttachmentResult`,
`download(attachment_id: str, *, output_dir: Path) -> Path`,
`upload_bytes(filename: str, payload: bytes, *, task_id: str | None = None) -> AttachmentResult`,
and `download_bytes(attachment_id: str) -> bytes`. `attachments.list` and the
legacy issue-id upload signature SHALL be absent. Byte helpers MUST delegate to
file methods, preserve filename/binary/empty content, clean temporary files on
success/failure, and propagate the underlying SDK exception.

#### Scenario: File upload emits pinned argv
- **WHEN** upload is called with a path and optional task ID
- **THEN** argv is `attachment upload <path> [--task <id>] --output json` and no issue ID or `--file` flag is emitted

#### Scenario: File download emits pinned argv
- **WHEN** download is called with attachment ID and output directory
- **THEN** argv is `attachment download <id> --output-dir <dir> --output json` and the returned path is the decoded downloaded path

#### Scenario: upload_bytes preserves the supplied filename
- **WHEN** upload_bytes receives empty or binary bytes and a safe filename
- **THEN** it delegates through a temporary file with the exact filename/task ID and returns the file upload result

#### Scenario: download_bytes returns the file content as bytes
- **WHEN** download_bytes delegates to a temporary output directory
- **THEN** it reads and returns the exact downloaded bytes, including empty content

#### Scenario: Empty payload uploads and returns the decoded result
- **WHEN** `upload_bytes` receives empty bytes
- **THEN** it preserves the empty payload and returns the decoded upload result

#### Scenario: Empty attachment downloads as empty bytes
- **WHEN** the downloaded attachment is empty
- **THEN** `download_bytes` returns `b""`

#### Scenario: Temporary files are removed after success
- **WHEN** either byte helper succeeds
- **THEN** its temporary directory is removed

#### Scenario: Temporary files are removed when the underlying CLI operation fails
- **WHEN** the underlying operation raises
- **THEN** the temporary directory is removed and the original exception type propagates

#### Scenario: Path separators and empty values are rejected
- **WHEN** filename or attachment ID is empty, contains a separator, or contains `..`
- **THEN** `ValueError` identifies the parameter before filesystem or transport access

#### Scenario: Existing upload and download behavior is unchanged
- **WHEN** callers use the supported path-based upload and download methods
- **THEN** their governed argv, results, and error behavior remain unchanged

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

### Requirement: Unsupported surface migration
The SDK MUST publish an alpha migration mapping for every unsupported, renamed,
or intentionally narrowed public surface changed by this roadmap and the
consumer read-path change.

#### Scenario: Migration table is complete
- **WHEN** release documentation is reviewed
- **THEN** it maps legacy attachment, user, repository, runtime, autopilot, agent skill, skill file, issue label/children/metadata, rerun/cancel, run-message, avatar, direct issue-list, and issue-list relation surfaces to the supported replacement or explicitly states that no CLI-backed replacement exists

#### Scenario: Unsupported service replacements are exact
- **WHEN** migration documentation is inspected
- **THEN** it specifies `attachments.list` remains removed; issue-result discovery uses a fresh `issues.get(issue_id).attachments` snapshot and `download_bytes`; `users.list/get` remains replaced by profile operations while workspace registry reconciliation uses `workspace.members` with `user_id`; `repositories.get` is removed in favor of URL/ref list/add/remove/checkout; `runtimes.get` is removed; `autopilots.run` is renamed `trigger`; `autopilots.get_run` is replaced by history-page selection; and list callers use `IssueSummary` plus explicit `issues.get(summary.id)` when a full issue is needed

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

### Requirement: Dual input convention for request-bearing resource methods

The SDK SHALL support two equivalent public calling conventions on every
in-scope request-bearing resource method: (1) a single positional request
object argument, and (2) the request object's fields passed directly as
keyword-only arguments. The two conventions SHALL be mutually exclusive within a
single call.

The direct keyword form SHALL be the primary form presented in documentation.
The request-object form SHALL remain available for reuse, validation, storage,
and cross-layer assembly. No public method SHALL be renamed, split, or added to
distinguish the two forms — both SHALL use the same domain method.

In-scope methods are exactly:
`projects.create`, `projects.update`, `agents.create`, `agents.update`,
`skills.create`, `skills.update`, `issues.create`, `issues.update`,
`issues.assign`, `issues.reorder`, `runtimes.update`,
`project_resources.add_local_directory`,
`project_resources.update_local_directory`, and `users.profile_update`.

Request-bearing methods not listed above are intentionally out of scope and
SHALL retain their existing request-object-only signature unchanged.

#### Scenario: Direct keyword arguments build the request and invoke the CLI

- **WHEN** an in-scope method is called with keyword-only fields matching the
  request model's field names, types, defaults, and optional-ness
- **THEN** the SDK constructs the equivalent request object internally and
  emits the exact same argv, transport method, stdin, and timeout as the
  equivalent request-object call.

#### Scenario: Request object call remains supported and unchanged

- **WHEN** an in-scope method is called with a single positional request
  object
- **THEN** the SDK emits the exact same argv, transport method, stdin, and
  timeout it emits today, with no behavioral change.

#### Scenario: Both forms return the same type

- **WHEN** the same in-scope operation is invoked via the direct keyword form
  and via the request-object form with equivalent inputs
- **THEN** both calls return values of the same public type (e.g. `Project`,
  `IssueEntity`, `AgentEntity`, `SkillEntity`, `RuntimeUpdateResult`,
  `ProjectResourceRecord`, `UserProfile`).

#### Scenario: Direct fields are keyword-only

- **WHEN** an in-scope method is called with positional arguments beyond the
  accepted single request-object positional slot
- **THEN** the call raises `TypeError` at call time, before any CLI
  invocation, because the direct fields are keyword-only.

#### Scenario: Mixed input is rejected before invocation

- **WHEN** an in-scope method is called with both a positional request object
  and one or more keyword fields
- **THEN** the SDK raises `TypeError` with the message
  `Pass either a request object or keyword arguments, not both.` before any
  CLI invocation.

#### Scenario: Neither request object nor direct fields raises TypeError

- **WHEN** an in-scope method is called with no positional request object and
  no keyword fields (beyond any required positional identifiers the method
  already takes, such as `project_id` on `projects.update`)
- **THEN** the SDK raises `TypeError` indicating the missing required
  request input, before any CLI invocation.

#### Scenario: Direct keyword form preserves request validation

- **WHEN** the direct keyword form supplies values that would violate the
  request model's `__post_init__` validation (e.g. blank `project_id` on
  `IssueCreateRequest`, non-exactly-one target on `IssueAssignmentRequest` or
  `IssueReorderRequest`, blank `daemon_id` on
  `ProjectResourceAddLocalDirectoryRequest`, blank `local_path` on
  `ProjectResourceUpdateLocalDirectoryRequest`)
- **THEN** the same `ValueError` the request object raises is raised from the
  direct form too, before any CLI invocation. A relative `local_path` on
  `ProjectResourceAddLocalDirectoryRequest` is NOT such a case: that
  request's `__post_init__` only validates `daemon_id`, and the call site
  normalizes `local_path` via `os.path.abspath` in both forms identically.

#### Scenario: Update-style presence semantics are identical in both forms

- **WHEN** an update-style in-scope method (`projects.update`,
  `users.profile_update`) is called via the direct keyword form with an
  omitted field, an explicit `None`, or an explicit `Unset` where the request
  model distinguishes them
- **THEN** the resulting argv matches the equivalent request-object call bit
  for bit, including the omission-vs-null-vs-unset distinction.

#### Scenario: Static type checkers understand both forms

- **WHEN** `uv run mypy src` and `uv run mypy tests` are run against the
  dual-input method signatures
- **THEN** both pass and a direct keyword call type-checks with the field
  names and types advertised by the request model.

#### Scenario: IDE autocomplete surfaces direct fields

- **WHEN** a caller starts a direct keyword call on an in-scope method
- **THEN** the `@overload` signatures expose the request model's field names
  as keyword-only parameters with their declared types and defaults.

#### Scenario: Request-object methods out of scope are unchanged

- **WHEN** an out-of-scope request-bearing method
  (`issue_comments` list overloads, `issue_metadata.query`,
  `issue_metadata.set_typed`) is inspected
- **THEN** its signature, argv, and behavior are unchanged and no direct
  keyword overload is added.

### Requirement: Dual input convention documentation default

The SDK documentation SHALL present the direct keyword form as the default
example for every in-scope method and SHALL document the request-object form as
the advanced/reusable alternative, explaining when request objects are useful
(reuse, validation, cross-layer assembly, complex/mutually-exclusive inputs).

#### Scenario: Docs show direct keyword form first

- **WHEN** the resource method documentation for an in-scope method is
  reviewed
- **THEN** the primary example uses the direct keyword form and a secondary
  example shows the request-object form labeled as the reusable/advanced
  alternative.

#### Scenario: Docs explain when request objects remain valuable

- **WHEN** the documentation is reviewed
- **THEN** it states that request objects are useful for reuse, validation,
  storage, and cross-layer assembly, and that out-of-scope request objects
  remain the only form for their methods.

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

### Requirement: Issue search preserves its API and decodes v0.4.20 results

`IssueResource.search(query) -> tuple[IssueSummary, ...]` and
`search_command(query) -> Command[tuple[IssueSummary, ...]]` SHALL retain their
existing public signatures and exact `issue search <query> --output json`
mapping. The decoder SHALL accept the `v0.4.20` object envelope containing an
`issues` array and SHALL continue accepting the legacy top-level issue array.
`IssueSummary` SHALL expose `match_source: str | None = None`; the field SHALL
remain an open string, SHALL preserve values returned by upstream, and SHALL
default to `None` when omitted. Envelope pagination/count metadata is not a new
public return type in this change.

#### Scenario: v0.4.20 search envelope returns the existing tuple
- **WHEN** `issue search --output json` returns `{"issues":[...],"total":1}`
- **THEN** `issues.search()` returns a one-item immutable tuple of `IssueSummary` rather than exposing a new result wrapper

#### Scenario: Search match source is preserved
- **WHEN** search rows report `match_source` values `title`, `description`, or `comment`
- **THEN** each corresponding `IssueSummary.match_source` preserves the returned string

#### Scenario: Number-shaped query remains a normal query
- **WHEN** `issues.search("412")` returns a number-only match whose upstream fallback source is `comment`
- **THEN** argv contains the exact query `412` and the returned summary exposes `match_source == "comment"`

#### Scenario: Missing match source is backward-compatible
- **WHEN** an envelope or legacy array row omits `match_source`
- **THEN** the row decodes successfully with `IssueSummary.match_source is None`

#### Scenario: Unknown future match source is readable
- **WHEN** a future CLI returns an unrecognized nonempty `match_source` string
- **THEN** decoding succeeds and preserves that string without an SDK enum update

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

