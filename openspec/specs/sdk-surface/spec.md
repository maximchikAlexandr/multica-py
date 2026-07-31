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
The SDK SHALL decode the executor fields the Multica CLI already returns on `agent get`, `agent list`, and `squad get`, and SHALL expose a typed `squad member list` operation.
#### Scenario: Agent skills decode as typed AgentSkill objects
- **WHEN** the CLI response for `agent get` / `agent list` contains `"skills": [{"id":"sk_1","name":"openspec-propose","enabled":true}]`
- **THEN** the decoded `Agent.skills` is `tuple[AgentSkill, ...]` with `AgentSkill(id="sk_1", name="openspec-propose", enabled=True)`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Agent with no skills decodes to empty tuple
- **WHEN** the CLI response omits `skills` or returns `"skills": []`
- **THEN** the decoded `Agent.skills` is `()`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Agent archived_at null decodes to None
- **WHEN** the CLI response contains `"archived_at": null` or omits the key
- **THEN** the decoded `Agent.archived_at` is `None`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Agent archived_at RFC3339 decodes to datetime
- **WHEN** the CLI response contains `"archived_at": "2026-07-28T11:47:17Z"`
- **THEN** the decoded `Agent.archived_at` is a `datetime.datetime` equal to `datetime.datetime(2026, 7, 28, 11, 47, 17, tzinfo=datetime.timezone.utc)`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Assigned skills read returns typed AgentSkill
- **WHEN** `client.agents.skills.list("a1")` is called and the CLI returns `{"id":"sk_1","name":"openspec-propose","enabled":true}`
- **THEN** the result is `tuple[AgentSkill, ...]` with `AgentSkill(id="sk_1", name="openspec-propose", enabled=True)`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad leader_id decodes
- **WHEN** the CLI response for `squad get` / `squad list` contains `"leader_id": "leader-agent-id"`
- **THEN** the decoded `Squad.leader_id` is `"leader-agent-id"`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad leader_id absent decodes to None
- **WHEN** the CLI response omits `leader_id` or returns `"leader_id": null`
- **THEN** the decoded `Squad.leader_id` is `None`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad archived_at null decodes to None
- **WHEN** the CLI response contains `"archived_at": null` or omits the key
- **THEN** the decoded `Squad.archived_at` is `None`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad archived_at RFC3339 decodes to datetime
- **WHEN** the CLI response contains `"archived_at": "2026-07-28T11:47:17Z"`
- **THEN** the decoded `Squad.archived_at` is a `datetime.datetime` equal to `datetime.datetime(2026, 7, 28, 11, 47, 17, tzinfo=datetime.timezone.utc)`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Existing minimal squad fixture still decodes
- **WHEN** a fixture encodes `Squad(id="s1", name="S")` with no `leader_id` or `archived_at`
- **THEN** it decodes back to a `Squad` with `leader_id is None` and `archived_at is None` and `member_count == 0`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad member list emits exact argv
- **WHEN** `client.squads.members.list("sq_1")` is called
- **THEN** the transport receives the argv `("squad", "member", "list", "sq_1", "--output", "json")` via `run_bytes`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad member list returns typed members
- **WHEN** `client.squads.members.list("sq_1")` is called and the CLI returns `[{"member_id":"a1","member_type":"agent","role":"architecture-reviewer"}]`
- **THEN** the result is `tuple[SquadMember, ...]` with `SquadMember(member_id="a1", member_type="agent", role="architecture-reviewer")`.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

#### Scenario: Squad member list with multiple roles preserves each
- **WHEN** the CLI returns multiple members with distinct roles
- **THEN** each `SquadMember` preserves its `member_id`, `member_type`, and `role` verbatim, in response order.
<!-- Source IDs: pending — see issue #10 (deferred_owner_decision) -->

Specifically:

- `Agent.skills` SHALL be `tuple[AgentSkill, ...]` where `AgentSkill` is a frozen `msgspec.Struct` with `id: str`, `name: str`, `enabled: bool`.
- `Agent` SHALL decode `archived_at` as `datetime.datetime | None`, where JSON `null` decodes to `None` and an RFC3339 timestamp decodes to a `datetime.datetime`.
- `Squad` SHALL decode `leader_id: str | None = None` and `archived_at: datetime.datetime | None = None`.
- A `SquadMember` model (frozen `msgspec.Struct`, `member_id: str`, `member_type: str`, `role: str`) SHALL decode the `multica squad member list <squad-id> --output json` response.
- `SquadResource` SHALL expose a nested `members` resource whose `list(squad_id)` method returns `tuple[SquadMember, ...]` and emits the argv `("squad", "member", "list", <squad-id>, "--output", "json")`.
- `AgentSkillResource.list` SHALL return `tuple[AgentSkill, ...]` (same typed shape as `Agent.skills`), replacing the previous generic `Skill` decode.

