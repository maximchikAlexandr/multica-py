# Execution Backends Specification

## Purpose
Define provider-neutral execution contracts, lifecycle rules, optional dependency boundaries, staging semantics, and conformance requirements for local and remote backends.

## Requirements

### Requirement: Provider-independent execution contracts
The SDK SHALL expose a provider-independent execution layer under
`multica_py.execution` with a `CommandExecutor` protocol
(`run(request) -> ExecutionResult`, `spawn(request) -> ProcessHandle`,
`stage(label, content) -> ContextManager[str]`, bounded `capture_output(label) -> ContextManager[OutputArtifact]`, `close()`), an immutable
`ExecutionRequest` (argv, target-local cwd string, explicit environment
overrides, optional stdin, optional timeout), and an immutable
`ExecutionResult` (exit_code, stdout bytes, stderr bytes).
`ExecutionRequest` and `ExecutionResult` SHALL NOT contain any
provider-specific fields; provider connection
configuration SHALL live on the executor object. `ExecutionRequest.environment`
SHALL have exactly one meaning for every executor: explicit target-process
overrides only. The transport SHALL NOT branch on executor type to build the
environment; `LocalExecutor` SHALL perform local `os.environ` inheritance
internally inside its own `run`/`spawn`. `ProcessHandle` SHALL expose an
opaque optional `id`, `poll`, `wait(timeout=None)`,
`collect(timeout=None) -> ExecutionResult` (buffered collection, the
provider-independent equivalent of `communicate()`), `terminate`, `kill`,
`stdout_lines`, `stderr_lines`, and `close`. `collect` and the line
iterators SHALL be mutually exclusive single-owner operations: calling
`collect` after streaming (or vice versa) SHALL raise `RuntimeError`. The
handle SHALL NOT assume every remote process has a controller-visible Unix
PID; `id` SHALL be `str | int | None`. `stage()` SHALL return a context
manager that yields a target-local absolute path and removes the staged
content on exit; the caller supplies the content bytes once.

#### Scenario: ExecutionRequest is provider-neutral
- **WHEN** a `CommandExecutor.run` or `spawn` is invoked
- **THEN** the request carries only argv, target-local cwd string, explicit environment overrides, optional stdin, and optional timeout, and no provider field

#### Scenario: ExecutionResult is provider-neutral
- **WHEN** an executor completes a command
- **THEN** the result exposes exit_code, stdout bytes, and stderr bytes, and no provider response object leaks

#### Scenario: ProcessHandle identity is opaque
- **WHEN** a spawned process is inspected
- **THEN** `id` is `str | int | None`, a local handle exposes the integer PID, and a remote handle exposes a provider-specific identifier or `None` rather than assuming a Unix PID

#### Scenario: Buffered collection is provider-independent
- **WHEN** a spawned process's complete output is needed (e.g. `ManagedProcess.result()`)
- **THEN** `ProcessHandle.collect(timeout=...)` returns an `ExecutionResult` with the complete buffered stdout/stderr bytes and exit code, and is the provider-independent equivalent of `communicate()`

#### Scenario: Buffered collection and streaming are mutually exclusive
- **WHEN** `collect()` is called after `stdout_lines()` or `stderr_lines()` has been consumed (or vice versa)
- **THEN** a `RuntimeError` is raised because output is single-owner and can be claimed exactly once

#### Scenario: Environment is explicit overrides only for every executor
- **WHEN** an executor receives an `ExecutionRequest`
- **THEN** `environment` contains only explicit target-process overrides, and the transport did not branch on executor type to build it; `LocalExecutor` merges `os.environ` internally

#### Scenario: Staging carries content
- **WHEN** `executor.stage(label, content)` is entered
- **THEN** it yields a target-local absolute path containing the exact bytes and removes those bytes when the context exits

