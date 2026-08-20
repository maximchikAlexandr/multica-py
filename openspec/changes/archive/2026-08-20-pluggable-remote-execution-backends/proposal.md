## Why

`multica-py` assumes the Python controller process shares one filesystem,
environment, process table, `$HOME`, Multica config, daemon, and executable
path with the process running the `multica` CLI. Today `CliTransport`
(`src/multica_py/_internal/transport.py`) owns both Multica CLI semantics
(argv, global args, compatibility, decode, redaction, error mapping) and
operating-system process creation (`subprocess.Popen`, `pgrep`-based
descendant cleanup, local env inheritance). There is no way to run the same
SDK operations inside an existing local Microsandbox microVM or an existing
SSH-accessible Linux VM without forking the entire resource layer. A later
environment-provisioning feature needs
these execution primitives first; it cannot be built on top of a transport
that is welded to `subprocess.Popen`.

GitHub issue `maximchikAlexandr/multica-py#41` (Multica issue
`MYL-42`, `32818f4e-eb61-4cff-8b75-44d6825f071d`) asks for exactly this:
introduce a provider-agnostic execution layer so the same Multica CLI
operations run in the initial three environments without changing the
resource-level SDK API, the `Command[T]` preview, or the typed models. The
issue is intentionally limited to **execution primitives** for an already
existing target; it must not provision microVMs, Droplets,
repositories, Codex, or Multica installations.

## Starting Revision

