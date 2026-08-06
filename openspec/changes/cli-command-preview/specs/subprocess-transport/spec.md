## MODIFIED Requirements

### Requirement: CLI-only transport

The SDK MUST invoke Multica through one shell-free controlled subprocess
transport. `CliTransport` SHALL add the executable and current global
arguments through one full-argv path used by both preview rendering and
execution. When a resource runs a command, exact argv, cwd, profile,
workspace, environment, stdin, and timeout reach that transport. The
argv passed to the transport during `Command.run()` SHALL be the same
plan-derived argv that produced the rendered `commands` tuple; the SDK
SHALL NOT execute rendered strings and SHALL NOT use `shell=True`.

#### Scenario: Resource calls use the controlled subprocess

- **WHEN** a resource runs a command
- **THEN** exact argv, cwd, profile, workspace, environment, stdin, and
  timeout reach that transport

#### Scenario: Preview and execution share the full-argv path

- **WHEN** a `Command` is constructed and then run
- **THEN** the executable and global args in `command.commands` and the
  argv received by `CliTransport` are both produced by the same
  full-argv path, and no separate argv builder is used for preview

#### Scenario: Rendered strings are never executed

- **WHEN** `Command.run()` executes any plan
- **THEN** `CliTransport` receives the argv tuple directly from the plan
  and no `subprocess.*(..., shell=True)` call occurs

### Requirement: Managed process lifecycle

The SDK MUST expose managed processes with bounded concurrency, timeout
cancellation, escalation, and descendant cleanup. A root client and views
derived through `with_*()` MUST share exactly one `ProcessSemaphore` while
remaining otherwise independent clients with distinct immutable
configuration, transport, services, and close behavior. Command plans
that retain the `spawn` execution mode SHALL call `spawn()` during
`run()` and SHALL NOT silently convert to `run_bytes()` or `run_text()`.

#### Scenario: Timed processes clean up descendants

- **WHEN** the timeout process case expires
- **THEN** parent and descendant are absent

#### Scenario: Derived clients share concurrency only

- **WHEN** root and derived client views invoke operations concurrently
- **THEN** all invocations are bounded by the same `max_processes`
  semaphore without a shared runtime, transport registry, identity map,
  or family closed state

#### Scenario: Derived configuration reaches transport

- **WHEN** a relation loads from an entity returned by a derived client
  view
- **THEN** exact cwd, profile, workspace, environment, stdin, and
  timeout from that view reach its controlled transport

#### Scenario: Client views close independently

- **WHEN** one root or derived view closes
- **THEN** other views remain usable and already-started calls follow
  existing transport timeout/cancellation behavior

#### Scenario: Prefetch shares the process limit

- **WHEN** relation prefetch runs with `max_parallel=N`
- **THEN** executor concurrency observes `N` while each CLI process also
  observes the shared `max_processes` semaphore

#### Scenario: Spawn command plan retains spawn execution

- **WHEN** a `Command` constructed from a `spawn`-mode operation (e.g.
  `daemon.start_command()`) is run
- **THEN** `CliTransport.spawn` is called and a `ManagedProcess` is
  returned; neither `run_bytes` nor `run_text` is called for that step

### Requirement: Decode and diagnostics

The SDK MUST decode supported structured output, map reliable failures to
typed errors, and redact secrets from diagnostics. `Command.run()` SHALL
preserve the existing decode, error-classification, redaction, and
diagnostics behavior of the transport. Secrets SHALL be redacted from
`commands`, exceptions, reprs, and test output while execution receives
the real secret value.

#### Scenario: Failures expose typed redacted diagnostics

- **WHEN** malformed output or nonzero exit occurs during
  `Command.run()`
- **THEN** the diagnostic has redacted command context and the
  documented error type, matching the behavior of the equivalent eager
  operation

#### Scenario: Secrets redacted in command preview and repr

- **WHEN** a `Command` carrying a secret is constructed, printed, or
  raised in an exception
- **THEN** the secret value is redacted and only `***` (or the
  equivalent redacted form) appears in `commands`, `repr(command)`, and
  exception messages, while `run()` receives the real secret value