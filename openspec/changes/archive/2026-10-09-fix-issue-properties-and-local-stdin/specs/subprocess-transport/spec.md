## MODIFIED Requirements

### Requirement: Managed process lifecycle
The SDK MUST expose managed processes with bounded concurrency, timeout
cancellation, escalation, and descendant cleanup. A root client and views
derived through `with_*()` MUST share exactly one `ProcessSemaphore` while
remaining otherwise independent clients with distinct immutable configuration,
transport, services, and close behavior.

For a local spawned handle using buffered pipe pumps, each undrained stdout or
stderr queue SHALL retain at most 256 chunks of 4096 bytes (1 MiB) at a time.
If either queue would exceed that resident-capture bound, the handle SHALL
record a capture failure, terminate the process through the existing local
process-group cleanup path, and raise `ProcessOutputCaptureError` rather than
returning a partial `ExecutionResult`. The bound applies to resident queued
data while collection is not draining; captures that remain within the bound
retain the existing complete-output and exact-byte behavior.

After a capture failure, `close()` SHALL close owned pipes, cancel the initial
stdin worker, join the stdin and output-pump workers within bounded intervals,
and escalate from terminate to kill when a worker or process remains live.
The caller's subsequent `wait()` SHALL reap the terminated process; no live
stdin or output-pump worker may remain after this cleanup sequence.

#### Scenario: Timed processes clean up descendants
- **WHEN** the timeout process case expires
- **THEN** parent and descendant are absent

#### Scenario: Derived clients share concurrency only
- **WHEN** root and derived client views invoke operations concurrently
- **THEN** all invocations are bounded by the same `max_processes` semaphore without a shared runtime, transport registry, identity map, or family closed state

#### Scenario: Derived configuration reaches transport
- **WHEN** a relation loads from an entity returned by a derived client view
- **THEN** exact cwd, profile, workspace, environment, stdin, and timeout from that view reach its controlled transport

#### Scenario: Client views close independently
- **WHEN** one root or derived view closes
- **THEN** other views remain usable and already-started calls follow existing transport timeout/cancellation behavior

#### Scenario: Prefetch shares the process limit
- **WHEN** relation prefetch runs with `max_parallel=N`
- **THEN** executor concurrency observes `N` while each CLI process also observes the shared `max_processes` semaphore

#### Scenario: Spawn command plan retains spawn execution
- **WHEN** a `Command` constructed from a `spawn`-mode operation (e.g. `daemon.start_command()`) is run
- **THEN** `CliTransport.spawn` is called and a `ManagedProcess` is returned; neither `run_bytes` nor `run_text` is called for that step

#### Scenario: ManagedProcess collects buffered output
- **WHEN** `ManagedProcess.result()` is called on a spawned process whose output has not been streamed and each captured stream remains within its resident bound
- **THEN** it routes through `ProcessHandle.collect()` and returns the complete buffered stdout/stderr bytes and exit code as an `ExecutionResult`

#### Scenario: Buffered collection and streaming are mutually exclusive
- **WHEN** `result()` (buffered) is called after `stdout_lines()` has been consumed (or vice versa)
- **THEN** a `RuntimeError` is raised because output is single-owner

#### Scenario: ManagedProcess wraps a ProcessHandle
- **WHEN** a long-running operation spawns a process through any executor
- **THEN** the returned `ManagedProcess` wraps that executor's `ProcessHandle` and `stdout_lines`/`stderr_lines` route through the handle

#### Scenario: Remote pid is not assumed
- **WHEN** a non-local executor spawns a process that has no controller-visible Unix PID
- **THEN** `ManagedProcess.pid` is `None` and `ManagedProcess.id` exposes the provider-specific identity

#### Scenario: Local terminate guarantees process-group cleanup
- **WHEN** `ManagedProcess.terminate()` or `kill()` is called under `LocalExecutor`
- **THEN** the process and its descendants are terminated via process-group signaling and descendant cleanup is guaranteed

