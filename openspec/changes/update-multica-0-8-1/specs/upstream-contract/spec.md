## ADDED Requirements

### Requirement: Multica 0.8.1 provenance is exact and complete
The approved SDK contract SHALL identify SDK base `b268e3bec0436fe51727fda50583344f57663284`, baseline Multica `0.7.1` commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`, target Multica `0.8.1` commit `b1ea927def6490c43bedff537b6f4ed9a47fa828`, release id `436353568`, target archive SHA-256 `d7737360df06c05a547072755e3f3fe0e4d51a1bf4e4a4890d6b105ffc38a976`, and target executable SHA-256 `355ca19f1573d2b4cf5cfe614ca9b760f6b33628f70d4ceaa1c6a86f1726a565` as distinct provenance fields. It SHALL retain the intermediate `0.7.2` and `0.8.0` release commits and archive digests in migration evidence.

#### Scenario: Provenance validation
- **WHEN** the contract and pinned source references are validated
- **THEN** every identity SHALL match the reviewed releases, assets, checksums, version output, and source commits for the complete `0.7.1..0.8.1` chain

### Requirement: The command inventory is closed
The contract review SHALL account for 209 baseline and 225 target CLI nodes, exactly 17 additions, one removal from public help, and 15 changed nodes. The public dynamically constructed `issue wakeup checkin` command SHALL be retained through explicit reconciliation; hidden `probe-runtimes`, hidden/deprecated `issue rerun`, and the root constructor SHALL NOT be misclassified as new public commands.

#### Scenario: Inventory reconciliation
- **WHEN** collector validation and the reviewed gap audit are rerun against the pinned baseline and target
- **THEN** all 225 target nodes and the removed baseline row SHALL have one explicit retained, adapted, deferred, or non-surface disposition with no pending verdict

#### Scenario: Parser exception remains explicit
- **WHEN** literal source extraction does not discover the loop-created `issue wakeup checkin` command
- **THEN** the reconciled evidence SHALL add only that binary-and-source-confirmed row while preserving the original collector outputs unchanged

### Requirement: Supported response review is complete
The approved response review SHALL cover all 196 supported entrypoints, classify 23 as changed and 173 as unchanged, and SHALL set `response_review_complete=true`. Changed rows SHALL carry pinned target source, model action, fixture action, and compatibility rationale; unchanged rows SHALL NOT expand the public SDK without new evidence and approval.

#### Scenario: Response manifest closes without speculation
- **WHEN** response review is validated
- **THEN** every supported entrypoint SHALL have exactly one verdict and the 23 changed rows SHALL map to implementation and verification tasks

### Requirement: Approved contract remains the sole production authority
Only human-reviewed `contracts/sdk-contract.json` SHALL drive committed signatures, mappings, validators, response decoders, fixtures, documentation projections, or generated runtime behavior. Archives, binaries, source clones, collector output, response-review files, audit JSON, and transient renders SHALL remain untracked evidence.

#### Scenario: Deterministic approved projection
- **WHEN** validation, rendering, and check mode run twice from an unchanged approved contract
- **THEN** the committed projection SHALL be byte-stable and no evidence artifact SHALL appear in Git

### Requirement: Compatibility targets the reviewed stable range
The SDK SHALL preserve its reviewed minimum CLI version, set maximum tested to `0.8.1`, and use `0.8.2` as the exclusive ceiling. It SHALL document direct migration from `0.7.1`, the proposed rerun break, and rollback to the previous contract projection.

#### Scenario: Target version is accepted
- **WHEN** compatibility preflight receives Multica `0.8.1`
- **THEN** it SHALL accept the CLI as tested

#### Scenario: Unreviewed next version is rejected
- **WHEN** compatibility preflight receives Multica `0.8.2` or newer
- **THEN** it SHALL reject the CLI before invoking a command
