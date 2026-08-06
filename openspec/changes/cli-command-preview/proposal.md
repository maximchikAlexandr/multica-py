## Why

Callers cannot inspect the Multica CLI command(s) behind an SDK operation
without running it, and routing tests reconstruct expected argv through a
separate path from the eager execution code. That makes the SDK opaque for
debugging, scripting, and audit, and lets preview and execution drift apart
silently. The SDK surface has grown to 123 canonical resource methods with
three transport modes, dynamic argv positions, local I/O wrappers, dependent
multi-command behavior, and lazy/paged relations, so a hand-picked preview
subset no longer holds.

This change makes one immutable structured command plan the single source of
truth for both preview and execution of every CLI-executing operation, exposed
through a typed `*_command()` sibling for each eager operation. GitHub issue
#20 (`maximchikAlexandr/multica-py#20`) asks for exactly this.

## What Changes

- Add one new public type `Command[T]` with `commands: tuple[str, ...]`
  (shell-rendered, redacted, in execution order) and `run() -> T`
  (executes the same immutable plan and returns the normal SDK result).
  `Command[T]` is the only new required public type.
- Add a typed `*_command()` method to every CLI-executing public resource
  operation. Its arguments and validation MUST match the eager operation.
  The eager operation MUST become a thin delegation:
  `operation(...) -> operation_command(...).run()`.
- Add command forms to every CLI-loading relation entry point:
  `relation.all_command()`, `relation.refresh_command()`,
  `offset_relation.page_command(limit=, offset=)`,
  `cursor_relation.page_command(cursor=)`. `invalidate()` stays local-only
  with no command variant. Unloaded `all_command()` returns the loader plan;
  loaded `all_command()` returns a `Command` with `commands == ()` and a
  `run()` returning the cached value. `refresh_command()` always carries a
  loader plan and updates the cache on success.
- The private structured plan owns argv, execution mode (`run_bytes` /
  `run_text` / `spawn`), stdin, timeout, decoder/result binding, ordered
  dependencies, and runtime references. Preview construction performs no
  subprocess or network I/O.
- Composite operations (e.g. `issues.create` with `label_ids`) expose an
  ordered multi-step plan. Runtime references (e.g. `${create.id}`) are SDK
  result references rendered for display only; during `run()` the resolved
  argv is derived from the same plan. Execution stops at the first failed
  step and preserves existing public exception behavior; completed steps are
  not rolled back or repeated.
- Local-I/O wrappers (`attachments.upload_bytes` / `download_bytes`) and
  process/spawn operations (`daemon.start`, `daemon.logs`, `setup.*`,
  `maintenance.update`, `auth.login` with `token=None`) are in scope. Their
  plan MAY carry an explicit SDK runtime placeholder (e.g. `${temp.path}`)
  resolved from the same plan during `run()`. The plan retains the execution
  mode; `run()` calls `spawn()` for spawn plans, not a silent `run_bytes`
  conversion.
- `CliTransport` stays the only subprocess layer. It adds executable and
  current global arguments through one full-argv path used by both rendering
  and execution. Display strings are rendered with `shlex.join()` after
  redaction; execution argv sequences are passed directly, never as rendered
  strings, and never with `shell=True`.
- Snapshot command-relevant client configuration when the `Command` is
  created so later client/config changes cannot make preview differ from
  execution.
- Keep secrets redacted from `commands`, exceptions, reprs, and test output;
  execution still receives the real secret value.
- Do NOT add `prefetch_command()` (prefetch is orchestration over relation
  command plans, not a CLI command); prefetch MUST continue to load each
  selected relation through `all_command().run()` under the existing
  deduplication, origin-scope validation, parallelism bounds, and
  fail-fast behavior.
- Do NOT add `preview=True`, union return types, a mirrored
  `client.commands.*` tree, callable proxies, metaclasses, a generic
  workflow/DAG API, public mutable steps, public result-reference objects,
  or fake commands for local-only methods (`invalidate()`).
- Migrate the existing table-driven `OperationCase` inventory to assert
  commands through this public feature: construct the matching
  `*_command()` without subprocess I/O, assert the complete
  `command.commands` tuple (executable + global args + shell quoting),
  call `command.run()`, assert result decoding and side effects, and
  assert the transport received argv/execution-mode/stdin/timeout derived
  from the same plan. CLI-routing component cases, relation loader cases,
  process/spawn cases, redaction cases, and live smoke cases use the new
  inspectable path wherever they assert CLI routing. Transport-only tests
  may still test `CliTransport` directly.
- Add focused cases for: no-I/O command construction; one-command,
  multi-command, `run_text`, `run_bytes`, and `spawn` plans; global args
  and shell quoting; token redaction without changing executed argv; stdin
  and timeout preservation; runtime path/result-reference resolution; cache
  hit (`commands == ()`) and forced refresh; offset/cursor pagination and
  failure guards; prefetch calling relation command plans under
  concurrency; command/config snapshot behavior; failures stopping a
  composite plan at the correct step.
- Strengthen the table-driven completeness gate
  (`test_discovered_public_methods`) so it fails closed when a new public
  CLI-executing method is added without a command form and command-preview
  test case.
