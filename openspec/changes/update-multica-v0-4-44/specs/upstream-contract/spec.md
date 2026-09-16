## MODIFIED Requirements

### Requirement: Generated compatibility
The generated runtime module SHALL provide the tested CLI interval from the
approved target version. For the Multica `0.4.44` target, the interval SHALL be
`[0.4.42,0.4.45)`: `0.4.42` remains the minimum compatible CLI for retained
operations, `0.4.44` is the maximum tested CLI, safe comment deletion SHALL
require `0.4.44`, and `0.4.45` is the exclusive upper bound.

#### Scenario: Compatibility uses the reviewed direct-patch interval
- **WHEN** a client reads the generated default policy after the `0.4.44` contract is rendered
- **THEN** it accepts retained operations on `0.4.42` through `0.4.44`, rejects or warns at `0.4.45` according to policy, and identifies comment deletion as requiring `0.4.44`

#### Scenario: Compatibility uses the generated interval
- **WHEN** a client reads the default policy
- **THEN** it uses generated minimum, maximum-tested, exclusive next-patch, and operation-level availability values
<!-- Source IDs: 002:FR-025,FR-033 -->

## ADDED Requirements

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
