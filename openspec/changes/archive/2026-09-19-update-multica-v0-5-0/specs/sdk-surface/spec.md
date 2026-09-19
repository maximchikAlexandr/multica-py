## ADDED Requirements

### Requirement: Optimistic comment update API
The SDK SHALL expose eager and lazy `issues.comments.update` operations taking a nonblank comment identifier, text body, and required positive non-boolean `expected_revision`. It SHALL use exactly the CLI text content channel and SHALL preserve the decoded `Comment` response.

#### Scenario: Valid comment update emits exact argv
- **WHEN** a caller updates a comment with body `revised` and revision `3`
- **THEN** the canonical operation vector SHALL pass the comment identifier and body positionally, SHALL pass keyword-only `expected_revision=3`, SHALL emit exactly `issue comment update <id> --content revised --expected-revision 3 --output json`, and SHALL decode the updated comment

#### Scenario: Invalid revision fails before transport
- **WHEN** revision is omitted, zero, negative, boolean, or noninteger
- **THEN** the SDK SHALL raise before CLI execution

#### Scenario: Stale revision remains explicit
- **WHEN** upstream rejects a stale revision
- **THEN** the SDK SHALL preserve the centralized conflict error and SHALL NOT read, merge, or retry automatically

#### Scenario: Update preserves upstream side effects
- **WHEN** an update succeeds
- **THEN** attachments SHALL remain unchanged and upstream mention retrigger semantics SHALL remain observable without SDK suppression

### Requirement: Typed skill labels
The SDK SHALL expose `skills.labels.list/add/remove` with validated nonblank skill and label identifiers, path-safe argv, a resolver fenced to skill labels, typed Label results, and the reviewed remove-refresh fallback.

#### Scenario: Skill labels list and add return typed labels
- **WHEN** list or add succeeds
- **THEN** the SDK SHALL decode the returned label rows without accepting issue-only resolver matches

#### Scenario: Remove refresh succeeds
- **WHEN** removal and the target refresh both succeed
- **THEN** the SDK SHALL return the refreshed typed label page and invalidate a bound skill's cached labels

#### Scenario: Remove refresh fails after detach
- **WHEN** upstream confirms detach but its refresh fails
- **THEN** the SDK SHALL preserve the reviewed detached fallback and SHALL NOT report the mutation as undone

### Requirement: Label resource type and description inputs
The SDK SHALL expose reviewed `issue` and `skill` label resource types, label description output, create resource type and description inputs, list resource-type filtering, and presence-aware update description clearing.

#### Scenario: Create uses explicit defaults
- **WHEN** create omits resource type and description
- **THEN** exact argv SHALL retain the issue resource default and SHALL omit description

#### Scenario: List filters skill labels
- **WHEN** list receives resource type `skill`
- **THEN** exact argv SHALL include `--resource-type skill` and every decoded label SHALL preserve its returned resource type

#### Scenario: Update distinguishes omit set and clear
- **WHEN** description is `Unset`, non-empty, `None`, or empty
- **THEN** the SDK SHALL respectively omit, set, explicitly clear, or explicitly clear `--description` with complete argv evidence

#### Scenario: Invalid resource type fails closed
- **WHEN** a caller supplies an unsupported resource type to a request
- **THEN** validation SHALL fail before transport while unknown future response strings remain decodable under open-response policy

### Requirement: Skill-list label projection
Every bound `Skill` SHALL expose `labels` as `LazyCollection[Label]`. Each `skills.list` item SHALL initialize that collection from its required non-null labels array so empty and populated payloads are available without another transport call. Nested field type/nullability/omission SHALL be enforced. A `skills.get` response that omits labels SHALL retain its prior wire contract and leave the same public collection unloaded until first access.

#### Scenario: Empty and populated list labels preload one public relation
- **WHEN** skill list returns `labels: []` or populated label rows
- **THEN** `Skill.labels` SHALL be `LazyCollection[Label]` preloaded respectively with an empty tuple or typed labels with exact nested values, and its first read SHALL NOT execute another CLI command

#### Scenario: Malformed nested label fails closed
- **WHEN** a nested label has an invalid required field or invalid nullability
- **THEN** decoding SHALL raise `OutputShapeError`

#### Scenario: Detail response leaves the same relation unloaded
- **WHEN** skill detail omits labels under its retained contract
- **THEN** detail decoding SHALL remain valid, `Skill.labels` SHALL still be `LazyCollection[Label]`, and its first read SHALL load only through `skills.labels.list` rather than claiming the list-only field was returned

### Requirement: Presence-correct task issue-state deltas
Task-run and agent-task models SHALL preserve omission, null, empty, and value states for target issue-state delta fields, including title, description, current status, current assignee, known flags, and delta arrays. Failure reasons SHALL remain open strings and SHALL accept `runtime_access_denied`.

#### Scenario: Absent delta differs from known empty
- **WHEN** delta fields are absent versus `known=true` with an empty array
- **THEN** the SDK SHALL expose distinguishable states

#### Scenario: Changed issue state decodes
- **WHEN** title, description, current status, or current assignee changes are present
- **THEN** exact typed values and their wire presence SHALL be preserved

#### Scenario: Failure reason stays open
- **WHEN** failure reason is `runtime_access_denied` or a future unknown string
- **THEN** decoding SHALL preserve the string without closed-enum failure

### Requirement: OMP model and thinking validation
Agent create and update SHALL reject a supplied thinking level without an effective model before transport. Create SHALL require an explicit model; update SHALL distinguish omitted, set, and clear model states and SHALL apply the same rule across runtime changes.

#### Scenario: Create combinations are validated
- **WHEN** create receives model/thinking as omitted, model-only, both, or thinking-only
- **THEN** all valid combinations SHALL emit exact argv and thinking-only SHALL fail before transport

#### Scenario: Update respects set and clear
- **WHEN** update sets, retains, or clears model while supplying or omitting thinking level
- **THEN** validation SHALL use the effective model and explicit clear plus thinking SHALL fail before transport

#### Scenario: Validation prevents partial mutation
- **WHEN** an invalid combination is attempted with other agent changes
- **THEN** no CLI call SHALL occur and no partial agent mutation SHALL be observed

### Requirement: Structured runtime-delete conflict
Runtime delete SHALL preserve empty success and centralized `ConflictError` behavior while exposing optional reviewed structured guidance for online, offline, and profile-backed blockers. It SHALL also preserve legacy or proxy plain-body errors.

#### Scenario: Empty delete success remains unchanged
- **WHEN** runtime deletion succeeds with empty output
- **THEN** the existing successful `ActionResult` contract SHALL be preserved

#### Scenario: Structured 409 preserves context
- **WHEN** target CLI returns structured blocker guidance with optional counts, timestamps, or profile identity
- **THEN** code, message, and all present reviewed context SHALL remain available to the caller

#### Scenario: Plain conflict remains supported
- **WHEN** a legacy server or proxy returns a plain 409 body
- **THEN** the SDK SHALL raise the centralized conflict with its message and SHALL NOT require structured fields

#### Scenario: Delete never escalates automatically
- **WHEN** any runtime-delete conflict occurs
- **THEN** the SDK SHALL NOT add cascade, retry, unbind agents, or delete a profile automatically
