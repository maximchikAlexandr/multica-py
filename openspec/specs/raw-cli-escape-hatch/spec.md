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

#### Scenario: Raw command uses the configured executor
- **WHEN** a raw command runs on a client configured with a non-local executor
- **THEN** the command executes through that executor and `CliResult` exposes only provider-independent stdout/stderr/exit/duration
### Requirement: Escape hatch participates in SDK configuration
Raw commands SHALL honor base/scoped configuration and `OperationOptions` using the same precedence and immutable command-plan snapshot as typed operations. The feature SHALL follow the current `Command` execution contract and SHALL NOT introduce asynchronous execution, interactive login, TTY attachment, indefinite streaming, or process spawning.

#### Scenario: Scoped and operation options apply
- **WHEN** a raw command is built from a profiled client with an operation-level workspace and timeout
- **THEN** preview and execution use the effective profile, workspace, cwd, environment, and timeout snapshot

#### Scenario: Process-oriented command is outside the contract
- **WHEN** a caller needs interactive authentication, TTY input, indefinite logs, or another managed process
- **THEN** documentation directs them to a dedicated typed SDK operation or `ManagedProcess` surface rather than promising support through `client.cli.command`

### Requirement: Known process-oriented command forms are classified locally
`client.cli.command(*argv)` SHALL classify known command paths and overloaded execution forms before constructing a raw `Command[CliResult]`. For `auth login`, the governed bounded form `auth login --token <token>` SHALL remain allowed, including trailing arguments/options after the token operand; `auth login` without that token form SHALL be rejected as interactive, including trailing arguments/options and a missing or option-like token operand. It SHALL also reject the process-oriented forms `setup cloud`, `setup self-host`, `daemon start`, `daemon logs`, and top-level `update`, including additional arguments after those prefixes. The rejected-path registry and auth-form classifier SHALL be explicit and reviewable rather than inferred from generic command words. Unknown command paths SHALL remain available when they otherwise satisfy structured-argv validation.

#### Scenario: Bounded token login is allowed
- **WHEN** a caller builds either `client.cli.command("auth", "login", "--token", token)` or `command_command` with the same `--token <token>` form, optionally followed by trailing arguments/options
- **THEN** construction creates the ordinary bounded `Command[CliResult]` without transport or process spawning, preserves the structured argv and existing options/result contracts, and does not expose `token` in the command preview or representation

#### Scenario: Interactive authentication is rejected without a token
- **WHEN** either raw entry point receives `auth login` with no `--token <token>` operand, whether bare or followed by trailing arguments/options
- **THEN** construction raises the same `ValueError` before transport or process spawning, directs the caller to `client.auth.login(...)` whose interactive form uses `ManagedProcess`, and does not include any raw argument or token value in the error

#### Scenario: Malformed token option is rejected
- **WHEN** either raw entry point receives `auth login --token` or `auth login --token --other-option` without a token operand
- **THEN** construction raises the same local `ValueError` before transport or process spawning and does not include the token option's value or any raw argv value in the error or diagnostic text

#### Scenario: Managed daemon command is rejected
- **WHEN** a caller builds `client.cli.command("daemon", "start")` or `client.cli.command("daemon", "logs", "--follow")`
- **THEN** construction raises `ValueError` before transport and directs the caller to the dedicated daemon API and `ManagedProcess`

#### Scenario: Setup and update paths are rejected
- **WHEN** raw argv begins with `setup cloud`, `setup self-host`, or top-level `update`
- **THEN** construction raises `ValueError` before transport and identifies the corresponding typed SDK surface in the error

#### Scenario: Bounded workspace watch remains available
- **WHEN** raw argv begins with `workspace watch` and the typed `WorkspaceResource.watch[_command]` contract is `Command[ActionResult[None]]`
- **THEN** the raw escape hatch does not classify it as streaming or managed, constructs the ordinary bounded `Command[CliResult]`, and applies the existing structured-argv, option, redaction, and result contracts

#### Scenario: Unknown bounded command remains forward compatible
- **WHEN** a caller supplies a nonempty valid argv path that does not match a reviewed rejected prefix, including a newly introduced upstream bounded subcommand
- **THEN** the SDK constructs the ordinary shell-free `Command[CliResult]` under the existing configuration, redaction, timeout, and error contracts

#### Scenario: Rejection has zero execution side effects
- **WHEN** any reviewed process-oriented form, including no-token or malformed `auth login`, is rejected through `command` or `command_command`
- **THEN** no transport method, subprocess spawn, TTY attachment, or command-plan execution occurs and both entry points report the same local error

#### Scenario: Token values stay out of diagnostics
- **WHEN** an allowed token-login command is previewed or its bounded execution returns a failure containing the token in stdout/stderr
- **THEN** the command preview, representation, exception text/argv/stdout/stderr, and returned bounded result surfaces contain the existing redaction marker instead of the token value
