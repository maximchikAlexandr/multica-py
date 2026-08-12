## ADDED Requirements

### Requirement: Structured managed-process result contract
The SDK SHALL expose an immutable closed `ProcessResult` type with `argv: tuple[str, ...]`, `exit_code: int`, `stdout: str`, and `stderr: str`. `ProcessResult.ok` SHALL equal `exit_code == 0`, and `ProcessResult.failed` SHALL equal `exit_code != 0`. The type SHALL represent OS/CLI process completion only and SHALL NOT replace typed domain results from ordinary resource commands or add domain decoding. The initial synchronous API SHALL NOT require duration fields or an asynchronous process API.

#### Scenario: Successful result exposes typed completion data
- **WHEN** a managed process exits with code zero and buffered output
- **THEN** its result preserves argv and both text streams, `ok is True`, and `failed is False`

#### Scenario: Failed result remains data rather than a domain exception
- **WHEN** a managed process exits with a nonzero code through the process-oriented API
- **THEN** its result preserves the actual exit code and streams, `ok is False`, and `failed is True`

#### Scenario: Result is immutable and closed
- **WHEN** a consumer inspects or type-checks `ProcessResult`
- **THEN** its fields cannot be mutated, no public `Any` is exposed, and no domain-specific payload field exists

#### Scenario: Typed resource commands keep domain return values
- **WHEN** a normal resource command such as `client.issues.get(...)` completes
- **THEN** it continues returning its documented domain model rather than `ProcessResult`

## MODIFIED Requirements

### Requirement: Deliberately small package root
The `multica_py` root SHALL export only the default/configuration and operation option types, `Command`, common page/action/process contracts including `ManagedProcess` and `ProcessResult`, primary bound entities, common workflow enums and `Unset`, and the public exception hierarchy including `ProcessOutputModeError`. Relation implementations, JSON/metadata aliases, reusable filters and semantic value objects, compatibility page names, raw CLI result details, and resource-specific output models SHALL be imported from dedicated modules. Moving canonical entity definitions into `multica_py.entities` SHALL NOT remove or replace any existing root entity export.

#### Scenario: Common path remains concise
- **WHEN** a consumer uses `from multica_py import ...`
- **THEN** the client, config/options, `Command`, `ManagedProcess`, `ProcessResult`, primary entities, common workflow enums, `Unset`, and public exceptions needed for ordinary workflows are available

#### Scenario: Advanced types use dedicated modules
- **WHEN** `multica_py.__all__` is inspected
- **THEN** request DTOs and advanced relation/wire/value/compatibility types are absent and documentation gives their dedicated-module locations when retained

#### Scenario: Entity root imports survive canonical relocation
- **WHEN** a consumer imports any existing primary bound entity from `multica_py`
- **THEN** the import resolves to the canonical class in `multica_py.entities` with unchanged identity and behavior
