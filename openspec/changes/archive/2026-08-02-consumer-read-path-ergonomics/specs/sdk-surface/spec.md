## ADDED Requirements

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

## MODIFIED Requirements

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
