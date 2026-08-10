# raw-cli-escape-hatch Specification

## Purpose
TBD - created by archiving change simplify-public-sdk-experience. Update Purpose after archive.
## Requirements
### Requirement: Structured non-interactive CLI escape hatch
`MulticaClient` SHALL expose `client.cli.command(*argv, options=None) -> Command[CliResult]` for unsupported non-interactive Multica subcommands. `argv` SHALL be a nonempty sequence of strings appended after the configured executable/global arguments; the API SHALL NOT accept a shell command string, invoke a shell, or duplicate the executable. `CliResult` SHALL be an immutable dedicated-module result containing redacted-safe stdout bytes, stderr bytes, and duration, but SHALL NOT retain unredacted full argv. Nonzero exits SHALL continue raising the existing typed transport exceptions.

#### Scenario: Unsupported command is inspectable
- **WHEN** a caller builds `client.cli.command("issue", "new-command", "MUL-123", "--flag", "value")`
- **THEN** `commands` contains one safely quoted/redacted preview and construction performs no subprocess I/O

#### Scenario: Execution remains argv based
- **WHEN** the raw command runs with spaces or shell metacharacters in an argument
- **THEN** `CliTransport` receives the original argv tuple with `shell=False` behavior and no rendered string is executed

#### Scenario: Invalid command shape fails locally
- **WHEN** argv is empty, its first element is blank/the configured executable, any element is non-string, or any element contains NUL
- **THEN** `TypeError` or `ValueError` is raised before transport

#### Scenario: Typed failures are preserved
- **WHEN** the Multica CLI exits nonzero for a raw command
- **THEN** the same classification, detail redaction, timeout, and exception contracts as typed resources apply and no unsuccessful `CliResult` is returned

### Requirement: Escape hatch participates in SDK configuration
Raw commands SHALL honor base/scoped configuration and `OperationOptions` using the same precedence and immutable command-plan snapshot as typed operations. The feature SHALL follow the current `Command` execution contract and SHALL NOT introduce asynchronous execution, interactive login, TTY attachment, indefinite streaming, or process spawning.

#### Scenario: Scoped and operation options apply
- **WHEN** a raw command is built from a profiled client with an operation-level workspace and timeout
- **THEN** preview and execution use the effective profile, workspace, cwd, environment, and timeout snapshot

#### Scenario: Process-oriented command is outside the contract
- **WHEN** a caller needs interactive authentication, TTY input, indefinite logs, or another managed process
- **THEN** documentation directs them to a dedicated typed SDK operation or `ManagedProcess` surface rather than promising support through `client.cli.command`

