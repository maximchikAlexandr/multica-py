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

### Requirement: Incremental run-message input is contract-approved
The approved `v0.4.28` `issues.run_messages` operation SHALL add `since: int = 0` to its eager and command signatures, map the value to the Cobra `--since <sequence>` integer flag and, for a positive value, its `since` query parameter, and require an exact non-boolean integer in the inclusive DB/server-safe range `0..2_147_483_647`. The canonical vector SHALL include `--since 0`; positive and negative vectors SHALL prove boundary mapping and pre-I/O rejection. Source references SHALL pin the tagged Cobra flag and `runIssueRunMessages` query construction, the user-authenticated handler's `strconv.Atoi` and subsequent `int32(sinceSeq)` query argument, and the server strict-greater-than sequence query. The SDK SHALL enforce the `int32` upper bound even on a 64-bit CLI host so the handler cast cannot wrap to an incorrect SQL cursor. Rendering zero is the deterministic SDK argv form; the tagged CLI omits the query parameter when zero and therefore requests full history.

#### Scenario: Zero cursor is explicit
- **WHEN** `run_messages(task_id, issue_id=issue_id, since=0)` executes
- **THEN** argv is exactly `issue run-messages <task-id> --issue <issue-id> --since 0 --output json` and the full ordered history is decoded

#### Scenario: Positive cursor requests only newer messages
- **WHEN** `since=42` is supplied
- **THEN** argv contains `--since 42` and pinned upstream returns only rows whose sequence is greater than 42 in ascending sequence order

#### Scenario: Maximum server-safe cursor is accepted
- **WHEN** `since=2_147_483_647` is supplied
- **THEN** argv contains `--since 2147483647` and the handler's `int32` query cursor preserves the requested value

#### Scenario: Invalid or overflowing cursor fails before transport
- **WHEN** `since` is negative, boolean, noninteger, or greater than `2_147_483_647` (including `2_147_483_648` on a 64-bit CLI host)
- **THEN** construction raises `TypeError` or `ValueError` before subprocess execution

### Requirement: Run-message response schema is source-governed
The approved contract SHALL replace the unsupported run-message response schema retained after the `v0.4.28` upgrade with the pinned tagged payload: required `task_id`, `seq`, and `type`; optional `issue_id`, `tool`, `content`, `input`, `output`, and `created_at`. It SHALL record `type` as an open string and structured `input` as recursive JSON. Source references SHALL trace the database row through `taskMessageToPayload`, `TaskMessagePayload`, and the user-authenticated task-message handler at commit `38c992ad0a757434fb51584fa34e3bc57d1b78e1`. The approved response SHALL NOT claim fields absent from upstream.

#### Scenario: Contract matches source payload
- **WHEN** contract integrity and source validation inspect `issues.run_messages`
- **THEN** every approved response field maps to the pinned handler payload and `id`, `run_id`, and `role` are absent

#### Scenario: Semantic events do not alter the transport contract
- **WHEN** event streaming converts a decoded `RunMessage`
- **THEN** the governed operation still returns raw messages and semantic classification remains handwritten SDK policy above the approved transport adapter

### Requirement: Issue activity contract records the reviewed compatibility window

The approved SDK contract SHALL distinguish the pinned `v0.4.28` source target from verified release binaries and SHALL retain the reviewed issue assignee, issue usage, and issue runs mappings from CLI `0.4.28` through `0.4.32`. It SHALL additionally record CLI `0.4.38` binary identity and version-command provenance for the compatibility preflight and schedule-trigger live lifecycle without claiming unreviewed `0.4.38` response fields for other operations. Generated default compatibility bounds SHALL come only from that approved contract, SHALL accept versions `0.4.28` through `0.4.38`, and SHALL use exclusive maximum `0.4.39`.

#### Scenario: Reviewed contract generates default bounds
- **WHEN** the approved contract is rendered
- **THEN** the generated compatibility projection accepts CLI versions `0.4.28` through `0.4.38` and rejects or warns at `0.4.39` according to policy, without using evidence files directly as generator input

