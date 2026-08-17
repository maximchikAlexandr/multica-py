## Context

The SDK invokes the Multica CLI through one controlled transport
`CliTransport` (`src/multica_py/_internal/transport.py`). Today that class
owns two concerns at once:

```text
CliTransport
├── build Multica argv (build_full_argv)
├── apply global args (profile, workspace, server_url, debug)
├── compatibility preflight (_check_compat -> multica version)
├── decode JSON/text
├── classify Multica CLI errors (exit codes, HTTP status, markers)
├── redact diagnostics
├── inherit host environment (_effective_environment = os.environ + overrides)
├── create subprocess.Popen (create_process)
├── run with timeout/cancel (run_with_timeout, _communicate_until_exit)
├── terminate/kill process groups + descendants (terminate_process, killpg)
└── spawn long-running processes (ManagedProcess wraps subprocess.Popen)
```

The process-creation half is local-OS-specific (`subprocess.Popen`,
`start_new_session=True`, `pgrep`-based descendant collection, `os.killpg`).
It cannot represent a Microsandbox VM call or an SSH channel. Resources,
commands, and relations all route through this one
transport, so there is currently no seam at which a different execution
target can be plugged in.

Verified current state against the pinned baseline
(`79501f3b1c5afe960a6b4b63abba4acae508653c`):

- `CliTransport._execute` calls `run_with_timeout(argv, stdin, timeout, cwd, env)`
  from `_internal/processes.py`, which calls `subprocess.Popen(..., start_new_session=True)`.
  `_effective_environment` returns `dict(os.environ) | config.environment`.
- `CliTransport.spawn` calls `create_process(argv, cwd, env)` and wraps the
  `Popen` in `ManagedProcess(process, argv, semaphore)` from `process.py`.
- `ManagedProcess` (`src/multica_py/process.py`) holds a `subprocess.Popen[bytes]`,
  owns the output-claim state machine (buffered vs streaming vs discarded),
  releases a `ProcessSemaphore` on close, and exposes `.pid: int`
  (`process.pid or 0`).
- `_internal/processes.py` owns `CancellationToken`, `create_process`,
  `terminate_process` (SIGTERM -> 2s grace -> SIGKILL, with descendant
  cleanup via `pgrep -P`), `kill_process`, and `run_with_timeout`.
- `_internal/commands.py` `_CommandPlan` is the single source of truth for
  preview + execution. It calls `transport.run_bytes`/`run_text`/`spawn`.
  `${temp.path}` is resolved by a `_TempProvider` that creates a local
  `tempfile.TemporaryDirectory` on the controller; for remote execution this
  path would not be visible inside the target.
- `MulticaClient.__init__(config=None, _semaphore=None)` builds a
  `ProcessSemaphore(config.max_processes)` and a `CliTransport(config, semaphore)`.
  `with_options()` constructs a new `MulticaClient` sharing only the semaphore.
  `__exit__` calls `self._transport.close()`.
- Resources (`src/multica_py/resources/_base.py`) hold `(transport, config)`
  and build `_CommandPlan`s via `BaseResource._plan`; lazy relations and
  bound entities (`models/relations.py`, `entities/`) capture the originating
  client view.
- The approved SDK contract (`contracts/sdk-contract.json`) is the generator
  input; the public surface is pinned by `tests/contract/`.
- `pyproject.toml` base `dependencies = ["msgspec>=0.19,<2"]`; no extras.

Constraints carried from the existing specs and `AGENTS.md`:

- No eager public method renamed/split/removed; `*_command()` siblings
  unchanged; the discovered-public-methods invariant stays green.
- `uv run mypy src` and `uv run mypy tests` pass; no `Any` leaks; only
  stdlib + pytest in tests.
- Default suite offline (`uv run pytest -m "not live"`); live tests gated.
- The approved SDK contract remains the generator input. Evidence/heuristic
  output MUST NOT create public executor behavior directly.
- Conventional Commits; pre-commit runs Ruff + mypy on `src`.
- Provider-specific configuration lives under `multica_py.execution`, not at
  the package root; the root namespace stays focused on ordinary usage.
- Optional dependencies are opt-in extras; missing extras produce
  actionable install guidance; provider modules are not imported eagerly
  during normal package import.

GitHub issue `maximchikAlexandr/multica-py#41` (MYL-42) asks for the
execution layer this design specifies, deliberately stopping at "an
execution target already exists."

## Goals / Non-Goals

**Goals:**

- One stable provider-independent execution boundary: `CommandExecutor` with
  `ExecutionRequest`/`ExecutionResult`/`ProcessHandle`, so the same Multica
  CLI operations run locally, in an existing Microsandbox microVM, or on an
  existing SSH host.
- An open, conformance-gated adapter model: a future provider adds one
  `multica_py.execution.<provider>` module (or a third-party implementation
  of the public protocol), an optional extra when first-party, and focused
  tests. It does not change `CliTransport`, `_CommandPlan`, resources, models,
  or `MulticaClient`.
- `CliTransport` keeps Multica semantics; process creation moves to the
  executor. The same transport works with every executor.
- `ManagedProcess` becomes provider-independent; `.pid` is retained only
  where meaningful and a new `.id` covers opaque provider identities.
- `MulticaClient(config, executor=...)` selects a backend; default stays
  local and one-argument; `with_*()` views and bound entities preserve the
  executor; closing a scoped view never destroys a shared executor.
- Target-aware environment, path, and staging semantics; no implicit
  controller-`os.environ` leak into remote targets; SDK-owned temp files
  live where the CLI runs.
- Optional extras (`microsandbox`, `vps`); missing extras raise clear
  actionable errors; base install stays lightweight.
- `Command[T]` previews stay provider-independent (no `ssh` wrapper).
- Preserve the entire existing resource API, typed models, redaction,
  compatibility, and the approved SDK contract.

**Non-Goals:**

