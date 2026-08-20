## Context

The SDK currently has a synchronous `MulticaClient`, synchronous resource/entity methods, synchronous lazy relations, and three executor backends. All CLI-backed public operations already converge on immutable `Command[T]` plans: eager methods call `<method>_command(...).run()`, plans snapshot configuration, and transport owns compatibility checks, process limits, decoding, redaction, and typed error classification. `ManagedProcess` separately owns long-running process collection and cleanup.

Async parity crosses most public modules, but the actual execution seam is narrow. The merged v0.4.28 tree has a synchronous canonical inventory of 194 public methods and 321 operation cases. The design must keep that inventory, command preview, approved upstream contract/descriptors, and `[0.4.28, 0.4.29)` compatibility interval unchanged; derive async coverage separately; work with every installed executor; avoid public `Any`; and add no dependency or second object model.

## Goals / Non-Goals

**Goals:**

- Make all public I/O-bound resource and entity operations naturally awaitable with matching arguments, results, validation, cache effects, and errors.
- Keep the event-loop thread responsive and permit standard `asyncio.gather()` composition while retaining the configured process bound.
- Reuse one `Command`, transport, executor protocol, model set, exception hierarchy, and relation cache.
- Provide awaitable I/O lifecycle operations for `ManagedProcess`, including provider-backed polling.
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

The discovery source is the actual merged public eager/command surface, not a frozen module list. It includes `resources/plugins.py`, `properties.py`, `agent_mcp.py`, `workspace_mcp.py`, `issue_properties.py`, `skills.refresh/search`, bound MCP actions in `entities/agents.py` and `entities/workspaces.py`, and Workspace/Issue/Agent relations R34–R38. Removed `issues.deprioritize` and `workspaces.watch/unwatch` remain absent; `configuration.get()` keeps its v0.4.28 no-key compatibility-alias signature. The existing sync canonical consumer and its 194/321 assertions remain untouched. A separate async parity consumer derives eager siblings and explicit relation/client/process declarations without adding `_async` entrypoints to `contracts/sdk-contract.json` or generated approved descriptors.

`TaskRun` and `AutopilotRun` are the explicit naming collision: their backward-compatible `.messages` property is a `LazyCollection`, while `messages_command()` is already the direct command form. Add `list_messages()` and `list_messages_async()` as the sync/async eager sibling pair over that command. Both accept the same `options`, return the same typed message tuple, preserve detached/missing-task validation and binding, and leave `.messages` cache state unchanged; relation loading remains available through `.messages.all()` / `.messages.all_async()`. The closed inventory declares this pair directly instead of inventing `messages_async()` without a synchronous sibling.

### Keep cancellation honest and backend-neutral

Cancelling the asyncio task cancels the wait and propagates `asyncio.CancelledError` unchanged. Python cannot safely stop an arbitrary running worker thread, and the current executor protocol does not expose an in-flight handle for ordinary `run` calls. Therefore an already-started operation may finish in its worker and perform its existing finalization; operation timeouts remain the bound on underlying work.

Adding backend-specific forced cancellation would require a second lifecycle contract and could leave mutating composite plans or temporary resources in ambiguous states. Documentation and tests pin this boundary rather than claiming stronger behavior.

### Reuse relation commands and one cache coordinator

For command-backed relations, `all_async`, `refresh_async`, and paged `page_async` call the corresponding existing command forms' `run_async`. For loader-only `LazyCollection`, `OffsetLazyCollection`, `CursorLazyCollection`, and `LazyMapping` instances, the async method offloads its corresponding existing synchronous `all`, `refresh`, or `page` path through the standard-library asyncio thread bridge. This reuses loader pagination and normalization rather than requiring a command that the instance cannot construct. Neither path introduces an async cache or duplicate pagination loop. The current condition-based generation coordinator remains the single cache/coalescing/retry point across sync and async all/refresh callers; its blocking loader work and coordinator wait run off the event-loop thread. Cache hits, refresh replacement, metadata, pagination guards, results, and errors therefore match the selected synchronous path.

`prefetch_async` uses a per-call asyncio worker pool (or equivalent task admission gate) sized by `max_parallel`, in addition to the existing shared process semaphore inside command execution. Jobs retain their deduplicated input index. On the first observed failure, the coordinator stops admitting work and cancels jobs that have not started, drains every admitted job so command finalization completes, records all admitted failures, and raises the failure with the smallest input index. Successful completion returns `None`, matching `prefetch()`. This preserves both independent bounds rather than treating the process semaphore as a replacement for `max_parallel`.

### Coordinate all process lifecycle I/O across sync and async callers

