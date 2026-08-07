## MODIFIED Requirements

### Requirement: Bound entity data boundary

Participating resource operations MUST return typed entities that
privately retain their originating `MulticaClient` view, while scalar
data remains available as an immutable typed snapshot that excludes
runtime context and relations. Every CLI-loading relation entry point
(`all`, `refresh`, offset `page`, cursor `page`) SHALL expose a matching
typed command method returning `Command[T]` / `Command[Mapping[K, V]]` /
`Command[OffsetPage[T]]` / `Command[CursorPage[T]]`:
`all_command()`, `refresh_command()`,
`OffsetLazyCollection.page_command(limit=, offset=)`,
`CursorLazyCollection.page_command(cursor=)`. `invalidate()` SHALL remain
local-only and SHALL NOT receive a command variant. Collection/mapping
dunder methods (`__iter__`, `__len__`, `__contains__`, `__getitem__`)
SHALL load through the same `all_command().run()` path. Concurrent
callers SHALL retain the existing load coalescing, retry, and generation
semantics. Command construction SHALL perform no subprocess I/O.

#### Scenario: Resource result is bound

- **WHEN** a participating list, get, create, update, or aggregate
  operation returns an entity
- **THEN** its relations use the exact configuration and services of the
  originating client view and its shared process semaphore

#### Scenario: Passive entity operations perform no I/O

- **WHEN** a consumer reads scalar fields or uses `to_data()`, repr,
  equality, hashing, logging, or supported serialization
- **THEN** zero subprocess calls occur and runtime context is not
  serialized

#### Scenario: Relation entry points expose command forms

- **WHEN** a CLI-loading relation entry point is inspected
- **THEN** `all_command()`, `refresh_command()`, and (where applicable)
  `page_command()` exist and return `Command[...]`, while `invalidate()`
  has no command variant

#### Scenario: Dunder loading routes through the command plan

- **WHEN** a consumer iterates a `LazyCollection`, calls `len()` on it,
  tests containment, or looks up a `LazyMapping` key
- **THEN** the load is performed through `all_command().run()` and the
  same plan-derived argv reaches the transport as the eager `all()`
  would produce

#### Scenario: Command construction performs no I/O

- **WHEN** `relation.all_command()`, `refresh_command()`, or
  `page_command()` is constructed
- **THEN** no `CliTransport` method is called and no subprocess is
  spawned

#### Scenario: Concurrent command runs coalesce

- **WHEN** multiple threads call `all_command().run()` on the same
  lazy object concurrently
- **THEN** one loader sequence runs and all waiters observe its result
  or error, matching the existing coalescing behavior

### Requirement: Relation load points are explicit

Reading a relation property or query view MUST perform no I/O. I/O MAY
begin only through iteration, length, containment, mapping lookup,
`all()`, `page()`, `refresh()`, explicit `prefetch()`, or the matching
`*_command().run()`. Constructing a `*_command()` SHALL perform no I/O.

#### Scenario: Property access is lazy

- **WHEN** a consumer stores `relation = entity.relation`
- **THEN** transport call count remains zero and `relation.loaded` is
  false

#### Scenario: Complete load is cached

- **WHEN** iteration or `all()` (or `all_command().run()`) completes
  successfully
- **THEN** the immutable complete result is cached and repeated complete
  access performs zero additional subprocess calls until invalidation

#### Scenario: Command construction is lazy

- **WHEN** a consumer stores `command = relation.all_command()`
- **THEN** transport call count remains zero and `relation.loaded` is
  unchanged

### Requirement: Relation cache refresh and invalidation

Each bound entity MUST memoize one lazy object per relation and
normalized query parameters. The lazy object owns its state and lock;
failed loads remain retryable, refresh swaps only on success, and
successful nested mutations call `invalidate()` only on proven-stale
memoized relations. Automatic invalidation is local only when the
successful mutation signature contains the exact parent ID used by the
memoized relation. `refresh_command()` SHALL always carry a loader plan
and SHALL update the cache on success; `all_command()` on an already
loaded relation SHALL return a `Command` with `commands == ()` whose
`run()` returns the cached value without subprocess I/O; `invalidate()`
SHALL remain local-only with no command variant.

#### Scenario: Failed first load retries

- **WHEN** an initial relation load fails
- **THEN** no empty success is cached and a later load retries

#### Scenario: Failed refresh preserves prior success

- **WHEN** refresh fails after a successful cached load
- **THEN** the error is raised and the prior cached value remains
  available

#### Scenario: Concurrent first loads coalesce

- **WHEN** multiple threads load the same cache key concurrently
- **THEN** one loader sequence runs and all waiters observe its result
  or error

#### Scenario: Successful mutation targets invalidation

- **WHEN** project resources, agent skills, skill files, squad members,
  issue labels/subscribers/metadata/comments, or autopilot triggers
  mutate successfully
- **THEN** only matching affected cache keys are invalidated

#### Scenario: Cache-hit command is a no-op

- **WHEN** `all_command()` is constructed on an already-loaded relation
  and run
- **THEN** `command.commands == ()`, `command.run()` returns the cached
  value, and no `CliTransport` method is called

#### Scenario: Refresh command always carries a loader plan

- **WHEN** `refresh_command()` is constructed on a loaded or unloaded
  relation
- **THEN** `command.commands` contains the loader plan argv and
  `command.run()` performs the load with `force=True` semantics, updates
  the cache on success, and preserves the prior value on failure

### Requirement: Bounded relation prefetch

`MulticaClient.prefetch(entities, selector, *, max_parallel=4) -> None`
MUST pre-load the lazy object returned by a typed selector for multiple
bound entities using `ThreadPoolExecutor`, deduplication, and explicit
bounded parallelism through the shared process semaphore. `prefetch` is
orchestration over relation command plans, not a Multica CLI command of
its own; the SDK SHALL NOT add `prefetch_command()`. Each selected
relation SHALL load through `all_command().run()`, so the same
inspectable command path is used under concurrent prefetch. Existing
deduplication, origin-scope validation, parallelism bounds, and
deterministic first-failure behavior SHALL remain intact.

#### Scenario: Prefetch does not fake server batching

- **WHEN** the CLI has no multi-parent filter
- **THEN** prefetch runs at most one loader/page chain per distinct
  uncached parent key and does not emit an invented multi-parent command

#### Scenario: Prefetch obeys max parallelism

- **WHEN** `prefetch(..., max_parallel=N)` loads multiple parents
- **THEN** no more than `N` relation loaders and no more than the
  runtime process limit execute concurrently

#### Scenario: Prefetch validates before I/O

- **WHEN** `max_parallel < 1`, entities have mixed origin scopes, or the
  selector yields inconsistent lazy-object types
- **THEN** `ValueError` is raised before transport access

#### Scenario: Prefetch failure is fail-fast

- **WHEN** one loader fails
- **THEN** pending futures are cancelled, the first loader exception is
  re-raised, and already completed successful loads remain cached

#### Scenario: Prefetch routes through relation command plans

- **WHEN** `prefetch` loads a selected relation
- **THEN** the load is performed through the relation's
  `all_command().run()` path and the same plan-derived argv reaches the
  transport as an eager `all()` would produce

#### Scenario: No prefetch command

- **WHEN** the public surface is inspected
- **THEN** no `prefetch_command()` method exists on `MulticaClient`