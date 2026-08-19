## ADDED Requirements

### Requirement: Persisted messages map to semantic events
The SDK SHALL map each persisted run message to exactly one immutable semantic event while retaining the complete `RunMessage` as `raw_message`. Every message-backed event SHALL expose the upstream `task_id`, optional `issue_id`, `seq` as `sequence`, and `created_at`. The mapping SHALL be `text` to `RunTextEvent`, `thinking` to `RunThinkingEvent`, `tool_use` and compatibility spelling `tool-use` to `RunToolStartedEvent`, `tool_result` and compatibility spelling `tool-result` to `RunToolFinishedEvent`, and `error` to `RunErrorEvent`. Any other nonblank upstream type SHALL produce `RunUnknownEvent` carrying that type and raw message instead of being dropped or causing decode failure.

#### Scenario: Text and thinking messages narrow by type
- **WHEN** a stream receives ordered `text` and `thinking` messages
- **THEN** it yields `RunTextEvent` and `RunThinkingEvent` objects whose text, sequence, timestamps, task context, and raw messages match the upstream payloads

#### Scenario: Tool lifecycle preserves structured data
- **WHEN** a `tool_use` message with `tool` and `input` is followed by a `tool_result` message with `tool` and `output`
- **THEN** the stream yields a `RunToolStartedEvent` followed by a `RunToolFinishedEvent` preserving the tool name, structured input, output, sequence, and raw messages

#### Scenario: Error message is semantic
- **WHEN** a persisted message has type `error`
- **THEN** the stream yields `RunErrorEvent(error=<content>)` without raising merely because the event represents an execution error

#### Scenario: Future message type is lossless
- **WHEN** pinned or future upstream returns an unrecognized nonblank message type
- **THEN** the stream yields `RunUnknownEvent` in sequence order and preserves the complete raw message

### Requirement: Bound task runs stream incrementally
`TaskRun.stream_events(*, poll_interval: float = 1.0) -> Iterator[RunEvent]` SHALL repeatedly request raw messages with `since` equal to the greatest emitted upstream sequence, yield only messages whose sequence is greater than that cursor, and sleep for `poll_interval` seconds only when another poll is required. `poll_interval` SHALL be a positive finite real number; booleans, zero, negative, nonnumeric, NaN, and infinity SHALL fail before the first subprocess call.

#### Scenario: Initial poll starts at zero
- **WHEN** a consumer starts `stream_events()` on a bound task run
- **THEN** the first message request emits `issue run-messages <task-id> --issue <issue-id> --since 0 --output json` and the consumer manages no cursor

#### Scenario: Cursor advances to greatest emitted sequence
- **WHEN** a poll returns messages with sequences 4, 5, and 6
- **THEN** they are yielded in ascending sequence order and the next message request uses `--since 6`

#### Scenario: Duplicate and stale messages are suppressed
- **WHEN** a later response repeats a message whose sequence is less than or equal to the greatest emitted sequence
- **THEN** the repeated message is not emitted and all newer messages retain ascending order

#### Scenario: Invalid interval fails before I/O
- **WHEN** `poll_interval` is not a positive finite real number
- **THEN** iteration raises `TypeError` or `ValueError` before a message or run-status command executes

### Requirement: Stream termination follows durable run completion
The iterator SHALL refresh its own task run through the inherited issue context after each incremental message batch. It SHALL treat `completed`, `failed`, and `cancelled` as terminal statuses and SHALL also treat any run with non-null `completed_at` as terminal for forward compatibility. When a nonterminal observed status changes, it SHALL yield one immutable `RunStatusChangedEvent` carrying the previous status (or `None` for the first observation), current status, task context, observation time, and no raw message. After first observing a terminal run, the iterator SHALL drain incremental message reads until one yields no unseen message, then yield the terminal status event and terminate so no message event appears after terminal status.

#### Scenario: Running status is observable
- **WHEN** the first status refresh observes `running`
- **THEN** the iterator yields one `RunStatusChangedEvent(previous_status=None, status="running")` after all messages from that poll and does not emit the same status again while it remains unchanged

#### Scenario: Terminal transition drains the tail
- **WHEN** a status refresh changes from `running` to `completed`
- **THEN** the iterator requests from the current cursor until a read has no unseen message, yields all tail events before one completed status event, and then stops

#### Scenario: Failed and cancelled runs end naturally
- **WHEN** the refreshed run status is `failed` or `cancelled`
- **THEN** the iterator drains unseen messages, yields the terminal status event last, and terminates without converting the terminal outcome into an iterator exception

#### Scenario: Unknown terminal status uses completion timestamp
- **WHEN** a refreshed run has a future unknown status and non-null `completed_at`
- **THEN** the iterator treats it as terminal, drains unseen messages, and terminates

### Requirement: Stream failures remain explicit
Streaming SHALL require the same bound client and inherited issue ID used by `TaskRun.messages`. Missing binding or issue context SHALL raise the existing typed entity/relation context error before polling. A missing target run in the refreshed issue run list, malformed message ordering with two different payloads at the same sequence, or an upstream command failure SHALL raise an explicit typed error and SHALL NOT be silently retried or interpreted as completion.

#### Scenario: Detached task run cannot stream
- **WHEN** `stream_events()` is consumed from a `TaskRun` without a bound client or inherited issue ID
- **THEN** it raises the existing context error before executing `run-messages` or `runs`

#### Scenario: Target disappears during refresh
- **WHEN** the issue run refresh succeeds but does not contain the streamed task ID
- **THEN** the iterator raises an explicit not-found or protocol error instead of looping forever or reporting completion

#### Scenario: Command failure propagates
- **WHEN** an incremental message read or run-status refresh raises a typed SDK command error
- **THEN** the same failure escapes the iterator and no later polling occurs
