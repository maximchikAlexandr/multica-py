## Context

`IssueResource.run_messages()` currently executes the pinned `issue run-messages` command but decodes into a model whose `id`, `run_id`, and `role` fields do not exist in Multica `v0.4.20`. The upstream command and user-authenticated handler already provide everything needed for incremental consumption: `--since <seq>`, ascending `seq`, semantic `type`, task/issue context, tool data, and timestamps. `TaskRun` is already a bound entity with inherited `issue_id`, a client, current status, and raw `messages`; `IssueResource.runs(issue_id)` is the available status refresh operation.

The SDK is intentionally synchronous. `Command.run()` performs one bounded CLI operation, and there is no async client, async transport, or task-run creation method. The solution therefore belongs above the existing command/resource layer as a synchronous iterator, not in `CliTransport`, `ManagedProcess`, or a new concurrency subsystem.

## Goals / Non-Goals

**Goals:**

- Decode the actual approved run-message payload without `Any` or fabricated fields.
- Offer concrete semantic events that narrow with normal Python typing and pattern matching.
- Hide sequence cursor, polling, duplicate suppression, status refresh, and terminal-quiescence mechanics behind `TaskRun.stream_events()`.
- Preserve raw snapshots and raw messages for consumers that need exact upstream data.
- Keep the implementation dependency-free and testable with the existing fake CLI and table-driven test patterns.

**Non-Goals:**

- Server push, SSE, websockets, latency guarantees, or changes to Multica server/CLI.
- Creating or rerunning a task through a new `issues.run()` convenience API.
- A one-off async client, thread bridge, background worker, retry policy, persisted resume cursor, or configurable event registry.
- Completion-aware streaming on `AutopilotRun`, whose relation does not own the issue-run status refresh contract.

## Decisions

### 1. Correct the raw boundary before adding semantic models

Add a private `_RunMessageWire` matching `taskMessageToPayload`, convert its recursive `input: object | None` through the same strict JSON coercion already used for autopilot payloads, and construct the public frozen `RunMessage`. Move that coercion to one internal helper reused by both domains rather than duplicating it. Generalize the existing private-wire decoder hook so `Page[RunMessage]` uses this adapter while other page decoding remains unchanged.

This is preferred to weakening `RunMessage.input` to `object`, teaching event conversion to parse dictionaries independently, or retaining placeholder legacy fields. One truthful raw model makes raw and semantic paths agree and fails malformed JSON at the established decoder boundary. The constructor-field break is documented because upstream provides no value from which `id`, `run_id`, or `role` can be honestly reconstructed.

### 2. Use a small closed set of concrete events plus one open fallback

Create `models/run_events.py` with a frozen, keyword-only `RunEvent` base and frozen concrete subclasses. The public field table is normative:

| Concrete event | Common fields | Concrete fields | Sparse payload policy |
| --- | --- | --- | --- |
| `RunTextEvent` | `task_id: str`, `issue_id: str | None`, `sequence: int`, `created_at: datetime | None`, `raw_message: RunMessage` | `text: str | None` | missing `content` becomes `None` |
| `RunThinkingEvent` | same message-backed fields | `thinking: str | None` | missing `content` becomes `None` |
| `RunToolStartedEvent` | same message-backed fields | `tool: str | None`, `input: Mapping[str, JsonValue] | None` | missing `tool` or `input` independently becomes `None` |
| `RunToolFinishedEvent` | same message-backed fields | `tool: str | None`, `output: str | None` | missing `tool` or `output` independently becomes `None` |
| `RunErrorEvent` | same message-backed fields | `error: str | None` | missing `content` becomes `None`; the event is still yielded |
| `RunUnknownEvent` | same message-backed fields | `message_type: str` | exact type string, including blank; all other sparse data remains available through `raw_message` |
| `RunStatusChangedEvent` | `task_id: str`, `issue_id: str | None`, `sequence: None`, `created_at: None`, `raw_message: None` | `previous_status: str | None`, `status: str`, `observed_at: datetime` | not message-backed; message fields narrow to literal `None` |

`observed_at` is an aware UTC timestamp captured immediately after the successful refresh whose status it reports, not an upstream run timestamp. Optional semantic fields are never replaced with empty strings or fabricated values.