### Requirement: Provider extension is protocol-based and conformance-gated
`CommandExecutor` SHALL be the only production extension interface for a new
execution provider. A provider adapter SHALL keep provider connection,
authentication, SDK client, target identity, and transport details inside its
own executor module and SHALL NOT add provider branches or fields to
`CliTransport`, `_CommandPlan`, `MulticaClient`, `ClientConfig`, resources,
entities, `ExecutionRequest`, or `ExecutionResult`. An executor SHALL adapt an
already-existing target and SHALL NOT create, build, start, stop, delete, or
otherwise own that target's lifecycle. A first-party provider SHALL live in
one `multica_py.execution.<provider>` submodule, use one independently
installable optional extra with lazy dependency loading, and pass the shared
executor conformance suite plus provider-specific tests. A third-party
provider MAY implement the same public protocol in another distribution and
SHALL use explicit `MulticaClient(executor=...)` injection. The SDK SHALL NOT
use a provider registry, entry points, automatic activation, or runtime
package installation.

The shared conformance contract SHALL cover exact argv semantics; target cwd;
explicit environment; stdin and timeout; byte-exact exit/stdout/stderr;
run; non-PTY spawn; poll and wait; streaming and buffered collection with
single ownership; opaque identity;
byte-exact staging with unconditional cleanup; typed provider/executable
errors; and closing adapter-owned sessions without destroying the target. A
provider that cannot satisfy every mandatory behavior SHALL NOT be advertised
as supported and SHALL NOT cause the common contracts to be weakened.
Provider-specific terminate, kill, and descendant-cleanup guarantees SHALL be
verified in focused adapter tests rather than encoded in the shared case table.

#### Scenario: A provider is added without core branches
- **WHEN** a conforming first-party provider is added
- **THEN** the change is limited to one provider adapter, its optional dependency metadata, provider-specific documentation/tests, and the shared conformance cases, with no provider condition added to transport, command-plan, resource, or model code

#### Scenario: Third-party executor uses explicit injection
- **WHEN** an external package implements `CommandExecutor` and passes its instance to `MulticaClient(executor=...)`
- **THEN** the SDK uses it without registration, entry-point discovery, or changes to `multica-py`

#### Scenario: An incomplete provider is not declared supported
- **WHEN** a candidate provider cannot preserve a mandatory behavior such as exact argv, separate stdout/stderr, non-PTY spawn, process collection, or staging cleanup
- **THEN** it remains unsupported and no capability is removed from the shared contract to accommodate it

### Requirement: Execution error hierarchy is distinct from CLI failures
The SDK SHALL expose an `ExecutionError` hierarchy under
`multica_py.execution` with `ExecutionConnectionError`,
`ExecutionTargetNotFoundError`, and `ExecutionUnavailableError`. A missing
sandbox, microVM, or host SHALL NEVER be reported as a missing `multica`
binary. A reachable target with a missing or non-runnable executable SHALL
raise the existing `ExecutableNotFoundError` or
`ExecutableNotRunnableError` directly. Execution errors SHALL be distinct
from the existing
`CommandExecutionError` Multica CLI hierarchy. A provider failure to
execute the process (connection refused, sandbox/VM/host missing, session
disappeared) SHALL raise an `ExecutionError` subclass and SHALL NOT be
classified as a Multica CLI error. Once the provider successfully executes
`multica` and receives an exit code with stdout/stderr, the existing Multica
CLI error classifier in `CliTransport` SHALL remain authoritative.
`ExecutionTargetNotFoundError`, `ExecutionConnectionError`, and
`ExecutionUnavailableError` SHALL be re-raised as-is and SHALL NOT be mapped
to `ExecutableNotFoundError`.

#### Scenario: Provider failure is not a CLI failure
- **WHEN** an SSH connection is refused or a Microsandbox session disappeared
- **THEN** the executor raises the matching `ExecutionError` subclass and no `CommandExecutionError` is raised for that failure

