## ADDED Requirements

### Requirement: Collection and mapping relations share generation state ownership
`LazyCollection` and `LazyMapping` SHALL delegate `UNLOADED`/`LOADING`/`LOADED` transitions, generation ownership, waiter registration and outcomes, retry, failure restoration, refresh, and invalidation to one private generic state object in `models/relations.py`. Collection tuple/metadata normalization and immutable mapping normalization SHALL remain owned by their respective containers. The shared object SHALL NOT become a public cache API, pluggable backend, inheritance hierarchy, or general event framework.

#### Scenario: Concurrent first-load success is coalesced for both containers
- **WHEN** concurrent callers first load the same `LazyCollection` or `LazyMapping`
- **THEN** one loader generation runs and every waiter receives the same successful generation value

#### Scenario: Concurrent first-load failure is shared and retryable
- **WHEN** the active first-load generation raises
- **THEN** all registered waiters receive that generation's exception, state returns to `UNLOADED`, and a later caller starts a new generation

#### Scenario: Failed refresh restores container-specific prior state
- **WHEN** refresh fails after a collection with metadata or an immutable mapping has loaded
- **THEN** the prior value and collection metadata remain atomically available and the refresh error is raised

#### Scenario: Invalidation waits for either container transition
- **WHEN** invalidation races an active collection or mapping load/refresh
- **THEN** it completes after the active generation and leaves the relation `UNLOADED` with no partial result

### Requirement: Relation commands compose through the command module
Relation code SHALL construct cached/no-step commands, coalesced run wrappers, aliased results, result-field references, and sequential offset/cursor continuations only through private transformations exported by `_internal.commands`. Relation code SHALL NOT access `command._plan`, instantiate or copy `_CommandPlan`/`_Step`/`_StepRef`, or depend on their dataclass fields. Relation code SHALL retain ownership of offset/cursor semantics, page and item limits, progress guards, result aggregation, metadata, and cache installation.

#### Scenario: Cached relation command performs no I/O
- **WHEN** `all_command()` is built for an already loaded relation
- **THEN** the command module returns an inspectable no-step command whose `run()` returns the cached container value with zero transport calls

#### Scenario: Offset continuation is previewable before execution
- **WHEN** an unloaded offset relation builds `all_command()`
- **THEN** `.commands`, `repr`, and `str` expose the exact first request and a `${page.next_offset}` continuation template without running the loader or transport

#### Scenario: Cursor continuation is previewable before execution
- **WHEN** an unloaded cursor relation builds `all_command()`
- **THEN** `.commands`, `repr`, and `str` expose the exact first request and complete `${page.next_cursor.before}`/`${page.next_cursor.before_id}` template without I/O

#### Scenario: Runtime traversal retains relation-owned guards
- **WHEN** the composed sequential command encounters an empty page with more data, a repeated offset/cursor, or the page/item limit
- **THEN** the existing typed pagination error and bounded subprocess count are preserved and no partial complete-cache entry is installed

#### Scenario: Command diagnostics remain safe
- **WHEN** cached, coalesced, offset, or cursor relation commands are previewed
- **THEN** command rendering uses the command snapshot and existing redaction rules and exposes no secret-bearing internal state
