## MODIFIED Requirements

### Requirement: Generated compatibility
The generated runtime module MUST provide the tested CLI interval from the approved target version.
For the Multica `0.5.1` target, the interval SHALL be
`[0.4.42,0.5.2)`: `0.4.42` remains the minimum compatible CLI for retained
operations, `0.5.1` is the maximum tested CLI, `TaskRun.wakeup_id` and
`RunMessage.call_id` SHALL require `0.5.1` where field-level compatibility is
represented, and `0.5.2` is the exclusive next-patch ceiling. Existing
operation-level minimums SHALL remain unchanged unless target source proves an
operation delta.

#### Scenario: Compatibility uses the reviewed direct-patch interval
- **WHEN** a client reads the generated default policy after the `0.5.1` contract is rendered
- **THEN** it accepts retained operations on `0.4.42` through `0.5.1`, rejects or warns at `0.5.2` according to policy, and identifies the newly decoded optional fields as `0.5.1` response additions

#### Scenario: Compatibility uses the generated interval
- **WHEN** a client reads default policy
- **THEN** it uses generated minimum and exclusive next-patch maximum versions

## ADDED Requirements

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
