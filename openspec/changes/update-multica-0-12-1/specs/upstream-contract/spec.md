## ADDED Requirements

### Requirement: Multica 0.12.1 provenance is exact
The approved SDK contract SHALL identify SDK base `b268e3bec0436fe51727fda50583344f57663284`, baseline Multica `0.7.1` commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0`, target Multica `0.12.1` commit `fc8028d761707b506cec498385f31fcebbbff598`, target release id `455946845`, target archive `multica-cli-0.12.1-darwin-arm64.tar.gz` with SHA-256 `8334855fa2c116304adcce6348b58a6d539b044ad8a3d62dde0ee2e09ceaea6d`, and target executable SHA-256 `24f0dfc09c3985959ed83619bdc6e00d98bd4c53a12693cbb56bdd12bf75c029` as distinct fields.

#### Scenario: Exact target identity validates
- **WHEN** contract validation inspects source, release, archive, executable, version, commit prefix, OS, architecture, and Go-version identity
- **THEN** every value SHALL match the pinned `0.12.1` evidence and the target commit SHALL descend from the pinned `0.7.1` baseline

#### Scenario: Mixed provenance fails closed
- **WHEN** any source commit, release id, artifact digest, executable digest, version, operating system, or architecture is substituted from another artifact
- **THEN** validation SHALL fail before producing a production projection

### Requirement: The direct command inventory is closed and source-traced
The approved contract SHALL reconcile all `209` baseline and `276` target help nodes, including `68` additions, `1` removal, `34` changed nodes, every positional argument, local and inherited flag, default, alias, `Flags().Changed` presence rule, constraint, destination mapping, and the eight target source-only names.

#### Scenario: Inventory totals reconcile
- **WHEN** baseline and target command identities are audited
- **THEN** the contract SHALL report exactly `276` target nodes, `68` added nodes, `1` removed node, `34` changed nodes, and no duplicate, missing, or pending item

#### Scenario: Every changed input is traced
- **WHEN** any added or changed argument or flag is approved
- **THEN** its row SHALL record path, query, JSON body, header, multipart, or local-process destination; omission and explicit-value semantics; constraints; open-or-closed value policy; and positive and negative test references

#### Scenario: Source-only names do not bypass policy
- **WHEN** `doc`, `environment`, or another target name is attached in source but absent from grouped public help
- **THEN** the contract SHALL record an explicit deferred or non-SDK-surface decision and SHALL NOT generate a public operation

#### Scenario: Unresolved mapping blocks promotion
- **WHEN** extraction cannot resolve a helper, imperative validation, dynamic value, or presence-sensitive branch
- **THEN** the candidate SHALL remain review-only and SHALL NOT alter generated SDK behavior

### Requirement: All supported responses receive one 0.12.1 verdict
The response registry SHALL contain exactly one reviewed verdict for each of the `196` supported response work items, including exactly `118` changed rows, with old and target exact source URLs, factual conclusion, public-model action, adapter action, fixture action, documentation action, nullability/presence policy, and typed-error behavior.

#### Scenario: Response registry is complete
- **WHEN** the direct interval response audit runs
- **THEN** it SHALL report `196` unique work items, `118` changed rows, zero duplicates, zero missing rows, and `response_review_complete=true`

#### Scenario: Retained response remains explicit
- **WHEN** a reviewed operation is wire-compatible at `0.12.1`
- **THEN** its row SHALL retain exact target source, equality rationale, regression fixture, and documentation disposition rather than relying on release-note silence

#### Scenario: Changed response drives all required actions
- **WHEN** a response changes field, type, nullability, omission, pagination, redaction, conflict, replay, or error behavior
- **THEN** its row SHALL identify the concrete model/adapter/test/doc work and SHALL block approval if any action remains pending

### Requirement: Compatibility advances without discarding the supported floor
The contract SHALL preserve `min_cli_version=0.6.2`, set `max_tested_cli_version=0.12.1`, and use `0.12.2` as the exclusive compatibility ceiling.

#### Scenario: Reviewed versions remain accepted
- **WHEN** preflight receives a CLI version from `0.6.2` through `0.12.1`
- **THEN** it SHALL apply existing operation-level gates and accept the reviewed envelope

#### Scenario: Unreviewed next patch is rejected
- **WHEN** preflight receives CLI `0.12.2` or later
- **THEN** it SHALL raise the existing typed incompatibility error before invoking a governed operation

### Requirement: Approved contract remains the sole production generator input
Only `contracts/sdk-contract.json` SHALL drive the committed generated runtime projection and any generated signatures, validators, fixtures, or documentation projections.

#### Scenario: Repeated render is byte-stable
- **WHEN** validate, render, and check run repeatedly from the same approved contract and pinned source
- **THEN** the committed projection SHALL remain byte-identical and check mode SHALL report no drift

#### Scenario: Review evidence stays untracked
- **WHEN** archives, binaries, collector output, gap audits, response manifests, source supplements, or transient renders are used
- **THEN** they SHALL remain outside Git and SHALL NOT become production generator inputs
