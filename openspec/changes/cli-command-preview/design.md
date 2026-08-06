## Context

The SDK invokes the Multica CLI through one controlled subprocess transport
`CliTransport` (`src/multica_py/_internal/transport.py`). Today every
resource method on every `*Resource` builds a `tuple[str, ...]` of command
args, calls `self._run_json_decode(args, Model)` /
`self._transport.run_text(args)` / `self._transport.spawn(args)`, decodes
the result, and returns a typed value. There is no way to inspect the
command without running it. Routing tests (`tests/cases/operations.py`,
`tests/unit/resources/test_operations.py`) reconstruct expected argv in a
separate `OperationCase.expected_argv` field and compare it against the
argv received by a mock transport — a second argv construction path that
can drift from the eager code.

The current state, verified against the repo:

- 123 canonical public resource methods covered by 207 table-driven
  `OperationCase` rows (`tests/cases/operations.py`), with the
  completeness gate `test_discovered_public_methods` asserting
  `discovered_public_methods == {c.sdk_method for c in OPERATION_CASES
  if c.is_canonical}` with no allowlist.
- Three transport methods: `CliTransport.run_bytes` (decodes JSON bytes),
  `run_text` (returns a `TextResult`), and `spawn` (returns a
  `ManagedProcess`). `_SPAWN_SDK_METHODS` in `operations.py` enumerates
  the spawn operations.
- `_build_full_argv(command_args)` in `CliTransport` prepends the
  executable and `build_global_args(config)` (`--server-url`,
  `--workspace-id`, `--profile`, `--debug`). Compat preflight runs once
  per transport inside `_execute`/`spawn`.
- `BaseResource._run_json_decode` appends `--output json` and decodes via
  `decode_json`; `_run_json_decode_list` decodes a `list[Model]`.
- Composite operations exist today: `IssueResource.create` with
  `label_ids` runs `issue create`, then a `label add` per label, then a
  final `issue get`. The byte helpers (`attachments.upload_bytes`/
  `download_bytes`) wrap a temp file/dir around a single CLI call. The
  process helpers (`daemon.start`, `daemon.logs --follow`, `setup.*`,
  `maintenance.update`, `auth.login` with `token=None`) use `spawn`.
- Lazy relations live in `src/multica_py/models/relations.py`:
  `LazyCollection` (`all`/`refresh`/`invalidate`, with retry,
  coalescing, generation outcomes), `OffsetLazyCollection` (adds
  `page(limit=, offset=)` and a multi-page `_load_pages`),
  `CursorLazyCollection` (adds `page(cursor=)` and a multi-page
  `_load_pages`), and `LazyMapping` (`all`/`refresh`/`invalidate`).
  `MulticaClient.prefetch` (`client.py`) loads selected relations under
  a `ThreadPoolExecutor` with deduplication, origin-scope validation,
  and fail-fast first-failure semantics.
- Redaction is centralized in `_internal/redaction.py`:
  `collect_secret_values`, `redact_argv`, `redact_text`. Only `--token`
  is treated as secret today.
- The approved SDK contract (`contracts/sdk-contract.json`) is the
  generator input; the public SDK surface is pinned by
  `tests/contract/test_bound_public_surface.py` (export table),
  `test_bound_public_docs.py` (doc strings), `test_public_invariants.py`
  (annotation resolution), and `test_sdk_contract.py`.

Constraints carried over from the existing specs and `AGENTS.md`:

- No CLI, transport dependency, packaging, or generated-contract change.
- No public resource method renamed, split, or removed; the
  discovered-public-methods invariant stays green.
- `uv run mypy src` and `uv run mypy tests` pass; no `Any` leaks; test
  helpers live under the typed `tests.*` override.
- Tests reuse the existing table-driven pattern (`OperationCase`,
  `ArgvCase`, `DecodeCase`, `CommandCase`); coverage grows as new rows,
  not new files. Only stdlib + pytest.
- Default suite is offline (`uv run pytest -m "not live"`); live tests
  stay gated with their triple marker.
- The approved SDK contract remains the generator input. Evidence or
  heuristic output MUST NOT create public command support directly.

GitHub issue #20 (`maximchikAlexandr/multica-py#20`) asks for exactly
this: a no-I/O `*_command()` preview for every CLI-executing SDK
operation and CLI-loading relation, with `Command[T]` as the only new
public type and the command plan as the single source of truth for
preview and execution.

