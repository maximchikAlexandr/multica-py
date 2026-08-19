## 1. Approve the upstream cursor and raw payload

- [ ] 1.1 Update both scoped `issues.run_messages` entries in `contracts/sdk-contract.json` with keyword-only `since: int = 0`, `--since` / `query:since` mapping, exact nonnegative-nonboolean integer validation, the truthful run-message response schema, and reviewed `v0.4.20` source references to `server/cmd/multica/cmd_issue.go`, `server/internal/handler/daemon.go`, `server/pkg/protocol/messages.go`, and the strict-greater-than SQL query; update the generated runtime projection and contract schema data deterministically.
- [ ] 1.2 Replace the canonical run-message vector with exact `--since 0` argv, add a positive `since=42` vector, and add table-driven negative cases for negative, boolean, noninteger, and CLI-overflow cursors; run the focused contract integrity and operation-discovery tests until the approved and handwritten operation inventories agree.
- [ ] 1.3 Move the existing recursive finite-JSON coercion into one private internal helper, reuse it for autopilot payloads, add `_RunMessageWire` plus public conversion, and generalize the private-wire decoder hook so complete and sparse `Page[RunMessage]` payloads decode with recursively immutable tool input while malformed JSON fails as `OutputShapeError`.
- [ ] 1.4 Replace `RunMessage` with the required `task_id`, `seq`, and open `type` fields plus optional `issue_id`, `tool`, `content`, recursive `input`, `output`, and `created_at`; update raw decoder, equality/immutability, relation, and operation cases to remove unsupported `id`, `run_id`, and `role` assumptions.

## 2. Add semantic event models

- [ ] 2.1 Add frozen, keyword-only `RunEvent`, `RunTextEvent`, `RunThinkingEvent`, `RunToolStartedEvent`, `RunToolFinishedEvent`, `RunErrorEvent`, `RunStatusChangedEvent`, and `RunUnknownEvent` models in `multica_py.models.run_events`, with precise shared/context fields and no `Any` or closed provider vocabularies.
- [ ] 2.2 Implement one private total message-to-event converter for `text`, `thinking`, underscore/hyphen tool start and finish spellings, `error`, and unknown nonblank types; preserve the complete raw message and structured tool data in every message-backed event.
- [ ] 2.3 Export every semantic event from `multica_py` and add table-driven runtime and type-check cases proving immutability, `isinstance`/pattern-match narrowing, exact field mapping, unknown-type preservation, and the absence of a one-off async surface.

## 3. Implement incremental bound streaming

- [ ] 3.1 Add validated `since: int = 0` to `IssueResource.run_messages_command()`, `run_messages()`, and `_run_messages_relation_command()`; always render `--since`, preserve task/issue addressing and `OperationOptions`, and update `TaskRun` plus `AutopilotRun` raw relation expectations to use an explicit zero cursor without changing cache behavior.
- [ ] 3.2 Add `TaskRun.stream_events(*, poll_interval: float = 1.0) -> Iterator[RunEvent]` with eager interval validation at first iteration, required client/issue context, incremental reads, ascending sequence normalization, identical duplicate suppression, conflicting-sequence rejection, exact task lookup through `issues.runs(issue_id)`, and sleeps only between nonterminal polls.
- [ ] 3.3 Complete the iterator lifecycle: emit changed nonterminal status once, recognize `completed`/`failed`/`cancelled` or non-null `completed_at`, drain unseen messages to an empty read, emit terminal status last, propagate command failures, and raise an explicit typed error if the refreshed run disappears.
- [ ] 3.4 Add focused mocked-resource iterator cases for initial/advanced cursors, out-of-order rows, identical and conflicting duplicates, unchanged/changed statuses, all terminal outcomes, future status with completion timestamp, tail drain ordering, invalid intervals before I/O, detached/missing issue context, missing target run, propagated transport errors, raw-cache independence, and no `AutopilotRun.stream_events` surface.

## 4. Document the synchronous incremental contract

- [ ] 4.1 Update `docs/api.md` and `docs/service-usage.md` with a concise `Issue.runs` → `TaskRun.stream_events()` example, semantic pattern matching, raw `TaskRun.messages` access, poll interval behavior, natural terminal completion, and the distinction between incremental polling and server push/real-time delivery.
- [ ] 4.2 Update `docs/migration.md` with the breaking `RunMessage` field mapping (`run_id` → `task_id`, ordering → `seq`, semantic kind → `type`/event class, no replacement for fabricated `id`) and state that async streaming waits for an SDK-wide async execution model.
- [ ] 4.3 Update the smallest existing example to show live event handling and ensure API/coverage documentation lists the governed `since` input and public event exports without adding a new example framework or dependency.

## 5. Verify the complete change

- [ ] 5.1 Run focused event, issue-resource, relation, decoder, public-invariant, and approved-contract tests; verify offline test discovery excludes every `tests/live/*` node and fix all failures.
- [ ] 5.2 Run `make pr` (Ruff format/check, source/tests/tools mypy, parallel and serial offline coverage gates, mutation, compatibility, approved contract check, build, and packaging tests), then run `git diff --check`; record successful command proof for review.
