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
For the Multica `0.5.2` target, the interval SHALL be
`[0.4.42,0.5.3)`: `0.4.42` remains the minimum compatible CLI for retained
operations, `0.5.2` is the maximum tested CLI, the newly decoded duplicate and
supplement fields SHALL require `0.5.2` where field-level compatibility is
represented, atomic create-time properties SHALL require `0.5.2`, and `0.5.3`
is the exclusive next-patch ceiling. Existing operation-level minimums SHALL
remain unchanged unless target source proves an operation delta.

#### Scenario: Compatibility uses the reviewed direct-patch interval
- **WHEN** a client reads the generated default policy after the `0.5.2` contract is rendered
- **THEN** it accepts retained operations on `0.4.42` through `0.5.2`, rejects or warns at `0.5.3` according to policy, and identifies the new response fields and atomic create properties as `0.5.2` additions

#### Scenario: Compatibility uses the generated interval
- **WHEN** a client reads default policy
- **THEN** it uses generated minimum and exclusive next-patch maximum versions
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

### Requirement: Multica 0.4.43 evidence is fully reconciled
The approved contract SHALL pin tag `v0.4.43`, commit
`2ae2dbbb8f9ed9ffe1739ecf5abfe31a940ee50c`, release ID `387217464`, and
separate official archive and extracted-executable identities. Review SHALL
account for all `189` baseline and `189` target command nodes with no added,
removed, renamed, or moved commands and exactly three changed help nodes. It
SHALL account for all `160` approved operations and all `163` response
entrypoints exactly once, with four changed and 159 unchanged response rows.

#### Scenario: Complete inventory closes before promotion
- **WHEN** strict contract and source-link validation inspect the target update
- **THEN** command and response totals, dispositions, exact old/target source URLs, and nonempty conclusions match the reviewed inventories without an allowlist

#### Scenario: Release and executable identities are independent
- **WHEN** target provenance is validated
- **THEN** the archive matches official `checksums.txt` and asset digest, the extracted executable has its separately recorded SHA-256 and version JSON, and neither value is substituted for the other

### Requirement: Target delta is approved rather than inferred
Only human-reviewed `contracts/sdk-contract.json` changes SHALL approve the
agent request mapping, task-run cancellation actor, run-message truncation,
issue-usage coverage counts, status-sort semantic fixture, or compatibility
interval. Evidence and rendered suggestions SHALL remain review-only. The
contract SHALL retain all other supported operations and SHALL record
`repo checkout --fresh` as outside the SDK surface.

#### Scenario: Evidence cannot promote a candidate
- **WHEN** extracted evidence contains a new flag or response field before the approved contract contains its reviewed mapping, presence, constraints, sources, and test references
- **THEN** generation changes no public behavior

#### Scenario: Rejected upstream JSON forms remain recorded
- **WHEN** the reviewed agent flag evidence is inspected
- **THEN** the contract records that empty input, malformed JSON, raw `null`, non-array JSON, and arrays over three items are rejected before the request, without exposing raw JSON as the SDK input type

#### Scenario: Checkout fresh remains non-SDK
- **WHEN** the target command inventory contains `repo checkout --fresh`
- **THEN** the contract records its destructive explicit-only semantics but generates no typed SDK operation, parameter, or relation

### Requirement: Multica 0.4.44 evidence is fully reconciled
The approved contract SHALL pin tag `v0.4.44`, commit
`c7f259c70a60bff30011c403fada79ab382f608a`, release ID `389061637`, and
separate official archive and extracted-executable identities. Review SHALL
account for all `189` baseline and `189` target public command nodes with no
added, removed, renamed, moved, argument, or flag changes and exactly one
transport/error adaptation. It SHALL account for all `163` response entrypoints
exactly once, with 30 changed and 133 unchanged rows.

#### Scenario: Complete inventories close before promotion
- **WHEN** strict contract and source-link validation inspect the target update
- **THEN** command and response totals, unique work-item IDs, dispositions, exact old/target source URLs, and nonempty conclusions match the reviewed inventories without an allowlist

#### Scenario: Release and executable identities remain independent
- **WHEN** baseline and target provenance are validated
- **THEN** each archive matches official `checksums.txt` and asset digest, each executable has its separately recorded SHA-256 and version JSON, and no identity is substituted for another

### Requirement: Target comment and issue decisions are approved rather than inferred
Only reviewed `contracts/sdk-contract.json` changes SHALL approve comment
deletion time, keep-replies deletion, custom lifecycle projection, Triage
parent presence, response dispositions, or compatibility bounds. Evidence and
rendered suggestions SHALL remain review-only. The contract SHALL retain all
other supported operations and SHALL record agent activity, daemon garbage
collection, maintenance, Dingtalk, and telemetry changes as outside the SDK
surface.

