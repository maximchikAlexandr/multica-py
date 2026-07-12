# CLI-to-SDK Coverage Contract

**Pinned upstream:** `48b8dbf43971e5ea974bf827220cd212a1240c72`

Source tree root: `server/cmd/multica`. Root registration is in [`main.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/main.go).

This table is the current manifest-backed command contract. Every non-unsupported row must resolve to exactly one SDK operation and one source-backed output mode.

Manifest source: `/Users/alexandr/local_dev/repositories/my_projects/multica-py/src/multica_py/_generated/cli_manifest.json`

Current totals:

- `108` manifest command rows
- `107` supported rows
- `1` explicit unsupported row

| Command | SDK method | Output mode | Aliases | Status | Reason | Source file |
|---|---|---|---|---|---|---|
| `auth status` | `auth.status` | `json` |  | `supported` |  | `cmd_auth.go` |
| `auth login` | `auth.login` | `text` |  | `supported` |  | `cmd_login.go` |
| `auth logout` | `auth.logout` | `json` |  | `supported` |  | `cmd_auth.go` |
| `setup cloud` | `setup.cloud` | `text` |  | `supported` |  | `cmd_setup.go` |
| `setup self-host` | `setup.self_host` | `text` |  | `supported` |  | `cmd_setup.go` |
| `daemon status` | `daemon.status` | `json` |  | `supported` |  | `cmd_daemon.go` |
| `daemon start` | `daemon.start` | `text` |  | `supported` |  | `cmd_daemon.go` |
| `daemon stop` | `daemon.stop` | `json` |  | `supported` |  | `cmd_daemon.go` |
| `daemon restart` | `daemon.restart` | `json` |  | `supported` |  | `cmd_daemon.go` |
| `daemon logs` | `daemon.logs` | `text` |  | `supported` |  | `cmd_daemon.go` |
| `daemon disk-usage` | `daemon.disk_usage` | `json` |  | `supported` |  | `cmd_daemon.go` |
| `workspace list` | `workspaces.list` | `json` |  | `supported` |  | `cmd_workspace.go` |
| `workspace get` | `workspaces.get` | `json` |  | `supported` |  | `cmd_workspace.go` |
| `workspace members` | `workspaces.members` | `json` |  | `supported` |  | `cmd_workspace.go` |
| `workspace switch` | `workspaces.switch` | `text` |  | `supported` |  | `cmd_workspace.go` |
| `workspace watch` | `workspaces.watch` | `text` |  | `supported` |  | `cmd_workspace.go` |
| `workspace unwatch` | `workspaces.unwatch` | `text` |  | `supported` |  | `cmd_workspace.go` |
| `issue list` | `issues.list` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue get` | `issues.get` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue pull-requests` | `issues.pull_requests` | `json` | `prs` | `supported` |  | `cmd_issue.go` |
| `issue children` | `issues.children` | `json` | `subissues` | `supported` |  | `cmd_issue.go` |
| `issue create` | `issues.create` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue update` | `issues.update` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue assign` | `issues.assign` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue set-status` | `issues.set_status` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue reorder` | `issues.reorder` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue search` | `issues.search` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue runs` | `issues.runs` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue run-messages` | `issues.run_messages` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue usage` | `issues.usage` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue rerun` | `issues.rerun` | `text` |  | `supported` |  | `cmd_issue.go` |
| `issue cancel-task` | `issues.cancel_task` | `text` |  | `supported` |  | `cmd_issue.go` |
| `issue comment list` | `issues.comments.list` | `json` |  | `supported` | flat comments via `list(issue_id)`; extended typed modes via `list_flat`, `list_thread`, `list_recent` | `cmd_issue.go` |
| `issue comment add` | `issues.comments.add` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue comment reply` | `issues.comments.reply` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue comment delete` | `issues.comments.delete` | `text` |  | `supported` |  | `cmd_issue.go` |
| `issue comment resolve` | `issues.comments.resolve` | `text` |  | `supported` |  | `cmd_issue.go` |
| `issue comment unresolve` | `issues.comments.unresolve` | `text` |  | `supported` |  | `cmd_issue.go` |
| `issue metadata list` | `issues.metadata.list` | `json` |  | `supported` | basic list via `list(issue_id)`; repeated predicate/cursor mode via `query(MetadataListRequest)` | `cmd_issue_metadata.go` |
| `issue metadata get` | `issues.metadata.get` | `json` |  | `supported` |  | `cmd_issue_metadata.go` |
| `issue metadata set` | `issues.metadata.set` | `json` |  | `supported` | inferred primitive typing via `set`; explicit type via `set_typed(MetadataSetRequest)` | `cmd_issue_metadata.go` |
| `issue metadata delete` | `issues.metadata.delete` | `text` |  | `supported` |  | `cmd_issue_metadata.go` |
| `issue subscriber list` | `issues.subscribers.list` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue subscriber add` | `issues.subscribers.add` | `json` |  | `supported` |  | `cmd_issue.go` |
| `issue subscriber remove` | `issues.subscribers.remove` | `text` |  | `supported` |  | `cmd_issue.go` |
| `issue label list` | `issues.labels.list` | `json` |  | `supported` |  | `cmd_issue_label.go` |
| `issue label add` | `issues.labels.add` | `text` |  | `supported` |  | `cmd_issue_label.go` |
| `issue label remove` | `issues.labels.remove` | `text` |  | `supported` |  | `cmd_issue_label.go` |
| `project list` | `projects.list` | `json` |  | `supported` |  | `cmd_project.go` |
| `project get` | `projects.get` | `json` |  | `supported` |  | `cmd_project.go` |
| `project create` | `projects.create` | `json` |  | `supported` |  | `cmd_project.go` |
| `project update` | `projects.update` | `json` |  | `supported` |  | `cmd_project.go` |
| `project delete` | `projects.delete` | `text` |  | `supported` |  | `cmd_project.go` |
| `project set-status` | `projects.set_status` | `json` |  | `supported` |  | `cmd_project.go` |
| `label list` | `labels.list` | `json` |  | `supported` |  | `cmd_label.go` |
| `label get` | `labels.get` | `json` |  | `supported` |  | `cmd_label.go` |
| `label create` | `labels.create` | `json` |  | `supported` |  | `cmd_label.go` |
| `label update` | `labels.update` | `json` |  | `supported` |  | `cmd_label.go` |
| `label delete` | `labels.delete` | `text` |  | `supported` |  | `cmd_label.go` |
| `agent list` | `agents.list` | `json` |  | `supported` |  | `cmd_agent.go` |
| `agent get` | `agents.get` | `json` |  | `supported` |  | `cmd_agent.go` |
| `agent create` | `agents.create` | `json` |  | `supported` |  | `cmd_agent.go` |
| `agent update` | `agents.update` | `json` |  | `supported` |  | `cmd_agent.go` |
| `agent archive` | `agents.archive` | `text` |  | `supported` |  | `cmd_agent.go` |
| `agent restore` | `agents.restore` | `text` |  | `supported` |  | `cmd_agent.go` |
| `agent tasks` | `agents.tasks` | `json` |  | `supported` |  | `cmd_agent.go` |
| `agent avatar upload` | `agents.upload_avatar` | `text` |  | `supported` |  | `cmd_agent.go` |
| `agent skill list` | `agents.skills.list` | `json` |  | `supported` |  | `cmd_agent.go` |
| `agent skill set` | `agents.skills.set` | `text` |  | `supported` |  | `cmd_agent.go` |
| `skill list` | `skills.list` | `json` |  | `supported` |  | `cmd_skill.go` |
| `skill get` | `skills.get` | `json` |  | `supported` |  | `cmd_skill.go` |
| `skill create` | `skills.create` | `json` |  | `supported` |  | `cmd_skill.go` |
| `skill update` | `skills.update` | `json` |  | `supported` |  | `cmd_skill.go` |
| `skill delete` | `skills.delete` | `text` |  | `supported` |  | `cmd_skill.go` |
| `skill import` | `skills.import_from_url` | `json` |  | `supported` |  | `cmd_skill.go` |
| `skill file list` | `skills.files.list` | `json` |  | `supported` |  | `cmd_skill.go` |
| `skill file upsert` | `skills.files.upsert` | `json` |  | `supported` |  | `cmd_skill.go` |
| `skill file delete` | `skills.files.delete` | `text` |  | `supported` |  | `cmd_skill.go` |
| `autopilot list` | `autopilots.list` | `json` |  | `supported` |  | `cmd_autopilot.go` |
| `autopilot get` | `autopilots.get` | `json` |  | `supported` |  | `cmd_autopilot.go` |
| `autopilot create` | `autopilots.create` | `json` |  | `supported` |  | `cmd_autopilot.go` |
| `autopilot update` | `autopilots.update` | `json` |  | `supported` |  | `cmd_autopilot.go` |
| `autopilot delete` | `autopilots.delete` | `text` |  | `supported` |  | `cmd_autopilot.go` |
| `autopilot run` | `autopilots.run` | `json` |  | `supported` |  | `cmd_autopilot.go` |
| `autopilot history` | `autopilots.history` | `json` |  | `supported` |  | `cmd_autopilot.go` |
| `autopilot run get` | `autopilots.get_run` | `json` |  | `supported` |  | `cmd_autopilot.go` |
| `autopilot trigger list` | `autopilots.triggers.list` | `json` |  | `supported` |  | `cmd_autopilot.go` |
| `autopilot trigger create` | `autopilots.triggers.create` | `json` |  | `supported` |  | `cmd_autopilot.go` |
| `autopilot trigger delete` | `autopilots.triggers.delete` | `text` |  | `supported` |  | `cmd_autopilot.go` |
| `repo list` | `repositories.list` | `json` |  | `supported` |  | `cmd_repo.go` |
| `repo get` | `repositories.get` | `json` |  | `supported` |  | `cmd_repo.go` |
| `repo checkout` | `repositories.checkout` | `json` |  | `supported` |  | `cmd_repo.go` |
| `runtime list` | `runtimes.list` | `json` |  | `supported` |  | `cmd_runtime.go` |
| `runtime get` | `runtimes.get` | `json` |  | `supported` |  | `cmd_runtime.go` |
| `attachment list` | `attachments.list` | `json` |  | `supported` |  | `cmd_attachment.go` |
| `attachment upload` | `attachments.upload` | `json` |  | `supported` |  | `cmd_attachment.go` |
| `attachment download` | `attachments.download` | `text` |  | `supported` |  | `cmd_attachment.go` |
| `config show` | `configuration.show` | `text` |  | `supported` |  | `cmd_config.go` |
| `config get` | `configuration.get` | `text` |  | `supported` |  | `cmd_config.go` |
| `config set` | `configuration.set` | `text` |  | `supported` |  | `cmd_config.go` |
| `squad list` | `squads.list` | `json` |  | `supported` |  | `cmd_squad.go` |
| `squad get` | `squads.get` | `json` |  | `supported` |  | `cmd_squad.go` |
| `user list` | `users.list` | `json` |  | `supported` |  | `cmd_user.go` |
| `user get` | `users.get` | `json` |  | `supported` |  | `cmd_user.go` |
| `version` | `maintenance.version` | `json` |  | `supported` |  | `cmd_version.go` |
| `update` | `maintenance.update` | `text` |  | `supported` |  | `cmd_update.go` |
| `issue deprioritize` | `issues.deprioritize` | `text` |  | `supported` |  | `cmd_issue.go` |
| `auth whoami` | `` | `text` |  | `unsupported` | Deprecated upstream, removed from command tree | `` |

Notes:

- `auth login` is intentionally documented as `text` output mode. The SDK now treats `auth.login(token)` as a text-backed action result rather than inventing a JSON decode contract.
- `auth whoami` is kept as an explicit unsupported row so the manifest remains a complete inventory of pinned upstream discovery, including deprecated drift.
