# Cli Command Preview Specification

## Purpose
Define provider-independent command preview, deferred execution, rendering, composition, and coverage contracts for every CLI-backed SDK operation.

## Requirements

### Requirement: Command plan type and naming

The SDK SHALL expose one new public generic type `Command[T]` with:

- `commands: tuple[str, ...]` — safe shell-rendered Multica CLI commands in
  execution order, with executable and global args included, secrets
  redacted, and shell quoting applied via `shlex.join()`;
- `run() -> T` — execute this exact immutable command plan and return the
  normal SDK result.

For every CLI-executing public resource operation `operation(...)`, the SDK
SHALL expose a typed sibling `operation_command(...) -> Command[result]`.
The arguments, overloads, type narrowing, and validation of
`operation_command()` SHALL match `operation()` exactly, including any
dual-input convention (request-object vs direct keyword) and any
`@overload` set. The eager operation SHALL become a thin delegation:

```python
def operation(self, ...) -> Result:
    return self.operation_command(...).run()
```

`Command[T]` SHALL be the only new public type. The SDK SHALL NOT add
`preview=True` parameters, union return types, a mirrored
`client.commands.*` tree, callable proxies, metaclasses, a generic
workflow/DAG API, public mutable step objects, or public result-reference
objects. Local-only methods that perform no CLI subprocess (e.g.
`invalidate()`) SHALL NOT receive a command variant.

#### Scenario: One new public type

- **WHEN** the public surface is inspected
- **THEN** `Command` is exported from `multica_py` and is the only newly
  added public type; no `CommandStep`, `CommandPlan`, `CommandBuilder`,
  `CommandProxy`, or `Workflow` public type is added

#### Scenario: Eager operation delegates through the command plan

- **WHEN** a consumer calls `client.issues.get("issue_123")`
- **THEN** the call is equivalent to
  `client.issues.get_command("issue_123").run()` and returns the same
  `Issue` with the same bound `_client`

#### Scenario: Command method matches eager signature

- **WHEN** `operation_command()` is inspected for a dual-input operation
  (e.g. `issues.create`, `projects.update`, `issues.assign`)
- **THEN** it carries the same `@overload` set, the same positional
  request-object slot, the same keyword-only direct fields, the same
  `TypeError` on mixed input, and the same request-model validation as the
  eager operation, raised before any subprocess invocation

#### Scenario: No command variant for local-only methods

- **WHEN** the public surface is inspected
- **THEN** no `*_command()` method exists for `invalidate()` or any other
  method that performs no CLI subprocess, and no fake command is constructed
  for them

### Requirement: Command plan is the single source of truth

The private structured plan SHALL own operation argv, execution mode
(`run_bytes`, `run_text`, or `spawn`), stdin, timeout, decoder/result
binding, ordered dependencies, and runtime references. Preview rendering
and execution SHALL derive from one immutable plan instance. The SDK
SHALL NOT rebuild argv independently for preview. `commands` and the
argv passed to `CliTransport` during `run()` SHALL come from the same
plan steps.

#### Scenario: Preview and execution share one plan

- **WHEN** `command = client.issues.get_command("issue_123")` is
  constructed and then `command.run()` is called
- **THEN** the argv, execution mode, stdin, and timeout received by
  `CliTransport` are derived from the same plan steps that produced
  `command.commands`, and the preview did not perform any subprocess I/O

#### Scenario: No subprocess I/O at construction

- **WHEN** any `*_command()` is constructed
- **THEN** no `CliTransport` method is called, no subprocess is spawned,
  no network call is made, and no compat preflight runs

#### Scenario: Commands is always a tuple

- **WHEN** `command.commands` is read for a no-op, a single CLI call, or a
  composite operation
- **THEN** it is a `tuple[str, ...]`: empty for a no-op, one item for one
  CLI call, and ordered items (or explicit next-page templates) for a
  composite operation; preview metadata such as `# repeat while ...` is
  not included in `commands`

### Requirement: Snapshot client configuration at construction

The command plan SHALL snapshot command-relevant client configuration
(executable, global args derived from `ClientConfig`, cwd, environment,
timeout, compatibility policy) when the `Command` is created. Later
changes to the originating `MulticaClient` or `ClientConfig` SHALL NOT
alter the preview or the execution of an already-constructed `Command`.

#### Scenario: Later config change does not affect a constructed command

