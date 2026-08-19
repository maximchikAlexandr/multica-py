## 1. Async command and process primitives

- [ ] 1.1 Add `Command.run_async()` in `src/multica_py/_internal/commands.py` using the standard-library asyncio thread bridge around the existing plan run; add focused deterministic tests for identical result/exception behavior, event-loop progress, cancellation propagation, command inspection, composite cleanup, and no new executor protocol.
- [ ] 1.2 Add one thread-safe per-process lifecycle state machine in `src/multica_py/process.py` with short mutex sections for output/collection ownership, `open`/`collecting`/`closing`/`finalized` transitions, result-or-failure publication, and exactly-once finalization/release; run provider collect/wait/terminate/kill calls outside the mutex and coordinate waiters with a condition.
- [ ] 1.3 Add `ManagedProcess.wait_async()`, `result_async()`, `terminate_async()`, `kill_async()`, `close_async()`, `__aenter__`, and `__aexit__` as offloaded delegates to the coordinated synchronous lifecycle operations, including remote provider I/O.
- [ ] 1.4 Add event/barrier-driven lifecycle tests for every sync/async pairing of blocked result collection with terminate, kill, and close, plus result-result, close-close, and cancelled-await interleavings; assert both callers finish without mutex deadlock, control I/O advances the blocked handle, one output owner preserves the post-signal result-or-failure contract, close-before-result raises discarded-output `ProcessOutputModeError` without collection, and handle finalization/semaphore release occur exactly once.
- [ ] 1.5 Run the focused command/process tests plus `uv run mypy src` and fix until the new generic and lifecycle annotations are precise without public `Any`.

## 2. Top-level resource async parity

- [ ] 2.1 Add explicit `<method>_async(...)` siblings for all eager I/O methods in `issues.py`, `issue_comments.py`, `issue_labels.py`, `issue_metadata.py`, and `issue_subscribers.py`; preserve overloads and delegate each sibling to its existing command form's `run_async()`.
- [ ] 2.2 Add explicit async siblings in `agents.py`, `agent_skills.py`, `skills.py`, `skill_files.py`, `squads.py`, and `squad_members.py`, preserving all direct-input signatures, overloads, bound result conversion, and exceptions.
- [ ] 2.3 Add explicit async siblings in `projects.py`, `project_resources.py`, `workspaces.py`, `autopilots.py`, `labels.py`, `repositories.py`, and `runtimes.py`, preserving pagination, presence-aware inputs, action results, and operation options.
- [ ] 2.4 Add explicit async siblings in `attachments.py`, `auth.py`, `configuration.py`, `daemon.py`, `maintenance.py`, `setup.py`, and `users.py`; preserve attachment staging/cleanup, auth overload result distinctions, spawn results, stdin, timeouts, and secret redaction. Keep `CliResource.command()` synchronous because it only constructs and returns a `Command` without I/O.
- [ ] 2.5 Extend the existing canonical operation cases so each resource async sibling is executed against the same exact argv, mode, stdin, timeout, result, exception, and subprocess-count expectations as its synchronous method; run focused resource unit and contract tests.

## 3. Bound entity action async parity

- [ ] 3.1 Add async siblings for every I/O action on `Issue` and `TaskRun` in `entities/issues.py`, including refresh, update, assignment, status, ordering, comments, labels, subscribers, metadata, and messages; preserve originating client binding and targeted cache invalidation.
- [ ] 3.2 Add async siblings for entity actions in `entities/agents.py`, `entities/skills.py`, `entities/squads.py`, and `entities/projects.py`; preserve detached-context validation, immutable replacement, and relation invalidation.
- [ ] 3.3 Add async siblings for entity actions in `entities/autopilots.py`, including trigger mutations and run messages; preserve aggregate relation cache seeding/invalidation and missing-task-context failures before I/O.
- [ ] 3.4 Extend bound-entity table cases to compare sync and async command, result, exception, cache, and binding behavior; run focused entity/relation tests and `uv run mypy src tests` for overload parity.

## 4. Lazy relations and client lifecycle

