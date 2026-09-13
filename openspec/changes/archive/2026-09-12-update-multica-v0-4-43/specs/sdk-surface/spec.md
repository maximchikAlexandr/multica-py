## MODIFIED Requirements

### Requirement: Raw run messages match the approved upstream payload
`multica_py.models.issue_activity.RunMessage` SHALL be an immutable keyword-only
model with required `task_id: str`, `seq: int`, and `type: str`; optional
`issue_id: str | None`, `tool: str | None`, `content: str | None`,
`input: Mapping[str, JsonValue] | None`, `output: str | None`,
`created_at: datetime | None`, and `output_truncated: bool | None`; and no
fabricated `id`, `run_id`, or `role` fields. Decoding SHALL map an omitted
`output_truncated` to unknown (`None`), preserve present `false` and `true`, and
reject explicit null or non-boolean values. It SHALL preserve every type string,
including blank, recursively immutable structured tool input, and the timestamp
received from upstream.

#### Scenario: Complete upstream message decodes
- **WHEN** raw JSON contains every approved task-message field including nested tool input, timestamp, and `output_truncated=true`
- **THEN** `RunMessage` preserves each field, parses the timestamp, snapshots nested input immutably, and can be used as a stable raw event payload

#### Scenario: Truncation state remains tri-state
- **WHEN** legacy, complete-current, and truncated-current rows respectively omit `output_truncated`, contain `false`, and contain `true`
- **THEN** public values are respectively `None`, `False`, and `True` without defaulting unknown history to false

#### Scenario: Malformed truncation fails closed
- **WHEN** `output_truncated` is explicit null or a non-boolean JSON value
- **THEN** decoding raises `OutputShapeError` rather than claiming a truncation state

#### Scenario: Sparse message decodes
- **WHEN** a valid text or error payload omits inapplicable tool, input, output, issue, timestamp, and truncation fields
- **THEN** those fields decode as `None` without inventing identifiers, roles, empty structured values, or output completeness

#### Scenario: Blank type remains lossless
- **WHEN** a structurally valid raw message has `type=""`
- **THEN** `RunMessage` decoding succeeds with the blank string preserved and semantic conversion yields `RunUnknownEvent(message_type="")` retaining that raw message

#### Scenario: Legacy constructor fields are removed
- **WHEN** a caller constructs `RunMessage` with `id`, `run_id`, or `role`
- **THEN** construction fails and migration documentation directs the caller to `task_id`, `seq`, and `type`

## ADDED Requirements

### Requirement: Agent conversation-starter mutations are explicit
`AgentResource.create`, `create_command`, `update`, and `update_command` SHALL
accept the keyword `conversation_starters: tuple[AgentConversationStarter, ...]
| UnsetType = Unset`. Omission SHALL emit no flag. An explicit tuple, including
the empty tuple, SHALL emit one `--conversation-starters` argument containing a
deterministic JSON array in tuple order; the empty tuple SHALL set an empty list
on create and clear the list on update. `None`, non-tuples, non-starter items,
more than three items, blank label or prompt after trim, label length over 80,
and prompt length over 4000 Unicode code points SHALL fail before transport.

#### Scenario: Create and update omit the field
- **WHEN** either mutation is called with `conversation_starters=Unset`
- **THEN** complete argv omits `--conversation-starters` and the upstream request omits the JSON key

#### Scenario: Ordered starters are encoded once
- **WHEN** a caller supplies one to three valid typed starters
- **THEN** complete argv contains one deterministic JSON-array flag preserving tuple order and each exact label/prompt string

#### Scenario: Empty tuple has explicit meaning
- **WHEN** create or update receives `conversation_starters=()`
- **THEN** argv contains `--conversation-starters []`, causing create to set an empty list and update to clear the existing list

#### Scenario: Boundaries use Unicode code points
- **WHEN** labels of 80/81 code points or prompts of 4000/4001 code points are supplied
- **THEN** the lower boundary is accepted and the upper boundary raises `ValueError` before transport

#### Scenario: Invalid shape never executes
- **WHEN** the input is `None`, raw JSON text including malformed JSON or `"null"`, another non-tuple, contains a non-starter item, exceeds three entries, or contains a blank label/prompt
- **THEN** construction raises `TypeError` or `ValueError` and the executor call count remains zero

### Requirement: Task cancellation actor remains presence-correct and open
The SDK SHALL expose immutable keyword-only
`TaskCancellationActor(type: str, id: str | None = None, name: str | None =
None)` from the issue-activity model module and optional
`TaskRun.cancelled_by: TaskCancellationActor | None = None`. Private wire
decoding SHALL accept omission or an object with required string `type` and
optional string `id`/`name`; it SHALL reject null, missing/wrong-typed `type`,
and wrong-typed optional members. Actor type SHALL remain an open string.

#### Scenario: Legacy absence remains compatible
- **WHEN** an agent-task or issue-run payload omits `cancelled_by`
- **THEN** the typed task run exposes `cancelled_by=None`

#### Scenario: Sparse actor object decodes
- **WHEN** a payload contains `cancelled_by={"type":"system"}`
- **THEN** the immutable actor preserves `type="system"` with `id=None` and `name=None`

#### Scenario: Current and future actor types remain open
- **WHEN** actor type is `member`, `agent`, `system`, or an unknown future nonblank string
- **THEN** decoding preserves the exact string without closed-enum failure

#### Scenario: Malformed actor fails closed
- **WHEN** the actor is null, lacks `type`, or contains a non-string known member
- **THEN** decoding raises `OutputShapeError` without fabricating an actor

### Requirement: Issue usage coverage counts retain their own meaning
`IssueUsage` SHALL add optional exact-integer `terminal_task_count`,
`metered_task_count`, and `unreported_task_count`. Omission in `0.4.42` payloads
SHALL produce `None`; present target values SHALL be nonnegative integers and
SHALL not be converted through floating point. Legacy `task_count` SHALL remain
the count of rows having usage and SHALL not be renamed, replaced, or inferred
from the three new counts.

#### Scenario: Legacy usage remains decodable
- **WHEN** a `0.4.42` usage payload omits all three coverage counts
- **THEN** each new public field is `None` and all legacy token/cost/task values remain unchanged

#### Scenario: Target counts preserve exact integers
- **WHEN** a `0.4.43` payload contains zero or large exact integer coverage counts
- **THEN** each value is preserved as its corresponding integer without float conversion or cross-field inference

#### Scenario: Coverage meanings remain distinct
- **WHEN** terminal, metered, unreported, and legacy task counts differ
- **THEN** the SDK exposes every value separately and documentation explains that metered plus unreported describes terminal-run coverage while `task_count` retains its legacy meaning

#### Scenario: Invalid counts fail closed
- **WHEN** a present coverage count is negative, boolean, fractional, string, or null
- **THEN** decoding raises `OutputShapeError`

### Requirement: Status sorting retains the target server contract
The existing issue-list `sort="status"` and direction pass-through SHALL remain
unchanged. Compatibility fixtures and documentation SHALL pin `0.4.43`
semantics: canonical and custom statuses are ordered by effective status
category, direction is respected, and existing property/manual sort behavior is
not reimplemented or regressed in the SDK.

#### Scenario: Canonical and custom statuses share category ordering
- **WHEN** target-backed semantic fixtures sort issues containing canonical and custom statuses by status
- **THEN** order follows the target status-category catalog rather than raw status spelling

#### Scenario: Other sorts remain pass-through
- **WHEN** status direction, property sort, or another already approved sort is requested
- **THEN** the SDK preserves the existing exact argv and performs no client-side reorder
