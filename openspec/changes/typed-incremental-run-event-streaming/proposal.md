## Why

Consumers can read a task run's messages only as a complete snapshot, so every live monitor must rebuild the same sequence cursor, polling, deduplication, event classification, and completion loop. The reviewed Multica `v0.4.28` baseline already exposes ordered messages and `run-messages --since`; the SDK should turn that existing contract into a small typed iterator.

## What Changes

- Add immutable semantic run-event models for text, thinking, tool start, tool finish, error, observed run-status changes, and unknown future message types.
- Add `TaskRun.stream_events()` for ordered incremental consumption from a bound task run, including cursor management, duplicate suppression, terminal-state detection, a normal completed/failed tail drain, and a documented cancellation quiescence drain.
- Extend the already governed `v0.4.28` `issues.run_messages` operation with the currently unmodeled `since` input, and keep `TaskRun.messages` / `IssueResource.run_messages()` available for snapshot access.
- Correct `RunMessage` to the pinned upstream payload (`task_id`, `issue_id`, `seq`, `type`, `tool`, `content`, `input`, `output`, `created_at`) so raw and typed views share one truthful source model.
- Document that the iterator is polling-backed incremental delivery, not server push or a real-time guarantee, and that externally cancelled runs expose no SDK-visible flush acknowledgement so cancellation quiescence reduces but cannot eliminate a late-tail race.
- Keep this change synchronous because the SDK has no asynchronous client or command execution model; an async stream is deferred until an SDK-wide async API exists.
- **BREAKING**: replace the unsupported `RunMessage.id`, `run_id`, and `role` constructor fields with the pinned upstream message fields.

## Capabilities

### New Capabilities

- `run-event-streaming`: Typed event mapping and incremental, completion-aware iteration for a task run.

### Modified Capabilities

- `sdk-surface`: Expose truthful raw run messages and public semantic run-event types without introducing a one-off async API.
- `bound-resource-relations`: Extend bound `TaskRun` with an incremental event stream while preserving raw message snapshot access.
- `upstream-contract`: Govern the existing `run-messages --since` mapping and the pinned response payload used by both raw and semantic APIs.

## Impact

The change affects issue activity models, the bound `TaskRun` entity, issue resource command construction, public exports, the approved SDK contract, focused unit/contract/component tests, API documentation, and a concise streaming example. It adds no dependency, transport, background thread, server endpoint, or server-push protocol.