#### Scenario: Evidence cannot promote target behavior
- **WHEN** extracted evidence contains a response field or transport change before the approved contract contains its reviewed type, presence, mapping, sources, compatibility, and test references
- **THEN** generation changes no public behavior

#### Scenario: Complete response decisions are unique
- **WHEN** the response review is validated
- **THEN** each of the 163 work-item IDs occurs once, all seven comment rows and all 23 issue projection/update rows carry their approved actions, and the remaining 133 rows are explicitly retained

#### Scenario: Internal target changes remain non-SDK
- **WHEN** source review finds activity, daemon, maintenance, Dingtalk, or telemetry behavior absent from the approved operation registry and public CLI tree
- **THEN** the contract records `not_sdk_surface` and generates no public symbol, parameter, relation, or adapter

### Requirement: Multica 0.5.0 source authority
The approved contract SHALL pin stable Multica `0.5.0` to exact commit `2df765a3c8f39789c9fb76316378bcffc20d22d9`, release ID `391379076`, verified archive and executable digests, and exact source locations for every changed mapping and response.

#### Scenario: Identity is independently reproducible
- **WHEN** maintainers reproduce the target evidence
- **THEN** release, tag, archive, executable, version JSON, and source commit identities SHALL match the approved contract before public behavior changes

### Requirement: Complete 0.4.44 to 0.5.0 command reconciliation
The approved contract SHALL reconcile all 189 baseline and 194 target public help nodes, including five additions, zero removals, renames, or moves, and the three changed label commands. Every retained or added command SHALL record positional arity, aliases, local and persistent flags, defaults, required and conflict rules, presence-sensitive constraints, secret channels, destination encoding, and positive and negative test references.

#### Scenario: Command topology is exact
- **WHEN** strict validation compares approved command inventory with pinned evidence
- **THEN** it SHALL prove 189 baseline nodes, 194 target nodes, five additions, zero removals/renames/moves, and exact changed label mappings

#### Scenario: Imperative constraints remain review-gated
- **WHEN** a changed command uses `Flags().Changed`, custom validation, or helper logic
- **THEN** the approved mapping SHALL normalize the behavior and SHALL NOT promote collector output directly

### Requirement: Complete response reconciliation
The approved contract SHALL contain one decision for each of the 163 supported response entrypoints: targeted reviewed mappings and fixtures for six changed entrypoints and exact-equality evidence for 157 unchanged entrypoints. Every source-link work item SHALL occur exactly once.

#### Scenario: Response audit is complete
- **WHEN** the response and source-link audit runs
- **THEN** all 163 entrypoints SHALL be accounted for exactly once with a `changed` or `unchanged` disposition and resolvable pinned source

### Requirement: Reviewed 0.5.0 compatibility
The generated default compatibility interval SHALL be `[0.4.42,0.5.1)`, with `0.5.0` as maximum tested and operation-level `0.5.0` minimums for new comment-update, skill-label, label-input, and target-only response behavior.

#### Scenario: Retained operations preserve the floor
- **WHEN** a retained operation is checked against CLI `0.4.42` through `0.5.0`
- **THEN** the generated policy SHALL preserve its reviewed compatibility unless an operation-specific target gate applies

#### Scenario: Unreviewed future CLI is outside the interval
- **WHEN** CLI version `0.5.1` or later is detected
- **THEN** compatibility policy SHALL reject or warn according to the existing mode and SHALL NOT claim unreviewed support

### Requirement: Evidence remains non-authoritative
Only the human-reviewed `contracts/sdk-contract.json` SHALL drive generated production behavior. Archives, binaries, collector output, gap audits, response reviews, and transient renders SHALL remain untracked evidence.

#### Scenario: Candidate evidence cannot add API
- **WHEN** evidence contains a new command or field absent from the approved contract
- **THEN** rendering SHALL leave public behavior unchanged and strict review SHALL remain required

### Requirement: Multica 0.5.1 provenance is exact
The approved contract SHALL identify tag `v0.5.1`, peeled commit
`f41fae6b08fb734afcbd13205c0b3203dd0bc9c6`, release ID `392880229`, Darwin
ARM64 archive SHA-256
`85c5e6d8f9af4c3cfef9a6632a94b682ca09afb1e62900a8565eab5bb26a12ec`,
executable SHA-256
`a7223c87c3da4b77afa8b0941504678c30a2770dd1d03df5f2325301360ed588`,
and checksum-manifest SHA-256
`cf71aab5b40ed16e89c5f826109deace7b4b92198ef1147dd1608e4aea396800`.
The unsigned annotated tag SHALL be recorded as a provenance fact and SHALL NOT
override matching official release assets, checksums, and peeled source identity.

