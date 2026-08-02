## Purpose

Define how reviewed upstream CLI evidence becomes deterministic public SDK
behavior.
## Requirements
### Requirement: Pinned source authority
The approved contract MUST cite full pinned source commits and locations, while extraction records only declared declarative facts.
#### Scenario: Unknown patterns require review
- **WHEN** extraction sees an unknown pattern
- **THEN** it emits a review item and changes no approved behavior.
<!-- Source IDs: 001:FR-032A–FR-032G,002:FR-001,FR-002,FR-027 -->

### Requirement: Verified evidence
Evidence collection MUST record verified binary identity, release identity, ordered declarative facts, and review items outside version control.
#### Scenario: Collection records verified evidence
- **WHEN** collection succeeds
- **THEN** its two files satisfy the schemas in `generation.md`.
<!-- Source IDs: 002:FR-003,FR-004,FR-012,FR-023,FR-032 -->

### Requirement: Reviewed mapping semantics
Every approved mapping MUST state source evidence, destination, five-state presence, enum policy, and normalized constraints with positive and negative evidence.
#### Scenario: Mappings state reviewed semantics
- **WHEN** a mapping is incomplete or unresolved
- **THEN** validation fails.
<!-- Source IDs: 002:FR-028,007:FR-009,FR-010 -->

### Requirement: Deterministic generation
The approved contract MUST be the only generator input and MUST render one
committed runtime module plus deterministic transient projections. Bound
entities, operation identifiers, loader closures, response adapters, validators,
and compatibility metadata MUST NOT be generated from evidence, heuristic
suggestions, or upgrade bundles directly.

#### Scenario: Rendering is deterministic
- **WHEN** rendered twice from the same approved contract
- **THEN** all relative paths and bytes are identical

#### Scenario: Candidate evidence cannot promote relations
- **WHEN** evidence contains an operation or relation absent from the approved contract
- **THEN** public generated behavior remains unchanged

### Requirement: Generated compatibility
The generated runtime module MUST provide the tested CLI interval from the approved target version.
#### Scenario: Compatibility uses the generated interval
- **WHEN** a client reads default policy
- **THEN** it uses generated minimum and exclusive next-patch maximum versions.
<!-- Source IDs: 002:FR-025,FR-033 -->

### Requirement: Git promotion
A reviewed Git merge changing the approved contract and runtime projection MUST be the only promotion action.
#### Scenario: Git review promotes the contract
- **WHEN** a PR is merged
- **THEN** no candidate, supported, observer, or journal state is written.
<!-- Source IDs: 002:FR-030,007:FR-011 -->

### Requirement: D15–D17 public-symbol integrity
The approved contract MUST define immutable public/wire schemas, cardinality,
presence semantics, validators, command mappings, and exact vectors for
profile, repository, and runtime operations. Validation MUST resolve every
approved `public_symbol`, normalize and compare its signature, and require
exactly one canonical vector for every approved operation. Repository checkout
MUST be recorded as daemon-only removal, not as a transport-compatible
operation. Source and binary evidence remain review-only and MUST NOT generate
public behaviour without this approval.

#### Scenario: Contract cannot certify a missing SDK method
- **WHEN** an approved D15–D17 public symbol is absent, has a different
  signature, or lacks one canonical vector
- **THEN** the contract integrity gate fails before release verification

### Requirement: Complete relation operation governance
Every operation used by the 33-relation matrix MUST be approved in
`contracts/sdk-contract.json` with pinned source references, exact input
destination mappings, five-state presence semantics, response envelope/wire
adapter, pagination strategy, compatibility decision, and positive/negative
test vectors before a private relation loader may call it.

#### Scenario: Ungoverned operation blocks relation generation
- **WHEN** a relation references an absent or unresolved operation
- **THEN** strict contract validation fails and no public relation behavior is generated

#### Scenario: Operation names do not prove mappings
- **WHEN** a relation parameter name resembles an upstream flag or field
- **THEN** approval still requires source tracing through `RunE` and helpers to its actual path, query, body, header, multipart, or process destination

### Requirement: Nineteen drift areas are reconciled first
The approved contract MUST explicitly reconcile every drift area identified by
issue #14 against current main and pinned CLI `0.4.9` before related lazy
surfaces are enabled.

#### Scenario: Drift audit is complete
- **WHEN** phase 0 is accepted
- **THEN** closed IDs D01 through D19 from `design.md` each appear in contract compatibility metadata and have every named positive/negative test reference

#### Scenario: Newly discovered drift does not expand D19
- **WHEN** pinned-source review discovers behavior not represented by D01 through D19
- **THEN** implementation stops for a spec amendment or follow-up change rather than silently absorbing it into this phase gate

#### Scenario: Unsupported method is intentionally changed
- **WHEN** pinned source has no compatible operation for a legacy public method
- **THEN** the contract records removal or replacement with rationale and migration instead of fabricating argv compatibility

### Requirement: Relation loaders use governed resource services
Private relation loader closures MUST call only typed resource-service methods
whose operation IDs and traversal behavior are fixed by the normative 33-row
inventory and approved contract. Loader closures MUST NOT contain raw argv,
wire decoders, strategy objects, or direct transport calls.

#### Scenario: Loader remains semantic
- **WHEN** relation loader closures are inspected
- **THEN** exact CLI command knowledge exists only in the approved/generated resource layer and no runtime descriptor registry exists

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
