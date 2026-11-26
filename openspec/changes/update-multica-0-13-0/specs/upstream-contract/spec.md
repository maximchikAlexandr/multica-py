## MODIFIED Requirements

### Requirement: Approved upstream contract is pinned and complete

The approved SDK contract SHALL represent one direct Multica `0.7.1` to `0.13.0` upgrade using release `457951728`, target commit `35b54a3742bb51bdf5ffa688655367ec98044862`, and exact reviewed source range `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0..35b54a3742bb51bdf5ffa688655367ec98044862`.

#### Scenario: Exact release identity is retained

- **WHEN** contract provenance is validated
- **THEN** tag, release id, source commit, archive checksum, executable checksum, version-output checksum, platform, architecture, and source URLs equal the verified `0.13.0` evidence and the prior reviewed lineage remains intact

#### Scenario: Complete command disposition is closed

- **WHEN** target binary help and the prior inventory are reconciled
- **THEN** all `277` target nodes and the removed `issue rerun` node have exactly one reviewed disposition with args, local/inherited flags, defaults, aliases, presence rules, constraints, and source provenance, and pending count is zero

#### Scenario: Complete response review is closed

- **WHEN** supported response coverage is audited
- **THEN** all `196` response work items have old and target source URLs, a factual shape/semantic conclusion, error behavior, and an SDK/test/documentation action, and pending count is zero

### Requirement: Approved contract alone generates production artifacts

Production signatures, models, validators, docs projections, fixtures, and runtime metadata SHALL be deterministic functions of `contracts/sdk-contract.json`; collector output and audit evidence SHALL remain review-only.

#### Scenario: Generated output is reproducible

- **WHEN** validate, render, and check run twice from the same approved contract and pinned source
- **THEN** tracked generated output is byte-identical and no ignored evidence or transient rendering appears in the tracked tree

#### Scenario: Unknown extraction pattern fails closed

- **WHEN** extraction encounters unresolved helpers, dynamic values, imperative presence checks, or unapproved enum candidates
- **THEN** it creates a review item or fails validation and does not modify public SDK behavior

### Requirement: Compatibility is direct and bounded

The SDK SHALL retain its approved minimum CLI version, advertise `0.13.0` as maximum tested, and reject versions at or above the exclusive `0.13.1` ceiling without requiring intermediate-version delivery.

#### Scenario: Supported and unsupported versions are classified

- **WHEN** compatibility checks receive the retained minimum, `0.7.1`, `0.13.0`, and `0.13.1` or newer
- **THEN** the first three follow the approved interval and `0.13.1` or newer fails with the existing typed compatibility error
