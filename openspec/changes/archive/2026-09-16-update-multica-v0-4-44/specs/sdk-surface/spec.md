## ADDED Requirements

### Requirement: Comment tombstones preserve strict deletion presence
The SDK SHALL expose `Comment.deleted_at: datetime.datetime | None = None` on
the existing immutable bound comment class. Private wire decoding SHALL accept
omission or a valid timestamp, map only omission to public `None`, and reject
explicit null, malformed timestamps, and wrong JSON types. Add, reply, direct
list, flat list, thread list, and recent-thread comment paths SHALL use the same
wire policy.

#### Scenario: Live comment omission remains compatible
- **WHEN** a live baseline or target comment omits `deleted_at`
- **THEN** the public comment has `deleted_at=None` and preserves all existing identity, content, author, thread, time, and revision fields

#### Scenario: Tombstone timestamp and descendants are preserved
- **WHEN** a deleted target comment contains empty content, a valid `deleted_at` timestamp, and retained replies
- **THEN** the comment preserves the timestamp and metadata, the empty body remains lossless, and its replies remain reachable in the original thread

#### Scenario: Empty content alone is not deletion
- **WHEN** a structurally valid comment has empty content and omits `deleted_at`
- **THEN** the SDK exposes `body=""` and `deleted_at=None` without inferring a tombstone

#### Scenario: Invalid deletion time fails closed
- **WHEN** `deleted_at` is null, malformed, numeric, boolean, an array, or an object
- **THEN** decoding raises `OutputShapeError` rather than reporting a live comment or fabricated time

### Requirement: Issue lifecycle retains the legacy public projection
The SDK SHALL retain known built-in `IssueStatus` values and open custom status
strings. For target custom statuses, public `status_category` SHALL project
unstarted, started, done, and closed phases to `todo`, `in_progress`, `done`,
and `closed` respectively. Built-in keys SHALL retain their established
category. Projection omission SHALL remain distinguishable from a present
value, present `status_name` SHALL remain a non-null string, and malformed
category or name values SHALL fail closed.

#### Scenario: Custom phases project to legacy categories
- **WHEN** target issue fixtures contain custom status keys in unstarted, started, done, and closed phases
- **THEN** `status` preserves each custom key and `status_category` is respectively `todo`, `in_progress`, `done`, and `closed`

#### Scenario: Built-in status keys retain identity
- **WHEN** target issue fixtures contain each approved built-in status key
- **THEN** the existing enum/open-string normalization and corresponding legacy category remain unchanged

#### Scenario: Partial rows preserve omission
- **WHEN** a valid partial issue row omits `status_category` or `status_name`
- **THEN** projection presence remains missing rather than being fabricated from status spelling

#### Scenario: Malformed lifecycle projection fails closed
- **WHEN** a present category or status name is null or has a non-string type not approved by its wire contract
- **THEN** decoding raises `OutputShapeError`

### Requirement: Triage parent updates are presence-sensitive and atomic
Unbound and bound issue update forms SHALL preserve `Unset` as omission and
`None` as explicit parent clear. For a Triage entry, any present parent update,
including same value, explicit null, or a foreign value, SHALL surface the
standard HTTP 400 SDK error with code `issue_in_triage` and message, and SHALL
perform no partial mutation. Ordinary issues SHALL retain parent omit, set, and
clear behavior.

#### Scenario: Triage omission remains allowed
- **WHEN** a Triage update changes only approved non-parent fields and leaves `parent_id=Unset`
- **THEN** complete argv omits `--parent` and the server applies the update according to its ordinary non-parent rules

#### Scenario: Every present Triage parent form is rejected
- **WHEN** a Triage update supplies the same parent, a foreign parent, or `parent_id=None`
- **THEN** the SDK raises the standard error preserving code `issue_in_triage` and performs no fallback request

#### Scenario: Rejected combined update is atomic
- **WHEN** a rejected Triage parent update also supplies title, description, priority, assignee, or project changes
- **THEN** an authoritative refetch shows every field unchanged

#### Scenario: Ordinary issues retain set and clear
- **WHEN** an ordinary issue omits, sets, changes, or explicitly clears `parent_id`
- **THEN** exact argv and resulting parent state preserve the existing `Unset`/value/`None` contract
