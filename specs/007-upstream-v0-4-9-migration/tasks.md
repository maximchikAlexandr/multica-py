# Tasks: Upstream v0.4.9 Migration

**Input**: All files in `specs/007-upstream-v0-4-9-migration/`.
**Decision authority**:
`contracts/sdk-contract-v2.seed.json`, `contracts/operation-decisions.md`,
`contracts/source-authority.md`, `contracts/upstream-family-disposition.md`,
`contracts/generated-output-formats.json`, and `contracts/live-acceptance.md`.

An implementer MUST stop on a failed task. It MUST NOT choose a different
signature, binding, schema, source range, output format, mutation, artifact
path, or promotion policy.

## Phase 1: Setup

- [x] T001 Create only `.test-artifacts/upstream-v0.4.9/{offline,mutation,smoke,extended,stability}/` in `.gitignore`; do not add another feature artifact root

## Phase 2: Foundational schema

- [x] T002 Materialize and verify `.devlocal/upstream/multica-v0.4.9` with the three exact commands in `contracts/source-authority.md`
- [x] T003 Add schema-v2 frozen `msgspec.Struct` types and closed enums in `src/multica_py/_internal/upstream_contract/generator/schema.py`
- [x] T004 Add validator tests for exact 16 operations, 11 families, 65 trace IDs, catalogs, references, unknown fields, and target identity in `tests/unit/test_upstream_contract_generator.py`
- [x] T005 Implement schema validation, including all catalog/ref resolution and exact 15-compatible/1-intentional counts, in `src/multica_py/_internal/upstream_contract/generator/validation.py`

## Phase 3: User Story 2 — Approve source-backed contract changes

**Goal**: prove every decision against pinned source before generation.
**Independent test**: `validate-source` passes and approved bytes equal the seed.

- [x] T006 [US2] Add source-ref tests for every operation binding and all family refs from `contracts/source-authority.json`, plus byte-consistency with its Markdown view, in `tests/contract/upstream/test_source_authority.py`
- [x] T007 [US2] Implement pinned-checkout commit/path/symbol/line validation and the exact `validate-source --approved ... --source-root ...` CLI in `src/multica_py/_internal/upstream_contract/source_validation.py` and `src/multica_py/_internal/upstream_contract/cli.py`
- [x] T008 [US2] Validate `specs/007-upstream-v0-4-9-migration/contracts/sdk-contract-v2.seed.json`; fail if any source audit item is unresolved
- [x] T009 [US2] Byte-copy the validated seed to `contracts/sdk-contract.json`; assert byte equality and semantic-hash equality in `tests/contract/upstream/test_approved_seed.py`

**Checkpoint**: No generation or SDK source edit is allowed until T002–T009 pass.

## Phase 4: User Story 1 — Preserve the existing public SDK

**Goal**: generate and integrate exactly the 16 governed operations.
**Independent test**: seven goldens, focused behavior tests, and `generate --check` pass.

- [x] T010 [US1] Add the seven exact golden files under `tests/fixtures/upstream_contract/v2/` from `contracts/generated-output-formats.json`
- [x] T011 [US1] Add renderer byte-comparison, check-no-write, unsupported-input, and fixed-order tests in `tests/unit/test_upstream_contract_generator.py`
- [x] T012 [US1] Implement catalog-only rendering in `src/multica_py/_internal/upstream_contract/generator/renderer.py`
- [x] T013 [US1] Implement same-directory staged writes for the seven outputs in `src/multica_py/_internal/upstream_contract/generator/writer.py`
- [x] T014 [US1] Implement `generate --approved ... [--check]` and reject evidence/candidate/suggestion inputs in `src/multica_py/_internal/upstream_contract/cli.py`
- [x] T015 [US1] Generate all seven paths in `specs/007-upstream-v0-4-9-migration/contracts/generated-output-formats.json` and prove exact golden equality with `generate --check`
- [x] T016 [US1] Add exact traceability-set and collectability guards for FR-001..FR-040, BC-001..BC-006, SC-001..SC-012, and ET-001..ET-007 in `tests/contract/upstream/test_requirement_traceability.py`

### Public behavior integration

