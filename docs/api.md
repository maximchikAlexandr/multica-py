# API Reference

## Client

- `MulticaClient(config: ClientConfig)` — construct with immutable configuration
- `MulticaClient.with_profile(profile)` — clone with a different profile
- `MulticaClient.with_workspace(workspace_id)` — clone with a different workspace
- `MulticaClient.with_timeout(timeout)` — clone with a different default timeout
- `MulticaClient.with_cwd(cwd)` — clone with a different working directory
- `MulticaClient.with_environment(environment)` — clone with merged environment overrides
- `ClientConfig` — frozen `msgspec.Struct`: `executable`, `server_url`, `workspace_id`, `profile`, `cwd`, `environment` (immutable tuple), `timeout`, `compatibility` (CompatibilityPolicy enum), `debug`, `encoding`, `max_processes`

## Resources

All resources accessed as attributes of `MulticaClient`:

- **auth**: `status()` → `AuthenticationStatus`, `login(token)` → `str`, `login()` → `ManagedProcess`, `logout()` → `AuthenticationStatus`
- **setup**: `cloud()`, `self_host(url)` → both return `ManagedProcess`
- **daemon**: `start()` → `ManagedProcess`, `status()` → `DaemonStatus`, `stop/restart()` → `DaemonStatus`, `disk_usage()` → tuple, `logs(follow?)` → `ManagedProcess`
- **workspaces**: `list/get/members` → typed tuples/objects, `watch/unwatch` → text
- **issues**: full CRUD + `pull_requests`, `children`, `search`, `runs`, `run_messages`, `usage`, `rerun`, `cancel_task`
- **issues.comments**: `list` for flat comments, `list_flat`, `list_thread`, `list_recent`, `add`, `reply`, `delete`, `resolve`, `unresolve`
- **issues.metadata**: `list`, `query`, `get`, `set`, `set_typed`, `delete`
- **issues.subscribers**: `list/add/remove`
- **issues.labels**: `list/add/remove`
- **projects**: `list/get/create/update/delete/set_status`
- **labels**: `list/get/create/update/delete`
- **agents**: `list/get/create/update/archive/restore/tasks/upload_avatar`
- **agents.skills**: `list/set`
- **skills**: `list/get/create/update/delete/import_from_url`
- **skills.files**: `list/upsert/delete`
- **autopilots**: `list/get/create/update/delete/run/history/get_run`
- **autopilots.triggers**: `list/create/delete`
- **repositories**: `list/get/checkout`
- **runtimes**: `list/get`
- **attachments**: `list/upload/download`
- **configuration**: `show/get/set`
- **squads**: `list/get`
- **users**: `list/get`
- **maintenance**: `version()` → `MaintenanceVersion`, `update()` → `ManagedProcess`

## Exceptions

- `MulticaError` — base
- `ExecutableNotFoundError`, `ExecutableNotRunnableError` — executable
- `UnsupportedCliVersionError` — version check
- `CommandTimeoutError`, `CommandCancelledError` — lifecycle
- `CommandExecutionError` (+ subclasses: `AuthenticationError`, `AuthorizationError`, `NotFoundError`, `ConflictError`, `ValidationError`, `NetworkError`, `UnknownCommandError`)
- `ProtocolError` (+ `JsonOutputError`, `OutputShapeError`, `EncodingError`)

## Shared Models

- `Page[T]` — immutable tuple payload with `next_cursor`
- `ActionResult` — typed success/message container for commands that expose structured action results

