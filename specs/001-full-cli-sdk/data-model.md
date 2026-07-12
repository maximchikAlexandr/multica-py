# Data Model

## Configuration models

### `ClientConfig`

Immutable client settings: executable, server URL, workspace ID, profile, cwd, environment tuple, default timeout, compatibility policy, encoding.

### `CliVersion`

Fields: semantic version text, commit, build date, Go version, OS, architecture, raw output.

## Transport models

### `CommandSpec[T]`

Internal generic definition: argv tuple, stdin bytes, output mode, decoder, timeout, secret argument positions.

### `RawCommandResult`

Fields: argv with redacted values, exit code, stdout bytes, stderr bytes, duration.

### `TextResult`

Fields: text, stderr text, exit code.

### `ManagedProcess`

Lifecycle wrapper around a child process. It is not serializable and is never a msgspec model.

## Shared domain types

- `IssueStatus`: backlog, todo, in_progress, in_review, done, blocked, cancelled.
- `ProjectStatus`: planned, in_progress, paused, completed, cancelled.
- `Priority`: copied exactly from `validIssuePriorities` in the pinned source.
- `OutputMode`: json, table/text where source exposes it.
- `MetadataValue`: str | int | float | bool | None.
- `Unset`: explicit patch omission sentinel.
- `Page[T]`: tuple of items plus optional cursor fields where upstream exposes pagination.
- `ActionResult`: success flag/message only when upstream emits structured fields.

## Issue models

- `IssueSummary`
- `Issue`
- `IssueAssignee`
- `IssueChildStageGroup`
- `LinkedPullRequest`
- `IssueCreateRequest`
- `IssueUpdateRequest`
- `IssueListFilter`
- `IssueReorderRequest` as a tagged union of before/after/top/bottom
- `IssueAssignmentRequest` as member/agent/squad/unassign variants
- `Comment`
- `CommentThread`
- `CommentListRequest` as flat/thread/recent variants
- `Subscriber`
- `MetadataEntry`
- `TaskRun`
- `RunMessage`
- `IssueUsage`

Patch models distinguish omitted values from explicit clearing. A nullable field alone is insufficient.

## Other resource models

- Workspace, WorkspaceMember
- Project, ProjectCreateRequest, ProjectUpdateRequest
- Label
- Agent, AgentCreateRequest, AgentUpdateRequest, AgentTask
- Skill, SkillFile, SkillCreateRequest, SkillUpdateRequest
- Autopilot, AutopilotRun, AutopilotTrigger
- RuntimeDefinition
- DaemonStatus, DaemonDiskUsageEntry
- AuthenticationStatus
- RepositoryCheckoutResult
- AttachmentResult

Exact fields are copied from pinned Go JSON structs and stored in `contracts/model-source-map.md`; no field is inferred from table output alone.