- [ ] 4.1 Add `all_async()` and `refresh_async()` to `LazyCollection` and `LazyMapping` by awaiting their existing command forms; prove loaded cache hits perform zero I/O and failed refreshes retain the prior generation.
- [ ] 4.2 Add `page_async()` plus async all/refresh behavior to offset and cursor lazy collections by reusing existing page/composite commands; retain total metadata, cursor pairs, and every empty/repeated/maximum progress guard with identical bounded call counts.
- [ ] 4.3 Verify overlapping sync and async loads on one relation use the existing coordinator and completed cache generation without blocking the event-loop thread; add deterministic synchronization tests for success, failure/retry, invalidation, and refresh overlap.
- [ ] 4.4 Add `MulticaClient.close_async()`, async context management, and `prefetch_async()` with the same origin checks, deduplication, cache effects, and `None` return contract as synchronous client lifecycle/prefetch; use explicit task admission to preserve `max_parallel` independently of the shared process semaphore.
- [ ] 4.5 Add deterministic prefetch tests proving both concurrency ceilings, cancellation of jobs not yet started after failure, draining and cleanup of started jobs, `None` on success, and selection of the smallest failing deduplicated input-job index regardless of completion order.
- [ ] 4.6 Run focused relation, client-scope, concurrency, local executor, SSH, and microsandbox tests to prove all backends use the unchanged synchronous executor contract outside the event-loop thread.

## 5. Closed public surface and typing gates

- [ ] 5.1 Extend public method discovery to derive in-scope async methods from command-executing eager resource/entity methods, excluding command builders, passive/local helpers, serialization, invalidation, permalinks, `CliResource.command()`, and synchronous line iterators by structural rules rather than a missing-method allowlist.
- [ ] 5.2 Add a bidirectional gate: every derived synchronous I/O method has exactly one `_async` sibling, every public `_async` method maps to a derived synchronous method or an explicitly declared client/relation/process lifecycle primitive, and normalized inputs plus resolved result annotations are equivalent.
- [ ] 5.3 Update public export, API contract, and typing tests for additive async members while confirming `Command` remains the only command abstraction, approved operation counts/argv stay unchanged, and no `AsyncClient`, `AsyncCommand`, duplicate models, public `Any`, or new dependency appears.

## 6. Async behavioral verification

- [ ] 6.1 Add deterministic asyncio tests showing two permitted calls overlap under `asyncio.gather()`, results retain gather order, and calls above `max_concurrent_processes` never exceed the existing shared semaphore bound.
- [ ] 6.2 Add cancellation tests showing `asyncio.CancelledError` reaches the awaiter unchanged, the event loop remains responsive, and an already-started fake executor is allowed to finish its existing plan cleanup; use synchronization events rather than timing-only sleeps.
- [ ] 6.3 Add parity cases for classified CLI failures, operation timeout, executable/backend failure, decoding failure, configuration snapshot, redaction, staging/output capture, multi-step success/failure, and relation pagination errors through both execution styles.
- [ ] 6.4 Add invalid-input async cases that await resource and entity delegates, assert the synchronous validation class/message, and prove zero transport/executor calls.
- [ ] 6.5 Run `uv run pytest -m "not live" --collect-only` and confirm async additions do not collect live tests or introduce serial markers outside the existing process/live boundaries.

## 7. Documentation

- [ ] 7.1 Update `docs/api.md` with the `_async` convention, `Command.run_async()`, async client/process lifecycle, precise typing parity, and the list of local helpers that intentionally remain synchronous.
- [ ] 7.2 Update `docs/service-usage.md` with paired sync/async resource, bound action, relation, command, `asyncio.gather()`, and `async with` examples; state that cancellation stops awaiting but may not terminate an already-started executor call and recommend operation timeouts for an underlying bound.
- [ ] 7.3 Update README, migration, and compatibility/release documentation where primary workflows or public surface guarantees are listed; describe the feature as additive and do not imply native backend cancellation or async line streaming.
- [ ] 7.4 Extend documentation contract tests so examples, cancellation wording, and synchronous compatibility statements cannot drift.

## 8. Final verification

- [ ] 8.1 Run `openspec validate full-async-api-parity` and `openspec validate --specs`; resolve every delta/spec validation error.
- [ ] 8.2 Run `uv run ruff check`, `uv run ruff format --check`, `uv run mypy src`, and `uv run mypy tests`; fix until green.
- [ ] 8.3 Run approved contract validation/check and package validation through the repository's existing commands; confirm `contracts/sdk-contract.json` and generated upstream operation descriptors have not changed merely to add execution style.
- [ ] 8.4 Run `uv run pytest -m "not live"` and the closed async inventory test end to end; confirm exact sync/async parity, no live collection, and unchanged synchronous behavior.
