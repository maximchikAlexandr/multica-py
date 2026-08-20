## 1. Async command and process primitives

- [ ] 1.1 Add `Command.run_async()` in `src/multica_py/_internal/commands.py` using the standard-library asyncio thread bridge around the existing plan run; add focused deterministic tests for identical result/exception behavior, event-loop progress, cancellation propagation, command inspection, composite cleanup, and no new executor protocol.
- [ ] 1.2 Add one thread-safe per-process lifecycle state machine in `src/multica_py/process.py` with short mutex sections for buffered/streaming and collection ownership, active stdout/stderr stream membership, `open`/`collecting`/`closing`/`finalized` transitions, result-or-failure publication, and exactly-once handle-close/cleanup/semaphore-release; run provider poll/collect/wait/terminate/kill and cleanup outside the mutex and coordinate waiters with a condition.
- [ ] 1.3 Add `ManagedProcess.poll_async()`, `wait_async()`, `result_async()`, `terminate_async()`, `kill_async()`, `close_async()`, `__aenter__`, and `__aexit__` as offloaded delegates to the coordinated synchronous lifecycle operations, including remote provider I/O and cleanup.
- [ ] 1.4 Add event/barrier-driven lifecycle tests for every sync/async pairing of poll/close/result/terminate/kill with active stdout, stderr, and both streams, plus blocked collection, result-result, close-close, and cancelled-await interleavings; assert event-loop progress, both callers/streams finish, output ownership is preserved, no finalization precedes the last active stream, and handle close, cleanup callback, and semaphore release each occur once.
- [ ] 1.5 Add deterministic handle-close and cleanup-callback exception cases for poll, result, streaming completion, and close; assert remaining finalization steps execute exactly once, exceptions retain the synchronous contract, and provider poll/cleanup never run under the state mutex.
- [ ] 1.6 Run the focused command/process tests plus `uv run mypy src` and fix until the new generic and lifecycle annotations are precise without public `Any`.

## 2. Top-level resource async parity

- [ ] 2.1 Derive the resource async worklist from the merged public eager/command inventory rather than a frozen module list; assert removed `issues.deprioritize` and `workspaces.watch/unwatch` remain absent and `configuration.get_async()` mirrors the v0.4.28 no-key `configuration.get()` alias.
- [ ] 2.2 Add explicit async siblings for all discovered eager methods in existing issue, agent, skill, workspace, project, autopilot, label, repository, runtime, attachment, auth, configuration, daemon, maintenance, setup, user, squad, and nested-resource modules, preserving overloads and delegating to existing command forms.
- [ ] 2.3 Add explicit async siblings in `resources/plugins.py`, `properties.py`, `agent_mcp.py`, `workspace_mcp.py`, and `issue_properties.py`, including `skills.refresh/search`; preserve filesystem/path inputs, credential and config stdin/file channels, presence rules, redaction, staging/cleanup, typed results, binding, and exceptions.
- [ ] 2.4 Extend current canonical table/shared execution fixtures so every new v0.4.28 resource sync/async pair asserts exact argv, mode, stdin, timeout, result, error, redaction, staging/cleanup, and subprocess count; keep `CliResource.command()` synchronous.

## 3. Bound entity action async parity

- [ ] 3.1 Add async siblings for every I/O action on `Issue` in `entities/issues.py`, including refresh, update, assignment, status, ordering, comments, labels, subscribers, and metadata; preserve originating client binding and targeted cache invalidation.
- [ ] 3.2 Add `TaskRun.list_messages()` and `list_messages_async()` as the direct sibling pair over `messages_command()`; retain `.messages` as the lazy relation and prove equivalent options, typed tuple results, validation/errors, binding, and no implicit relation-cache mutation.
- [ ] 3.3 Add async siblings for entity actions in `entities/agents.py`, `entities/workspaces.py`, `entities/skills.py`, `entities/squads.py`, and `entities/projects.py`, explicitly including Agent MCP add/enable/disable/remove and Workspace MCP add/update/remove with identical secret handling, binding, and targeted cache invalidation.
- [ ] 3.4 Add async siblings for entity actions in `entities/autopilots.py`; add `AutopilotRun.list_messages()` and `list_messages_async()` over `messages_command()` while retaining `.messages`, aggregate relation cache behavior, and missing-task-context failures before I/O.
- [ ] 3.5 Extend bound-entity table cases to compare sync and async command, result, exception, cache, and binding behavior, with canonical rows for both `list_messages` pairs and assertions that direct calls leave `.messages` cache unchanged; run focused entity/relation tests and `uv run mypy src tests` for signature parity.