#### Scenario: Binary and source provenance are not conflated
- **WHEN** CLI `0.4.38` is verified from release binary metadata and its exact version-command source is reviewed at commit `47dc75741cd03127d32f1b78d04c644ccf690e7f`
- **THEN** the contract retains catalog target `v0.4.28` for trigger mappings, retains the existing `0.4.32` reviewed response provenance, and records the `0.4.38` binary/version-command evidence separately

#### Scenario: Response mappings have provenance
- **WHEN** a reviewer inspects issue get, usage, runs, trigger add/update, and compatibility version-probe operations
- **THEN** each newly supported public field has a source reference, response destination, omission/null policy where applicable, and named test reference

#### Scenario: Unknown future projection remains review-gated
- **WHEN** a CLI response adds an unreviewed field beyond the approved issue activity, trigger, or version-envelope mappings
- **THEN** that field does not automatically alter the public SDK contract or generated behavior

### Requirement: Approved trigger contract matches pinned source

`contracts/sdk-contract.json` SHALL govern trigger add and update from Multica `v0.4.28` commit `38c992ad0a757434fb51584fa34e3bc57d1b78e1`. Source references SHALL cover the Cobra declarations, flag registrations, `RunE` validation, `Flags().Changed` handling, JSON body destinations, and trigger response fields. Add mappings SHALL be `kind -> --kind -> json_body:kind`, `cron_expression -> --cron -> json_body:cron_expression`, `timezone -> --timezone -> json_body:timezone`, and `label -> --label -> json_body:label`. Update mappings SHALL be `cron_expression -> --cron -> json_body:cron_expression`, `timezone -> --timezone -> json_body:timezone`, `label -> --label -> json_body:label`, and `enabled -> --enabled -> json_body:enabled`. The contract SHALL contain five-state presence semantics, normalized kind/required/conditional/at-least-one constraints, compatibility rationale, response provenance, and positive/negative test references.

#### Scenario: Obsolete mappings are absent
- **WHEN** the approved trigger add/update bindings and signatures are inspected
- **THEN** neither contains `--title`, trigger update contains no `--kind`, and every supported schedule field has one reviewed mapping

#### Scenario: Presence semantics are closed
- **WHEN** contract validation inspects each trigger mutation field
- **THEN** omitted, null, empty, zero, and false behavior is explicit or marked not applicable, including false-as-emitted for enabled

#### Scenario: Constraints cite imperative source
- **WHEN** schedule cron requirements, webhook incompatibilities, allowed kind values, or nonempty update constraints are inspected
- **THEN** each normalized constraint cites the pinned imperative source and has positive and negative test references

### Requirement: Trigger bindings regenerate deterministically

The approved contract SHALL remain the only input that generates trigger runtime constants and conventions. Rendering SHALL produce trigger add/update mappings and validators equivalent to the approved contract, and `check` SHALL reject any handwritten drift. Transient provenance and documentation projections SHALL be generated outside tracked paths and SHALL cite the same pinned source revision.

#### Scenario: Generated add binding is exact
- **WHEN** the approved contract is rendered
- **THEN** `AUTOPILOT_TRIGGER_ADD_BINDING` contains only the approved identifier, kind, cron-expression, timezone, and label mappings and constraints

#### Scenario: Generated update binding is exact
- **WHEN** the approved contract is rendered
- **THEN** `AUTOPILOT_TRIGGER_UPDATE_BINDING` contains only the approved identifiers and cron-expression, timezone, label, and enabled mappings and constraints

#### Scenario: Contract check detects drift
- **WHEN** a generated trigger binding differs from a deterministic render of the approved contract
- **THEN** `scripts/upstream_contract.py check` fails without modifying tracked files

### Requirement: Multica 0.4.42 is the exact reviewed authority

The approved SDK contract SHALL target tag `v0.4.42`, version `0.4.42`, release
ID `385445715`, and commit
`76f59f5f1cd9b6e779d0d34c603407d5d4001bf7`. The compatibility interval SHALL
have minimum and maximum-tested version `0.4.42` and SHALL render the exclusive
upper bound `0.4.43`. Every retained, changed, or removed operation SHALL cite
exact source URLs pinned to either the approved old commit
`38c992ad0a757434fb51584fa34e3bc57d1b78e1` or the target commit.