#### Scenario: Independent provenance validation succeeds
- **WHEN** the approved target, official release metadata, checksum manifest, archive, executable, and `multica version --output json` evidence are compared
- **THEN** every version, release, commit, platform, architecture, and digest equals the pinned `0.5.1` identity

#### Scenario: Any identity mismatch fails closed
- **WHEN** any approved version, commit, release ID, asset name, platform, architecture, or digest differs from independently collected evidence
- **THEN** strict validation fails before rendering or public SDK edits

### Requirement: Complete command inventory is dispositioned
The approved contract SHALL reconcile all 194 baseline and 201 target public
help nodes, recording seven additions, zero removals, renames, or moves, and
the changed existing nodes `issue` and `runtime profile create`. Every node
SHALL record positional arity, local and inherited flags, defaults, aliases,
accepted values, required and conflict constraints, presence semantics, value
destination, compatibility, source references, and one of `retain`, `adapt`,
`defer`, or `not_sdk_surface`.

#### Scenario: Inventory reconciliation is complete
- **WHEN** the baseline and target help/source inventories are audited
- **THEN** the result contains exactly 201 target nodes and classifies every delta without an unresolved or implicit disposition

#### Scenario: Mapping names are not treated as proof
- **WHEN** a new or changed argument or flag is reviewed
- **THEN** its path, query, JSON, file, header, multipart, or local-process destination is supported by pinned `RunE` and helper source rather than name similarity

### Requirement: Issue wakeup remains deferred as a complete family
The approved contract SHALL classify the `issue wakeup` parent and each leaf
`events`, `list`, `get`, `disable`, `create`, and `update` as `defer`. This
change SHALL add no wakeup operation ID, public method, resource, request or
response model, enum, relation, retry behavior, or compatibility promise.
Candidate mappings and constraints SHALL remain review evidence only.

#### Scenario: Every wakeup leaf is absent from public generation
- **WHEN** the `0.5.1` approved contract is validated, rendered, and compared with public discovery
- **THEN** all seven wakeup nodes have explicit deferred dispositions and no generated or handwritten public SDK entrypoint exists for them

#### Scenario: Deferred create and update semantics remain documented evidence
- **WHEN** candidate wakeup evidence is audited
- **THEN** it retains exact source mappings for agent, instruction, kind, mode, event, actor, task, parent, absolute/delayed/interval/cron schedule, and timezone inputs plus complete-replacement, re-enable, one-shot 409 retry, duration, mutual-exclusion, and loop-protection rules without promoting them

### Requirement: Non-SDK and retained source-only deltas stay bounded
`runtime profile create --runtime-type` SHALL remain `not_sdk_surface` because
runtime profile operations have no approved SDK operation. Configurable release
sources for `update` and stricter workdir path diagnostics SHALL remain
`retain` because they do not change approved public signatures, mappings, or
response shapes.

#### Scenario: Runtime profile candidate is not promoted
- **WHEN** the target adds `--runtime-type` and retains `--protocol-family` as a compatible legacy alternative
- **THEN** the contract records the source delta and no runtime-profile SDK method or model is generated

#### Scenario: Source-only hardening preserves the public contract
- **WHEN** updater release-source configuration and workdir canonicalization are compared with approved operations
- **THEN** signatures and response models remain unchanged and focused compatibility tests cover only existing public file/process boundaries

### Requirement: Complete supported response review governs adaptation
The contract SHALL reproduce `response_review_complete=true` for all 167
supported response entrypoints: `agents.tasks` SHALL adapt its existing
`Page[AgentTask]` projection and `issues.runs` SHALL adapt its `Page[TaskRun]`
projection for the shared optional `wakeup_id` response field,
`issues.run_messages` SHALL adapt `page_run_messages` for optional `call_id`,
and the remaining 164 entrypoints SHALL retain their exact reviewed envelopes,
fields, paths, types, nullability, omission, collection and pagination behavior,
ordering, timestamps, numeric precision, enum openness, and errors.

#### Scenario: Changed response set is exact
- **WHEN** old and target source mappings are compared for all supported entrypoints
- **THEN** exactly three entrypoints are changed for the two additive optional string fields and exactly 164 are unchanged

#### Scenario: Evidence cannot change public response behavior directly
- **WHEN** collector, gap-audit, or response-review evidence contains the target fields
- **THEN** public runtime output changes only after the same decisions and sources enter the approved contract

### Requirement: Multica 0.5.2 provenance is exact
The approved contract SHALL identify target tag `v0.5.2`, release
`394535503`, peeled commit
`d45aba1cd7582bef9210b921bbb7dc198b48e1ee`, baseline commit
`f41fae6b08fb734afcbd13205c0b3203dd0bc9c6`, their direct comparison, official
checksum sources, both reviewed Darwin ARM64 archive and executable SHA-256
values, and both version JSON identities. The unsigned tag SHALL be recorded and
accepted only when the official release, checksum material, asset digest,
peeled commit, executable identity, and binary-reported commit agree.

