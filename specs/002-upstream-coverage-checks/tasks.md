# Tasks: Versioned Upstream CLI Contract and SDK Upgrade Workflow

**Input**: Design documents from `/Users/alexandr/local_dev/repositories/my_projects/multica-py/specs/002-upstream-coverage-checks/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md, `.specify/memory/constitution.md`

**Tests**: Required by the specification and plan: golden fixtures, mutation fixtures, determinism tests, contract tests, argv/output contract tests, security tests, observer idempotency tests, runtime compatibility tests, and no-write `--check` workflow tests.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified as an independent increment.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the upstream-contract package skeleton and fixture/artifact locations used by every story.

- [ ] T001 Create upstream-contract package directories in `src/multica_py/_internal/upstream_contract/`
- [ ] T002 Create collector package directories in `src/multica_py/_internal/upstream_contract/collectors/`
- [ ] T003 Create source-evidence package directories in `src/multica_py/_internal/upstream_contract/source_evidence/`
- [ ] T004 Create generator package directories in `src/multica_py/_internal/upstream_contract/generator/`
- [ ] T005 Create fixture directories in `tests/fixtures/upstream_contract/golden/` and `tests/fixtures/upstream_contract/mutations/`
- [ ] T006 Create upgrade artifact placeholder directory in `artifacts/upstream-upgrades/`
- [ ] T007 Create approved SDK contract placeholder in `contracts/sdk-contract.yaml`
- [ ] T008 Create unified maintainer CLI adapter in `scripts/upstream_contract.py`
- [ ] T009 Create compatibility wrapper for old drift command in `scripts/check_upstream_drift.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define typed domain models, canonical artifact handling, state boundaries, and report plumbing before any story-specific behavior.

**Critical**: No user story implementation should begin until this phase is complete.

- [ ] T010 [P] Define immutable upstream contract models in `src/multica_py/_internal/upstream_contract/models.py`
- [ ] T011 [P] Define report and exit-code models in `src/multica_py/_internal/upstream_contract/reporting.py`
- [ ] T012 [P] Define atomic file IO and no-write helpers in `src/multica_py/_internal/upstream_contract/files.py`
- [ ] T013 [P] Define provenance models and full-commit validators in `src/multica_py/_internal/upstream_contract/provenance.py`
- [ ] T014 Implement schema decoding, encoding, migration, JSON Schema generation, and unknown-schema rejection in `src/multica_py/_internal/upstream_contract/schema.py`
- [ ] T015 Implement canonical JSON serialization and semantic hashing in `src/multica_py/_internal/upstream_contract/normalize.py`
- [ ] T016 Implement supported, observed, and candidate state loading rules in `src/multica_py/_internal/upstream_contract/state.py`
- [ ] T017 Implement approved SDK contract loading boundaries in `src/multica_py/_internal/upstream_contract/generator/contract.py`
- [ ] T018 Add baseline/state golden fixtures with full commits and no absolute executable paths in `tests/fixtures/upstream_contract/golden/`
- [ ] T019 [P] Add schema and canonicalization tests in `tests/unit/test_upstream_contract_schema.py`
- [ ] T020 [P] Add provenance validation tests in `tests/unit/test_upstream_contract_provenance.py`
- [ ] T021 [P] Add no-write atomic file tests in `tests/unit/test_upstream_contract_files.py`
- [ ] T022 [P] Add approved-contract boundary tests in `tests/unit/test_upstream_contract_generator.py`

**Checkpoint**: The repository can parse, validate, canonicalize, hash, and render upstream contract artifacts without collecting or diffing live data.

---

## Phase 3: User Story 1 - Verify Supported Upstream Baseline (Priority: P1) MVP

**Goal**: Provide one offline quality gate that validates supported baseline artifacts against SDK coverage decisions.

**Independent Test**: Run `uv run python scripts/upstream_contract.py check --format human` and `uv run python scripts/upstream_contract.py check --format json --output /tmp/upstream-contract-report.json` using checked-in fixtures only; clean fixtures exit 0, gap fixtures exit 2, invalid artifacts exit 3.

### Tests for User Story 1

