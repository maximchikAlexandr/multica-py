## MODIFIED Requirements

### Requirement: Generated compatibility
The generated runtime module MUST provide the tested CLI interval from the approved target version. For the Multica `0.6.3` target, the interval SHALL be `[0.6.0,0.6.4)`: `0.6.0` remains the minimum compatible CLI for retained operations, `0.6.3` is the maximum tested CLI, and `0.6.4` is the exclusive next-patch ceiling. Field- and operation-level minimums introduced after `0.6.0` SHALL remain explicit, including existing `0.6.1` gates and new `0.6.3` behavior. Draft PR #101 and PR #103 SHALL NOT be treated as an approved baseline or required intermediate delivery.

#### Scenario: Compatibility uses the reviewed direct-patch interval
- **WHEN** a client reads the generated default policy after the `0.6.3` contract is rendered
- **THEN** it accepts retained operations on `0.6.0` through `0.6.3`, rejects or warns at `0.6.4` according to policy, and retains explicit field-level minimums

#### Scenario: Compatibility uses the generated interval
- **WHEN** a client reads default policy
- **THEN** it uses generated minimum, maximum-tested, and exclusive next-patch maximum versions

## ADDED Requirements

### Requirement: Multica 0.6.3 provenance is exact and complete
The approved contract SHALL identify stable release `v0.6.3`, release id `414793438`, annotated tag object `61bf2402edf4a585f8356f9b68b03f9e1bdabafe`, peeled commit `18fa9f728a9e25f2465df2789631edb2a75442ad`, Darwin arm64 archive `multica-cli-0.6.3-darwin-arm64.tar.gz`, archive SHA-256 `c0124613b6727e8db6f21dbcac460d1dc3a54b6b8b6203177074a8fcea898e18`, and extracted binary SHA-256 `d1387c44020c0198c67d949a0059f7ebb4a55477a46fa621db27b20097f7cfcf`. It MUST retain verified 0.6.1 baseline identity and cite full commit-pinned source references.

#### Scenario: Strict validation receives pinned source
- **WHEN** `upstream_contract.py validate` runs against the exact target checkout
- **THEN** release, tag, commit, artifact, checksum, binary identity, and every approved source reference agree or validation fails

### Requirement: Target CLI and response inventories are closed
The approved contract SHALL classify exactly 209 target CLI nodes, with four additions, zero removals, and three changes, and SHALL classify every child, positional argument, and flag as `support`, `retain`, `adapt`, `remove`, `defer`, or `not_sdk_surface`. It SHALL also contain exactly 196 unique supported response work items with 56 changed and 140 unchanged verdicts, exact old and target source URLs, and test/documentation actions.

#### Scenario: Inventory reconciliation succeeds
- **WHEN** recursive help, pinned source, approved contract, runtime bindings, and response audit are reconciled
- **THEN** all declared counts and dispositions match exactly with no unresolved or duplicate item

#### Scenario: Dynamic checkin remains reproducible
- **WHEN** the collector omits dynamically registered `checkin`
- **THEN** raw collector evidence remains unchanged and the reviewed audit records the source-pinned manual resolution separately

### Requirement: Evidence cannot expand approved SDK surface
Workflow-management HTTP endpoints and `AgentTaskResponse.project_workflow` SHALL remain `not_sdk_surface`, and `daemon autostart*` SHALL remain `defer`, because the approved typed CLI operation set does not expose them. Evidence, source availability, or draft implementations MUST NOT generate public methods without a later approved contract change.

#### Scenario: Unapproved target additions are present in evidence
- **WHEN** render and generated freshness checks run
- **THEN** no workflow-management or daemon-autostart public SDK symbol is produced
