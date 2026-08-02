## ADDED Requirements

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

## MODIFIED Requirements

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
