## ADDED Requirements

### Requirement: Multica 0.6.2 source authority and compatibility

The approved SDK contract SHALL identify Multica `0.6.2`, tag `v0.6.2`, and full source commit `7ab92d7622ecd81d179a8d83ae2dea74835a5069` as the target; SHALL compare it directly with `0.6.1` at `2ea01ae4ef55de4310b99af192d2dbd367832883`; SHALL record the verified release, archive, checksum, executable, and version-output provenance; SHALL retain existing lower operation and field gates; and SHALL use `0.6.2` as maximum tested with `0.6.3` as the exclusive next-patch ceiling.

#### Scenario: Direct patch policy is generated
- **WHEN** the approved `0.6.2` contract is validated and rendered
- **THEN** the generated compatibility policy represents the direct `0.6.1` to `0.6.2` review, accepts the retained lower compatibility floor through `0.6.2`, and treats `0.6.3` as outside the reviewed interval

#### Scenario: Provenance mismatch fails closed
- **WHEN** the tag, release identity, full target commit, archive checksum, executable digest, or version output disagrees with the approved provenance
- **THEN** contract validation fails before generated behavior changes

### Requirement: Complete 0.6.2 command and response reconciliation

The approved contract SHALL disposition all 209 target CLI nodes and reconcile all 196 supported response entrypoints against both pinned source endpoints. Every command SHALL record arity, aliases, hidden state, local and persistent flags, defaults, inherited flags, destinations, presence checks, imperative constraints, enum policy, secret handling, local-control classification, coverage decision, full-SHA source references, and test references. Every response SHALL record envelope, fields, types, nullability, omission, nested collections, pagination and cursors, enum openness, timestamps and numbers, and success, validation, authentication, not-found, conflict, transport, and local-process errors.

#### Scenario: Dynamic and hidden nodes remain explicit
- **WHEN** the inventory is validated
- **THEN** dynamic `issue wakeup checkin` is resolved from reviewed source and binary evidence, hidden `daemon probe-runtimes` remains identified, and neither collector limitation is silently rewritten

#### Scenario: Changed and unchanged registries reconcile
- **WHEN** command and response review completes
- **THEN** every target node and supported response has exactly one reviewed disposition and the changed/unchanged totals agree with the approved manifest

### Requirement: Daemon autostart remains deferred

The approved inventory SHALL record `daemon autostart enable`, `disable`, and `status` as a complete deferred local-control family and SHALL NOT assign them public SDK symbols, generated bindings, response models, or operation cases in this change.

#### Scenario: Deferred nodes do not become public API
- **WHEN** the approved contract is rendered and the public method inventory is discovered
- **THEN** all three autostart nodes remain auditable inventory entries and no daemon-autostart SDK method exists

#### Scenario: Evidence cannot promote local controls
- **WHEN** collector evidence or a generated suggestion contains an autostart operation
- **THEN** validation prevents that evidence from creating public behavior without a later approved contract change

### Requirement: Approved contract remains the only promotion input

Only `contracts/sdk-contract.json` SHALL drive committed runtime generation. Collector output, audit JSON, binary artifacts, response-review files, and transient suggestions SHALL remain outside Git and SHALL NOT alter production behavior.

#### Scenario: Rendering is deterministic and isolated
- **WHEN** validate, render, and check run twice from the same approved contract
- **THEN** the committed runtime bytes are identical and no review-only artifact is consumed as production input
