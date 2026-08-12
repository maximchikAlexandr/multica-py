## Context

The current main branch defines 13 immutable bound classes directly beside resource services in nine `resources/*` modules. `_BoundEntity` lives in `models/_bound.py`; models, wire converters, resources, and entity relations therefore name canonical domain types through resource modules. The resulting graph already uses local imports to avoid cycles (`issues` must recognize `Agent`, `Squad`, `WorkspaceMember`, and `Project`; those entities expose issue relations), and the coupling will grow as entity actions and relations grow.

`ManagedProcess` currently wraps a `subprocess.Popen[bytes]`, holds a shared `ProcessSemaphore`, exposes independent stdout/stderr iterators, and finalizes pipes plus semaphore after `wait()`, completed iteration, or `close()`. `wait()` calls `Popen.wait()` without draining pipes, so sufficiently large child output can deadlock and a successful wait closes the pipes before callers can retrieve output. The synchronous transport already uses `Popen.communicate()` for ordinary commands; the managed-process API needs the equivalent safe buffered path without removing streaming.

Constraints:

- Existing root and resource-module entity imports are compatibility commitments for this change.
- Unified entities remain frozen `msgspec.Struct` values with private client and relation runtime state.
- Entity actions must continue delegating to resource command paths; CLI argv, transport, and wire decoding remain outside entities.
- `ManagedProcess` keeps its existing `datetime.timedelta | None` timeout convention and built-in `TimeoutError` surface.
- Process concurrency accounting must be released exactly once and only when process ownership actually ends.
- No external dependency, upstream CLI change, async API, or implementation code is part of this planning change.

## Goals / Non-Goals

**Goals:**

- Establish `multica_py.entities` as the only defining package for the private bound base and all bound subclasses.
- Make resource/entity ownership and allowed dependency edges mechanically testable.
- Preserve one class identity across root, canonical entity-package, and former resource-module imports.
- Add a typed immutable result for safe buffered managed-process completion.
- Make successful waits preserve output, make timeouts retryable, and make cleanup order deterministic.
- Preserve explicit incremental streaming while rejecting mixed output-consumption modes before data can be lost.

**Non-Goals:**

- Renaming entities, fields, relations, actions, resources, or normal command return types.
- Removing compatibility re-exports from resource modules in this change.
- Moving request/filter/output models into `entities`, or merging entities with wire models.
- Adding async process execution, teeing, logging integration, duration tracking, bounded spill-to-disk buffering, or decoded domain payloads in `ProcessResult`.
- Making `ManagedProcess` thread-safe; it retains its current single-owner usage model.
- Redesigning `CliTransport.run_bytes` / `run_text` or the ordinary command error-classification contract.

## Decisions

### Decision 1: Move definitions by domain and keep compatibility aliases

Create the following canonical mapping:

| Canonical module | Bound classes moved there |
| --- | --- |
| `entities/_base.py` | `_BoundEntity` and its private runtime/normalization helpers |
| `entities/agents.py` | `Agent` |
| `entities/autopilots.py` | `Autopilot`, `AutopilotRun` |
| `entities/comments.py` | `Comment`, `CommentThread` |
| `entities/issues.py` | `Issue`, `TaskRun` |
| `entities/labels.py` | `Label` |
| `entities/projects.py` | `Project` |
| `entities/skills.py` | `Skill` |
| `entities/squads.py` | `Squad` |
| `entities/workspaces.py` | `Workspace`, `WorkspaceMember` |

`entities/__init__.py` exports the 13 public classes but not `_BoundEntity`. `multica_py.__init__` imports those classes from `entities`. Each former resource module imports and re-exports its entity names from the canonical module while continuing to define only its `*Resource` service and resource-only helpers. Thus `multica_py.Issue is multica_py.entities.Issue is multica_py.resources.issues.Issue`; no wrapper or duplicate `msgspec` type is introduced. Keeping the former attributes also allows old pickle references that import a resource module and look up an entity name to resolve.

`models/_bound.py` is removed after all private references move to `entities._base`; it is not a supported public path and retaining a second facade would obscure ownership.

Alternative considered: remove the resource-module entity names entirely. Rejected because those modules currently include entity names in `__all__`, so a supposedly internal refactor would become a visible import break.

### Decision 2: Enforce a one-way service boundary without forbidding legitimate resource composition

Entity modules may import other entity classes and neutral value/relation types. They use postponed annotations, `TYPE_CHECKING`, and local canonical-entity imports where needed to break entity-to-entity cycles. They do not import resource modules at runtime. Attached relations/actions obtain services from `_client` (`client.issues`, `client.autopilots`, and so on) and call resource methods.

