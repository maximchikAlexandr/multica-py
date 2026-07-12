# Model Source Map

This table records the current public Python model surface and the pinned upstream command/source file that owns the JSON shape. It is the field-provenance checklist for Spec 001.

Primary upstream source directories:

- Command registration and presentation: [`server/cmd/multica`](https://github.com/multica-ai/multica/tree/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica)
- CLI HTTP client and transport structs: [`server/internal/cli`](https://github.com/multica-ai/multica/tree/48b8dbf43971e5ea974bf827220cd212a1240c72/server/internal/cli)
- Root/global flags: [`server/cmd/multica/main.go`](https://github.com/multica-ai/multica/blob/48b8dbf43971e5ea974bf827220cd212a1240c72/server/cmd/multica/main.go)

Rules:

1. Prefer explicit Go structs with `json` tags.
2. If a command builds an anonymous JSON object/map, reproduce exactly that stable object as a dedicated Python model.
3. Never model table-only columns as API fields unless the JSON branch contains them.
4. Preserve optionality from pointers/omitempty and actual response behavior.
5. Convert RFC3339 timestamps to aware `datetime` only when source guarantees RFC3339; otherwise retain `str` with a named alias.
6. Internal wire helpers in `src/multica_py/_internal/wire_models.py` are not public models and therefore do not appear in this table.

| Python model | Python file | Primary command evidence | Upstream source file(s) | Notes |
|---|---|---|---|---|
| `Workspace` | `src/multica_py/models/workspaces.py` | `workspace list`, `workspace get` | `cmd_workspace.go` | Public list/get payload |
| `WorkspaceMember` | `src/multica_py/models/workspaces.py` | `workspace members` | `cmd_workspace.go` | Member listing payload |
| `Project` | `src/multica_py/models/projects.py` | `project list`, `project get`, `project create`, `project update`, `project set-status` | `cmd_project.go` | Project response model |
| `ProjectCreateRequest` | `src/multica_py/models/projects.py` | `project create` | `cmd_project.go` | Request flags only |
| `ProjectUpdateRequest` | `src/multica_py/models/projects.py` | `project update` | `cmd_project.go` | Request flags only |
| `Label` | `src/multica_py/models/labels.py` | `label list`, `label get`, `label create`, `label update` | `cmd_label.go` | Label JSON payload |
| `Agent` | `src/multica_py/models/agents.py` | `agent list`, `agent get`, `agent create`, `agent update` | `cmd_agent.go` | Agent response model |
| `AgentCreateRequest` | `src/multica_py/models/agents.py` | `agent create` | `cmd_agent.go` | Request flags only |
| `AgentUpdateRequest` | `src/multica_py/models/agents.py` | `agent update` | `cmd_agent.go` | Request flags only |
| `AgentTask` | `src/multica_py/models/agents.py` | `agent tasks` | `cmd_agent.go` | Task listing payload |
| `Skill` | `src/multica_py/models/skills.py` | `skill list`, `skill get`, `skill create`, `skill update`, `skill import` | `cmd_skill.go` | Skill response payload |
| `SkillFile` | `src/multica_py/models/skills.py` | `skill file list`, `skill file upsert` | `cmd_skill.go` | Nested skill file payload |
| `SkillCreateRequest` | `src/multica_py/models/skills.py` | `skill create` | `cmd_skill.go` | Request flags only |
| `SkillUpdateRequest` | `src/multica_py/models/skills.py` | `skill update` | `cmd_skill.go` | Request flags only |
| `Autopilot` | `src/multica_py/models/autopilots.py` | `autopilot list`, `autopilot get`, `autopilot create`, `autopilot update` | `cmd_autopilot.go` | Autopilot response payload |
| `AutopilotRun` | `src/multica_py/models/autopilots.py` | `autopilot run`, `autopilot history`, `autopilot run get` | `cmd_autopilot.go` | Run/history payload |
| `AutopilotTrigger` | `src/multica_py/models/autopilots.py` | `autopilot trigger list`, `autopilot trigger create` | `cmd_autopilot.go` | Public immutable trigger projection |
| `TriggerConfigItem` | `src/multica_py/models/autopilots.py` | `autopilot trigger list`, `autopilot trigger create` | `cmd_autopilot.go` | Public immutable config item |
| `Page[T]` | `src/multica_py/models/common.py` | `issue comment list`, `issue metadata list`, any cursor-bearing public result | `cmd_issue.go`, `cmd_issue_metadata.go` | Shared paginated public wrapper |
| `ActionResult` | `src/multica_py/models/common.py` | structured action responses where upstream emits success/message | command-specific | Shared action result wrapper |
| `IssueSummary` | `src/multica_py/models/issues.py` | `issue list`, `issue search` | `cmd_issue.go` | List/search row payload |
| `Issue` | `src/multica_py/models/issues.py` | `issue get`, `issue create`, `issue update`, `issue assign`, `issue set-status`, `issue reorder` | `cmd_issue.go` | Public immutable normalized issue projection |
| `IssueAssignee` | `src/multica_py/models/issues.py` | `issue get`, `issue create`, `issue update`, `issue assign` | `cmd_issue.go` | Nested issue assignee |
| `LinkedPullRequest` | `src/multica_py/models/issues.py` | `issue pull-requests`, `issue get` | `cmd_issue.go` | Nested PR payload |
| `IssueChildStageGroup` | `src/multica_py/models/issues.py` | `issue children`, `issue get` | `cmd_issue.go` | Nested children payload |
| `IssueMetadataItem` | `src/multica_py/models/issues.py` | `issue get`, `issue create`, `issue update` | `cmd_issue.go` | Public immutable metadata pair derived from wire map |
| `IssueListFilter` | `src/multica_py/models/issues.py` | `issue list` | `cmd_issue.go` | Request flags only |
| `InlineDescription` | `src/multica_py/models/issues.py` | `issue create` | `cmd_issue.go` | Request variant |
| `FileDescription` | `src/multica_py/models/issues.py` | `issue create` | `cmd_issue.go` | Request variant |
| `StdinDescription` | `src/multica_py/models/issues.py` | `issue create` | `cmd_issue.go` | Request variant |
| `NoDescription` | `src/multica_py/models/issues.py` | `issue create` | `cmd_issue.go` | Request variant |
| `IssueCreateRequest` | `src/multica_py/models/issues.py` | `issue create` | `cmd_issue.go` | Request flags only |
| `IssueUpdateRequest` | `src/multica_py/models/issues.py` | `issue update` | `cmd_issue.go` | Request flags only |
| `IssueReorderRequest` | `src/multica_py/models/issues.py` | `issue reorder` | `cmd_issue.go` | Request flags only |
| `IssueAssignmentRequest` | `src/multica_py/models/issues.py` | `issue assign` | `cmd_issue.go` | Request flags only |
| `Comment` | `src/multica_py/models/issue_activity.py` | `issue comment list`, `issue comment add`, `issue comment reply` | `cmd_issue.go` | Comment payload |
| `CommentThread` | `src/multica_py/models/issue_activity.py` | `issue comment list --recent` | `cmd_issue.go` | Recent-thread listing payload |
| `CommentListFlatRequest` | `src/multica_py/models/issue_activity.py` | `issue comment list` | `cmd_issue.go` | Flat comment listing request |
| `CommentListThreadRequest` | `src/multica_py/models/issue_activity.py` | `issue comment list --thread-id ...` | `cmd_issue.go` | Thread-scoped comment listing request |
| `CommentListRecentRequest` | `src/multica_py/models/issue_activity.py` | `issue comment list --recent` | `cmd_issue.go` | Recent-thread listing request |
| `Subscriber` | `src/multica_py/models/issue_activity.py` | `issue subscriber list`, `issue subscriber add` | `cmd_issue.go` | Subscriber payload |
| `MetadataEntry` | `src/multica_py/models/issue_activity.py` | `issue metadata list`, `issue metadata get`, `issue metadata set` | `cmd_issue_metadata.go` | Metadata response payload |
| `MetadataPredicate` | `src/multica_py/models/issue_activity.py` | repeated metadata filter clauses on `issue metadata list` | `cmd_issue_metadata.go` | Typed metadata filter clause |
| `MetadataListRequest` | `src/multica_py/models/issue_activity.py` | `issue metadata list` | `cmd_issue_metadata.go` | Predicate/cursor/limit request |
| `MetadataSetRequest` | `src/multica_py/models/issue_activity.py` | `issue metadata set` | `cmd_issue_metadata.go` | Typed metadata set request |
| `TaskRun` | `src/multica_py/models/issue_activity.py` | `issue runs` | `cmd_issue.go` | Run list payload |
| `RunMessage` | `src/multica_py/models/issue_activity.py` | `issue run-messages` | `cmd_issue.go` | Run message payload |
| `IssueUsage` | `src/multica_py/models/issue_activity.py` | `issue usage` | `cmd_issue.go` | Usage payload |
| `Repository` | `src/multica_py/models/system.py` | `repo list`, `repo get` | `cmd_repo.go` | Repository payload |
| `RepositoryCheckoutResult` | `src/multica_py/models/system.py` | `repo checkout` | `cmd_repo.go` | Checkout result payload |
| `RuntimeDefinition` | `src/multica_py/models/system.py` | `runtime list`, `runtime get` | `cmd_runtime.go` | Runtime payload |
| `AttachmentResult` | `src/multica_py/models/system.py` | `attachment list`, `attachment upload` | `cmd_attachment.go` | Attachment payload |
| `DaemonStatus` | `src/multica_py/models/system.py` | `daemon status` | `cmd_daemon.go` | Daemon state payload |
| `DaemonDiskUsageEntry` | `src/multica_py/models/system.py` | `daemon disk-usage` | `cmd_daemon.go` | Disk usage payload |
| `AuthenticationStatus` | `src/multica_py/models/system.py` | `auth status`, `auth logout` | `cmd_auth.go` | `auth login` is text-backed and intentionally excluded |
| `User` | `src/multica_py/models/system.py` | `user list`, `user get` | `cmd_user.go` | User payload |
| `Squad` | `src/multica_py/models/system.py` | `squad list`, `squad get` | `cmd_squad.go` | Squad payload |
| `MaintenanceVersion` | `src/multica_py/models/system.py` | `version` | `cmd_version.go` | Version payload |

Coverage notes:

- Public request models appear here because they are part of the SDK’s typed contract even when the upstream source expresses them as flag groups rather than JSON output structs.
- `auth login` is explicitly absent from `AuthenticationStatus` provenance because the pinned manifest marks it as `text`, not `json`.