#### Scenario: Provenance gate accepts one coherent target
- **WHEN** strict provenance validation runs for the approved direct-patch contract
- **THEN** every target and baseline identity equals the pinned release evidence and any mismatch fails validation

#### Scenario: Review evidence stays outside production inputs
- **WHEN** collector, gap, response, checksum, archive, executable, or version evidence is inspected
- **THEN** it remains ignored review input and cannot directly generate or promote public SDK behavior

### Requirement: Complete 0.5.1 to 0.5.2 command inventory is dispositioned
The approved contract SHALL reconcile both 201-node public help trees with zero
additions, removals, renames, or moves and exactly three changed help nodes:
`issue create`, `issue list`, and `issue timeline`. Every retained or changed
node SHALL record positional arity, local and inherited flags, aliases, defaults,
accepted values, required and presence rules, conflicts, and path/query/JSON/
header/multipart/stdin/file/process destinations. Source-only names SHALL be
classified exactly as root normalization (`multica`), hidden
(`probe-runtimes`), test-only (`repo-test`, `test`), and parser false-positive
(`x`).

#### Scenario: Command reconciliation is exact
- **WHEN** strict command audit compares the baseline and target inventories
- **THEN** it reports `201→201`, zero topology changes, three changed help nodes, no unresolved rows, and a disposition for every node and source-only name

#### Scenario: Unchanged nodes retain complete semantics
- **WHEN** any of the 198 unchanged nodes is sampled or exhaustively validated
- **THEN** its arity, flags, aliases, defaults, values, presence, conflicts, and destination mappings equal the approved baseline

### Requirement: Complete 0.5.2 response review governs adaptation
The approved contract SHALL contain exactly 167 unique supported response
work-item IDs with `response_review_complete=true`, pinned old and target source
URLs, exact changed or unchanged disposition, model/fixture/document action, and
no unresolved item. It SHALL adapt the `IssueResponse.duplicate_of` projection
and task supplement metadata only where target source hydrates them, while
retaining existing envelopes, pagination, ordering, timestamps, numeric
encoding, error decoding, and open-enum policy.

#### Scenario: Response registry is complete
- **WHEN** strict response validation runs
- **THEN** all 167 supported work-item IDs occur exactly once and every changed row has reviewed fields, omission policy, source URLs, and test references

#### Scenario: Shared server fields do not imply CLI output
- **WHEN** shared comment or task types contain supplement receipt or daemon-only fields that supported CLI entrypoints do not hydrate
- **THEN** those fields remain absent from the corresponding SDK response contract and negative inventory guards prove no accidental projection

### Requirement: Atomic create-time property mapping is approved
The `issues.create` operation SHALL map each ordered
`IssuePropertyAssignment(reference, value)` to one repeatable
`--property <reference>=<value>` binding. SDK-local validation SHALL be limited
to the tuple and item types, a nonblank string reference, and a string value.
Empty string values, `__none__`, and comparison spellings SHALL reach the pinned
CLI unchanged. The pinned CLI SHALL remain the authority for value grammar,
configuration and capability preflight, name or UUID definition resolution,
all property-type canonical JSON conversions, duplicate and archived rejection,
atomic request binding, and post-create property snapshot verification. The
approved mapping SHALL preserve caller order and SHALL NOT introduce a
client-side catalog lookup.

#### Scenario: Ordered assignments map without extra I/O
- **WHEN** create receives multiple valid assignments
- **THEN** command construction emits one `--property` pair per item in caller order and performs no filesystem, catalog, or transport I/O

#### Scenario: CLI owns value grammar, catalog validation, and atomicity
- **WHEN** a property value is empty, equals `__none__`, uses a comparison spelling, or a property reference is unresolved, archived, duplicated, type-invalid, or mismatches the returned snapshot
- **THEN** the pinned CLI returns its reviewed failure and the SDK surfaces that failure without a create-then-set fallback

### Requirement: New REST-only and local-file behavior remains outside the SDK
Task-supplement create/retry/claim/ack handlers, supplement receipt fields on
comment handlers, duplicate mark/unmark mutations, duplicate timeline actions,
and issue-create attachment path behavior SHALL NOT create public SDK operation
IDs, methods, resources, enums, retries, models, or file inputs in this change.

#### Scenario: Negative inventory prevents accidental promotion
- **WHEN** public symbols, operation IDs, generated mappings, and canonical vectors are enumerated
- **THEN** no supplement mutation, duplicate mutation, issue timeline, comment receipt, or issue-create attachment surface is present
