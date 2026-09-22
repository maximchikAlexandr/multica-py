## ADDED Requirements

### Requirement: Task-run projections expose optional wakeup correlation
`TaskRun` SHALL expose `wakeup_id: str | None`, and the existing `AgentTask`
projection returned by `agents.tasks` SHALL expose the same optional field. The
task-run wire decoder SHALL accept a non-null string when present and SHALL
produce `None` when the field is omitted by ordinary or legacy rows. The value
SHALL remain an open identifier, SHALL survive entity/model serialization and
both `agents.tasks` (`AgentTask`) and `issues.runs` (`TaskRun`) decoding, and
SHALL NOT imply that wakeup CRUD is supported. `AgentTask.wakeup_id` is the
same reviewed upstream response field projected through the existing
`AgentTask` model, not a new operation or relation.

#### Scenario: Wakeup-created task projections preserve their identifier
- **WHEN** an `agents.tasks` or `issues.runs` response contains a string `wakeup_id`
- **THEN** the decoded `AgentTask.wakeup_id` or `TaskRun.wakeup_id` equals that exact string and existing task fields remain unchanged

#### Scenario: Ordinary and legacy task projections omit the identifier
- **WHEN** an `agents.tasks` or `issues.runs` response omits `wakeup_id`
- **THEN** decoding succeeds with the corresponding `AgentTask.wakeup_id` or `TaskRun.wakeup_id` set to `None` and serialization preserves the established omission behavior

#### Scenario: Invalid wakeup identifier fails typed decoding on both projections
- **WHEN** an `agents.tasks` or `issues.runs` response contains a non-string non-null `wakeup_id`
- **THEN** the existing protocol error boundary rejects the malformed response without coercion

### Requirement: Run messages expose optional call correlation
`RunMessage` SHALL expose `call_id: str | None`. The run-message wire decoder
SHALL accept a non-null string when present and SHALL produce `None` when the
field is omitted by legacy rows. The field SHALL remain open, SHALL preserve
message ordering by `seq`, and SHALL NOT alter the existing tri-state
`output_truncated`, timestamp, content, input, output, or error semantics.

#### Scenario: Correlated message preserves its call identifier
- **WHEN** an `issues.run_messages` row contains a string `call_id`
- **THEN** the decoded `RunMessage.call_id` equals that exact string and all existing fields retain their values

#### Scenario: Legacy message omits call correlation
- **WHEN** an `issues.run_messages` row omits `call_id`
- **THEN** decoding succeeds with `RunMessage.call_id is None` and sequence ordering is unchanged

#### Scenario: Invalid call identifier fails typed decoding
- **WHEN** a run-message row contains a non-string non-null `call_id`
- **THEN** the existing protocol error boundary rejects the malformed response without coercion

### Requirement: Optional correlation fields use existing model boundaries
The implementation SHALL extend the existing `_TaskRunWire`, task-run adapter,
`TaskRun`, run-message wire model/adapter, and `RunMessage` types. It SHALL NOT
introduce a new enum, wrapper, relation, lazy loader, transport path, or
dependency for either identifier.

#### Scenario: Public model inventory changes only by two upstream fields
- **WHEN** public symbols, signatures, resources, and models are compared before and after the upgrade
- **THEN** the only response-surface additions are the shared `wakeup_id` field on existing `TaskRun`/`AgentTask` projections and `RunMessage.call_id`, while operation and resource inventories remain unchanged
