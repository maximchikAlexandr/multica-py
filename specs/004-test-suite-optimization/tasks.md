---

description: "Task list for Test Suite Optimization (feature 004)"
---

# Tasks: Test Suite Optimization

**Input**: Design documents from `/specs/004-test-suite-optimization/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/test-harness.md, quickstart.md

**Tests**: This feature's deliverable IS the test suite. There are no separate
"write a test for the code" tasks — every task below edits `tests/` (plus a
two-line `pyproject.toml` mypy-override change). `src/multica_py/**` is unchanged.

**Organization**: Tasks are grouped by user story. The authoritative
implementation order is **US1 → US2 → US3 → US4 → US5 → US6 → US7** (plan.md;
the source ticket order is non-binding). Each user story leaves the offline
`-m "not live"` suite green (FR-017) and is independently mergeable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1–US7; Setup/Foundational/Polish have no story label

## Path Conventions

Single-project layout. All changes under `tests/` and `pyproject.toml`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Capture the SC-002 no-coverage-loss baseline before any change.

- [ ] T001 Capture offline baseline node IDs to `/tmp/004-baseline-nodeids.txt` via `uv run pytest --collect-only -q -m "not live" > /tmp/004-baseline-nodeids.txt` and record the collected count (~449) in the PR description (SC-002; quickstart Prerequisites)
- [ ] T002 [P] Record the MUST-retain node IDs and current `[tool.coverage.thresholds]` values from `pyproject.toml` (`tests/contract/test_public_invariants.py::test_models_are_frozen`, all of `tests/contract/test_full_cli_coverage.py`, feature-002 security invariants in `tests/unit/test_upstream_contract_security.py`) as the SC-002 acceptance set
- [ ] T003 [P] Establish the tooling baseline: `git config core.hooksPath .githooks`, then `uv run mypy src && uv run mypy tests` and `uv run ruff format --check . && uv run ruff check .` all pass

**Checkpoint**: Baseline recorded; any later regression is now detectable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: One shared manifest helper reused by all three offline/live guards, so the guard-eligible predicate is defined once (reuse-first rule).

**⚠️ CRITICAL**: Blocks the guards in US2, US3, and US6.

- [ ] T004 Add a shared `guard_eligible_operations()` helper (returns the set `E` of `ManifestEntry.sdk_method` where `sdk_method` is non-empty AND `status != "unsupported"`) in a shared test-support module (e.g. `tests/_manifest_support.py`), driven by `load_manifest()`; this single definition is imported by every completeness guard (FR-005/FR-020/FR-021)

**Checkpoint**: Guard-eligible set is available; user stories can begin.

---

## Phase 3: User Story 1 - Remove dead, tautological, and duplicated tests (Priority: P1) 🎯 MVP

**Goal**: Delete tests that cannot fail or fully duplicate a broader invariant, relocating the few genuine assertions, with no real coverage lost.

**Independent Test**: After deletions/relocations, `uv run pytest -m "not live"` passes and the frozen-msgspec + full-CLI-coverage invariants still run over all modules.

- [ ] T005 [US1] Relocate verbatim `test_invalid_value_rejected`, `test_issue_assignment_request_rejects_multiple_targets`, and `test_issue_reorder_request_rejects_multiple_targets` from `tests/unit/resources/test_mutually_exclusive.py` into `tests/unit/resources/test_issues.py` (FR-002)
- [ ] T006 [US1] Delete `tests/unit/resources/test_mutually_exclusive.py` after T005 relocation (the six description/dispatch tautologies are dropped; their coverage is restored as `ArgvCase` rows in US2/T013) (FR-002)
- [ ] T007 [P] [US1] Delete `tests/unit/resources/test_labels.py` (asserts a msgspec default — a library guarantee) (FR-002)
- [ ] T008 [P] [US1] Delete the entire `tests/contract/models/` directory (10 per-module duplicates + `__init__.py`) (FR-001)
- [ ] T009 [P] [US1] Delete the entire `tests/typing/` package including empty `cases/` (FR-003)
- [ ] T010 [US1] Remove the `tests.contract.models.*` and `tests.typing.*` entries from the mypy `overrides` module list in `pyproject.toml` (FR-018)
- [ ] T011 [US1] Verify offline suite + `uv run mypy src && uv run mypy tests` are green, and `tests/contract/test_public_invariants.py::test_models_are_frozen` still enforces the invariant over all `multica_py.models` modules

**Checkpoint**: Suite is smaller and still green; MUST-retain invariants intact.

---

## Phase 4: User Story 2 - Table-driven unit resource tests with a manifest completeness guard (Priority: P1)

**Goal**: Collapse `tests/unit/resources/` into shared parametrized tables + fixtures, and add the argv-completeness guard.

**Independent Test**: The two parametrized tests plus the guard run; coverage is at least preserved; the guard fails when a guard-eligible operation has no argv row.

- [ ] T012 [US2] Create `tests/unit/resources/conftest.py` with a shared `mock_transport` fixture and a `raw_result` factory (full `RawCommandResult` constructor) per contracts/test-harness.md (US2)
- [ ] T013 [US2] Create `tests/unit/resources/cases.py` with `@dataclass(frozen=True)` `ArgvCase` and `DecodeCase` and their tables; migrate every existing per-file resource case verbatim per Appendix A (incl. `test_issue_comments.py`/`test_issue_labels.py`/`test_issue_metadata.py`), and add the three `description`-union `ArgvCase` rows (Inline/File/Stdin) required by FR-006a; preserve every deleted decode assertion as a `DecodeCase` row (FR-004/FR-004a)
- [ ] T014 [US2] Create `tests/unit/resources/test_operations.py` with `test_command_argv` (parametrized over `ArgvCase`, asserting the complete `expected_argv` incl. `stdin`/`timeout` per FR-006), `test_decode` (parametrized over `DecodeCase`), and the guard `test_every_guard_eligible_operation_has_argv_case` using `guard_eligible_operations()` and `KNOWN_ARGV_GAPS` (FR-005/FR-006)
- [ ] T015 [US2] Seed `KNOWN_ARGV_GAPS: frozenset[str]` with exactly the guard-eligible operations that still have no argv row, each with a short inline reason, so the guard is green (FR-005/FR-017)
- [ ] T016 [US2] Delete all remaining `tests/unit/resources/test_*.py` EXCEPT `tests/unit/resources/test_issues.py` after their cases are migrated (FR-004)
- [ ] T017 [US2] Verify the guard fails (temporarily remove one row to confirm it names the operation, then restore) and that offline suite + mypy are green

**Checkpoint**: Adding a unit operation = one `ArgvCase` row (SC-004a); argv guard enforced.

---

## Phase 5: User Story 3 - Fixture-based integration tests over every JSON fixture (Priority: P2)

**Goal**: Parallel-safe integration tests over one `FakeCliCase` table, with fixture-usage and operation-coverage guards.

**Independent Test**: One table replaces the 17 per-file tests; the fixture-usage guard fails on an unused fixture; the operation-coverage guard fails on an uncovered eligible op.

- [ ] T018 [US3] Add a `fake_cli_client` fixture to `tests/integration/conftest.py` that sets `PATH` through pytest (monkeypatch), removing all direct `os.environ` mutation (FR-007/SC-005)
- [ ] T019 [US3] Create `tests/integration/resources/test_fake_cli_operations.py` with a `@dataclass(frozen=True)` `FakeCliCase` table — one row per JSON fixture per Appendix B (incl. `set_status`, `deprioritize`), each carrying `sdk_method`, `sdk_call`, and `check` — and a parametrized `test_fake_cli_operation` (FR-008)
- [ ] T020 [US3] Add the fixture-usage guard (every `tests/fixtures/json/**/*.json` is referenced by a row) and the operation-coverage guard `test_every_guard_eligible_operation_has_fixture_or_gap` (uses `guard_eligible_operations()` + `KNOWN_FIXTURE_GAPS`, matched via `FakeCliCase.sdk_method`) (FR-008/FR-020)
- [ ] T021 [US3] Seed `KNOWN_FIXTURE_GAPS: frozenset[str]` with the uncovered guard-eligible operations, each with an inline reason, so the guard is green (FR-020/FR-017)
- [ ] T022 [US3] Delete the 17 `tests/integration/resources/test_*.py` modules after migration (FR-008)
- [ ] T023 [US3] Verify no `os.environ` mutation remains in `tests/integration/resources/`, both guards fail on a seeded gap (spot check then restore), and offline suite is green

**Checkpoint**: Integration coverage bound to the manifest; two offline guards enforced.

---

## Phase 6: User Story 4 - Shared harness for maintainer upstream-contract tests (Priority: P2)

**Goal**: A contract-test conftest so per-test bodies contain only meaningful assertions.

**Independent Test**: Collect/check/prepare-upgrade/promotion/quickstart/apply-suggestions tests run on the shared harness with unchanged behavior.

- [ ] T024 [US4] Create `tests/contract/conftest.py` with a `fake_upstream_cli` fixture, a `contract_cli` argv-builder helper (fills default `upstream_contract.py` parameters), and a `preserved_generated_state` auto-fixture (backs up/restores `upstream_state.json` and removes generated candidate contracts) (FR-009)
- [ ] T025 [US4] Rewrite `tests/contract/test_upstream_contract_*.py` onto the conftest, deleting the repeated ~30-line argv blocks and per-test `try/finally` state handling (FR-009)
- [ ] T026 [US4] Parametrize output-path rows for `test_candidate_collection_is_deterministic` and `test_collect_persists_in_repo_output_outside_generated` in `tests/contract/test_upstream_contract_collect.py` (Appendix D)
- [ ] T027 [US4] Verify behavior unchanged and offline suite + mypy are green

**Checkpoint**: Upstream-contract tests share one harness.

---

## Phase 7: User Story 5 - Parametrized contract-diff severity tests (Priority: P3)

**Goal**: One severity table replaces six near-identical diff tests.

**Independent Test**: The five file-mutation rows each yield their expected severity; genuinely specific tests remain separate.

- [ ] T028 [US5] Add a `@dataclass(frozen=True)` `MutationSeverityCase` table of exactly five file-mutation rows (`required-flag-added`, `help-text-changed` [severities ⊆ {`doc_only`,`provenance_only`}], `command-added`, `command-removed`, `optional-flag-added`) and a parametrized `test_mutation_severity` in the unit and contract diff modules (`tests/unit/test_upstream_contract_diff.py`, `tests/contract/test_upstream_contract_diff.py`) (FR-010)
- [ ] T029 [US5] Keep the `command-renamed` rename-heuristic test, summary-reconciliation tests, and manual `SemanticCLIContract`-assembly tests as separate tests (not in the table) (FR-010)
- [ ] T030 [US5] Verify offline suite + mypy are green

**Checkpoint**: Severity classification is one table.

---

## Phase 8: User Story 6 - Full live command coverage: CRUD matrix, command execution, presence, errors (Priority: P3)

**Goal**: Parametrized live CRUD/errors/presence + a live invocation registry and the live command-execution guard so every command/resource is exercised live (or explicitly allowlisted).

**Independent Test**: Live guard passes under `-m live_smoke`; full execution runs under `-m live_extended`; `-m "not live" --collect-only` lists no `tests/live/*` node.

- [ ] T031 [US6] Add a `live_ctx` fixture to `tests/live/conftest.py` returning a `LiveContext` (`client`, `oracle`, `register_resource`, `identity`), reusing the existing live infrastructure (data-model.md)
- [ ] T032 [US6] Create `tests/live/crud_descriptors.py` (`CRUD_DESCRIPTORS` seed for `labels` and `projects` per Appendix C) and `tests/live/test_crud.py` (module-level `pytestmark = [pytest.mark.live, pytest.mark.live_extended]`; parametrized `test_crud_round_trip` using `live_ctx`; Unicode/emoji as a `name_builder` variant) (FR-013/SC-004c)
- [ ] T033 [US6] Parametrize `tests/live/test_errors.py` (error-mapping table `(client_fixture_name, operation, expected_exc)`) and `tests/live/test_projects.py` (presence P-OMIT/P-EMPTY/P-SET), keeping destructive/diagnostic-bundle/synthetic-wrapper/P-NULL-HTTP separate, and fold `tests/live/test_labels.py` into `crud_descriptors.py`/`test_crud.py` (FR-011/FR-012)
- [ ] T034 [US6] Create `tests/live/live_operations.py` with `LIVE_OPERATIONS` (non-CRUD `LiveOperation` entries), `LIVE_EXEC_EXCEPTIONS: Mapping[str, LiveExecReason]`, `KNOWN_LIVE_GAPS: frozenset[str]`, and the `crud_sdk_methods(CRUD_DESCRIPTORS)` helper (FR-021)
- [ ] T035 [US6] Create `tests/live/test_live_command_coverage.py` (module `pytestmark = [pytest.mark.live]`) with `test_live_operation_executes` (`@pytest.mark.live_extended`, parametrized over `LIVE_OPERATIONS`) and the guard `test_every_guard_eligible_operation_runs_live` (`@pytest.mark.live_smoke`) implementing the FR-021 formula (uncovered / stale / bucket-intersection / invalid-reason failures); seed `KNOWN_LIVE_GAPS = E - T_live - set(LIVE_EXEC_EXCEPTIONS)` with inline reasons per Appendix E (FR-021/SC-008)
- [ ] T036 [US6] Verify `uv run pytest -m "not live" --collect-only` lists no `tests/live/*` node (FR-017/Constitution IV), the guard is green under `-m live_smoke`, and (with a backend) full execution passes under `-m live_extended`

**Checkpoint**: Every live command/resource is exercised or explicitly allowlisted; fourth guard enforced.

---

## Phase 9: User Story 7 - Consolidate test-infrastructure unit tests (Priority: P3)

**Goal**: Shared target/settings factories in one place, fewer tiny modules, all feature-002 security invariants intact.

**Independent Test**: Merged modules pass; no local `_target()`/`_settings()` copies remain; security invariants still run.

- [ ] T037 [US7] Move `make_target()` and `make_settings(tmp_path, **overrides)` into `tests/unit/conftest.py` and replace the local copies across live-infra modules (FR-014)
- [ ] T038 [US7] Merge `tests/unit/test_live_naming.py` into `tests/unit/test_live_settings.py` and `tests/unit/test_live_resource_registry.py` into `tests/unit/test_live_bootstrap.py` (FR-014)
- [ ] T039 [US7] Fold `tests/unit/test_transport_errors.py` into `tests/unit/test_transport.py` as a `(exit_code, stderr, expected_exc)` table, then delete `tests/unit/test_transport_errors.py` (FR-014)
- [ ] T040 [US7] Verify all feature-002 security invariants (`tests/unit/test_upstream_contract_security.py` and live security tests) still run, and offline suite + mypy are green (FR-015)

**Checkpoint**: Infra consolidated with no coverage change.

---

## Phase 10: Polish & Cross-Cutting Concerns

- [ ] T041 [P] Run the full `quickstart.md` validation end to end (Prerequisites + each user story block)
- [ ] T042 [P] Confirm all FOUR guards are enforced (SC-003) and that `KNOWN_ARGV_GAPS`, `KNOWN_FIXTURE_GAPS`, and `KNOWN_LIVE_GAPS` are driven toward `frozenset()`; verify SC-008 (guard green; execution passes under `-m live_extended`)
- [ ] T043 Final acceptance: `uv run pytest -m "not live"`, `uv run ruff format --check . && uv run ruff check .`, `uv run mypy src && uv run mypy tests`, and the SC-002 MUST-retain node IDs still present (T002 set)
- [ ] T044 [P] Line-count sanity across the eight targeted areas trending toward ~3,410 lines (SC-001, secondary/non-binding)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — T004 blocks the guards in US2/US3/US6.
- **User Stories (Phases 3–9)**: Implemented in the authoritative order US1 → US7. Each leaves the offline suite green and is independently mergeable.
- **Polish (Phase 10)**: After all desired stories are complete.

### User Story Dependencies

- **US1 (P1)**: After Foundational. Independent. Note: T006 drops description-dispatch coverage that US2/T013 restores as `ArgvCase` rows (green is preserved; SC-002 is validated at the end).
- **US2 (P1)**: After Foundational (needs T004). Independent of US1 except the description-row restoration noted above.
- **US3 (P2)**: After Foundational (needs T004). Independent (integration tree).
- **US4 (P2)**: Independent (contract tree). No guard.
- **US5 (P3)**: Independent (diff modules). No guard.
- **US6 (P3)**: After Foundational (needs T004). Independent (live tree). Highest risk (backend).
- **US7 (P3)**: Independent (unit infra). No coverage change.

### Within Each User Story

- Shared fixtures/case tables before the parametrized tests and guards that use them.
- Migrate cases before deleting the per-file sources.
- Seed the `KNOWN_*_GAPS` allowlist in the same story as its guard so the suite is never left red.

### Parallel Opportunities

- Setup: T002, T003 in parallel.
- US1: T007, T008, T009 in parallel (independent deletions) after T005/T006.
- Across stories: because each story lives in a different `tests/` subtree, US3, US4, US5, US6, and US7 can be developed in parallel once Foundational is done (if staffed), though the authoritative merge order remains US1 → US7.
- Polish: T041, T042, T044 in parallel.

---

## Parallel Example: User Story 1

```bash
# After relocating assertions (T005) and deleting the source (T006), run the
# independent deletions together:
Task: "Delete tests/unit/resources/test_labels.py"           # T007
Task: "Delete tests/contract/models/ directory"              # T008
Task: "Delete tests/typing/ package"                         # T009
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Phase 1 Setup → Phase 2 Foundational.
2. US1 (safe deletions/relocations) → validate offline green.
3. US2 (unit table + argv guard) → validate SC-004a and the guard.
4. **STOP and VALIDATE**: largest duplication removed, first guard live.

### Incremental Delivery

US3 → US4 → US5 → US6 → US7, each validated independently against `quickstart.md`
and merged on its own. Guards ship with their tables (argv=US2, fixture+operation
coverage=US3, live command execution=US6), each kept green by its `KNOWN_*_GAPS`
allowlist.

---

## Notes

- This feature changes only `tests/` and two `pyproject.toml` mypy-override lines.
- Follow the repo test rules in `AGENTS.md` (table-driven, reuse shared fixtures,
  exact assertions, no dead tests, markers do not inherit).
- Commit per task or logical group using Conventional Commits.
- The three `KNOWN_*_GAPS` allowlists are a temporary bridge; the feature goal is
  each `== frozenset()` (SC-003/SC-008).
