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

### Requirement: v0.4.20 compatibility delta is verified end to end

Offline verification SHALL cover the pinned baseline, contract reconciliation,
runtime cascade semantics, agent copy, issue-search response adaptation,
forward-compatible upstream strings, conflict/validation detail preservation,
the retained autopilot trigger mapping, command preview, and documentation.
Repeated operation and decoding cases SHALL extend the repository's existing
frozen dataclass tables and shared fixtures. The full acceptance gate SHALL run
Ruff check and format check, `mypy src`, `mypy tests`, contract validation and
check, package validation, and `pytest -m "not live"` without requiring a
backend or network.

#### Scenario: Compatibility constants and provenance agree
- **WHEN** contract, generated runtime, compatibility policy, docs, and provenance fixtures are checked
- **THEN** tracked baseline values consistently identify `v0.4.20` and `[0.4.20, 0.4.21)`, with no stale `v0.4.9` expectation outside historical/archive material

#### Scenario: Agent copy has table-driven command coverage
- **WHEN** canonical and variant operation cases run
- **THEN** they cover same-runtime copy, cross-runtime default model, explicit portable overrides, repeated permission members, `copy_skills=False`, exact command preview, bound result decoding, and zero-I/O validation failures

#### Scenario: Secret and machine-local copy behavior is negative-tested
- **WHEN** agent copy is constructed without secret configuration
- **THEN** tests prove `--custom-env`, `--mcp-config`, and `--runtime-config` are absent from signature, preview, executed argv, and copied behavior

#### Scenario: Issue search shapes and sources are covered
- **WHEN** search decoding tests run
- **THEN** they cover a `v0.4.20` envelope and legacy array, present title/description/comment sources, a number-shaped query, an omitted source, an unknown future source, exact argv, and the unchanged tuple return type

#### Scenario: Conflict and validation matrices preserve detail
- **WHEN** transport failure cases run
- **THEN** raw statuses, pinned English/Chinese prefixes, generic fallbacks, exit `5`, reviewed local validation, empty diagnostics, and secret-bearing diagnostics assert exact exception class, reported exit code, redacted attributes, and useful `str(exc)` text

#### Scenario: Runtime cascade docs and tests use unbind semantics
- **WHEN** runtime resource tests and public/maintainer documentation are inspected
- **THEN** `cascade=True` is described and asserted as unbinding agents and cancelling active work while preserving configuration, chats, and history, and no current documentation claims that agents are deleted or archived

#### Scenario: Autopilot source-contract regression rejects run spelling
- **WHEN** the approved binding, generated descriptor, canonical operation case, and source-validation fixture are checked
- **THEN** every expected command uses `autopilot trigger` and a mutation back to `autopilot run` fails at least one offline gate

#### Scenario: Unknown upstream-owned strings stay decodable
- **WHEN** typed model and command cases use future provider, model, thinking-level, service-tier, or match-source strings
- **THEN** no closed-enum decode or construction failure occurs before upstream validation

#### Scenario: Canonical discovery includes new command methods
- **WHEN** public method discovery is compared with canonical operation cases
- **THEN** `agents.copy` and `agents.copy_command` follow the repository's command-preview completeness convention, every eager CLI method still has exactly one canonical row, and stored counts equal computed table partitions

#### Scenario: Complete offline gate is green
- **WHEN** the change is ready for delivery
- **THEN** contract `validate --source-checkout`, deterministic render/check, Ruff check, Ruff format check, `mypy src`, `mypy tests`, package validation, and `pytest -m "not live"` all pass

### Requirement: Simplified public surface is verified from one inventory
Offline verification SHALL derive the final public method and symbol inventories, direct-only input signatures, eager/command pairs, operation categories, and return contracts from the approved SDK contract plus explicit bound/relation declarations. Every added, removed, or changed operation SHALL have exactly one canonical success case and focused invalid-input cases. No allowlist SHALL hide an ungoverned request DTO, summary return, domain alias, operation-options parameter, or raw command entry point.

#### Scenario: Removed DTOs and plumbing are absent
- **WHEN** source, imports, annotations, exports, docs, tests, and generated contract projections are scanned
- **THEN** all 23 removed DTO names, their overload paths, and deleted-request `_resolve_request` uses are absent while retained semantic models remain

