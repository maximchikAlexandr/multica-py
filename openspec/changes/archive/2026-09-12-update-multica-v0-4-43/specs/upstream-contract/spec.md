## MODIFIED Requirements

### Requirement: Generated compatibility
The generated runtime module MUST provide the tested CLI interval from the approved target version.
For the Multica `0.4.43` target, the interval MUST be
`[0.4.42,0.4.44)`: `0.4.42` remains the minimum compatible CLI for the retained
surface, `0.4.43` is the maximum tested CLI and is required when
`conversation_starters` is explicitly supplied, and `0.4.44` is the exclusive
upper bound.

#### Scenario: Compatibility uses the reviewed direct-patch interval
- **WHEN** a client reads the generated default policy after the `0.4.43` contract is rendered
- **THEN** it accepts `0.4.42` and `0.4.43`, rejects or warns at `0.4.44` according to policy, and documentation states that explicit conversation-starter mutations require `0.4.43`

#### Scenario: Compatibility uses the generated interval
- **WHEN** a client reads default policy
- **THEN** it uses generated minimum and exclusive next-patch maximum versions.
<!-- Source IDs: 002:FR-025,FR-033 -->

## ADDED Requirements

### Requirement: Multica 0.4.43 evidence is fully reconciled
The approved contract SHALL pin tag `v0.4.43`, commit
`2ae2dbbb8f9ed9ffe1739ecf5abfe31a940ee50c`, release ID `387217464`, and
separate official archive and extracted-executable identities. Review SHALL
account for all `189` baseline and `189` target command nodes with no added,
removed, renamed, or moved commands and exactly three changed help nodes. It
SHALL account for all `160` approved operations and all `163` response
entrypoints exactly once, with four changed and 159 unchanged response rows.

#### Scenario: Complete inventory closes before promotion
- **WHEN** strict contract and source-link validation inspect the target update
- **THEN** command and response totals, dispositions, exact old/target source URLs, and nonempty conclusions match the reviewed inventories without an allowlist

#### Scenario: Release and executable identities are independent
- **WHEN** target provenance is validated
- **THEN** the archive matches official `checksums.txt` and asset digest, the extracted executable has its separately recorded SHA-256 and version JSON, and neither value is substituted for the other

### Requirement: Target delta is approved rather than inferred
Only human-reviewed `contracts/sdk-contract.json` changes SHALL approve the
agent request mapping, task-run cancellation actor, run-message truncation,
issue-usage coverage counts, status-sort semantic fixture, or compatibility
interval. Evidence and rendered suggestions SHALL remain review-only. The
contract SHALL retain all other supported operations and SHALL record
`repo checkout --fresh` as outside the SDK surface.

#### Scenario: Evidence cannot promote a candidate
- **WHEN** extracted evidence contains a new flag or response field before the approved contract contains its reviewed mapping, presence, constraints, sources, and test references
- **THEN** generation changes no public behavior

#### Scenario: Rejected upstream JSON forms remain recorded
- **WHEN** the reviewed agent flag evidence is inspected
- **THEN** the contract records that empty input, malformed JSON, raw `null`, non-array JSON, and arrays over three items are rejected before the request, without exposing raw JSON as the SDK input type

#### Scenario: Checkout fresh remains non-SDK
- **WHEN** the target command inventory contains `repo checkout --fresh`
- **THEN** the contract records its destructive explicit-only semantics but generates no typed SDK operation, parameter, or relation