A private total conversion function maps exactly the five persisted `v0.4.20` categories: `text`, `thinking`, `tool_use`, `tool_result`, and `error`. Content maps to `text`, `thinking`, or `error` according to the concrete class. Hyphenated `tool-use`/`tool-result`, blank, and every other unrecognized `type` string map losslessly to `RunUnknownEvent(message_type=message.type)` and retain the complete raw message. At pinned Multica commit `93342d04a7a9f788fec921e5aa736f86c7f22d8f`, the persistence/drain implementation in `server/internal/daemon/daemon.go:6382-6722` writes the underscore spellings (`tool_use`/`tool_result` branches at `6555-6615`), and `server/pkg/protocol/messages.go:147-157` documents only those persisted payload spellings; accepting internal pre-normalization aliases would add unsupported policy.

This is preferred to an enum-plus-payload bag, user registration hooks, or one class per provider. Concrete classes give the requested narrowing; the fallback avoids coupling SDK releases to upstream message vocabulary.

### 3. Extend the governed raw operation with an explicit sequence cursor

Add keyword-only `since: int = 0` to eager, command, and private relation helpers and always render `--since <value>`. Validate an exact non-boolean integer in the DB/server-safe inclusive range `0..2_147_483_647` before command construction. The pinned handler parses with `strconv.Atoi` and then casts to `int32` before the strict-greater-than SQL query, so accepting a larger 64-bit CLI integer could wrap the query cursor. Update the approved contract, source references, generated/runtime projection, canonical operation case, and raw relation expectations together.

Always rendering zero produces one deterministic argv contract and lets `stream_events()` use the same call shape on every iteration. It is preferred to a second private incremental command or post-filtering full snapshots, both of which duplicate or waste an upstream capability.

### 4. Keep the stream loop on bound `TaskRun`

`TaskRun.stream_events()` validates `poll_interval`, then obtains its bound client and required `issue_id`. Its local state is: greatest emitted sequence, a `sequence -> RunMessage` table for every emitted message, last observed status, whether terminal state has been observed, and a terminal quiet-read count. The table retains one immutable raw message per emitted sequence for this iterator's lifetime (`O(emitted messages)` memory) and is released when the iterator returns, closes, or errors. This is the minimum state that can distinguish an identical replay from a different payload both within one response and in any later poll. Each cycle:

1. Call `issues.run_messages(task_id, issue_id=issue_id, since=cursor)`.
2. Sort by `seq`. For a sequence in the table, suppress the row only when its complete `RunMessage` equals the stored value; otherwise raise `OutputShapeError`. Convert and yield each unseen row in ascending order, record its raw message, and advance the cursor to the greatest emitted sequence.
3. Refresh `issues.runs(issue_id)` and locate this exact task ID.
4. For a changed nonterminal status, yield one status event.
5. For `completed` or `failed`, immediately drain incremental reads until one response contains no unseen message; empty and verified identical-replay-only responses end the drain. Pinned daemon code flushes queued messages before making the terminal callback, so no sleep is required between these reads.
6. For `cancelled`, or a future unknown status treated as terminal only because `completed_at` is non-null, enter conservative terminal quiescence. Perform incremental reads until two consecutive responses contain no unseen message, sleeping exactly `poll_interval` between those reads. Empty and verified identical-replay-only responses are quiet. Any unseen message is yielded, stored, advances the cursor, and resets the quiet count to zero. After the second consecutive quiet response, yield the already observed terminal status event last and return.
7. Otherwise sleep for `poll_interval` and repeat.

Keeping the loop on `TaskRun` reuses its established identity/binding contract and makes `for event in run.stream_events()` discoverable. A separate stream manager, client-wide scheduler, or cache-backed implementation would add ownership and lifecycle problems without improving the current synchronous use case.