#### Scenario: Public signatures are structural
- **WHEN** every CLI-backed eager/command pair is inspected
- **THEN** normalized parameters match, direct typed fields are explicit, the shared `options` keyword is consistent, and no broad `Any`, `object` kwargs, or new `type: ignore` workaround was introduced

#### Scenario: Root namespace is intentional
- **WHEN** `multica_py.__all__`, dedicated modules, docs, and packaging artifacts are compared
- **THEN** common root imports and advanced dedicated-module imports match the declared namespace policy exactly

#### Scenario: Approved contract remains authoritative
- **WHEN** contract validation/render/check runs
- **THEN** direct-only input modes, new entry points, response types, source references, and canonical cases agree and no extracted evidence directly promotes runtime behavior

### Requirement: Layered execution and raw CLI behavior are adversarially tested
Table-driven tests SHALL cover base/scoped/operation precedence for every supported option, explicit clears, normalization failures, command snapshot immutability, composite plans, raw argv validation/quoting/redaction, and in-memory attachment materialization. Dynamic temporary paths SHALL normalize only the declared placeholder position while all other argv, mode, stdin, timeout, result, and call counts remain exact.

#### Scenario: Option precedence matrix is complete
- **WHEN** profile, workspace, timeout, cwd, and environment cases run across base, scoped, and per-operation layers
- **THEN** omission/inheritance, replacement/clear, validation, preview, execution, and source-client immutability are asserted

#### Scenario: Raw command safety is complete
- **WHEN** valid metacharacter argv, invalid shapes, secrets, nonzero exits, timeout, and unsupported interactive/process documentation cases run
- **THEN** shell-free execution, redaction, typed errors, and explicit scope boundaries are proven

#### Scenario: Upload source matrix is complete
- **WHEN** path, path-like, empty/binary bytes, named/unnamed streams, closed/text streams, unsafe filenames, preview-only, success, and failure cases run
- **THEN** exact content, lazy materialization, cleanup, stream ownership, aliases, and governed upload argv are asserted

### Requirement: Bound issue and relation behavior is verified without N plus one calls
Offline type and behavior tests SHALL cover Issue values from get, list, search, workspace, workspace-member, project, agent, squad, and child relations; entity actions; project-scoped issue creation; pagination; client binding; optional search metadata; partial-field defaults; cache invalidation; and exact subprocess counts.

#### Scenario: Every issue origin is actionable
- **WHEN** each issue-producing path returns an entity
- **THEN** it is typed/bound as `Issue`, can construct an entity action command, and uses the originating client scope

#### Scenario: Collection command counts are exact
- **WHEN** N rows load from each list/search/relation path
- **THEN** tests assert only governed collection page calls and zero implicit `issue get` calls

#### Scenario: Project create cache behavior is exact
- **WHEN** scoped creation succeeds or fails against loaded and unloaded project issue relations
- **THEN** success invalidates only the matching relation, failure preserves state, and the next load reflects the governed server response

#### Scenario: Permalinks are passive and deployment-correct
- **WHEN** hosted, self-hosted, unsafe, missing-context, encoded-ID, detached, and repeated-access cases run
- **THEN** exact reviewed routes or typed failures are asserted with zero CLI/network calls

### Requirement: Consolidated breaking migration is release-gated
README, API reference, migration guide, examples, changelog, and typed documentation fixtures SHALL present one canonical quickstart and a complete before/after mapping for default client construction, each removed DTO, `IssueSummary`, assignment/reorder modes, attachment uploads, project-scoped create, operation options, raw CLI commands, permalinks, and root namespace moves. The release SHALL identify this as a breaking alpha API change and SHALL not claim request-object compatibility.

#### Scenario: Canonical quickstart is minimal
- **WHEN** README usage is reviewed
- **THEN** it begins with `client = MulticaClient()`, retrieves/iterates bound issues, and uses an entity action before introducing explicit config, filters, command inspection, or low-level modules

#### Scenario: Every removal has a compiling replacement
- **WHEN** migration examples are type-checked
- **THEN** all 23 DTO migrations, summary-to-Issue migration, domain verbs, unified uploads, and dedicated-module import moves resolve against the final public API

