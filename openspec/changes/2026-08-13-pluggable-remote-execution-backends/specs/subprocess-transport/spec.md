## MODIFIED Requirements

### Requirement: CLI-only transport
The SDK MUST invoke Multica through one shell-free controlled subprocess
transport. The transport SHALL build Multica argv, apply global arguments,
perform compatibility checks, decode output, classify Multica errors, and
redact diagnostics; it SHALL delegate process creation and I/O transport
to a provider-independent `CommandExecutor` instead of creating
`subprocess.Popen` directly. Exact argv, cwd, profile, workspace,
environment overrides, stdin, and timeout SHALL reach the executor as an
`ExecutionRequest`. The same `CliTransport` SHALL be usable with every
executor. The default `LocalExecutor` SHALL preserve the pre-change local
subprocess behavior byte-for-byte (descendant cleanup, terminate/kill
escalation, timeout, cancellation, local environment inheritance).
<!-- Modified by pluggable-remote-execution-backends: transport delegates process
     creation to CommandExecutor; LocalExecutor preserves local behavior. -->

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
cancellation, escalation, and descendant cleanup. `ManagedProcess` SHALL
wrap a provider-independent `ProcessHandle` instead of `subprocess.Popen`
directly, while preserving the existing output-claim state machine
(buffered/streaming/discarded), semaphore release, and public long-running
operations (`daemon.start`, `daemon.logs`, `setup.*`, `maintenance.update`,
`auth.login`). `ProcessHandle` SHALL expose a buffered-collection operation
`collect(timeout=None) -> ExecutionResult` (the provider-independent
equivalent of `communicate()`); `ManagedProcess.result()` SHALL route
through `handle.collect()`. `collect` and the line iterators
(`stdout_lines`/`stderr_lines`) SHALL be mutually exclusive single-owner
operations: calling `collect` after streaming (or vice versa) SHALL raise
`RuntimeError`. `.pid` SHALL return the handle's integer id when the
executor exposes a local Unix PID, and SHALL be `None` for handles with no
meaningful controller-visible PID; a new provider-independent `.id` SHALL
expose the opaque process identity (`str | int | None`). A root client and
views derived through `with_*()` MUST share exactly one `ProcessSemaphore`
AND one `CommandExecutor` while remaining otherwise independent clients with
distinct immutable configuration, transport, services, and close behavior.
`terminate()`/`kill()` and descendant-cleanup guarantees SHALL be
executor-specific and documented on their methods. `LocalExecutor` SHALL
guarantee process-group termination and descendant cleanup.
`MicrosandboxExecutor` SHALL use the backing `ExecHandle`'s per-command
`signal(SIGTERM)` and `kill()` (`SIGKILL`) operations but SHALL NOT guarantee
descendant cleanup. `SshExecutor` SHALL close its channel on a best-effort
basis; channel close does NOT guarantee a signal to the remote process or
descendant cleanup. Future executors SHALL document and test their actual
provider guarantee rather than inheriting one blanket "remote" behavior.
`MicrosandboxExecutor` SHALL NOT call `sandbox.kill()`/`sandbox.remove()`
(destroying the sandbox is forbidden). Timeout/cancellation reports
completion of the controller-side operation; callers of a remote executor
decide whether to seek independent confirmation.

#### Scenario: Timed processes clean up descendants
- **WHEN** the timeout process case expires under `LocalExecutor`
- **THEN** parent and descendant are absent

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

#### Scenario: Client views close independently
- **WHEN** one root or derived view closes
- **THEN** other views remain usable, the shared user-supplied executor is not closed by a scoped view, and already-started calls follow existing transport timeout/cancellation behavior

#### Scenario: Prefetch shares the process limit
- **WHEN** relation prefetch runs with `max_parallel=N`
- **THEN** executor concurrency observes `N` while each CLI process also observes the shared `max_processes` semaphore

### Requirement: Executable failures are classified at the transport boundary
The SDK SHALL use `ClientConfig.executable` directly when building command
argv. `LocalExecutor` SHALL map `FileNotFoundError` to
`ExecutableNotFoundError` and `PermissionError` to
`ExecutableNotRunnableError` via exception chaining (`raise ... from e`),
preserving the underlying exception in `__cause__`. Non-local executors
SHALL raise the existing `ExecutableNotFoundError` or
`ExecutableNotRunnableError` directly when the target is reachable. A missing
sandbox, microVM, or host (`ExecutionTargetNotFoundError`/
`ExecutionConnectionError`) SHALL NOT be mapped to
`ExecutableNotFoundError`; it SHALL be re-raised as-is so a missing target
is never reported as a missing `multica` binary. The SDK SHALL NOT
pre-resolve executables with a separate `find_executable` helper or emit a
writable-directory warning before execution. The configured `executable`
and `cwd` SHALL be treated as target paths and SHALL NOT be validated
against the controller filesystem.

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

### Requirement: Runtime materialization belongs to the command plan
Unified attachment uploads from bytes or binary streams SHALL use the
existing private runtime temp-provider/reference mechanism, resolved
through the configured executor's content-bearing staging context manager
`stage(label, content) -> ContextManager[str]` so the materialized artifact
exists in the execution target. Command construction and preview SHALL
validate metadata but SHALL not create/read temporary content. Execution
SHALL stage the exact content bytes once through `executor.stage`,
resolve `${temp.path}` to the yielded target-local path, and use `ExitStack`
for cleanup on success, decoder failure, transport failure, timeout, or
cancellation. Path-like upload inputs SHALL be treated as controller-local:
the SDK reads their bytes and uses the same staging context for every
executor. `_CommandPlan` SHALL NOT branch on executor type. This contract
SHALL NOT be delegated to individual provider implementations.

#### Scenario: Preview is filesystem passive
- **WHEN** an in-memory upload command is constructed and its `commands` property is read
- **THEN** no staging artifact is created and preview shows only the redacted runtime placeholder

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