- Provisioning: no creating/deleting microVMs, Droplets, images;
  no `pydo`; no Terraform/Pulumi/Coder; no Multica/Codex installation; no
  auth/bootstrap; no repo cloning or arbitrary file sync; no persistent dev
  volumes, snapshots, pools, TTL, cost mgmt, IDE/browser exposure, SSH
  port-forwarding as a general feature, Kubernetes, or a generic cloud
  abstraction. Those belong to a later environment-provisioning feature.
- No provider-specific parameters on resource methods; the execution target
  belongs to the client execution scope, not individual business operations.
- No change to the approved SDK contract as generator input; no new public
  command representation; `Command[T]` stays the only command type.
- No async public API; executors stay synchronous from the current SDK's
  perspective even if a backing SDK exposes async primitives.
- No special daemon transport; the daemon lives in the same execution
  target as the CLI it controls.
- No universal microVM lifecycle abstraction and no lowest-common-denominator
  `MicroVmExecutor`. MicroVM provisioning/lifecycle and command execution are
  independent concerns; providers expose different command transports.
- No plugin registry, entry-point discovery, automatic activation, or runtime
  installation. Explicit construction and injection remain the extension
  mechanism.

## Design

### Module boundary

```text
multica_py/
├── execution/
│   ├── __init__.py     # re-export common contracts, LocalExecutor, exceptions
│   ├── base.py         # CommandExecutor, ExecutionRequest, ExecutionResult,
│   │                   # ProcessHandle, ExecutionError hierarchy, staging protocol
│   ├── local.py        # LocalExecutor (stdlib only)
│   ├── microsandbox.py # MicrosandboxExecutor (optional `microsandbox`)
│   └── ssh.py          # SshExecutor (optional `paramiko`)
│
├── process.py          # ManagedProcess wraps ProcessHandle (public)
└── _internal/
    ├── transport.py     # CliTransport delegates to CommandExecutor
    ├── commands.py      # _CommandPlan staging via executor
    └── processes.py     # local-only helpers reused by LocalExecutor
```

Optional provider classes are importable only from their
`multica_py.execution.<provider>` submodules and are NOT re-exported from
`multica_py.execution` or the package root. Common contracts and
`LocalExecutor` remain available from `multica_py.execution`.

### Provider adapter model

The architecture separates three axes that must not be collapsed into one
"microVM provider" abstraction:

```text
target lifecycle (outside this change)
    creates/finds/starts/stops a sandbox or VM
                 │ existing target/session identity
                 ▼
provider adapter (`CommandExecutor`)
    maps run/spawn/stage/process control to provider SDK or SSH
                 │ ExecutionRequest / Result / ProcessHandle
                 ▼
`CliTransport`
    owns Multica argv, compatibility, decode, redaction, error classification
```

Microsandbox uses its agent protocol, CubeSandbox uses the E2B-compatible
`envd` data plane, and a VPS uses SSH. Their isolation technology may all be
described as a VM or microVM, but their command and file APIs are not
interchangeable. Therefore `CommandExecutor`, not `MicroVmExecutor`, is the
only shared production interface.

Adding another provider follows one bounded recipe:

1. Implement `CommandExecutor` and `ProcessHandle` in one provider module.
2. Keep connection/auth/provider SDK objects on that executor; do not add
   them to `ExecutionRequest`, `ClientConfig`, resources, or models.
3. Adapt an already-existing target. Creation, image/template builds, start,
   stop, delete, snapshots, and pools stay outside the executor.
4. Preserve exact argv semantics, or use one reviewed shell serializer when
   the provider accepts only a command string. Shell rendering must never be
   delegated to `CliTransport`.
5. Pass the shared conformance suite for run, non-PTY spawn, poll/wait,
   collect/stream ownership, cwd, explicit environment, stdin, timeout,
   byte-exact stdout/stderr, opaque identity, staging/cleanup, error mapping,
   and close without target destruction. Test provider-specific process
   control in that adapter's focused tests.
6. If first-party, add one independently installable extra and lazy provider
   import. If third-party, depend only on the public protocol and use explicit
   `MulticaClient(executor=...)` injection.

There is deliberately no provider registry, factory hierarchy, capability
object, or automatic discovery. A provider that cannot satisfy the required
contract is not advertised as supported; the common contract is not weakened
for it. Provider-specific differences such as descendant cleanup remain
documented method guarantees rather than transport branches.

### Provider-independent contracts (`execution/base.py`)

`ExecutionRequest` is an immutable value object:

```python
@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    argv: tuple[str, ...]
    cwd: str | None = None              # target-local path string (see Target paths)
    environment: tuple[tuple[str, str], ...] = ()  # explicit target-process overrides ONLY
    stdin: bytes | None = None
    timeout: datetime.timedelta | None = None
```

It carries NO provider-specific fields. Provider connection and SDK config
live on the executor object.

