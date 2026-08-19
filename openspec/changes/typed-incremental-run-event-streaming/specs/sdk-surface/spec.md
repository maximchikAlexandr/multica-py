## ADDED Requirements

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
The root `multica_py` package SHALL export `RunEvent`, `RunTextEvent`, `RunThinkingEvent`, `RunToolStartedEvent`, `RunToolFinishedEvent`, `RunErrorEvent`, `RunStatusChangedEvent`, and `RunUnknownEvent`. These immutable types SHALL support `isinstance`, structural pattern matching, and strict static type narrowing without `Any`; provider-controlled message and run-status strings SHALL remain open strings.

#### Scenario: Root imports support pattern matching
- **WHEN** a user imports semantic run events from `multica_py` and matches an event by concrete class
- **THEN** the class-specific fields are available with precise annotations and no raw dictionary parsing

#### Scenario: Future strings remain accepted
- **WHEN** upstream returns a new message type or run status string
- **THEN** model decoding succeeds and the string is preserved rather than rejected by a closed enum

### Requirement: Async streaming follows the SDK execution model
This change SHALL NOT add `stream_events_async`, `run_async`, an async client, a thread bridge, or a second command transport. Documentation SHALL state that asynchronous event streaming becomes applicable only when the SDK adopts an end-to-end asynchronous command execution model.

#### Scenario: Public surface remains consistently synchronous
- **WHEN** the SDK public API is inspected after this change
- **THEN** `TaskRun.stream_events()` is present and no isolated async streaming method or hidden worker thread is present
