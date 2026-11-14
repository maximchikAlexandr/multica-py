## ADDED Requirements

### Requirement: Retained 0.9.0 response additions are typed
The SDK SHALL adapt existing public projections for issue requester and list creator identity, project visibility and creator identity, task credits and redaction, attachment dimensions, comment resolution, runtime capacity and usage, user profile, workspace pinning, and project-inherited subscribers without adding unrelated top-level resources.

#### Scenario: Added field has complete presence coverage
- **WHEN** a retained response field is present, omitted by an older server, explicitly null where allowed, or malformed
- **THEN** the SDK SHALL respectively expose the typed value, apply the approved compatibility default, preserve approved null, or raise the standard output-shape error

#### Scenario: Open values remain forward compatible
- **WHEN** a retained response contains a syntactically valid future status, provider, reason, or visibility value governed as open
- **THEN** the SDK SHALL preserve that value without coercing it into a closed enum

### Requirement: Private-project semantics remain authorization safe
The SDK SHALL preserve the proven `0.9.0` 404, omission, and redaction behavior for inaccessible private projects and project-scoped records.

#### Scenario: Inaccessible direct read is not disclosed
- **WHEN** the CLI reports the reviewed not-found response for a private project the caller cannot access
- **THEN** the SDK SHALL raise the standard not-found command error without exposing project identity or membership details

#### Scenario: Inaccessible list member is omitted
- **WHEN** a list response omits an inaccessible private-project record
- **THEN** the SDK SHALL return the remaining typed page without manufacturing a redacted row

#### Scenario: Private fixture setup does not expand the SDK mutation surface
- **WHEN** protected verification needs a private project under pinned `0.9.0`
- **THEN** the administrator fixture channel SHALL create it outside the candidate SDK, while project create/update SHALL NOT gain visibility input under this change

### Requirement: Issue rerun is run targeted
The SDK SHALL remove the obsolete `issue rerun <issue-id>` mapping and provide explicit eager and command-preview operations for `issue rerun-task <run-id>` with reviewed resume and fresh behavior and a typed result.

#### Scenario: Existing run is resumed
- **WHEN** a caller requests resume for a valid run identifier
- **THEN** exact reviewed argv SHALL target that run, the operation SHALL decode the reviewed task result, and no issue identifier SHALL be substituted

#### Scenario: Fresh rerun is requested
- **WHEN** a caller requests fresh behavior for a valid run identifier
- **THEN** exact reviewed argv SHALL include only the approved fresh-mode flag and the result SHALL preserve the server-reported fresh state

#### Scenario: Obsolete issue-targeted call is not retained
- **WHEN** a caller follows migration documentation from the removed issue rerun method
- **THEN** the documentation SHALL direct the caller to obtain a run identifier and invoke the new operation without a compatibility alias that changes identifier meaning

### Requirement: Relationship mutations fail closed
Create and update operations that bind projects, parents, assignees, properties, attachments, or other relationships SHALL complete local dependency, conflict, and presence validation before invoking transport.

#### Scenario: Invalid relationship combination has no mutation
- **WHEN** required-together, exactly-one, conflict, identifier, or attachment prevalidation fails
- **THEN** the SDK SHALL raise before any CLI process, upload, or create/update mutation begins

#### Scenario: Inline attachment binding is atomic
- **WHEN** all files and relationship inputs validate and the CLI accepts the mutation
- **THEN** literal argv and file inputs SHALL bind to the returned typed object, while a failure SHALL not report partial success