**Environment invariant (#8).** `ExecutionRequest.environment` has exactly
one meaning for every executor: explicit target-process overrides only. The
transport NEVER branches on `isinstance(executor, LocalExecutor)`. There is
no `_effective_environment_for_executor` policy in the transport. The
transport builds `ExecutionRequest.environment` from `config.environment`
alone (the explicit overrides). `LocalExecutor` performs local-process
inheritance internally inside its own `run`/`spawn` by merging
`dict(os.environ)` with `request.environment` before calling
`subprocess.Popen`; this is an implementation detail of `LocalExecutor`, not
a transport concern. Non-local executors pass `request.environment` to the
target with no controller `os.environ` merge. A third-party local-like
executor can express the same policy by doing the merge in its own `run`/
`spawn`; the `CommandExecutor` protocol does not encode it.

**Preview/redaction environment (#8).** Redaction is deliberately
conservative and remains independent of the executor. `_CommandPlan.render()`
keeps using the existing `_effective_environment(config)` helper, which
returns `dict(os.environ) | dict(config.environment)`, only to collect secret
values for diagnostics. This may redact a controller secret that a remote
target would not receive, which is safe. It does not copy the controller
environment into `ExecutionRequest`; remote execution still receives only
explicit overrides. No redaction-only method is added to `CommandExecutor`.

**Target paths (#9).** `ExecutionRequest.cwd` is an opaque target-local path
string, not a controller-native `pathlib.Path`. Public path inputs continue
to accept `str | os.PathLike` and are converted once with `os.fspath()`;
the resulting string is passed to `ExecutionRequest.cwd` unchanged.
The string MUST NOT be normalized, resolved, or interpreted using the
controller's filesystem flavor. A Windows controller targeting a Linux VM
passes the Linux path string verbatim. See the Target paths section for the
`ClientConfig` representation change.

`ExecutionResult` is an immutable completed-process result:

```python
@dataclass(frozen=True, slots=True)
class ExecutionResult:
    exit_code: int
    stdout: bytes
    stderr: bytes
```

`ProcessHandle` is a protocol for a running command. In addition to the
streaming iterators, it exposes a buffered-collection operation (#1):

```python
class ProcessHandle(Protocol):
    @property
    def id(self) -> str | int | None: ...
    def poll(self) -> int | None: ...
    def wait(self, timeout: datetime.timedelta | None = None) -> int: ...
    def collect(self, timeout: datetime.timedelta | None = None) -> ExecutionResult: ...
    def terminate(self) -> None: ...
    def kill(self) -> None: ...
    def stdout_lines(self) -> Iterator[str]: ...
    def stderr_lines(self) -> Iterator[str]: ...
    def close(self) -> None: ...
```

Termination semantics stay on the methods and in documentation: local process
group cleanup is guaranteed; Microsandbox sends per-command POSIX signals but
does not guarantee descendant cleanup; SSH can only close its channel and
cannot guarantee delivery of a process signal. No extra capability field is
added before a real caller needs to branch on it.

**Buffered collection (#1).** `collect(timeout=...) -> ExecutionResult` is
the provider-independent equivalent of `subprocess.Popen.communicate()`. It
waits for the process to exit (or the timeout to elapse), then returns the
complete buffered `stdout`/`stderr` as bytes and the exit code. `collect`
and the line iterators (`stdout_lines`/`stderr_lines`) are **mutually
exclusive single-owner operations**: calling `collect` after any lines have
been consumed from `stdout_lines`/`stderr_lines` raises a `RuntimeError`
(output already claimed as a stream), and vice versa. This preserves the
existing single-owner/output-claim semantics of `ManagedProcess`: a
process's output is claimed exactly once, either buffered (via `collect`)
or streamed (via the iterators), never both. `ManagedProcess.result()`
routes through `handle.collect()`. `LocalExecutor.collect` maps to
`Popen.communicate()`; `SshExecutor.collect` reads the channel stdout+stderr
file objects to EOF; `MicrosandboxExecutor.collect` delegates to the native
async `ExecHandle.collect()` and maps its `ExecOutput`.

`CommandExecutor` is a protocol:

```python
class CommandExecutor(Protocol):
    def run(self, request: ExecutionRequest) -> ExecutionResult: ...
    def spawn(self, request: ExecutionRequest) -> ProcessHandle: ...
    def stage(self, label: str, content: bytes) -> ContextManager[str]: ...
    def capture_output(self, label: str) -> ContextManager[OutputArtifact]: ...
    def close(self) -> None: ...
```

**Staging with content (#3).** `stage(label, content) -> ContextManager[str]`
is the provider-independent staging operation. The caller supplies bytes
once; entering the context makes them available and yields a target-local
absolute path; exiting removes them deterministically.
The executor chooses the transfer mechanism internally (SFTP write for SSH,
`sandbox.fs.write` for Microsandbox, local `tempfile` for `LocalExecutor`);
the contract carries
the content so the transport never needs to know the mechanism. The previous
`staging_path(label) -> StagingPath` (path-only, no content) is replaced;
there is no path-only staging operation because a path without content is
insufficient for remote targets.

For `LocalExecutor`, `stage` writes `content` into a controller-local
`TemporaryDirectory`-backed file and context exit removes that directory
exactly as `_TempPathProvider.cleanup()` does today
(`attachments.py:335-338`), preserving the pre-change behavior. For remote
executors the artifact is created in the target and context exit removes it
from the target. The *cleanup-is-unconditional* contract (success, decoder
failure, transport failure, timeout, cancellation) is the same for every
executor, matching the `subprocess-transport` spec's "Cleanup is
unconditional in the target" scenario and the `execution-backends` spec's
"Local staging is a local temp dir" scenario. The SDK uses `stage` only for
`${temp.path}` resolution in composite plans; it is not a general
remote-filesystem SDK.

**Bounded command output retrieval.** `capture_output(label)` creates one
SDK-owned target output directory. Its artifact yields that directory path and
may read only a direct child path reported by the CLI before context exit;
cleanup removes the file and directory. It exists for `download_bytes`, not as
a general filesystem facade.

### Exception hierarchy (`execution/base.py`)

```python
class ExecutionError(MulticaError): ...

class ExecutionConnectionError(ExecutionError): ...        # SSH refused, provider unreachable
class ExecutionTargetNotFoundError(ExecutionError): ...     # sandbox/VM/host missing
class ExecutionUnavailableError(ExecutionError): ...        # session disappeared, daemon down
```

These are distinct from the existing `CommandExecutionError` hierarchy.
Boundary rule:

```text
provider could not execute the process -> ExecutionError (subclass)
process executed, `multica` returned nonzero -> existing CLI error classifier
```

**Separating target-missing from executable-missing (#6).** A missing
sandbox/VM/host (`ExecutionTargetNotFoundError`) and a reachable target
where the `multica` binary is absent are different failures requiring
different remediation. Target/connection/session failures use the small
execution hierarchy; once the target is reachable, missing and non-runnable
binaries use the existing `ExecutableNotFoundError` and
`ExecutableNotRunnableError` directly. Local errors preserve the underlying
`FileNotFoundError`/`PermissionError` through chaining. A missing sandbox or
unreachable SSH host MUST NEVER be reported as a missing binary.
`ExecutionTargetNotFoundError`,
`ExecutionConnectionError`, and `ExecutionUnavailableError` are re-raised
as-is (they are not executable failures and are not mapped to
`ExecutableNotFoundError`).

### `LocalExecutor` (`execution/local.py`)

Stdlib only. Wraps the existing `_internal/processes.py` helpers
(`create_process`, `run_with_timeout`, `terminate_process`, `kill_process`,
`close_process_pipes`, `CancellationToken`). `run` returns an
`ExecutionResult` from the `CompletedProcess[bytes]`; `spawn` returns a
`_LocalProcessHandle` wrapping `subprocess.Popen`. **Environment semantics
(#8):** `LocalExecutor` performs local-process inheritance *internally*:
inside its own `run`/`spawn` it merges `dict(os.environ) | dict(request.environment)`
before calling `subprocess.Popen`. The transport does not participate in this
merge; `ExecutionRequest.environment` carries only the explicit overrides.
The existing transport helper continues to use
`dict(os.environ) | dict(config.environment)` for conservative diagnostic
redaction only. The staging context
writes `content` into a controller-local `TemporaryDirectory`-backed file and
removes that directory on exit, exactly as
`_TempPathProvider.cleanup()` does today. This is the compatibility adapter;
it MUST reproduce the current descendant cleanup and terminate/kill
escalation exactly. **Descendant cleanup (#2):** among the three initial
executors, `LocalExecutor` is the only one that guarantees descendant-process
cleanup (via `pgrep -P` + `os.killpg`). Microsandbox and SSH do not; a future
provider may advertise such a guarantee only when its adapter can prove it in
the shared conformance suite (see Process control guarantees).

### `MicrosandboxExecutor` (`execution/microsandbox.py`)

Optional, gated on `microsandbox` (compatibility range
`microsandbox>=0.6,<0.7` — see Packaging). Constructed with `sandbox: str`
(the name of an existing sandbox). The adapter resolves it with
`Sandbox.get(name)` and `SandboxHandle.connect()`; it MUST NOT call
`Sandbox.create()` or `Sandbox.start()`. The reviewed Microsandbox Python SDK
range is async-only. The published 0.6.0 lower-bound wheel and 0.6.9 both
expose `exec`, `exec_stream`, `ExecHandle.collect`, `ExecHandle.signal`,
`ExecHandle.kill`, `Sandbox.fs`, and reconnecting to an existing sandbox.
There is no native sync API; all calls are coroutines.

**Sync-bridging strategy (#10 — resolved): dedicated event-loop thread.**
`MicrosandboxExecutor` creates and owns a private `asyncio` event loop
running on a dedicated daemon thread (created in `__init__`, joined in
`close()`). Every async SDK call (`Sandbox.get`, `handle.connect`,
`sandbox.exec`, `sandbox.exec_stream`, `ExecHandle.collect`/`signal`/`kill`,
and `sandbox.fs` operations) is dispatched via
`asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout)`.
This is safe under a caller thread that already has a running event loop
(Jupyter, async web apps, test runners) because the coroutine runs on the
executor's own loop/thread, not the caller's. `asyncio.run()` on the
caller's thread is **forbidden** (it raises `RuntimeError` if a loop is
already running and is unsafe in nested-async contexts). The dedicated-
thread bridge is the primary and only strategy; there is no "native sync
API fallback" because none exists.

**Execution (async API mapped to sync):**
- `run`: `output = await sandbox.exec(prog, args, cwd=..., env=..., timeout=...)`
  → `ExecutionResult(exit_code=output.exit_code, stdout=output.stdout_bytes,
  stderr=output.stderr_bytes)`. The SDK's `exec` returns the complete
  buffered result directly (it is the buffered-collection primitive).
- `spawn`: `handle = await sandbox.exec_stream(prog, args, ...)`; events
  arrive as `async for event in handle:` with `event.event_type` ∈
  `stdout`/`stderr`/`exited` and `event.data: bytes`. The
  `_MicrosandboxProcessHandle` wraps the async iterator and drains events
  on the executor's loop thread.
- `collect`: `output = await handle.collect()` drains remaining output and
  waits for exit; the adapter maps its exit code/stdout/stderr bytes to
  `ExecutionResult`. For `run`, `exec` already returns the buffered result.

**File staging:** `stage(label, content)` uses
`await sandbox.fs.write(target_path, content_bytes)` to write the content
into a target `mktemp`-created path. Alternatively
`await sandbox.fs.copy_from_host(local_path, target_path)` when the content
is already on a controller-local file. Context exit removes the target path
via `await sandbox.fs.remove(target_path)` or equivalent.

**Process control (#2):** the Microsandbox 0.6.x `ExecHandle` exposes
per-command `signal(sig)` and `kill()`. `MicrosandboxExecutor.terminate()`
sends `SIGTERM` through `handle.signal(signal.SIGTERM)`;
`MicrosandboxExecutor.kill()` delegates to `handle.kill()` (`SIGKILL`). A
configured execution timeout also kills the individual command. These are
stronger guarantees than closing a controller-side stream, but they do not
guarantee descendant cleanup. The adapter MUST NOT call sandbox-level
`sandbox.stop()`, `sandbox.kill()`, or `sandbox.remove()` for process control
because those operations affect the entire execution environment.

**Lifecycle:** sandbox-missing maps to `ExecutionTargetNotFoundError`;
missing executable in a reachable sandbox maps to
`ExecutableNotFoundError`. `close()` detaches/closes the connection it opened,
stops the private event loop, and joins the daemon thread; it does NOT stop,
kill, remove, or otherwise destroy the sandbox.

### CubeSandbox compatibility candidate (deferred adapter)

CubeSandbox is concrete evidence that the extension point must describe
command execution rather than a particular microVM implementation. Source
review at `TencentCloud/CubeSandbox@0f7ab984be668313232fa3136e1a688b46cb558c`
shows that its native Python `Commands.run()` sends HTTP Connect-JSON RPC to
the guest `envd` process API on port `49983`, endpoint
`/process.Process/Start`; it is not SSH. The current native method accepts a
shell command string and builds `/bin/bash -l -c <cmd>`. Remote deployments
route that data-plane request through CubeProxy; sandbox lifecycle uses a
separate control-plane API.

This change does NOT add `CubeSandboxExecutor`, a `cubesandbox` dependency,
an optional extra, or any image/template build. A compatibility spike must
first prove all mandatory executor behavior against a pinned CubeSandbox SDK
and runtime:

- exact `ExecutionRequest.argv` semantics without unsafe or lossy shell
  reinterpretation;
- non-PTY background start with a stable handle, streaming, native buffered
  collection, and separate stdout/stderr bytes;
- stdin, cwd, explicit environment, timeout, and executable-not-found
  behavior;
- per-command terminate/kill semantics and the absence or presence of a
  descendant-cleanup guarantee;
- byte-exact `stage(label, content)` and unconditional target cleanup through
  the provider file API;
- connection/session close without stopping or deleting the existing sandbox.

The spike may evaluate either the public E2B-compatible command surface or
the provider's public `envd` process API. It MUST NOT depend on a private SDK
module without an explicit stability decision. If safe argv mapping requires
a shell string, one provider-private serializer equivalent to the reviewed
SSH serializer is acceptable only with adversarial round-trip tests. If any
mandatory behavior cannot be implemented, CubeSandbox remains unsupported;
the common contract is not weakened and provider branches are not added to
`CliTransport`.

If the spike succeeds, a separate OpenSpec change may add exactly one
`execution/cubesandbox.py` adapter, one independently installable
`multica-py[cubesandbox]` extra with a tested range, provider-specific tests,
and a gated live smoke test. That later change reuses the contracts and
conformance suite defined here.

### `SshExecutor` (`execution/ssh.py`)

Optional extra `multica-py[vps]`, backed by `paramiko` (compatibility range
`paramiko>=3,<4` — see Packaging). Constructed with `host`, `port=22`,
`username`, optional
`key_filename`/`password`/`look_for_keys`/... Host-key verification is
**safe by default**: a missing/changed host key raises
`ExecutionConnectionError` rather than being auto-accepted; an explicit
opt-in (`allow_unknown_host_key=False` default) documents the risk. `run`
opens a channel, runs the command with `get_pty=False`, feeds stdin,
collects stdout/stderr (separate streams via `exec_command`'s stdout/stderr
file objects), respects timeout. `spawn` returns a handle wrapping the
channel; `collect` reads stdout+stderr to EOF; `stdout_lines`/`stderr_lines`
iterate the channel file objects. `close()` closes the SSH client/session; it
does not destroy the host. `stage(label, content)` uses SFTP to write
`content` into a target `mktemp`-created path (#3). **No DigitalOcean-specific
API.**

**SSH command serialization (#7 — resolved).** Paramiko `exec_command()`
accepts a command string executed by the remote user's login shell. The
supported remote shell contract is a **POSIX-compatible shell** (`/bin/sh`
or equivalent). The serialization rules are safe-by-construction and cover
all command components:

- **cwd**: validated to be a non-empty string with no shell metacharacters
  after `shlex.quote`; serialized as `cd $(shlex.quote(cwd)) &&`. If `cwd`
  is `None`, no `cd` prefix. The path is passed as a single-quoted string,
  so whitespace, `$`, backticks, and `;` inside the path are inert.
- **environment**: each `(name, value)` pair is validated and serialized as
  `name=value` where `name` MUST match `^[A-Za-z_][A-Za-z0-9_]*$` (rejected
  with `ValueError` otherwise — no shell metacharacter can appear in a valid
  env name) and `value` is passed through `shlex.quote`. Serialized as
  `KEY=quoted_value` prefix assignments joined by spaces.
- **argv**: each token is passed through `shlex.quote`; the argv list is
  serialized with `shlex.join(argv)`.
- **full command**: `cd quoted_cwd && KEY=quoted_val ... quoted_argv`. Every
  component is individually quoted, so the concatenation is shell-safe even
  if any component contains whitespace, quotes, `$`, backticks, `;`, `|`,
  `&`, newlines, or other metacharacters.

The serializer is a single function `_serialize_ssh_command(cwd, env, argv)`
in `execution/ssh.py` with unit tests covering adversarial inputs:
whitespace-only cwd, cwd with `; rm -rf /`, env values with backticks and
`$()`, argv tokens with embedded newlines and single quotes, empty argv,
unicode. This is no longer an open question.

**Process control guarantees (#2).** SSH has no controller-visible remote
PID. `SshExecutor.terminate()`/`kill()` close the Paramiko channel.
Paramiko documents `Channel.close()` as closing the channel and stopping
data transport; it does **not** guarantee a `SIGHUP` or any signal to the
remote process — the remote process may continue running after the channel
is closed. This is a **capability gap** versus `LocalExecutor`:
`SshExecutor` cannot guarantee process termination and cannot enumerate or
signal descendants. The observable guarantee is: `terminate()`/`kill()`
close the channel on a best-effort basis; the remote process may continue
running, and the caller MUST NOT assume the remote process and its
descendants have terminated when `terminate()` returns. `id` is an opaque
channel id or `None`. Timeout/cancellation reports that the controller-side
channel was closed; the caller decides whether to seek independent
confirmation of remote termination. This gap is documented on the methods.

### `CliTransport` refactor (`_internal/transport.py`)

`CliTransport.__init__(config, executor, semaphore=None)` stores the
executor. `_execute` and `spawn` build an `ExecutionRequest`:

```python
request = ExecutionRequest(
    argv=self._build_full_argv(command_args),
    cwd=self._config.cwd,  # already str; passthrough (see Target paths)
    environment=tuple(self._config.environment.items()),  # explicit overrides ONLY
    stdin=stdin,
    timeout=effective_timeout,
)
```

**No executor-type branching in the transport (#8).** The transport builds
`ExecutionRequest.environment` from `config.environment` alone — explicit
overrides only. There is no `_effective_environment_for_executor` and no
`isinstance(executor, LocalExecutor)` check. `LocalExecutor` does its own
`os.environ` merge internally; non-local executors use only the overrides.

**Preview/redaction environment (#8).** `_CommandPlan.render()`
(`commands.py:69`) keeps calling `_effective_environment(self.config_snapshot)`
to collect diagnostic secret values from `os.environ` plus explicit
overrides. This is intentionally a conservative redaction input, not the
remote execution environment. `ExecutionRequest.environment` still contains
only explicit overrides, so controller variables are never sent to a remote
target. No executor hook or type check is needed.

**Target paths (#9).** Public path-like inputs are converted once with
`os.fspath()` and the resulting string is passed through without controller
filesystem resolution. Remote paths should be supplied as strings; local
`Path` input remains accepted for compatibility.

Then `executor.run(request)` / `executor.spawn(request)`. `ExecutionError`
subtypes are re-raised as-is (provider failures); the existing CLI error
classifier runs on the `ExecutionResult` exactly as today. Executable
failures: every executor raises the existing
`ExecutableNotFoundError`/`ExecutableNotRunnableError`; `LocalExecutor`
preserves the underlying `FileNotFoundError`/`PermissionError` via chaining.
`ExecutionTargetNotFoundError`/`ExecutionConnectionError`/
`ExecutionUnavailableError` are re-raised as-is and are NOT mapped to
`ExecutableNotFoundError`. Compatibility preflight (`_check_compat`) runs
the `version` command through the executor (i.e. in the target), not on the
controller.

### `ManagedProcess` refactor (`process.py`)

`ManagedProcess` wraps a `ProcessHandle` instead of `subprocess.Popen`
directly. The output-claim state machine (buffered/streaming/discarded) and
semaphore release are preserved. `.pid` delegates to the handle when it
exposes an `int`; otherwise the new `.id` is the provider-independent
identity and `.pid` returns `None` (documented: remote handles may have no
Unix PID). `.id` is always available. Process-control guarantees are
documented on `terminate()`/`kill()` rather than represented by another
property. `result()` routes through
`handle.collect()` (the buffered-collection operation, #1); streaming routes
through `handle.stdout_lines()`/`stderr_lines()`. The single-owner/output-
claim invariant is preserved: `result()` (buffered) and streaming are
mutually exclusive; calling `result()` after streaming has started raises a
`RuntimeError`, and vice versa.

### `MulticaClient` (`client.py`)

```python
def __init__(self, config=None, *, executor=None, _semaphore=None):
    ...
    self._executor = executor if executor is not None else LocalExecutor()
    self._owns_executor = executor is None  # only the default is owned
    self._transport = CliTransport(config, self._executor, semaphore)
```

**Unified ownership model (#5).** Ownership is defined at exactly one point:
`MulticaClient` owns the executor if and only if it constructed it (i.e.
`executor is None` → default `LocalExecutor()`). A user-supplied executor
is NEVER owned by any client — root or scoped. The rules:

- **Root client `close()`:** closes the transport and closes the executor
  only if the client owns it (`_owns_executor`). A user-supplied executor
  is not closed by the root client; the user owns its lifecycle.
- **Scoped `with_options()`/`with_*()` client `close()`:** closes only the
  scoped transport; NEVER closes the shared executor (owned or not). A
  scoped view shares the executor and the semaphore; closing it MUST NOT
  affect the shared executor or any other view.
- **Executor never destroys the execution environment:** `close()` on any
  executor closes the session it created (SSH client or Microsandbox
  handle); it NEVER destroys the sandbox or VM.

Provider-client injection is deferred. First-milestone executor constructors
accept target/connection parameters, create one session, and own its cleanup.

This resolves the contradiction: the `execution-backends` spec scenario
"Close does not destroy the environment" applies to the executor's own
`close()` (which closes sessions it owns), NOT to `MulticaClient.close()` on
a user-supplied executor (which does not call `executor.close()` at all
because the client does not own it). The spec scenarios are updated to make
this distinction explicit. `__enter__`/`__exit__` and an explicit `close()`
are both supported.

### Staging for composite plans (`_internal/commands.py`)

`_CommandPlan` resolves `${temp.path}` with `with
executor.stage(label, content) as target_path`. It uses `ExitStack` so every
staging context exits on success, failure, timeout, and cancellation. Local
staging yields a local temp path; remote staging yields a target path.
This is the ONLY filesystem concern the execution layer takes on in this
change; it is not a general remote FS SDK.

### Path-like upload inputs (#4 — resolved)

Path-like upload input is a controller-local source. The SDK reads its bytes
and sends them through the same `stage()` context as bytes/stream input for
every executor. This deliberately gives up the local fast path to keep
`_CommandPlan` provider-neutral: there is no `is_local` capability and no
executor-type branch. If local-copy cost becomes measurable, optimization can
be added inside `LocalExecutor.stage()` without widening the protocol.

This means `/Users/alex/file.zip` on the controller is read by the SDK and
its bytes are staged into the configured non-local target via `executor.stage`
before the CLI command runs. The user does not need to mount or transfer
files manually.

### Target paths (#9)

`ClientConfig.executable` and `ClientConfig.cwd` are paths in the execution
target, not on the controller. At the execution boundary
(`ExecutionRequest.cwd` and the argv's executable token), they are plain
strings with no controller-filesystem normalization.

**Compatible target-path conversion (#9).** `ClientConfig.cwd`,
`ClientConfig.executable`, `OperationOptions.cwd`, and `with_cwd` continue to
accept `str | os.PathLike`. Normalization changes from `pathlib.Path(value)`
to `os.fspath(value)`, producing a string without resolving it through the
controller filesystem. Remote callers should pass target paths as strings;
existing local callers may keep using `Path`. A Windows controller targeting
a Linux VM passes
`/workspace/backend` as the string `/workspace/backend` — no backslash
conversion, no drive-letter handling, no `os.path.exists` check. Paths yielded
by staging contexts are target-local absolute strings.

`_target_path_string` simplifies to a passthrough (returns the string
as-is). `ClientConfig` documents that `cwd` and `executable` are target
paths; local-path convenience (resolving relative paths against `$PWD`) is
applied only inside `LocalExecutor`.

A cross-platform contract test (`tests/unit/test_target_paths.py`) asserts
that `ClientConfig(cwd="/workspace/backend")` on a simulated Windows
controller renders as `/workspace/backend` in `ExecutionRequest.cwd` with
no backslash/drive-letter normalization. The test uses mock/parametrization
and does not depend on the current OS.

### Process control guarantees (#2, #3)

`terminate()`/`kill()` and descendant-cleanup guarantees differ per executor
and are documented on those methods. No capability property is added until a
real provider-independent caller needs to branch on it.

| Executor | `terminate()`/`kill()` behavior | Descendant cleanup |
|----------|----------------------------------|--------------------|
| `LocalExecutor` | `SIGTERM` → 2s grace → `SIGKILL` on the process group | Guaranteed (`pgrep -P` + `os.killpg`) |
| `MicrosandboxExecutor` | Per-command `ExecHandle.signal(SIGTERM)` / `ExecHandle.kill()` (`SIGKILL`); sandbox-level stop/kill is forbidden | Not guaranteed |
| `SshExecutor` | Close the channel; no signal guarantee | Not guaranteed |

`ManagedProcess.terminate()`/`kill()` document this: for `LocalExecutor`
the pre-change guarantee is preserved; Microsandbox confirms sending a signal
to the selected process but does not cover descendants; SSH is best-effort
channel close. A caller MUST NOT infer descendant cleanup from a remote
`terminate()`/`kill()` result. Timeout/cancellation reports completion of the
provider-specific control operation (signal sent / channel closed); the
caller decides whether to wait for independent confirmation. The
`subprocess-transport` spec's timeout-cancellation
scenarios are scoped to `LocalExecutor` for the strong guarantee; non-local
executors have a weaker observable guarantee. This is not a regression —
the pre-change behavior only existed for local execution.

### Optional dependency gating

Each provider module imports its backing package lazily at class
construction (or module import for the type), and raises a clear error if
missing:

```python
class MicrosandboxExecutor:
    def __init__(self, sandbox, ...):
        try:
            import microsandbox  # noqa: PLC0415
        except ImportError as e:
            raise ImportError(
                'Microsandbox execution requires the optional `microsandbox` dependency. '
                'Install it with: pip install "multica-py[microsandbox]"'
            ) from e
        ...
```

`multica_py.execution.__init__` imports `base` + `local` eagerly (stdlib
only); `microsandbox`/`ssh` submodules are imported lazily so a
plain `import multica_py` and `from multica_py.execution import
CommandExecutor, LocalExecutor` never pull optional deps. The provider
classes can be imported from `multica_py.execution.microsandbox` and
`multica_py.execution.ssh` without the
extra installed (the import of the class is cheap; the error fires at
construction).

### Packaging

`pyproject.toml`:

```toml
[project.optional-dependencies]
microsandbox = ["microsandbox>=0.6,<0.7"]  # pre-1.0, bounded range (async API 0.6.x)
vps = ["paramiko>=3,<4"]                     # generic SSH/VPS support
```

**Compatibility ranges (#11).** Each optional extra has a tested
compatibility range recorded in both `pyproject.toml` and this design. The
adapter contract is designed and tested against the lower bound of each
range; the upper bound is bounded to prevent silent breakage from a major
release. `microsandbox` is pre-1.0 (beta), so its range is tightly bounded
(`>=0.6,<0.7`). The published 0.6.0 lower-bound wheel and 0.6.9 were inspected
for the required surface. The spec identifies the provider API version each
adapter is designed against: Microsandbox 0.6.x (async
`Sandbox.get`/`SandboxHandle.connect`, `Sandbox.exec`/`exec_stream`, native
`ExecHandle.collect`/`signal`/`kill`, and `Sandbox.fs`), Paramiko 3.x
(`SSHClient`/`exec_command`/`SFTPClient` surface). Bumping a
range requires re-running the real-backend integration smoke tests (#12).

Base `dependencies` unchanged (`msgspec` only).

### Installation and extension model

First-party remote providers use standard Python extras, not a plugin
manager. Installation never discovers entry points and the SDK never installs
packages at runtime. After installation, the caller imports the provider class
from its submodule and explicitly passes an instance to
`MulticaClient(executor=...)`.

For this repository's Git distribution, the documented uv commands are:

```bash
# Lightweight base installation
uv add "multica-py @ git+https://github.com/maximchikAlexandr/multica-py"

# Microsandbox build
uv add "multica-py[microsandbox] @ git+https://github.com/maximchikAlexandr/multica-py"

# VPS/SSH build
uv add "multica-py[vps] @ git+https://github.com/maximchikAlexandr/multica-py"

# Reproducible pinned variants
uv add "multica-py[microsandbox] @ git+https://github.com/maximchikAlexandr/multica-py@<tag-or-commit>"
uv add "multica-py[vps] @ git+https://github.com/maximchikAlexandr/multica-py@<tag-or-commit>"
```

If the base Git dependency is already recorded in the consumer's
`[tool.uv.sources]`, either build can be enabled without replacing that source:

```bash
uv add --extra microsandbox multica-py
uv add --extra vps multica-py
```

The library cannot infer whether the consuming project uses uv, pip, a Git
source, or an index, so missing-extra exceptions name the extra and a generic
package requirement. The exact Git commands belong in installation docs.
Third-party executors use the public `CommandExecutor` protocol, the same
conformance contract, and explicit injection. Automatic discovery and
registration are intentionally absent: adding a provider requires no central
registry change.

### Preview independence

`Command[T].commands` continues to render
`multica --profile automation issue get MUL-123 --output json` via
`transport.build_full_argv` + redaction + `shlex.join`. It MUST NOT prepend
`ssh ...` or any provider wrapper — the visible command is
the Multica operation; execution routing is a separate concern.

## Risks and Trade-offs

- **`ManagedProcess.pid` typed-surface change.** `ManagedProcess` is in
  `multica_py.__all__` (`__init__.py:78`), so the `.pid` annotation widening
  from `int` to `int | None` is a public typed-source change even though
  `discover_public_methods` (which scans functions, not properties) stays
  green and does not catch it. Local callers are unaffected at runtime: `.pid`
  returns the handle's int id when local (preserving `subprocess.Popen.pid`),
  and `None` for remote handles; `.id` is the new provider-independent
  identity (`str | int | None`). Documented as a typed-source behavior change
  for non-local executors; local stays `int`.
- **Environment semantics change for remote.** Remote executors no longer
  inherit controller `os.environ`. This is intentional (avoids leaking
  controller secrets) but could surprise users who set `MULTICA_*` in their
  shell and expect it to reach the remote target. Mitigation: documented in
  `execution-backends.md` and `migration.md`; `LocalExecutor` is unchanged.
- **SSH command serialization.** SSH has no native per-exec cwd/env without
  a shell. The chosen approach is a POSIX-shell protocol with
  `shlex.quote` for cwd and env values, regex validation for env names, and
  `shlex.join` for argv. Every component is individually quoted, so the
  concatenation is shell-safe. Adversarial tests cover whitespace, quotes,
  `$`, backticks, `;`, newlines, and unicode. This is resolved, not an open
  question (#7).
- **Remote process control differs by provider.** `MicrosandboxExecutor`
  sends per-command POSIX signals, while `SshExecutor` can only close its
  channel. Neither guarantees descendant cleanup the way `LocalExecutor`
  does. These differences are documented guarantees rather than a fabricated
  lowest-common-denominator capability (#2).
- **CubeSandbox is not yet claimed compatible.** Its native command API is
  `envd` over HTTP Connect rather than SSH, but the reviewed Python
  `Commands.run()` surface accepts a shell string. Exact argv, non-PTY spawn,
  stream separation, process control, and staging must pass the spike before
  a first-party adapter or dependency is added.
- **Optional deps at construction, not import.** Importing a provider class
  without its extra does not error; only constructing it does. This keeps
  provider-submodule import cheap for type-checking/IDE, but the
  error message fires later than at-import. Acceptable: the error is clear
  and actionable.
- **Concurrency name.** `max_processes` is retained for compatibility but
  the architecture stops treating it as `subprocess.Popen`-specific; a future
  rename to `max_concurrent_commands` is noted but NOT done in this change
  (no public rename).

## Migration Plan

- Purely additive for users: `MulticaClient(config)` stays local-by-default.
  Existing code is unchanged. New `executor=` kwarg is opt-in.
- `ManagedProcess.pid` annotation widens from `int` to `int | None` (local
  stays `int`, remote returns `None`); `.id` is the new provider-independent
  identity (`str | int | None`). This is a typed-source contract change on a
  public `__all__` symbol; `discover_public_methods` does not catch it (it
  scans functions, not properties), so it is documented here explicitly. Local
  callers are unaffected at runtime.
- Cwd/executable APIs keep accepting `str | os.PathLike`; internal conversion
  changes from `pathlib.Path` to `os.fspath()` so target strings are not
  resolved with controller semantics. Remote paths SHOULD be passed as
  strings. Tests cover Windows-controller → POSIX-target passthrough and local
  `Path` compatibility.
- `ClientConfig.executable`/`cwd` semantics documented as target paths;
  local behavior is preserved at runtime for `str` inputs.
- Optional extras are new; base install unchanged.
- No contract change to the generator input; the generator input is
  untouched. The new public execution surface (`executor=` on
  `MulticaClient`, the `multica_py.execution` package, `ManagedProcess.id`,
  `ManagedProcess.pid` widening) is **outside the generated SDK contract**
  (`contracts/sdk-contract.json` covers generated resource methods only).
  Focused import, constructor, and behavior tests cover this surface without
  duplicating exact `__all__` contents and annotations in a snapshot.

## Open Questions

- Whether to add `max_concurrent_commands` alias now (deferred — no public
  rename in this change).
- Whether CubeSandbox can satisfy the existing executor contract without a
  private `envd` dependency or lossy shell semantics. The compatibility spike
  records evidence; implementation belongs to a later change only if it
  passes.

## Resolved Decisions (previously open)

- **SSH command serialization (#7):** resolved — POSIX-shell protocol with
  `shlex.quote` for cwd/env-values, regex validation (`^[A-Za-z_][A-Za-z0-9_]*$`)
  for env-names, `shlex.join` for argv. See `SshExecutor` section.
- **Microsandbox sync bridge (#10):** resolved — the SDK is async-only
  (0.6.x, no native sync API); `MicrosandboxExecutor` uses a dedicated
  event-loop thread (`asyncio.run_coroutine_threadsafe`) as the primary
  and only bridge. See `MicrosandboxExecutor` section.
