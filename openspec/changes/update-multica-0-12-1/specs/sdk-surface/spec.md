## ADDED Requirements

### Requirement: Revision-aware issue, comment, and skill contracts are typed
Existing issue, comment, and skill operations SHALL expose target revision fields and optimistic-write inputs through existing domain models and methods, with omission distinct from explicit values and stale writes mapped to the centralized typed conflict.

#### Scenario: Issue description revision round-trips
- **WHEN** issue get, create, update, or description editing returns `description_revision`
- **THEN** the typed issue projection SHALL preserve the reviewed integer or null/omitted state exactly

#### Scenario: Stale issue description conflicts
- **WHEN** a description write supplies a stale reviewed revision
- **THEN** the SDK SHALL raise the typed 409 conflict and SHALL preserve the server's current issue state

#### Scenario: Comment idempotent replay returns one logical comment
- **WHEN** comment creation is repeated with the same approved idempotency identity
- **THEN** the SDK SHALL decode the same logical comment result and SHALL NOT represent a duplicate as a second successful comment

#### Scenario: Skill base revision is presence-sensitive
- **WHEN** skill mutation omits a base revision or supplies an explicit current or stale base revision
- **THEN** omission SHALL omit the target input, a current revision SHALL succeed and round-trip, and a stale revision SHALL raise the typed conflict

### Requirement: Project progress and activity remain typed and paginated
Approved project list/get and retained project operations SHALL decode the target progress, activity, archival, membership, and pagination fields identified by the response registry without exposing deferred project-management commands as SDK methods.

#### Scenario: Project progress decodes
- **WHEN** an approved project response includes progress counts or percentages
- **THEN** the typed project projection SHALL preserve every reviewed field, numeric boundary, and omission/nullability rule

#### Scenario: Pagination remains monotonic
- **WHEN** a retained project page supplies the target cursor or offset metadata
- **THEN** iteration SHALL preserve response order, stop at the reviewed terminal state, and reject a non-progressing continuation

#### Scenario: Deferred project commands stay absent
- **WHEN** project resource discovery runs
- **THEN** project member, overview, progress-command, workflow-management, archive, restore, and activity commands SHALL remain absent unless already represented by a retained approved read model

### Requirement: Workspace guest projections enforce target visibility
Workspace member and invitation models SHALL support target `guest` role and reviewed `project_ids` presence while preserving target caller-dependent redaction.

#### Scenario: Authorized non-guest sees guest project scope
- **WHEN** a non-guest caller lists a guest member and the target includes `project_ids`
- **THEN** the typed member SHALL preserve the ordered project identifiers

#### Scenario: Guest caller receives redacted membership
- **WHEN** a guest caller lists visible workspace members
- **THEN** the SDK SHALL decode the target-visible rows and SHALL NOT synthesize or expose redacted `project_ids`

#### Scenario: Older member payload remains compatible
- **WHEN** a supported older CLI returns a member without guest-specific fields
- **THEN** the existing typed member SHALL decode with the approved empty/absent projection

### Requirement: Configuration, daemon, runtime, and execution additions use existing models
Approved target additions for configuration limits, daemon log/start/stop controls, runtime/profile state, usage windows, autopilot run outcomes, attachment dimensions, and other retained operational responses SHALL extend existing models and operations without introducing version-specific resources.

#### Scenario: Added operational fields preserve presence
- **WHEN** a target response contains an approved added field
- **THEN** its existing domain model SHALL preserve the reviewed type, nullability, omission, and open-value policy

#### Scenario: Older payload omits new field
- **WHEN** a supported older CLI omits a target-only field
- **THEN** decoding SHALL use the approved absent/default projection and SHALL NOT fail or invent target state

#### Scenario: Unknown valid upstream value remains open
- **WHEN** a compatible CLI returns a previously unseen value in an upstream-owned open field
- **THEN** the SDK SHALL preserve the value without closed-enum rejection

### Requirement: Changed response adapters preserve pagination and error boundaries
Every changed response adapter SHALL preserve the approved success envelope, field types, nullability, omission, pagination, unknown-value, and standard-error behavior recorded in its response-registry row.

#### Scenario: Positive and omission cases decode
- **WHEN** a changed response uses each approved positive, omitted, explicit-null, empty, zero, or false representation
- **THEN** the typed projection SHALL distinguish those representations exactly as the contract specifies

#### Scenario: Malformed changed response fails closed
- **WHEN** a changed response violates an approved closed field type or required envelope
- **THEN** decoding SHALL raise the existing output-shape error without partial domain state

#### Scenario: Retained 400, 409, 413, and 499 behavior remains typed
- **WHEN** a governed target operation returns a reviewed validation, conflict, size, or client-cancellation failure
- **THEN** the SDK SHALL raise the existing sanitized typed error and preserve the approved status/payload fields
