## ADDED Requirements

### Requirement: Multica 0.7.2 provenance is exact
The approved SDK contract SHALL identify SDK base `b268e3bec0436fe51727fda50583344f57663284`, baseline Multica `0.7.1` commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`, target Multica `0.7.2` commit `f05a525ac8e82f5e9169ad078e44f166fad6d5c8`, release `428864784`, archive SHA-256 `d1a7286f8798cc4b28e0e0499d35e7657f7dde24806ce627a380ab7e4db64d92`, and executable SHA-256 `6ad4e01cc2719824b211fe8cc68ad3fafcf445e32b2617987e939892cc1db492` as distinct reviewed fields.

#### Scenario: Provenance validation uses pinned identities
- **WHEN** contract and source-checkout validation inspect the direct upgrade
- **THEN** every identity SHALL match the pinned release, version JSON SHALL report `0.7.2` and commit prefix `f05a525ac` on darwin/arm64 with Go 1.27.3, and target SHALL descend from baseline

### Requirement: The 0.7.1 to 0.7.2 command inventory is closed
The approved contract SHALL reconcile 209 baseline and 209 target public command nodes, Cobra root/source-only nodes, every added/removed/renamed/hidden/deprecated/moved node, and every positional validator, flag, default, presence rule, alias, conflict, destination, and secret channel. It SHALL classify legacy hidden `issue rerun` separately from public `issue rerun-task`.

#### Scenario: Command audit has no pending node
- **WHEN** the inventory audit completes
- **THEN** each baseline and target public node SHALL have exactly one disposition, `rerun`, `rerun-task`, comment steering, daemon force, hidden `probe-runtimes`, Cobra root, and the reconciled wakeup `checkin` extractor defect SHALL be explicitly accounted for, and no pending candidate SHALL generate SDK behavior

### Requirement: The 0.7.2 response review is complete and unique
The response registry SHALL contain exactly 196 unique generated work-item IDs, exactly eight changed and 188 unchanged verdicts, exact old and target source URLs, public-model, fixture, documentation, and error actions, and `response_review_complete=true`.

#### Scenario: Response audit closes the reviewed surface
- **WHEN** response integrity is checked
- **THEN** agent tasks, daemon stop, comment add, rerun-task migration, run messages, issue runs, property create, and property update SHALL be the eight changed rows and every other supported response row SHALL be explicitly retained

### Requirement: Compatibility and generation remain approved-contract-only
The generated compatibility interval SHALL preserve minimum `0.6.2`, set maximum-tested `0.7.2`, and reject `0.7.3` or later. Contract validation, source validation, render, check, source-link audit, and repeated rendering SHALL use only `contracts/sdk-contract.json`; collector output, audits, archives, binaries, and transient renderings SHALL remain untracked.

#### Scenario: Deterministic generation rejects evidence inputs
- **WHEN** the approved contract is rendered twice and the tracked tree is inspected
- **THEN** both projections SHALL be byte-identical, the compatibility interval SHALL be `[0.6.2,0.7.3)`, and no review-only or transient artifact SHALL be tracked or consumed as generator input
