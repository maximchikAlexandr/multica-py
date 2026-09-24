## ADDED Requirements

### Requirement: Issues expose a narrow duplicate snapshot
Supported issue decoding SHALL expose
`duplicate_of: DuplicateIssueReference | None` on the canonical immutable
`Issue` model. `DuplicateIssueReference` SHALL contain exactly `id`,
`identifier`, `title`, and open-string `status`; it SHALL NOT be client-bound or
provide relation or mutation methods. Legacy omission and explicit null SHALL
decode to `None`, while wire presence SHALL remain distinguishable. A present
malformed object SHALL fail strict typed decoding.

#### Scenario: Valid duplicate snapshot is preserved everywhere
- **WHEN** list, get, create, update, children, search, or a bound operation returns a valid `duplicate_of` object
- **THEN** all four fields are preserved in `DuplicateIssueReference` without hydration and existing pagination, labels, metadata, and properties remain unchanged

#### Scenario: Legacy and null responses remain compatible
- **WHEN** `duplicate_of` is omitted by a legacy response or is explicitly null
- **THEN** public `Issue.duplicate_of` is `None` and presence-aware contract evidence distinguishes omission from null

#### Scenario: Malformed duplicate response fails at the protocol boundary
- **WHEN** a present duplicate object is missing a required member or contains a wrong member type
- **THEN** strict decoding raises the existing output/protocol error and does not synthesize a partial issue

#### Scenario: Missing original and status changes remain snapshots
- **WHEN** the original issue becomes unavailable or changes status after the duplicate response was produced
- **THEN** the SDK returns only the nullable server-provided snapshot and performs no lookup or local status inference

### Requirement: Duplicate list projection is a governed field
`IssueListFilter.fields` and the direct `fields` keyword SHALL accept
`duplicate_of` as a legal target projection while retaining tuple type,
whitespace, unknown-field, and duplicate-field validation. The field SHALL map
only to the existing comma-separated `--fields` binding.

#### Scenario: Duplicate projection emits exact argv
- **WHEN** issue list receives `fields=("id", "duplicate_of")`
- **THEN** it emits exactly one `--fields id,duplicate_of` argument and decodes the returned snapshot through the canonical issue adapter

#### Scenario: Existing field validation remains closed
- **WHEN** fields are not a tuple, contain a non-string, blank or unknown member, or repeat `duplicate_of`
- **THEN** command construction fails locally before transport with the existing validation category

### Requirement: Task projections expose read-only supplement metadata
Existing `AgentTask` and `TaskRun` projections SHALL expose optional open-string
`supplement_capability`, ordered `supplement_comment_ids`, and optional boolean
`can_supplement`. Omitted capability and permission SHALL decode to `None`;
omitted or explicit-empty IDs SHALL expose `()` while wire presence distinguishes
them; explicit false permission SHALL remain `False`. Existing task usage,
result, error, failure, cancellation, issue-state delta, ordering, and
serialization behavior SHALL remain unchanged.

#### Scenario: Present task metadata round-trips on both operations
- **WHEN** `agents.tasks` or `issues.runs` returns an open capability string, ordered comment IDs, and true or false permission
- **THEN** the corresponding `AgentTask` or `TaskRun` preserves every value and ID order exactly

#### Scenario: Legacy omission remains compatible
- **WHEN** any supplement member is omitted by a legacy row
- **THEN** defaults remain compatible and presence metadata records the omitted state rather than inventing server support

#### Scenario: Malformed supplement metadata fails strictly
- **WHEN** capability is not a string or null, IDs are not an array of strings, or permission is not a boolean or null
- **THEN** strict decoding raises the existing output/protocol error on both task paths

### Requirement: Issue create accepts typed ordered property assignments
`IssueResource.create` and `create_command`, including project-bound delegates,
SHALL expose `properties: tuple[IssuePropertyAssignment, ...] = ()` with eager
and command signature parity. Each immutable assignment SHALL contain a nonblank
property name or UUID reference and a string value. Valid assignments SHALL emit
one repeatable `--property <reference>=<value>` argument in caller order on the
single create command. Non-tuples, wrong item types, non-string values, and
non-string or blank references SHALL fail before transport. Empty string
values, `__none__`, and comparison spellings SHALL be emitted unchanged so the
pinned CLI owns their value-grammar validation and rejection.

#### Scenario: All server property types use one stable SDK mapping
- **WHEN** callers supply text, URL, number, date, checkbox, select,
  multi-select, actor, or multi-actor values as assignments
- **THEN** the SDK preserves each reference and value in ordered `--property` argv and the pinned CLI performs type-specific canonicalization and atomic binding

#### Scenario: Name and UUID references are both accepted
- **WHEN** an assignment uses a nonblank property display name or definition UUID
- **THEN** the SDK emits that reference without a catalog lookup and returns the issue snapshot decoded by the existing issue adapter

#### Scenario: Invalid stable structures perform no I/O
- **WHEN** the properties collection is not a tuple, an assignment has the wrong item type, a reference is not a string or is blank, or a value is not a string
- **THEN** construction raises `TypeError` or `ValueError` before transport and no partial issue exists

#### Scenario: CLI-owned value and catalog failures remain atomic
- **WHEN** the CLI rejects an empty string value, `__none__`, a comparison spelling, a duplicate, unresolved, archived, type-invalid, capability-incompatible, or snapshot-mismatched property
- **THEN** the SDK surfaces the reviewed command failure and never falls back to post-create property mutation

#### Scenario: Existing label workflow remains explicit
- **WHEN** a caller supplies both atomic properties and legacy `label_ids`
- **THEN** properties remain on the create step and label additions retain their documented post-create steps and partial-label failure semantics

### Requirement: Supplement and duplicate mutations remain absent
The SDK SHALL expose the new supplement and duplicate data only through the
approved read projections. It SHALL NOT add task-supplement operations,
supplement comment receipts, duplicate mutation methods, issue timeline methods,
or a create-time attachment input.

#### Scenario: Response adaptation does not create mutation APIs
- **WHEN** the public package, resources, bound entities, operation inventory, and generated symbols are inspected
- **THEN** the new read fields exist and every excluded mutation, timeline, receipt, and attachment symbol remains absent
