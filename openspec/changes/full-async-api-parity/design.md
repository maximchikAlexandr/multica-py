## Context

The SDK currently has a synchronous `MulticaClient`, synchronous resource/entity methods, synchronous lazy relations, and three executor backends. All CLI-backed public operations already converge on immutable `Command[T]` plans: eager methods call `<method>_command(...).run()`, plans snapshot configuration, and transport owns compatibility checks, process limits, decoding, redaction, and typed error classification. `ManagedProcess` separately owns long-running process collection and cleanup.

Async parity crosses most public modules, but the actual execution seam is narrow. The design must keep command preview authoritative, preserve 163 canonical operations and their signatures, work with every installed executor, avoid public `Any`, and add no dependency or second object model.

## Goals / Non-Goals

**Goals:**

- Make all public I/O-bound resource and entity operations naturally awaitable with matching arguments, results, validation, cache effects, and errors.
- Keep the event-loop thread responsive and permit standard `asyncio.gather()` composition while retaining the configured process bound.
- Reuse one `Command`, transport, executor protocol, model set, exception hierarchy, and relation cache.
- Provide awaitable buffered lifecycle operations for `ManagedProcess`.
- Make completeness mechanically discoverable rather than maintaining a handwritten exception list.

**Non-Goals:**

- Replacing executor backends with native asyncio implementations.
- Guaranteeing termination of an already-started executor call when its awaiter is cancelled.
- Adding async variants for local helpers, command construction/inspection, serialization, passive properties, invalidation, permalinks, or synchronous line iterators.
- Changing approved upstream operations, argv, models, command previews, sync signatures, or the SDK contract generator.

## Decisions

### Put asynchronous execution on the existing `Command`

Add `async def Command.run_async(self) -> T` and offload `self._plan.run` with the Python standard library's asyncio thread bridge. Resource and entity `_async` methods will be one-line delegates to the same `<method>_command()` used by the eager method.

This is the smallest seam that guarantees plan, argv, configuration snapshot, decoding, finalization, redaction, and exception parity. A separate `AsyncCommand`, `AsyncMulticaClient`, async transport, or async executor protocol would duplicate established behavior across local, SSH, and microsandbox backends.

### Keep repetitive async delegates explicit and mechanically verified

Async siblings are structurally uniform, but this repository's public resource and entity methods are handwritten; the approved generated module describes upstream operations rather than owning those Python methods. Add explicit checked-in async methods beside their synchronous siblings, preserving each overload and concrete result annotation. A temporary mechanical edit may produce candidates, but it SHALL NOT become runtime dispatch or a new production generator. The final discovery gate compares sync command-executing methods and async siblings bidirectionally, while the approved SDK contract and generated operation descriptors remain unchanged.

Runtime `__getattr__`, decorators that erase signatures, and dynamic monkey-patching are rejected: they save lines but weaken IDE discovery, overload precision, and closed-surface verification.

### Keep cancellation honest and backend-neutral

Cancelling the asyncio task cancels the wait and propagates `asyncio.CancelledError` unchanged. Python cannot safely stop an arbitrary running worker thread, and the current executor protocol does not expose an in-flight handle for ordinary `run` calls. Therefore an already-started operation may finish in its worker and perform its existing finalization; operation timeouts remain the bound on underlying work.

Adding backend-specific forced cancellation would require a second lifecycle contract and could leave mutating composite plans or temporary resources in ambiguous states. Documentation and tests pin this boundary rather than claiming stronger behavior.

### Reuse relation commands and one cache coordinator

`all_async`, `refresh_async`, and paged `page_async` call the existing relation command forms' `run_async`. They do not introduce async caches or duplicate pagination loops. The current condition-based load coordinator remains the single serialization point across sync and async callers; any blocking coordinator wait is also offloaded so it cannot block the event loop. Cache hits resolve without transport access, and all pagination guards remain in the existing command plan.

`prefetch_async` uses a per-call asyncio worker pool (or equivalent task admission gate) sized by `max_parallel`, in addition to the existing shared process semaphore inside command execution. Jobs retain their deduplicated input index. On the first observed failure, the coordinator stops admitting work and cancels jobs that have not started, drains every admitted job so command finalization completes, records all admitted failures, and raises the failure with the smallest input index. Successful completion returns `None`, matching `prefetch()`. This preserves both independent bounds rather than treating the process semaphore as a replacement for `max_parallel`.

