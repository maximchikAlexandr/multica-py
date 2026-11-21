## ADDED Requirements

### Requirement: Multica 0.11.1 provenance is exact
The approved SDK contract SHALL identify SDK base `b268e3bec0436fe51727fda50583344f57663284`, baseline Multica `0.7.1` commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`, target Multica `0.11.1` commit `e1fe10d6694848e35dd1aa00e08cd11d93e545ac`, target release id `451169000`, target tree `ee6863ff521e3fdf1937b545d7087ae1b4d83d5e`, target Darwin arm64 archive SHA-256 `32965a28b2d91f10b17d806801ef6598625881d7ac5ffcfb4153e67309e08592`, and target executable SHA-256 `a78cfd71e97ccedfffdf1a520a31d95cc86242457d29b6531ed4d0ada1ffebee` as distinct provenance fields.

#### Scenario: Exact target identity validates
- **WHEN** contract validation inspects target source, release, tree, archive, executable, and version-output identity
- **THEN** every value SHALL match the pinned `0.11.1` evidence and every source URL SHALL pin the full target commit

#### Scenario: Mixed provenance fails closed
- **WHEN** any source commit, release id, tree, digest, version, operating system, or architecture is substituted from another artifact
- **THEN** validation SHALL fail without rendering a production projection

### Requirement: The 0.7.1 to 0.11.1 command inventory is closed
The approved contract SHALL account for all 209 baseline nodes and 263 target help nodes, including 55 added, one removed, and 31 changed nodes, with every positional argument, alias, local/inherited flag, default, constraint, destination, presence rule, and one `retain`, `adapt`, `remove`, `defer`, or `not_sdk_surface` disposition.

#### Scenario: Every target help node has one decision
- **WHEN** the direct-range inventory is validated
- **THEN** all 263 target help nodes SHALL resolve exactly once and no changed flag, positional argument, alias, default, or constraint SHALL remain pending

#### Scenario: Source-only names are reconciled separately
- **WHEN** source-attached names outside grouped public help are audited
- **THEN** `multica` and `probe-runtimes` SHALL be `not_sdk_surface`, `doc` and `environment` SHALL be `defer`, and hidden `rerun` SHALL be `not_sdk_surface` while its former public mapping is removed

#### Scenario: Unknown extraction blocks promotion
- **WHEN** an extractor cannot resolve a dynamic helper, validation branch, destination, or presence rule
- **THEN** the candidate SHALL remain review evidence and SHALL NOT change approved or generated SDK behavior

### Requirement: All supported responses receive one target verdict
The approved response registry SHALL contain exactly one verdict for each of the 196 supported entrypoint/response work items: 102 `changed` rows requiring adaptation and 94 `unchanged` rows requiring retained regression coverage. Every row SHALL record baseline and target source URLs, field/envelope/type/nullability/omission/pagination/error conclusions, and concrete SDK, fixture, test, and documentation actions.

#### Scenario: Registry reconciliation succeeds
- **WHEN** the response registry is audited for the direct target interval
- **THEN** it SHALL contain 196 unique work items, exactly 102 changed and 94 unchanged, with no missing, duplicate, or pending verdict

#### Scenario: A wire-compatible semantic change remains explicit
- **WHEN** target behavior changes without changing the success envelope
- **THEN** its row SHALL still identify the semantic delta, adapter or retained-model action, positive/negative/omission coverage, and documentation action

### Requirement: Compatibility advances without discarding the proven floor
The generated compatibility policy SHALL preserve `min_cli_version=0.6.2`, set `max_tested_cli_version=0.11.1`, and use `0.11.2` as the exclusive next-patch ceiling. Operation-level minimums SHALL remain unless pinned target evidence proves that a retained operation requires a later CLI.

#### Scenario: Reviewed versions remain governed
- **WHEN** compatibility preflight receives a CLI version from `0.6.2` through `0.11.1`
- **THEN** it SHALL apply existing operation-level gates and the reviewed compatibility policy without requiring intermediate SDK packages

#### Scenario: Unreviewed next patch is rejected
- **WHEN** strict compatibility preflight receives CLI `0.11.2` or later
- **THEN** it SHALL raise the existing typed incompatibility error before invoking a governed operation

### Requirement: Approved contract remains the sole generator input
Only `contracts/sdk-contract.json` SHALL drive the committed generated runtime projection, bindings, validators, compatibility metadata, fixtures, or documentation projections. Collector evidence, reconciled manifests, gap/response audits, binaries, and `.devlocal` content SHALL remain review-only inputs outside Git.

#### Scenario: Deterministic render is fresh
- **WHEN** validate, render, and check run twice from the same approved contract and pinned source
- **THEN** relative paths and bytes SHALL be identical and check mode SHALL report no drift

#### Scenario: Evidence cannot promote a candidate
- **WHEN** review evidence contains a command, field, enum value, or mapping absent from the approved contract
- **THEN** public generated behavior SHALL remain unchanged until an explicit contract edit is reviewed
