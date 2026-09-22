## ADDED Requirements

### Requirement: Task runs expose optional wakeup correlation
`TaskRun` SHALL expose `wakeup_id: str | None`. The task-run wire decoder SHALL
accept a non-null string when present and SHALL produce `None` when the field is
omitted by ordinary or legacy rows. The value SHALL remain an open identifier,
SHALL survive entity serialization and both `agents.tasks` and `issues.runs`
decoding, and SHALL NOT imply that wakeup CRUD is supported.

#### Scenario: Wakeup-created run preserves its identifier
- **WHEN** either supported task-run response contains a string `wakeup_id`
- **THEN** the decoded `TaskRun.wakeup_id` equals that exact string and existing task fields remain unchanged

#### Scenario: Ordinary and legacy runs omit the identifier
- **WHEN** either supported task-run response omits `wakeup_id`
- **THEN** decoding succeeds with `TaskRun.wakeup_id is None` and serialization preserves the established omission behavior

#### Scenario: Invalid wakeup identifier fails typed decoding
- **WHEN** a task-run response contains a non-string non-null `wakeup_id`
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

#### Scenario: Public model inventory changes only by two fields
- **WHEN** public symbols, signatures, resources, and models are compared before and after the upgrade
- **THEN** the only response-surface additions are `TaskRun.wakeup_id` and `RunMessage.call_id`, while operation and resource inventories remain unchanged
