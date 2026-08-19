## ADDED Requirements

### Requirement: One async execution path
The SDK SHALL expose `Command.run_async()` on the existing `Command[T]` abstraction. It SHALL execute the same immutable plan, configuration snapshot, argv, decoding, finalization, cache effects, result type, and public exception behavior as `Command.run()` without blocking the caller's asyncio event-loop thread. The SDK SHALL NOT introduce a separate async command, client, transport, request model, result model, exception hierarchy, or runtime dependency.

#### Scenario: One command supports either execution style
- **WHEN** a consumer builds a command and executes it with `run()` or `await run_async()` against equivalent responses
- **THEN** both paths send the same transport request and return equivalent values of the same public type

#### Scenario: Command inspection remains execution-independent
- **WHEN** a consumer reads `command.commands` before asynchronous execution
- **THEN** inspection performs no I/O and reports the same immutable plan that `run_async()` executes

#### Scenario: Async execution does not block the event loop
- **WHEN** a command is awaiting blocking executor I/O
- **THEN** another scheduled asyncio task can make progress on the event-loop thread

### Requirement: Complete async naming and signature parity
Every public synchronous SDK method that can perform CLI, process, filesystem, or remote-executor I/O SHALL expose a sibling named `<method>_async`. Each sibling SHALL accept the same operation arguments and configuration options, preserve overload distinctions, and return an awaitable whose resolved value has the synchronous method's public result type. Purely local properties, command builders, validation helpers, serialization, command inspection, cache invalidation, and permalink helpers SHALL remain synchronous and SHALL NOT receive artificial async variants.

#### Scenario: Resource operation has an async sibling
- **WHEN** a public resource method executes an existing `<method>_command()` plan
- **THEN** `<method>_async()` exists with an equivalent input signature and delegates to that plan's `run_async()`

#### Scenario: Local helper has no artificial sibling
- **WHEN** a public method performs only local computation or inspection
- **THEN** the async inventory excludes an `_async` variant for that method

#### Scenario: Overloads remain typed
- **WHEN** a synchronous I/O method has overloads with distinct inputs or result types
- **THEN** its async sibling preserves the corresponding overloads and precise awaitable result annotations without public `Any`

### Requirement: Standard asyncio composition and bounded execution
Independent async SDK calls SHALL compose with `asyncio.gather()` and SHALL retain the client's existing process-concurrency limit. A waiting coroutine SHALL be cancellable using standard asyncio cancellation. Cancellation SHALL stop waiting and raise `asyncio.CancelledError`; because execution reuses synchronous executor backends, it SHALL NOT claim that cancellation terminates a CLI operation that has already started. Existing operation timeouts SHALL remain the mechanism that bounds underlying execution.

#### Scenario: Independent calls overlap
- **WHEN** two independent async resource calls are passed to `asyncio.gather()` and the configured process limit permits both
- **THEN** both may execute concurrently and results retain input order under standard gather semantics

#### Scenario: Existing concurrency limit is retained
- **WHEN** concurrent async calls exceed the client's configured maximum process count
- **THEN** the existing shared process semaphore limits active executor calls without blocking the event-loop thread

#### Scenario: Awaiting caller is cancelled
- **WHEN** a task awaiting an already-started async SDK call is cancelled
- **THEN** it raises `asyncio.CancelledError`, does not translate cancellation into a Multica exception, and documentation states that the underlying executor operation may continue until completion or timeout

### Requirement: Awaitable managed process lifecycle
`ManagedProcess` SHALL expose async counterparts for every lifecycle operation that can perform process-provider I/O: `wait_async()`, `result_async()`, `terminate_async()`, `kill_async()`, and `close_async()`. It SHALL support `async with` by delegating asynchronous exit to `close_async()`. Synchronous and asynchronous lifecycle paths SHALL use one thread-safe per-process lifecycle coordinator. Its mutex SHALL serialize only state transitions, output and collection ownership, result-or-failure publication, close state, handle finalization, and semaphore release; it SHALL NOT be held during blocking provider `collect`, `wait`, `terminate`, or `kill` I/O. A control or close path SHALL therefore be able to signal and advance an active blocked collection without waiting for that collection while holding the mutex. Concurrent result, close, terminate, kill, and cancellation paths SHALL preserve timeout and cached-result behavior and SHALL finalize the handle and release the semaphore exactly once. Synchronous streaming iterators SHALL remain unchanged in this change.

#### Scenario: Process result is awaited
- **WHEN** a consumer awaits `process.result_async(timeout)`
- **THEN** the event loop remains responsive and the resolved `ProcessResult` equals the synchronous result contract

#### Scenario: Process is closed with async context management
- **WHEN** execution leaves `async with managed_process`
- **THEN** `close_async()` applies the existing terminate-wait-kill cleanup policy and releases the process semaphore exactly once

#### Scenario: Buffered output ownership is shared
- **WHEN** synchronous and asynchronous lifecycle methods are mixed on one managed process
- **THEN** they observe one result cache and the existing single-owner buffered-versus-streaming rules

#### Scenario: Remote process signals do not block the event loop
- **WHEN** a consumer awaits `terminate_async()` or `kill_async()` while the process handle performs provider I/O
- **THEN** the provider call runs outside the event-loop thread and preserves the synchronous signal behavior and exception contract

#### Scenario: Concurrent result and close have one finalization
- **WHEN** deterministic synchronization overlaps sync or async result collection with sync or async close on one managed process
- **THEN** close signals terminate, waits on the coordinator condition, and signals kill after the existing cleanup grace period if still needed without starting a competing provider wait or collection; both callers finish, and the collection owner publishes its `ProcessResult` or existing collection failure before the handle is closed and the semaphore is released exactly once

#### Scenario: Close wins before buffered collection
- **WHEN** close claims an open managed process before a result caller claims buffered output
- **THEN** close owns cleanup and discards output, and the later result caller raises the existing discarded-output `ProcessOutputModeError` without starting provider collection

#### Scenario: Signal advances a blocked collection
- **WHEN** a barrier holds provider collection after it owns buffered output and a concurrent sync or async terminate or kill call signals the handle
- **THEN** the signal executes without waiting on the coordinator mutex, both callers finish, the collector preserves the normal post-signal result-or-failure contract, and finalization and semaphore release occur exactly once

#### Scenario: Cancellation does not corrupt lifecycle state
- **WHEN** a task awaiting a started managed-process lifecycle operation is cancelled while another sync or async lifecycle caller proceeds
- **THEN** cancellation reaches that awaiter unchanged, the started coordinator operation completes safely, and later callers observe one consistent result-or-closed state with exactly-once finalization
