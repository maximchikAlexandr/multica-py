## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Executable failures are classified at the transport boundary
The SDK SHALL use `ClientConfig.executable` directly when building command argv and SHALL map `FileNotFoundError` and `PermissionError` raised by execution or spawn to the existing typed SDK exceptions. It SHALL NOT pre-resolve executables with a separate `find_executable` helper or emit a writable-directory warning before transport execution.

#### Scenario: Missing executable retains typed failure
- **WHEN** the configured executable cannot be found during command execution
- **THEN** transport raises `ExecutableNotFoundError` with the existing diagnostic contract

#### Scenario: Non-runnable executable retains typed failure
- **WHEN** the configured executable cannot be executed due to permissions
- **THEN** transport raises the existing non-runnable executable SDK error without a separate path-directory policy