#### Scenario: Missing target is not a missing executable
- **WHEN** a sandbox, microVM, or host is missing or unreachable
- **THEN** the executor raises `ExecutionTargetNotFoundError` (or `ExecutionConnectionError`) and `ExecutableNotFoundError` is not raised for that failure

#### Scenario: Missing executable in a reachable target is distinguishable
- **WHEN** a non-local executor reports the target is reachable but the configured executable is not found
- **THEN** the executor raises the existing `ExecutableNotFoundError` directly, while target and connection failures retain their execution-specific classes

#### Scenario: CLI nonzero exit is not a provider failure
- **WHEN** the provider executes `multica` and it returns a nonzero exit code
- **THEN** the existing CLI error classifier maps it to the existing typed `CommandExecutionError` subclass and no `ExecutionError` is raised for that exit code

### Requirement: Three initial first-party executors
The SDK SHALL provide `LocalExecutor`, `MicrosandboxExecutor`, and
`SshExecutor`. `LocalExecutor` SHALL be
stdlib-only and preserve current local execution behavior.
`MicrosandboxExecutor` SHALL execute inside an
existing sandbox and SHALL NOT own sandbox lifecycle.
`SshExecutor` SHALL execute on an existing SSH host, SHALL be generic, and
SHALL contain no DigitalOcean-specific API. All three SHALL support `run`
and `spawn` and the baseline operations required by `CliTransport`.
Long-running output SHALL be consumable through the `ProcessHandle`
contract.

#### Scenario: LocalExecutor preserves current behavior
- **WHEN** `LocalExecutor` runs or spawns a command
- **THEN** ordinary-command argv, cwd, environment inheritance, stdin, timeout, descendant cleanup, and terminate/kill escalation match the pre-change local subprocess behavior; path-like uploads preserve content and results but may use an SDK staging path

#### Scenario: MicrosandboxExecutor executes in an existing sandbox
- **WHEN** `MicrosandboxExecutor(sandbox="multica-runtime")` runs a Multica command
- **THEN** the adapter resolves and connects to that existing sandbox without calling `Sandbox.create`/`Sandbox.start`, executes through the async SDK bridged by a dedicated event-loop thread, uses native `ExecHandle.collect`/`signal`/`kill`, and never stops, kills, removes, or otherwise destroys the sandbox

#### Scenario: SshExecutor is cloud-agnostic
- **WHEN** `SshExecutor(host=..., username=...)` runs a Multica command
- **THEN** the command executes on that SSH host and no DigitalOcean, EC2, or provider-specific API is present

### Requirement: CubeSandbox support is compatibility-gated and deferred
This change SHALL NOT add a `CubeSandboxExecutor`, `cubesandbox` dependency,
optional extra, image/template build, or target lifecycle behavior. It SHALL
record a bounded compatibility spike against a pinned CubeSandbox SDK/runtime.
The spike SHALL treat CubeSandbox command execution as its actual non-SSH
`envd` HTTP Connect data plane and SHALL verify the complete shared executor
conformance contract, with special evidence for exact argv mapping from a
shell-string API, non-PTY background execution, separate stdout/stderr,
process identity/control, and file staging/cleanup. The spike SHALL distinguish
public stable provider APIs from private implementation modules. Only a later
OpenSpec change MAY add `CubeSandboxExecutor` and an independent
`multica-py[cubesandbox]` extra after all mandatory checks pass.

#### Scenario: CubeSandbox is not routed through SshExecutor
- **WHEN** the CubeSandbox candidate is evaluated
- **THEN** the spike traces its `envd` command/file APIs and does not model it as SSH merely because the target is a microVM

#### Scenario: CubeSandbox does not weaken the executor contract
- **WHEN** CubeSandbox cannot satisfy any mandatory conformance behavior through a reviewed public API
- **THEN** it remains unsupported, no CubeSandbox dependency or extra is added, and the common executor contract is unchanged

