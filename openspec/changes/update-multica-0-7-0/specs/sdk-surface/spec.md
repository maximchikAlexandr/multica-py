## ADDED Requirements

### Requirement: Array property values are typed and deterministic

Property definitions and issue property values SHALL support the reviewed
`multi_text` and `multi_url` types through the existing typed model and JSON
boundaries. Encoding and decoding SHALL preserve array order, duplicates,
explicit empty arrays, and the reviewed distinction between omission and null.

#### Scenario: An array property round-trips

- **WHEN** a caller supplies an ordered array containing duplicate valid values
- **THEN** the SDK emits the reviewed JSON-array form and decodes the same order and duplicates

#### Scenario: An invalid array value is supplied

- **WHEN** a value has the wrong container or element type, an invalid URL, or a disallowed null
- **THEN** the SDK raises the documented typed validation error before transport

### Requirement: Property comparison filters use reviewed operators

Issue list property predicates SHALL support the reviewed comparison operators
with deterministic ordered argv/query encoding and SHALL retain equality and
unset-sentinel compatibility.

#### Scenario: Ordered comparisons are valid

- **WHEN** a caller supplies reviewed comparison predicates for supported property types
- **THEN** the SDK preserves predicate order and emits each reviewed operator exactly once

#### Scenario: A comparison is ambiguous or unsupported

- **WHEN** an operator/type/value combination violates the approved contract
- **THEN** a stable validation error occurs before transport

### Requirement: Project workflow presence is explicit

Project responses SHALL expose nullable `workflow_id`, and project create/update
writes SHALL preserve omitted, null, empty, and present workflow semantics from
the approved mapping without turning workflow-management endpoints into SDK
operations.

#### Scenario: Workflow is omitted or null

- **WHEN** a project response omits `workflow_id` or explicitly returns null
- **THEN** decoding preserves the reviewed legacy/nullable meaning without inventing an identifier

#### Scenario: A workflow-aware write is invalid

- **WHEN** a project write violates a reviewed workflow constraint
- **THEN** validation or the typed upstream error is stable and no unrelated field is changed

### Requirement: Daemon status exposes CLI commit identity

Daemon status SHALL expose optional `cli_commit` from `0.7.0` while accepting
legacy responses that omit or empty the field.

#### Scenario: Target status includes a commit

- **WHEN** daemon status returns a valid CLI commit
- **THEN** the typed status model exposes it unchanged

#### Scenario: Legacy status omits the commit

- **WHEN** the field is absent or empty under the reviewed legacy policy
- **THEN** decoding succeeds with the documented optional value

### Requirement: Wakeup PR-conflict conditions and diagnostics are typed

Wakeup create and update SHALL support the reviewed PR-conflict condition within
the existing exactly-one condition model. Wakeup responses SHALL expose reviewed
diagnostics, including stale `last_error` clearing, without changing unrelated
condition or event semantics.

#### Scenario: A PR-conflict wakeup is constructed

- **WHEN** the caller selects the PR-conflict condition and no competing condition
- **THEN** eager and command forms produce identical reviewed argv and typed results

#### Scenario: Conditions conflict

- **WHEN** the PR-conflict condition is combined with another exclusive condition
- **THEN** validation fails before transport

#### Scenario: A stale diagnostic is cleared

- **WHEN** upstream returns the reviewed cleared diagnostic representation
- **THEN** the SDK distinguishes it from an omitted/unloaded diagnostic

### Requirement: Runtime sharing and privacy errors are explicit

Runtime definitions SHALL expose reviewed `shared_with` identities. Runtime
update/delete and agent create/update SHALL preserve explicit-grant authorization,
atomic privacy revocation, busy-blocker, and structured conflict behavior through
existing resource and exception boundaries.

#### Scenario: Sharing identities are returned

- **WHEN** a runtime response contains `shared_with`
- **THEN** the SDK decodes the ordered reviewed identity shape without exposing private fields

#### Scenario: Privacy revocation is blocked

- **WHEN** an atomic revoke has active reviewed blockers
- **THEN** the SDK raises the typed conflict with safe blocker context and leaves sharing unchanged

#### Scenario: An agent write lacks an explicit grant

- **WHEN** agent create or update selects a runtime the actor may not use
- **THEN** the SDK exposes the reviewed authorization failure without retrying or leaking backend details

### Requirement: Reviewed failures remain sanitized and stable

Upload/network failures, stable server failures, and self-host workspace allowlist
failures SHALL map to the current typed exception hierarchy with reviewed status,
code, safe message, and structured context only.

#### Scenario: A reviewed failure occurs

- **WHEN** the CLI returns a reviewed upload, network, server, or allowlist error
- **THEN** the SDK raises the corresponding stable exception and redacts private URL, hostname, path, credential, and backend detail

#### Scenario: An unknown error occurs

- **WHEN** the payload does not match an approved structured error
- **THEN** the current generic command failure remains in effect and no new public type is inferred
