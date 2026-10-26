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

### Requirement: Runtime sharing reads and authorization failures are CLI-backed

Runtime-definition results from reviewed CLI operations SHALL expose `visibility`
and ordered `shared_with` identities. Target-version runtime update SHALL retain
its `RuntimeUpdateResult` response. Agent create/update SHALL expose reviewed
authorization rejection through the existing sanitized exception hierarchy.
The SDK SHALL NOT expose runtime visibility, sharing, grant, or atomic-revocation
write methods or flags until a separately approved CLI operation exists.

#### Scenario: Sharing identities are returned

- **WHEN** runtime list or rename JSON contains `visibility` and `shared_with`
- **THEN** the SDK decodes the reviewed runtime-definition fields, preserves order, and exposes no private fields

#### Scenario: Runtime target-version update completes

- **WHEN** `runtimes.update` returns the reviewed target-version update result
- **THEN** the SDK decodes `RuntimeUpdateResult` and does not infer runtime-definition sharing fields

#### Scenario: An agent write lacks runtime access

- **WHEN** agent create or update selects a runtime the actor may not use
- **THEN** the SDK raises the reviewed authorization failure without retrying, managing grants, or leaking backend detail

#### Scenario: A caller seeks runtime access management

- **WHEN** public discovery and approved bindings are inspected for visibility, share, grant, or revoke writes
- **THEN** no such SDK symbol or flag exists and the server-only routes remain `not_sdk_surface`

#### Scenario: Runtime deletion is inspected as a substitute

- **WHEN** the runtime delete/cascade operation is compared with privacy revocation
- **THEN** it remains a separate destructive lifecycle operation and satisfies no sharing or revocation requirement

### Requirement: Workspace allowlist failures remain sanitized

The target workspace create/update allowlist failure SHALL map through the
existing exception hierarchy with reviewed status, code, and safe message only;
PR #101 upload/network/server behavior SHALL remain retained.

#### Scenario: A reviewed allowlist failure occurs

- **WHEN** the CLI returns the target workspace allowlist failure shape
- **THEN** the SDK raises the approved stable exception and exposes no URL, hostname, path, credential, personal, or backend detail

#### Scenario: An unknown failure occurs

- **WHEN** the payload does not match an approved structured error
- **THEN** the PR #101 generic command failure remains in effect and no public type is inferred
