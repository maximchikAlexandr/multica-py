## ADDED Requirements

### Requirement: Execution backends are verified offline and against real backends
Offline verification SHALL cover the provider-independent execution
contracts, the three initial first-party executors, optional-dependency gating,
executor lifecycle/ownership, target-aware environment/path/staging
semantics, preview independence, and the `CliTransport`/`ManagedProcess`
refactor using stdlib and pytest without a backend or network. One reusable
executor-conformance case table SHALL exercise every first-party executor
through provider-neutral factories; adding a provider SHALL add its factory
to that table rather than copy the common assertions into a new suite. The
shared cases SHALL cover exact argv, cwd, explicit environment, stdin,
timeout, byte-exact stdout/stderr/exit, run, non-PTY spawn, poll/wait,
collect/stream single ownership, opaque identity, staging and
cleanup, error mapping, and close without target destruction. Provider-only
serialization, authentication, protocol, and process-control behavior SHALL
remain in focused adapter tests.
`LocalExecutor` SHALL be asserted to preserve the pre-change ordinary-command
local subprocess behavior (argv, cwd, environment inheritance,
stdin, timeout, descendant cleanup, terminate/kill escalation, semaphore
release); path-like uploads may use a staged path but SHALL preserve bytes and
results. `MicrosandboxExecutor` and `SshExecutor`
SHALL be tested with fake provider clients asserting exact
`ExecutionRequest` construction (argv, target-local cwd, explicit
environment overrides only, stdin, timeout), `ExecutionResult`/
`ProcessHandle` mapping (including `collect()` buffered collection and
mutual-exclusion with streaming), provider-failure mapping to the small
`ExecutionError` hierarchy, and direct use of the existing executable errors
for reachable-target binary failures. Microsandbox tests SHALL assert native
`ExecHandle.collect`, `signal(SIGTERM)`, and `kill()` mapping, connection to an
existing sandbox through `Sandbox.get`/`SandboxHandle.connect`, and no
sandbox-level stop/kill/remove. SSH serialization SHALL be tested with
adversarial inputs (whitespace, quotes, `$`, backticks, `;`, newlines,
unicode in cwd/env-values/argv; invalid env names rejected). Missing-extra
errors SHALL assert the exact actionable install message.
`Command[T].commands` SHALL be asserted to remain provider-independent
(no `ssh` or provider wrapper) under non-local executors. Scoped
`with_*()` clients and bound entities SHALL be asserted to preserve the
originating executor and not fall back to local; closing a scoped view
SHALL be asserted not to close a shared user-supplied executor; root
close SHALL be asserted not to close a user-supplied executor. A
packaging test SHALL assert the base install stays lightweight (no
`microsandbox`/`paramiko` requirement) and the `microsandbox`/`vps` extras install
their backing packages with the tested compatibility ranges. In addition
to the offline suite, opt-in/gated integration smoke tests (marker
`@pytest.mark.live_executor` requiring a real backend) SHALL verify each
first-party executor against the real SDK/runtime: run a command
preserving stdout/stderr/exit; spawn and stream a long-running command;
`collect()` buffered output; terminate/kill per the executor's documented
guarantee; cwd/environment semantics; `stage(label, content)` + cleanup.
These integration tests SHALL NOT run in the default offline suite and
SHALL be excluded from `pytest -m "not live"`.

CubeSandbox SHALL be evaluated only by a compatibility spike in this change.
The spike SHALL pin reviewed source/runtime versions and record whether the
public SDK or E2B-compatible `envd` API can satisfy exact argv semantics,
non-PTY spawn, separate streams, collection, process control, staging, error
mapping, and non-destructive close. It SHALL record CubeSandbox's actual
HTTP Connect `envd` path rather than assume SSH. The spike result SHALL NOT
add a dependency, extra, production adapter, image/template build, or live
test to this change.

