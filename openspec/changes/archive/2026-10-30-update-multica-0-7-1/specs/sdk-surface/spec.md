## ADDED Requirements

### Requirement: Agent custom arguments preserve provider-owned validation
Agent create and update SHALL retain the existing ordered `custom_args` input and open tuple projection while preserving target standard-error behavior for provider-reserved values.

#### Scenario: Allowed custom arguments round-trip
- **WHEN** create or update receives an ordered tuple of provider-allowed argument strings
- **THEN** the SDK SHALL emit the reviewed JSON-body mapping and decode the returned order unchanged

#### Scenario: Provider-reserved value is rejected authoritatively
- **WHEN** the pinned target rejects a custom argument reserved by the selected provider
- **THEN** the SDK SHALL raise the existing standard typed command error with the sanitized status and payload fields

#### Scenario: Runtime changes retain existing arguments
- **WHEN** an agent runtime changes and `custom_args` is omitted
- **THEN** the SDK SHALL omit the field and the returned agent SHALL retain the upstream arguments

#### Scenario: Omitted and empty arguments remain distinct
- **WHEN** `custom_args` is omitted or explicitly supplied as an empty tuple
- **THEN** omission SHALL produce no body member while the explicit empty tuple SHALL produce an empty array

### Requirement: Issue boundary and assignment corrections remain on existing methods
The existing issue search and update methods SHALL expose the pinned target corrections without adding version-specific wrappers.

#### Scenario: Out-of-range integer-looking search is text
- **WHEN** issue search receives a decimal query outside signed int4 range
- **THEN** the SDK SHALL pass the query as text and SHALL decode the normal issue page rather than failing integer conversion

#### Scenario: Workflow resolution preserves assignee
- **WHEN** an issue update invokes workflow resolution and the target response retains the current assignee
- **THEN** the decoded issue SHALL preserve that assignee identity and SHALL NOT replace it with null or a workflow actor

### Requirement: Concurrent project-resource partial updates do not lose unrelated fields
The existing project resource update operation SHALL preserve omitted fields when concurrent partial updates modify distinct attributes.

#### Scenario: Independent partial updates converge
- **WHEN** two updates derived from the same initial project resource modify distinct supported fields and the target accepts both
- **THEN** the final decoded resource SHALL contain both changes and all untouched fields

#### Scenario: Explicit clear remains distinct from omission
- **WHEN** a nullable resource field is explicitly cleared while another field is omitted
- **THEN** the SDK SHALL emit null only for the clear and SHALL omit the unrelated field

### Requirement: Skill bundles are portable and atomic through existing operations
Skill import and refresh SHALL keep the existing public methods and success models while enforcing portable relative paths, skipping binary content, and preserving the previous complete bundle when target acquisition or validation fails.

#### Scenario: Complete portable bundle succeeds
- **WHEN** a remote bundle contains valid portable relative text-file paths and supported content within limits
- **THEN** import or refresh SHALL expose the complete new bundle with no partial old/new mix

#### Scenario: Unsafe path is rejected
- **WHEN** a bundle contains an absolute path, traversal segment, platform-specific escape, or otherwise non-portable member
- **THEN** the SDK SHALL surface the target standard error and SHALL preserve the prior bundle

#### Scenario: Binary members are skipped
- **WHEN** a bundle contains valid text members and detected binary members
- **THEN** the resulting bundle SHALL contain the valid text members and SHALL omit binary payloads without exposing binary data as text

#### Scenario: Remote failure classes remain typed
- **WHEN** acquisition fails with target status 400, 413, 502, 503, or 504
- **THEN** the SDK SHALL preserve the existing typed standard-error boundary and sanitized response details for that status

#### Scenario: Refresh failure preserves prior bundle
- **WHEN** any remote, size, path, decode, or validation failure occurs after a prior bundle exists
- **THEN** the previously committed bundle SHALL remain complete and readable

### Requirement: Process-cleanup task outcomes remain forward-compatible
Task projections SHALL cover the known `0.7.1` process-cleanup outcomes while keeping `failure_reason` and `result` open to future string and mapping values.

#### Scenario: Known cleanup outcome decodes
- **WHEN** issue-run or agent-task history returns a reviewed process-cleanup result and failure reason
- **THEN** both response paths SHALL preserve the exact known values

#### Scenario: Unknown future cleanup outcome decodes
- **WHEN** a later compatible CLI returns a previously unseen cleanup result member or failure-reason string with valid wire types
- **THEN** the SDK SHALL preserve that value without closed-enum rejection

#### Scenario: Invalid wire shape still fails
- **WHEN** `failure_reason` or `result` uses a wire type outside the existing open contract
- **THEN** typed decoding SHALL fail with the existing output-shape error
