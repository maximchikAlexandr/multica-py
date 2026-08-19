## ADDED Requirements

### Requirement: Persisted messages map to semantic events
The SDK SHALL map each persisted run message to exactly one immutable keyword-only semantic event while retaining the complete `RunMessage` as `raw_message`. Every message-backed event SHALL have `task_id: str`, `issue_id: str | None`, `sequence: int` copied from `seq`, `created_at: datetime | None`, and `raw_message: RunMessage`. `RunTextEvent` SHALL add `text: str | None` from `content`; `RunThinkingEvent` SHALL add `thinking: str | None` from `content`; `RunToolStartedEvent` SHALL add `tool: str | None` and `input: Mapping[str, JsonValue] | None`; `RunToolFinishedEvent` SHALL add `tool: str | None` and `output: str | None`; and `RunErrorEvent` SHALL add `error: str | None` from `content`. A missing optional source field SHALL map to `None`, never an empty or fabricated value, and SHALL NOT prevent yielding the semantic event. The mapping SHALL accept `text`, `thinking`, `tool_use`/`tool-use`, `tool_result`/`tool-result`, and `error` respectively. Every other type string, including blank, SHALL produce `RunUnknownEvent` with the shared message fields plus `message_type: str` equal to `RunMessage.type`; sparse unknown payload fields SHALL remain available through `raw_message`.

#### Scenario: Text and thinking messages narrow by type
- **WHEN** a stream receives ordered `text` and `thinking` messages
- **THEN** it yields `RunTextEvent(text=<content>)` and `RunThinkingEvent(thinking=<content>)` objects whose sequence, timestamps, task context, and raw messages match the upstream payloads

#### Scenario: Tool lifecycle preserves structured data
- **WHEN** a `tool_use` message with `tool` and `input` is followed by a `tool_result` message with `tool` and `output`
- **THEN** the stream yields a `RunToolStartedEvent` followed by a `RunToolFinishedEvent` preserving the tool name, structured input, output, sequence, and raw messages

#### Scenario: Sparse known payload remains typed
- **WHEN** a known message type omits its optional `content`, `tool`, `input`, or `output` field
- **THEN** the corresponding concrete event is yielded with each absent semantic field set to `None` and with the complete sparse `raw_message`

#### Scenario: Error message is semantic
- **WHEN** a persisted message has type `error`
- **THEN** the stream yields `RunErrorEvent(error=<content>)` without raising merely because the event represents an execution error

#### Scenario: Unknown or blank message type is lossless
- **WHEN** pinned or future upstream returns an unrecognized or blank message type
- **THEN** the stream yields `RunUnknownEvent(message_type=<exact type string>)` in sequence order and preserves the complete raw message

### Requirement: Bound task runs stream incrementally
`TaskRun.stream_events(*, poll_interval: float = 1.0) -> Iterator[RunEvent]` SHALL repeatedly request raw messages with `since` equal to the greatest emitted upstream sequence. Its local message state SHALL contain that cursor and the complete immutable `RunMessage` keyed by every emitted sequence for the iterator lifetime, using `O(emitted messages)` memory and releasing it when iteration ends. For each sequence already in the table, whether repeated within the current batch or in a later poll, it SHALL suppress the row only when the complete payload equals the stored message and SHALL raise `OutputShapeError` when it differs; it SHALL yield unseen messages in ascending sequence order, store them, and advance the cursor. It SHALL sleep for `poll_interval` seconds only when another poll or terminal quiescence read is required. `poll_interval` SHALL be a positive finite real number; booleans, zero, negative, nonnumeric, NaN, and infinity SHALL fail before the first subprocess call.

#### Scenario: Initial poll starts at zero
- **WHEN** a consumer starts `stream_events()` on a bound task run
- **THEN** the first message request emits `issue run-messages <task-id> --issue <issue-id> --since 0 --output json` and the consumer manages no cursor

#### Scenario: Cursor advances to greatest emitted sequence
- **WHEN** a poll returns messages with sequences 4, 5, and 6
- **THEN** they are yielded in ascending sequence order and the next message request uses `--since 6`

#### Scenario: Duplicate and stale messages are suppressed
- **WHEN** a later response repeats a message whose sequence is less than or equal to the greatest emitted sequence
- **THEN** the complete payload is checked against the stored message, an identical repeat is not emitted, and all unseen messages retain ascending order

#### Scenario: Conflicting repeated sequence is rejected
- **WHEN** a later response contains an already emitted sequence with any different `RunMessage` field
- **THEN** iteration raises `OutputShapeError` before emitting that conflicting row or advancing past it