### Coordinate all process lifecycle I/O across sync and async callers

Add one thread-safe lifecycle coordinator owned by each `ManagedProcess`, and route both existing synchronous methods and new async delegates through it. Its mutex protects only short state transitions and publication: output ownership, `open`/`collecting`/`closing`/`finalized` state, one collection owner, cached result or collection failure, and exactly-once handle finalization/semaphore release. No blocking provider `collect`, `wait`, `terminate`, or `kill` call runs while that mutex is held.

The first buffered result caller atomically claims output and collection ownership, then performs `collect` outside the mutex. Other result callers wait on the coordinator condition and reuse its published result or failure. If terminate or kill overlaps collection, its provider signal executes outside the mutex and may unblock the collector; it does not take collection ownership or consume output. If close overlaps an owned collection, close atomically moves to `closing`, sends terminate outside the mutex, waits on the coordinator condition for the existing cleanup grace period, sends kill outside the mutex if the collector is still blocked, and waits for that owner to publish; it never starts a competing provider wait or collection. The collection owner publishes its normal post-signal `ProcessResult` or existing collection failure, and the winning finalizer closes/releases once. If close claims an open process before any result caller claims buffered output, it discards output and owns the existing terminate-wait-kill cleanup; a later result call observes the existing discarded-output `ProcessOutputModeError` without provider collection. Thus the linearization order yields one explicit result-or-closed outcome and control operations can advance a blocked collection without lock inversion.

A started collection or cleanup retains coordinator ownership if its async awaiter is cancelled, after which later callers observe the same published result, failure, or discarded closed state. `wait_async`, `result_async`, `terminate_async`, `kill_async`, and `close_async` offload the corresponding coordinated synchronous lifecycle operation, including microsandbox provider I/O. `__aenter__` returns the same process and `__aexit__` awaits close.

The existing `stdout_lines()` and `stderr_lines()` iterators remain synchronous. Turning iterators into async iterators requires queueing, cross-thread generator ownership, and cancellation policy that is separate from the issue's awaitable operation requirement; consumers needing incremental streaming can continue to dedicate a worker or use buffered `result_async()`.

### Verify parity by extending existing inventories

Canonical operation cases already prove exact transport behavior and command previews. Extend those tables/tests to invoke async siblings against the same expected rows rather than creating a parallel fixture corpus. Add small deterministic focused tests for event-loop progress, gather, cancellation, mixed sync/async relation coalescing, and process lifecycle. Documentation and public-symbol contract tests cover the additive surface.

## Risks / Trade-offs

- **Cancelled awaiters do not stop started commands** → State this prominently, preserve cleanup in the worker, and require operation timeouts for bounded underlying execution.
- **Many repetitive public methods can drift** → Generate or mechanically derive them and enforce bidirectional discovery/signature equality.
- **Prefetch has a per-call job bound distinct from the process limit** → Use explicit `max_parallel` task admission plus the shared process semaphore and test both bounds independently.
- **Sync and async process lifecycle calls can race** → Linearize state/ownership with short mutex sections, run blocking provider calls outside the mutex, and deterministically test blocked-result/close/signal/cancellation interleavings and exactly-once finalization.
- **Blocking relation coordination could leak onto the event loop** → Route every unloaded/coalesced async relation path through offloaded command execution and deterministically test responsiveness.
- **Async and sync calls may race over shared lazy state** → Reuse the existing relation coordinator and generation checks; do not add an independent async lock/cache.
- **Client/process shutdown can block** → Provide async context management and async close methods while keeping existing sync context management unchanged.

## Migration Plan

1. Add and verify `Command.run_async()` and managed-process async lifecycle primitives.
2. Add deterministic async delegates and the closed parity inventory across resources and entities.
3. Add async lazy relations, client lifecycle, and prefetch using the same caches and process semaphore.
4. Extend offline tests, typing, docs, and OpenSpec validation; release as an additive minor feature.

Rollback removes only additive `_async` methods and lifecycle entries; no stored data, wire contract, or synchronous migration is involved.

## Open Questions

None. Native backend cancellation and asynchronous streaming can be proposed separately if measured consumer demand justifies the additional execution contract.
