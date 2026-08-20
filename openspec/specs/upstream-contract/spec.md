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

### Requirement: Approved-operation realization starts with one bounded pilot
The approved SDK contract SHALL remain the only production generator input. The generator SHALL emit ordinary private Python argv builders and validators for exactly the homogeneous `squads.members.list`, `squads.members.add`, and `squads.members.remove` pilot family only when the pilot's stop/go decision succeeds. On a failed stop/go decision, the rollback SHALL be the normative terminal state: generation SHALL remain descriptor-only for this family, with no private argv builders, and `SquadMemberResource` eager and `*_command()` methods SHALL retain manual validation and argv construction. No other marker-only binding may be considered after a failed pilot. When the pilot succeeds, explicit typed `SquadMemberResource` eager and `*_command()` methods SHALL call the private generated functions and SHALL retain their public signatures, return types, eager delegation, validation timing, exact argv, decoding, options, and error behavior.

#### Scenario: Pilot builder emits exact list argv
- **WHEN** `SquadMemberResource.list_command(squad_id)` receives a valid identifier
- **THEN** the generated private builder validates before I/O and returns exactly `squad member list <squad_id>` for the existing decoded-page command path

#### Scenario: Pilot builder emits exact mutation argv
- **WHEN** add or remove receives valid squad and member identifiers
- **THEN** the generated private builder returns exactly `squad member add|remove <squad_id> <member_id>` for the existing action-command path

#### Scenario: Explicit public methods remain the API
- **WHEN** the generated module and resource are inspected
- **THEN** no runtime registry dispatch, reflection over `python_path`, dynamic public method, generated composite workflow, or second command namespace exists

### Requirement: Generated-operation expansion is evidence-gated
After the pilot, expansion to another marker-only family SHALL occur only when a committed stop/go report records all required evidence for the pilot: deterministic generation from `sdk-contract.json`, unchanged signatures/return types/validation timing/exact argv/results, table-driven canonical vectors, an independent expected-result guard, and a measured net deletion across production plus tests. A failed criterion SHALL stop expansion; it SHALL NOT be offset by projected future savings. Imperative, composite, temporary-file, spawn, pagination, and runtime-specific operations SHALL remain manual in this change.

#### Scenario: Pilot passes every go criterion
- **WHEN** the implementer compares the pilot baseline and final implementation
- **THEN** expansion may be proposed only if every criterion is recorded as passing with commands and line/concept counts

#### Scenario: Pilot fails any criterion
- **WHEN** generated realization adds runtime interpretation, changes a public/command contract, weakens independent verification, or does not produce net deletion
- **THEN** expansion stops and the normative terminal state is descriptor-only generation for the three `squads.members.*` descriptors plus manual validation and argv construction in `SquadMemberResource`; no private builders or resource delegation are retained

#### Scenario: Deferred families remain markers
- **WHEN** a marker-only binding lies outside an explicitly recorded passing expansion decision
- **THEN** its current handwritten resource implementation and generated descriptor remain unchanged

### Requirement: Multica v0.4.28 is the reviewed compatibility baseline

The approved SDK contract SHALL target tag `v0.4.28`, version `0.4.28`, release
ID `371790559`, and commit
`38c992ad0a757434fb51584fa34e3bc57d1b78e1`. Every retained or added source
reference SHALL point to that exact commit and a reviewed path, symbol, and line
range. Release evidence SHALL be collected from a verified `v0.4.28` CLI asset
whose name, operating system, architecture, SHA-256, and `version --output
json` bytes agree with release metadata. Evidence and transient projections
SHALL remain outside version control and SHALL NOT directly promote public SDK
behavior.

#### Scenario: Baseline metadata is exact
- **WHEN** `contracts/sdk-contract.json` and the generated runtime projection are inspected
- **THEN** they identify `v0.4.28` at commit `38c992ad0a757434fb51584fa34e3bc57d1b78e1`, release ID `371790559`, and no retained `v0.4.20` target or source commit remains except in historical/archive material

#### Scenario: Compatibility interval advances one patch
- **WHEN** default compatibility policy is generated from the approved target
- **THEN** its minimum is `0.4.28` and its exclusive maximum is `0.4.29`

#### Scenario: Promotion uses the complete workflow
- **WHEN** maintainers prepare the baseline upgrade
- **THEN** they run `collect` with pinned source and verified binary evidence, `validate --source-checkout` against the approved contract, deterministic `render`, and `check` in that order before offline release verification

#### Scenario: Unreleased main commands stay excluded
- **WHEN** upstream `main` contains commands or behavior absent from tag `v0.4.28`
- **THEN** those candidates do not enter the approved contract, generated runtime, public SDK, or canonical operation inventory through this change

### Requirement: v0.4.28 command tree is reconciled before promotion

The approved contract SHALL classify every tagged `v0.4.28` Cobra command as
retained, newly approved, or explicitly deferred with rationale. Newly approved
families SHALL include plugins, properties, issue properties, workspace MCP,
agent MCP, and skill refresh unless source proves a command is hidden,
interactive, or otherwise unsafe. Every exposed positional argument and flag
SHALL record its CLI binding, actual landing destination or local-control role,
presence policy, normalized constraint, response/adapter policy, exact source
references, and positive/negative test references. Name similarity SHALL NOT
prove mapping.

#### Scenario: Plugin operations are source-governed
- **WHEN** `plugins.list` and `plugins.install` are inspected
- **THEN** list traces to `/api/workspaces/{id}/plugins/private` and install traces to the private install upload path, with human-local guards recorded from `requireHumanLocalCommand`

#### Scenario: Property actor types are source-governed
- **WHEN** `properties.create` and `issues.properties.set` are inspected
- **THEN** `actor` / `multi_actor` types, option rejection, and `--value` encoding are traced through `cmd_property.go` rather than inferred from flag names

#### Scenario: MCP config channels are source-governed
- **WHEN** `workspaces.mcp.add` is inspected
- **THEN** exactly-one config input among inline JSON, file, and stdin is recorded from `resolveMcpJSONObject`, and list decoding cites the write-only public fields

#### Scenario: Deferred commands are explicit
- **WHEN** a tagged command is not approved
- **THEN** contract compatibility metadata names the command and the deferral rationale, and generated public SDK behavior does not include it

#### Scenario: Retained command paths exist in the pinned tree
- **WHEN** every approved operation command path is compared with the tagged Cobra tree
- **THEN** the exact leaf exists or the operation is remapped/removed; canonical fixtures cannot approve `auth login`, `config get`, `issue deprioritize`, or `workspace watch|unwatch` when those leaves are absent

#### Scenario: Destination mappings follow CLI preprocessing
- **WHEN** a flag or stdin/file channel is transformed before the API call
- **THEN** traceability records the transformed local-control or request-body destination, including file contents rather than falsely recording the path as the JSON value