#### Scenario: Complete offline gate is green
- **WHEN** the change is ready for delivery
- **THEN** contract source validation and deterministic render/check, Ruff check, Ruff format check, `mypy src`, `mypy tests`, package validation, and `pytest -m "not live"` all pass without backend/network access

### Requirement: Remaining public ergonomics are release-gated
Offline verification SHALL cover the final natural project/issue inputs, exact status-string normalization for issue surfaces and `ProjectResource`, mode-sensitive raw CLI classification for token-login and interactive/process forms, bounded `workspace watch` raw compatibility, direct issue-children binding, and canonical documentation order. Repeated operation, invalid-input, raw-command, and collection-origin cases SHALL extend the repository's existing frozen dataclass tables and shared fixtures. The complete release gate SHALL remain backend-free and network-free.

#### Scenario: Natural-input matrices prove parity and exact plans
- **WHEN** project and issue create cases exercise inline, path-like, semantic description, identifier, entity-reference, omission, and conflict forms through eager and command APIs
- **THEN** signatures match, valid cases produce exact approved argv/results, and invalid cases raise `TypeError` or `ValueError` with zero filesystem/transport I/O

#### Scenario: Status matrices reject implementation errors
- **WHEN** issue list/filter, issue status actions, and `ProjectResource` status actions receive enum members, exact strings, unknown strings, and incompatible values
- **THEN** exact strings and enums produce identical argv while invalid values fail locally without `AttributeError`

#### Scenario: Raw CLI boundary is table-driven
- **WHEN** allowed `auth login --token <token>` forms with trailing options, rejected bare/no-token/malformed auth forms, every other reviewed rejected prefix with trailing arguments, bounded `workspace watch` argv, and representative unknown bounded commands are tested through both raw entry points
- **THEN** allowed cases retain exact structured argv, redaction, options, and result behavior; rejected cases have identical actionable errors, zero transport/spawn calls, and no token or raw secret leakage

#### Scenario: Direct children binding is exhaustive
- **WHEN** empty, children-only, unstaged-only, and mixed child envelopes are decoded through direct eager and command APIs
- **THEN** all issues are bound, metadata is unchanged, entity action construction succeeds, and subprocess counts prove one collection call with no hydration

#### Scenario: README teaches one working workflow in order
- **WHEN** the README introduction and typed documentation fixtures are inspected
- **THEN** they first show `MulticaClient()`, `issues.get(...)`, and a direct entity action, then listing with a valid status value, then command inspection, and all later examples use supported natural inputs without removed request DTOs

#### Scenario: Complete offline gate remains green
- **WHEN** an active change is ready for delivery, or an archived change is reverified
- **THEN** the active change validation runs before archive and its successful proof is preserved; archived tips use `openspec validate --specs --strict --json` instead of a no-delta change validation, while approved-contract validation/render/check, Ruff check and format check, `mypy src`, `mypy tests`, package validation, and `pytest -m "not live"` all pass without backend or network access

### Requirement: Current operation IDs own independent payload fingerprints
The offline regression guard SHALL store immutable SHA-256 fingerprints keyed directly by every currently guarded `OperationCase.id`. Expected fingerprints SHALL be literal test data and SHALL NOT be computed from implementation, generated bindings, the approved contract, or the operation table during the test. Legacy sequential IDs, both legacy-to-current migration maps, the approved-contract `legacy_argv_migration` field, its loader field/closed-key validation, and migration-only tests SHALL be removed. Manual operation cases SHALL retain a non-null provenance/source reference without recreating a migration map.

#### Scenario: Every guarded current case matches its literal fingerprint
- **WHEN** the payload tuple for a guarded current operation case is hashed
- **THEN** its hash equals the literal value stored under that exact current case ID

#### Scenario: Payload mutation is detected independently
- **WHEN** resource, method, args, kwargs, transport method, exact argv, stdin, timeout, or stdout changes without an intentional literal fingerprint update
- **THEN** the regression test fails

#### Scenario: Fingerprint coverage is closed
- **WHEN** the current fingerprint fixture and guarded case inventory are compared
- **THEN** their keys are exactly equal, all keys resolve to unique current operation cases, and no `legacy:NNN` key or migration lookup remains

