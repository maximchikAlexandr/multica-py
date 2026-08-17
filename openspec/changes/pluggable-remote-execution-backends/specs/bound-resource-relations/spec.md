## MODIFIED Requirements

### Requirement: Bound entity data boundary
Participating resource operations MUST return typed entities that privately
retain their originating `MulticaClient` view, while scalar data remains available as an
immutable typed snapshot that excludes runtime context and relations. The
originating client view SHALL retain the same `CommandExecutor` as the root
client, so bound-entity follow-up operations and lazy relations execute in
the same target as the operation that produced the entity.

#### Scenario: Resource result is bound to the same executor
- **WHEN** a participating list, get, create, update, or aggregate operation returns an entity under a non-local executor
- **THEN** its relations use the exact configuration, the same executor, and the shared process semaphore of the originating client view

#### Scenario: Passive entity operations perform no I/O
- **WHEN** a consumer reads scalar fields or uses `to_data()`, repr, equality, hashing, logging, or supported serialization
- **THEN** zero subprocess calls occur and runtime context is not serialized

### Requirement: Lazy/entity follow-up operations preserve the execution scope
Bound entity mutation methods, lazy-relation loaders, `*_command()` siblings,
and follow-up operations SHALL preserve the originating `CommandExecutor`.
A bound entity returned by a client configured with a non-local executor
SHALL execute all of its follow-up operations and lazy relations through
that same executor and SHALL NOT fall back to local execution. Prefetch
SHALL continue to share the same executor and the same concurrency scope.
Closing a scoped client view SHALL NOT close a shared user-supplied executor.

#### Scenario: Bound entity follow-up uses the same executor
- **WHEN** an `Issue` returned by a client configured with an `SshExecutor` calls `issue.update(...)` or `issue.comments.all()`
- **THEN** the follow-up operation executes through the same SSH executor and does not fall back to local

#### Scenario: Lazy relations preserve the executor
- **WHEN** `workspace.agents.all()` loads on a workspace bound to a client using a `MicrosandboxExecutor`
- **THEN** the `agents.list` command executes inside that same Microsandbox VM

#### Scenario: Prefetch shares the executor
- **WHEN** relation prefetch runs on entities bound to a non-local executor
- **THEN** every relation load executes through that same executor and the shared concurrency scope
