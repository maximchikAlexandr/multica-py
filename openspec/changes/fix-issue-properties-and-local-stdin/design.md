## Context

The approved MYL-422 audit identified two independent violations in existing code.

`_property_relation_initial()` in `src/multica_py/entities/issues.py` currently accepts any mapping as a loaded `LazyMapping[str, PropertyValue]`. Ordinary issue list/get responses contain a UUID-keyed JSON value map, so `Issue.properties` can return strings or other JSON values even though the public relation promises name-keyed `PropertyValue` objects. The authoritative typed path already exists at `IssuePropertyResource.list()` and `IssueResource._properties_relation_command()`.

`run_with_timeout()` writes all stdin synchronously before `_communicate_until_exit()` starts draining stdout and stderr. `LocalExecutor.spawn()` performs the same synchronous write before returning a handle. A child that fills an output pipe before reading a large input can therefore deadlock outside effective timeout supervision. The code already has process-group cleanup, output-ownership rules, stream pumps, and retryable collection semantics that must be preserved.

The approved base is `39700e7e7316489646ace220838674d055654699` on `main`. This is a corrective change to the existing property-resource and subprocess-transport contracts; it does not change the Multica CLI protocol.

## Goals / Non-Goals

**Goals:**

- Keep raw issue property projection data available for projection/serialization compatibility while making the public relation typed on every supported response shape.
- Prevent local pipe deadlocks by servicing input and both output streams concurrently under the existing timeout and cancellation lifecycle.
- Make spawned initial stdin asynchronous from the caller's perspective and lossless for later buffered collection.
- Prove the fixes through public issue APIs and real child processes using payloads larger than pipe capacity.

**Non-Goals:**

- No change to property catalog/value CLI commands, property resolution flags, metadata, or the public `PropertyValue` model.
- No new public raw-properties accessor; the existing issue projection/serialization is the compatibility surface.
- No redesign of remote executors, terminal-mode interactive stdin, output-ownership semantics, cancellation APIs, or process-group signaling.
- No work on MYL-422 item P3, no new dependency, and no new general-purpose concurrency framework.

## Decisions

### 1. Validate an eager property snapshot structurally; otherwise lazy-load it

`_property_relation_initial()` will return an initial typed mapping only when the projection consists entirely of complete resolved rows that can be converted to `PropertyValue`. A UUID-to-JSON-value mapping, including an empty raw mapping when its shape cannot prove resolved rows, will not initialize the typed relation. `Issue.properties` will then use the existing `issues.properties.list` loader/command loader. Raw projection data remains in `_property_projection`/`_projection` for `to_dict()` and fields-selected compatibility.

Alternative considered: wrap raw values in synthetic `PropertyValue` instances. Rejected because names and types are absent and fabrication would preserve the contract violation. Alternative considered: discard the raw projection. Rejected because list/get projection compatibility is explicitly required.

### 2. Let `Popen.communicate` own synchronous stdin/output multiplexing

`run_with_timeout()` will pass stdin into the first bounded `communicate` attempt rather than writing it beforehand. Retry iterations after `TimeoutExpired` will continue the same communication without resubmitting input, while cancellation and deadline checks retain the existing terminate/escalate/cleanup path. This uses the standard-library primitive already responsible for concurrently feeding stdin and draining both outputs.

Alternative considered: add three bespoke threads to the synchronous path. Rejected because `communicate(input=...)` already solves the same exchange with less state and preserves exact bytes.

### 3. Reuse the handle's pipe pumps for spawned initial I/O

For a spawned request with initial stdin, `LocalProcessHandle` will take ownership of that payload. It will start the existing stdout/stderr pump mechanism and a single private stdin-delivery worker before returning. Buffered collection on this mode will wait with the existing effective timeout and assemble bytes from the pump queues; streaming continues to consume the same queues under the existing single-owner rule. A collection timeout will leave workers and queues intact so a retry can finish without resending input. The stdin worker closes only the owned stdin pipe after exactly one delivery.

Requests without initial stdin retain the current direct `communicate` collection path. This bounds the change to the unsafe mode and avoids altering ordinary managed-process behavior.

Alternative considered: defer initial stdin until `collect()`. Rejected because `wait()` or a delayed collector could leave the child blocked indefinitely. Alternative considered: a background `communicate()` plus a second foreground `communicate()`. Rejected because concurrent ownership of `Popen` pipes is unsafe and incompatible with streaming.

### 4. Use deterministic real-process fixtures above pipe capacity

The existing `tests/fixtures/child_process.py` gains narrowly scoped modes that coordinate with release/ready files and exchange repeated byte chunks. Component tests will use payloads comfortably above common pipe capacities, verify exact byte counts/content, prove spawn returns while reading is gated, and exercise the existing timeout/cleanup exception path. Unit tests will cover property relation loading and handle state transitions without duplicating component behavior.

Alternative considered: mock only `Popen.write`/`communicate`. Rejected because mocks cannot demonstrate an OS-pipe deadlock regression.

### 5. Ponytail full gate: introduce no new subsystem

No new subsystem is necessary. The existing alternatives are `IssuePropertyResource`, `LazyMapping`, `Popen.communicate`, and `LocalProcessHandle` pipe pumps; all are retained and extended at their current ownership seams. New executor types, async frameworks, public options, and dependencies are removed from consideration.

## Risks / Trade-offs

- **Empty property projections are shape-ambiguous** → Treat them as non-authoritative for the typed relation and perform one property-list load; this favors type correctness over avoiding a request whose emptiness cannot be proven authoritative.
- **Background spawned I/O introduces thread lifecycle edges** → Reuse existing daemon pump conventions, keep one writer, make payload delivery exactly-once, preserve queues across timeout retries, and join owned workers during close.
- **Timeout cleanup can race active I/O workers** → Termination remains process-group-owned; workers tolerate closed pipes and collection drains already-captured bytes without replacing the timeout exception.
- **Pipe capacity varies by operating system** → Fixtures use payloads substantially larger than typical capacities and readiness/release coordination rather than timing alone.
- **Raw projection and typed relation show different key spaces by design** → Tests name both surfaces explicitly: UUID keys remain projection data, property names belong to `Issue.properties`.

## Migration Plan

No data or API migration is required. Implement both corrections and focused regressions, then run strict OpenSpec validation, focused tests, the offline suite, Ruff, and mypy. Rollback is the single implementation commit/PR because no persisted state or external contract changes.

## Open Questions

None. The authoritative typed property source, stdin ownership, timeout behavior, compatibility boundary, and test strategy are fixed by the delta specs.
