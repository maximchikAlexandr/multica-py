## ADDED Requirements

### Requirement: Multica 0.8.2 is the exact reviewed authority
The approved contract SHALL identify SDK baseline `b268e3bec0436fe51727fda50583344f57663284`, upstream baseline `0.7.1` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`, and target `0.8.2` at `b7f8efcaae6c5f3273c0038252b5d10c81b41068`; it SHALL use only the direct upstream range between those commits for this upgrade.

#### Scenario: Provenance is complete
- **WHEN** strict contract validation inspects the upgrade metadata
- **THEN** release IDs, full commits, asset names, verified archive checksums, extracted executable hashes, and source references identify the two endpoints without mixing evidence from another release

#### Scenario: Review evidence cannot promote behavior
- **WHEN** collected help, source, or binary evidence contains a candidate command, field, enum, or constraint
- **THEN** public generated behavior remains unchanged until `contracts/sdk-contract.json` contains the reviewed disposition, mapping, policy, and tests

### Requirement: Target command inventory is closed
The approved contract SHALL account exactly once for all 235 target help nodes, including 27 added, 1 removed-from-public-help, and 18 changed nodes, and SHALL record source-only reconciliation separately from public help.

#### Scenario: Inventory closure succeeds
- **WHEN** the contract audit compares the approved inventory with pinned `0.8.2` help and source
- **THEN** every node has one `support`, `adapt`, `retain`, `defer`, or `not_sdk_surface` disposition and duplicate, missing, or unparsed rows fail validation

#### Scenario: Hidden commands remain non-public
- **WHEN** source contains hidden `probe-runtimes` or hidden/deprecated `issue rerun`
- **THEN** generation emits no new public operation from those source-only facts

### Requirement: Response review is complete
The approved contract SHALL retain a source-pinned conclusion for all 196 baseline response entrypoints and SHALL govern each changed model, error, fixture, documentation, and compatibility action.

#### Scenario: Changed responses retain open-world compatibility
- **WHEN** `0.8.2` adds an optional field, nullable value, open enum string, timestamp, pagination value, or millionths-precision credit field
- **THEN** the reviewed decoder preserves the exact type and omission semantics while unknown enum strings remain representable

#### Scenario: Private resources fail closed
- **WHEN** an inaccessible private project, issue, comment, attachment, or relation is requested
- **THEN** the SDK follows the reviewed omission or not-found/authorization contract and never reveals a hidden object through fallback decoding

### Requirement: Compatibility metadata advances only after closure
The generated compatibility policy SHALL identify `0.8.2` as the maximum tested CLI and SHALL derive its bounds only from the approved contract after inventory, response, source-link, and regeneration checks pass.

#### Scenario: Target compatibility is generated
- **WHEN** the approved `0.8.2` contract is rendered
- **THEN** the committed generated module exposes the reviewed minimum and exclusive-next-version ceiling and the package contains the same values

#### Scenario: Above-ceiling CLI is rejected or warned
- **WHEN** version preflight observes a CLI at or above the generated exclusive ceiling
- **THEN** strict and warning policies retain their documented behavior without treating an unreviewed future CLI as tested

