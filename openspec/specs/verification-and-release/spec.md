## Purpose

Define the offline, packaging, live-smoke, and release checks required for the
SDK.
## Requirements
### Requirement: Offline quality and release
CI MUST run Ruff, configured mypy, offline pytest, statement and branch coverage, contract check, package validation, and approved release validation through `uv`. Coverage acceptance MUST include named gates for process lifecycle code and individually selected critical resource modules so that aggregate package coverage cannot conceal their regression.

#### Scenario: Pull requests run offline quality and release checks
- **WHEN** a pull request runs
- **THEN** job outcomes, not workflow-text tests, decide acceptance.
<!-- Source IDs: 001:FR-051–FR-059C,005:FR-011–FR-017 -->

#### Scenario: Critical coverage zones are enforced
- **WHEN** offline coverage is checked
- **THEN** each configured critical zone independently satisfies both its statement and branch threshold and a missing zone or threshold fails the gate

### Requirement: Canonical operation coverage
Every supported public SDK resource method MUST have exactly one canonical
success operation row with complete transport behavior. The expected method
set MUST be derived from public discovery and compared for exact equality to
canonical rows with no allowlist. Case-count constants and legacy fingerprint
counts MUST be changed in the same commit as their added/removed rows and MUST
equal the lengths computed from the final case tables; historic literals
117/146/29/143 are not post-change requirements.

#### Scenario: Public methods have canonical operation coverage
- **WHEN** `discovered_public_methods` is compared to `{case.sdk_method for case in OPERATION_CASES if case.is_canonical}`
- **THEN** the sets are equal, every supported method has one canonical row, removed methods have none, and stored count constants equal the computed table partitions

### Requirement: Focused process and offline checks
Offline tests MUST use stdlib and pytest, keep exact argv assertions including operations with dynamic temporary paths, retain exactly three real-process cases, and use deterministic synchronization or subprocess test doubles for additional lifecycle branches.

#### Scenario: Offline checks keep focused process cases
- **WHEN** the process module is collected
- **THEN** IDs are `bytes-env`, `text-stdin`, and `timeout-tree-cleanup`.
<!-- Source IDs: 004:FR-006,FR-015,FR-016,005:FR-002,FR-005,FR-006,006:FR-009 -->

#### Scenario: Dynamic argv remains exact
- **WHEN** an operation creates a temporary file or directory path
- **THEN** only the declared dynamic argv position is normalized and the complete remaining argv, transport method, stdin, and timeout are compared exactly

### Requirement: Prepared-target live smoke
Live smoke MUST run separately against a prepared CLI/profile/workspace and clean uniquely named resources through the SDK.
#### Scenario: Prepared targets run live smoke
- **WHEN** live smoke is selected
- **THEN** five fixed scenarios run without backend provisioning or direct HTTP.
<!-- Source IDs: 003:FR-001,FR-002,FR-007,FR-014,FR-022,FR-029,FR-030 -->

### Requirement: Maintainer documentation
Documentation MUST describe CLI installation/authentication, compatibility, and approved upstream review.
#### Scenario: Maintainers can follow approved upstream review
- **WHEN** a maintainer follows it
- **THEN** they validate, collect, render, and check without a promotion state machine.
<!-- Source IDs: 001:FR-067–FR-075 -->

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
Packaging and documentation checks MUST verify that renamed, removed, and
intentionally narrowed public surfaces have complete migration guidance and
that no unsupported legacy method remains discoverable as a canonical public
method. This includes replacing compact bound issue-list wrappers with
`IssueSummary` on direct list and five issue-list relations.

#### Scenario: Canonical discovery matches supported surface
- **WHEN** `discovered_public_methods` is compared to canonical operation cases
- **THEN** the sets are exactly equal after all additions, removals, and replacements with no allowlist

#### Scenario: Migration examples import and type-check
- **WHEN** migration tokens are checked in documentation and equivalent before/after API examples are compiled in the existing typed public-surface contract test
- **THEN** documentation and typed examples agree on `IssueSummary`, explicit `issues.get(summary.id)` only when needed, workspace-member `user_id`, and embedded issue attachments through the supported public API without requiring a Markdown snippet harness

### Requirement: Consumer read-path compatibility verification
Offline verification MUST prove the exact transport, decoding, typing,
presence, and consumer-shaped behavior of issue summaries, workspace-member
identity, and embedded issue attachments. Repeated cases MUST extend the
repository's existing frozen dataclass case tables rather than adding duplicate
test structures.

#### Scenario: Metadata argv is exact and table-driven
- **WHEN** string, integer, finite float, boolean, null, multiple-predicate, omitted, blank-key, equals-key, duplicate-key, `nan`, `inf`, and `-inf` cases are tested
- **THEN** complete expected argv and zero-I/O validation failures are asserted through existing unit operation cases

#### Scenario: Summary decoding preserves queue fields
- **WHEN** issue-list fixtures include or omit labels, metadata, pagination, identity, and hierarchy fields
- **THEN** `IssueListPage` and `IssueSummary` decode exact immutable values without constructing bound issues

#### Scenario: Five issue relations expose summary types
- **WHEN** workspace, project, agent, squad, and workspace-member issue relations are type-checked and loaded against the fake CLI
- **THEN** each relation yields `IssueSummary`, preserves its governed filter and pagination behavior, and performs no per-item `issues.get`

#### Scenario: Member identity distinguishes filter and reconciliation keys
- **WHEN** a fixture has different membership `id` and `user_id`
- **THEN** the member issue relation emits membership `id` while consumer-shaped creator reconciliation matches `user_id` and exposes `email`

#### Scenario: Attachment presence variants decode exactly
- **WHEN** issue-get fixtures contain multiple attachments, an empty array, or an omitted field
- **THEN** tests assert ordered `AttachmentResult` tuples, `()`, and `()` respectively, with no property-access transport call

#### Scenario: Consumer-shaped read flow avoids N plus one reads
- **WHEN** a compatibility test performs queue discovery and external-key lookup from an issue-list page
- **THEN** it reads labels and metadata from summaries and invokes no per-row issue or relation command

#### Scenario: Consumer-shaped result discovery is retry-safe
- **WHEN** a compatibility fixture polls an issue and observes an empty embedded attachment snapshot before a later snapshot containing exactly one attachment
- **THEN** the flow retries explicit `issues.get` and passes `issue.attachments[0].id` directly to existing `download_bytes` without implementing selection policy

#### Scenario: Offline quality gates remain green
- **WHEN** the change is ready for delivery
- **THEN** Ruff check, Ruff format check, `mypy src`, `mypy tests`, contract checks, and `pytest -m "not live"` pass without backend or network access