Add one thread-safe lifecycle coordinator owned by each `ManagedProcess`, and route both existing synchronous methods and new async delegates through it. Its mutex protects only short state transitions and publication: buffered/streaming ownership, active stdout/stderr stream membership, `open`/`collecting`/`closing`/`finalized` state, one collection owner, cached result or collection failure, an in-flight provider-operation lease count, and exactly-once finalization. Before `poll`, `collect`, stream read, `wait`, `terminate`, or `kill` touches the handle, the caller atomically verifies admission and acquires a lease; it releases the lease and publishes its outcome under the condition after provider I/O. Finalization first prevents general admission, waits for all previously admitted leases, then performs `handle.close`, the optional cleanup callback, and semaphore release exactly once. Cleanup itself is the finalizer's exclusive phase rather than a provider lease. No blocking provider call or cleanup callback runs while the mutex is held, and no handle call starts after finalization has begun.

The first buffered result caller atomically claims output, collection ownership, and a collect lease. Other result callers wait on the coordinator condition and reuse its published result or failure. Terminate/kill acquire their own leases and may advance a collector or blocked stream without taking output ownership. If close overlaps admitted work, it atomically moves to `closing`, blocks ordinary new leases, admits only its terminate/wait/kill control sequence, and waits for all earlier leases to publish before finalizing; it never calls a closed handle or starts a competing collection. If close wins before buffered collection, it discards output and a later result raises the existing `ProcessOutputModeError`. After `closing` or `finalized`, poll returns the recorded terminal exit code (or `None` if none was recorded), result returns the cached result or the existing discarded-output error, close waits for/reuses the published close outcome, and terminate/kill are idempotent no-ops; none performs provider I/O.

Error precedence follows the admitted owner. A state/output rejection before lease admission is returned without provider I/O. Otherwise the admitted provider/collection/control error is primary. Handle-close or cleanup failure is published as the close/finalization error only when no primary error exists; when a primary error already exists it remains primary and the finalization failure is chained for diagnostics. Semaphore release is still attempted once, and all concurrent close callers observe the one published close outcome.

A started collection or cleanup retains coordinator ownership if its async awaiter is cancelled, after which later callers observe the same published result, failure, or discarded closed state. `poll_async`, `wait_async`, `result_async`, `terminate_async`, `kill_async`, and `close_async` offload the corresponding coordinated synchronous lifecycle operation, including remote provider I/O and cleanup. Passive poll/EOF finalization waits until both stdout and stderr generators have ended. Explicit close instead guarantees completion before returning: it revokes every paused/abandoned stream registration, uses its control sequence to advance any currently leased stream read, waits only for those in-flight reads, and then finalizes. A later `next()` on a revoked generator ends without provider I/O. This avoids same-thread `next(stream); close()` deadlock while preserving the invariant that context-manager exit has completed handle close, cleanup, and semaphore release. Concurrent stdout/stderr readers are both advanced and joined before close returns. `__aenter__` returns the same process and `__aexit__` awaits that completed close.

The existing `stdout_lines()` and `stderr_lines()` iterators remain synchronous. Turning iterators into async iterators requires queueing, cross-thread generator ownership, and cancellation policy that is separate from the issue's awaitable operation requirement; consumers needing incremental streaming can continue to dedicate a worker or use buffered `result_async()`.

### Verify parity by extending existing inventories

The existing `OPERATION_CASES`, `discover_public_methods`, canonical consumer, and shared resource execution fixtures remain the source for synchronous transport evidence and stay green at 194 canonical methods / 321 cases. A separate derived async parity gate reuses those rows and fixtures to invoke async siblings, plus explicit bound/relation/client/process declarations; it has no missing-method allowlist and does not mutate the approved upstream contract. This covers new plugin/filesystem, Property/MCP/issue-property, Skill refresh/search, credential/config stdin/file, redaction, staging/cleanup, binding, and cache-invalidation paths. Add small deterministic focused tests for event-loop progress, gather, cancellation, mixed sync/async relation coalescing, and process lifecycle.

## Risks / Trade-offs

- **Cancelled awaiters do not stop started commands** → State this prominently, preserve cleanup in the worker, and require operation timeouts for bounded underlying execution.
- **Many repetitive public methods can drift** → Generate or mechanically derive them and enforce bidirectional discovery/signature equality.
- **Prefetch has a per-call job bound distinct from the process limit** → Use explicit `max_parallel` task admission plus the shared process semaphore and test both bounds independently.
- **Sync and async process lifecycle calls can race** → Linearize state/ownership and provider leases with short mutex sections, block new admission during close, and deterministically test poll/result/control/stream/finalization interleavings and exactly-once published outcomes.
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