- **WHEN** `command = client.with_profile("a").issues.get_command("x")`
  is constructed, then the originating client's profile is changed
  (e.g. a new `with_profile("b")` view is created), then `command.run()`
  executes
- **THEN** `command.commands` and the argv received by `CliTransport`
  both reflect the profile snapshotted at construction time (`"a"`), not
  the later value

#### Scenario: Snapshot includes global args and executable

- **WHEN** `command.commands` is read for a command constructed under a
  client view with `server_url`, `workspace_id`, `profile`, or `debug` set
- **THEN** the rendered strings include the executable and those global
  args in the same positions `CliTransport` would emit them at execution

### Requirement: Rendering and execution safety

Display strings in `commands` SHALL be rendered with `shlex.join()` after
redaction through the existing redaction helpers. Execution SHALL pass
argv sequences directly to `CliTransport`; the SDK SHALL NOT execute
rendered strings and SHALL NOT use `shell=True`. Secrets SHALL be
redacted from `commands`, exceptions, reprs, and test output, while
execution SHALL receive the real secret value.

#### Scenario: Shell quoting is applied

- **WHEN** an argument contains a space, a quote, or a shell metacharacter
- **THEN** the corresponding `commands` entry uses `shlex.join()` quoting
  and the executed argv still contains the original unquoted value

#### Scenario: Token is redacted in preview, preserved in execution

- **WHEN** `client.auth.login_command(token="secret")` is constructed
- **THEN** `command.commands` shows `--token ***` (or the equivalent
  redacted form) and `command.run()` passes the real `secret` value to
  `CliTransport`

#### Scenario: No rendered string is executed

- **WHEN** `command.run()` executes any plan
- **THEN** `CliTransport` receives the argv tuple directly from the plan
  and no `subprocess.*(..., shell=True)` call occurs

#### Scenario: Repr and exceptions redact secrets

- **WHEN** `repr(command)`, an exception message, or test output is
  produced for a plan carrying a secret
- **THEN** the secret value is redacted and only `***` (or the equivalent
  redacted form) appears

### Requirement: Single-command plans

A single CLI call SHALL produce a one-item `commands` tuple and a `run()`
that invokes the plan's execution mode once. The execution mode
(`run_bytes`, `run_text`, `spawn`) SHALL be retained by the plan; `run()`
SHALL NOT silently convert a `spawn` plan to `run_bytes`/`run_text` or
vice versa.

#### Scenario: One JSON-decoding command

- **WHEN** `client.issues.get_command("issue_123")` is constructed and run
- **THEN** `command.commands` is a one-item tuple containing the
  executable, global args, `issue get issue_123 --output json`, and
  `command.run()` returns the bound `Issue` decoded from the
  `run_bytes` result

#### Scenario: One text-returning command

- **WHEN** `client.issues.deprioritize_command("issue_123")` is
  constructed and run
- **THEN** `command.commands` is a one-item tuple whose argv ends with
  `issue deprioritize issue_123` (no `--output json`) and `command.run()`
  returns the `run_text` result string

#### Scenario: Spawn plan retains spawn execution

- **WHEN** `client.daemon.start_command()` is constructed and run
- **THEN** `command.commands` is a one-item tuple for `daemon start` and
  `command.run()` calls `CliTransport.spawn` and returns a
  `ManagedProcess`; it does not call `run_bytes` or `run_text`

### Requirement: Composite multi-command plans

A composite operation SHALL expose an ordered multi-step plan. Each
runtime reference (e.g. `${create.id}`) SHALL be a rendered SDK result
reference, not shell interpolation; the underlying structured reference
SHALL resolve immediately before that step is passed to `CliTransport`
during `run()`. Execution SHALL stop at the first failed step and SHALL
preserve existing public exception behavior; completed steps SHALL NOT be
rolled back or repeated.

#### Scenario: Issue create with labels exposes ordered plan

- **WHEN**
  `command = client.issues.create_command(IssueCreateRequest(title="Bug", label_ids=("label_1", "label_2")))`
  is constructed
- **THEN** `command.commands` is an ordered tuple whose entries render the
  `issue create --title Bug --output json` step, a
  `issue label add ${create.id} label_1` step, a
  `issue label add ${create.id} label_2` step, and a
  `issue get ${create.id} --output json` step, with `${create.id}` shown
  as a result reference in preview

#### Scenario: Runtime reference resolves during run

