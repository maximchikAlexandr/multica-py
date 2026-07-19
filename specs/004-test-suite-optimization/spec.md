# Feature Specification: Test Suite Optimization

**Feature Branch**: `004-test-suite-optimization`

**Created**: 2026-07-19

**Status**: Ready for planning

**Input**: User description: "Optimize the multica-py test suite per `.devlocal/tickets/004/test-suite-optimization.md`: remove dead/duplicate tests, convert repetitive per-file tests into table-driven parametrized tests with shared fixtures, and add completeness guards that turn the code reduction into growing coverage."

## Context

The current `tests/` tree is ~11,170 lines and pytest collects 493 tests (449
without live). Large parts of it are mechanical repetition rather than distinct
verification:

- the `mock transport → call method → assert argv` pattern lives in the 21
  `tests/unit/resources/test_*.py` modules, with copy-pasted local helpers
  (`_make_transport()` / `_result()`, a.k.a. `_t()` / `_r()`) duplicated across
  ~19 of them;
- 17 files in `tests/integration/resources/` byte-for-byte repeat a direct
  `os.environ["PATH"]` mutation (unsafe under parallel runs) just to make one
  `list()` call;
- 10 files in `tests/contract/models/` duplicate an existing common invariant
  test;
- maintainer upstream-contract tests repeat a ~30-line argv block invoking
  `scripts/upstream_contract.py` plus a manual `try/finally` backup of
  `upstream_state.json`;
- integration coverage is thin: the manifest lists >100 CLI operations but only
  23 fake-binary JSON fixtures exist, some unused by any test.