## Goals / Non-Goals

**Goals:**

- One private structured command-plan type that owns argv, execution
  mode (`run_bytes` / `run_text` / `spawn`), stdin, timeout, decoder/
  result binding, ordered dependencies, and runtime references.
- One public `Command[T]` with `commands: tuple[str, ...]` and
  `run() -> T`, derived from that plan.
- A typed `*_command()` sibling for every CLI-executing public resource
  operation and every CLI-loading relation entry point, with matching
  arguments/validation and eager delegation through `*_command().run()`.
- Preview that performs no subprocess/network I/O and snapshots
  command-relevant client config at construction.
- One full-argv path in `CliTransport` used by both rendering and
  execution; `shlex.join()` after redaction for display; direct argv
  execution with no `shell=True`.
- Composite, local-I/O, and spawn plans covered by the same plan type.
- Table-driven routing tests assert through the public command preview;
  the completeness gate fails closed for new uncovered CLI-executing
  methods.
- Preserve every existing eager API, return type, transport behavior,
  redaction, cache/refresh/invalidation, concurrency, and prefetch
  semantic.

**Non-Goals:**

- No general workflow/DAG execution, parallel command steps inside one
  `Command`, rollback/compensation/resumability/automatic retries, a
  second backend or transport abstraction, a mirrored command namespace
  or dynamic proxy API, public mutable steps or result-reference
  objects, fake commands for local-only methods (`invalidate()`), or
  requiring `.run()` for ordinary eager SDK usage.
- No `prefetch_command()`.
- No change to the approved SDK contract or the upstream-contract
  pipeline.
- No change to `CliTransport`'s compat preflight, cwd, environment,
  semaphore, timeout, error classification, or process lifecycle.

## Decisions

### Decision 1: One private `_CommandPlan[T]` owns the plan; `Command[T]` is a thin public wrapper

Introduce a private structured plan in a new module
`src/multica_py/_internal/commands.py`:

```python
@dataclass(frozen=True, slots=True)
class _StepRef:
    kind: str  # "result.<field>" | "temp.path" | ...
    field: str | None = None

@dataclass(frozen=True, slots=True)
class _Step:
    argv: tuple[str, ...]                      # command args (no executable/global)
    mode: str                                  # "run_bytes" | "run_text" | "spawn"
    stdin: bytes | None = None
    timeout: datetime.timedelta | None = None
    refs: tuple[_StepRef, ...] = ()            # positions in argv that resolve from prior results
    decode: Callable[..., object] | None = None
    # ...

@dataclass(frozen=True, slots=True)
class _CommandPlan(Generic[T]):
    config_snapshot: ClientConfig              # executable + global args + cwd + env + timeout + compat
    steps: tuple[_Step, ...]                   # ordered; empty for a no-op
    finalize: Callable[[tuple[object, ...]], T]
```

The public `Command[T]` (in `src/multica_py/commands.py` or
`src/multica_py/_internal/commands.py` with re-export from
`multica_py`) holds one `_CommandPlan[T]` and exposes:

```python
class Command(Generic[T]):
    def __init__(self, plan: _CommandPlan[T]) -> None: ...
    @property
    def commands(self) -> tuple[str, ...]: ...
    def run(self) -> T: ...
    def __repr__(self) -> str: ...
```

`commands` renders each step by (a) substituting refs with their display
form (`${create.id}`, `${temp.path}`), (b) prepending the executable and
`build_global_args(config_snapshot)`, (c) redacting with `redact_argv`,
and (d) `shlex.join`-ing the result. `run()` iterates the steps,
resolves refs against prior step results (and the temp-path provider for
local-I/O steps), passes the resolved argv directly to the transport
method named by `step.mode`, collects results, and calls
`plan.finalize(results)`. An empty `steps` tuple is a no-op: `commands
== ()` and `run()` returns `finalize(())` (the cached value for a
cache-hit relation).

**Why one plan type, not a per-operation subclass tree:** the issue
explicitly forbids a public workflow/DAG API, public mutable steps, and
public result-reference objects. A single private frozen dataclass tree
keeps all of that internal. `Command[T]` stays a thin generic wrapper
with two members, satisfying "only one new public type".

