## MODIFIED Requirements

### Requirement: Generated compatibility
The generated runtime module MUST provide the tested CLI interval from the
approved target version. For Multica `0.6.5`, the interval SHALL be
`[0.6.0,0.6.6)`: `0.6.0` remains the minimum compatible CLI for retained
operations, `0.6.5` is the maximum tested CLI, and `0.6.6` is the exclusive
next-patch ceiling. Field- and behavior-level minimums introduced after `0.6.0`
SHALL remain explicit. Draft PR #101, PR #103, and the unmerged MYL-495 plan
SHALL NOT be treated as an approved baseline or required intermediate delivery.

#### Scenario: Compatibility uses the reviewed direct-upgrade interval
- **WHEN** a client reads the generated default policy after the `0.6.5` contract is rendered
- **THEN** it accepts retained operations on `0.6.0` through `0.6.5`, rejects or warns at `0.6.6` according to policy, and retains explicit later field-level minimums

#### Scenario: Compatibility uses generated bounds
- **WHEN** a client reads the generated compatibility policy
- **THEN** it receives the approved minimum, maximum-tested, and exclusive next-patch versions

## ADDED Requirements

### Requirement: Multica 0.6.5 provenance is exact and complete
The approved contract SHALL retain stable `v0.6.1` baseline commit
`2ea01ae4ef55de4310b99af192d2dbd367832883` and SHALL identify stable release
`v0.6.5`, release id `419381779`, annotated tag object
`8a4d3eeb521e699eb977a6a5709bc834bb1927bb`, peeled commit
`654b8ca954034f8181eb6bbb4fc298dede760156`, Darwin arm64 archive
`multica-cli-0.6.5-darwin-arm64.tar.gz`, archive SHA-256
`1ddb1b2546e6ec960e6507c3b8adfde18edc4b63a294e1cfa992be3fe544ae6f`,
and extracted binary SHA-256
`477ccb77877dd74440a1c12873e9a3d693c23eb5d3341a72fb95ac4b8d511720`.
Every approved source reference MUST use a full baseline or target commit.

#### Scenario: Strict validation receives pinned source
- **WHEN** source-aware contract validation runs against the exact target checkout
- **THEN** release, tag, commit, archive, checksum, executable identity, version output, and every approved source reference agree or validation fails

### Requirement: Target CLI and response inventories are closed
The approved contract SHALL classify exactly 209 target CLI nodes, with four
additions, zero removals, and three changes. Every child, positional argument,
local flag, and persistent flag SHALL have exactly one `support`, `retain`,
`adapt`, `remove`, `defer`, or `not_sdk_surface` disposition and a traced
path/query/JSON/header/multipart/stdin/file/local-control destination. The
contract SHALL also classify exactly 196 unique supported response work items
as 57 changed and 139 unchanged with exact old/target source URLs and one
fixture, test, and documentation action.

#### Scenario: Inventory reconciliation succeeds
- **WHEN** recursive help, pinned source, approved mappings, runtime bindings, and the response audit are reconciled
- **THEN** all declared counts, destinations, and dispositions match exactly with no unresolved, duplicated, or silently omitted item

#### Scenario: Dynamic checkin remains reproducible
- **WHEN** the collector omits dynamically registered `checkin`
- **THEN** raw collector evidence remains unchanged and the reviewed audit records exactly one source-pinned manual resolution

### Requirement: Reviewed constraints are normalized and executable
Every adapted input SHALL express imperative rules as `requires`,
`conflicts_with`, `exactly_one`, `at_least_one`, `required_together`, or a named
validator. Each normalized constraint SHALL cite positive and negative vectors,
and unresolved prose-only constraints MUST fail strict validation.

#### Scenario: An adapted mapping has an imperative rule
- **WHEN** contract validation encounters a rule that cannot be resolved to a normalized constraint and test references
- **THEN** validation fails before generation or handwritten implementation

### Requirement: Evidence cannot expand approved SDK surface
Workflow-management HTTP endpoints and daemon-internal CA or workflow payloads
SHALL remain `not_sdk_surface`; `daemon autostart*` SHALL remain `defer`.
Evidence, source availability, and draft implementations MUST NOT generate public
methods without a later approved OpenSpec revision.

#### Scenario: Excluded target additions appear in evidence
- **WHEN** deterministic render and public discovery checks run
- **THEN** no workflow-management, daemon-autostart, internal-CA, or UI-only SDK symbol is produced