- [ ] T023 [P] [US1] Add coverage-level fixture rows for typed, raw, process, unsupported, legacy, and incomplete decisions in `tests/fixtures/upstream_contract/golden/coverage-manifest-v2.json`
- [ ] T024 [P] [US1] Add offline supported-contract fixture with command args, flags, aliases, execution, output, and provenance in `tests/fixtures/upstream_contract/golden/supported-cli-contract-v2.json`
- [ ] T025 [P] [US1] Add coverage policy unit tests in `tests/unit/test_upstream_contract_coverage.py`
- [ ] T026 [P] [US1] Add machine report rendering tests in `tests/unit/test_upstream_contract_reporting.py`
- [ ] T027 [P] [US1] Add offline gate contract tests in `tests/contract/test_upstream_contract_check.py`
- [ ] T028 [P] [US1] Add raw coverage safety tests for `Sequence[str]` and no shell interpolation in `tests/unit/test_upstream_contract_raw.py`
- [ ] T029 [P] [US1] Add typed argv contract tests for exact process argument sequences in `tests/contract/test_upstream_contract_argv.py`
- [ ] T030 [P] [US1] Add typed output fixture and strict-decoder negative tests in `tests/contract/test_upstream_contract_output.py`

### Implementation for User Story 1

- [ ] T031 [US1] Implement coverage decision validation and coverage-level counts in `src/multica_py/_internal/upstream_contract/coverage.py`
- [ ] T032 [US1] Implement operation ID, versioned binding, alias, and explicit shared-implementation validation in `src/multica_py/_internal/upstream_contract/coverage.py`
- [ ] T033 [US1] Implement typed input/output contract evidence requirements in `src/multica_py/_internal/upstream_contract/coverage.py`
- [ ] T034 [US1] Implement raw coverage safety policy in `src/multica_py/_internal/upstream_contract/coverage.py`
- [ ] T035 [US1] Implement human output rendered from CoverageReport in `src/multica_py/_internal/upstream_contract/reporting.py`
- [ ] T036 [US1] Implement `check` command, `--format`, `--output`, and exit-code mapping in `scripts/upstream_contract.py`
- [ ] T037 [US1] Wire `scripts/check_upstream_drift.py` to the new offline check behavior in `scripts/check_upstream_drift.py`
- [ ] T038 [US1] Update generated CLI manifest compatibility or migration inputs in `src/multica_py/_generated/cli_manifest.json`
- [ ] T039 [US1] Update coverage documentation for typed/raw/process/unsupported/legacy/incomplete states in `docs/cli-coverage.md`

**Checkpoint**: User Story 1 is complete when the offline gate is deterministic, network-free, and distinguishes unsupported/incomplete/raw rows correctly.

---

## Phase 4: User Story 2 - Refresh a Candidate Contract for a New Multica Release (Priority: P1)

**Goal**: Collect a deterministic candidate semantic contract from selected release evidence without changing SDK coverage decisions.

**Independent Test**: Run `uv run python scripts/upstream_contract.py collect --binary tests/fixtures/fake_multica.py --output /tmp/candidate-contract.json`; repeated runs for unchanged inputs produce canonical byte-identical semantic content, incomplete traversal exits 4, source/binary mismatch exits 5.

### Tests for User Story 2

- [ ] T040 [P] [US2] Add fake exporter fixture for `multica __contract --format json` in `tests/fixtures/upstream_contract/golden/exporter-contract.json`
- [ ] T041 [P] [US2] Add help-parser fallback fixture with degraded trust metadata in `tests/fixtures/upstream_contract/golden/help-parser-contract.json`
- [ ] T042 [P] [US2] Add source-evidence fixture for declarative Cobra facts and review items in `tests/fixtures/upstream_contract/golden/source-evidence.json`
- [ ] T043 [P] [US2] Add binary collector tests for exporter, release asset, Go helper, fallback, timeout, and incomplete traversal in `tests/unit/test_upstream_contract_collector.py`
- [ ] T044 [P] [US2] Add source extractor tests for known declarative patterns and unknown-pattern review items in `tests/unit/test_upstream_contract_source_evidence.py`
- [ ] T045 [P] [US2] Add collector security tests for checksum mismatch, sanitized environment, and output limits in `tests/unit/test_upstream_contract_security.py`
- [ ] T046 [P] [US2] Add candidate determinism tests for same-input byte identity in `tests/contract/test_upstream_contract_collect.py`

