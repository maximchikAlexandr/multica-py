## MODIFIED Requirements

### Requirement: Structured non-interactive CLI escape hatch
`MulticaClient` SHALL expose `client.cli.command(*argv, options=None) -> Command[CliResult]` for unsupported non-interactive Multica subcommands. `argv` SHALL be a nonempty sequence of strings appended after the configured executable/global arguments; the API SHALL NOT accept a shell command string, invoke a shell, or duplicate the executable. `CliResult` SHALL be an immutable dedicated-module result containing redacted-safe stdout bytes, stderr bytes, and duration, but SHALL NOT retain unredacted full argv. Nonzero exits SHALL continue raising the existing typed transport exceptions. Raw commands SHALL continue to route through `CliTransport` and the configured `CommandExecutor`; raw output SHALL NOT leak a provider channel object or provider-specific response object, and `CliResult` SHALL remain provider-independent.

#### Scenario: Unsupported command is inspectable
- **WHEN** a caller builds `client.cli.command("issue", "new-command", "MUL-123", "--flag", "value")`
- **THEN** `commands` contains one safely quoted/redacted preview and construction performs no subprocess I/O

#### Scenario: Execution remains argv based
- **WHEN** the raw command runs with spaces or shell metacharacters in an argument
- **THEN** `CliTransport` receives the original argv tuple with `shell=False` behavior and no rendered string is executed, and the configured executor receives an `ExecutionRequest` built from that argv

#### Scenario: Raw command uses the configured executor
- **WHEN** a raw command runs on a client configured with a non-local executor
- **THEN** the command executes through that executor and `CliResult` exposes only provider-independent stdout/stderr/exit/duration

#### Scenario: Invalid command shape fails locally
- **WHEN** argv is empty, its first element is blank/the configured executable, any element is non-string, or any element contains NUL
- **THEN** `TypeError` or `ValueError` is raised before transport

#### Scenario: Typed failures are preserved
- **WHEN** the Multica CLI exits nonzero for a raw command
- **THEN** the same classification, detail redaction, timeout, and exception contracts as typed resources apply and no unsuccessful `CliResult` is returned