# Tasks: Reduce Non-Production Complexity

**Input**: Design documents from `/specs/008-reduce-nonprod-complexity/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and
`contracts/`

**Tests**: Tests are required where this task list names them. Each test must
implement the exact contract assertion before its replacement or deletion is
accepted.

**Organization**: Tasks are grouped by independently verifiable user stories.
Within a phase, perform tasks in listed order unless `[P]` is present and its
stated prerequisite is already complete.

## Format: `[ID] [P?] [Story] Description`

- `[P]` means the task changes disjoint files and may run after its stated
  prerequisite.
- `[US#]` maps to the numbered user story in `spec.md`.

## Phase 1: Setup

**Purpose**: Establish the immutable baseline and working boundaries before any
deletion.

- [X] T001 Record baseline tree `b3a299b36d1ad5bc386b5e4517d2a348d53db31c` in the implementation PR description; use, but do not duplicate, the staged-tree physical-line command already fixed in `specs/008-reduce-nonprod-complexity/quickstart.md`.
- [X] T002 Inventory every path in groups A–F of `specs/008-reduce-nonprod-complexity/contracts/reduction-map.md` and mark each as create, rewrite, delete, or retain in the implementation PR description; do not add a repository inventory file.
- [X] T003 Run `uv run pytest -m "not live"`, `uv run mypy src`, `uv run mypy tests`, and `git diff --check`; paste the four command outcomes into the implementation PR description linked from `specs/008-reduce-nonprod-complexity/tasks.md` before changing code.

---

## Phase 2: Foundational Contracts and Baselines

**Purpose**: Install the replacement contracts and OpenSpec-compatible active
knowledge before removing their predecessors.

**⚠️ CRITICAL**: Complete this phase before deleting any file named by groups
A–F.

- [X] T004 Create the four baseline capability files exactly at `openspec/specs/sdk-surface/spec.md`, `openspec/specs/subprocess-transport/spec.md`, `openspec/specs/upstream-contract/spec.md`, and `openspec/specs/verification-and-release/spec.md` from the closed matrix in `specs/008-reduce-nonprod-complexity/contracts/historical-baseline.md`.
- [X] T005 Create `tests/contract/test_baseline_specs.py` to enforce the exact `## ADDED Requirements` → `### Requirement:` → `#### Scenario:` grammar and every source-to-destination row in `specs/008-reduce-nonprod-complexity/contracts/historical-baseline.md`.
- [X] T006 Update `AGENTS.md`, `README.md`, `docs/cli-coverage.md`, `docs/releasing.md`, and `scripts/audit_source_links.py` to point only to the four baseline specifications instead of `specs/001-*` through `specs/006-*`.
- [X] T007 Delete `specs/001-full-cli-sdk/`, `specs/002-upstream-coverage-checks/`, `specs/003-multica-live-integration-tests/`, `specs/004-test-suite-optimization/`, `specs/005-test-suite-agent-sandbox/`, and `specs/006-test-suite-consolidation/`; retain `specs/007-upstream-v0-4-9-migration/` and `specs/008-reduce-nonprod-complexity/`.
- [X] T008 Run the Group-A `git grep` guard from `specs/008-reduce-nonprod-complexity/contracts/reduction-map.md`, `uv run pytest tests/contract/test_baseline_specs.py`, and `uv run pytest -m "not live"`; fix every non-feature-008 stale reference before continuing.

**Checkpoint**: Active historical requirements exist in four OpenSpec-compatible
baseline specifications and no deleted feature directory remains referenced.

---

## Phase 3: User Story 1 — Maintain a Lean SDK Verification Suite (Priority: P1) 🎯 MVP

**Goal**: Replace test-architecture governance and duplicate success harnesses
with one complete, provenance-backed operation table and focused product tests.

**Independent Test**: `tests/cases/operations.py` exposes 137 rows: 116 unique
canonical public methods and 21 variants; the unit executor asserts the full
transport call for each row, and the offline suite collects no live test.

### Implementation for User Story 1

- [X] T009 [US1] Rewrite the foundation of `tests/cases/operations.py` to define frozen `OperationCase`, `RESOURCE_SPECS`, `generated_operation_cases()`, and the closed legacy mapping interfaces required by `contracts/verification.md` and `contracts/generation.md`.
- [X] T010 [US1] Add the exact public-resource discovery and canonical-set completeness assertions to `tests/unit/resources/test_operations.py` after T009, using `RESOURCE_SPECS` and the expression in `contracts/verification.md`.
- [X] T011 [US1] Add the legacy payload-bijection migration test to `tests/unit/resources/test_operations.py` after T009, mapping rows `001`–`135` to final rows by complete transport payload as required by `contracts/generation.md`.
- [X] T012 [US1] Complete `tests/cases/operations.py` after T010–T011 with the 107 manual rows and single `OPERATION_CASES` tuple; satisfy the 137-row/116-canonical/21-variant assertions.
- [X] T013 [US1] Move only distinct negative/error data into `tests/cases/errors.py` and remove duplicated success-case data from `tests/cases/argv_data.py`, `tests/cases/models.py`, `tests/cases/assertions.py`, and `tests/cases/execution.py`.
- [X] T014 [US1] Rewrite `tests/unit/resources/test_operations.py` so `test_operation` is the sole generic successful-operation executor and asserts exact transport method, argv, stdin, timeout, and result shape for every `OperationCase`.
- [X] T015 [US1] Reduce `tests/component/test_process_contract.py` to the three `bytes-env`, `text-stdin`, and `timeout-tree-cleanup` rows using `tests/fixtures/child_process.py`; delete `tests/component/test_cli_roundtrip.py`, fake OpenCode fixtures/tests, live-policy registries, manifest support, and manifest coverage files listed in Group C of `contracts/reduction-map.md`.
- [X] T016 [US1] Delete `src/multica_py/_internal/manifest.py`, `src/multica_py/_generated/cli_manifest.json`, `tests/contract/test_cli_manifest.py`, and `tests/contract/test_full_cli_coverage.py`; update imports and contract test references so no compatibility alias remains.
- [X] T017 [US1] Remove Group-B files and rules: `scripts/_loc_metrics.py`, `scripts/check_test_architecture.py`, `scripts/check_test_baseline.py`, `scripts/capture_test_baseline.py`, `tests/behavioral-coverage.json`, `tests/duplicate-removal-map.json`, `tests/quality-baseline.json`, `tests/unit/test_test_architecture.py`, and `tests/unit/test_quality_baseline_tools.py`.
- [X] T018 [US1] Update `AGENTS.md`, `README.md`, `.github/workflows/ci.yml`, and `tests/conftest.py` to remove five-stage architecture/baseline/deletion-ledger rules and retain only the marker topology, one offline parallel pass, and one serial process pass fixed by `contracts/verification.md`.
- [X] T019 [US1] Run Group-B and Group-C reference guards from `contracts/reduction-map.md`, `uv run pytest -m "not live" --collect-only`, `uv run pytest -m "not live"`, `uv run mypy tests`, and the existing coverage command; resolve all failures without allowlists.

**Checkpoint**: One canonical operation table supplies all successful argv
coverage; duplicate harnesses and meta-governance are gone.

---

## Phase 4: User Story 2 — Migrate an Upstream CLI Release Through Approved Generation (Priority: P1)

**Goal**: Replace the upstream state machine with one approved contract,
fail-closed evidence, deterministic generation, and Git-review promotion.

**Independent Test**: A clean checkout can run `collect → source-validate →
render → check`; only `contracts/sdk-contract.json` affects public generated
runtime code, and two clean renders are identical.

### Tests for User Story 2

- [X] T020 [P] [US2] Create `tests/unit/test_upstream_contract.py` for the closed v3 contract schema, tagged-value grammar, generated IDs, 135-row legacy mapping, ResultAssertion algorithms, source-reference modes, and stdlib socket prohibition in `tools/upstream_contract/`.
- [X] T021 [P] [US2] Create `tests/contract/test_sdk_contract.py` for approved-contract-only rendering, semantic invariants, transient-output paths, committed-runtime drift, and retired-flow rejection in `contracts/sdk-contract.json` and `scripts/upstream_contract.py`.
- [X] T022 [P] [US2] Create `tests/packaging/test_generated_runtime.py` for the exact isolated-wheel protocol and exports listed in `contracts/verification.md`.

### Implementation for User Story 2

- [X] T023 [US2] Create `tools/upstream_contract/contract.py`, `tools/upstream_contract/evidence.py`, `tools/upstream_contract/generation.py`, `tools/upstream_contract/cli.py`, and `tools/upstream_contract/__init__.py` with only the four commands and exact ownership in `contracts/generation.md`.
- [X] T024 [US2] Extend `contracts/sdk-contract.json` to the closed v3 catalogs, vector IDs, tagged values, assertion objects, binding descriptors, enum members, validator definitions, and source/test references defined in `contracts/generation.md`.
- [X] T025 [US2] Implement `generated_operation_cases()` in `tests/cases/operations.py` from the approved v3 `test_vectors`; enforce the unique `generated:<operation-id>:<entrypoint-id>:canonical|variant:<nn>` IDs and the one-public-method `issues.comments.list` rule.
- [X] T026 [US2] Render and commit only `src/multica_py/_generated/approved_sdk.py`; update `src/multica_py/enums.py`, `src/multica_py/_internal/compat.py`, and each governed resource module to import the exact generated binding/validator symbols in `contracts/generation.md`.
- [X] T027 [US2] Replace `scripts/upstream_contract.py` with the thin entrypoint to `tools.upstream_contract.cli.main`, update `.gitignore` for one committed runtime projection and ignored evidence/transient output, and document the four-command maintainer flow in `AGENTS.md`, `docs/contributing.md`, `docs/cli-coverage.md`, `docs/releasing.md`, `docs/compatibility.md`, and retired-flow references in `specs/007-upstream-v0-4-9-migration/` only.
- [X] T028 [US2] Rewrite `contracts/sdk-contract.json.test_refs` to the exact `T-OPERATION` and `T-CONTRACT` nodes in `contracts/verification.md` before deleting their old referenced tests.
- [X] T029 [US2] Delete `src/multica_py/_internal/upstream_contract/`, `scripts/upstream_upgrade.sh`, `scripts/check_upstream_drift.py`, observer/drift workflows, upstream state/promotions/coverage fixtures, golden snapshots, mutation fixtures, and all old upstream-contract test modules listed in Group D of `contracts/reduction-map.md`.
- [X] T030 [US2] Replace golden comparisons with two-clean-render byte equality, compilation, JSON/Markdown validation, semantic assertions, and the isolated built-wheel import test in `tests/unit/test_upstream_contract.py`, `tests/contract/test_sdk_contract.py`, and `tests/packaging/test_generated_runtime.py`.
- [X] T031 [US2] Run `collect`, source-mode `validate`, `render`, `check`, the Group-D reference guard, focused upstream tests, and the exact wheel command from `contracts/verification.md`; leave no candidate/supported state, journal, golden output, or deprecated command alias.

**Checkpoint**: An approved contract PR is the only upstream promotion flow;
runtime code is generated once and all other projections are transient.

---

## Phase 5: User Story 3 — Run Focused Live and CI Assurance (Priority: P2)

**Goal**: Keep a prepared-target SDK smoke suite and real CI outcomes while
removing SDK-owned backend, sandbox, direct-HTTP, and YAML-text-test ownership.

**Independent Test**: The default suite stays offline; a prepared runner can
collect exactly five `live_smoke` tests and execute the five closed scenarios.

### Tests for User Story 3

- [X] T032 [US3] Create `tests/live/conftest.py` with the sole `prepared_client()` factory, exact five environment inputs, `pytest.UsageError` behavior, and `ClientConfig` construction in `contracts/verification.md`.
- [X] T033 [US3] Create `tests/live/test_smoke.py` after T032 with exactly the five scenarios and module markers in `contracts/verification.md`; use the sole `prepared_client()` and one `ExitStack` cleanup path only.

### Implementation for User Story 3

- [X] T034 [US3] Create `tests/live/README.md` and `.github/workflows/live-smoke.yml` with only `workflow_dispatch`, `[self-hosted, multica-live]`, 10-minute timeout, required variables, and the exact live pytest command in `contracts/verification.md`.
- [X] T035 [US3] Delete all backend/sandbox/extended live trees, `tools/live_support/`, listed live scripts, extended/canary workflows, `tests/unit/test_live_*`, `tests/contract/test_live_target_workflows.py`, and `httpx` according to Group E of `contracts/reduction-map.md`; update `pyproject.toml` and regenerate `uv.lock` with `uv lock`.
- [X] T036 [US3] Delete `tests/contract/test_ci_profiles.py`, workflow-text helpers, and every remaining pytest assertion that reads `.github/workflows/*.yml`; retain CI-008 only as the manual PR evidence template in `contracts/verification.md`.
- [X] T037 [US3] Update `.github/workflows/ci.yml` and marker declarations in `pyproject.toml`/`tests/conftest.py` to the exact retained/deleted jobs and markers in `plan.md` and `contracts/verification.md`.
- [X] T038 [US3] Run Group-E and Group-F guards, `uv lock --check`, `uv run pytest -m "not live"`, and `uv run pytest -o addopts="" -q -m live_smoke --collect-only tests/live/test_smoke.py`; verify exactly five live nodes collect.

**Checkpoint**: The SDK owns only five prepared-target smoke scenarios; CI is
verified through job outcomes rather than repository parsing of workflow text.

---

## Phase 6: User Story 4 — Preserve Useful Project Knowledge for OpenSpec (Priority: P2)

**Goal**: Complete the OpenSpec-compatible historical baseline without
installing or migrating to OpenSpec itself.

**Independent Test**: The baseline grammar/traceability test passes and the
repository contains no active reference to removed features 001–006.

- [X] T039 [US4] Re-read `openspec/specs/*/spec.md` against every row of `contracts/historical-baseline.md` and update only the four baseline files until `tests/contract/test_baseline_specs.py` proves each exact requirement and scenario.
- [X] T040 [US4] Verify `openspec/` contains only the four `openspec/specs/*/spec.md` baseline files and no OpenSpec initialization/configuration, change proposal, command integration, or agent-integration artifact.
- [ ] T041 [US4] Run the Group-A reference guard and `uv run pytest tests/contract/test_baseline_specs.py`; paste both outcomes into the implementation PR description.

**Checkpoint**: The next feature can migrate to OpenSpec from concise baseline
specifications without retaining the historical Spec Kit directories.

---

## Phase 7: Polish and Cross-Cutting Proof

**Purpose**: Demonstrate the complete reduction without weakening product
guarantees.

- [ ] T042 Run every quickstart section verbatim from `specs/008-reduce-nonprod-complexity/quickstart.md`, including source validation, generator check, offline/package commands, dependency check, live collection, and reference guards.
- [X] T043 Obsolete: the staged-tree physical-line measurement gate was removed from the feature contract.
- [X] T044 Verify `git status --short`, `git diff --check`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`, `uv run mypy tests`, and `uv run pytest -m "not live"` against `pyproject.toml`, `.github/workflows/ci.yml`, `src/`, and `tests/`; resolve all failures without reintroducing a deleted allowlist, shim, snapshot, state machine, or workflow-text test.
- [ ] T045 Attach manual CI-008 evidence in the exact template from `contracts/verification.md` after one green `ci.yml` run and one green manually dispatched `live-smoke.yml` run.

## Phase 8: Convergence

- [X] T046 Obsolete: SC-001's physical-line threshold was removed from the feature contract.
- [X] T047 Remove the retired `tests/fixtures/upstream_contract/v2/` golden fixture and re-run the Group-D guards per FR-013.
- [X] T049 Run source-mode validation and every quickstart section with the actual pinned upstream checkout, resolving the remaining quickstart blockers per SC-002.
- [ ] T050 Obtain one green `ci.yml` run and one manually dispatched green `live-smoke.yml` run, then attach the exact CI-008 evidence per US3/AC3 (missing).

## Dependencies & Execution Order

- Phase 1 precedes every modification.
- Phase 2 must complete before deleting legacy specs or beginning user-story
  replacements.
- US1 (Phase 3) and US2 (Phase 4) share `tests/cases/operations.py`; complete
  T009–T019 before T023–T031. T020–T022 may run after Phase 2 in parallel with
  US1 tests only.
- US3 (Phase 5) starts after T018 because it changes CI and markers; T032 and
  T033 may run in parallel.
- US4 (Phase 6) is validated by Phase-2 work and is a final traceability
  checkpoint, not a second baseline migration.
- Phase 7 starts only after T031, T038, and T041 are complete.

## Parallel Opportunities

- After Phase 2, T009–T011 and T020–T022 are parallelizable because they create
  disjoint test modules.
- In US3, T032 is the required fixture foundation; T033 and then T034 depend on it.
- T039 and T040 can run together after T008; T041 depends on both.

## Implementation Strategy

### MVP First

1. Complete Phases 1–3 through T019.
2. Validate one canonical offline table, the removal of meta-governance, and
   network-free default verification.
3. Stop before upstream tooling and live ownership changes if this checkpoint
   is not green.

### Incremental Delivery

1. Land the OpenSpec baseline and operation-table reduction.
2. Land the deterministic upstream generator replacement.
3. Land the prepared-target live scope and CI cleanup.
4. Run cross-cutting proof and record the reduction.

## Format Validation

- All 45 tasks use checkbox, sequential task ID, required user-story label
  where applicable, and at least one exact file path.
- `[P]` is used only for tasks with disjoint files after stated prerequisites.
- Every user story has an independent test criterion and a checkpoint.
