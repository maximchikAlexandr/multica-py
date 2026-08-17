## MODIFIED Requirements

### Requirement: Synchronous resource client
The SDK MUST expose one synchronous `MulticaClient` with stateless domain
resources and immutable typed models. `MulticaClient` SHALL accept an
optional keyword-only `executor: CommandExecutor | None` runtime argument,
defaulting to `LocalExecutor()` so that omitting it remains equivalent to
local execution and the common case stays one-argument. The executor SHALL
be a live runtime dependency and SHALL NOT be embedded in the immutable
`ClientConfig` value object. `ClientConfig` SHALL continue to describe how
the Multica CLI is invoked; the executor SHALL describe where/how that
invocation is executed.

#### Scenario: Resource calls remain stateless
- **WHEN** a consumer calls a resource method
- **THEN** no model performs hidden I/O or Active Record persistence.

#### Scenario: Default client is local
- **WHEN** `MulticaClient(config)` is constructed without an executor
- **THEN** it behaves equivalently to `MulticaClient(config, executor=LocalExecutor())` and uses local execution

#### Scenario: Executor is separate from config
- **WHEN** `MulticaClient(config, executor=SshExecutor(...))` is constructed
- **THEN** `config` remains the immutable CLI-invocation description and the executor is the live runtime execution backend

### Requirement: Default and layered client options
`MulticaClient` SHALL accept no argument and use `ClientConfig()` defaults,
while continuing to accept one explicit `ClientConfig` and an optional
keyword-only `executor`. The SDK SHALL expose `with_options(...)` for
immutable client views and `OperationOptions` for one-call overrides. The
supported override fields SHALL be `profile`, `workspace_id`, `timeout`,
`cwd`, and `environment`; omission SHALL inherit the lower layer, explicit
`None` SHALL clear nullable scalar/path settings, and an explicit empty
environment SHALL clear inherited SDK environment entries. Cwd/executable
inputs SHALL continue to accept `str | os.PathLike`, convert with
`os.fspath()`, and avoid `pathlib` resolution or controller-filesystem
validation; remote paths SHOULD be supplied as strings. Effective
precedence SHALL be operation options over scoped-client options over base
configuration. Scoped `with_*()` clients SHALL preserve the originating
executor exactly and SHALL NOT fall back to local execution. `ClientConfig.executable`
and `ClientConfig.cwd` SHALL be documented as paths in the execution
target. `ClientConfig.environment` SHALL be explicit target-process
overrides (no implicit controller `os.environ` merge for non-local
executors).

#### Scenario: Default client is usable
- **WHEN** a caller constructs `MulticaClient()`
- **THEN** it behaves as `MulticaClient(ClientConfig())` with `LocalExecutor()` and exposes the complete resource tree

#### Scenario: Explicit configuration and executor remain available
- **WHEN** a caller passes a `ClientConfig` and an executor to `MulticaClient`
- **THEN** that exact immutable configuration remains the base layer and that executor is the execution backend

#### Scenario: Scoped options do not mutate their source
- **WHEN** `scoped = client.with_options(profile="automation", workspace_id="ws_1", timeout=30, cwd="./repo")` is created
- **THEN** `scoped` uses the normalized overrides and the same executor, `client.config` is unchanged, and both clients share only the existing process semaphore and the executor

#### Scenario: Scoped clients preserve the executor
- **WHEN** `remote.with_workspace("ws_123")` is created from a client configured with a non-local executor
- **THEN** the scoped client uses the same non-local executor and does not silently fall back to local execution

#### Scenario: Per-operation options win
- **WHEN** a command is constructed with `OperationOptions(timeout=5, workspace_id="ws_2")` from a client scoped to timeout 30 and workspace `ws_1`
- **THEN** its preview and execution use timeout 5 and workspace `ws_2` while inheriting every non-overridden setting

#### Scenario: Invalid execution values fail before I/O
- **WHEN** a timeout is negative, non-finite, or not a supported duration/number, or a non-`None` profile/workspace is blank
- **THEN** construction raises `TypeError` or `ValueError` before command or transport I/O

### Requirement: Deliberately small package root
The `multica_py` root SHALL export only the default/configuration and operation option types, `Command`, common page/action/process contracts, primary bound entities, common workflow enums and `Unset`, and the public exception hierarchy. Provider executors and configuration SHALL NOT be added to the root or re-exported from the common execution package; they SHALL be imported from `multica_py.execution.<provider>`. `LocalExecutor` and common execution contracts MAY be imported from `multica_py.execution` but SHALL NOT be added to the root.

#### Scenario: Common imports remain obvious
- **WHEN** a normal user imports `MulticaClient`, `ClientConfig`, `OperationOptions`, `Issue`, `Project`, `Agent`, `IssueStatus`, or `MulticaError` from `multica_py`
- **THEN** each import succeeds

#### Scenario: Executors leave root autocomplete
- **WHEN** `multica_py.__all__` is inspected
- **THEN** every optional provider executor (including `MicrosandboxExecutor` and `SshExecutor`) and provider-specific configuration is absent from the root namespace and documentation gives its `multica_py.execution.<provider>` location

### Requirement: Executor lifecycle on the client
`MulticaClient` SHALL expose an explicit `close()` method in addition to
context-manager cleanup. `MulticaClient` owns the executor if and only if
it constructed it (the default `LocalExecutor()` when `executor is None`);
a user-supplied executor is NEVER owned by any client. `close()` on the
root client SHALL close the transport and SHALL close the executor only if
the client owns it. `close()` on a scoped `with_*()` client SHALL close
only the scoped transport and SHALL NEVER close the shared executor. Provider
executors SHALL create and own their sessions from connection parameters;
provider-client injection is outside this milestone. `close()` SHALL close
the session but SHALL NEVER destroy the execution
environment (sandbox or VM). Derived client views SHALL NOT
independently destroy a shared executor/session.

#### Scenario: Explicit close is available
- **WHEN** a caller calls `client.close()` or the context manager exits on a root client that used the default `LocalExecutor()`
- **THEN** the transport and the client-owned default executor are closed

#### Scenario: User-supplied executor survives a root client close
- **WHEN** the root client that was given a user-supplied executor is closed
- **THEN** the transport is closed and the executor is NOT closed (the user owns its lifecycle)

#### Scenario: User-supplied executor survives a scoped view close
- **WHEN** a scoped client view using a user-supplied executor is closed while the root client still uses it
- **THEN** only the scoped transport is closed, the executor is not closed, and the root client remains usable with that executor

#### Scenario: Executor closes its session without destroying the target
- **WHEN** a provider executor is closed
- **THEN** its provider session is closed and the underlying sandbox or VM remains intact
