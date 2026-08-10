## ADDED Requirements

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

## REMOVED Requirements

### Requirement: Breaking migration verification
**Reason**: The previous release gate required `IssueSummary` and explicit follow-up gets, which are removed by this breaking API stabilization.
**Migration**: Use the consolidated breaking-migration gate and its typed examples for bound issues, direct inputs, options, domain verbs, uploads, permalinks, and namespace changes.

### Requirement: Consumer read-path compatibility verification
**Reason**: Consumer paths now operate on partial-but-bound `Issue` entities instead of immutable public summaries.
**Migration**: Preserve exact list/search decoding and zero-N+1 assertions while expecting `Issue` and entity continuation behavior.