#### Scenario: Target and generated interval agree
- **WHEN** the approved contract, generated runtime, and compatibility docs are inspected
- **THEN** they identify `v0.4.42` at the exact target commit and generated bounds `[0.4.42, 0.4.43)`

#### Scenario: Moving source references fail
- **WHEN** a changed or retained mapping cites a branch, tag URL, abbreviated object, or any commit other than its reviewed old/target SHA
- **THEN** strict validation or the source-link audit fails before promotion

### Requirement: Release archive and executable identities remain distinct

The review SHALL record the `multica-cli-0.4.28-darwin-arm64.tar.gz` archive
SHA-256 `e42c1c6df05201d2d0feff1a9d8032a9ea11c6644721fd465496826124007acf`
and extracted executable SHA-256
`26a722384d8ef39a30cb83fec4e76f3185768369536d1f13a546b03e6c7fbeb9` as
separate baseline values. It SHALL likewise record the `0.4.42` archive SHA-256
`a3bb48baeeb757361686978210e6195aaf50bc69edf83bf3b9c52ca3efc12e41`
and executable SHA-256
`22abcd910562e8800c0e9db561229731e19486ec94b4815d6b1a075dc92ef36c`
as separate target values. Collector binary identity validation SHALL receive
the executable digest, while release verification SHALL verify the archive
against the official manifest and asset digest.

#### Scenario: Archive digest is not passed as binary digest
- **WHEN** a maintainer follows the compatibility collection example
- **THEN** the archive is verified with its archive SHA-256 and collector `--sha256` receives the extracted executable SHA-256

#### Scenario: Binary version envelope is exact
- **WHEN** the target executable runs `version --output json`
- **THEN** it reports version `0.4.42`, commit prefix `76f59f5f1`, date `2026-09-09T11:06:33Z`, Go `1.26.8`, and `darwin/arm64`, and the prefix resolves to the approved full SHA

### Requirement: Complete 0.4.28 to 0.4.42 command and response reconciliation

The approved review SHALL account for all `199` baseline and `189` target
Cobra nodes as `166` unchanged, `21` changed, `2` added, and `12` removed.
It SHALL classify `multica` as the root, `probe-runtimes` as hidden, and
`repo-test`, `test`, and `x` as test-only/unattached. It SHALL also account for
all `173` exact SDK response work items exactly once, with `51` changed and
`122` unchanged, without duplicate IDs or missing target source URLs.

#### Scenario: Inventory totals are exact
- **WHEN** strict validation reconciles baseline and target inventories
- **THEN** every command node and response entrypoint appears exactly once and the required totals match

#### Scenario: Retained mappings are fully traced
- **WHEN** a retained or changed command is approved
- **THEN** every positional validator, local and inherited flag, default, alias, required flag, enum/range, `Flags().Changed` branch, destination, encoding, conflict, and secret channel is traced through `RunE` and helpers

#### Scenario: Extractor output cannot approve behavior
- **WHEN** evidence or a generated suggestion contains a new command, enum, mapping, or response field
- **THEN** generated public behavior remains unchanged until the reviewed fact exists in `contracts/sdk-contract.json`

### Requirement: Target command dispositions are explicit

The approved contract SHALL remove all Plugin operations and autopilot priority
inputs because the target CLI lacks them. It SHALL retain the default
`issues.runs` history operation and safe redacted autopilot reads. It SHALL
defer `issue timeline`, `autopilot trigger-list`, and compact
`issues.runs --active/--siblings` until separate typed response contracts are
approved. It SHALL approve opt-in `issue get --resolve-properties` and issue
list `--fields`, repeatable `--property`, `--resolve-properties`, and property
sort while preserving existing defaults.

#### Scenario: Removed Plugin tree cannot remain approved
- **WHEN** approved operation paths are compared with target root registration
- **THEN** no `plugins.*` operation, binding, response adapter, or canonical vector remains

#### Scenario: Deferred commands do not become public methods
- **WHEN** target evidence contains timeline, trigger-list, active, or sibling command facts
- **THEN** the review records the stated deferral and generation creates no public method or alternate response adapter for them

#### Scenario: Issue query additions are opt-in
- **WHEN** no new issue projection or property option is supplied
- **THEN** approved argv and default response adapters remain compatible with the existing issue get/list behavior
