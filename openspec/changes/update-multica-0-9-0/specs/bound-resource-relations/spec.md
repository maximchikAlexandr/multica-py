## ADDED Requirements

### Requirement: Subscriber provenance includes project inheritance
Issue subscriber projections SHALL represent direct and project-inherited subscriber rows using the reviewed open reason value `project` and the existing typed relation surface.

#### Scenario: Project subscriber is decoded
- **WHEN** an issue subscriber list contains a row inherited from the containing project
- **THEN** the SDK SHALL preserve the subscriber identity, open `project` reason, and pagination metadata without treating the row as directly added to the issue

#### Scenario: Older direct subscriber remains compatible
- **WHEN** an older server returns the existing direct subscriber shape without project provenance
- **THEN** the SDK SHALL decode the row using the approved compatibility default and preserve existing relation behavior

### Requirement: Authorization-safe relations do not infer hidden objects
Bound issue, project, task, requester, creator, and subscriber relations SHALL use only identifiers present in the approved response and SHALL preserve private-project omission and redaction.

#### Scenario: Omitted private relation has no loader
- **WHEN** an inaccessible private-project relation is omitted or redacted without an approved identifier
- **THEN** the SDK SHALL not synthesize an identifier, loader, permalink, or placeholder object

#### Scenario: Present relation uses governed resource service
- **WHEN** a permitted relation identifier is present
- **THEN** its lazy loader SHALL call the existing typed resource service governed by an approved operation and SHALL not embed raw argv or direct transport logic

### Requirement: Collection loading remains bounded
Retained relation pages SHALL preserve cursor and pagination behavior while accepting the additive `0.9.0` fields.

#### Scenario: Project-inherited rows paginate
- **WHEN** subscriber or related collection responses span multiple pages
- **THEN** the SDK SHALL follow only the approved cursor, stop at exhaustion, preserve row order, and avoid duplicate fetches caused by the new provenance field

#### Scenario: Malformed pagination fails
- **WHEN** the response has a malformed cursor or page envelope
- **THEN** the SDK SHALL raise the standard output-shape error rather than looping or returning a partial typed collection as complete