### Requirement: Optional dependency gating with actionable errors
The base `multica-py` installation SHALL remain lightweight and SHALL NOT
require `microsandbox` or `paramiko`. Microsandbox support SHALL be the
optional extra `multica-py[microsandbox]` backed by `microsandbox` with a
bounded range (`microsandbox>=0.6,<0.7` for the pre-1.0 async-only API);
VPS/SSH support SHALL be `multica-py[vps]` backed by `paramiko` with a tested range
(`paramiko>=5,<6`). Each adapter contract SHALL be designed and tested
against the lower bound of its range. Bumping a range SHALL require
re-running the real-backend integration smoke tests. Importing
`multica_py.execution` (contracts + `LocalExecutor`) SHALL NOT import any
optional provider package. Constructing a provider executor without its
extra installed SHALL raise a clear error naming the extra and an install
requirement (e.g. `Microsandbox execution requires the optional
'microsandbox' dependency. Install it with: pip install
"multica-py[microsandbox]"`). Provider modules SHALL NOT be
imported eagerly during a normal `import multica_py`.

#### Scenario: Base install stays lightweight
- **WHEN** `multica-py` is installed from its configured source without extras and `import multica_py` runs
- **THEN** neither `microsandbox` nor `paramiko` is required or imported

#### Scenario: Missing Microsandbox dependency gives actionable guidance
- **WHEN** `MicrosandboxExecutor(...)` is constructed without the `microsandbox` extra installed
- **THEN** an `ImportError` is raised whose message names `microsandbox` and the `multica-py[microsandbox]` requirement

#### Scenario: Missing VPS dependency gives actionable guidance
- **WHEN** `SshExecutor(...)` is constructed without the `vps` extra installed
- **THEN** an `ImportError` is raised whose message names `paramiko` and the `multica-py[vps]` requirement

#### Scenario: Contracts import without optional deps
- **WHEN** `from multica_py.execution import CommandExecutor, LocalExecutor` runs in a base install
- **THEN** the import succeeds and no optional package is imported

### Requirement: Provider installation uses extras and explicit injection
First-party remote-provider installation SHALL use standard Python extras,
not a plugin registry. Documentation SHALL include exact uv commands for the
lightweight Git installation, the `microsandbox` build, the `vps` build,
tag/SHA-pinned variants, and enabling either extra on an existing Git
dependency. The SDK SHALL NOT discover entry points, auto-register executors,
or install packages at runtime. The caller SHALL explicitly import a provider
executor from its submodule and pass an instance as
`MulticaClient(executor=...)`. Third-party executors MAY implement the public
`CommandExecutor` protocol, satisfy the same conformance contract, and use the
same explicit injection seam.

#### Scenario: Git consumer installs only the Microsandbox build
- **WHEN** a consumer runs `uv add "multica-py[microsandbox] @ git+https://github.com/maximchikAlexandr/multica-py"`
- **THEN** uv records the Git source and installs the base dependencies plus `microsandbox>=0.6,<0.7`, without `paramiko`

#### Scenario: Git consumer installs only the VPS build
- **WHEN** a consumer runs `uv add "multica-py[vps] @ git+https://github.com/maximchikAlexandr/multica-py"`
- **THEN** uv records the Git source and installs the base dependencies plus `paramiko>=5,<6`, without `microsandbox`

#### Scenario: Existing Git dependency enables one provider
- **WHEN** a consumer with an existing Git source for `multica-py` runs `uv add --extra microsandbox multica-py` or `uv add --extra vps multica-py`
- **THEN** uv preserves the recorded Git source and enables only the selected extra

#### Scenario: Provider selection is explicit
- **WHEN** an optional provider package is installed
- **THEN** no executor is discovered or activated automatically; the caller imports its class and passes `MulticaClient(executor=...)`