### Implementation for User Story 2

- [ ] T047 [US2] Implement preferred exporter collection in `src/multica_py/_internal/upstream_contract/collectors/binary.py`
- [ ] T048 [US2] Implement release asset and Go helper collection hooks with trust-level metadata in `src/multica_py/_internal/upstream_contract/collectors/binary.py`
- [ ] T049 [US2] Implement help-parser fallback as degraded mode with review items in `src/multica_py/_internal/upstream_contract/collectors/binary.py`
- [ ] T050 [US2] Implement collector security policy, checksum validation, timeout, environment sanitization, and output limits in `src/multica_py/_internal/upstream_contract/collectors/security.py`
- [ ] T051 [US2] Implement source evidence extraction for declarative Cobra facts in `src/multica_py/_internal/upstream_contract/source_evidence/extract.py`
- [ ] T052 [US2] Implement source/binary comparison and mismatch reporting in `src/multica_py/_internal/upstream_contract/collectors/source.py`
- [ ] T053 [US2] Implement tag-to-commit verification and no absolute executable path checks in `src/multica_py/_internal/upstream_contract/provenance.py`
- [ ] T054 [US2] Implement `collect` command, `--binary`, `--write`, `--dry-run`, `--output`, and collector exit codes in `scripts/upstream_contract.py`

**Checkpoint**: User Story 2 is complete when candidate collection is reproducible, provenance-rich, and unable to silently promote partial or degraded evidence.

---

## Phase 5: User Story 3 - Understand Upstream Impact Before SDK Work (Priority: P1)

**Goal**: Compare supported and candidate contracts semantically and map each non-documentation change to SDK operations or unresolved decisions.

**Independent Test**: Run `uv run python scripts/upstream_contract.py diff --from tests/fixtures/upstream_contract/golden/supported-cli-contract-v2.json --to tests/fixtures/upstream_contract/mutations/required-flag-added.json --format human`; required flag additions are breaking, help-only changes are documentation-only, possible renames remain suggestions.

### Tests for User Story 3

- [ ] T055 [P] [US3] Add mutation fixtures for command added/removed, optional flag added, required argument added, flag removed, flag renamed, type changed, default changed, alias changed, and hidden/deprecated transitions in `tests/fixtures/upstream_contract/mutations/`
- [ ] T056 [P] [US3] Add mutation fixtures for output field added, output field removed, output type changed, documentation-only change, provenance-only change, and source/binary disagreement in `tests/fixtures/upstream_contract/mutations/`
- [ ] T057 [P] [US3] Add semantic diff unit tests in `tests/unit/test_upstream_contract_diff.py`
- [ ] T058 [P] [US3] Add impact-map tests linking diff entries to operation IDs and unresolved mappings in `tests/unit/test_upstream_contract_impact.py`
- [ ] T059 [P] [US3] Add diff command contract tests for exit codes and JSON report output in `tests/contract/test_upstream_contract_diff.py`

### Implementation for User Story 3

- [ ] T060 [US3] Implement supported-to-candidate semantic diff and severity classification in `src/multica_py/_internal/upstream_contract/diff.py`
- [ ] T061 [US3] Implement rename and move suggestion heuristics without automatic operation identity changes in `src/multica_py/_internal/upstream_contract/diff.py`
- [ ] T062 [US3] Implement output contract change classification for optional additions, removals, and type changes in `src/multica_py/_internal/upstream_contract/diff.py`
- [ ] T063 [US3] Implement SDK impact mapping from diff entries to operation IDs and unresolved mappings in `src/multica_py/_internal/upstream_contract/impact.py`
- [ ] T064 [US3] Implement `diff` command, `--from`, `--to`, `--format`, and unresolved-breaking exit behavior in `scripts/upstream_contract.py`
- [ ] T065 [US3] Update coverage gate to consume candidate diff status when candidate artifacts exist in `src/multica_py/_internal/upstream_contract/coverage.py`

