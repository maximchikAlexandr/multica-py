## Purpose

Define the controlled subprocess boundary used for all Multica CLI operations.

## Requirements

### Requirement: CLI-only transport
The SDK MUST invoke Multica through one shell-free controlled subprocess transport.
#### Scenario: Resource calls use the controlled subprocess
- **WHEN** a resource runs a command
- **THEN** exact argv, cwd, profile, workspace, environment, stdin, and timeout reach that transport.
<!-- Source IDs: 001:FR-006–FR-010,FR-015 -->

#### Scenario: Preview and execution share the full-argv path

- **WHEN** a `Command` is constructed and then run
- **THEN** the executable and global args in `command.commands` and the
  argv received by `CliTransport` are both produced by the same
  full-argv path, and no separate argv builder is used for preview

#### Scenario: Rendered strings are never executed

- **WHEN** `Command.run()` executes any plan
- **THEN** `CliTransport` receives the argv tuple directly from the plan
  and no `subprocess.*(..., shell=True)` call occurs

#### Scenario: Resource calls reach the executor
- **WHEN** a resource runs a command
- **THEN** exact argv, cwd, environment overrides, stdin, and timeout reach the configured executor as an `ExecutionRequest`, and the executor performs process creation/transport

#### Scenario: LocalExecutor preserves byte-for-byte behavior
- **WHEN** the default `LocalExecutor` executes a command
- **THEN** ordinary-command argv, cwd, environment inheritance, stdin, timeout, descendant cleanup, and terminate/kill escalation match the pre-change behavior; path-like uploads may replace the source path with an SDK staging path while preserving bytes and results

#### Scenario: Compatibility preflight runs in the target
- **WHEN** a non-local executor is configured and compatibility checks are enabled
- **THEN** the `multica version` preflight command executes in the configured target through the executor, not on the controller host
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

#### Scenario: Spawn command plan retains spawn execution

- **WHEN** a `Command` constructed from a `spawn`-mode operation (e.g.
  `daemon.start_command()`) is run
- **THEN** `CliTransport.spawn` is called and a `ManagedProcess` is
  returned; neither `run_bytes` nor `run_text` is called for that step

#### Scenario: ManagedProcess collects buffered output
- **WHEN** `ManagedProcess.result()` is called on a spawned process whose output has not been streamed
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
### Requirement: Decode and diagnostics
The SDK MUST decode supported structured output, map reliable failures to typed errors, and redact secrets from diagnostics.
Classified failures MUST preserve actionable upstream detail. A raw HTTP `409`,
the stable `v0.4.28` localized conflict prefixes,
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
generic command-failed message SHALL remain the fallback. `--server-config` inline JSON SHALL be a collected secret.
`--server-config-file` path SHALL NOT be a secret. `--credential-file` path
SHALL NOT be a secret; plugin Remote MCP stdin and credential-file **contents**
SHALL be collected into `secret_values`. The SDK SHALL NOT add a plaintext
`--credential` flag. A `--credential*` key match MUST NOT redact the file path.
Successful stdout and stderr bytes SHALL reach typed decoders unchanged;
redaction SHALL occur only while constructing error diagnostics or finalizing
the public raw `CliResult`. File-channel secret contents SHALL be read only
immediately before execution, using binary I/O; preview/render SHALL retain
the file path without reading it. UTF-8/JSON secret extraction from file bytes
is best-effort, while opaque non-UTF-8 bytes SHALL still participate in exact
diagnostic redaction.

#### Scenario: Failures expose typed redacted diagnostics
- **WHEN** malformed output or nonzero exit occurs
- **THEN** the diagnostic has redacted command context and the documented error type.

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
- **WHEN** `v0.4.28` rejects max concurrency through its reviewed local CLI validation message before an HTTP request
- **THEN** the SDK raises `ValidationError` with that message rather than an unclassified `CommandExecutionError`

#### Scenario: Detail redaction precedes message construction
- **WHEN** upstream detail, stdout, stderr, or argv contains a collected secret
- **THEN** the secret is absent from `str(exc)`, exception attributes, reprs,
  redacted argv, and command preview while the actual argv passed to the
  subprocess still receives the real value

#### Scenario: Empty diagnostics use the generic fallback
- **WHEN** a classified or unclassified failure has no nonempty safe stderr or stdout detail
- **THEN** `str(exc)` uses the existing redacted command-failed fallback and no detail is fabricated

#### Scenario: MCP and plugin credentials are redacted
- **WHEN** a workspace MCP add uses inline `--server-config` JSON or plugin Remote MCP configure uses credential-file or stdin contents
- **THEN** the inline JSON and credential bytes are absent from `str(exc)`, redacted argv, and preview while `--server-config-file` and `--credential-file` paths remain visible

#### Scenario: Credential file path is not treated as a secret
- **WHEN** `collect_secret_values` sees `--credential-file <path>` or `--server-config-file <path>`
- **THEN** the path is not added as a secret; file or stdin contents are collected when those channels carry credentials or config JSON

#### Scenario: File channels are passive during preview
- **WHEN** a command using `--credential-file` or `--server-config-file` is rendered
- **THEN** construction and preview do not read the file, the path remains in the rendered argv, and execution reads the bytes only when `run()` starts

#### Scenario: Successful typed output preserves secret-looking values
- **WHEN** successful stdout contains a short or overlapping environment/file/stdin secret in valid JSON
- **THEN** the typed decoder receives the original bytes and preserves the numeric/string values, while a public raw `CliResult` redacts the same secret values and bytes

