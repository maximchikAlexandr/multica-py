## ADDED Requirements

### Requirement: Direct Multica 0.7.1 to 0.10.0 provenance is exact
The approved SDK contract SHALL identify SDK planning base `b268e3bec0436fe51727fda50583344f57663284`, baseline Multica `0.7.1` commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`, target Multica `0.10.0` commit `2fcb424b72b024f65161809081009063846ea44d`, target release id `446890529`, target archive SHA-256 `ddf7a6f7f59f90bf844edff92428e45affa0a80a40b93bed86ab9218d297c9f7`, and target executable SHA-256 `459eeca0af331b137155370651e944269dfa5a99fbe248d67c32616a03826905` as distinct provenance fields.

#### Scenario: Exact target identity validates
- **WHEN** contract validation inspects target source, release, archive, executable, version-output identity, and direct comparison range
- **THEN** every value SHALL match the pinned `0.10.0` evidence and the target commit SHALL descend from the pinned `0.7.1` baseline

#### Scenario: Mixed provenance fails closed
- **WHEN** any source commit, release id, archive digest, executable digest, version, operating system, architecture, or direct-range endpoint is substituted
- **THEN** contract validation SHALL fail without rendering a production projection

### Requirement: The 0.7.1 to 0.10.0 command inventory is closed
The approved contract SHALL account for all `209` baseline and `246` target CLI nodes, exactly `38` additions, `1` removal, and `26` changes, and SHALL classify dynamic `checkin`, hidden/source-only `rerun` and `probe-runtimes`, and attached-but-omitted `environment`.

#### Scenario: Every target node has a reviewed disposition
- **WHEN** the command inventory is validated
- **THEN** every node SHALL have one explicit `retain`, `adapt`, `remove`, `defer`, or `not_sdk_surface` disposition with positional arity, local/inherited flags, defaults, aliases/deprecation, required/conflict/presence rules, RunE/helper destination, full-SHA source references, and test references

#### Scenario: Unknown mapping blocks promotion
- **WHEN** an extractor cannot resolve a helper, imperative validation, dynamic value, or presence-sensitive branch
- **THEN** the candidate SHALL remain a review item and SHALL NOT change generated SDK behavior

## MODIFIED Requirements

### Requirement: All supported responses receive one target verdict
The approved response registry SHALL contain exactly one verdict for each of the `196` supported response entrypoints and SHALL record baseline and target source URLs, public model/error action, fixture action, documentation action, presence/nullability behavior, and malformed-payload behavior. The direct `0.7.1` to `0.10.0` review SHALL contain `94` changed and `102` unchanged verdicts with zero pending.

#### Scenario: Registry reconciliation succeeds
- **WHEN** the response registry is audited for the direct target interval
- **THEN** it SHALL contain `196` unique entrypoints, exactly `94` changed and `102` unchanged dispositions, and no missing, duplicate, or pending verdict

#### Scenario: Wire-compatible server correction remains explicit
- **WHEN** a target correction changes behavior without changing response fields
- **THEN** its registry row SHALL still identify the required fixture, behavioral test, documentation action, retained public model, and error behavior

#### Scenario: Evidence does not promote output
- **WHEN** collector output, gap-audit JSON, response-review JSON, release notes, or binaries contain a candidate field or operation
- **THEN** no generated or public behavior SHALL change until the reviewed approved contract records the decision

### Requirement: Compatibility advances without discarding the supported floor
The contract SHALL preserve `min_cli_version=0.6.2`, set `max_tested_cli_version=0.10.0`, and use the repository policy-derived exclusive upper ceiling for this direct release.

#### Scenario: Reviewed versions remain accepted
- **WHEN** compatibility preflight receives a supported CLI version from `0.6.2` through `0.10.0`
- **THEN** it SHALL apply the existing operation-level gates and SHALL accept the reviewed version envelope

#### Scenario: A version exceeds the reviewed ceiling
- **WHEN** compatibility preflight receives a version at or above the generated exclusive upper ceiling
- **THEN** it SHALL fail with the existing typed incompatibility error before invoking a governed operation

### Requirement: Approved contract remains the sole generator input
Only `contracts/sdk-contract.json` SHALL drive the committed generated runtime, signatures, validators, fixtures, or documentation projections for target `0.10.0`.

#### Scenario: Deterministic render is fresh
- **WHEN** validate, render, and check run twice from the same approved contract and pinned source
- **THEN** the committed projection SHALL remain byte-stable and check mode SHALL report no drift

#### Scenario: Review evidence stays untracked
- **WHEN** collector evidence, parser supplements, gap audits, response reviews, binaries, or transient renders are used during implementation or verification
- **THEN** they SHALL remain outside Git and SHALL NOT become production generator inputs

## REMOVED Requirements

### Requirement: Multica 0.7.1 provenance is exact
**Reason**: The reviewed `0.7.1` delivery is now the exact baseline for a direct `0.10.0` target rather than the active target requirement.

**Migration**: Use `Direct Multica 0.7.1 to 0.10.0 provenance is exact`; retain all `0.7.1` identities as baseline provenance.

### Requirement: The 0.7.0 to 0.7.1 command inventory is closed
**Reason**: The active inventory interval is now the direct `0.7.1` to `0.10.0` range with a different node count and changed-node set.

**Migration**: Use `The 0.7.1 to 0.10.0 command inventory is closed`; preserve the archived `0.7.0` to `0.7.1` evidence as history only.