Resource modules import canonical entity classes directly. Internal wire models and decoders also import from `entities`, so a type reference never needs to travel through a sibling resource module. Resource-to-resource imports remain only for real service composition such as `IssueResource.comments`, `AgentResource.skills`, `ProjectResource.resources`, and `SquadResource.members`.

Use two non-overlapping adapter categories. A pure relation-state adapter only creates or updates relation state from already decoded entity/value data; it has no client, `Command`/argv, transport, or raw-wire-decoding dependency and stays in the entity layer or existing neutral relation/model infrastructure. A command-construction or wire-adaptation adapter builds CLI plans, prepares transport, or adapts raw output for a relation; it is a private method on the resource that owns the operation and is called by entity loaders through the bound client. Some relation loaders currently rely on the latter as free functions in sibling resource modules, notably `_issue_offset_page_command`, `_runs_page_command`, comment binding, and workspace/autopilot page adapters. Move those functions behind their owning resources (for example an issue-list-to-`OffsetPage` command adapter on `IssueResource`), while keeping only pure relation-state construction in the entity or neutral layer. This keeps `Command` plan construction and wire adaptation in resources without introducing entity-to-resource imports.

Add a contract test that enumerates the canonical class set, asserts defining modules and alias identity, scans resource-module defined classes, and imports entity/resource/internal converter modules in isolated interpreter processes. Add a narrow AST/import assertion for sibling resource imports: allow documented nested-service composition edges, reject imports used solely to obtain entity types.

Alternative considered: place command-construction or wire-adaptation adapters in `entities` or neutral relation helpers alongside their consumers. Rejected because those adapters inspect or rewrite command plans and raw decoders, which belongs to the owning service layer. This does not prohibit pure relation-state adapters from living in the entity or neutral layer.

### Decision 3: Use an immutable `msgspec.Struct` for `ProcessResult`

Define `ProcessResult` in `process.py` as a frozen `msgspec.Struct` with:

```python
class ProcessResult(msgspec.Struct, frozen=True):
    argv: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool: ...

    @property
    def failed(self) -> bool: ...
```

This follows the repository's closed-public-type rule, needs no dependency, and is reusable by a future async wrapper without coupling it to `Popen`. Nonzero exit is represented as data because managed-process APIs currently expose raw lifecycle status; ordinary CLI resource methods keep their existing classified exception behavior.

Export `ProcessResult` from `multica_py` and add `ProcessOutputModeError(MulticaError)` to `exceptions.py` and the root exception surface. The exception covers attempts to switch output consumers and attempts to consume output after `close()` discarded it; messages name the current and requested modes.

Alternative considered: use `subprocess.CompletedProcess[str]`. Rejected because it is mutable, uses `returncode`/`args` rather than the requested SDK field names, and does not expose the stable `ok`/`failed` contract.

### Decision 4: Model managed output as a single-owner state machine

Add private mode state and a cached result to `ManagedProcess`. The observable transitions are:

| Current state | Operation | Resulting behavior |
| --- | --- | --- |
| unclaimed | `result()` or `wait()` | claim buffered mode and call `Popen.communicate(timeout=...)` |
| buffered, incomplete after timeout | `result()` or `wait()` | retry `communicate`; Python preserves previously read bytes across timeout retries |
| buffered, complete | `result()` | return the identical cached object |
| buffered | either stream iterator begins | raise `ProcessOutputModeError` before reading |
| unclaimed | either stream iterator begins | claim streaming mode and retain current incremental iterator behavior |
| streaming | `result()` or `wait()` | raise `ProcessOutputModeError` before reading |
| unclaimed/buffered-incomplete | `terminate()` or `kill()` | signal only; caller may still collect the final result |
| any state without cached result | `close()` | terminate/escalate as needed, finalize once, mark output discarded |
| closed with discarded output | result or stream access | raise `ProcessOutputModeError`; do not touch pipes or semaphore |

The iterator claims streaming mode inside the generator body, when iteration actually begins, rather than when a generator object is created. Creating but never consuming a generator therefore does not unexpectedly block `result()`.

`result()` uses one `Popen.communicate()` call per attempt, not sequential reads and not `Popen.wait()` followed by reads. On success it decodes complete byte streams with the same strict UTF-8 policy as the existing iterators, creates and stores `ProcessResult`, and only then calls the existing idempotent finalizer. Cache-before-finalize ensures the value survives closed OS pipes. If decoding unexpectedly fails after the child exits, finalization still runs so concurrency capacity cannot leak; no result is fabricated.