- **WHEN** `command.run()` executes the create-with-labels plan
- **THEN** each `issue label add` step receives the real `create.id` value
  resolved from the prior step's result, and the `issue get` step receives
  the same resolved id

#### Scenario: Composite execution stops on first failure

- **WHEN** a composite plan's first step raises a typed SDK exception
- **THEN** the exception propagates, no subsequent step is executed, and
  completed steps are not rolled back or repeated

#### Scenario: Composite execution never returns partial success

- **WHEN** a composite plan fails partway
- **THEN** `command.run()` raises and no successful partial data is
  returned

### Requirement: Local-I/O wrappers and runtime placeholders

Convenience wrappers that combine local file work with a CLI call whose
temporary path does not exist at preview time (e.g.
`attachments.upload_bytes`, `attachments.download_bytes`) SHALL be in
scope. Their structured plan MAY carry an explicit SDK runtime
placeholder such as `${temp.path}`. The placeholder SHALL be resolved
from the same plan during `run()`. The resolved argv, local cleanup,
return value, and displayed placeholder SHALL belong to one plan, not
two argv builders. The SDK SHALL NOT claim a placeholder is an
already-resolved runtime command.

#### Scenario: upload_bytes plan carries a temp-path placeholder

- **WHEN**
  `command = client.attachments.upload_bytes_command("file.txt", b"\\x00", task_id="t1")`
  is constructed
- **THEN** `command.commands` shows the `attachment upload ${temp.path}
  --task t1 --output json` step with the `${temp.path}` placeholder and
  the preview performs no filesystem write to the eventual temp path

#### Scenario: upload_bytes run resolves the placeholder and cleans up

- **WHEN** `command.run()` executes the `upload_bytes` plan
- **THEN** a temporary file is created, the resolved path is passed to
  `CliTransport`, the decoded `AttachmentResult` is returned, and the
  temporary directory is removed on both success and failure

#### Scenario: download_bytes run resolves and reads within one plan

- **WHEN** `command.run()` executes a `download_bytes` plan
- **THEN** a temporary output directory is created, the resolved path is
  passed to `CliTransport`, the downloaded bytes are read from within the
  plan, and the temporary directory is removed on both success and failure

### Requirement: Auth login dual-mode command

`auth.login(token=None)` is in scope even though its execution mode and
result type depend on the argument. `login_command(token: str)` SHALL
produce a `Command[str]` plan that executes via `run_text` with the token
redacted in preview and preserved in execution. `login_command(token=None)`
SHALL produce a `Command[ManagedProcess]` plan that executes via `spawn`.

#### Scenario: login with token is a run_text plan

- **WHEN** `command = client.auth.login_command(token="secret")` is
  constructed and run
- **THEN** `command.commands` redacts the token, `command.run()` calls
  `CliTransport.run_text` with the real token, and the return type is
  `str`

#### Scenario: login without token is a spawn plan

- **WHEN** `command = client.auth.login_command(token=None)` is
  constructed and run
- **THEN** `command.commands` shows `auth login` with no token, and
  `command.run()` calls `CliTransport.spawn` and returns a
  `ManagedProcess`

### Requirement: Full public inventory coverage

The command surface SHALL cover the discovered public resource inventory,
not a hand-picked subset. At minimum it SHALL include every canonical
method in `tests.cases.operations.discover_public_methods()`, nested
resources (issue comments/labels/metadata/subscribers, agent skills,
skill files, project resources, squad members), all three transport
methods, issue creation with dependent label/get calls, attachment path
and byte helpers, lazy collections, lazy mappings, offset pages, cursor
pages, refresh, cache hits, dunder-triggered loading, and prefetch
routing. The completeness gate SHALL fail closed when a new public
CLI-executing method is added without a command form and
command-preview test case.

#### Scenario: Every canonical method has a command form

- **WHEN** the public surface is discovered and the canonical operation
  cases are inspected
- **THEN** every canonical CLI-executing `sdk_method` has a matching
  typed `*_command()` method and a command-preview test case

#### Scenario: New uncovered method fails the gate

- **WHEN** a new public CLI-executing method is added without a
  `*_command()` sibling and command-preview case
- **THEN** the table-driven completeness gate fails

#### Scenario: Local-only methods are excluded from the gate

- **WHEN** the completeness gate runs
- **THEN** methods that perform no CLI subprocess (e.g. `invalidate()`)
  are not required to have a command form and are not flagged as uncovered