#### Scenario: Remote process control follows the executor guarantee
- **WHEN** `ManagedProcess.terminate()` or `kill()` is called under a non-local executor
- **THEN** Microsandbox sends the documented per-command signal, SSH closes its channel on a best-effort basis, another provider follows its documented and provider-tested behavior, and no remote executor implies descendant cleanup unless it explicitly guarantees it

#### Scenario: Derived clients share concurrency and executor
- **WHEN** root and derived client views invoke operations concurrently
- **THEN** all invocations are bounded by the same `max_processes` semaphore AND share the same `CommandExecutor` without a shared runtime, transport registry, identity map, or family closed state

#### Scenario: Derived configuration reaches the executor
- **WHEN** a relation loads from an entity returned by a derived client view
- **THEN** exact cwd, profile, workspace, environment overrides, stdin, and timeout from that view reach its executor as an `ExecutionRequest`

#### Scenario: Resident capture overflow is typed and bounded
- **WHEN** a spawned child writes more than 256 chunks of 4096 bytes to stdout or stderr before buffered collection drains that stream
- **THEN** local capture stops retaining data, terminates the process, and raises `ProcessOutputCaptureError` without returning a partial result

#### Scenario: Capture overflow cleanup is reapable and worker-free
- **WHEN** the caller handles `ProcessOutputCaptureError` and closes the spawned handle
- **THEN** owned pipes are closed, the initial-stdin worker and both output-pump workers are no longer alive, and a subsequent bounded `wait()` reaps the terminated child

## ADDED Requirements

### Requirement: Local buffered execution services every pipe concurrently

The local executor SHALL service supplied stdin, stdout, and stderr concurrently from process creation until completion, cancellation, or timeout. The configured timeout SHALL bound the complete exchange, including blocked stdin delivery, and existing process-group termination, descendant cleanup, exact-byte, and exception contracts SHALL remain in force.

#### Scenario: Three pipe-capacity payloads complete

- **WHEN** a local child emits stdout and stderr payloads and consumes a stdin payload, with each payload larger than the corresponding OS pipe capacity
- **THEN** local buffered execution completes without deadlock and returns the exact stdin-dependent result, stdout bytes, stderr bytes, and exit code

#### Scenario: Timeout bounds a blocked exchange

- **WHEN** a local child does not complete a pipe-capacity exchange before the configured timeout
- **THEN** execution terminates through the existing timeout path, cleans up the process group and descendants, closes owned pipes, and raises the existing timeout exception within a bounded cleanup interval

### Requirement: Spawned initial stdin is delivered asynchronously and losslessly

`LocalExecutor.spawn` SHALL return its `ProcessHandle` without waiting for a child to consume a supplied initial stdin payload. The handle SHALL own delivery and closure of that payload together with concurrent output draining. Subsequent buffered collection SHALL return complete stdout and stderr without duplicating or losing stdin bytes while each stream remains within the bounded resident-capture limit; exceeding that limit SHALL raise `ProcessOutputCaptureError` and follow the terminate/reap and worker-cleanup contract in the modified managed-process requirement. Existing single-owner buffered-versus-streaming rules and retry-after-collection-timeout behavior SHALL remain unchanged.

#### Scenario: Spawn returns before the child reads initial stdin

- **WHEN** `LocalExecutor.spawn` receives a pipe-capacity stdin payload for a child that is intentionally prevented from reading it
- **THEN** `spawn` returns a handle before the child is released to read and does not synchronously wait on the stdin pipe

#### Scenario: Collection preserves all three channels

- **WHEN** the child is released after spawn and produces stdout and stderr while consuming the supplied initial stdin
- **THEN** buffered collection returns the exact complete stdout and stderr and the child observes the initial stdin exactly once

#### Scenario: Timed-out collection can be retried

- **WHEN** collection times out while asynchronous initial I/O is still in progress and the caller retries after the child completes
- **THEN** the retry returns all buffered stdout and stderr without resending stdin, changing output ownership, or losing data captured before the first timeout
