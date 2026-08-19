## ADDED Requirements

### Requirement: Bound task runs offer raw and semantic activity views
A bound `TaskRun` SHALL continue exposing cached snapshot access through `messages` and `messages_command()`, and SHALL additionally expose uncached incremental semantic consumption through `stream_events()`. Both views SHALL reuse `IssueResource.run_messages` with the task-run identifier and inherited issue identifier; streaming SHALL NOT mutate, seed, or invalidate the `messages` relation cache.

#### Scenario: Raw relation remains unchanged
- **WHEN** a consumer loads `TaskRun.messages` or runs `messages_command()`
- **THEN** one governed message snapshot is returned with the existing lazy relation cache semantics and no status polling begins

#### Scenario: Semantic stream is independent of raw cache
- **WHEN** `TaskRun.messages` has already been loaded and the consumer then starts `stream_events()`
- **THEN** streaming performs incremental governed reads from sequence zero and neither reuses stale cached messages nor changes the cached snapshot

#### Scenario: Stream preserves inherited addressing
- **WHEN** a task run obtained from `Issue.runs` starts streaming
- **THEN** every message read carries the task-run ID plus the parent issue ID and every status refresh reads the parent issue's runs

### Requirement: Autopilot run relation remains raw-only
`AutopilotRun.messages` SHALL continue using the governed raw run-message relation. This change SHALL NOT add semantic streaming to `AutopilotRun` because it does not provide the issue-run status refresh contract required for completion-aware termination.

#### Scenario: Autopilot messages do not imply completion streaming
- **WHEN** an `AutopilotRun` has task and issue context
- **THEN** its raw `messages` and `messages_command()` APIs continue to work and no `stream_events()` method is advertised