**Alternative considered:** make `Command` itself the plan (no
separate `_CommandPlan`). Rejected: the plan carries refs, decoders,
and a finalize closure that are not public; exposing them on `Command`
would either leak internals or require a second internal type anyway.
Keeping the plan private and `Command` a wrapper is cleaner and matches
the issue's "private structured plan owns ...".

### Decision 2: `CliTransport` gains one full-argv path used by both rendering and execution

Today `CliTransport._build_full_argv(command_args)` is private and called
inside `_execute`/`spawn`. To make preview and execution share one
full-argv path, extract a public-to-internal method:

```python
def build_full_argv(self, command_args: tuple[str, ...]) -> tuple[str, ...]:
    return (str(self._config.executable), *build_global_args(self._config), *command_args)
```

`_execute`/`spawn` keep calling it internally. The command plan's
renderer calls `transport.build_full_argv(step.argv)` to get the
full argv, then `redact_argv(...)`, then `shlex.join(...)`. The plan's
runner calls `transport.<mode>(step.argv, stdin=..., timeout=...)`
exactly as eager code does today — `CliTransport` still prepends
executable/global args internally, so the plan never passes a rendered
string to the transport. This is the smallest change that makes
"executable and global args through one full-argv path used by both
rendering and execution" true without altering transport semantics.

**Why render through `build_full_argv` rather than reading
`config.executable` + `build_global_args` directly in the plan:** the
transport is the authority for the executable string (`str(config.
executable)`) and the global-arg order. Routing both preview and
execution through the same method guarantees they cannot diverge.

**Alternative considered:** have the plan build the full argv once and
pass it to a new `transport.run_full_argv(...)` / `spawn_full_argv(...)`.
Rejected: it would split the transport API into two parallel sets and
risk diverging cwd/env/semaphore/compat handling. Keeping
`run_bytes`/`run_text`/`spawn` taking command args (as today) and adding
only `build_full_argv` is a smaller, safer diff.

### Decision 3: Resource methods build a plan; eager bodies become `return self.<method>_command(...).run()`

Each CLI-executing resource method is split into two:

```python
def get(self, issue_id: str) -> Issue:
    return self.get_command(issue_id).run()

def get_command(self, issue_id: str) -> Command[Issue]:
    validate_nonblank(issue_id)
    return self._plan(
        steps=((("issue", "get", issue_id), "run_bytes", _decode_issue),),
        finalize=lambda r: _issue_from_wire(r[0])._with_client(self._client),
    )
```

`BaseResource` gains a small `_plan(...)` helper that snapshots
`self._config` (and the originating client's semaphore reference for
spawn plans, without mutating it) and constructs a `_CommandPlan`. The
helper centralizes snapshot + finalize, so each resource method only
declares its steps and its result binding.

For dual-input operations (`issues.create`, `projects.update`, ...),
`operation_command` carries the same `@overload` set and the same
`_resolve_request` validation as the eager operation, raised before any
plan step runs. The plan is built from the resolved request.

`_run_json_decode` / `_run_json_decode_list` stay on `BaseResource` as
the execution-time decoders; the plan's per-step `decode` closure calls
them. This keeps the decode + `--output json` append in one place.

**Why not generate `*_command()` from the approved contract:** the
contract is the generator input for signatures/argv, but the issue
requires the public command support to be reviewed and approved, not
auto-generated from evidence. The implementer writes `*_command()`
by hand next to each eager method; the contract test
(`test_approved_symbols_signatures_and_canonical_vectors_are_complete`)
already pins signatures and will catch drift.

### Decision 4: Composite plans use ordered steps with result refs

`issues.create` with `label_ids` becomes a four-step plan:

1. `issue create --title ... [--output json]` → `_IssueWire` → `Issue`
   (the `create` result; the plan records it as result index 0).
2. For each `label_id`: `issue label add ${create.id} <label_id>` →
   `LabelCollection` (argv position 3 is a `_StepRef("result", "id")`
   resolving from result 0).
3. `issue get ${create.id} --output json` → `_IssueWire` → `Issue`.

