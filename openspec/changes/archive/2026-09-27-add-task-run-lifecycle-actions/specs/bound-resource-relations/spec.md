## MODIFIED Requirements

### Requirement: Entity continuation actions use root command plans
Bound `Issue`, `Project`, and `TaskRun` entities SHALL expose their specified refresh and mutation methods when their originating client is present. Each eager method SHALL delegate through an argument-identical `*_command()` method, bind fixed entity context without asking the caller to repeat an ID, and reuse the corresponding root resource plan, validation, `OperationOptions`, return type, and error behavior. Entities SHALL remain immutable: a successful refresh or mutation SHALL return a new value where the root operation returns one and SHALL NOT change the original wrapper.

#### Scenario: Bound Issue refreshes through get
- **WHEN** `issue.refresh_command()` is inspected and run
- **THEN** it previews and runs the same governed `issues.get(issue.id)` plan and returns a newly bound `Issue`

#### Scenario: Bound Issue mutates without repeated ID
- **WHEN** `issue.update(...)`, `issue.assign(...)`, `issue.unassign()`, `issue.set_status(...)`, or a move method is used
- **THEN** the bound ID is forwarded once to the root command method and all remaining arguments and options match the resource form

#### Scenario: Bound Project continues naturally
- **WHEN** `project.refresh()` or `project.update(...)` is used
- **THEN** the root project resource plan is reused and the returned `Project` remains bound to the same client scope

#### Scenario: Bound TaskRun refresh selects the exact run
- **WHEN** `task_run.refresh_command()` is inspected and run with bound client and issue context
- **THEN** it reuses `issues.runs_command(task_run.issue_id)`, selects only the row whose ID equals `task_run.id`, returns that newly bound snapshot, and leaves the original unchanged

#### Scenario: Missing refreshed run is a protocol failure
- **WHEN** a successful issue-runs response omits the bound task-run ID
- **THEN** refresh raises `ProtocolError` and SHALL NOT substitute another run or reinterpret the omission as a transport not-found failure

#### Scenario: Bound TaskRun cancel reuses the root action
- **WHEN** `task_run.cancel_command(options=options)` is inspected or run
- **THEN** it reuses `issues.cancel_task_command(task_run.id, issue_id=task_run.issue_id, options=options)` and returns the root `ActionResult[None]` without refreshing or mutating the snapshot

#### Scenario: Cancel preserves optional issue addressing
- **WHEN** a client-bound `TaskRun` without inherited issue context builds its cancellation command
- **THEN** the existing task-ID-only cancellation plan is used and no fabricated issue identifier is added

#### Scenario: Detached continuation fails before I/O
- **WHEN** a detached Issue, Project, or TaskRun invokes a continuation action
- **THEN** the existing typed detached-entity error is raised before command construction or transport

#### Scenario: TaskRun refresh requires issue context
- **WHEN** a client-bound `TaskRun` without an inherited issue ID invokes refresh or constructs its refresh command
- **THEN** the existing typed missing-relation-context error is raised before transport because issue runs cannot be addressed
