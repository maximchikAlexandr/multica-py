## ADDED Requirements

### Requirement: Projects expose nullable workflow identity
Every decoded `Project` SHALL expose `workflow_id: str | None`. A 0.6.3 named workflow UUID SHALL be preserved exactly; JSON null and omission by a compatible older CLI SHALL normalize to `None`.

#### Scenario: Named workflow is preserved
- **WHEN** project list, get, create, or update output contains a workflow UUID
- **THEN** the bound project exposes the exact UUID and round-trips it through public serialization

#### Scenario: Default or legacy workflow normalizes to null
- **WHEN** project output contains `workflow_id: null` or omits the field
- **THEN** the bound project exposes `workflow_id is None`

### Requirement: Workflow-aware issue writes remain CLI-owned atomic operations
Issue create, status, update, and project-move methods SHALL emit their existing approved argv once and SHALL decode the final 0.6.3 issue response. The SDK MUST NOT duplicate server workflow rules, invent workflow-management calls, retry conflicts, or synthesize remapped status/assignee/run state.

#### Scenario: Valid write returns authoritative state
- **WHEN** a workflow-aware write succeeds
- **THEN** the returned issue preserves the server-selected status, project, assignee, and run-handoff fields exactly

#### Scenario: Invalid workflow status remains one failure
- **WHEN** the CLI rejects a create, status change, update, or project move because the requested status conflicts with the target workflow
- **THEN** the SDK surfaces the existing typed command failure after exactly one mutation attempt and performs no retry

#### Scenario: Project move remap is not simulated
- **WHEN** moving an issue causes 0.6.3 to remap status by workflow category
- **THEN** the SDK returns the emitted remapped status and does not compute a local mapping

#### Scenario: Handoff side effects are not repeated
- **WHEN** an accepted write changes assignee or run ownership as part of the server transaction
- **THEN** the SDK exposes the returned final state and issues no follow-up assignment, status, or run command

### Requirement: Partial project updates preserve presence semantics
Project update SHALL continue distinguishing omitted, null, and empty values according to existing `Unset` boundaries and SHALL not clear unrelated project fields when 0.6.3 applies a partial update.

#### Scenario: Omitted fields remain omitted
- **WHEN** a caller updates one project field
- **THEN** argv contains only that reviewed field and the response preserves unrelated values
