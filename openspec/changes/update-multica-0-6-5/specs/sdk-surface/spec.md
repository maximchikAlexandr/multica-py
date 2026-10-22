## ADDED Requirements

### Requirement: Multi-value properties preserve typed presence and ordering
Existing property definition and value models SHALL accept reviewed
`multi_text` and `multi_url` values as immutable ordered string tuples while
retaining the open upstream property-type string. Issue property writes SHALL
accept a legacy scalar string or an immutable string tuple; tuple input SHALL be
encoded as one compact JSON array. The SDK MUST distinguish omission, null,
empty tuple, order, duplicates, commas inside values, and malformed/non-string
members without adding a recursive JSON value type.

#### Scenario: Ordered values round-trip
- **WHEN** a write receives a tuple containing ordered, duplicate, and comma-containing strings and the CLI returns the corresponding array
- **THEN** one JSON-array property argument is emitted and decoding preserves the exact immutable sequence

#### Scenario: Invalid collection fails before transport
- **WHEN** a property tuple contains a non-string member or violates the reviewed URL validator
- **THEN** the named validator raises locally and no command, upload, or other I/O occurs

#### Scenario: Presence variants remain distinct
- **WHEN** fixtures contain omission, JSON null, an empty array, or a non-empty array
- **THEN** the decoder preserves the reviewed distinct projection for each variant

### Requirement: Projects expose workflow identity without a workflow client
The existing Project wire and bound entity SHALL expose
`workflow_id: str | None`, preserving named workflow UUID, explicit null, and
legacy omission. Existing issue create, status, update, and project-move
operations SHALL keep their public signatures and command plans while decoding
the server-owned workflow validation, status remap, assignment, and run-handoff
results atomically.

#### Scenario: Named and default workflows decode
- **WHEN** project responses contain a workflow UUID or null/omitted legacy value
- **THEN** the existing Project type exposes the UUID or `None` and retains binding, serialization, and partial-field behavior

#### Scenario: Workflow validation changes an issue
- **WHEN** an existing issue mutation succeeds under the destination project workflow
- **THEN** the SDK returns the authoritative status, assignee, and run-handoff projection without a second mutation, retry, or client-side remap

#### Scenario: Workflow conflict is atomic
- **WHEN** the CLI rejects an unavailable status or invalid workflow transition
- **THEN** the existing typed/redacted command error is raised and the SDK performs no retry or compensating write

### Requirement: Daemon status exposes compatible CLI commit identity
`DaemonStatus` SHALL expose `cli_commit: str | None`. A nonempty target commit
SHALL be preserved exactly; empty string, JSON null, and field omission from
compatible older output SHALL normalize to `None` without changing daemon-status
command construction.

#### Scenario: Full target commit decodes
- **WHEN** daemon status output contains `654b8ca954034f8181eb6bbb4fc298dede760156`
- **THEN** `cli_commit` preserves that exact value

#### Scenario: Legacy output remains compatible
- **WHEN** daemon status omits `cli_commit` or emits an empty or null value
- **THEN** `cli_commit is None` and all existing fields retain their previous decoding

### Requirement: Wakeup and self-hosted pull-request behavior stays server-owned
Existing wakeup create/update/check-in/read models SHALL preserve reviewed
diagnostics and clear stale `last_error` after a successful pass. Existing
`--until-pr` condition input SHALL work with supported self-hosted VCS references
without a GitHub-only SDK validator, secondary poll, or synthesized result.

#### Scenario: Successful pass clears stale diagnostics
- **WHEN** a wakeup previously reported `last_error` and a later check passes
- **THEN** the decoded authoritative wakeup state no longer exposes the stale error

#### Scenario: Self-hosted pull request condition succeeds
- **WHEN** the existing wakeup condition references a supported self-hosted pull request and the CLI reports a pass
- **THEN** the SDK returns the CLI result without provider-specific rewriting or an extra request

### Requirement: Runtime privacy conflicts retain atomic structured errors
Runtime privacy transitions and agent runtime binding locks SHALL use existing
runtime/agent operations and typed redacted command-error boundaries. Reviewed
structured 409, busy, and authorization details SHALL remain actionable and safe;
the SDK MUST NOT expose the HTTP-only confirm endpoint, retry, cascade, unbind,
cancel, pause, or partially repeat a failed mutation.

#### Scenario: Privacy transition is blocked
- **WHEN** a public-to-private transition is rejected with structured blocker context
- **THEN** the existing public error exposes safe blocker identity/count guidance and no automatic side effect is attempted

#### Scenario: Agent binding is locked
- **WHEN** an agent mutation is rejected as busy or unauthorized
- **THEN** the SDK surfaces one redacted typed failure with zero retry and preserves the authoritative binding state

### Requirement: Upload, network, and server errors preserve stable boundaries
Reviewed upload/network failures and stable server 500 messages SHALL map through
existing process exceptions, redaction, and partial-side-effect documentation.
The SDK MUST preserve safe actionable text and MUST NOT expose credentials,
private hostnames, backend stack traces, or retry a mutation automatically.

#### Scenario: Stable server failure is safe
- **WHEN** a reviewed command returns a stable redacted server error
- **THEN** the existing exception contains safe message, exit status, and command context without backend detail leakage

#### Scenario: Upload fails after an earlier effect
- **WHEN** a multipart or attachment step fails after a prior server mutation
- **THEN** the SDK reports the documented partial-side-effect boundary and performs no retry or rollback claim

### Requirement: Additive target behavior does not create unrelated APIs
The SDK SHALL add only approved fields, value shapes, adapters, and error
fixtures required by the `0.6.5` contract. It MUST NOT expose workflow-management
endpoints, runtime revoke-confirm HTTP endpoints, daemon autostart, daemon CA
payloads, or UI default-workflow status behavior as public operations.

#### Scenario: Public discovery remains governed
- **WHEN** resources, symbols, signatures, canonical cases, and approved bindings are compared
- **THEN** only approved additive behavior appears and every excluded surface remains undiscoverable
