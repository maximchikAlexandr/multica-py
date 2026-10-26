## ADDED Requirements

### Requirement: Property comparison filters use reviewed operators

Issue list property predicates SHALL support the reviewed comparison operators
through the existing ordered predicate and argv/query boundary while retaining
PR #101 equality, unset-sentinel, and list-value behavior.

#### Scenario: Ordered comparisons are valid

- **WHEN** a caller supplies reviewed comparison predicates for supported property types
- **THEN** the SDK preserves predicate order and emits each reviewed operator exactly once

#### Scenario: A comparison is ambiguous or unsupported

- **WHEN** an operator, property type, or value combination violates the approved contract
- **THEN** a stable validation error occurs before transport

### Requirement: Project workflow presence and writes are explicit

Project responses SHALL expose nullable `workflow_id`. Reviewed project and issue
writes SHALL preserve omitted, null, empty, and present workflow semantics and
authoritative status, assignment, move, and run-handoff results without exposing
workflow-management HTTP operations.

#### Scenario: Workflow identity is omitted or null

- **WHEN** a project response omits `workflow_id` or explicitly returns null
- **THEN** decoding preserves the reviewed legacy or nullable meaning without inventing an identifier

#### Scenario: A workflow-aware write succeeds

- **WHEN** a reviewed issue or project write returns remapped status, assignment, move, or run-handoff state
- **THEN** the SDK decodes the authoritative result without client-side workflow simulation or retry

#### Scenario: A workflow-aware write is rejected

- **WHEN** a reviewed workflow constraint is violated
- **THEN** the stable typed validation or upstream error is exposed and no unrelated field is changed

### Requirement: PR-conflict wakeup conditions are typed

Wakeup create and update SHALL support the reviewed PR-conflict condition within
the existing exactly-one condition model while retaining PR #101 diagnostic and
clearing behavior.

#### Scenario: A PR-conflict wakeup is constructed

- **WHEN** the caller selects the PR-conflict condition and no competing condition
- **THEN** eager and command forms produce identical reviewed argv and typed results

#### Scenario: Wakeup conditions conflict

- **WHEN** the PR-conflict condition is combined with another exclusive condition
- **THEN** validation fails before transport

### Requirement: Runtime sharing and privacy failures are explicit

Runtime definitions SHALL expose reviewed `shared_with` identities. Runtime
update/delete and agent create/update SHALL preserve explicit-grant authorization,
atomic privacy revocation, busy blockers, and structured conflict behavior through
the existing resources and sanitized exception hierarchy.

#### Scenario: Sharing identities are returned

- **WHEN** a runtime response contains `shared_with`
- **THEN** the SDK decodes the ordered reviewed identity shape without private fields

#### Scenario: Privacy revocation is blocked

- **WHEN** an atomic revoke has active reviewed blockers
- **THEN** the SDK raises the typed conflict with safe blocker context and leaves sharing unchanged

#### Scenario: An agent write lacks an explicit grant

- **WHEN** agent create or update selects a runtime the actor may not use
- **THEN** the SDK exposes the reviewed authorization failure without retrying or leaking backend details

### Requirement: Workspace allowlist failures remain sanitized

The target workspace create/update allowlist failure SHALL map through the
existing exception hierarchy with reviewed status, code, safe message, and safe
structured context only; PR #101 upload/network/server behavior SHALL remain retained.

#### Scenario: A reviewed allowlist failure occurs

- **WHEN** the CLI returns the target workspace allowlist conflict shape
- **THEN** the SDK raises the approved stable exception and redacts URL, hostname, path, credential, personal, and backend detail

#### Scenario: An unknown failure occurs

- **WHEN** the payload does not match an approved structured error
- **THEN** the PR #101 generic command failure remains in effect and no public type is inferred