#### Scenario: Conflicts are detected within and across batches
- **WHEN** one batch contains two different payloads for one sequence or a later poll changes a previously accepted sequence
- **THEN** the retained message for that sequence makes iteration raise `OutputShapeError` in either case

#### Scenario: Invalid interval fails before I/O
- **WHEN** `poll_interval` is not a positive finite real number
- **THEN** iteration raises `TypeError` or `ValueError` before a message or run-status command executes

### Requirement: Stream termination follows durable run completion
The iterator SHALL refresh its own task run through the inherited issue context after each incremental message batch. It SHALL treat `completed`, `failed`, and `cancelled` as terminal statuses and SHALL also treat any run with non-null `completed_at` as terminal for forward compatibility. For each observed status change it SHALL create one immutable keyword-only `RunStatusChangedEvent` with `task_id: str`, `issue_id: str | None`, `sequence: None`, `created_at: None`, `raw_message: None`, `previous_status: str | None`, `status: str`, and `observed_at: datetime`. `observed_at` SHALL be an aware UTC timestamp captured immediately after the successful refresh that supplied `status`; it SHALL NOT represent upstream `created_at` or `completed_at`. After first observing a terminal run, the iterator SHALL require two consecutive incremental responses with no unseen message, sleeping exactly `poll_interval` between terminal reads. Empty and verified identical-replay-only responses SHALL count as quiet; any unseen message SHALL be yielded and SHALL reset the quiet count to zero. After the second consecutive quiet response, the iterator SHALL yield the already observed terminal status event and terminate so no message event appears after terminal status. Because pinned upstream exposes no transcript-complete watermark and cancellation acknowledgement occurs after status cancellation, this quiescence rule SHALL NOT be documented as a guarantee that no still-later message can exist.

#### Scenario: Running status is observable
- **WHEN** the first status refresh observes `running`
- **THEN** the iterator yields one `RunStatusChangedEvent(previous_status=None, status="running")` after all messages from that poll and does not emit the same status again while it remains unchanged

#### Scenario: Terminal transition drains the tail
- **WHEN** a status refresh changes from `running` to `completed`
- **THEN** the iterator waits for two consecutive quiet incremental responses separated by `poll_interval`, resets the quiet count when a tail event arrives, yields all observed tail events before one completed status event, and then stops

#### Scenario: Failed and cancelled runs end naturally
- **WHEN** the refreshed run status is `failed` or `cancelled`
- **THEN** the iterator applies the same two-quiet-read policy, yields the terminal status event last, and terminates without converting the terminal outcome into an iterator exception

#### Scenario: Delayed cancellation tail resets quiescence
- **WHEN** the first post-cancellation read is quiet and the next read contains a message flushed by the daemon after cancellation status was stored
- **THEN** the message is yielded, the quiet count resets to zero, and two further consecutive quiet reads are required before the cancelled status event

#### Scenario: Quiescence is not an upstream completeness watermark
- **WHEN** a message is persisted only after the two-quiet-read window has ended
- **THEN** the completed iterator does not promise to include it and documentation directs authoritative consumers to a later raw message snapshot

#### Scenario: Unknown terminal status uses completion timestamp
- **WHEN** a refreshed run has a future unknown status and non-null `completed_at`
- **THEN** the iterator treats it as terminal, applies the same two-quiet-read policy, and terminates

### Requirement: Stream failures remain explicit
Streaming SHALL require the same bound client and inherited issue ID used by `TaskRun.messages`. Missing binding or issue context SHALL raise the existing typed entity/relation context error before polling. A successful run-list refresh that omits the target run SHALL raise `ProtocolError`. Two different complete `RunMessage` payloads at one sequence SHALL raise `OutputShapeError`. Existing typed command failures, including transport `NotFoundError`, SHALL propagate unchanged. None of these failures SHALL be silently retried or interpreted as completion.

#### Scenario: Detached task run cannot stream
- **WHEN** `stream_events()` is consumed from a `TaskRun` without a bound client or inherited issue ID
- **THEN** it raises the existing context error before executing `run-messages` or `runs`

#### Scenario: Target disappears during refresh
- **WHEN** the issue run refresh succeeds but does not contain the streamed task ID
- **THEN** the iterator raises `ProtocolError` instead of looping forever, raising transport `NotFoundError`, or reporting completion

#### Scenario: Sequence payload conflicts
- **WHEN** a response repeats an emitted sequence with a different complete raw payload
- **THEN** the iterator raises `OutputShapeError` and performs no later status refresh or poll

#### Scenario: Command failure propagates
- **WHEN** an incremental message read or run-status refresh raises a typed SDK command error
- **THEN** the same failure escapes the iterator and no later polling occurs
