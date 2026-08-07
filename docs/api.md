# API Reference

Migration details and removed/renamed surfaces are documented in
[docs/migration.md](migration.md). A complete bound-graph example is in
[examples/resource_relations.py](../examples/resource_relations.py).

## Client

- `MulticaClient(config: ClientConfig)` — construct with immutable configuration
- `MulticaClient.with_profile(profile)` — clone with a different profile
- `MulticaClient.with_workspace(workspace_id)` — clone with a different workspace
- `MulticaClient.with_timeout(timeout)` — clone with a different default timeout
- `MulticaClient.with_cwd(cwd)` — clone with a different working directory
- `MulticaClient.with_environment(environment)` — clone with merged environment overrides
- `ClientConfig` — frozen `msgspec.Struct`: `executable`, `server_url`, `workspace_id`, `profile`, `cwd`, `environment` (immutable tuple), `timeout`, `compatibility` (CompatibilityPolicy enum), `debug`, `encoding`, `max_processes`

## Inspectable command plans

Every CLI-executing resource method also has a typed `*_command()` sibling.
It returns the public `Command[T]` type, where `T` is the same result type as
the eager method. `Command[T].commands` is always a tuple: it is empty for a
cache-hit no-op, has one item for a single CLI call, and contains ordered
commands or reference templates for a composite operation. Preview performs no
I/O. Calling `run()` executes that same immutable plan and returns `T`.

The preview is shell-rendered and redacted for display; execution still passes
the original argv values to the transport. Composite plans expose dependencies
such as `${create.id}` in their ordered command templates. The eager API remains
the default when inspection is not needed.

## Resources

All resources accessed as attributes of `MulticaClient`:

- **auth**: `status()` → `AuthenticationStatus`, `login(token)` → `str`, `login()` → `ManagedProcess`, `logout()` → `AuthenticationStatus`
- **setup**: `cloud()`, `self_host(url)` → both return `ManagedProcess`
- **daemon**: `start()` → `ManagedProcess`, `status()` → `DaemonStatus`, `stop/restart()` → `DaemonStatus`, `disk_usage()` → tuple, `logs(follow?)` → `ManagedProcess`
- **workspaces**: `list/get/members` → typed tuples/objects, `watch/unwatch` → text
- **issues**: full CRUD + `comments`, `recent_comment_threads`, `labels`, `subscribers`, `metadata`, `pull_requests`, `children`, `runs`, `run_messages`, `usage`, `rerun(issue_id)`, `cancel_task(task_id)`; create/update accept optional `project_id` (emits `--project`)
- **issues.comments**: `list` for flat comments, `list_flat`, `list_thread`, `list_recent`, `add`, `reply`, `delete`, `resolve`, `unresolve`
- **issues.metadata**: `list`, `query`, `get`, `set`, `set_typed`, `delete`
- **issues.subscribers**: `list/add/remove`
- **issues.labels**: `list/add/remove`
- **projects**: `list/get/create/update/delete/set_status`
- **projects.resources**: `list`, `add_local_directory`, `update_local_directory`, `remove`
- **labels**: `list/get/create/update/delete`
- **agents**: `list/get/create/update/archive/restore/tasks/avatar`
- **agents.skills**: `list/set`
- **skills**: `list/get/create/update/delete/import_from_url`
- **skills.files**: `list/upsert/delete`
- **autopilots**: `list/get/create/update/delete/trigger/history/trigger_add/trigger_update/trigger_delete`
- **repositories**: `list/add/remove/checkout`
- **runtimes**: `list/usage/activity/update/rename/delete`
- **attachments**: `upload/download/upload_bytes/download_bytes` (no `list`)
- **configuration**: `show/get/set`
- **squads**: `list/get`
- **users**: `profile_get/profile_update`
- **maintenance**: `version()` → `MaintenanceVersion`, `update()` → `ManagedProcess`

## Exceptions

- `MulticaError` — base
- `ExecutableNotFoundError`, `ExecutableNotRunnableError` — executable
- `UnsupportedCliVersionError` — version check
- `CommandTimeoutError`, `CommandCancelledError` — lifecycle
- `CommandExecutionError` (+ subclasses: `AuthenticationError`, `AuthorizationError`, `NotFoundError`, `ConflictError`, `ValidationError`, `NetworkError`, `UnknownCommandError`)
- `ProtocolError` (+ `JsonOutputError`, `OutputShapeError`, `EncodingError`)

## Shared Models

- `_BoundEntity` (private mixin in `multica_py.models._bound`) — frozen
  `msgspec.Struct(kw_only=True)` base that backs every unified domain class.
  Carries the `_client` field, `_require_client`, `detach`,
  `__eq__`/`__hash__`/`__repr__` over `_PUBLIC_FIELDS`, and `to_dict()` /
  `from_dict()` / `to_json()` / `from_json()`. Not exported; treat as
  implementation detail.
- Unified domain classes (`Issue`, `Project`, `Agent`, `Skill`, `Squad`,
  `Workspace`, `WorkspaceMember`, `Autopilot`, `AutopilotRun`, `Comment`,
  `CommentThread`, `TaskRun`, `Label`) — single immutable bound class per
  resource; replaces the prior `*Entity` + `*Data` pair. See
  [docs/migration.md](migration.md) for the rename table.
- `LazyCollection[T]` — cached one-call collection
- `OffsetLazyCollection[T]` — offset-paged collection with `page()` and bounded traversal
- `CursorLazyCollection[T]` — cursor-paged collection with progress guards
- `LazyMapping[K, V]` — cached mapping relation
- `Page[T]` — immutable tuple payload used by non-relation paged services
- `ActionResult` — typed success/message container for commands that expose structured action results
- `ProjectResourceRecord`, `LocalDirectoryResourceRef`, `ProjectResourceAddLocalDirectoryRequest`, `ProjectResourceUpdateLocalDirectoryRequest` — typed project-resource models
- `IssueUsage.cost_usd` — optional float decoded from `issue usage` JSON
- `JsonValue` — closed recursive JSON union. Object nodes are immutable
  `Mapping[str, JsonValue]` snapshots and arrays are tuples; use
  `AutopilotRun.to_dict()` / `to_json()` to materialize standard JSON
  containers for serializers.

## Bound entities and load points

Workspace, project, issue, agent, skill, squad, member, label, comment,
comment-thread, task-run, autopilot, and autopilot-run results are unified
domain classes. Scalar properties are passive. Relation property access is
also passive; `all()`, `page()`, iteration, `refresh()`, and
`MulticaClient.prefetch()` may invoke the CLI.

Each wrapper owns its cache. A later `get()` returns a new wrapper rather than
mutating an earlier list result. `to_json()` / `to_dict()` exclude client,
cache, and loader state. `from_json()` / `from_dict()` construct a detached
instance with `_client=None`. Detached entities raise `DetachedEntityError`
before transport access.

The complete relation inventory and removed surfaces are documented in
[docs/migration.md](migration.md).