The immutable behavior baseline is `79501f3b1c5afe960a6b4b63abba4acae508653c`
(`feat: simplify SDK architecture`, merged as PR #50). Record it once before
implementation, verify local parity after `LocalExecutor`, run focused checks
as each provider lands, and run the complete offline gate once before delivery.

## What Changes

- Introduce a provider-independent **execution layer** under
  `multica_py/execution/`:
  - `CommandExecutor` protocol with `run(request) -> ExecutionResult`,
    `spawn(request) -> ProcessHandle`, and `close()`.
  - Immutable value objects `ExecutionRequest` (argv, target-local cwd,
    explicit environment overrides, optional stdin, optional timeout) and
    `ExecutionResult` (exit_code, stdout bytes, stderr bytes). No provider
    fields leak into either.
  - `ProcessHandle` protocol (opaque optional `id`, `poll`, `wait`,
    `collect`, `terminate`, `kill`, `stdout_lines`, `stderr_lines`, `close`). The
    existing `ManagedProcess` becomes a thin public wrapper over a
    `ProcessHandle`, retaining `.pid` only where meaningful (local) and
    adding a provider-independent `.id`.
  - A small execution exception hierarchy `ExecutionError` with
    `ExecutionConnectionError`, `ExecutionTargetNotFoundError`,
    `ExecutionUnavailableError`, separate from the existing Multica CLI
    `CommandExecutionError` hierarchy. Provider failures are never
    classified as Multica CLI failures and vice versa.
- Provide three initial first-party executors:
  - `LocalExecutor` (stdlib only) preserves current local behavior; it is
    the default when no executor is supplied.
  - `MicrosandboxExecutor` (optional extra `multica-py[microsandbox]`, backed by
    `microsandbox>=0.6,<0.7`) executes in an **existing** sandbox; no
    lifecycle. The SDK is async-only; the executor bridges through a
    dedicated event-loop thread (`asyncio.run_coroutine_threadsafe`) and maps
    native per-command collect/SIGTERM/SIGKILL operations without touching
    sandbox lifecycle.
  - `SshExecutor` (optional extra `multica-py[vps]`, backed by `paramiko`)
    executes on an **existing** SSH host; generic, no DigitalOcean-specific
    API; host-key verification safe by default.
- Keep the provider set open through the same public `CommandExecutor`
  protocol and explicit `MulticaClient(executor=...)` injection. Adding a
  provider means adding one isolated adapter plus its optional extra and
  running the shared executor conformance suite; it MUST NOT add provider
  branches to `CliTransport`, `_CommandPlan`, resources, or models, and it
  MUST NOT require a plugin registry or entry-point discovery.
- Treat CubeSandbox as a concrete compatibility candidate, not as a promised
  executor in this change. A bounded spike SHALL verify its non-SSH `envd`
  command path, exact-argv preservation, non-PTY spawn/stream behavior,
  separate stdout/stderr, per-command control, target-side staging, and
  existing-target lifecycle before a later change may add a
  `CubeSandboxExecutor` and `multica-py[cubesandbox]`. No CubeSandbox
  dependency or image/build workflow enters this change.
- Refactor `CliTransport` to stop creating subprocesses directly. It keeps
  Multica semantics (build argv, global args, compatibility, decode,
  redaction, error mapping, semaphore, staging) and delegates process
  creation/transport to the configured `CommandExecutor`. The same
  `CliTransport` works with every executor.
- `MulticaClient(config, executor=...)` selects a non-local backend.
  Omitting `executor` remains equivalent to `LocalExecutor()`; the common
  case stays one-argument. The executor is a live runtime dependency, not
  part of the immutable `ClientConfig`.
- `with_profile()`/`with_workspace()`/`with_timeout()`/`with_cwd()`/
  `with_environment()` and bound entities preserve the originating executor
  exactly; no silent fallback to local. Closing a scoped view MUST NOT
  destroy a shared executor.
- Environment semantics become **target-aware**: remote executors MUST NOT
  implicitly copy the controller's entire `os.environ`; `ClientConfig.environment`
  is explicit target-process overrides only. `LocalExecutor` MAY keep the
  current local-process inheritance for compatibility, but the generic
  `ExecutionRequest` MUST NOT require the host environment.
- `ClientConfig.executable` and `ClientConfig.cwd` are interpreted as paths
  **in the execution target**, never tested on the controller. They accept
  `str | os.PathLike`; values are converted once with `os.fspath()` and are
  never resolved or normalized through `pathlib`. Remote target paths SHOULD
  be strings, so a Windows controller passes Linux paths verbatim, while
  existing local `Path` callers remain compatible.
- SDK-owned temporary command artifacts (composite plans' `${temp.path}`)
  MUST exist in the same execution target the corresponding CLI command runs
  in. The staging contract is a standard context manager
  (`stage(label, content) -> ContextManager[str]`): the caller supplies bytes,
  the yielded string is a target-local path, and leaving the context removes
  the staged content. Path-like uploads use this path for every executor; no
  `is_local` capability or provider branch is added to `_CommandPlan`. This is
  not a general remote-filesystem SDK. SDK-owned command outputs use the bounded
  `capture_output(label) -> ContextManager[OutputArtifact]`: it provides one
  target output directory, reads only a path returned beneath that directory,
  and removes it on exit; it is not arbitrary remote filesystem access.
- `Command[T]` previews continue to render the logical Multica CLI command
  only (e.g. `multica --profile automation issue get MUL-123 --output json`);
  they MUST NOT render `ssh` or any provider wrapper. Direct
  execution and `*_command(...).run()` use the same executor.
- Optional dependencies are opt-in extras with tested compatibility ranges.
  Using a provider class without its extra installed raises a clear error
  naming the required extra. The base `multica-py` installation stays
  lightweight (only `msgspec`).
- Extras are the installation mechanism for first-party remote providers;
  there is no plugin registry, entry-point discovery, or runtime package
  installation. A caller explicitly imports a provider executor and passes it
  as `MulticaClient(executor=...)`. For Git consumers, docs include the exact
  `uv add "multica-py[microsandbox] @ git+https://github.com/maximchikAlexandr/multica-py"`
  and `uv add "multica-py[vps] @ git+https://github.com/maximchikAlexandr/multica-py"`
  forms, tag/SHA-pinned forms, and `uv add --extra <name> multica-py`
  for enabling either extra on an existing Git dependency.
- Preserve the entire existing resource-oriented API, eager methods,
  `*_command()` siblings, typed models, redaction, and the approved SDK
  contract (`contracts/sdk-contract.json`). No resource method gains a
  provider-specific parameter.

## Capabilities

### New Capabilities

- `execution-backends`: Defines the provider-independent
  `CommandExecutor`/`ExecutionRequest`/`ExecutionResult`/
  `ProcessHandle` contracts, the `ExecutionError` hierarchy, the three
  initial first-party executors (`LocalExecutor`, `MicrosandboxExecutor`,
  `SshExecutor`), the conformance-gated extension model, optional-dependency gating,
  executor lifecycle/ownership, and target-aware environment/path/staging
  semantics.

### Modified Capabilities

- `subprocess-transport`: `CliTransport` SHALL delegate process creation to
  a `CommandExecutor` instead of `subprocess.Popen` directly, while keeping
  all Multica semantics (argv, global args, compatibility, decode,
  redaction, error mapping, semaphore, staging). `ManagedProcess` SHALL
  wrap a provider-independent `ProcessHandle` rather than `subprocess.Popen`
  directly. The default `LocalExecutor` SHALL preserve byte-for-byte local
  behavior (descendant cleanup, terminate/kill escalation, timeout,
  cancellation).
- `sdk-surface`: `MulticaClient` SHALL accept an optional `executor`
  runtime argument (separate from immutable `ClientConfig`), default to
  local, preserve it across `with_*()` views and bound entities, expose
  deterministic `close()`, and not destroy user-supplied environments on
  close. `Command[T]` previews SHALL remain provider-independent.
- `bound-resource-relations`: Lazy/entity follow-up operations SHALL preserve
  the originating executor; closing a scoped view SHALL NOT destroy a shared
  executor/session; prefetch SHALL continue to share the same executor and
  concurrency scope.
- `raw-cli-escape-hatch`: Raw CLI commands SHALL continue to route through
  `CliTransport` and the configured executor; raw output SHALL not leak a
  provider channel object or provider-specific response.
- `verification-and-release`: Adds a reusable offline executor-conformance
  suite plus provider-specific adapter tests
  (`LocalExecutor` byte-for-byte, fake-transport `MicrosandboxExecutor`/
  `SshExecutor` argv/stdin/cwd/env/timeout
  construction, missing-extra errors, preview independence, lifecycle
  sharing), a packaging test asserting the base install stays lightweight
  and the extras install their backing packages, and a documentation-only
  CubeSandbox compatibility spike that cannot add production dependencies or
  weaken the common contract.

## Impact

- `src/multica_py/execution/` — new public advanced module: `base.py`
  (contracts plus the small `ExecutionError` hierarchy,
  `ProcessHandle.collect()` for buffered output and
  `CommandExecutor.stage(label, content)` as a context manager), `local.py`,
  `microsandbox.py`, `ssh.py`.
  `multica_py.execution` re-exports only common contracts, exceptions, and
  `LocalExecutor`; optional providers are imported from their submodules and
  never from the package root. A future provider adds one sibling adapter
  module without changing the transport or resource layers.
- `src/multica_py/_internal/transport.py` — `CliTransport` takes a
  `CommandExecutor`; `_execute`/`spawn` build an `ExecutionRequest` and call
  `executor.run`/`executor.spawn` instead of `create_process`/
  `run_with_timeout`. No executor-type branching in the transport;
  `ExecutionRequest.environment` is explicit overrides only.
  `LocalExecutor` does `os.environ` inheritance internally. All executors use
  the existing `ExecutableNotFoundError`/`ExecutableNotRunnableError` directly
  when a reachable target cannot run its executable.
- `src/multica_py/process.py` — `ManagedProcess` wraps a `ProcessHandle`;
  `.pid` delegates to the handle when a local PID exists, otherwise the new
  `.id` is the provider-independent identity (`str | int | None`).
  `result()` routes through `handle.collect()` (buffered); streaming routes
  through `handle.stdout_lines()`/`stderr_lines()`.
- `src/multica_py/client.py` — `MulticaClient(config=None, *, executor=None)`
  stores the executor, defaults to `LocalExecutor()`, threads it through
  `CliTransport`, preserves it across `with_options()`, exposes `close()`
  that closes the executor it owns without destroying scoped views' shared
  executor.
- `src/multica_py/_internal/commands.py` — `_CommandPlan` staging resolves
  `${temp.path}` through the executor's target-side staging concept, so
  remote composite plans' temp files live where the CLI runs.
- `src/multica_py/config.py` — `ClientConfig.executable`/`cwd` documented as
  target paths; no validation against the controller filesystem. No field
  added to `ClientConfig` for the executor (it is runtime, not config).
- `src/multica_py/__init__.py` — root namespace unchanged except any
  re-exports needed for `ManagedProcess`/`ProcessResult` (already exported).
  Executors are NOT added to the root.
- `pyproject.toml` — adds `[project.optional-dependencies]` `microsandbox`
  and `vps`; base `dependencies` unchanged.
- `contracts/sdk-contract.json` — no contract change to the generator input;
  the generated resource-method contract remains untouched. The manually
  maintained execution surface is covered by focused import, constructor, and
  behavior tests rather than an exact `__all__`/annotation snapshot.
- `tests/` — new `tests/unit/execution/` with a reusable provider-conformance
  case table plus adapter-specific tests (fake executor + fake provider
  clients asserting argv/stdin/cwd/env/timeout
  construction, missing-extra errors, lifecycle, preview independence);
  existing component fake-CLI suite extended to assert a `LocalExecutor`
  preserves byte-for-byte behavior; packaging test for extras. Reuse the
  table-driven pattern; only stdlib + pytest.
- `docs/` — `execution-backends.md` documents the executor API, the three
  initial providers, the adapter recipe and conformance requirements for a
  future provider, exact uv/pip and Git-extra installation commands, explicit
  executor injection without plugin discovery, the target-aware env/path/staging rules,
  and the ownership model; `migration.md` records that eager APIs are
  unchanged and local-by-default.
- No eager public resource method is renamed, split, or removed; no
  `*_command()` sibling gains a provider parameter; the discovered-public-
  methods invariant stays green.