### Requirement: Executor lifecycle and ownership
Remote executors own the provider session they construct (SSH sessions,
Microsandbox handles, and streaming channels). `CommandExecutor` SHALL support
`close()` and a context-manager form. `MulticaClient` SHALL expose an
explicit `close()` and context-manager cleanup. `MulticaClient` owns the
executor if and only if it constructed it (the default `LocalExecutor` when
`executor is None`); a user-supplied executor is NEVER owned by any client
— root or scoped. `close()` on the root client SHALL close the transport
and close the executor only if the client owns it; a user-supplied executor
SHALL NOT be closed by any `MulticaClient.close()`. `close()` on a scoped
`with_*()` client SHALL close only the scoped transport and SHALL NEVER
close the shared executor. Provider-client injection is not part of this
milestone: constructors accept connection parameters and own the sessions they
create. Closing an executor SHALL mean closing those sessions/resources, NOT destroying the
execution environment (sandbox or VM).

#### Scenario: Scoped views share the executor
- **WHEN** `remote.with_workspace("ws_123")` is created from a client configured with an `SshExecutor`
- **THEN** the scoped client uses the same SSH executor and does not fall back to local

#### Scenario: Closing a scoped view does not close the shared executor
- **WHEN** a scoped client view is closed while another view still uses the same user-supplied executor
- **THEN** the scoped transport is closed, the executor is not closed, and the other view remains usable

#### Scenario: Root close does not close a user-supplied executor
- **WHEN** the root client that was given a user-supplied executor is closed
- **THEN** the transport is closed and the executor is NOT closed (the user owns its lifecycle); the executor's connections remain open

#### Scenario: Root close closes a client-owned default executor
- **WHEN** the root client that used the default `LocalExecutor()` is closed
- **THEN** the transport and the default executor are closed

#### Scenario: Close does not destroy the environment
- **WHEN** an executor's own `close()` is called (by an owner)
- **THEN** the executor's owned connection/session is closed and the underlying sandbox or VM is not destroyed

### Requirement: Process control guarantees are executor-specific
`terminate()`/`kill()` and descendant-cleanup guarantees SHALL differ per
executor and SHALL be documented on their public methods rather than exposed
as another capability field. `LocalExecutor` SHALL guarantee process
termination via `SIGTERM` → 2s grace → `SIGKILL` on
the process group and SHALL guarantee descendant cleanup via `pgrep`-based
collection and `os.killpg`. `MicrosandboxExecutor.terminate()` SHALL send
per-command `SIGTERM` through `ExecHandle.signal()` and `kill()` SHALL use
native `ExecHandle.kill()` (`SIGKILL`); it SHALL NOT guarantee descendant
cleanup. `SshExecutor` SHALL provide best-effort `terminate()`/`kill()` by
closing its channel and SHALL NOT guarantee either signal delivery or
descendant cleanup. The SDK SHALL document the exact guarantee of each
executor and SHALL NOT generalize all remote providers to channel close.
`SshExecutor.terminate()`/`kill()` SHALL close the channel; Paramiko
`Channel.close()` does NOT guarantee a signal to the remote process, and
the remote process MAY continue running. `MicrosandboxExecutor` SHALL NOT
call `sandbox.kill()` or `sandbox.remove()` in `terminate()`/`kill()`
because that would destroy the execution environment (forbidden by the
`close()` contract).

#### Scenario: LocalExecutor guarantees termination and descendant cleanup
- **WHEN** `LocalExecutor.terminate()` or `kill()` is called on a spawned process
- **THEN** the process and its descendants are terminated (SIGTERM → grace → SIGKILL on the process group) and descendant cleanup is guaranteed

#### Scenario: Non-local process control follows the provider guarantee
- **WHEN** `MicrosandboxExecutor`/`SshExecutor` `terminate()` or `kill()` is called
- **THEN** Microsandbox sends the documented signal to the selected process while SSH closes its channel on a best-effort basis, and neither executor promises descendant cleanup

