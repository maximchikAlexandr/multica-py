## ADDED Requirements

### Requirement: Direct Multica 0.7.1 to 0.10.0 provenance
The approved SDK contract SHALL identify baseline `0.7.1` at `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0` and target `0.10.0` release `446890529` at `2fcb424b72b024f65161809081009063846ea44d`, including the verified archive and executable SHA-256 identities, direct comparison range, and compatibility bounds.

#### Scenario: Exact release lineage is accepted
- **WHEN** contract validation inspects the reviewed baseline and target records
- **THEN** it SHALL require the exact release, commit, archive, executable, and version-output identities and reject a substituted tag, commit, digest, or indirect range

#### Scenario: Compatibility metadata is projected
- **WHEN** the approved contract is rendered
- **THEN** maximum tested SHALL be `0.10.0`, the prior supported minimum SHALL remain unless an approved removal requires otherwise, and the exclusive upper boundary SHALL follow the repository compatibility policy

### Requirement: Complete command reconciliation
The approved contract SHALL reconcile all `209` baseline and `246` target CLI nodes, exactly `38` additions, `1` removal, and `26` changes, and SHALL classify dynamic `checkin`, hidden/source-only `rerun` and `probe-runtimes`, and attached-but-omitted `environment`.

#### Scenario: Every target node has a reviewed disposition
- **WHEN** the command inventory is validated
- **THEN** every node SHALL have one explicit `retain`, `adapt`, `remove`, `defer`, or `not_sdk_surface` disposition with positional arity, local/inherited flags, defaults, aliases/deprecation, required/conflict/presence rules, RunE/helper destination, full-SHA source references, and test references

#### Scenario: Unknown mapping fails closed
- **WHEN** a helper, dynamic value, imperative constraint, or destination cannot be proven from pinned source
- **THEN** validation SHALL leave it as a review blocker or deferred item and SHALL NOT generate public SDK behavior

### Requirement: Complete response reconciliation
The approved contract SHALL contain exactly `196` unique supported response-entrypoint verdicts, with `94` changed and `102` unchanged, and zero pending verdicts.

#### Scenario: Response registry closes every entrypoint
- **WHEN** the response registry is validated
- **THEN** each entrypoint SHALL name baseline/target source, disposition, public model/error action, fixture action, documentation action, presence/nullability behavior, and malformed-payload behavior

#### Scenario: Source-only evidence does not promote output
- **WHEN** collector output, gap-audit JSON, response-review JSON, release notes, or binaries contain a candidate field or operation
- **THEN** no generated or public behavior SHALL change until the reviewed approved contract records the decision

### Requirement: Approved-contract-only deterministic generation
Production generation SHALL consume only `contracts/sdk-contract.json` and SHALL produce a byte-stable existing runtime projection.

#### Scenario: Repeat render is stable
- **WHEN** the renderer runs twice from the same approved contract
- **THEN** both runtime projections SHALL be byte-identical and check mode SHALL report no stale output

#### Scenario: Evidence remains untracked
- **WHEN** implementation and packaging contents are audited
- **THEN** `.devlocal`, archives, executables, collector output, audit JSON, source checkouts, transient renders, and visual HTML SHALL be absent from tracked and packaged files
