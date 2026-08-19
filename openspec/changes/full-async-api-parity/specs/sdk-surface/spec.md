## ADDED Requirements

### Requirement: Async resource surface
The SDK SHALL expose async counterparts for every public I/O-bound resource method while retaining every existing synchronous method unchanged. Async resource calls SHALL construct the same existing command form and await `Command.run_async()` so arguments, operation options, validation timing, transport behavior, binding, result models, and exceptions cannot drift between execution styles.

#### Scenario: Async get returns the same entity type
- **WHEN** `await client.issues.get_async(issue_id)` succeeds
- **THEN** it returns the same bound `Issue` type and originating client scope as `client.issues.get(issue_id)`

#### Scenario: Async mutation preserves behavior
- **WHEN** an async resource mutation succeeds or fails
- **THEN** its result, cache invalidation, and public exception behavior match the synchronous method for the same command response

#### Scenario: Synchronous compatibility remains intact
- **WHEN** existing synchronous consumer code runs after the async API is added
- **THEN** its method signatures, return types, command previews, and runtime behavior remain backward compatible

### Requirement: Async client lifecycle and prefetch
`MulticaClient` SHALL support `async with` and an awaitable `close_async()` that preserve the existing close behavior without blocking the event loop. The client SHALL expose `prefetch_async()` with the same relation selection, origin validation, deduplication, bounded parallelism, cache effects, and return contract as `prefetch()`.

#### Scenario: Client closes asynchronously
- **WHEN** execution leaves `async with MulticaClient(...)`
- **THEN** the client's existing transport and executor resources are closed through the async lifecycle path

#### Scenario: Relations are prefetched asynchronously
- **WHEN** `prefetch_async()` receives valid bound relations
- **THEN** it loads them through their async command path with the same caches and result tuple contract as synchronous prefetch