On `subprocess.TimeoutExpired`, translate to the existing managed-process `TimeoutError` wording, keep buffered ownership, and do not cache/finalize. Python documents retrying `communicate()` after timeout without losing output; real-process tests pin that behavior. `wait()` becomes `return self.result(timeout).exit_code` and therefore gets the same deadlock-safe collection and timeout recovery.

Alternative considered: tee every streamed byte into an internal buffer so `result()` can follow streaming. Rejected because it silently changes memory use, complicates two-pipe coordination, and makes partial iterator consumption ambiguous. Explicit exclusive modes are smaller and deterministic.

### Decision 5: Keep finalization one-way and result-independent

The existing `_finalize()` remains the only pipe-close/semaphore-release path and stays idempotent. Successful buffered completion caches first and finalizes second. Timeout does neither. `terminate()` and `kill()` continue to signal without finalizing, allowing `result()` to drain trailing output and obtain the real return code. `close()` remains the explicit discard path: it terminates, waits, escalates to kill if required, finalizes, and records that no result is available. `__exit__` and `__del__` continue delegating to `close()`.

This preserves semaphore behavior for normal completion, timeout/retry, termination, kill, context-manager exit, explicit close, and destructor fallback without adding a second cleanup mechanism.

Alternative considered: make `terminate()`/`kill()` finalize immediately. Rejected because closing pipes before draining can lose diagnostics and would contradict the required post-signal result path.

### Decision 6: Verify moves and lifecycle behavior at contract, unit, and real-process layers

Entity relocation reuses the existing bound-entity, relation, operation-routing, serialization, docs, and typing suites. New contract rows pin defining modules, alias identity, no bound definitions under resources/models, allowed dependency edges, pure-relation versus command/wire adapter placement, and fresh-interpreter imports. The existing public operation inventory remains an invariant: entity relocation and process additions do not change the set discovered by `tests/unit/resources/test_operations.py::test_discovered_public_methods`.

Process unit tests use the existing process mock helpers to pin mode transitions, identical cached results, exception-before-read behavior, and exactly-once finalization. Real child-process/component cases cover stdout-only, stderr-only, simultaneous high-volume stdout+stderr, nonzero exit, wait-then-result, timeout-then-result retry, terminate/kill followed by result, explicit close, and existing streaming. Repeated variants are table-driven per repository rules. Documentation shows buffered `result()` for finite output and context-managed iterators for follow-style output.

## Risks / Trade-offs

- [Large mechanical entity move can hide semantic drift] → Move classes and their relation behavior intact first, retain aliases, and run the existing focused relation/public-surface tests after each domain group.
- [New module graph can introduce circular imports] → Use canonical entity imports plus deferred annotations, keep command adapters on owning resources, and add fresh-interpreter import coverage.
- [Private resource adapters could become an accidental second API] → Prefix them with `_`, test behavior through entity relations, and do not export them.
- [Buffered `wait()` can use unbounded memory for follow-style commands] → Document `result()`/`wait()` as finite-output completion and keep direct streaming as the explicit long-running path.
- [`communicate()` timeout retry semantics are subtle] → Add a real-process timeout/retry test with output before and after the timeout, and assert no duplicate/lost bytes or early semaphore release.
- [Strict mode exclusivity can reject legacy stream-then-wait patterns] → Raise a typed error with actionable guidance and document context-managed iteration as the supported streaming completion path; no silent truncation is allowed.
- [A decoder failure after process completion could leak capacity] → Finalize in the post-communicate failure path even when no `ProcessResult` can be cached.

## Migration Plan

1. Add `entities/_base.py` and domain modules, moving bound definitions without changing fields or behavior.
2. Redirect resource, model, internal wire/decoder, root, and test imports to canonical entity modules; keep resource-module compatibility aliases and existing `__all__` names.
3. Move command/wire relation adapters behind their owning resources, then verify the entity layer has no runtime resource imports and all existing relation/action tests pass.
4. Remove `models/_bound.py` after its reference count reaches zero and add architecture/import compatibility checks.
5. Add `ProcessResult`, `ProcessOutputModeError`, managed-process state transitions, and focused unit tests.
6. Add real-process lifecycle cases and update API/service/migration documentation.
7. Run the full offline pytest suite, source and test mypy, Ruff check/format, `uv run openspec validate extract-entities-and-add-process-results`, `uv run openspec validate --specs`, and `tests/unit/resources/test_operations.py::test_discovered_public_methods` before review; confirm the discovered public resource-method set is unchanged.

The change is additive at the supported public surface and does not require a data migration. Rollback is a branch revert: resource-module aliases keep import compatibility during the forward change, and no persisted state or external schema is rewritten.

## Open Questions

None. Duration tracking, async parity, tee buffering, and eventual removal of resource-module aliases are explicitly deferred to separate proposals.