#### Scenario: Secrets redacted in command preview and repr

- **WHEN** a `Command` carrying a secret is constructed, printed, or
  raised in an exception
- **THEN** the secret value is redacted and only `***` (or the
  equivalent redacted form) appears in `commands`, `repr(command)`, and
  exception messages, while `run()` receives the real secret value
### Requirement: Effective operation configuration is snapshotted once
Every public CLI-backed command method that accepts `OperationOptions` SHALL resolve the effective `ClientConfig` before constructing its private plan. One private config-level overlay function SHALL copy the base/scoped config, apply each present operation field, and preserve the normalization already performed by `OperationOptions`; both `MulticaClient.with_options` and `BaseResource._effective_config` SHALL use that function rather than enumerate overlay fields independently. The function SHALL preserve omitted `Unset`, explicit `None`, and an explicitly empty environment. Command construction SHALL create the transport snapshot from the effective config and store that effective config in `_CommandPlan.config_snapshot`. Preview and execution SHALL derive global argv, cwd, environment, timeout, compatibility, and redaction context from that one snapshot. Existing resources and clients SHALL not be mutated.

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

#### Scenario: Explicit clears survive shared overlay application
- **WHEN** a scoped or operation overlay sets a nullable scalar/path field to `None` or sets environment to an empty mapping/tuple
- **THEN** the resulting immutable config contains the explicit clear rather than inheriting the lower-layer value

#### Scenario: Derived clients share only the existing semaphore
- **WHEN** `with_options` applies the shared overlay function
- **THEN** the source config is unchanged, the derived client has a distinct config and transport/resources, and both clients retain the same existing `ProcessSemaphore`

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

#### Scenario: Preview redaction remains conservative
- **WHEN** a command plan's `commands` property is read under a non-local executor while the controller process has an env var (e.g. `OPENAI_API_KEY`) set
- **THEN** the preview may redact that controller value using the existing conservative redaction environment, but `ExecutionRequest.environment` still excludes it unless it is an explicit `ClientConfig.environment` override

#### Scenario: Execution writes exact bytes once in the target
- **WHEN** the command runs with bytes or an open binary stream under any executor
- **THEN** the executor stages exact input bytes once via `stage(label, content)`, transport receives the resolved target-local path, and the caller-owned stream is not closed

#### Scenario: Cleanup is unconditional in the target
- **WHEN** any stage after materialization succeeds or raises
- **THEN** leaving the staging context removes the content from the execution target and preserves the original result/exception contract

#### Scenario: Path source uses the common staging path
- **WHEN** an upload source is a controller-local path under any executor
- **THEN** the SDK reads its bytes, stages them through `executor.stage`, and introduces no local/provider branch in the command plan
### Requirement: Raw commands preserve the controlled transport boundary
The raw CLI escape hatch SHALL build one ordinary `run_bytes` step through `BaseResource._plan` and `CliTransport`; it SHALL reuse full-argv construction, compatibility checks, semaphore, timeout, cwd/environment, error classification, and redaction. It SHALL not use `subprocess` directly, invoke a shell, spawn a managed process, or bypass the SDK executable/global configuration.

#### Scenario: Raw command uses the same full argv path
- **WHEN** a raw command is previewed and executed
- **THEN** both use `CliTransport.build_full_argv` from the same immutable plan step

#### Scenario: Raw output cannot leak command secrets
- **WHEN** command arguments or environment contain collected secrets
- **THEN** preview/exceptions are redacted and the public raw result omits unredacted argv while actual execution receives the original values

### Requirement: Executable failures are classified at the transport boundary
The SDK SHALL use `ClientConfig.executable` directly when building command argv and SHALL map `FileNotFoundError` and `PermissionError` raised by execution or spawn to the existing typed SDK exceptions. It SHALL NOT pre-resolve executables with a separate `find_executable` helper or emit a writable-directory warning before transport execution.

#### Scenario: Missing executable retains typed failure
- **WHEN** the configured executable cannot be found during command execution
- **THEN** transport raises `ExecutableNotFoundError` with the existing diagnostic contract

#### Scenario: Non-runnable executable retains typed failure
- **WHEN** the configured executable cannot be executed due to permissions
- **THEN** transport raises the existing non-runnable executable SDK error without a separate path-directory policy

#### Scenario: Missing executable retains typed failure locally
- **WHEN** the configured executable cannot be found during `LocalExecutor` execution
- **THEN** transport raises `ExecutableNotFoundError` with the existing diagnostic contract and the underlying `FileNotFoundError` is preserved in `__cause__`

#### Scenario: Non-runnable executable retains typed failure locally
- **WHEN** the configured executable cannot be executed due to permissions under `LocalExecutor` execution
- **THEN** transport raises the existing non-runnable executable SDK error and the underlying `PermissionError` is preserved in `__cause__`

#### Scenario: Remote missing executable is distinguishable
- **WHEN** a non-local executor reports the target is reachable but the configured executable is not found
- **THEN** the executor raises the existing `ExecutableNotFoundError` directly, while target/connection failures keep their execution-specific classes

#### Scenario: Missing target is not a missing executable
- **WHEN** a non-local executor reports the sandbox, microVM, or host is missing or unreachable
- **THEN** `ExecutionTargetNotFoundError` or `ExecutionConnectionError` is re-raised as-is and `ExecutableNotFoundError` is not raised for that failure
