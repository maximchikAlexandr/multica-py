## MODIFIED Requirements

### Requirement: Synchronous resource client
The SDK MUST expose one synchronous `MulticaClient` with typed domain resource
services, immutable scalar data snapshots, and explicitly lazy bound entity
relations. Scalar access and passive inspection MUST perform no hidden I/O;
only iteration, `all()`, `page()`, `refresh()`, or `prefetch()` may invoke a
documented governed operation, and models MUST NOT implement Active Record
persistence.

#### Scenario: Scalar access remains passive
- **WHEN** a consumer reads, inspects, compares, logs, hashes, or serializes supported scalar entity data
- **THEN** no subprocess or persistence operation occurs

#### Scenario: Relation consumption is explicit
- **WHEN** a consumer invokes a documented relation load point
- **THEN** only the governed operation and strategy declared for that relation may execute

#### Scenario: Resource calls remain stateless
- **WHEN** a consumer calls a resource method or passively inspects its returned entity
- **THEN** no model performs hidden persistence and only documented explicit load points may perform additional I/O

### Requirement: Public resource surface
The SDK MUST retain every supported public resource method present in the
canonical operation table and MUST remove or replace legacy methods proven
unsupported by the pinned upstream CLI through an intentionally changed
contract decision and documented migration.

#### Scenario: Public methods have canonical rows
- **WHEN** a supported public resource method exists
- **THEN** exactly one canonical operation row covers it

#### Scenario: Unsupported legacy methods do not remain callable
- **WHEN** pinned-source review proves that arbitrary user list/get, repository get, runtime get, attachment list-by-issue, autopilot get-run, or legacy trigger commands have no compatible upstream operation
- **THEN** the public method is removed or replaced and its migration is documented rather than preserved as a misleading callable

### Requirement: Closed public types
Every public scalar snapshot and request/response record MUST be a frozen
immutable `msgspec.Struct` or documented closed primitive. Each bound
`ResourceEntity[*Data]` MUST be a separately typed externally read-only Python
wrapper that privately retains its originating client view; it MUST expose no
public `Any`, MUST NOT be encoded directly by msgspec, and MUST serialize only
through its frozen `to_data()` result. A later resource call returns a new
wrapper rather than mutating an earlier wrapper.

#### Scenario: Structured output stays closed and typed
- **WHEN** structured CLI output is decoded and returned as a bound entity
- **THEN** wire data adapts to frozen `*Data`, the wrapper retains runtime state privately, and `msgspec.encode(entity.to_data())` contains no client, transport, semaphore, or relation state

#### Scenario: Bound wrappers use replacement semantics
- **WHEN** list returns a compact wrapper and get later returns richer data for the same ID
- **THEN** get returns a distinct wrapper with a distinct frozen snapshot and does not enrich the list wrapper in place

## ADDED Requirements

### Requirement: Bound entity and snapshot naming
Participating entity names MUST refer to bound public wrappers; immutable
scalar forms MUST use explicit data/snapshot types, and relation names MUST not
also mean eager scalar collections.

#### Scenario: Conflicting eager names migrate
- **WHEN** `Agent.skills`, `Issue.labels`, `Issue.children`, or `Issue.metadata` is accessed
- **THEN** the name consistently exposes its typed relation while eager data is available only as `AgentData.skill_refs`, `IssueData.label_names`, `IssueData.child_stages`, or `IssueData.metadata_snapshot`

#### Scenario: Autopilot subscriber name migrates
- **WHEN** subscriber data from autopilot get is inspected
- **THEN** eager data is `AutopilotData.subscriber_snapshot` and `Autopilot.subscribers` is `LazyCollection[AutopilotSubscriber]`

#### Scenario: Entity snapshot is explicit
- **WHEN** a consumer calls `entity.to_data()`
- **THEN** the result is the immutable typed scalar snapshot without client runtime state

## MODIFIED Requirements

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

## ADDED Requirements

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
