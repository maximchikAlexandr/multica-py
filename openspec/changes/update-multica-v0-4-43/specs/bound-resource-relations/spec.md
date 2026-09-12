## ADDED Requirements

### Requirement: Bound task activity preserves target additive fields
`Agent.tasks`, `Issue.runs`, `TaskRun.messages`, and
`AutopilotRun.messages` SHALL preserve the approved `0.4.43` task cancellation
actor and raw-message truncation state through their existing eager, command,
and lazy relation paths. Binding, parent addressing, cache ownership,
invalidation, pagination, and subprocess counts SHALL remain unchanged.

#### Scenario: Agent and issue task rows agree
- **WHEN** equivalent task-run rows containing `cancelled_by` are decoded through `Agent.tasks` and `Issue.runs`
- **THEN** both paths return the same immutable actor projection without an extra read

#### Scenario: Bound message paths preserve tri-state
- **WHEN** TaskRun or AutopilotRun message relations decode omitted, false, and true truncation values
- **THEN** each relation preserves `None`, `False`, and `True` respectively while retaining its current addressing and cache behavior

#### Scenario: Additive fields do not alter relation topology
- **WHEN** bound relation discovery and operation counts run after the target adaptation
- **THEN** the existing 37 relation IDs, loaders, eager/command pairs, and call counts remain exact
