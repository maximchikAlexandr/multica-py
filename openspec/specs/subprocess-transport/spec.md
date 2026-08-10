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
Classified failures MUST preserve actionable upstream detail. A raw HTTP `409`,
the stable `v0.4.20` localized conflict prefixes,
and the localized generic conflict fallback SHALL map to `ConflictError` even
though upstream has no conflict-specific process exit code. Known validation
failures SHALL map to `ValidationError` through exit code `5`, raw HTTP
`400`/`422`, the stable localized validation prefixes, or an explicitly reviewed
local CLI validation marker. A classified exception's `str(exc)` SHALL contain
the redacted nonempty upstream detail from stderr (or stdout when stderr is
empty); the exception SHALL retain redacted `stdout`, `stderr`, redacted argv,
and the documented reported exit code. The actual argv SHALL be supplied only
to the executed subprocess invocation and SHALL NOT be retained in exception
attributes, reprs, or previews. When no safe detail exists, the existing
generic command-failed message SHALL remain the fallback.

#### Scenario: Failures expose typed redacted diagnostics
- **WHEN** malformed output or nonzero exit occurs
- **THEN** the diagnostic has redacted command context and the documented error type.
<!-- Source IDs: 001:FR-011–FR-014,FR-040–FR-044 -->

#### Scenario: Failures retain redacted streams
- **WHEN** malformed output or a nonzero CLI exit occurs
- **THEN** the diagnostic retains captured redacted streams without exposing secrets

#### Scenario: Conflict detail reaches str of exception
- **WHEN** the CLI emits `Request conflict: <server detail>` for an HTTP `409`
- **THEN** the SDK raises `ConflictError`, `str(exc)` contains the actionable server detail, and generic retry advice does not replace it

#### Scenario: Localized and raw conflicts classify consistently
- **WHEN** stderr contains the pinned English or Chinese conflict prefix, the pinned generic conflict fallback, or a raw `returned 409` diagnostic
- **THEN** classification returns `ConflictError` while preserving the actual process exit code when no semantic conflict exit code exists

#### Scenario: Validation detail reaches str of exception
- **WHEN** a server-side invalid thinking-level or other HTTP `400`/`422` response reaches the SDK through exit `5` or a pinned validation prefix
- **THEN** the SDK raises `ValidationError` and `str(exc)` contains the actionable redacted upstream reason

#### Scenario: Reviewed local validation is classified
- **WHEN** `v0.4.20` rejects max concurrency through its reviewed local CLI validation message before an HTTP request
- **THEN** the SDK raises `ValidationError` with that message rather than an unclassified `CommandExecutionError`

#### Scenario: Detail redaction precedes message construction
- **WHEN** upstream detail, stdout, stderr, or argv contains a collected secret
- **THEN** the secret is absent from `str(exc)`, exception attributes, reprs,
  redacted argv, and command preview while the actual argv passed to the
  subprocess still receives the real value

#### Scenario: Empty diagnostics use the generic fallback
- **WHEN** a classified or unclassified failure has no nonempty safe stderr or stdout detail
- **THEN** `str(exc)` uses the existing redacted command-failed fallback and no detail is fabricated

### Requirement: Effective operation configuration is snapshotted once
Every public CLI-backed command method that accepts `OperationOptions` SHALL resolve the effective `ClientConfig` before constructing its private plan. Resolution SHALL copy the base/scoped config, apply each present operation field, normalize timeout/cwd/environment through the same helpers as `with_options`, create the transport snapshot from that effective config, and store that effective config in `_CommandPlan.config_snapshot`. Preview and execution SHALL derive global argv, cwd, environment, timeout, compatibility, and redaction context from that one snapshot. Existing resources and clients SHALL not be mutated.

#### Scenario: Preview and execution agree on precedence
- **WHEN** a command has base, scoped, and operation-level values for the same setting
- **THEN** both preview and execution use the operation value and no separate argv construction path exists

#### Scenario: Later changes cannot alter an existing command
- **WHEN** another client view or options object is created after a command plan
- **THEN** the existing command's preview and execution retain the effective snapshot captured at construction

#### Scenario: Composite plans use one effective scope
- **WHEN** an operation produces multiple dependent CLI steps or pagination continuations
- **THEN** every step and continuation uses the same effective config and process semaphore

#### Scenario: Omitted options preserve behavior
- **WHEN** `options` is omitted or all `OperationOptions` fields are omitted
- **THEN** preview, executed argv, cwd, environment, timeout, result, and errors are byte-for-byte/semantically identical to the pre-change client scope

### Requirement: Runtime materialization belongs to the command plan
Unified attachment uploads from bytes or binary streams SHALL use the existing private runtime temp-provider/reference mechanism. Command construction and preview SHALL validate metadata but SHALL not create/read temporary content. Execution SHALL create one private temporary directory, write the exact content under the validated basename, resolve `${temp.path}` into the governed upload argv, and remove the directory in the plan's `finally` cleanup on success, decoder failure, transport failure, timeout, or cancellation.

#### Scenario: Preview is filesystem passive
- **WHEN** an in-memory upload command is constructed and its `commands` property is read
- **THEN** no temporary path is created and preview shows only the redacted runtime placeholder

#### Scenario: Execution writes exact bytes once
- **WHEN** the command runs with bytes or an open binary stream
- **THEN** the provider materializes exact input bytes once, transport receives the resolved path, and the caller-owned stream is not closed

#### Scenario: Cleanup is unconditional
- **WHEN** any stage after materialization succeeds or raises
- **THEN** the temporary directory is removed and the original result/exception contract is preserved

#### Scenario: Path source bypasses materialization
- **WHEN** upload source is path-like
- **THEN** the normalized existing path is placed directly in the plan and no temp provider is installed

### Requirement: Raw commands preserve the controlled transport boundary
The raw CLI escape hatch SHALL build one ordinary `run_bytes` step through `BaseResource._plan` and `CliTransport`; it SHALL reuse full-argv construction, compatibility checks, semaphore, timeout, cwd/environment, error classification, and redaction. It SHALL not use `subprocess` directly, invoke a shell, spawn a managed process, or bypass the SDK executable/global configuration.

#### Scenario: Raw command uses the same full argv path
- **WHEN** a raw command is previewed and executed
- **THEN** both use `CliTransport.build_full_argv` from the same immutable plan step

#### Scenario: Raw output cannot leak command secrets
- **WHEN** command arguments or environment contain collected secrets
- **THEN** preview/exceptions are redacted and the public raw result omits unredacted argv while actual execution receives the original values

