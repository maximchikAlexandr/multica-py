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
- **agents**: `list/get/create/update/archive/restore/tasks/upload_avatar`
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

- `Page[T]` — immutable tuple payload with `next_cursor`
- `ActionResult` — typed success/message container for commands that expose structured action results
- `ProjectResourceRecord`, `LocalDirectoryResourceRef`, `ProjectResourceAddLocalDirectoryRequest`, `ProjectResourceUpdateLocalDirectoryRequest` — typed project-resource models
- `IssueUsage.cost_usd` — optional float decoded from `issue usage` JSON