**Checkpoint**: User Story 3 is complete when every semantic change appears once in the diff, has a severity, and maps to affected SDK operations or an unresolved state.

---

## Phase 6: User Story 4 - Prepare a Reviewable Upgrade Bundle (Priority: P2)

**Goal**: Generate deterministic review context, incomplete suggestions, and verification work items for a candidate release.

**Independent Test**: Run `uv run python scripts/upstream_contract.py prepare-upgrade --candidate /tmp/candidate-contract.json --output-dir artifacts/upstream-upgrades/v0.4.2..v0.4.3` twice; the second run produces no diff, suggestions remain incomplete, and generated facts are separated from maintainer decisions.

### Tests for User Story 4

- [ ] T066 [P] [US4] Add upgrade bundle golden fixture layout in `tests/fixtures/upstream_contract/golden/upgrade-bundle/`
- [ ] T067 [P] [US4] Add upgrade suggestion tests for incomplete manifest rows, test suggestions, docs suggestions, and changelog fragments in `tests/unit/test_upstream_contract_suggestions.py`
- [ ] T068 [P] [US4] Add upgrade bundle determinism and idempotency tests in `tests/contract/test_upstream_contract_prepare_upgrade.py`
- [ ] T069 [P] [US4] Add apply-manifest-suggestions tests proving applied rows remain incomplete in `tests/contract/test_upstream_contract_apply_suggestions.py`

### Implementation for User Story 4

- [ ] T070 [US4] Implement incomplete manifest, test, documentation, and changelog suggestion generation in `src/multica_py/_internal/upstream_contract/suggestions.py`
- [ ] T071 [US4] Implement deterministic upgrade bundle writer in `src/multica_py/_internal/upstream_contract/upgrade.py`
- [ ] T072 [US4] Implement `prepare-upgrade` command and idempotent output handling in `scripts/upstream_contract.py`
- [ ] T073 [US4] Implement explicit `apply-manifest-suggestions` command that keeps rows incomplete in `scripts/upstream_contract.py`
- [ ] T074 [US4] Document generated facts versus maintainer decisions in `docs/cli-coverage.md`

**Checkpoint**: User Story 4 is complete when upgrade preparation is repeatable and creates reviewable context without approving SDK coverage.

---

## Phase 7: User Story 5 - Observe New Releases Without Breaking Offline CI (Priority: P2)

**Goal**: Add non-blocking release observation that prepares candidate context without changing supported baseline or ordinary PR gates.

**Independent Test**: Run observer tests with mocked release metadata; repeated runs for the same release reuse the same tracking identity, checksum mismatch rejects before execution, and supported baseline artifacts do not change.

### Tests for User Story 5

- [ ] T075 [P] [US5] Add mocked release metadata fixtures in `tests/fixtures/upstream_contract/golden/releases.json`
- [ ] T076 [P] [US5] Add observer idempotency and superseded-candidate tests in `tests/unit/test_upstream_contract_observer.py`
- [ ] T077 [P] [US5] Add workflow policy tests for offline PR gate separation in `tests/contract/test_upstream_contract_workflows.py`
- [ ] T078 [P] [US5] Add GitHub Actions static checks for labels, status, concurrency, and pinned actions in `tests/contract/test_upstream_contract_actions.py`

### Implementation for User Story 5

- [ ] T079 [US5] Implement release observation state transitions in `src/multica_py/_internal/upstream_contract/observer.py`
- [ ] T080 [US5] Implement deterministic issue/PR identity, `upstream-update` label, `needs-maintainer-decision` status, and superseded-candidate policy in `src/multica_py/_internal/upstream_contract/observer.py`
- [ ] T081 [US5] Implement `observe` command with `--dry-run` and non-promoting behavior in `scripts/upstream_contract.py`
- [ ] T082 [US5] Add non-blocking scheduled observer workflow with release-keyed concurrency in `.github/workflows/upstream-contract-observer.yml`
- [ ] T083 [US5] Ensure existing PR/push workflows run only offline supported checks in `.github/workflows/ci.yml`

