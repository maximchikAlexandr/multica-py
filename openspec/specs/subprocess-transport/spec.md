## Purpose

Define the controlled subprocess boundary used for all Multica CLI operations.
## Requirements
### Requirement: CLI-only transport
The SDK MUST invoke Multica through one shell-free controlled subprocess transport.
#### Scenario: Resource calls use the controlled subprocess
- **WHEN** a resource runs a command
- **THEN** exact argv, cwd, profile, workspace, environment, stdin, and timeout reach that transport.
<!-- Source IDs: 001:FR-006–FR-010,FR-015 -->

### Requirement: Managed process lifecycle
The SDK MUST expose managed processes with bounded concurrency, timeout
cancellation, escalation, and descendant cleanup. A root client and views
derived through `with_*()` MUST share exactly one `ProcessSemaphore` while
remaining otherwise independent clients with distinct immutable configuration,
transport, services, and close behavior.

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

### Requirement: Decode and diagnostics
The SDK MUST decode supported structured output, map reliable failures to typed errors, and redact secrets from diagnostics.
#### Scenario: Failures expose typed redacted diagnostics
- **WHEN** malformed output or nonzero exit occurs
- **THEN** the diagnostic has redacted command context and the documented error type.
<!-- Source IDs: 001:FR-011–FR-014,FR-040–FR-044 -->
