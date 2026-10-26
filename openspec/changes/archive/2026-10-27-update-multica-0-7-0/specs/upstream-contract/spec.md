## ADDED Requirements

### Requirement: Accepted implementation history and revised planning are exact

The implementation SHALL preserve immutable composition
`1f8083040d862669e65b875e7bc9555de96a7346`, whose first parent is exact PR #101
head `b1c350ce22941a66871f11e0c5830a6ec542878c` and whose second parent is original
verified planning SHA `4a83aa817cc2539bee60fe1f1a3996753428a28e`. It SHALL preserve accepted WP-01,
WP-02, and WP-03 commits and SHALL incorporate the new Plan-Verifier-approved
planning revision as a descendant of accepted integration
`9b5d112830831f9e727b35f4936f923ec9429cc7` without rewriting any existing ref.
Final OpenSpec equality SHALL use the new `VERIFIED_PLANNING_SHA`; historical
composition-parent checks SHALL continue using the original planning SHA.

#### Scenario: Historical composition identity changes

- **WHEN** the immutable composition, either exact parent, or its ancestry to the accepted implementation line differs
- **THEN** revised acceptance fails before remaining work is credited

#### Scenario: The revised planning input is incorporated

- **WHEN** the final candidate is checked
- **THEN** it descends from immutable composition and accepted integration, contains the accepted WP commits, and preserves the OpenSpec subtree byte-identically to the new `VERIFIED_PLANNING_SHA`

#### Scenario: Accepted behavior changes during migration

- **WHEN** revised integration alters an accepted WP-01/02/03 signature, mapping, decoder, validation rule, error classification, or regression fixture outside an explicit corrective task
- **THEN** retained-history checks fail and the change is not release-ready

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
Items satisfied by accepted WP history SHALL retain their regression evidence;
server-only runtime access-management routes SHALL be `not_sdk_surface`.

#### Scenario: A target item lacks one decision

- **WHEN** a command or response item is missing, duplicated, unresolved, or lacks a retained/adapted/excluded decision
- **THEN** validation fails and generation changes no public behavior

#### Scenario: Accepted work is needlessly reimplemented

- **WHEN** a target item matches accepted WP-01/02/03 behavior and has no reviewed corrective difference
- **THEN** its decision and accepted regression reference remain retained

#### Scenario: A server-only runtime write is discovered

- **WHEN** runtime visibility, sharing, grant, or atomic-revocation behavior has no pinned CLI command or flag
- **THEN** it is recorded as `not_sdk_surface` and generates no public symbol or binding

### Requirement: Remaining mappings are source-traced and deterministic

Every adapted input and response SHALL record its actual CLI operation, transport
destination, response type, presence behavior, normalized constraints, and
positive/negative references. The approved contract SHALL remain the sole
generator input and two renders SHALL be byte-identical. A related server
handler or matching resource name SHALL NOT substitute for an operation trace.

#### Scenario: A candidate has no traced behavior

- **WHEN** an evidence field or matching name lacks a pinned CLI trace and reviewed constraint
- **THEN** it remains review-only and cannot create a public symbol

#### Scenario: A response field is attached to the wrong operation

- **WHEN** a runtime-definition field is assigned to target-version `runtimes.update` or any operation returning another response type
- **THEN** contract validation fails until the field is assigned only to reviewed runtime-definition responses

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
