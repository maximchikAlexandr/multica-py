# CLI-to-SDK Coverage Contract

**Pinned upstream:** `48b8dbf43971e5ea974bf827220cd212a1240c72`

Source tree root: `server/cmd/multica`. Root registration is in [`main.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/main.go).

This table fixes resource placement and method naming. Flags and exact models are extracted from each linked source file during implementation and tested against snapshots.

| CLI family | SDK resource | Fixed methods / nested resources | Command source |
|---|---|---|---|
| `auth`, `login` | `client.auth` | `login`, `status`, `logout` | [`cmd_auth.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_auth.go), [`cmd_login.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_login.go) |
| `setup` | `client.setup` | `cloud`, `self_host` or source-equivalent exact methods | [`cmd_setup.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_setup.go) |
| `daemon` | `client.daemon` | `start`, `stop`, `restart`, `status`, `logs`, `disk_usage` | [`cmd_daemon.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_daemon.go) |
| `workspace` | `client.workspaces` | `list`, `get`, `members`, `watch`, `unwatch` | [`cmd_workspace.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_workspace.go) |
| `issue` | `client.issues` | `list`, `get`, `pull_requests`, `children`, `create`, `update`, `assign`, `set_status`, `reorder`, `runs`, `run_messages`, `usage`, `rerun`, `cancel_task`, `search` | [`cmd_issue.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_issue.go) |
| `issue comment` | `client.issues.comments` | `list`, `add`, `delete`, `resolve`, `unresolve`; list request variants encode thread/recent/cursor/since modes | [`cmd_issue.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_issue.go) |
| `issue metadata` | `client.issues.metadata` | `list`, `get`, `set`, `delete`; metadata filters remain on `issues.list` | [`cmd_issue_metadata.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_issue_metadata.go) |
| `issue subscriber` | `client.issues.subscribers` | `list`, `add`, `remove` | [`cmd_issue.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_issue.go) |
| `issue label` | `client.issues.labels` | exact add/remove/list methods from source | [`cmd_issue_label.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_issue_label.go) |
| `project` | `client.projects` | `list`, `get`, `create`, `update`, `delete`, `set_status` | [`cmd_project.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_project.go) |
| `label` | `client.labels` | exact list/get/create/update/delete methods registered in source | [`cmd_label.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_label.go) |
| `agent` | `client.agents` | `list`, `get`, `create`, `update`, `archive`, `restore`, `tasks`, `upload_avatar` | [`cmd_agent.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_agent.go) |
| `agent skills` | `client.agents.skills` | `list`, `set` | [`cmd_agent.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_agent.go) |
| `skill` | `client.skills` | `list`, `get`, `create`, `update`, `delete`, `import_from_url` | [`cmd_skill.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_skill.go) |
| `skill files` | `client.skills.files` | `list`, `upsert`, `delete` | [`cmd_skill.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_skill.go) |
| `autopilot` | `client.autopilots` | every registered CRUD/run/history method | [`cmd_autopilot.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_autopilot.go) |
| `autopilot trigger` | `client.autopilots.triggers` | every registered trigger create/update/delete method | [`cmd_autopilot.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_autopilot.go) |
| `repo` | `client.repositories` | every registered repository method, including `checkout` | [`cmd_repo.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_repo.go) |
| `runtime` | `client.runtimes` | every registered runtime method | [`cmd_runtime.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_runtime.go) |
| `attachment` | `client.attachments` | every registered upload/download/list method | [`cmd_attachment.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_attachment.go) |
| `config` | `client.configuration` | exact show/get/set methods from source | [`cmd_config.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_config.go) |
| `squad` | `client.squads` | all registered methods; included because root/source may expose squad semantics through assignment | [`cmd_squad.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_squad.go) |
| `user` | `client.users` | all registered lookup/list methods | [`cmd_user.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_user.go) |
| `version` | `client.maintenance` | `version` | [`cmd_version.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_version.go) |
| `update` | `client.maintenance` | `update` | [`cmd_update.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/cmd_update.go) |

## Exact confirmed command registrations

The pinned source explicitly confirms the following:

- Issue: `list`, `get`, `pull-requests`/`prs`, `children`/`subissues`, `create`, `update`, `assign`, `status`, `reorder`, comments `list/add/delete/resolve/unresolve`, subscribers `list/add/remove`, `runs`, `run-messages`, `usage`, `rerun`, `cancel-task`, `search`.
- Agent: `list`, `get`, `create`, `update`, `archive`, `restore`, `tasks`, `avatar`; skills `list/set`.
- Project: `list`, `get`, `create`, `update`, `delete`, `status`.
- Skill: `list`, `get`, `create`, `update`, `delete`, `import`; files `list/upsert/delete`.
- Workspace: `list`, `get`, `members`, `watch`, `unwatch`.
- Daemon: `start`, `stop`, `status`, `restart`, `logs`, `disk-usage`.

## Source-derived enums already fixed

- `IssueStatus`: `backlog`, `todo`, `in_progress`, `in_review`, `done`, `blocked`, `cancelled`.
- `ProjectStatus`: `planned`, `in_progress`, `paused`, `completed`, `cancelled`.

No SDK command may be implemented from this summary alone; the linked Go implementation and its `init()` flags remain mandatory inputs.
