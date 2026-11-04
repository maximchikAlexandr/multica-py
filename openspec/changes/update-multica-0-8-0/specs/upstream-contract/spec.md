## ADDED Requirements

### Requirement: Multica 0.8.0 provenance is exact
The approved SDK contract SHALL identify Multica `v0.8.0`, release `432551995`,
direct commit `9b1ab4f9eed9153a94719596eb8a728d2770f065`, verified darwin/arm64 archive
SHA-256 `cb649675794aacbf97163da87399da5524bb43cff31c9819dc1ac717adfa6a27`,
executable SHA-256 `4a3510930068312bff3487dbb9e35d6cdf99b5d738f126c84a31768cdf32f77f`,
and the version JSON fields observed from that executable. It SHALL preserve
the accepted `0.7.1` source and binary provenance as the direct baseline.

#### Scenario: Target provenance is reproducible
- **WHEN** the contract is validated against the exact target source checkout and official release artifacts
- **THEN** tag, release, commit, archive, executable, version, OS, and architecture values match the approved `0.8.0` record

#### Scenario: Planning evidence is not generation input
- **WHEN** collector output, a help inventory, a response audit, or the planning-only `0.7.2` branch exists
- **THEN** none of those artifacts can generate or modify public SDK behavior outside the reviewed `contracts/sdk-contract.json`

### Requirement: The complete 0.7.1 to 0.8.0 command inventory is closed
The contract SHALL reconcile the verified baseline tree, target tree, their
union, and the source-only root/hidden nodes exactly once. Every public node
SHALL have a reviewed retain, adapt, support, remove, defer, or
`not_sdk_surface` disposition with exact source provenance, argument and flag
semantics, destinations, constraints, presence behavior, and test references.

#### Scenario: No public node is unclassified
- **WHEN** the approved inventory is compared with the verified `0.7.1` and `0.8.0` command trees
- **THEN** every added, removed, changed, and unchanged node appears exactly once and no hidden/root node is promoted as public coverage

#### Scenario: Dynamic wakeup action remains reconciled
- **WHEN** the inventory encounters the dynamically registered `issue wakeup checkin` action
- **THEN** exact source and binary-help evidence retain it as an unchanged public node rather than reporting a parser omission

### Requirement: All generated response entrypoints receive one target verdict
The response registry SHALL contain exactly one reviewed target verdict for
every generated operation/variant identifier. Changed rows SHALL record full
field types, null and omission rules, numeric precision, pagination/envelope
behavior, open-enum policy, errors, fixtures, and old/target source URLs;
unchanged rows SHALL retain their accepted contracts with target source proof.

#### Scenario: Response closure is complete
- **WHEN** the registry closure check runs
- **THEN** every generated response identifier is covered once, changed and unchanged totals reconcile with the reviewed audit, and `response_review_complete` is true

#### Scenario: Additive numeric fields remain presence-correct
- **WHEN** task usage or runtime-definition payloads omit, null, zero, or populate their new numeric fields
- **THEN** the reviewed model policy distinguishes those cases without float coercion, invented defaults, or closed provider/runtime vocabularies

### Requirement: Compatibility advances without discarding the supported floor
The SDK SHALL set `compatibility.max_tested_cli_version` to `0.8.0`, retain the
accepted minimum supported CLI version, and append rather than replace the
verified release chain. Compatibility documentation SHALL distinguish
supported operations from commands intentionally deferred or excluded.

#### Scenario: Direct compatibility check accepts the target
- **WHEN** strict compatibility preflight receives the reviewed `0.8.0` version envelope
- **THEN** it accepts the CLI and reports the target as the maximum tested version

#### Scenario: Rollback remains coherent
- **WHEN** the `0.8.0` change is reverted
- **THEN** the prior `0.7.1` contract, generated projection, compatibility claim, source pin, and documentation are restored together
