## ADDED Requirements

### Requirement: Multica 0.7.1 provenance is exact
The approved SDK contract SHALL identify SDK base `f3c41027b89550731e52335e6bea42eeb7b4e905`, baseline Multica `0.7.0` commit `dbdbb299164347586e2650bb67684a490726a798`, target Multica `0.7.1` commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`, target release id `425269384`, target archive SHA-256 `a1f78965984fa0eacff331d67360da2cfc8298e9e97d5f136000b3e8682b1c9b`, and target executable SHA-256 `f167df5161555d8696a996be8fedfde8ab1cbad27c419c9a7905b23492ad9350` as distinct provenance fields.

#### Scenario: Exact target identity validates
- **WHEN** contract validation inspects target source, release, archive, executable, and version-output identity
- **THEN** every value SHALL match the pinned `0.7.1` evidence and the target commit SHALL descend from the pinned `0.7.0` baseline

#### Scenario: Mixed provenance fails closed
- **WHEN** any source commit, release id, archive digest, executable digest, version, operating system, or architecture is substituted from another artifact
- **THEN** contract validation SHALL fail without rendering a production projection

### Requirement: The 0.7.0 to 0.7.1 command inventory is closed
The approved contract SHALL account for all 209 baseline and target CLI nodes, every positional argument, every local and inherited flag, defaults, validators, destination mappings, presence semantics, and an explicit retain, adapt, defer, or not-SDK-surface disposition.

#### Scenario: Stable tree remains complete
- **WHEN** the approved baseline and target inventories are reconciled
- **THEN** they SHALL contain 209 nodes each with zero unexplained additions, removals, positional changes, or flag changes

#### Scenario: Four changed help nodes are source-traced
- **WHEN** `agent create`, `agent update`, `issue wakeup create`, and `issue wakeup update` are reviewed
- **THEN** each changed input SHALL record its path/query/body/header/process destination, omission and explicit-value behavior, approved open-or-closed enum policy, positive case, and negative cases

#### Scenario: Unknown mapping blocks promotion
- **WHEN** an extractor cannot resolve a helper, imperative validation, dynamic value, or presence-sensitive branch
- **THEN** the candidate SHALL remain a review item and SHALL NOT change generated SDK behavior

### Requirement: All supported responses receive one target verdict
The approved response registry SHALL contain exactly one verdict for each of the 196 supported response entrypoints and SHALL record baseline and target source URLs, public model action, fixture action, documentation action, and error behavior.

#### Scenario: Registry reconciliation succeeds
- **WHEN** the response registry is audited for the direct target interval
- **THEN** it SHALL contain 196 unique entrypoints with no missing, duplicate, or pending verdict

#### Scenario: Wire-compatible server correction remains explicit
- **WHEN** a `0.7.1` correction changes behavior without changing response fields
- **THEN** its registry row SHALL still identify the required fixture, behavioral test, documentation action, and retained public model

### Requirement: Compatibility advances without discarding the supported floor
The contract SHALL preserve `min_cli_version=0.6.2`, set `max_tested_cli_version=0.7.1`, and use `0.7.2` as the exclusive ceiling for this direct-patch release.

#### Scenario: Reviewed versions remain accepted
- **WHEN** compatibility preflight receives a supported CLI version from `0.6.2` through `0.7.1`
- **THEN** it SHALL apply the existing operation-level gates and SHALL accept the version envelope

#### Scenario: Unreviewed next patch is rejected
- **WHEN** compatibility preflight receives CLI `0.7.2` or later
- **THEN** it SHALL fail with the existing typed incompatibility error before invoking a governed operation

### Requirement: Approved contract remains the sole generator input
Only `contracts/sdk-contract.json` SHALL drive the committed generated runtime, signatures, validators, fixtures, or documentation projections.

#### Scenario: Deterministic render is fresh
- **WHEN** validate, render, and check run twice from the same approved contract and pinned source
- **THEN** the committed projection SHALL remain byte-stable and check mode SHALL report no drift

#### Scenario: Review evidence stays untracked
- **WHEN** collector evidence, parser supplements, gap audits, response reviews, binaries, or transient renders are used during implementation or verification
- **THEN** they SHALL remain outside Git and SHALL NOT become production generator inputs