**Checkpoint**: User Story 5 is complete when scheduled observation can detect release lag and prepare review work without mutating supported baseline or breaking offline CI.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Runtime compatibility, documentation, end-to-end validation, and cleanup after story increments.

- [ ] T084 [P] Implement runtime compatibility matrix loading in `src/multica_py/_internal/upstream_contract/compatibility.py`
- [ ] T085 [P] Implement runtime CLI version/build metadata read-once diagnostics in `src/multica_py/compatibility.py`
- [ ] T086 [P] Add runtime compatibility tests for read-once warning, override path, and supported range text in `tests/unit/test_compat_policy.py`
- [ ] T087 [P] Generate compatibility documentation from the compatibility matrix in `docs/compatibility.md`
- [ ] T088 [P] Update maintainer quickstart commands in `docs/contributing.md`
- [ ] T089 [P] Update source-link audit coverage for semantic contract provenance in `scripts/audit_source_links.py`
- [ ] T090 Add end-to-end quickstart validation test covering check, collect, diff, prepare-upgrade, and observe dry-run in `tests/contract/test_upstream_contract_quickstart.py`
- [ ] T091 [P] Add readable summary and under-30-second offline gate budget tests for SC-001 in `tests/contract/test_upstream_contract_check.py`
- [ ] T092 [P] Add approved SDK contract tests for presence semantics, enum policy, normalized imperative constraints, and positive/negative evidence for FR-028 in `tests/unit/test_upstream_contract_generator.py`
- [ ] T093 Implement approved SDK contract validation for omitted/null/empty/zero/false semantics, enum approval, and normalized constraint categories for FR-028 in `src/multica_py/_internal/upstream_contract/generator/contract.py`
- [ ] T094 [P] Add exporter-vs-help-parser mismatch classification tests for SC-017 in `tests/unit/test_upstream_contract_collector.py`
- [ ] T095 Implement exporter-vs-help-parser mismatch classification separate from SDK coverage gaps for SC-017 in `src/multica_py/_internal/upstream_contract/collectors/binary.py`
- [ ] T096 [P] Add PromotionDecision promote/reject workflow tests for FR-030 in `tests/contract/test_upstream_contract_promotion.py`
- [ ] T097 Implement PromotionDecision artifact validation and explicit promote/reject commands for FR-030 in `src/multica_py/_internal/upstream_contract/promotion.py`
- [ ] T098 Wire `promote` and `reject` commands to atomic state updates and refusal cases for FR-030 in `scripts/upstream_contract.py`
- [ ] T099 [P] Add failed upgrade write, superseded candidate, and rerun recovery requirement tests for FR-024 and US5 in `tests/unit/test_upstream_contract_observer.py`
- [ ] T100 Implement recovery and superseded-candidate state rules for failed writes and reruns in `src/multica_py/_internal/upstream_contract/observer.py`
- [ ] T101 [P] Add generated JSON Schema and external validation fixture tests for FR-017 in `tests/unit/test_upstream_contract_schema.py`
- [ ] T102 Document checked-in artifact locations, approved contract boundaries, and generated artifact boundaries in `docs/cli-coverage.md`
- [ ] T103 Update per-FR/SC traceability matrix for implementation-critical requirements in `specs/002-upstream-coverage-checks/tasks.md`
- [ ] T104 [P] Add implementation oracle contract reference fixtures in `tests/fixtures/upstream_contract/golden/oracles/`
- [ ] T105 [P] Add state transition table tests from `contracts/implementation-oracles.md` in `tests/unit/test_upstream_contract_state.py`
- [ ] T106 Implement fixed collector method order and trust-level promotion eligibility from `contracts/implementation-oracles.md` in `src/multica_py/_internal/upstream_contract/collectors/binary.py`
- [ ] T107 [P] Add exhaustive diff severity table tests from `contracts/implementation-oracles.md` in `tests/unit/test_upstream_contract_diff.py`
- [ ] T108 Implement exhaustive diff severity table from `contracts/implementation-oracles.md` in `src/multica_py/_internal/upstream_contract/diff.py`
- [ ] T109 [P] Add machine report schema file generation tests for `contracts/schema/upstream-report-v1.schema.json` in `tests/unit/test_upstream_contract_reporting.py`
- [ ] T110 [P] Add local upgrade directory layout tests from `contracts/implementation-oracles.md` in `tests/contract/test_upstream_contract_prepare_upgrade.py`
- [ ] T111 Run `uv run ruff format --check .` and fix formatting issues in `src/`, `tests/`, and `scripts/`
- [ ] T112 Run `uv run ruff check .` and fix lint issues in `src/`, `tests/`, and `scripts/`
- [ ] T113 Run `uv run mypy --namespace-packages --explicit-package-bases -p multica_py` and fix package typing issues in `src/multica_py/`
- [ ] T114 Run `uv run mypy tests scripts --ignore-missing-imports --follow-imports=silent --check-untyped-defs` and fix typing issues in `tests/` and `scripts/`
- [ ] T115 Run `uv run pytest` and fix any failing tests in `src/`, `tests/`, and `scripts/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: no dependencies.
- **Phase 2 Foundational**: depends on Phase 1; blocks all user stories.
- **US1 Offline Gate**: depends on Phase 2; MVP scope.
- **US2 Candidate Collection**: depends on Phase 2; can run after or alongside US1 once shared models are stable.
- **US3 Semantic Diff and Impact**: depends on Phase 2 and benefits from US1 coverage models; required before candidate promotion.
- **US4 Upgrade Bundle**: depends on US2 collection outputs and US3 diff/impact.
- **US5 Observer**: depends on US2 collector/security and US4 bundle behavior.
- **Phase 8 Polish**: depends on the stories needed for the delivery slice.

### User Story Dependencies

- **US1 (P1)**: starts after Phase 2 and delivers the first merge-blocking value.
- **US2 (P1)**: starts after Phase 2 and remains independent because it writes candidate artifacts only.
- **US3 (P1)**: starts after Phase 2; maps to US1/US2 artifacts but can be tested with fixtures.
- **US4 (P2)**: starts after US2 and US3.
- **US5 (P2)**: starts after US2 and US4.

### Parallel Opportunities

- T010-T013 can run in parallel after directories exist.
- T019-T022 can run in parallel once foundational model shapes are agreed.
- US1 tests T023-T030 can run in parallel before implementation.
- US2 tests T040-T046 can run in parallel before collector implementation.
- US3 mutation fixture and diff tests T055-T059 can run in parallel.
- US4 tests T066-T069 can run in parallel after bundle fixture shape is known.
- US5 tests T075-T078 can run in parallel after observer policy is fixed.
- Polish docs/tests T084-T105 can run in parallel after the relevant story APIs settle.

---

## Parallel Example: User Story 1

```bash
Task: "T025 [P] [US1] Add coverage policy unit tests in tests/unit/test_upstream_contract_coverage.py"
Task: "T026 [P] [US1] Add machine report rendering tests in tests/unit/test_upstream_contract_reporting.py"
Task: "T027 [P] [US1] Add offline gate contract tests in tests/contract/test_upstream_contract_check.py"
Task: "T028 [P] [US1] Add raw coverage safety tests for Sequence[str] and no shell interpolation in tests/unit/test_upstream_contract_raw.py"
Task: "T029 [P] [US1] Add typed argv contract tests for exact process argument sequences in tests/contract/test_upstream_contract_argv.py"
Task: "T030 [P] [US1] Add typed output fixture and strict-decoder negative tests in tests/contract/test_upstream_contract_output.py"
```

## Parallel Example: User Story 2

```bash
Task: "T043 [P] [US2] Add binary collector tests for exporter, release asset, Go helper, fallback, timeout, and incomplete traversal in tests/unit/test_upstream_contract_collector.py"
Task: "T044 [P] [US2] Add source extractor tests for known declarative patterns and unknown-pattern review items in tests/unit/test_upstream_contract_source_evidence.py"
Task: "T045 [P] [US2] Add collector security tests for checksum mismatch, sanitized environment, and output limits in tests/unit/test_upstream_contract_security.py"
Task: "T046 [P] [US2] Add candidate determinism tests for same-input byte identity in tests/contract/test_upstream_contract_collect.py"
```

## Parallel Example: User Story 3

```bash
Task: "T055 [P] [US3] Add mutation fixtures for command added/removed, optional flag added, required argument added, flag removed, flag renamed, type changed, default changed, alias changed, and hidden/deprecated transitions in tests/fixtures/upstream_contract/mutations/"
Task: "T056 [P] [US3] Add mutation fixtures for output field added, output field removed, output type changed, documentation-only change, provenance-only change, and source/binary disagreement in tests/fixtures/upstream_contract/mutations/"
Task: "T057 [P] [US3] Add semantic diff unit tests in tests/unit/test_upstream_contract_diff.py"
Task: "T058 [P] [US3] Add impact-map tests linking diff entries to operation IDs and unresolved mappings in tests/unit/test_upstream_contract_impact.py"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 only.
3. Validate with `uv run python scripts/upstream_contract.py check --format human`, `uv run python scripts/upstream_contract.py check --format json --output /tmp/upstream-contract-report.json`, and the US1 tests.
4. Stop for review before enabling collection, observer, or upgrade automation.

