## ADDED Requirements

### Requirement: TaskRun exposes only the minimal lifecycle action surface
The public bound `TaskRun` SHALL expose `refresh(*, options: OperationOptions | None = None) -> TaskRun`, `refresh_command(*, options: OperationOptions | None = None) -> Command[TaskRun]`, `cancel(*, options: OperationOptions | None = None) -> ActionResult[None]`, and `cancel_command(*, options: OperationOptions | None = None) -> Command[ActionResult[None]]`. The eager and command forms SHALL have identical operation parameters, SHALL use the standard per-operation options and typed exception behavior, and SHALL perform no transport I/O during command construction. This change SHALL NOT add a task handle, run lookup resource, wait/poll API, terminal-state helper, task creation/correlation API, or additional messages API.

#### Scenario: Refresh returns a new snapshot
- **WHEN** `run.refresh()` succeeds for a bound task run
- **THEN** it returns the exact current run as a newly bound immutable `TaskRun` and the original snapshot remains unchanged

#### Scenario: Refresh command is inspectable
- **WHEN** `run.refresh_command(options=options)` is constructed
- **THEN** it exposes the existing issue-runs command plan with the inherited issue ID and supplied options without executing transport

#### Scenario: Cancel returns the standard action result
- **WHEN** `run.cancel(options=options)` succeeds
- **THEN** it returns the unchanged `ActionResult[None]` from the existing task-cancellation operation and the original `TaskRun` remains unchanged

#### Scenario: Cancel command is inspectable
- **WHEN** `run.cancel_command()` is constructed for a run with inherited issue context
- **THEN** it exposes the existing `issue cancel-task <run-id> --issue <issue-id>` command plan without executing transport

#### Scenario: Lifecycle scope remains minimal
- **WHEN** the final public `TaskRun` surface is inspected
- **THEN** only the four lifecycle methods in this requirement are added and existing `Issue.runs`, `TaskRun.messages`, and `TaskRun.stream_events` behavior remains unchanged