- [x] T017 [P] [US1] Add `CommentCursor(before, before_id)` and the exact flat/thread/recent request shapes from the seed in `src/multica_py/models/issue_activity.py`
- [x] T018 [P] [US1] Add `IssueSort` and `SortDirection` generated re-exports in `src/multica_py/enums.py`
- [x] T019 [P] [US1] Add project `Unset` presence models and the exact add/update resource request shapes in `src/multica_py/models/projects.py` and `src/multica_py/models/project_resources.py`
- [x] T020 [US1] Add or update `ArgvCase` rows for all 16 IDs and all seed entrypoints in `tests/cases/argv_data.py`; expected argv must be complete
- [x] T021 [US1] Add positive and negative table rows for every validator ID from the seed in `tests/unit/resources/test_operations.py`
- [x] T022 [US1] Implement only generated comment bindings and cursor parsing in `src/multica_py/resources/issue_comments.py`
- [x] T023 [US1] Implement only generated issue create/list/status bindings in `src/multica_py/resources/issues.py`
- [x] T024 [US1] Implement only generated label add/list/remove bindings in `src/multica_py/resources/issue_labels.py`
- [x] T025 [US1] Implement project create/update/status with exact `Unset`/empty/None behavior in `src/multica_py/resources/projects.py`
- [x] T026 [US1] Implement project-resource behavior: add requires nonblank path and daemon, omits None/blank label; update exposes only nonblank path and preserves daemon/label with no clear API, in `src/multica_py/resources/project_resources.py`
- [x] T027 [US1] Add response-shape and exit 2/3/4/5/other/timeout table rows in `tests/unit/test_transport.py` and `tests/component/test_process_contract.py`
- [x] T028 [US1] Migrate matching component rows to `CommandCase` without adding allowlist entries in `tests/component/resources/cases.py`
- [x] T029 [US1] Run the focused Phase 3 tests listed in `specs/007-upstream-v0-4-9-migration/quickstart.md`; fix only mismatches against the seed

## Phase 5: User Story 3 — Resolve status and provenance conflicts

**Goal**: stage and promote through the selected recoverable transaction.
**Independent test**: dry-check passes; after the maintainer gate, ordinary check reports v0.4.9 and a null candidate.

- [x] T030 [US3] Historical record: source validation is now performed by `validate --source-checkout` against the approved contract.
- [x] T031 [US3] Historical record: reviewed Git merge is the sole promotion action after `collect → validate --source-checkout → render → check`.
- [x] T032 [US3] Add state/coherence tests for canonical refs, semantic hashes, target identity, candidate trust, and null candidate after promotion in `tests/unit/test_upstream_contract_state.py`
- [x] T033 [US3] Implement state/coherence validation in `src/multica_py/_internal/upstream_contract/state.py` and `coherence.py`
- [x] T034 [US3] Add promotion transaction tests for journal recovery and injected failure before/after ordinals 1..5 in `tests/unit/test_upstream_contract_promotion.py`
- [x] T035 [US3] Implement the exact lock/journal/backup/replace/rollback/recovery algorithm from `contracts/generation-and-provenance.md` in `src/multica_py/_internal/upstream_contract/promotion.py`
- [x] T036 [US3] Add `promote --check` projection validation and writing promotion CLI in `src/multica_py/_internal/upstream_contract/cli.py`
- [x] T037 [US3] Verify a maintainer-created `contracts/upstream-v0.4.9-promotion-decision.json` exists and binds a real reviewer identity, candidate hash, approved hash, provenance, previous identity, and operation-decisions ref; NEVER create or edit this file, and stop here when absent
- [x] T038 [US3] Run `generate --check`, `check --with-candidate`, and `promote --check --decision contracts/upstream-v0.4.9-promotion-decision.json`; do not write
- [x] T039 [US3] Run writing `promote` exactly once after T037–T038 and verify the five destinations in `specs/007-upstream-v0-4-9-migration/contracts/generation-and-provenance.md`
- [x] T040 [US3] Run ordinary `scripts/upstream_contract.py check` after T039 and require the active target `v0.4.9` and candidate null

## Phase 6: User Story 4 — Classify new upstream command families

**Goal**: preserve all 11 terminal family dispositions without scope growth.
**Independent test**: family/source guards pass and every projection contains exactly the 16 governed IDs.

- [x] T041 [US4] Add exact 11-row family disposition tests, including literal required-operation arrays and every source-ref ID, in `tests/contract/upstream/test_family_dispositions.py`
- [x] T042 [US4] Add negative fixtures proving 35 additions and 107 help-degraded removal rows cannot enter public coverage in `tests/unit/test_upstream_contract_coherence.py`
- [x] T043 [US4] Generate coverage, CLI manifest, and live target only from the promoted approved contract in `src/multica_py/_internal/upstream_contract/promotion.py`
- [x] T044 [US4] Run `tests/unit/test_upstream_contract_coherence.py` and require exact 16-ID equality across approved/generated/supported/state/coverage/manifest/live target