#### Scenario: LocalExecutor preserves byte-for-byte behavior
- **WHEN** the existing component fake-CLI suite runs with the default `LocalExecutor`
- **THEN** ordinary commands preserve argv, cwd, environment inheritance, stdin, timeout, descendant cleanup, terminate/kill escalation, and semaphore release; path-like uploads preserve exact bytes and results through staging

#### Scenario: Remote executors construct exact requests
- **WHEN** `MicrosandboxExecutor`/`SshExecutor` run a Multica command with fake provider clients
- **THEN** the executor receives an `ExecutionRequest` with exact argv, target-local cwd, explicit environment overrides only (no controller `os.environ` leak), stdin, and timeout

#### Scenario: Shared conformance cases admit another provider
- **WHEN** a new first-party executor factory is added to the conformance case table
- **THEN** the same provider-neutral run/spawn/collect/stream/control/stage/error/lifecycle assertions execute without modifying transport, command-plan, resource, or model tests

#### Scenario: Provider-only behavior stays focused
- **WHEN** an adapter requires provider-specific shell serialization, authentication, async bridging, or protocol mapping
- **THEN** only focused adapter tests cover that behavior while the shared conformance expectations remain unchanged

#### Scenario: Provider failures map to the execution hierarchy
- **WHEN** a fake provider client raises a connection-refused, target-missing, executable-missing, or session-disappeared error
- **THEN** connection/target/session failures use the matching `ExecutionError`, reachable-target executable failures use the existing executable errors, and none is classified as a Multica CLI failure

#### Scenario: SSH serialization is adversarially safe
- **WHEN** `_serialize_ssh_command` is called with cwd/env-values/argv containing shell metacharacters, whitespace, quotes, newlines, or unicode
- **THEN** the serialized command is shell-safe (every component individually quoted) and invalid env names are rejected with `ValueError`

#### Scenario: Buffered collection and streaming are mutually exclusive
- **WHEN** `ProcessHandle.collect()` is called after `stdout_lines()` has been consumed (or vice versa) in a fake-provider test
- **THEN** a `RuntimeError` is raised

#### Scenario: CLI nonzero exit is classified by the transport
- **WHEN** a fake provider returns an `ExecutionResult` with a nonzero exit code
- **THEN** `CliTransport` classifies it through the existing CLI error classifier and no `ExecutionError` is raised for that exit code

#### Scenario: Missing optional dependency gives actionable guidance
- **WHEN** a provider executor is constructed without its extra installed
- **THEN** an `ImportError` is raised whose message names the dependency and the required `multica-py[<extra>]` requirement, while installation docs provide exact uv/Git commands

#### Scenario: Optional builds remain independent
- **WHEN** packaging metadata is inspected for the `microsandbox` and `vps` extras
- **THEN** `microsandbox` installs only `microsandbox>=0.6,<0.7`, `vps` installs only `paramiko>=5,<6`, and neither dependency is present in the base installation

#### Scenario: Git-extra installation is documented exactly
- **WHEN** installation documentation is checked
- **THEN** it contains exact uv commands for base Git, `multica-py[microsandbox]`, `multica-py[vps]`, tag/SHA pinning, and enabling either extra on an existing Git dependency

#### Scenario: Provider activation is explicit
- **WHEN** an optional provider dependency is installed
- **THEN** tests and documentation require an explicit provider import and `MulticaClient(executor=...)`, with no entry-point discovery or runtime package installation

#### Scenario: Preview stays provider-independent
- **WHEN** a `*_command()` is constructed on a client configured with a non-local executor
- **THEN** `command.commands` renders only the logical Multica CLI command and no `ssh` or provider wrapper prefix appears

#### Scenario: Scoped clients and entities preserve the executor
- **WHEN** a scoped `with_workspace()` client and a bound entity from a non-local-executor client execute follow-up operations
- **THEN** they use the same non-local executor and do not fall back to local execution