## 4. Lazy relations and client lifecycle

- [ ] 4.1 Add `all_async()` and `refresh_async()` to `LazyCollection` and `LazyMapping`: use existing command forms with `run_async()` when present, otherwise offload the corresponding existing sync loader path through the stdlib asyncio thread bridge.
- [ ] 4.2 Add `page_async()` plus async all/refresh behavior to offset and cursor lazy collections: use existing page/composite commands when present and offload existing sync page/pagination paths for loader-only instances; retain total metadata, cursor pairs, and every empty/repeated/maximum progress guard with identical bounded call counts.
- [ ] 4.3 Add deterministic command-backed and loader-only fixtures for all/refresh/page success, cache hit, failure/retry, pagination guards, and event-loop progress; include Workspace plugins/properties/mcp_servers, Agent mcp_servers, and Issue properties and verify identical binding, invalidation, results, errors, metadata, cache state, and loader/transport call counts.
- [ ] 4.4 Add `MulticaClient.close_async()`, async context management, and `prefetch_async()` with the same origin checks, deduplication, cache effects, and `None` return contract as synchronous client lifecycle/prefetch; use explicit task admission to preserve `max_parallel` independently of the shared process semaphore.
- [ ] 4.5 Add deterministic prefetch tests proving both concurrency ceilings, cancellation of jobs not yet started after failure, draining and cleanup of started jobs, `None` on success, and selection of the smallest failing deduplicated input-job index regardless of completion order.
- [ ] 4.6 Run focused relation, client-scope, concurrency, local executor, SSH, and microsandbox tests to prove all backends use the unchanged synchronous executor contract outside the event-loop thread.

## 5. Closed public surface and typing gates

- [ ] 5.1 Preserve the existing `discover_public_methods`/`OPERATION_CASES` canonical consumer and `test_discovered_public_methods` unchanged and green at 194 synchronous canonical methods / 321 cases; do not add `_async` symbols to its discovered set, approved upstream contract, or generated descriptors.
- [ ] 5.2 Add a separate derived async inventory from the merged eager/command surface plus explicit `TaskRun`/`AutopilotRun` list_messages, relation, client, and process declarations; exclude command builders, relation properties, passive/local helpers, serialization, invalidation, permalinks, `CliResource.command()`, and synchronous line iterators structurally without an allowlist.
- [ ] 5.3 Add a bidirectional async gate: every derived synchronous I/O method has exactly one `_async` sibling, every public `_async` method maps back to its synchronous method or explicit primitive, and normalized inputs plus resolved result annotations are equivalent.
- [ ] 5.4 Update public export and typing tests while confirming `Command` remains the only command abstraction, sync canonical counts/argv stay unchanged, the compatibility interval is `[0.4.28, 0.4.29)`, and no `AsyncClient`, `AsyncCommand`, duplicate models, public `Any`, dependency, approved-contract change, or generated-descriptor change appears.

## 6. Async behavioral verification

- [ ] 6.1 Add deterministic asyncio tests showing two permitted calls overlap under `asyncio.gather()`, results retain gather order, and calls above `max_concurrent_processes` never exceed the existing shared semaphore bound.
- [ ] 6.2 Add cancellation tests showing `asyncio.CancelledError` reaches the awaiter unchanged, the event loop remains responsive, and an already-started fake executor is allowed to finish its existing plan cleanup; use synchronization events rather than timing-only sleeps.
- [ ] 6.3 Add parity cases for classified CLI failures, operation timeout, executable/backend failure, decoding failure, configuration snapshot, redaction, staging/output capture, multi-step success/failure, relation pagination errors, plugin filesystem operations, and MCP/config credential stdin/file inputs through both execution styles using current shared fixtures.
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