This feature refactors the suite so that adding a new command/operation costs one
row of data instead of a new file, while four fail-on-gap completeness guards make
missing coverage visible and enforced: three offline (unit argv-table vs manifest,
JSON-fixture usage, integration operation-coverage vs manifest) and one
live-gated (live command-execution vs manifest, run only under `-m live`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove dead, tautological, and duplicated tests (Priority: P1)

An SDK maintainer removes tests that cannot fail or that fully duplicate an
existing broader invariant, so the suite stops giving a false sense of coverage
and costs less to maintain.

**Why this priority**: These are pure, low-risk deletions (and small
relocations) that immediately shrink the suite without changing real coverage.
They are the safest first step and unblock the later table-driven refactors.

**Independent Test**: Delete the identified files/tests, relocate the genuinely
useful assertions, and confirm the full suite still passes with no loss of any
real invariant (the broader invariant tests still run over all modules).

**Acceptance Scenarios**:

1. **Given** the `tests/contract/models/` directory of 10 per-module duplicate
   files, **When** it is removed and its mypy override is dropped, **Then** the
   suite still passes and the frozen-msgspec invariant is still enforced over all
   `multica_py.models` modules by the common invariant test.
2. **Given** tautological tests that assert on objects they just constructed or
   on framework guarantees, **When** they are removed, **Then** collected test
   count drops but no previously covered SDK behavior becomes uncovered.
3. **Given** the empty `tests/typing/` package whose only real check is
   subsumed by an existing coverage test, **When** it is removed together with
   its mypy override, **Then** the suite still passes.
4. **Given** mutually-exclusive-target assertions that exercise real SDK
   validation, **When** the surrounding tautological tests are deleted, **Then**
   those real assertions are preserved by relocation, not lost.

---

### User Story 2 - Table-driven unit resource tests with a manifest completeness guard (Priority: P1)

A maintainer adds coverage for a CLI operation by adding one data row to a shared
case table instead of writing a new ~15-line test in a new file, and a guard test
fails whenever a supported manifest operation has no argv row.

**Why this priority**: This is the highest-leverage change: it collapses the
largest duplicated block (`tests/unit/resources/`), and its completeness guard
converts the reduction into a mechanism that grows coverage over time.

**Independent Test**: Move all existing per-file resource cases into the shared
table, run the two parametrized tests plus the guard, and confirm coverage is at
least preserved and the guard fails if a supported operation is missing a row.

**Acceptance Scenarios**:

1. **Given** shared fixtures for a mocked transport and raw-result factory,
   **When** an operation is expressed as one argv case row, **Then** a single
   parametrized test verifies the full expected argv for that operation.
2. **Given** a JSON-to-model decode case row, **When** the decode parametrized
   test runs, **Then** the decoded model is validated by the row's check.
3. **Given** optional-flag presence/absence behavior (e.g. `--description`,
   `--name` when `None`), **When** expressed as a complete `expected_argv`,
   **Then** the assertion is exact rather than partial `in`/`not in` checks.
4. **Given** a supported `sdk_method` in the manifest with no argv row, **When**
   the completeness guard runs, **Then** it fails and names the missing
   operation.

---

### User Story 3 - Fixture-based integration tests over every JSON fixture (Priority: P2)

A maintainer runs the integration suite safely in parallel because `PATH` is set
via a fixture (not raw `os.environ` mutation), and every fake-binary JSON fixture
is guaranteed to be exercised by at least one case.

**Why this priority**: Removes a real parallel-safety hazard and eliminates dead
fixtures, but depends on the shared-fixture approach proven in Story 2.

**Independent Test**: Replace the 17 per-file integration resource tests with one
table over the JSON fixtures using a shared client fixture, and confirm the guard
fails if any fixture file is unreferenced.

**Acceptance Scenarios**:

1. **Given** a shared fake-CLI client fixture that sets `PATH` through the test
   framework, **When** integration resource tests run, **Then** no test mutates
   `os.environ` directly and the suite is safe under parallel execution.
2. **Given** one table row per existing JSON fixture (including special checks
   like `set_status` and `deprioritize`), **When** the parametrized test runs,
   **Then** each fixture's operation is exercised.
3. **Given** a JSON fixture file that no table row references, **When** the
   fixture-usage guard runs, **Then** it fails and names the unused fixture.
4. **Given** a guard-eligible manifest operation that is neither exercised by a
   `FakeCliCase` row nor listed in `KNOWN_FIXTURE_GAPS`, **When** the
   operation-coverage guard runs, **Then** it fails and names the uncovered
   operation; a stale `KNOWN_FIXTURE_GAPS` entry (one that now has a row) also
   fails.

---

### User Story 4 - Shared harness for maintainer upstream-contract tests (Priority: P2)

A maintainer testing the upstream-contract pipeline writes only the meaningful
assertions, while shared fixtures build the full `upstream_contract.py` argv and
back up/restore generated state automatically.

**Why this priority**: Large duplicated block, but it touches the sensitive
upstream-contract pipeline, so it comes after the safer core refactors are
proven.

**Independent Test**: Introduce a contract-test conftest (fake upstream CLI
fixture, argv-builder helper, auto state-preservation) and rewrite the
collect/check/prepare-upgrade/promotion/quickstart/apply-suggestions tests onto
it; confirm behavior is unchanged.

**Acceptance Scenarios**:

1. **Given** a shared argv-builder that fills default upstream parameters,
   **When** a test overrides only the differing parameters, **Then** it obtains
   the process result without repeating the ~30-line argv block.
2. **Given** an auto-fixture that backs up and restores `upstream_state.json`
   and removes generated candidate contracts, **When** any contract test runs,
   **Then** generated state is preserved without per-test `try/finally`.
3. **Given** deterministic A/B and canonical-vs-custom-output pairs, **When**
   expressed via parametrized output paths, **Then** they run as data rows
   rather than duplicated test bodies.

---

### User Story 5 - Parametrized contract-diff severity tests (Priority: P3)

A maintainer verifies diff severity classification through one table mapping each
mutation fixture to its expected severity, instead of six near-identical tests.

**Why this priority**: Clear win but small relative to Stories 2–4.

**Independent Test**: Replace the repeated `decode baseline + decode mutation +
diff + assert severity` bodies with one parametrized test keyed on
`(mutation_file, must_contain, must_not_contain, unresolved_breaking)`.

**Acceptance Scenarios**:

1. **Given** the mutation→severity table of exactly five file-mutation rows
   (required-flag-added → breaking; help-text-changed → severities ⊆
   {doc_only, provenance_only}; command-added → additive; command-removed →
   breaking; optional-flag-added → additive, not breaking), **When** the
   parametrized test runs, **Then** each mutation yields its expected severity.
2. **Given** tests with genuinely specific logic (the `command-renamed`
   rename-heuristic test, summary reconciliation, manual `SemanticCLIContract`
   assembly), **When** the refactor is applied, **Then** they remain separate
   tests (not in the table).

---

### User Story 6 - Full live command coverage: CRUD matrix, command execution, presence, errors (Priority: P3)

A maintainer covers a new live resource by adding one CRUD descriptor (~10 lines)
or one live invocation (~3 lines) instead of a new file; error-mapping and
presence-semantics cases become single parametrized tests reusing the existing
oracle/fixtures; and a live guard fails whenever a manifest operation is never
executed against the real backend, so every command and resource is exercised
live (subject to a documented exceptions allowlist).

**Why this priority**: Highest risk (requires a real backend run) and depends on
patterns proven earlier, so it is sequenced last.

**Independent Test**: Collapse `test_errors.py` and `test_projects.py` presence
cases into parametrized tests, add a CRUD-descriptor round-trip test starting with
labels and projects, build a live invocation registry that executes every
guard-eligible manifest operation, and run everything against the live backend so
the live command-execution guard passes.

**Acceptance Scenarios**:

1. **Given** a table `(client_fixture_name, operation, expected_exc)`, **When**
   the parametrized error test runs, **Then** each client operation maps to its
   expected exception with a secret-free message; destructive and
   diagnostic-bundle tests stay separate.
2. **Given** a presence-semantics table for P-OMIT/P-EMPTY/P-SET, **When** the
   parametrized projects test runs, **Then** each update request yields the
   expected title/description; P-NULL-HTTP (which bypasses the SDK) stays
   separate.
3. **Given** a resource CRUD descriptor
   `(create, get, update, delete, oracle_path, name_builder)`, **When** the
   round-trip test runs for labels and projects, **Then** create/get/update/
   delete/absent are verified generically and the Unicode/emoji case is just a
   `name_builder` parameter.
4. **Given** a live invocation registry `LIVE_OPERATIONS` of non-CRUD operations
   (each a `(sdk_method, invoke)` pair whose `invoke(ctx)` sets up prerequisites
   and calls the SDK against the real backend) plus the CRUD-derived operations
   from `CRUD_DESCRIPTORS`, **When** the live command-execution guard (FR-021)
   runs, **Then** it fails and names any guard-eligible manifest operation that is
   neither covered (`T_live`) nor in `LIVE_EXEC_EXCEPTIONS` (permanent, with a
   valid reason code) nor in `KNOWN_LIVE_GAPS` (not-yet-automated), and fails on a
   stale entry in either allowlist or on an invalid reason code.

---

### User Story 7 - Consolidate test-infrastructure unit tests (Priority: P3)

A maintainer maintaining the live test infrastructure finds shared target/settings
factories in one place and fewer tiny modules, while all feature-002 security
invariants remain intact.

**Why this priority**: Cleanup with real value but no coverage change; sequenced
with the other low-risk consolidations.

**Independent Test**: Move `make_target()`/`make_settings()` into a shared
conftest, merge the tiny `test_live_*` modules into their topical owners, and fold
`test_transport_errors.py` into `test_transport.py` as a table; confirm all
security-invariant tests still run.

**Acceptance Scenarios**:

1. **Given** shared `make_target()`/`make_settings(tmp_path, **overrides)`
   factories in `tests/unit/conftest.py`, **When** live-infra tests run, **Then**
   local copies are removed and behavior is unchanged.
2. **Given** tiny modules (naming, resource-registry), **When** merged into their
   topical modules with truncation cases as one parametrized `(fn, args,
   max_len, pattern)`, **Then** the same assertions run from fewer files.
3. **Given** the feature-002 security-invariant tests (secrets outside the
   artifact tree, argv without shell, `KEEP_ENV` forbidden in CI, loopback-only
   URL), **When** the consolidation is done, **Then** every such invariant is
   still asserted.

---

### Edge Cases

- A completeness guard (argv table, JSON fixtures) must fail loudly and name the
  specific missing/unused item, not silently pass, so gaps stay visible.
- The argv guard must reconcile with a green suite (FR-017): a guard-eligible
  operation with no row is only tolerated if listed in `KNOWN_ARGV_GAPS`
  (FR-005); a stale allowlist entry (operation that now has a row) must also fail.
- Relocating live assertions (mutually-exclusive targets, Unicode label names)
  must not drop any previously covered validation.
- Consolidation must not weaken any feature-002 security invariant; those tests
  are explicitly out of scope for deletion.
- The refactored suite must remain safe under parallel execution (no direct
  `os.environ` mutation replacing framework-scoped environment control).
- Each completeness guard is introduced in the same user story as the table it
  guards, so the suite is never left red between stories.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `tests/contract/models/` directory (10 duplicate per-module
  files plus `__init__.py`) MUST be removed and its `tests.contract.models.*`
  mypy override MUST be dropped, while the common frozen-msgspec invariant test
  continues to enforce the invariant over all `multica_py.models` modules.
- **FR-002**: The following tautological/dead tests MUST be removed, and the
  listed genuine assertions MUST be relocated verbatim (not lost). This is the
  closed, authoritative list (see also the Test Inventory appendix):
  - In `tests/unit/resources/test_mutually_exclusive.py`: delete
    `test_description_input_is_tagged_union`, `test_inline_description_is_exclusive`,
    `test_file_description_is_exclusive`, `test_stdin_description_is_exclusive`,
    `test_unknown_description_type_rejected`, `test_description_dispatch`; RELOCATE
    `test_invalid_value_rejected`,
    `test_issue_assignment_request_rejects_multiple_targets`, and
    `test_issue_reorder_request_rejects_multiple_targets` into
    `tests/unit/resources/test_issues.py`; then delete the file.
  - Delete `tests/unit/resources/test_labels.py` (asserts a msgspec default — a
    library guarantee).
  - The removed `description` dispatch coverage MUST be replaced by three explicit
    `ArgvCase` rows (one per union variant) per FR-006a.
- **FR-003**: The `tests/typing/` package (including empty `cases/`) MUST be
  removed together with its mypy override, since its only real check is subsumed
  by the existing full-CLI-coverage test.
- **FR-004**: Unit resource tests MUST be expressed as shared parametrized case
  tables (argv cases and decode cases) driven by shared fixtures (a mocked
  transport and a raw-result factory), with one operation represented as one data
  row. After migration, every file matching `tests/unit/resources/test_*.py` is
  deleted EXCEPT `tests/unit/resources/test_issues.py`, which is retained to hold
  the assertions relocated per FR-002 (and any issue-specific non-table
  invariants). The `test_issue_comments.py`, `test_issue_labels.py`, and
  `test_issue_metadata.py` cases are migrated into the shared tables like any
  other resource. Each migrated case is copied verbatim per the extraction rule
  in the Test Inventory appendix (no behavior is invented).
- **FR-004a**: Decode coverage is NOT gated by a completeness guard (only argv is,
  per FR-005). Every decode assertion present in the deleted per-file tests MUST
  be preserved as a `DecodeCase` row; decode rows for currently-untested
  operations are out of scope for this feature.
- **FR-005**: A completeness guard test MUST fail when a *guard-eligible*
  manifest operation lacks at least one argv case row, naming the missing
  operation. "Guard-eligible" is defined precisely as a `ManifestEntry` whose
  `sdk_method` is non-empty AND whose `status != "unsupported"` (there is no
  `supported` field; `status` is the field). To keep the suite green during
  incremental migration (FR-017), the guard MUST support an explicit
  `KNOWN_ARGV_GAPS: frozenset[str]` allowlist of guard-eligible `sdk_method`
  values that are not yet covered; the guard fails if (a) a guard-eligible
  operation is neither in the argv table nor in `KNOWN_ARGV_GAPS`, or (b) an
  entry in `KNOWN_ARGV_GAPS` also has a table row (stale allowlist). The feature
  goal is `KNOWN_ARGV_GAPS == frozenset()`; every allowlist entry MUST carry a
  short inline comment naming the reason. `KNOWN_ARGV_GAPS` is seeded with exactly
  the guard-eligible operations that have no unit argv coverage at feature start.
- **FR-006**: Optional-flag presence/absence MUST be verified via a complete
  `expected_argv` value rather than partial `in`/`not in` assertions. The argv
  assertion form MUST match the transport method exactly: for `run_bytes`,
  `assert_called_once_with(expected_argv, stdin=<case.stdin|None>, timeout=<case.timeout|None>)`;
  for `run_text`, `assert_called_once_with(expected_argv)` with no keyword args.
- **FR-006a**: The unit argv table MUST include one `ArgvCase` row per issue
  `description` union variant — `InlineDescription` (`--description <text>`),
  `FileDescription` (`--description-file <path>`), and `StdinDescription`
  (`--description-stdin`) — replacing the coverage removed in FR-002.
- **FR-007**: Integration resource tests MUST use a shared fake-CLI client
  fixture that sets `PATH` through the test framework (no direct `os.environ`
  mutation) and MUST be safe under parallel execution.
- **FR-008**: Integration resource operations MUST be expressed as one table row
  (`FakeCliCase`) per existing JSON fixture (23 files, listed in the Test
  Inventory appendix), and a guard test MUST fail when any
  `tests/fixtures/json/**/*.json` file is not referenced by at least one row's
  `fixture`. Each row's `sdk_call` and `check` MUST be taken verbatim from the
  existing `tests/integration/resources/*` test that currently uses that fixture;
  for any fixture not currently used by a test, the `sdk_call` is derived from the
  resource method named by the fixture path (e.g. `issues/issue_status_*` →
  `client.issues.set_status(...)`, `issues/issue_deprioritize_*` →
  `client.issues.deprioritize(...)`) — see the appendix mapping. No new fake-CLI
  behavior is invented.
- **FR-020**: Integration tests MUST include an operation-coverage guard that
  fails when a guard-eligible manifest operation (same predicate as FR-005:
  `sdk_method` non-empty AND `status != "unsupported"`) is neither exercised by a
  `FakeCliCase` row (matched via the row's `sdk_method` field) nor listed in an
  explicit `KNOWN_FIXTURE_GAPS: frozenset[str]` allowlist; it also fails when a
  `KNOWN_FIXTURE_GAPS` entry is exercised by a `FakeCliCase` row (stale
  allowlist). Each `KNOWN_FIXTURE_GAPS` entry MUST carry a short inline reason
  comment. `KNOWN_FIXTURE_GAPS` is seeded with exactly the guard-eligible
  operations that have no fake-CLI JSON fixture at feature start; the goal is
  `KNOWN_FIXTURE_GAPS == frozenset()`, and closing a gap means adding a JSON
  fixture plus its `FakeCliCase` row. This guard is distinct from the FR-008
  fixture-usage guard (FR-008: every fixture is used, `fixture → row`; FR-020:
  every operation is covered, `operation → fixture-or-allowlist`) and ships with
  US3 (FR-017). It applies to the offline integration (fake-CLI) layer; live
  command-level completeness is required separately by FR-021.
- **FR-021**: The live suite MUST work toward executing every guard-eligible
  manifest operation (same predicate as FR-005) against the real backend, and MUST
  include a live command-execution guard. The guard compares the guard-eligible
  set `E` against the covered set
  `T_live = {op.sdk_method for op in LIVE_OPERATIONS} ∪ crud_sdk_methods(CRUD_DESCRIPTORS)`,
  where `crud_sdk_methods` expands each `CrudDescriptor` into its four manifest
  ids (see Appendix C: e.g. `labels` → `labels.create/get/update/delete`). CRUD
  operations are covered ONLY through `CRUD_DESCRIPTORS` (executed by
  `test_crud_round_trip`); `LIVE_OPERATIONS` holds ONLY non-CRUD standalone
  operations (executed by `test_live_operation_executes`), so no operation is
  executed twice. Coverage from `test_error_mapping`, presence tests, or other
  live tests does NOT count toward `T_live` — an operation covered only there
  still needs a `LIVE_OPERATIONS` entry, a `CRUD_DESCRIPTORS` entry, or a listing
  in one of the two allowlists below.

  Two disjoint allowlists exist (mirroring the offline guards' `KNOWN_*_GAPS`):
  - `LIVE_EXEC_EXCEPTIONS: Mapping[str, LiveExecReason]` — operations that CANNOT
    be run in the test environment, keyed by `sdk_method`, each carrying a reason
    from the CLOSED set `LiveExecReason = Literal["destructive-irrecoverable",
    "requires-external-infra", "interactive-or-foreground",
    "process-or-daemon-control"]` (definitions: `destructive-irrecoverable` = would
    break the shared test environment with no restore; `requires-external-infra` =
    needs infra unavailable in the live test env, e.g. cloud provisioning or a
    real external repo; `interactive-or-foreground` = interactive/streaming/
    long-running command not expressible as one synchronous call;
    `process-or-daemon-control` = daemon/process-group control incompatible with
    test isolation). This allowlist is permanent; its goal is the smallest possible
    size.
  - `KNOWN_LIVE_GAPS: frozenset[str]` — operations that CAN run but are NOT YET
    automated, tracked so the guard stays green during incremental development
    (exactly like `KNOWN_ARGV_GAPS`). Its goal is `frozenset()` at feature
    completion (SC-008).

  The guard MUST FAIL when `E - T_live - set(LIVE_EXEC_EXCEPTIONS) - KNOWN_LIVE_GAPS`
  is non-empty (naming each uncovered, untracked operation), when
  `T_live ∩ (set(LIVE_EXEC_EXCEPTIONS) ∪ KNOWN_LIVE_GAPS)` is non-empty (stale:
  an allowlisted operation is now executed), when
  `set(LIVE_EXEC_EXCEPTIONS) ∩ KNOWN_LIVE_GAPS` is non-empty (an operation in both
  buckets), or when a `LIVE_EXEC_EXCEPTIONS` value is not a member of
  `LiveExecReason` (invalid reason code).

  Because executing operations needs a running backend, `test_live_operation_executes`
  and `test_crud_round_trip` are marked `live_extended` (the scheduled/manual heavy
  suite). The guard itself needs no backend (pure set math over the manifest and
  registries) but stays inside the live layer marked `live_smoke` so the blocking
  live CI job enforces coverage cheaply.   All are `-m live`-gated and NEVER part of
  the offline `-m "not live"` suite (Constitution IV; FR-017). Because pytest
  markers do NOT inherit in this repo, EVERY new live module MUST set a module-level
  `pytestmark` that includes the base `pytest.mark.live` (plus the per-test subtag
  `live_smoke`/`live_extended`); otherwise `-m "not live"` would collect it. A weak
  implementer MUST verify `uv run pytest -m "not live" --collect-only` lists no
  `tests/live/*` node. Destructive operations that CAN be recovered MUST be executed
  with restore (as the existing backend-stop test does), marked both `destructive`
  and `serial`; only irrecoverable ones go in `LIVE_EXEC_EXCEPTIONS`.
  `LIVE_EXEC_EXCEPTIONS` and `KNOWN_LIVE_GAPS` MUST be disjoint (each operation in
  exactly one bucket); the guard also FAILS on a non-empty intersection. Every
  `KNOWN_LIVE_GAPS` entry MUST carry a short inline comment naming the reason
  (like `KNOWN_ARGV_GAPS`).
- **FR-009**: Maintainer upstream-contract tests MUST share a conftest providing a
  fake upstream CLI fixture, an argv-builder helper that fills default upstream
  parameters, and an auto-fixture that backs up/restores `upstream_state.json`
  and removes generated candidate contracts, so per-test bodies contain only
  meaningful assertions.
- **FR-010**: Contract-diff severity tests MUST be consolidated into a
  parametrized test keyed on mutation fixture and expected severity. The seed
  table has exactly five file-mutation rows: `required-flag-added` →
  contains `breaking`, `unresolved_breaking is True`; `help-text-changed` → only
  severities in `{"doc_only", "provenance_only"}`; `command-added` → contains
  `additive`; `command-removed` → contains `breaking`; `optional-flag-added` →
  contains `additive`, excludes `breaking`. A test MUST stay separate (NOT in the
  table) when its assertions cannot be expressed as
  `(mutation_file → severities present/absent [+ unresolved_breaking])`;
  specifically these remain separate: the `command-renamed` rename-heuristic test
  (asserts `suggested_action`/`affected_operations`, not severity), summary-
  reconciliation tests, and in-code `SemanticCLIContract`-assembly tests. This
  applies to whichever of these file-mutation tests exist in each of the unit
  (`tests/unit/test_upstream_contract_diff.py`) and contract
  (`tests/contract/test_upstream_contract_diff.py`) diff modules.
- **FR-011**: Live error-mapping tests MUST be a single parametrized test over
  `(client_fixture_name, operation, expected_exc)` resolving fixtures dynamically,
  with destructive and diagnostic-bundle tests kept separate.
- **FR-012**: Live project presence-semantics cases (P-OMIT/P-EMPTY/P-SET) MUST be
  one parametrized test, with the SDK-bypassing P-NULL-HTTP case kept separate.
- **FR-013**: A live CRUD round-trip MUST be driven by resource descriptors
  `(create, get, update, delete, oracle_path, name_builder)` starting with labels
  and projects, so each additional resource is one descriptor rather than a new
  file, with the Unicode/emoji case expressed as a `name_builder` parameter. The
  seed descriptors MUST reuse the exact SDK calls already present in the current
  live tests (see Test Inventory appendix): labels use
  `live_client.labels.create/get/update/delete` with
  `oracle_path=lambda i: f"/api/labels/{i}"`; projects use
  `live_client.projects.create/get/update/delete` with
  `oracle_path=lambda i: f"/api/projects/{i}"`. This user story (US6) is
  live-only: it is exercised under the `live`/`live_smoke`/`live_extended` markers
  against a real backend and is NOT part of the offline `-m "not live"` suite; a
  weaker implementer is not expected to run or verify it offline.
- **FR-014**: Shared `make_target()`/`make_settings(tmp_path, **overrides)`
  factories MUST live in `tests/unit/conftest.py`, replacing local copies; tiny
  live-infra modules MUST be merged into their topical owners; and
  `test_transport_errors.py` MUST be folded into `test_transport.py` as a
  `(exit_code, stderr, expected_exc)` table.
- **FR-015**: All feature-002 security invariants (secrets outside the artifact
  tree, argv without shell, `KEEP_ENV` forbidden in CI, loopback-only URL) MUST
  remain asserted after consolidation.
- **FR-016**: The optimization MUST use only stdlib + pytest capabilities
  (parametrization, case tables, fixtures, manifest/fixture completeness guards)
  and MUST NOT introduce third-party test frameworks or UI-automation patterns
  (Screenplay, Page Object, pytest-bdd, hypothesis, snapshot libraries).
- **FR-017**: The full non-live suite (`uv run pytest -m "not live"`) MUST pass
  after each user story is applied, and existing CI quality gates (Ruff, strict
  mypy on `src`, the `tests.*` mypy override, coverage audits) MUST continue to
  pass. Each completeness guard MUST be introduced in the same user story as the
  table it guards (argv guard with US2, fixture and integration operation-coverage
  guards with US3, live command-execution guard with US6), so no intermediate
  between-story state leaves a guard red; the `KNOWN_ARGV_GAPS` /
  `KNOWN_FIXTURE_GAPS` / `KNOWN_LIVE_GAPS` allowlists are the mechanism that keeps
  each guard green while coverage grows.
- **FR-018**: As part of US1, the `tests.typing.*` and `tests.contract.models.*`
  entries MUST be removed from the mypy `overrides` module list in
  `pyproject.toml` when those packages are deleted; no other `pyproject.toml`
  change is in scope.
- **FR-019**: Traceability is satisfied through the manifest: every `ArgvCase`
  row is keyed by a `sdk_method` that resolves to a `ManifestEntry` (which already
  carries `source_file` provenance), and every `FakeCliCase`/`MutationSeverityCase`
  references a pinned-source golden fixture. No separate per-row provenance field
  is required.

### Key Entities

All case-table containers MUST be `@dataclass(frozen=True)` (chosen once for the
whole feature — `Callable` fields such as `check`/`sdk_call` are incompatible
with frozen `msgspec.Struct`, and a single container type removes an
implementation decision). Every field is concretely typed (no `Any`).

- **Argv case** (`ArgvCase`): resource attribute, method, args, kwargs, stdout,
  expected argv (full/exact), transport method (`"run_bytes"`|`"run_text"`),
  optional `stdin`/`timeout` (default `None`, used only for `run_bytes`), and
  `sdk_method` (dotted manifest id, used as the `pytest.param` id and by the argv
  guard).
- **Decode case** (`DecodeCase`): resource attribute, method, args, stdout,
  `check` callable, id.
- **Fake-CLI table row** (`FakeCliCase`): `fixture` (repo-relative JSON path),
  `sdk_call` callable, `check` callable, `sdk_method` (dotted manifest id, used by
  the operation-coverage guard), id.
- **Contract argv-builder** (`contract_cli.run`): a shared helper that constructs
  the full `upstream_contract.py` argv from default upstream parameters with
  per-test overrides.
- **Mutation→severity row** (`MutationSeverityCase`): mutation file,
  `must_contain`, `must_not_contain`, `unresolved_breaking` (`bool | None`), id.
- **CRUD descriptor** (`CrudDescriptor`): create/get/update/delete callables,
  `oracle_path` builder, `name_builder`, id.
- **Argv completeness guard**: a test that fails when a guard-eligible manifest
  operation (`sdk_method` non-empty AND `status != "unsupported"`) has no argv row
  and is not listed in `KNOWN_ARGV_GAPS`, or when a `KNOWN_ARGV_GAPS` entry has a
  row (stale).
- **Fixture usage guard**: a test that fails when a `tests/fixtures/json/**/*.json`
  file is not referenced by any `FakeCliCase.fixture`.
- **Integration operation-coverage guard**: a test that fails when a
  guard-eligible manifest operation is neither exercised by a `FakeCliCase`
  (matched via `FakeCliCase.sdk_method`) nor listed in `KNOWN_FIXTURE_GAPS`, or
  when a `KNOWN_FIXTURE_GAPS` entry has a `FakeCliCase` row (stale).
- **LiveContext**: the object passed to every `LiveOperation.invoke`; provided by
  a `live_ctx` fixture in `tests/live/conftest.py`. Fields (all reuse existing
  live infrastructure): `client: MulticaClient`, `oracle: DirectApiOracle`,
  `register_resource: Callable[..., None]` (for teardown), and
  `identity: TestIdentity`.
- **LiveOperation**: a `(sdk_method: str, invoke: Callable[[LiveContext], None],
  id: str)` entry for a single NON-CRUD guard-eligible operation. `invoke` sets up
  prerequisites (registering any created parent via `ctx.register_resource`) and
  calls the SDK against the real backend. Executed by `test_live_operation_executes`
  (`live_extended`).
- **Live command-execution guard**: a `live_smoke`-marked test (no backend needed)
  implementing the FR-021 formula over `E`, `T_live`, `LIVE_EXEC_EXCEPTIONS`, and
  `KNOWN_LIVE_GAPS`.
- **LIVE_EXEC_EXCEPTIONS**: `Mapping[str, LiveExecReason]` — permanently unrunnable
  operations with a closed-set reason code.
- **KNOWN_LIVE_GAPS**: `frozenset[str]` — runnable operations not yet automated;
  goal `frozenset()` at completion.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** *(secondary, non-binding target)*: Total lines across the eight
  targeted areas trend down from ~6,230 to ~3,410 (about 2,800 fewer lines,
  roughly 30% of `tests/`). These per-area figures are approximate estimates from
  the source ticket and are NOT an acceptance gate; the binding criteria are
  SC-002, SC-003, SC-005, SC-006, SC-007 (plus SC-008 under `-m live`).
- **SC-002** *(binding)*: No real coverage is lost, verified concretely by:
  (a) a baseline `uv run pytest --collect-only -q -m "not live"` captured before
  the refactor; (b) these MUST-retain guard/invariant tests still existing and
  passing afterward — `tests/contract/test_public_invariants.py::test_models_are_frozen`,
  every test in `tests/contract/test_full_cli_coverage.py`, and every feature-002
  security-invariant test in `tests/unit/test_upstream_contract_security.py` and
  the live security tests; and (c) the existing per-area coverage thresholds in
  `[tool.coverage.thresholds]` (`transport`/`models`/`resources`/`errors`) do not
  decrease.
- **SC-003** *(binding)*: Effective coverage is enforced by FOUR fail-on-gap
  guard tests — three offline: (1) unit argv-table completeness vs guard-eligible
  manifest operations (FR-005), (2) JSON-fixture usage (FR-008), (3) integration
  operation-coverage vs guard-eligible manifest operations (FR-020); and one
  live-gated: (4) live command-execution vs guard-eligible manifest operations
  (FR-021 guard runs in the live layer under `-m live_smoke`; execution under
  `-m live_extended`) — PLUS one non-guard extensibility outcome:
  adding a live resource costs one CRUD descriptor (SC-004c).
- **SC-008** *(binding)*: The live command-execution guard is green — every
  guard-eligible manifest operation is covered by `T_live`, listed in
  `LIVE_EXEC_EXCEPTIONS` with a valid reason code, or listed in `KNOWN_LIVE_GAPS`.
  At feature completion `KNOWN_LIVE_GAPS == frozenset()` (every runnable operation
  executed live via `test_live_operation_executes`/`test_crud_round_trip` under
  `-m live_extended`), and `LIVE_EXEC_EXCEPTIONS` is as small as possible. The
  guard test runs in the blocking live CI job (`-m live_smoke`) and needs no
  backend itself; actual execution of every operation is verified under
  `-m live_extended`.
- **SC-004a**: Adding coverage for a new unit CLI operation requires adding one
  `ArgvCase` row (and, if it decodes a model, one `DecodeCase` row), not a new file.
- **SC-004b**: Adding integration coverage for a new operation that has a fake-CLI
  JSON fixture requires adding one `FakeCliCase` row, not a new file.
- **SC-004c**: Adding a live CRUD resource requires adding one `CrudDescriptor`
  (~10 lines), not a new file.
- **SC-004d**: Adding live coverage for a new non-CRUD operation requires adding
  one `LiveOperation` entry to `LIVE_OPERATIONS` (and removing it from
  `KNOWN_LIVE_GAPS` if present), not a new file.
- **SC-005** *(binding)*: The integration suite runs safely in parallel with zero
  direct `os.environ` mutations in `tests/integration/resources/`.
- **SC-006** *(binding)*: No third-party test dependency is added to the project.
- **SC-007** *(binding)*: All existing CI quality gates (Ruff format/check, strict
  mypy, unit, contract, integration, coverage audits) continue to pass.

## Assumptions

- **Authoritative implementation order** is the numeric user-story order
  US1 → US2 → US3 → US4 → US5 → US6 → US7 (defined once here and in `plan.md`).
  The source ticket's suggested order (`1 → 2 → 4 → 3 → 6 → 8 → 5 → 7`) is
  historical context only and is NOT binding; where they differ, this US order
  wins.
- Improvement #9 (no third-party frameworks) is a recorded decision with no code
  action beyond the FR-016 constraint.
- The existing live infrastructure (`DirectApiOracle`, live fixtures, fake CLI
  binary) is kept as-is and reused; only the test bodies that use it are
  refactored.
- The manifest (`load_manifest()`) is the source of truth for which operations
  require argv-table coverage. Selection uses the `status` field: an operation is
  guard-eligible when `sdk_method` is non-empty and `status != "unsupported"`.
  There is no boolean `supported` field.
- Line-count figures are the ticket's approximate estimates (SC-001, secondary);
  the binding success criteria are SC-002/SC-003/SC-005/SC-006/SC-007 (plus SC-008
  under `-m live`).
- This feature changes only test/infrastructure code and a two-line mypy-override
  edit in `pyproject.toml` (FR-018); it does not modify the public SDK surface
  under `src/`.

## Appendix: Test Inventory & Extraction Rules

This appendix makes migration mechanical so an implementer never invents behavior.

### A. Deterministic extraction rule for `ArgvCase` / `DecodeCase` (US2)

For each of the 21 `tests/unit/resources/test_*.py` modules being migrated,
convert existing tests one-to-one, copying values verbatim from the source test:

- Every `transport.run_bytes.assert_called_once_with((argv...), stdin=None, timeout=None)`
  or `transport.run_text.assert_called_once_with((argv...))` becomes one
  `ArgvCase` with `expected_argv=(argv...)`, `transport_method` set accordingly,
  and `args`/`kwargs` copied from the method call under test. Partial checks
  (`assert "--x" in args` / `not in`) are converted to a full `expected_argv`
  that includes/omits the flag (FR-006).
- Every decode assertion (`result.id == ...`, `len(result) == ...`) becomes one
  `DecodeCase` with the same `stdout` payload and a `check` closure asserting the
  same values.
- `sdk_method` = the dotted client path exercised (e.g. `agents.list`); it MUST
  resolve via `resolve_dotted_path(client, sdk_method)` (reuse the existing
  helper). Where a manifest entry maps a different `sdk_method` than
  `f"{resource_attr}.{method}"`, the manifest value wins and the guard matches on
  the manifest `sdk_method`.
- Source of truth for argv when a fixture-free operation is added to close a gap:
  read the corresponding method body in `src/multica_py/resources/<name>.py` (the
  argv is constructed there deterministically) — this is reading existing code,
  not inventing behavior.
- `KNOWN_ARGV_GAPS` is seeded with the guard-eligible `sdk_method` values that
  have no existing unit argv assertion after all 21 files are converted.

### B. JSON fixture → `FakeCliCase` mapping (US3)

All 23 fixtures under `tests/fixtures/json/` and their `sdk_call` (verbatim from
the existing `tests/integration/resources/*` test that uses the fixture; for
fixtures with no current test, from the resource method named by the path):

| Fixture (under `tests/fixtures/json/`) | `sdk_call` |
| --- | --- |
| `agents/agent_list.json` | `c.agents.list()` |
| `attachments/attachment_list.json` | `c.attachments.list(...)` |
| `attachments/attachment_list_iss_001.json` | `c.attachments.list("iss_001")` |
| `auth/auth_login.json` | `c.auth.login(...)` |
| `auth/auth_status.json` | `c.auth.status()` |
| `autopilots/autopilot_list.json` | `c.autopilots.list()` |
| `configuration/config_show.json` | `c.configuration.show()` |
| `daemon/daemon_status.json` | `c.daemon.status()` |
| `issues/issue_deprioritize_iss_001.json` | `c.issues.deprioritize("iss_001")` |
| `issues/issue_get_iss_001.json` | `c.issues.get(...)` |
| `issues/issue_list.json` | `c.issues.list()` |
| `issues/issue_status_iss_001_done.json` | `c.issues.set_status("iss_001", ...)` |
| `labels/label_list.json` | `c.labels.list()` |
| `maintenance/maintenance_version.json` | `c.maintenance.version()` |
| `projects/project_list.json` | `c.projects.list()` |
| `projects/project_status_pr_001_completed.json` | `c.projects.set_status("pr_001", ...)` |
| `repositories/repo_list.json` | `c.repositories.list()` |
| `runtimes/runtime_list.json` | `c.runtimes.list()` |
| `setup/setup_cloud.json` | `c.setup.cloud(...)` |
| `skills/skill_list.json` | `c.skills.list()` |
| `squads/squad_list.json` | `c.squads.list()` |
| `users/user_list.json` | `c.users.list()` |
| `workspaces/workspace_list.json` | `c.workspaces.list()` |

The exact method names/arguments MUST be confirmed against the existing
integration test or resource source before writing the row; the table above is
the binding fixture-to-resource mapping (one row per fixture, satisfying the
FR-008 usage guard). For status-style fixtures the enum value comes from the
filename: `issue_status_iss_001_done.json` → status `done`;
`project_status_pr_001_completed.json` → status `completed` (use the corresponding
`IssueStatus`/`ProjectStatus` value). `check` default: for a fixture already used
by an existing integration test, copy that test's assertion verbatim; for a
fixture with no existing test, `check` is a minimal successful-decode assertion
(result is not `None`, and non-empty for `list` operations).

### C. Live CRUD descriptors seed (US6)

Reuse the exact calls in the current `tests/live/test_labels.py` and
`tests/live/test_projects.py`:

- `labels`: `create=lambda c, n: c.labels.create(n, color="#ff0000")`,
  `get=lambda c, i: c.labels.get(i)`,
  `update=lambda c, i: c.labels.update(i, name=<updated>, color="#00ff00")`,
  `delete=lambda c, i: c.labels.delete(i)`,
  `oracle_path=lambda i: f"/api/labels/{i}"`, plus a Unicode/emoji `name_builder`.
- `projects`: the SDK create/update use request models (`ProjectCreateRequest` /
  `ProjectUpdateRequest`), NOT positional `(name, color)` like labels. Take the
  exact create/get/update/delete calls verbatim from `tests/live/test_projects.py`
  and `src/multica_py/resources/projects.py` (e.g.
  `update=lambda c, i: c.projects.update(i, ProjectUpdateRequest(name=<updated>))`);
  `oracle_path=lambda i: f"/api/projects/{i}"`. Do not invent request fields —
  read the existing code.

### D. Maintainer output-path parametrization targets (US4)

The specific tests to convert to parametrized output-path rows are
`test_candidate_collection_is_deterministic` (deterministic A/B) and
`test_collect_persists_in_repo_output_outside_generated` (canonical vs custom
output) in `tests/contract/test_upstream_contract_collect.py`.

### E. Live registry seeding rule (US6 / FR-021)

The implementer does NOT need a pre-written list of ~100 operations. Seed
mechanically and let the guard drive completion:

1. Compute `E` (guard-eligible operations) from the manifest — the same set the
   guard uses.
2. Author `LIVE_OPERATIONS` for the operations already exercised by the current
   live suite (start with the CRUD seed of Appendix C via `CRUD_DESCRIPTORS`, then
   any non-CRUD operations that existing live tests already call), plus any new
   ones you add in US6.
3. For each remaining operation in `E`, classify it into exactly one bucket:
   - It CANNOT run in the test env → add it to `LIVE_EXEC_EXCEPTIONS` with the one
     applicable `LiveExecReason` code.
   - It CAN run but you are not automating it yet → add its `sdk_method` to
     `KNOWN_LIVE_GAPS`.
   The initial `KNOWN_LIVE_GAPS` is therefore exactly
   `E - T_live - set(LIVE_EXEC_EXCEPTIONS)`; this makes the guard green from the
   first US6 commit.
4. Closing a gap = write a `LiveOperation` (or `CrudDescriptor`) and delete that
   `sdk_method` from `KNOWN_LIVE_GAPS`; the stale-entry check enforces the deletion.
   Feature completion requires `KNOWN_LIVE_GAPS == frozenset()` (SC-008).