The split lifecycle follows pinned Multica commit `93342d04a7a9f788fec921e5aa736f86c7f22d8f`. The `executeAndDrain` persistence path in `server/internal/daemon/daemon.go:6382-6722`, specifically `waitForDrain` at `6653-6695`, completes before control returns through `runner.run`/`runTask` to the existing completed/failed terminal callback, making the ordinary no-unseen drain evidence-backed. External cancellation differs: `CancelTaskWithResult` in `server/internal/service/task.go:2064-2141` synchronously commits and broadcasts cancellation, while `server/internal/daemon/client.go:340-346`, the post-run cancellation-ack paths in `server/internal/daemon/daemon.go:4427-4437,4464-4471`, and `server/internal/handler/daemon.go:3639-3650` send/receive `AckTaskCancelled` only after the daemon has “finished flushing the transcript.” That ack is not represented in `IssueResource.runs()`, so the SDK cannot wait for it. Two quiet reads reduce the cancellation race while preserving natural synchronous termination, but they do not guarantee capture of a message persisted after the quiet window. Future statuses terminal only by `completed_at` use the conservative cancellation path because no flush ordering is known. Documentation must state the limitation and direct consumers requiring authoritative cancelled-run completeness to fetch a later raw snapshot.

### 5. Treat transport failures and run disappearance as errors

The iterator does not retry command failures: existing typed transport exceptions propagate. If a successful run-list refresh omits the target ID, raise `ProtocolError`: transport `NotFoundError` is reserved for a CLI/server not-found failure, whereas a successful response that violates the iterator's observation contract is a protocol failure. Raise `OutputShapeError` when an already emitted sequence is returned with a different `RunMessage` payload. A failed or cancelled run is not itself an iterator failure; it is a terminal status event after its respective ordinary-drain or cancellation-quiescence path.

This separates “the observed run failed” from “the SDK could not observe the run.” Automatic retry, backoff, cancellation tokens, and total stream timeouts remain follow-up policy because the SDK has no shared retry contract today.

### 6. Test at the smallest existing layers

- Extend the canonical operation row and generated contract checks for exact `--since` argv and validation.
- Add focused raw-model decoder cases for complete, sparse, malformed, and recursively immutable input.
- Add one table-driven event-mapping test and iterator tests with mocked resource methods and patched sleep for cursor advancement, within-batch and later-poll duplicate handling, status changes, terminal quiescence, terminal outcomes, missing context/run, and propagated errors.
- Update existing TaskRun relation cases for the truthful message model and explicit zero cursor.
- Add root-export/type-check assertions and concise documentation/example coverage; do not add a new test framework or live-only requirement.

## Risks / Trade-offs

- **Breaking `RunMessage` constructor fields** → Document exact migration and keep the raw snapshot method name stable; the old fields are not backed by the pinned CLI and cannot be preserved truthfully.
- **Polling starts one CLI process per interval plus status refreshes** → Default to one second, expose only a validated interval, and document that this is incremental polling rather than push. Optimize only after measurement or a server-push contract exists.
- **A future terminal status may be unknown** → Treat non-null `completed_at` as terminal while keeping status strings open.
- **Cancelled status precedes transcript-flush acknowledgement** → Use two consecutive quiet reads separated by `poll_interval`, reset on unseen data, emit cancelled status last, and document that a later-than-window message can still be missed; authoritative consumers can fetch a later raw snapshot. Completed/failed retain the source-backed ordinary drain.
- **An upstream bug could repeat or reorder rows** → Retain one raw message per emitted sequence for the iterator lifetime, sort by sequence, suppress identical repeats, and fail explicitly on conflicting payloads within a batch or across polls instead of silently corrupting order.
- **A stream can run indefinitely while its task remains active** → This matches the task lifecycle; consumers can stop iteration themselves. A total deadline belongs in a future shared stream/cancellation policy.

## Migration Plan

1. Update the approved upstream contract and raw decoder/model together so the feature never lands on the unsupported legacy shape.
2. Add events and the bound iterator, then update tests, exports, migration notes, API docs, and one example.
3. Run contract integrity, offline tests, mypy for source/tests, Ruff checks, package validation, and diff checks required by the repository.
4. Release the constructor-field change with migration guidance: `run_id` becomes `task_id`, event ordering uses `seq`, and semantic role is represented by `type`/event class; `id` has no replacement because upstream has no message ID.

Rollback is a normal Git revert of the contract, model, event, and documentation change; no server state or persisted SDK state is migrated.

## Open Questions

None. Async streaming is intentionally gated on a future SDK-wide async execution design rather than left ambiguous in this change.