All new scalar fields are additive with `None` defaults so that fixtures and older CLI responses omitting them continue to decode.

### Requirement: Autopilot resource governance and pagination

The SDK MUST govern the autopilot resource operations in the approved contract
and MUST expose pagination metadata on `autopilots.list` and
`autopilots.history`, consistent with the issue-list pagination surface.

#### Scenario: Autopilot list returns AutopilotListPage

- **WHEN** `client.autopilots.list()` is called and the CLI returns
  `{"autopilots":[...],"total":N}`
- **THEN** the result is an `AutopilotListPage` with `total == N` and an
  `autopilots: tuple[Autopilot, ...]` field, not a bare `tuple[Autopilot, ...]`.

#### Scenario: Autopilot history returns AutopilotRunListPage

- **WHEN** `client.autopilots.history("a1", limit=10, offset=20)` is called and
  the CLI returns `{"runs":[...],"total":N}`
- **THEN** the result is an `AutopilotRunListPage` with `total`, `limit`,
  `offset`, and a Python-computed `has_more`.

#### Scenario: Autopilot operations are in the approved contract

- **WHEN** the approved contract operation list is inspected
- **THEN** `autopilots.list`, `autopilots.get`, `autopilots.create`,
  `autopilots.update`, `autopilots.delete`, `autopilots.run`, and
  `autopilots.history` are present with `compatibility` set to
  `intentionally_changed` and a rationale naming the model widening and
  pagination return-type change (and, for `history`, the argv fix to the
  upstream `autopilot runs <id>` subcommand; for `run`, the deferred
  `autopilot trigger <id>` argv divergence).
- **AND** `autopilots.get_run` is NOT present (it stays ungoverned; upstream
  has no single-run fetch subcommand).

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
The SDK SHALL expose `AttachmentResource.upload_bytes(issue_id, filename, payload) -> AttachmentResult` and `AttachmentResource.download_bytes(attachment_id) -> bytes` as convenience wrappers over the existing file-based `upload()` and `download()` methods. The byte methods SHALL NOT duplicate CLI command-building logic, SHALL accept `bytes` (not base64), SHALL preserve the exact filename supplied to `upload_bytes`, SHALL clean up temporary files automatically on both success and failure, SHALL correctly support empty and binary content, SHALL raise the same SDK exception types as the underlying file-based methods, and SHALL leave the existing `upload()` and `download()` behavior unchanged.

#### Scenario: upload_bytes preserves the supplied filename
- **WHEN** `upload_bytes("i1", "manifest.json", b'{"x":1}')` is called
- **THEN** the underlying `upload()` is called with a path whose final component is exactly `manifest.json`, and the returned `AttachmentResult` is the one decoded by `upload()`.

#### Scenario: download_bytes returns the file content as bytes
- **WHEN** `download_bytes("a1")` is called and the underlying `download()` writes a file containing `b'\x00\x01binary'`
- **THEN** the returned value is exactly `b'\x00\x01binary'`.

#### Scenario: Empty payload uploads and returns the decoded result
- **WHEN** `upload_bytes("i1", "empty.bin", b'')` is called
- **THEN** `upload()` is called with a path to a zero-length file named `empty.bin` and the decoded `AttachmentResult` is returned.

#### Scenario: Empty attachment downloads as empty bytes
- **WHEN** `download_bytes("a1")` is called and the underlying `download()` writes a zero-length file
- **THEN** the returned value is `b''`.

#### Scenario: Temporary files are removed after success
- **WHEN** `upload_bytes` or `download_bytes` completes successfully
- **THEN** the temporary directory created for the operation no longer exists on the filesystem after the call returns.

#### Scenario: Temporary files are removed when the underlying CLI operation fails
- **WHEN** the underlying `upload()` or `download()` raises an exception
- **THEN** the exception propagates to the caller (same SDK exception type) and the temporary directory created for the operation no longer exists on the filesystem.

#### Scenario: Path separators and empty values are rejected
- **WHEN** `upload_bytes` is called with a `filename` containing `/` or `\` or `..`, or with an empty string
- **THEN** `ValueError` is raised with a message identifying the parameter.
- **WHEN** `download_bytes` is called with an `attachment_id` containing `/` or `\` or `..`, or with an empty string
- **THEN** `ValueError` is raised with a message identifying the parameter.

#### Scenario: Existing upload and download behavior is unchanged
- **WHEN** `upload(issue_id, file_path)` or `download(attachment_id, output_path)` is called
- **THEN** the argv and return behavior are identical to before this change (no regression in the file-based API).

