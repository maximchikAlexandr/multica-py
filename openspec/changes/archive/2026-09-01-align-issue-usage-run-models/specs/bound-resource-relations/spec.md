## ADDED Requirements

### Requirement: Issue run relations retain execution-location context
`Issue.runs` SHALL return bound `TaskRun` entities that retain reviewed execution-location and runtime context from the issue-runs response. Relation binding, message loading, issue context inheritance, immutability, and refresh behavior SHALL remain unchanged.

#### Scenario: Consumer identifies a run work directory
- **WHEN** `Issue.runs` loads a task-run row with `work_dir` and `relative_work_dir`
- **THEN** the bound `TaskRun` exposes both values and the caller can select the privacy-safe relative value without a follow-up raw CLI call

#### Scenario: Legacy run omits new context
- **WHEN** a supported legacy task-run row omits the added execution fields
- **THEN** the bound `TaskRun` remains usable, exposes documented optional defaults, and retains its issue/messages relations
