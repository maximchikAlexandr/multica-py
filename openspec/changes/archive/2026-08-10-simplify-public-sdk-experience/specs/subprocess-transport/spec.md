## ADDED Requirements

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