### Requirement: Target-aware environment semantics
`ExecutionRequest.environment` SHALL have exactly one meaning for every
executor: explicit target-process overrides only. The transport SHALL NOT
branch on executor type to build the environment; there SHALL be no
`isinstance(executor, LocalExecutor)` check in transport code. For non-local
executors, the controller process environment (`os.environ`) SHALL NOT be
implicitly copied into the execution target; the target's own default
environment SHALL be the base. `ClientConfig.environment` SHALL be
interpreted as explicit target-process overrides, not as a merge over the
controller's `os.environ`. `LocalExecutor` MAY preserve the current
local-process environment inheritance for compatibility by merging
`dict(os.environ)` with `request.environment` internally inside its own
`run`/`spawn`, but the generic `ExecutionRequest` SHALL NOT require copying
the host environment. Preview and diagnostic redaction SHALL keep using the
existing conservative `dict(os.environ) | dict(config.environment)` input
without adding an executor method. That redaction input SHALL NOT be copied
into `ExecutionRequest`. This boundary prevents accidental leakage of
controller secrets into remote environments while preserving existing
redaction behavior.

#### Scenario: Remote executor does not inherit controller environment
- **WHEN** a `SshExecutor` runs a command while the controller process has `OPENAI_API_KEY` set
- **THEN** the remote target process does not receive `OPENAI_API_KEY` unless it is an explicit `ClientConfig.environment` override

#### Scenario: Explicit overrides reach the target
- **WHEN** `ClientConfig(environment=(("MULTICA_SERVER_URL", "https://..."),))` is used with a `SshExecutor`
- **THEN** the target process receives `MULTICA_SERVER_URL` as an override over the host's own default environment

#### Scenario: LocalExecutor preserves inheritance
- **WHEN** `LocalExecutor` runs a command
- **THEN** the local process inherits the controller `os.environ` plus explicit overrides, matching the pre-change behavior

### Requirement: Target-aware path semantics
`ClientConfig.executable` and `ClientConfig.cwd` SHALL be interpreted as
paths in the execution target, not on the controller. Their public inputs,
along with `OperationOptions.cwd`, SHALL continue to accept `str |
os.PathLike`; `os.fspath()` SHALL convert values to strings without
`pathlib.Path` construction. Remote target paths SHOULD be supplied as
strings. No code SHALL test these paths against the controller's filesystem
before execution. At the `ExecutionRequest` boundary, `cwd`
SHALL be an opaque target-local string passed through as-is (no
`Path.resolve()`, no `Path.absolute()`, no drive-letter or backslash
conversion). A Windows controller targeting a Linux VM SHALL pass Linux
path strings verbatim. A cross-platform contract test SHALL assert
Windows-controller → POSIX-target path preservation and a local compatibility
test SHALL keep accepting `pathlib.Path` input.

#### Scenario: Target paths are not validated on the controller
- **WHEN** `ClientConfig(executable="/usr/local/bin/multica", cwd="/workspace/backend")` is used with an `SshExecutor`
- **THEN** no controller-side `os.path.exists`/`stat` is performed and the paths are passed to the remote target as-is

#### Scenario: Local paths keep current behavior
- **WHEN** `LocalExecutor` runs with a configured `cwd`
- **THEN** the local process working directory is set to that path as today

### Requirement: Target-side staging for SDK-owned command artifacts
If the SDK creates temporary input needed by a Multica CLI command plan
(such as `${temp.path}` in composite attachment/upload plans), that
temporary input SHALL exist in the same execution environment in which the
corresponding CLI command runs. `CommandExecutor` SHALL expose a
content-bearing staging context manager `stage(label, content) ->
ContextManager[str]`. The caller supplies bytes once; entering yields the
target-local path and exiting removes the staged content deterministically.
This SHALL NOT be a general remote-filesystem SDK and
SHALL NOT cover user-facing source synchronization, repository cloning, or
arbitrary file upload/download.

#### Scenario: Local staging is a local temp dir
- **WHEN** a composite plan runs with `LocalExecutor`
- **THEN** entering `stage(label, content)` writes the bytes into a controller-local temporary directory, yields its path, and context exit removes the directory

