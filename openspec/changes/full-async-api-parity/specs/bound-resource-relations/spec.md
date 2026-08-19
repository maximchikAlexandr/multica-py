## ADDED Requirements

### Requirement: Async bound entity actions
Every public bound entity action that performs I/O SHALL expose a sibling named `<action>_async` with equivalent arguments and resolved public result type. It SHALL execute the entity's existing `<action>_command()` with `run_async()` and preserve client binding, immutable replacement, relation invalidation, validation, and exception behavior.

#### Scenario: Bound issue action executes asynchronously
- **WHEN** a consumer awaits `issue.set_status_async(status)`
- **THEN** the same command plan and cache effects as `issue.set_status(status)` produce a bound replacement `Issue`

#### Scenario: Detached entity validation is unchanged
- **WHEN** an async action is requested from an entity without required client context
- **THEN** the same typed validation or relation-context error is raised before transport I/O

### Requirement: Async lazy relation loading
`LazyCollection`, `OffsetLazyCollection`, `CursorLazyCollection`, and `LazyMapping` SHALL provide awaitable `all_async()` and `refresh_async()` operations. Paged collections SHALL also provide `page_async()` with the same arguments and page result types as `page()`. Async relation operations SHALL reuse existing command plans and the same per-instance cache, generation, coalescing, retry, pagination guard, metadata, and output ownership state as synchronous relation operations.

#### Scenario: Unloaded relation loads asynchronously
- **WHEN** `await relation.all_async()` is called on an unloaded relation
- **THEN** it executes the existing `all_command()` plan asynchronously and stores the same completed cache value as `all()`

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
