## ADDED Requirements

### Requirement: Async bound entity actions
Every public bound entity action that performs I/O SHALL expose a sibling named `<action>_async` with equivalent arguments and resolved public result type. It SHALL execute the entity's existing `<action>_command()` with `run_async()` and preserve client binding, immutable replacement, relation invalidation, validation, and exception behavior.

#### Scenario: Bound issue action executes asynchronously
- **WHEN** a consumer awaits `issue.set_status_async(status)`
- **THEN** the same command plan and cache effects as `issue.set_status(status)` produce a bound replacement `Issue`

#### Scenario: Detached entity validation is unchanged
- **WHEN** an async action is requested from an entity without required client context
- **THEN** the same typed validation or relation-context error is raised before transport I/O

#### Scenario: Bound MCP actions retain cache invalidation
- **WHEN** sync or async Agent MCP add/enable/disable/remove or Workspace MCP add/update/remove succeeds
- **THEN** both styles use the same command, result binding, validation, secret redaction, and invalidation of the originating entity's `mcp_servers` relation

### Requirement: Direct run message sibling pair
`TaskRun` and `AutopilotRun` SHALL retain the backward-compatible `.messages` lazy-relation property and existing `messages_command()` command builder. Each SHALL additionally expose `list_messages()` and `list_messages_async()` as a direct synchronous/asynchronous sibling pair over `messages_command()`. The pair SHALL accept the same operation options, return the same `tuple[RunMessage, ...]`, and preserve identical client binding, detached or missing-task-context validation, transport errors, and `.messages` cache effects. Direct listing SHALL NOT implicitly mark, replace, or invalidate the `.messages` relation cache.

#### Scenario: Run messages list in either execution style
- **WHEN** a consumer calls `run.list_messages(options=...)` or awaits `run.list_messages_async(options=...)` against equivalent responses
- **THEN** both execute the same `messages_command()` plan and return equivalent typed message tuples with identical errors and binding

#### Scenario: Messages relation remains backward compatible
- **WHEN** a consumer inspects or loads `run.messages` before or after a direct list call
- **THEN** `.messages` remains the same lazy-relation API and the direct call does not seed, replace, or invalidate its cache

#### Scenario: Missing run-message context fails before I/O
- **WHEN** a detached `TaskRun` or an `AutopilotRun` without its required task context invokes either direct listing style
- **THEN** the existing relation-context error is raised before transport I/O

### Requirement: Async lazy relation loading
`LazyCollection`, `OffsetLazyCollection`, `CursorLazyCollection`, and `LazyMapping` SHALL provide awaitable `all_async()` and `refresh_async()` operations. Paged collections SHALL also provide `page_async()` with the same arguments and page result types as `page()`. On a command-backed instance, each async operation SHALL execute its corresponding existing command form with `run_async()`. On a loader-only instance, it SHALL offload the corresponding existing synchronous `all()`, `refresh()`, or `page()` path through the standard-library asyncio thread bridge. Both paths SHALL reuse the same per-instance cache, generation, coalescing, retry, pagination guard, metadata, result, and error semantics as their synchronous counterpart without blocking the event-loop thread.

#### Scenario: Unloaded relation loads asynchronously
- **WHEN** `await relation.all_async()` is called on an unloaded command-backed relation
- **THEN** it executes the existing `all_command()` plan with `run_async()` and stores the same completed cache value as `all()`

#### Scenario: Loader-only relation loads asynchronously
- **WHEN** `all_async()`, `refresh_async()`, or `page_async()` is awaited on a loader-only relation while its synchronous loader is blocked by a deterministic barrier
- **THEN** the corresponding existing synchronous path runs off the event-loop thread, another event-loop task progresses, and release of the barrier produces the same value, cache or metadata effect, and error as the synchronous call

#### Scenario: Loaded relation is an async cache hit
- **WHEN** `await relation.all_async()` is called on a completely loaded relation
- **THEN** it returns the cached value without transport I/O

#### Scenario: Async refresh forces reload
- **WHEN** `await relation.refresh_async()` is called
- **THEN** it uses the existing refresh command and generation semantics to replace the cache only after successful completion

#### Scenario: Paged relation preserves guards
- **WHEN** async pagination encounters an empty continuation page, repeated offset or cursor, page limit, or item limit
- **THEN** it raises the same typed pagination error with the same bounded transport call count as synchronous pagination

#### Scenario: Concurrent sync and async loads coalesce
- **WHEN** synchronous and asynchronous callers overlap on one relation instance
- **THEN** the existing relation coordinator permits one active load and all successful waiters observe the same completed generation

#### Scenario: Both relation execution paths retain parity
- **WHEN** the same all, refresh, cache-hit, loader failure/retry, or pagination-guard case is exercised on command-backed and loader-only fixtures
- **THEN** each async operation matches its corresponding synchronous result, exception, bounded loader or transport call count, generation, metadata, and cache state

#### Scenario: New v0.4.28 relations are included
- **WHEN** async relation inventory and table-driven cases discover Workspace, Agent, and Issue relations
- **THEN** Workspace plugins/properties/mcp_servers, Agent mcp_servers, and Issue properties are covered alongside the pre-existing relations with identical command, binding, cache, invalidation, and error semantics
