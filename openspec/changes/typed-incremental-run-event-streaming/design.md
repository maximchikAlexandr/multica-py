## Context

`IssueResource.run_messages()` currently executes the pinned `issue run-messages` command but decodes into a model whose `id`, `run_id`, and `role` fields do not exist in Multica `v0.4.20`. The upstream command and user-authenticated handler already provide everything needed for incremental consumption: `--since <seq>`, ascending `seq`, semantic `type`, task/issue context, tool data, and timestamps. `TaskRun` is already a bound entity with inherited `issue_id`, a client, current status, and raw `messages`; `IssueResource.runs(issue_id)` is the available status refresh operation.

The SDK is intentionally synchronous. `Command.run()` performs one bounded CLI operation, and there is no async client, async transport, or task-run creation method. The solution therefore belongs above the existing command/resource layer as a synchronous iterator, not in `CliTransport`, `ManagedProcess`, or a new concurrency subsystem.

## Goals / Non-Goals

**Goals:**

- Decode the actual approved run-message payload without `Any` or fabricated fields.
- Offer concrete semantic events that narrow with normal Python typing and pattern matching.
- Hide sequence cursor, polling, duplicate suppression, status refresh, and final-drain mechanics behind `TaskRun.stream_events()`.
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

Create `models/run_events.py` with a frozen `RunEvent` base and frozen concrete subclasses. Message-backed events carry `task_id`, optional `issue_id`, `sequence`, `created_at`, and `raw_message`; status events carry the same task context, `sequence=None`, `raw_message=None`, previous/current status, and observation time. A private total conversion function maps the five persisted `v0.4.20` categories and accepts both underscore and historical hyphen tool spellings. `RunUnknownEvent` preserves every future type through its raw message.

This is preferred to an enum-plus-payload bag, user registration hooks, or one class per provider. Concrete classes give the requested narrowing; the fallback avoids coupling SDK releases to upstream message vocabulary.

### 3. Extend the governed raw operation with an explicit sequence cursor

Add keyword-only `since: int = 0` to eager, command, and private relation helpers and always render `--since <value>`. Validate an exact nonnegative non-boolean integer before command construction. Update the approved contract, source references, generated/runtime projection, canonical operation case, and raw relation expectations together.

Always rendering zero produces one deterministic argv contract and lets `stream_events()` use the same call shape on every iteration. It is preferred to a second private incremental command or post-filtering full snapshots, both of which duplicate or waste an upstream capability.

### 4. Keep the stream loop on bound `TaskRun`

`TaskRun.stream_events()` validates `poll_interval`, then obtains its bound client and required `issue_id`. It owns only local iterator state: greatest emitted sequence, last observed status, and whether terminal state has been observed. Each cycle:

1. Call `issues.run_messages(task_id, issue_id=issue_id, since=cursor)`.
2. Sort by `seq`, suppress identical repeats at or below the cursor, reject conflicting same-sequence payloads, convert messages, and yield them.
3. Refresh `issues.runs(issue_id)` and locate this exact task ID.
4. For a changed nonterminal status, yield one status event.
5. For a terminal status (`completed`, `failed`, `cancelled`, or non-null `completed_at`), immediately read and yield unseen messages until one incremental read is empty, yield the terminal status event last, and return.
6. Otherwise sleep for `poll_interval` and repeat.

Keeping the loop on `TaskRun` reuses its established identity/binding contract and makes `for event in run.stream_events()` discoverable. A separate stream manager, client-wide scheduler, or cache-backed implementation would add ownership and lifecycle problems without improving the current synchronous use case.

### 5. Treat transport failures and run disappearance as errors

The iterator does not retry command failures: existing typed transport exceptions propagate. If a successful run-list refresh omits the target ID, raise an explicit protocol/not-found error. A failed or cancelled run is not itself an iterator failure; it is a terminal status event after the raw error tail has drained.

This separates “the observed run failed” from “the SDK could not observe the run.” Automatic retry, backoff, cancellation tokens, and total stream timeouts remain follow-up policy because the SDK has no shared retry contract today.

### 6. Test at the smallest existing layers

- Extend the canonical operation row and generated contract checks for exact `--since` argv and validation.
- Add focused raw-model decoder cases for complete, sparse, malformed, and recursively immutable input.
- Add one table-driven event-mapping test and iterator tests with mocked resource methods and patched sleep for cursor advancement, duplicate handling, status changes, final drain, terminal outcomes, missing context/run, and propagated errors.
- Update existing TaskRun relation cases for the truthful message model and explicit zero cursor.
- Add root-export/type-check assertions and concise documentation/example coverage; do not add a new test framework or live-only requirement.

## Risks / Trade-offs

- **Breaking `RunMessage` constructor fields** → Document exact migration and keep the raw snapshot method name stable; the old fields are not backed by the pinned CLI and cannot be preserved truthfully.
- **Polling starts one CLI process per interval plus status refreshes** → Default to one second, expose only a validated interval, and document that this is incremental polling rather than push. Optimize only after measurement or a server-push contract exists.
- **A future terminal status may be unknown** → Treat non-null `completed_at` as terminal while keeping status strings open.
- **A backend/server race could expose tail messages near completion** → Drain incremental reads to empty before emitting the terminal status event; pinned upstream already flushes the transcript before terminal transition.
- **An upstream bug could repeat or reorder rows** → Sort by sequence, suppress identical repeats, and fail explicitly on conflicting payloads for one sequence instead of silently corrupting order.
- **A stream can run indefinitely while its task remains active** → This matches the task lifecycle; consumers can stop iteration themselves. A total deadline belongs in a future shared stream/cancellation policy.

## Migration Plan

1. Update the approved upstream contract and raw decoder/model together so the feature never lands on the unsupported legacy shape.
2. Add events and the bound iterator, then update tests, exports, migration notes, API docs, and one example.
3. Run contract integrity, offline tests, mypy for source/tests, Ruff checks, package validation, and diff checks required by the repository.
4. Release the constructor-field change with migration guidance: `run_id` becomes `task_id`, event ordering uses `seq`, and semantic role is represented by `type`/event class; `id` has no replacement because upstream has no message ID.

Rollback is a normal Git revert of the contract, model, event, and documentation change; no server state or persisted SDK state is migrated.

## Open Questions

None. Async streaming is intentionally gated on a future SDK-wide async execution design rather than left ambiguous in this change.
