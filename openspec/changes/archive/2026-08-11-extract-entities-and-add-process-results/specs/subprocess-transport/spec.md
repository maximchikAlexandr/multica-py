## MODIFIED Requirements

### Requirement: Managed process lifecycle
The SDK MUST expose managed processes with bounded concurrency, timeout cancellation, escalation, descendant cleanup, structured buffered completion, and explicit output-consumption modes. A root client and views derived through `with_*()` MUST share exactly one `ProcessSemaphore` while remaining otherwise independent clients with distinct immutable configuration, transport, services, and close behavior.

`ManagedProcess.result(timeout=...)` SHALL claim buffered mode, wait for process completion while draining stdout and stderr without sequential-pipe deadlock, decode both streams as UTF-8 text, construct and cache one immutable `ProcessResult`, then close pipes and release the semaphore exactly once. Repeated successful `result()` calls SHALL return that same cached object. `wait(timeout=...)` SHALL return `result(timeout=...).exit_code`, so a successful wait preserves the cached output.

Calling either output iterator SHALL claim streaming mode when iteration begins. Buffered mode and streaming mode SHALL be mutually exclusive: `result()` or `wait()` after streaming has begun, and either stream iterator after buffered collection has begun or completed, SHALL raise `ProcessOutputModeError` before reading another pipe. Streaming mode SHALL remain incremental and SHALL NOT silently tee or retain complete output.

If buffered completion times out, the SDK SHALL raise the same documented `TimeoutError` convention as managed-process waiting, SHALL NOT cache a result, close pipes, finalize the process, or release its semaphore, and SHALL allow a later `result()` or `wait()` call to resume buffered collection. `terminate()` and `kill()` SHALL leave final output collectable through `result()` after the process exits. `close()` SHALL retain its deterministic terminate/escalate/finalize behavior for callers intentionally discarding a result; result or stream access after such a close SHALL fail clearly and SHALL NOT re-finalize resources.

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

#### Scenario: Buffered completion captures both streams safely
- **WHEN** a managed child writes enough interleaved stdout and stderr to fill either pipe if read sequentially and then exits
- **THEN** `result()` completes without deadlock and returns the complete decoded content of both streams with the exit code and original argv

#### Scenario: Completed result is cached by identity
- **WHEN** `result()` is called more than once after successful completion
- **THEN** every call returns the same `ProcessResult` object and performs no additional process wait, pipe read, close, or semaphore release

#### Scenario: Wait preserves completed output
- **WHEN** `wait()` succeeds before the caller requests a result
- **THEN** a later `result()` returns the cached stdout and stderr and no pipe is read again

#### Scenario: Streaming and buffered modes cannot mix
- **WHEN** direct stdout or stderr iteration has begun and the caller invokes `result()` or `wait()`, or buffered collection has begun and the caller requests a stream iterator
- **THEN** `ProcessOutputModeError` is raised before any second consumer reads process output

#### Scenario: Existing direct streaming remains incremental
- **WHEN** a caller consumes `stdout_lines()` or `stderr_lines()` without using buffered completion
- **THEN** decoded lines are yielded incrementally with existing newline semantics and process finalization remains exactly once when ownership ends

#### Scenario: Buffered timeout can be retried
- **WHEN** `result(timeout=...)` times out while the child remains running and a later `result()` is called after more output or completion
- **THEN** the first call caches no result and releases no resources, while the later call returns one complete result without duplicated or lost output

#### Scenario: Explicit termination can still produce a result
- **WHEN** a caller invokes `terminate()` or `kill()` and then calls `result()` after process exit
- **THEN** the result contains the actual exit code and all output captured before pipe closure, followed by exactly-once finalization

#### Scenario: Explicit close discards completion ownership deterministically
- **WHEN** a caller invokes `close()` without obtaining a result
- **THEN** the process is terminated and escalated as needed, pipes and semaphore are finalized exactly once, no `ProcessResult` is fabricated, and later output access fails clearly
