## ADDED Requirements

### Requirement: Create-issue autopilot runs preserve corrected task settlement
The existing `AutopilotRun` projection SHALL preserve nullable `task_id` while accurately representing `0.7.1` create-issue task completion, blocked issue settlement, and failure/retry chains.

#### Scenario: Created issue task completes successfully
- **WHEN** a create-issue autopilot run produces a task and that task completes successfully
- **THEN** the decoded run SHALL retain the emitted `task_id`, terminal success state, and absence of a false failure reason

#### Scenario: Blocked issue does not falsely fail the run
- **WHEN** the created issue reaches `blocked` under the pinned target settlement rules
- **THEN** the autopilot run SHALL reflect the upstream terminal result without converting the issue state into an unrelated run failure

#### Scenario: Failure and retry remain linked
- **WHEN** a create-issue task fails and the upstream run retries through a successor task
- **THEN** decoded history SHALL preserve each emitted task identity, failure detail, and run ordering without collapsing the retry chain

#### Scenario: Legacy task identity remains nullable
- **WHEN** legacy or non-task autopilot run data omits `task_id` or emits null
- **THEN** `AutopilotRun.task_id` SHALL decode as `None` and no synthetic identity SHALL be created

#### Scenario: Malformed task identity fails typed decoding
- **WHEN** the target response emits a non-null `task_id` with an invalid wire type
- **THEN** the SDK SHALL raise the existing output-shape error rather than stringifying the value
