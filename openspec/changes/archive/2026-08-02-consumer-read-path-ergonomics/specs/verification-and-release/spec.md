## ADDED Requirements

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

## MODIFIED Requirements

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