## Phase 7: User Story 5 — Obtain interpretable acceptance evidence

**Goal**: produce closed offline, live, mutation, and stability evidence.
**Independent test**: mutation is 3/0/0, final baseline passes, stability is 10/10, and summary is accepted.

- [x] T045 [US5] Implement the closed live-outcome contract and fingerprint rules in the historical migration harness
- [x] T046 [US5] Add table-driven outcome, redaction, and result-validation tests to the historical migration harness
- [x] T047 [US5] Implement prepared-target readiness and categorized smoke outcomes in the historical migration harness
- [x] T048 [US5] Implement the historical migration mutation protocol and result schema
- [x] T049 [US5] Add clean-control, wrong-node, wrong-fingerprint, exit-code, missing-result, survivor, and hash-restoration tests to the historical migration harness
- [x] T050 [US5] Run mutation mode offline and require `.test-artifacts/upstream-v0.4.9/mutation/mutation-results.json` summary 3 killed, 0 survived, 0 invalid
- [x] T051 [US5] Produce offline JUnit and coverage at the two exact `.test-artifacts/upstream-v0.4.9/offline/` paths in `quickstart.md`
- [x] T052 [US5] Verify coverage from the merged report.
- [x] T053 [US5] Run the repository coverage check after offline verification.
- [ ] T054 [US5] Run smoke and extended with exact paths under `.test-artifacts/upstream-v0.4.9/{smoke,extended}/` and require passed category, exact target, cleanup passed, and secret scan passed
- [ ] T055 [US5] Run stability only from `.test-artifacts/upstream-v0.4.9/smoke/smoke-report.json` and require exactly 10/10 full-smoke passes
- [x] T056 [US5] Implement the sole aggregate command and closed summary schema in the historical migration harness
- [ ] T057 [US5] Aggregate smoke, extended, mutation, and stability to `.test-artifacts/upstream-v0.4.9/acceptance-summary.json`; require `accepted=true`

## Phase 8: Polish and cross-cutting quality

- [x] T058 Run Ruff format/check and mypy commands from `specs/007-upstream-v0-4-9-migration/quickstart.md`
- [x] T059 Run `uv run pytest -m "not live"` and collect-only from `tests/`; require no `tests/live/` node collected
- [x] T060 Run `generate --check`, ordinary coherence, all five architecture/baseline stages, and validate all JSON files with `jq -e .`

## Dependencies and parallel work

`T001 → T002 → T003–T009 → T010–T016 → T017–T029 → T030–T040 →
T041–T044 → T045–T057 → T058–T060`.

Only tasks explicitly marked `[P]` may run concurrently. T037 is an external
maintainer gate, not an implementation choice. No later task may bypass it.

Story order is `US2 → US1 → US3 → US4 → US5`. US2 precedes US1 because source
approval is a safety prerequisite; both are priority P1. US3 depends on the
generated/public contract. US4 depends on promotion projections. US5 depends
on the exact promoted target.

Parallel example for US1 after T016: run T017, T018, and T019 concurrently;
then continue sequentially at T020. Other stories intentionally contain no
parallel task because they mutate shared state or consume the preceding
artifact.

## Implementation strategy

The minimum independently demonstrable increment is US2: pinned-source
validation plus byte-identical approved seed. The public-SDK MVP is US2+US1.
Add US3, US4, and US5 strictly in dependency order. Stop at T037 until a real
maintainer supplies the decision file.

## Phase 9: Convergence

- [x] T061 Make the seven-output generator check pass from a clean checkout and prove `generate --check` has no missing governed outputs per FR-017 and T015/T038/T060 (partial)
- [x] T062 Reconcile canonical generated coverage and CLI manifest with the promoted 16-operation contract so ordinary `scripts/upstream_contract.py check` reports v0.4.9 with candidate null and no coverage gaps per FR-027 and T040/T060 (contradicts)
- [ ] T063 Run smoke and extended acceptance into the exact `.test-artifacts/upstream-v0.4.9/{smoke,extended}/` paths; require passed category, exact target, cleanup pass, and secret scan pass per US5/T054 (missing)
- [ ] T064 Run stability only from the accepted smoke report and record exactly 10/10 full-smoke passes per US5/T055 (missing)
- [ ] T065 Aggregate smoke, extended, mutation, and stability evidence into `.test-artifacts/upstream-v0.4.9/acceptance-summary.json` and require `accepted=true` per US5/T057 (missing)
