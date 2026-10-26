## ADDED Requirements

### Requirement: The accepted 0.6.2 implementation baseline is exact

The implementation SHALL start from draft PR #101 head
`b1c350ce22941a66871f11e0c5830a6ec542878c` and SHALL preserve its reviewed
public behavior while reconciling conflicts with the approved integration target.

#### Scenario: The implementation starts from another revision

- **WHEN** the implementation branch ancestry does not contain the exact PR #101 head
- **THEN** baseline acceptance fails before any `0.7.0` adaptation is credited

#### Scenario: Conflict resolution changes accepted behavior

- **WHEN** reconciliation alters a PR #101 signature, mapping, decoder, validation rule, error classification, or regression fixture without a source-pinned `0.7.0` adapt decision
- **THEN** the retained-baseline checks fail and the change is not release-ready

### Requirement: Multica 0.7.0 target provenance is authoritative

The approved contract SHALL identify the accepted `0.6.2` baseline and Multica
`0.7.0` release id `421685918`, tag object
`db6e38c32bdbdd3fd1c98210414c458362df16d1`, peeled commit
`dbdbb299164347586e2650bb67684a490726a798`, verified Darwin arm64 artifacts,
and commit-pinned source references for every remaining changed mapping.

#### Scenario: Provenance is incomplete or mixed

- **WHEN** strict validation finds a wrong release identity, digest, baseline, target, or mutable source reference
- **THEN** validation fails before generation

### Requirement: The 0.6.2 to 0.7.0 inventory is closed

The approved contract SHALL contain one reviewed verdict for every one of the
209 target CLI nodes and every one of the 196 supported response work items.
Items already satisfied by exact PR #101 SHALL be retained with regression
evidence; only source-pinned remaining differences SHALL be adapted.

#### Scenario: A target item lacks one decision

- **WHEN** a command or response item is missing, duplicated, unresolved, or lacks a retained/adapted/excluded decision
- **THEN** validation fails and generation changes no public behavior

#### Scenario: An accepted 0.6.2 item is needlessly reimplemented

- **WHEN** a target item matches the accepted PR #101 behavior and has no reviewed `0.7.0` difference
- **THEN** its decision remains retained and its existing regression reference is preserved

### Requirement: Remaining mappings are source-traced and deterministic

Every adapted input SHALL record its real path, query, JSON, header, multipart,
stdin, file, or local-control destination, five-state presence behavior, and
normalized constraints with positive and negative references. The approved
contract SHALL remain the sole generator input and two renders SHALL be byte-identical.

#### Scenario: A candidate has no traced behavior

- **WHEN** an evidence field or matching name lacks a pinned implementation trace and reviewed constraint
- **THEN** it remains review-only and cannot create a public symbol

#### Scenario: Generated output drifts

- **WHEN** a second render or generated freshness check differs from the approved contract
- **THEN** release readiness fails until the source contract or handwritten adapter is reconciled

### Requirement: Compatibility advances from the accepted baseline

The generated policy SHALL accept the reviewed interval through Multica CLI
`0.7.0`, set `max_tested_cli_version` to `0.7.0`, and apply the existing
exclusive-next-version rule above that target without requiring an SDK release
for every intermediate CLI patch.

#### Scenario: A reviewed endpoint is checked

- **WHEN** compatibility preflight observes `0.6.2` or `0.7.0`
- **THEN** it applies the reviewed policy and does not require an intermediate SDK package

#### Scenario: A version exceeds the reviewed ceiling

- **WHEN** compatibility preflight observes a version above the generated exclusive ceiling
- **THEN** the configured strict or warning policy applies and no unreviewed behavior is claimed
