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
The SDK SHALL accept `offset` and `project_id` on `IssueListFilter`, SHALL forward them as the upstream `--offset` and `--project` flags only when non-`None` (and `offset` nonnegative), SHALL return a typed `IssueListPage` from `IssueResource.list` carrying the listed issues and the pagination metadata (`has_more`, `limit`, `offset`, `total`) that the upstream `issue list --output json` response returns, and SHALL expose the per-issue identity and hierarchy scalar fields (`created_at`, `parent_id` renamed from `parent_issue_id`, `project_id`, `creator_id`, `creator_type`) on `IssueSummary`.

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
- **THEN** the returned object is an instance of `multica_py.models.issues.IssueListPage`.

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
supports machine, and delete supports cascade.

#### Scenario: D15–D17 discovery is exact
- **WHEN** public resources and the approved contract are inspected
- **THEN** every approved D15–D17 symbol resolves with its approved signature,
  no removed legacy or daemon-only checkout symbol resolves, and each supported
  method has exactly one canonical transport vector

### Requirement: Unsupported surface migration
The SDK MUST publish an alpha migration mapping for every unsupported or
renamed public surface changed by this roadmap.

#### Scenario: Migration table is complete
- **WHEN** release documentation is reviewed
- **THEN** it maps legacy attachment, user, repository, runtime, autopilot, agent skill, skill file, issue label/children/metadata, rerun/cancel, run-message, and avatar surfaces to the supported replacement or explicitly states that no CLI-backed replacement exists

#### Scenario: Unsupported service replacements are exact
- **WHEN** migration documentation is inspected
- **THEN** it specifies `attachments.list` removed; attachment upload/download signatures from D14; `users.list/get` replaced by `profile_get/profile_update`; `repositories.get` removed in favor of URL/ref list/add/remove/checkout; `runtimes.get` removed; `autopilots.run` renamed `trigger`; and `autopilots.get_run` replaced by history-page selection

