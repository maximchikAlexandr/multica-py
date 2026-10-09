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

`LocalExecutor.spawn` SHALL return its `ProcessHandle` without waiting for a child to consume a supplied initial stdin payload. The handle SHALL own delivery and closure of that payload together with concurrent output draining, and subsequent buffered collection SHALL return complete stdout and stderr without duplicating or losing stdin bytes. Existing single-owner buffered-versus-streaming rules and retry-after-collection-timeout behavior SHALL remain unchanged.

#### Scenario: Spawn returns before the child reads initial stdin

- **WHEN** `LocalExecutor.spawn` receives a pipe-capacity stdin payload for a child that is intentionally prevented from reading it
- **THEN** `spawn` returns a handle before the child is released to read and does not synchronously wait on the stdin pipe

#### Scenario: Collection preserves all three channels

- **WHEN** the child is released after spawn and produces stdout and stderr while consuming the supplied initial stdin
- **THEN** buffered collection returns the exact complete stdout and stderr and the child observes the initial stdin exactly once

#### Scenario: Timed-out collection can be retried

- **WHEN** collection times out while asynchronous initial I/O is still in progress and the caller retries after the child completes
- **THEN** the retry returns all buffered stdout and stderr without resending stdin, changing output ownership, or losing data captured before the first timeout