### Requirement: Simplification proceeds through phase gates
The implementation SHALL use `e719de13442841c64ed96855c5227bbe5e173f10` as the immutable behavior baseline and record `2ff0fd954851b9125ea3adba39696c00a57e8eab` as the current planning commit whose parent/merge-base is that baseline. Implementation SHALL start at the planning commit or a plan-only descendant; no gate SHALL require the implementation checkout's `HEAD` to equal the baseline. The implementation SHALL establish a recorded baseline, then complete and verify Phase 0 cleanup, Phase 1 options, Phase 2 entities, Phase 3 shared relation state, Phase 4 command encapsulation, and Phase 5 generator pilot in order. Each phase SHALL run its focused tests plus Ruff check/format, `mypy src`, `mypy tests`, offline pytest, collection-only marker verification, approved-contract validation/check, and `git diff --check` at the current phase tip, comparing the resulting evidence with the pinned baseline before the next phase begins. Contract validation SHALL use the pinned upstream checkout recorded by the approved contract. A failing gate SHALL stop later phases until corrected.

#### Scenario: Baseline is recorded before implementation
- **WHEN** implementation starts at planning commit `2ff0fd954851b9125ea3adba39696c00a57e8eab` or a plan-only descendant
- **THEN** required offline, type, style, contract, collection, and diff gates are recorded from the pinned baseline `e719de13442841c64ed96855c5227bbe5e173f10` before production changes, and the implementation tip remains a descendant of the planning commit

#### Scenario: Live tests remain excluded from offline collection
- **WHEN** `pytest -m "not live" --collect-only` runs after any phase
- **THEN** no `tests/live/*` node is collected

#### Scenario: Dead-code cleanup preserves active guardrails
- **WHEN** compatibility models/helpers and executable resolver code are deleted
- **THEN** generated min/max version enforcement, `check_version_from_config`, transport error mapping, and their runtime tests remain

#### Scenario: No unrelated cleanup enters a phase
- **WHEN** a phase diff is reviewed
- **THEN** it introduces no new dependency and contains only that phase's implementation, tests, generated artifacts, and required contract/spec updates

### Requirement: Public and behavioral invariants remain closed
Offline verification SHALL prove after the final phase that every CLI-backed eager operation retains one typed public `*_command() -> Command[T]` sibling and delegates through `Command.run()`, command construction validates before I/O, and public signatures/return types, exact argv, result decoding, redaction, stdin, timeout, cwd/environment, immutable config snapshots, compatibility preflight, shared semaphore, exception mapping, temporary cleanup, and process lifecycle are unchanged. Entity equality/hash/repr/serialization/detach/rebind and relation cache/concurrency/retry/refresh/invalidation/pagination semantics SHALL be asserted through public behavior.

#### Scenario: Public eager and command inventory is unchanged
- **WHEN** final public discovery, canonical operation rows, and approved entrypoints are compared to the baseline
- **THEN** the inventories and normalized eager/command signatures are identical

#### Scenario: Command preview remains passive
- **WHEN** representative eager, cached, composite, paginated, temporary-file, and generated-pilot commands expose `.commands`, `repr`, or `str` before `run()`
- **THEN** no subprocess, network, filesystem materialization, or other I/O occurs and secrets remain redacted

#### Scenario: Entity and relation matrices retain behavior
- **WHEN** table-driven public tests exercise field classification, round trips, cache hits, concurrent waiters, retry, failed refresh, invalidate, offset/cursor traversal, and progress limits
- **THEN** results, errors, metadata, and subprocess counts match the baseline contracts

### Requirement: Relation lifecycle follow-up requires a separate decision
After Phases 2 through 4, the implementer SHALL remeasure private entity-to-resource calls, `_set_runtime` usage, invalidation callbacks, concepts, and files touched per relation. This change SHALL NOT implement a repository-wide relation lifecycle rewrite. A future pilot MAY cover exactly one complex relation only after an explicit new decision records remaining material duplication and success criteria based on deleted helpers/callbacks and reduced change surface.

#### Scenario: Remeasurement finds no material duplication
- **WHEN** the post-Phase-4 measurements do not justify another abstraction
- **THEN** no relation-lifecycle pilot is created and the decision is recorded

#### Scenario: Remeasurement supports a pilot
- **WHEN** material duplication remains and one complex relation can test the hypothesis
- **THEN** implementation stops at a documented follow-up proposal rather than adding the pilot or a universal relation framework to this change
