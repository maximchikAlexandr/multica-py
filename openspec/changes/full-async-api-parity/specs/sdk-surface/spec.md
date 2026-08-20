## ADDED Requirements

### Requirement: Async resource surface
The SDK SHALL expose async counterparts for every public I/O-bound resource method while retaining every existing synchronous method unchanged. Async resource calls SHALL construct the same existing command form and await `Command.run_async()` so arguments, operation options, validation rules, transport behavior, binding, result models, and exceptions cannot drift between execution styles. Because an `async def` body begins when awaited, an async sibling SHALL apply the same local validation when awaited and SHALL raise the same validation error before any transport I/O; it SHALL NOT promise validation at the earlier function-call expression.

#### Scenario: Async get returns the same entity type
- **WHEN** `await client.issues.get_async(issue_id)` succeeds
- **THEN** it returns the same bound `Issue` type and originating client scope as `client.issues.get(issue_id)`

#### Scenario: Async mutation preserves behavior
- **WHEN** an async resource mutation succeeds or fails
- **THEN** its result, cache invalidation, and public exception behavior match the synchronous method for the same command response

#### Scenario: Synchronous compatibility remains intact
- **WHEN** existing synchronous consumer code runs after the async API is added
- **THEN** its method signatures, return types, command previews, and runtime behavior remain backward compatible

#### Scenario: Invalid async input fails before transport I/O
- **WHEN** a consumer awaits an async resource call with input rejected by its synchronous command builder
- **THEN** the same validation error is raised and no transport or executor I/O starts

#### Scenario: Merged v0.4.28 resource surface is complete
- **WHEN** async resource discovery runs against the merged public/command inventory
- **THEN** it includes Plugin, Property, Agent MCP, Workspace MCP, Issue Property, and Skill refresh/search eager methods; excludes removed issue deprioritize and workspace watch/unwatch methods; and preserves the no-key `configuration.get()` signature and result

#### Scenario: Sensitive and filesystem operations retain execution evidence
- **WHEN** plugin/filesystem operations or MCP/configuration operations with credential, stdin, or file inputs execute through sync and async siblings
- **THEN** canonical table-driven cases assert identical complete command plans, validation, redaction, staging ownership, cleanup, typed results, errors, and subprocess counts

### Requirement: Async client lifecycle and prefetch
`MulticaClient` SHALL support `async with` and an awaitable `close_async()` that preserve the existing close behavior without blocking the event loop. The client SHALL expose `prefetch_async()` with the same relation selection, origin validation, deduplication, cache effects, and `None` return contract as `prefetch()`. It SHALL limit started relation jobs to the call's `max_parallel` value while every underlying executor call remains subject to the client's shared process semaphore. After any job fails, it SHALL prevent jobs not yet started from starting, await every already-started job through completion and cleanup, and then raise the captured failure with the smallest deduplicated input-job index.

#### Scenario: Client closes asynchronously
- **WHEN** execution leaves `async with MulticaClient(...)`
- **THEN** the client's existing transport and executor resources are closed through the async lifecycle path

#### Scenario: Relations are prefetched asynchronously
- **WHEN** `prefetch_async()` receives valid bound relations
- **THEN** it loads them through their async command path, produces the same cache effects as synchronous prefetch, and resolves to `None`

#### Scenario: Prefetch retains both concurrency bounds
- **WHEN** `prefetch_async(..., max_parallel=N)` has more than `N` unloaded deduplicated relations and the client process limit is `M`
- **THEN** no more than `N` relation jobs are started concurrently and no more than `M` executor calls are active concurrently

#### Scenario: Prefetch failure is deterministic after cleanup
- **WHEN** multiple started prefetch jobs fail in an order different from their deduplicated input-job order
- **THEN** jobs not yet started are cancelled, all started jobs are drained, and the exception from the smallest failing input-job index is raised