- No eager API or return type changes. No public resource method is renamed,
  split, or removed. `CliTransport`'s existing behavior (compatibility
  preflight, cwd, environment, semaphore, timeout, error classification,
  process lifecycle, redaction) is preserved.

## Capabilities

### New Capabilities

- `cli-command-preview`: structured, no-I/O inspectable CLI command plans for
  every CLI-executing SDK operation and CLI-loading relation, with
  `Command[T]` as the single new public type and `*_command()` siblings
  paired one-to-one with eager operations.

### Modified Capabilities

- `sdk-surface`: every CLI-executing public resource operation and every
  CLI-loading relation entry point SHALL expose a typed `*_command()` method
  whose arguments and validation match the eager operation; the eager
  operation SHALL delegate through `*_command().run()`; `Command[T]` SHALL
  be the only new public type and `prefetch_command()` SHALL NOT exist.
- `subprocess-transport`: `CliTransport` SHALL add executable and current
  global arguments through one full-argv path used by both preview rendering
  and execution; preview SHALL render with `shlex.join()` after redaction and
  execution SHALL pass argv sequences directly without `shell=True`;
  transport behavior (compatibility preflight, cwd, environment, semaphore,
  timeout, error classification, process lifecycle, redaction) SHALL be
  unchanged.
- `bound-resource-relations`: every CLI-loading relation entry point
  (`all`, `refresh`, `offset page`, `cursor page`) SHALL expose a matching
  command method; `invalidate()` SHALL remain local-only with no command
  variant; collection/mapping dunder methods SHALL load through
  `all_command().run()`; cache-hit, refresh, concurrent coalescing/retry,
  and prefetch routing semantics SHALL remain unchanged; prefetch SHALL load
  each selected relation through `all_command().run()`.
- `verification-and-release`: the table-driven completeness gate SHALL
  cover command preview for the full discovered public inventory and SHALL
  fail closed for new uncovered CLI-executing methods; CLI-routing tests
  SHALL assert the public command preview instead of maintaining a second
  expected-command construction path; offline Ruff, mypy (`src` and
  `tests`), and `pytest -m "not live"` gates SHALL pass.

## Impact

- `src/multica_py/_internal/` — introduce a private structured command-plan
  module (e.g. `_internal/commands.py`) owning argv, execution mode, stdin,
  timeout, decoder/result binding, ordered dependencies, runtime
  references, and the rendering + execution path. `CliTransport`
  (`_internal/transport.py`) gains one full-argv path used by both
  rendering and execution; existing `_execute`/`_run`/`run_bytes`/
  `run_text`/`spawn` semantics are preserved. `_internal/argv.py`
  `build_global_args` is reused by the rendering path.
- `src/multica_py/resources/` — every CLI-executing public resource method
  gains a typed `*_command()` sibling and the eager body is rewritten to
  `return self.<method>_command(...).run()`. Composite operations
  (`issues.create` with `label_ids`, byte helpers, process helpers) build
  multi-step plans. Nested resources (`issue_comments`, `issue_labels`,
  `issue_metadata`, `issue_subscribers`, `agent_skills`, `skill_files`,
  `project_resources`, `squad_members`) get command forms for their
  CLI-executing methods. Local-only methods (`invalidate()` and similar)
  get none.
- `src/multica_py/models/relations.py` — `LazyCollection`,
  `OffsetLazyCollection`, `CursorLazyCollection`, and `LazyMapping` gain
  `all_command()`, `refresh_command()`, and `page_command()` (where
  applicable) returning `Command[T]` / `Command[Mapping[K, V]]` /
  `Command[OffsetPage[T]]` / `Command[CursorPage[T]]`; cache-hit and refresh
  semantics are preserved; concurrent coalescing/retry generation behavior
  is preserved; `invalidate()` is unchanged.
- `src/multica_py/client.py` — `MulticaClient.prefetch` loads each selected
  relation through `all_command().run()`; no `prefetch_command()` is added.
- `src/multica_py/__init__.py` — export `Command`. No other public type is
  added; no existing public type is removed or renamed.
- `contracts/sdk-contract.json` — no contract change. The approved SDK
  contract remains the generator input; evidence/heuristic output MUST NOT
  create public command support directly.
- `tests/cases/operations.py` — `OperationCase` extended with command
  preview expectations and the routing assertion rewritten to construct the
  `*_command()`, assert `command.commands`, call `command.run()`, and
  assert transport received the same plan's argv/execution-mode/stdin/
  timeout. The discovered-public-methods invariant stays green and is
  strengthened to fail closed for new uncovered CLI-executing methods.
- `tests/component/`, `tests/unit/resources/`, `tests/contract/`,
  `tests/live/` — CLI-routing assertions migrate to the public command
  preview path; transport-only tests keep testing `CliTransport` directly.
- `docs/` — `api.md` and `service-usage.md` document the `*_command()`
  convention and the `Command[T]` shape; `migration.md` records that eager
  APIs are unchanged and that `commands` is a tuple (empty for a no-op, one
  item for one CLI call, ordered items/templates for composite operations).
- No CLI, transport dependency, packaging, or generated-contract change. No
  eager public method is renamed, split, or removed.