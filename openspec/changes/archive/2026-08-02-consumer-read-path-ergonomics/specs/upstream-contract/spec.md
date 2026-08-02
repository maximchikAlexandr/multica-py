## ADDED Requirements

### Requirement: Consumer read mappings are contract-approved
The approved SDK contract SHALL govern the repeatable issue-list metadata
predicate supported by pinned Multica CLI `0.4.9`. Both scoped copies of the
`issues.list` operation SHALL contain the existing-schema mapping
`filter.metadata / repeat:--metadata / query:metadata`, with reviewed rationale,
source references, and test references. JSON scalar encoding, validation, and
response projection remain handwritten decoder/adapter policy because approved
contract schema v3 has no fields for those concerns. Evidence and heuristic
suggestions remain review-only inputs.

#### Scenario: Metadata predicate mapping is explicit
- **WHEN** the `issues.list` operation is validated
- **THEN** both scoped approved operation copies contain exactly `filter.metadata / repeat:--metadata / query:metadata`, while exact scalar encoding and validation are asserted by handwritten adapter tests

#### Scenario: Issue-list summary projection is explicit
- **WHEN** the reviewed `issues.list` rationale, sources, decoder, and tests are inspected
- **THEN** they trace upstream labels and metadata into `IssueSummary.label_names` and `IssueSummary.metadata_snapshot` without claiming a schema-v3 response-field mapping or promoting a list row to a full issue

#### Scenario: Workspace-member identities remain distinct
- **WHEN** the reviewed workspace-member decoder, source references, and tests are inspected
- **THEN** membership `id`, user `user_id`, and `email` are independently traced and the assignee-filter semantics of membership `id` are recorded without inventing unsupported contract-schema fields

#### Scenario: Issue-get attachments reuse the approved attachment shape
- **WHEN** the reviewed `issues.get` decoder, source references, and tests are inspected
- **THEN** its embedded attachment array maps to the existing `AttachmentResult` public projection with no new list command, attachment relation operation, or schema-v3 response-field extension

#### Scenario: Omitted attachments have an SDK normalization policy
- **WHEN** pinned upstream omits the optional attachments field after either an empty result or a best-effort read failure
- **THEN** handwritten decoder tests record SDK normalization to `()` and documentation records that consumers may retry rather than infer atomic completion

#### Scenario: No upstream change is required
- **WHEN** the change is reviewed for external dependencies
- **THEN** every approved behavior is supported by pinned CLI `0.4.9` source and response shapes and no Multica server or CLI patch is a prerequisite

#### Scenario: Evidence cannot directly promote the mapping
- **WHEN** source evidence or a generated suggestion contains any of these fields or mappings
- **THEN** production mapping generation remains blocked until the supported existing-schema mapping is present in `contracts/sdk-contract.json`; handwritten projections still require reviewed decoder tests
