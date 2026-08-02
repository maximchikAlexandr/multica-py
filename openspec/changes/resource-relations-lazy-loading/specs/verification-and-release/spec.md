## MODIFIED Requirements

### Requirement: Canonical operation coverage
Every supported public SDK resource method MUST have exactly one canonical
success operation row with complete transport behavior. The expected method
set MUST be derived from public discovery and compared for exact equality to
canonical rows with no allowlist. Case-count constants and legacy fingerprint
counts MUST be changed in the same commit as their added/removed rows and MUST
equal the lengths computed from the final case tables; historic literals
117/146/29/143 are not post-change requirements.

#### Scenario: Public methods have exact canonical coverage
- **WHEN** `discovered_public_methods` is compared to `{case.sdk_method for case in OPERATION_CASES if case.is_canonical}`
- **THEN** the sets are equal, every supported method has one canonical row, removed methods have none, and stored count constants equal the computed table partitions

## ADDED Requirements

### Requirement: Approved-operation integrity
Verification MUST resolve every approved public symbol, compare its normalized
signature, and require exactly one canonical exact-transport vector per
approved operation. Set equality alone MUST NOT conceal duplicate vectors or
unresolved D15–D17 entrypoints.

#### Scenario: Duplicate or unresolved approved operation fails
- **WHEN** a supported method has zero or multiple canonical rows, or an
  approved public symbol cannot be resolved with its approved signature
- **THEN** the offline contract gate fails

### Requirement: Complete relation roadmap verification
Offline verification MUST cover every relation in the 33-relation matrix,
every corrected drift operation, all five loading strategies, bound/snapshot
typing, exact argv and response shapes, subprocess counts, immutable replacement, presence,
per-entity lazy state/refresh/invalidation, concurrency, prefetch bounds, and
public migration behavior using stdlib and pytest.

#### Scenario: Matrix has traceable coverage
- **WHEN** relation coverage is audited
- **THEN** each of the 33 relations maps to an approved operation, requirement scenario, table-driven success case, negative/error case where applicable, and implementation test reference

#### Scenario: Drift fixes have positive and negative proof
- **WHEN** any of the 19 drift dispositions changes argv, decoding, validation, presence, or removes a method
- **THEN** focused fixtures prove the supported behavior and reject the legacy incompatible behavior

#### Scenario: Repeated relation tests are rows
- **WHEN** another parent/relation call-and-assert case is added
- **THEN** coverage grows through frozen dataclass case rows and shared fixtures before a new test function or file is considered

#### Scenario: Exact transport behavior is asserted
- **WHEN** lazy, paged, cached, refreshed, invalidated, retried, and prefetched cases run
- **THEN** they assert complete argv, transport method, stdin, timeout, and exact subprocess count

#### Scenario: Presence and replacement are adversarially tested
- **WHEN** compact, explicit-empty, complete embedded, and richer follow-up payloads are decoded across workspace scopes
- **THEN** tests distinguish missing from empty, seed only complete fields, and prove list/get return distinct immutable wrappers without cross-wrapper state

#### Scenario: Pagination cannot run forever
- **WHEN** offset or cursor fixtures return empty, repeated, malformed, or no-progress continuation state
- **THEN** a bounded call count and typed error are asserted and no partial complete result is cached

### Requirement: Relation live smoke by strategy
Gated live verification MUST exercise representative prepared-target flows for
workspace, project, agent/skill/squad, issue/comment/run, and autopilot graph
phases without direct HTTP access or backend provisioning.

#### Scenario: Live smoke proves representative strategies
- **WHEN** live smoke runs against an authenticated prepared profile/workspace
- **THEN** it proves at least one unpaged, offset-paged, cursor/query, aggregate-envelope, mapping, mutation-invalidation, and bounded-prefetch flow through the public SDK

#### Scenario: Live cleanup is scoped
- **WHEN** live relation smoke creates mutable records
- **THEN** it cleans only uniquely named test-created records and records IDs in proof output rather than reproduction instructions

#### Scenario: Offline collection excludes live nodes
- **WHEN** `uv run pytest -m "not live" --collect-only` runs
- **THEN** no `tests/live/*` node is collected

### Requirement: Breaking migration verification
Packaging and documentation checks MUST verify that renamed and removed public
surfaces have complete migration guidance and that no unsupported legacy
method remains discoverable as a canonical public method.

#### Scenario: Canonical discovery matches supported surface
- **WHEN** `discovered_public_methods` is compared to canonical operation cases
- **THEN** the sets are exactly equal after all additions, removals, and replacements with no allowlist

#### Scenario: Migration examples import and type-check
- **WHEN** documented before/after snippets for entity snapshots and renamed/removed methods are checked
- **THEN** replacement examples use the supported public API and pass configured typing checks