#### Scenario: Remote staging lives in the target
- **WHEN** a composite plan runs with any non-local conforming executor
- **THEN** the staging context transfers `content` into the target, yields the target-local path, and removes the content on exit

#### Scenario: Staged content is exact
- **WHEN** `stage(label, content)` places content in the target
- **THEN** the bytes available at the target-local path are exactly the `content` bytes supplied by the caller

### Requirement: SshExecutor safe host-key verification and command serialization
`SshExecutor` SHALL verify host keys safely by default. An unknown or
changed host key SHALL raise `ExecutionConnectionError` rather than being
silently accepted. An explicit opt-in SHALL be required to disable strict
verification and SHALL document the risk. The executor SHALL support
normal SSH authentication (key file, password, agent, look_for_keys).
`SshExecutor` SHALL serialize commands for a POSIX-compatible remote shell
using safe-by-construction quoting: `cwd` via `shlex.quote`, environment
variable names validated against `^[A-Za-z_][A-Za-z0-9_]*$` (rejected with
`ValueError` otherwise), environment values via `shlex.quote`, and argv via
`shlex.join`. The full command SHALL be `cd quoted_cwd && KEY=quoted_val
... quoted_argv` with every component individually quoted. The serializer
SHALL be covered by adversarial tests for whitespace, quotes, `$`,
backticks, `;`, newlines, and unicode in cwd, env values, and argv tokens.

#### Scenario: Unknown host key is rejected by default
- **WHEN** `SshExecutor(host=..., username=...)` connects to a host whose key is not known
- **THEN** the executor raises `ExecutionConnectionError` and does not silently accept the host

#### Scenario: Explicit opt-in is required to disable verification
- **WHEN** a caller wants to accept unknown host keys
- **THEN** they must pass an explicit opt-in parameter and the default behavior remains strict

#### Scenario: Adversarial cwd is shell-safe
- **WHEN** `cwd` contains shell metacharacters (e.g. `; rm -rf /`, backticks, `$()`, newlines)
- **THEN** the serialized command passes `cwd` through `shlex.quote` and the metacharacters are inert inside the quoted string

#### Scenario: Adversarial env value is shell-safe
- **WHEN** an environment value contains shell metacharacters (e.g. `$(whoami)`, backticks, quotes, newlines)
- **THEN** the serialized command passes the value through `shlex.quote` and the metacharacters are inert

#### Scenario: Invalid env name is rejected
- **WHEN** an environment variable name contains characters outside `^[A-Za-z_][A-Za-z0-9_]*$`
- **THEN** the executor raises `ValueError` before any command is sent to the target

#### Scenario: Adversarial argv token is shell-safe
- **WHEN** an argv token contains embedded single quotes, newlines, or shell metacharacters
- **THEN** `shlex.join` quotes the token so the metacharacters are inert in the serialized command

### Requirement: Provider classes live under the execution package
Provider-specific configuration and executor classes SHALL live under
`multica_py.execution` and SHALL NOT be added to the `multica_py` root
namespace. The root namespace SHALL stay focused on ordinary SDK usage.
The contracts (`CommandExecutor`, `ExecutionRequest`, `ExecutionResult`,
`ProcessHandle`) and `LocalExecutor` SHALL be importable from
`multica_py.execution`. Every optional first-party provider class SHALL be
imported from its `multica_py.execution.<provider>` module and SHALL NOT be
re-exported from the common execution package; the initial modules are
`microsandbox` and `ssh`.

#### Scenario: Executors are not at the root
- **WHEN** `multica_py.__all__` is inspected
- **THEN** all optional provider executors, including `MicrosandboxExecutor` and `SshExecutor`, are absent from the root namespace

#### Scenario: Executors are discoverable under execution
- **WHEN** a provider class is imported from its `multica_py.execution.<provider>` submodule
- **THEN** the requested provider is available without widening the common execution surface
