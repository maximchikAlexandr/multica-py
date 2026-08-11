## ADDED Requirements

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