### Incremental Delivery

1. US1: reliable offline semantic gate.
2. US2: deterministic candidate collection with provenance and trust levels.
3. US3: semantic diff and impact mapping.
4. US4: upgrade bundle and explicit suggestion application.
5. US5: non-blocking scheduled observer.
6. Polish: runtime compatibility diagnostics, docs, and full quality gate.

### Traceability Summary

- **FR-001**: T013, T018, T020, T035, T053.
- **FR-002**: T013, T020, T053.
- **FR-003**: T047-T054.
- **FR-004**: T040-T046, T047-T054, T106.
- **FR-005**: T023-T027, T031-T036.
- **FR-006**: T023, T025, T031, T039.
- **FR-007**: T025, T027, T031, T036.
- **FR-008**: T026, T035, T036, T091.
- **FR-009**: T067, T070, T072.
- **FR-010**: T067, T069, T070, T073.
- **FR-011**: T027, T036, T077, T083.
- **FR-012**: T046, T054.
- **FR-013**: T016, T079-T081, T105.
- **FR-014**: T024, T040-T049, T055-T062, T106.
- **FR-015**: T055-T064, T107-T108.
- **FR-016**: T057, T061, T063.
- **FR-017**: T014, T018-T020, T053, T101, T104, T109.
- **FR-018**: T015, T046, T068, T110.
- **FR-019**: T023, T031, T039.
- **FR-020**: T029-T033, T092-T093.
- **FR-021**: T011, T026, T035-T036, T059, T064.
- **FR-022**: T075-T083, T105.
- **FR-023**: T045, T050, T075, T078, T082.
- **FR-024**: T066-T073, T099-T100, T110.
- **FR-025**: T084-T087.
- **FR-026**: T032, T058, T063.
- **FR-027**: T042, T044, T051.
- **FR-028**: T092-T093.
- **FR-029**: T011, T026, T035.
- **FR-030**: T096-T098.
- **FR-031**: T028, T034, T039.
- **FR-032**: T040-T041, T043, T047-T049, T094-T095, T106.
- **FR-033**: T084-T087.
- **SC-001**: T026, T035, T091.
- **SC-002**: T025, T027, T031.
- **SC-003**: T023, T025, T031.
- **SC-004**: T046, T053-T054.
- **SC-005**: T067, T070, T073.
- **SC-006**: T055, T057, T060, T107-T108.
- **SC-007**: T056-T057, T060, T107-T108.
- **SC-008**: T015, T046, T068.
- **SC-009**: T043, T045, T050.
- **SC-010**: T075-T083, T105.
- **SC-011**: T057-T064, T107-T108.
- **SC-012**: T029-T033, T092-T093.
- **SC-013**: T068, T071-T072, T076, T080, T110.
- **SC-014**: T045, T050, T075.
- **SC-015**: T057-T064, T107-T108.
- **SC-016**: T028, T034, T039.
- **SC-017**: T094-T095, T106.
- **SC-018**: T084-T087.

## Format Validation

All executable tasks above use the required checklist format: `- [ ] T### [P?] [US?] Description with file path`.