#### Scenario: Scoped view close does not destroy a shared executor
- **WHEN** a scoped client view using a user-supplied executor is closed while another view still uses it
- **THEN** only the scoped transport is closed, the executor is not closed, and the other view remains usable

#### Scenario: Root close does not close a user-supplied executor
- **WHEN** the root client that was given a user-supplied executor is closed
- **THEN** the transport is closed and the executor is NOT closed

#### Scenario: Base install stays lightweight
- **WHEN** the packaging test inspects `pyproject.toml` base dependencies
- **THEN** `microsandbox` and `paramiko` are absent from base `dependencies` and are reachable only through the `microsandbox` and `vps` optional extras with tested compatibility ranges

#### Scenario: ManagedProcess identity is provider-appropriate
- **WHEN** a spawned process is inspected under each executor
- **THEN** a local handle exposes the integer PID via `.pid` and `.id`, and a remote handle exposes `.id` (`str | None`) with `.pid` returning `None` when no Unix PID is meaningful

#### Scenario: Real-backend integration smoke tests are gated
- **WHEN** `pytest -m "not live"` runs
- **THEN** no `live_executor`-marked integration test is collected

#### Scenario: Real SSH backend preserves stdout/stderr/exit
- **WHEN** the gated SSH integration test runs `SshExecutor.run` against a real SSH host
- **THEN** stdout, stderr, and exit code are preserved and `stage(label, content)` + cleanup works against the real host

#### Scenario: Real Microsandbox backend preserves stdout/stderr/exit
- **WHEN** the explicitly enabled Microsandbox integration test runs against a real runtime
- **THEN** stdout, stderr, and exit code are preserved; spawn + stream + native `collect()` work; terminate sends per-command SIGTERM and kill sends per-command SIGKILL without sandbox destruction; cwd/env semantics hold; `stage(label, content)` + cleanup works via `sandbox.fs`

#### Scenario: CubeSandbox compatibility is evidence-gated
- **WHEN** the CubeSandbox spike completes against pinned upstream evidence
- **THEN** it records pass/fail for every mandatory conformance behavior, confirms the non-SSH `envd` path, and leaves production dependencies and adapters unchanged; only a complete pass may justify a later OpenSpec change

#### Scenario: Complete offline gate is green
- **WHEN** the change is ready for delivery
- **THEN** Ruff check, Ruff format check, `mypy src`, `mypy tests`, package validation, and `pytest -m "not live"` all pass without backend or network access

### Requirement: Execution backends use focused checkpoints and one final gate
The implementation SHALL use `79501f3b1c5afe960a6b4b63abba4acae508653c`
as the immutable behavior baseline and record its complete offline evidence
once before implementation. After the local refactor, the focused component
fake-CLI and process-lifecycle tests SHALL prove local parity. Each provider
SHALL run the shared conformance cases and its own focused fake-client tests
when added. Ruff, mypy, the full
offline suite, package validation, collection-only marker verification, and
`git diff --check` SHALL run together once at the delivery gate. A failed
focused checkpoint or final gate SHALL be corrected before delivery.

#### Scenario: Baseline is recorded before implementation
- **WHEN** implementation starts
- **THEN** required offline, type, style, contract, collection, and diff gates are recorded from the pinned baseline `79501f3b1c5afe960a6b4b63abba4acae508653c` before production changes

#### Scenario: Local behavior is preserved at the Phase 1 gate
- **WHEN** Phase 1 completes
- **THEN** the existing component fake-CLI suite and process-lifecycle tests pass against `LocalExecutor` byte-for-byte against the baseline

#### Scenario: Each provider phase is independently verified
- **WHEN** Phase 4 or 5 completes
- **THEN** that provider's shared conformance cases and focused fake-client tests pass and no other optional provider dependency is required to run them

#### Scenario: Live tests remain excluded from offline collection
- **WHEN** `pytest -m "not live" --collect-only` runs at the final gate
- **THEN** no `tests/live/*` node is collected