`commands` renders the ref positions as `${create.id}` (the display
name is derived from the step's result alias, here `create`). `run()`
resolves them from the actual prior result before calling the
transport. Execution stops at the first failing step; the existing
exception behavior (typed `CommandExecutionError` subclasses from
`CliTransport._raise_command_error`) is preserved because each step
calls the same transport method the eager code calls today. No rollback
or retry is added.

The display name for a result ref is `<alias>.<field>` where `<alias>`
is a short name chosen by the resource method when it builds the plan
(e.g. `create`, `temp`). This is a private rendering detail, not a
public result-reference object.

**Why `${create.id}` and not the literal id at preview time:** the id
does not exist until `issue create` runs. The issue's example shows
exactly this rendering. The structured ref is private; only its
display form appears in `commands`.

### Decision 5: Local-I/O wrappers carry a `${temp.path}` placeholder resolved by a plan-local provider

`attachments.upload_bytes_command(filename, payload, *, task_id=None)`
builds a plan whose single step has a `_StepRef("temp.path")` at the
path argv position. The plan carries a `_TempPathProvider` (a small
private callable that creates a `TemporaryDirectory` lazily on first
resolve and cleans it up in a `finally` around `run()`). `commands`
renders `${temp.path}`; `run()` calls the provider to materialize the
temp file, writes the payload, passes the resolved path to the
transport, decodes the result, and removes the temp dir in `finally`
on both success and failure. `download_bytes_command` works the same
way for the output dir, then reads the downloaded bytes from within the
plan's finalize.

This keeps the existing `_safe_leaf` validation and the
`TemporaryDirectory` cleanup behavior, and it makes "resolved argv,
local cleanup, return value, and displayed placeholder belong to one
plan" true.

**Alternative considered:** resolve the temp path eagerly at
`*_command()` construction. Rejected: the issue says the temp path
does not exist at preview time and explicitly allows a `${temp.path}`
placeholder. Eager resolution would also leak a temp file/dir on every
preview call.

### Decision 6: Spawn and dual-mode operations retain their execution mode

`daemon.start_command()`, `daemon.logs_command(follow=...)`,
`setup.cloud_command(...)`, `setup.self_host_command(...)`,
`maintenance.update_command(...)` build plans whose step `mode` is
`"spawn"`. `run()` calls `transport.spawn(argv)` and returns the
`ManagedProcess` via `finalize`. The plan never converts a spawn step
to `run_bytes`/`run_text`.

`auth.login_command(token: str | None = None)` is dual-mode:
`token is not None` → `run_text` step with the token in argv (redacted
in `commands`, preserved in execution) → `Command[str]`; `token is
None` → `spawn` step → `Command[ManagedProcess]`. The `@overload` set
mirrors the eager `login` overloads.

### Decision 7: Relation command forms live on the lazy objects

`LazyCollection`, `OffsetLazyCollection`, `CursorLazyCollection`, and
`LazyMapping` gain `all_command()`, `refresh_command()` (and
`page_command(...)` where applicable). The lazy object already owns its
loader closure and its lock; the command methods build a plan whose
`finalize` calls `self.all()` / `self.refresh()` / `self.page(...)` —
i.e. the command plan delegates to the lazy object's existing
load path, which in turn calls the resource method, which in turn
delegates through its own `*_command().run()`. This keeps one argv
builder (the resource's) and preserves coalescing/retry/generation
semantics because `run()` still goes through `self.all()`.

For a loaded relation, `all_command()` returns a `Command` with
`steps == ()` and a `finalize` returning the cached value: `commands
== ()`, `run()` returns the cache with no I/O. `refresh_command()`
always carries a loader plan (it forces a load) and updates the cache
on success via `self.refresh()`. `page_command()` is exact and static:
it builds the single-page plan from the page loader's argv template.
For `OffsetLazyCollection`, the full `all_command()` is a composite
plan that creates each runtime page from the same page-command factory;
before execution, `commands` shows the exact first page and one
explicit next-page template with result references (e.g.
`${page.next_offset}`), never a `# repeat while ...` comment.

`invalidate()` is unchanged and gets no command variant. Dunder methods
(`__iter__`, `__len__`, `__contains__`, `__getitem__`) continue to
route through `all()` → `all_command().run()`.

`MulticaClient.prefetch` is unchanged in signature and behavior; it
loads each selected relation through `relation.all()` (which is now
`all_command().run()`). No `prefetch_command()` is added.

**Why put command methods on the lazy objects rather than only on the
resources:** the issue requires `relation.all_command()`,
`relation.refresh_command()`, `relation.page_command(...)`. The lazy
object is the public entry point for relation loading. Delegating
through `self.all()` keeps one argv builder (the resource's) and
preserves the lock/coalescing/generation behavior for free.

### Decision 8: Config snapshot at construction

`BaseResource._plan(...)` snapshots `msgspec.structs.replace(config)`
(executable, server_url, workspace_id, profile, cwd, environment,
timeout, compatibility, min_cli_version, max_cli_version, debug,
encoding, max_processes) into the plan. `build_full_argv` uses the
snapshot, not the live config. Later `client.with_profile("b")` views
do not affect an already-constructed `Command`. The semaphore is not
snapshotted (it is a shared runtime object); spawn plans reference it
through the transport at `run()` time, exactly as eager code does.

### Decision 9: Redaction reuse, no new secret surface

The plan's renderer calls the existing `redact_argv` and
`collect_secret_values` on the full argv. No new secret kind is
introduced; `--token` remains the only one. `Command.__repr__` renders
`commands` (already redacted), so `repr(command)` is safe. Exception
messages from `CliTransport` already use `redact_argv`/`redact_text`;
because `run()` calls the same transport methods, exception behavior is
unchanged.

### Decision 10: Test migration extends `OperationCase`, no parallel hierarchy

`OperationCase` gains a `expected_commands: tuple[str, ...] = ()` field
(or, to avoid storing two argv forms, a `command_preview: tuple[str,
...] = ()` field holding the rendered `commands` tuple including
executable + global args + `shlex.join` quoting). The routing assertion
in `tests/unit/resources/test_operations.py::_assert_transport_call` is
rewritten to:

1. construct `command = resource.<method>_command(*args, **kwargs)`;
2. assert `command.commands == case.expected_commands`;
3. call `result = command.run()`;
4. `case.assert_result(result, mock_transport)`;
5. assert the transport received the same plan-derived argv/execution-
   mode/stdin/timeout, normalizing only `dynamic_argv_positions`.

`expected_argv` (the command-args form, without executable/global args)
is retained for the transport assertion; `expected_commands` is the
full rendered form. The two are consistent by construction because both
come from the same plan.

`tests/component/test_public_operation_routing.py`,
`tests/component/resources/cases.py`, the relation loader cases, the
process/spawn cases, the redaction cases, and `tests/live/test_smoke.py`
migrate their CLI-routing assertions to the public command preview
wherever they assert CLI routing. Transport-only tests
(`tests/unit/test_transport.py`, the three real-process cases) keep
testing `CliTransport` directly.

The completeness gate `test_discovered_public_methods` is strengthened:
after asserting the discovered set equals the canonical set, it also
asserts that every canonical CLI-executing `sdk_method` has a
`<method>_command` attribute on its resource class (and, for relation
entry points, on the lazy object) and that `OPERATION_CASES` has a
command-preview case for it. Local-only methods are excluded.

**Why not a parallel `CommandPreviewCase` hierarchy:** the issue says
"the existing table-driven case inventory remains the source for
coverage" and "do not create a parallel command-preview case
hierarchy". Extending `OperationCase` with one field and rewriting the
routing assertion is the smallest change that satisfies this.

## Risks / Trade-offs

- **Risk:** Splitting every resource method into `_command` + eager
  delegation doubles the public method count and is a large, mechanical
  diff.
  → **Mitigation:** one concept-at-a-time task ordering (shared plan
  helper + `Command` first; then one resource module at a time, each
  landing green); the `_plan(...)` helper keeps each method's diff to
  a few lines. The contract test pins signatures and catches drift.
- **Risk:** Storing both `expected_argv` and `expected_commands` on
  `OperationCase` could drift if a case author updates one but not the
  other.
  → **Mitigation:** the routing assertion derives the transport argv
  from the same plan that produced `expected_commands`, so the two are
  consistent by construction. A focused case asserts
  `shlex.join(redact_argv(transport.build_full_argv(expected_argv)))
  == expected_commands[0]` for single-command cases.
- **Risk:** Composite plans with result refs are a small internal
  engine; getting ref resolution + display rendering consistent is
  fiddly.
  → **Mitigation:** one private `_StepRef` type, one renderer, one
  resolver; focused cases for `issues.create` with labels and for a
  forced-failure-at-step-N case. The engine is bounded: refs only ever
  point to prior-step results or the temp-path provider.
- **Risk:** Local-I/O `${temp.path}` plans could leak temp dirs if
  `run()` is never called or fails before cleanup.
  → **Mitigation:** cleanup runs in a `finally` around the step
  execution inside `run()`; constructing the command does not create
  the temp dir (the provider is lazy). Focused cases assert cleanup on
  success and failure.
- **Risk:** Snapshotting config could surprise callers who mutate
  `ClientConfig` in place. `ClientConfig` is `frozen=True`, so this is
  not possible today; derived clients via `with_*()` already create new
  instances.
  → **Mitigation:** no action needed; `frozen=True` makes the snapshot
  semantics unambiguous. Documented in `docs/api.md`.
- **Risk:** Spawn plans hold a `ManagedProcess` result whose lifecycle
  (semaphore release on process exit) must not be broken by the plan
  wrapper.
  → **Mitigation:** `run()` for a spawn step calls
  `transport.spawn(argv)` and returns the `ManagedProcess` directly;
  the plan does not wrap or extend it. The semaphore is acquired/released
  inside `transport.spawn` exactly as today.
- **Risk:** Putting `all_command()` on lazy objects requires the lazy
  object to know the resource's command-building path, which could
  re-introduce a second argv builder.
  → **Mitigation:** the lazy object's `all_command()` builds a plan
  whose `finalize` calls `self.all()`; `self.all()` calls the loader
  closure, which calls the resource method, which delegates through its
  own `*_command().run()`. There is still one argv builder (the
  resource's). The lazy object never builds argv itself.
- **Trade-off:** `commands` for an offset-paged `all_command()` shows
  the first page and one next-page template rather than every page,
  because pages are not known until the first page returns. This
  matches the issue's "After each page is resolved, the concrete argv
  sent to the transport MUST be derived from that same template" and
  avoids a fake infinite preview.

## Migration Plan

- One non-breaking change (no eager API or return type changes), lands
  in `feat/cli-command-preview`.
- Order: (1) private `_CommandPlan` + `Command` + `BaseResource._plan`
  + `CliTransport.build_full_argv`; (2) `IssueResource` (most
  entangled — composite create, runs, run-messages, byte helpers via
  attachments later) + `Issue`/`TaskRun` relation command forms;
  (3) `ProjectResource` + `Project` relations; (4) `AgentResource` +
  `Agent` relations; (5) `SkillResource` + `Skill` relations;
  (6) `AutopilotResource` + `Autopilot`/`AutopilotRun` relations;
  (7) `SquadResource` + `Squad` relations; (8) `WorkspaceResource` +
  `Workspace`/`WorkspaceMember` relations; (9) nested resources
  (`issue_comments`, `issue_labels`, `issue_metadata`,
  `issue_subscribers`, `agent_skills`, `skill_files`,
  `project_resources`, `squad_members`); (10) remaining resources
  (`daemon`, `auth`, `attachments`, `runtimes`, `repositories`,
  `labels`, `users`, `setup`, `maintenance`, `configuration`); (11)
  lazy collection command forms (`LazyCollection`,
  `OffsetLazyCollection`, `CursorLazyCollection`, `LazyMapping`) +
  prefetch routing verification; (12) test migration
  (`OperationCase` field + routing assertion rewrite + focused cases +
  strengthened completeness gate); (13) public export `Command` + docs;
  (14) final verification.
- Each step lands green: `uv run pytest -m "not live"`,
  `uv run mypy src`, `uv run mypy tests`, `uv run ruff check`,
  `uv run ruff format --check`.
- Rollback: revert the branch; no wire, storage, or persisted-state
  impact.

## Open Questions

None. The plan type (`_CommandPlan[T]` + `Command[T]`), the
full-argv path (`CliTransport.build_full_argv`), the composite/ref
design, the local-I/O placeholder design, the spawn/dual-mode handling,
the relation command-form placement (on the lazy objects, delegating
through `all()`), the config snapshot, the redaction reuse, and the
test migration strategy (extend `OperationCase`, rewrite the routing
assertion, strengthen the completeness gate) are settled by the
proposal and the existing codebase constraints.
