# Tasks: Test Suite Consolidation

**Feature:** `006-test-suite-consolidation`  
**Source snapshot:** `b3a299b36d1ad5bc386b5e4517d2a348d53db31c`

## Execution Rules

- Выполнять phases и tasks строго по порядку, кроме явно отмеченных `[P]`.
- Не начинать следующий stage, пока exit gate текущего stage не пройден.
- Удаление test node и запись в `tests/duplicate-removal-map.json` выполняются одним commit.
- Не снижать assertions, coverage config, mutation config или behavioral manifest ради прохождения gate.
- Не создавать compatibility aliases для удалённых registries/types.
- Если stage gate падает после commit-а дедупликации — остановить дедупликацию, revert commit или восстановить retained coverage по `tests/duplicate-removal-map.json` до продолжения (FR-032).
- Каждый новый или существенно переписанный test/support Python file должен иметь `<=800` logical lines.

## Phase 1: Setup

- [ ] T001 Добавить `pytest-timeout>=2.4,<3`, `timeout = 30`, `timeout_method = "signal"` и default marker selection `not live and not packaging` в `pyproject.toml`.
- [ ] T002 Обновить lock после T001 в `uv.lock`; убедиться, что runtime dependency list не изменился.
- [ ] T003 Создать canonical empty schema-1 map в `tests/duplicate-removal-map.json` и правила хранения evidence в `.artifacts/test-suite-consolidation/README.md`.
- [ ] T004 Создать CLI skeleton со stages `pr1`, `pr2`, `pr3`, `pr4`, `final` в `scripts/check_test_architecture.py`; неизвестный stage должен возвращать exit code 2.

## Phase 2: Foundational Prerequisites

- [ ] T005 Реализовать schema-2 capture, canonical serialization, logical-LOC counting, coverage/mutation fingerprints и package-path counting в `scripts/capture_test_baseline.py`; CLI args должны быть ровно `--git-sha`, `--source-snapshot`, `--coverage-json`, `--junit-xml`, `--mutation-results`, `--behavior-manifest`, `--output`.
- [ ] T006 Реализовать immutable baseline validation и stage comparisons без minimum node-count в `scripts/check_test_baseline.py`; compare CLI принимает ровно `--baseline`, `--stage`, `--coverage-json`, `--junit-xml`, `--mutation-results`.
- [ ] T007 Реализовать loaders/validators для `tests/behavioral-coverage.json` и `tests/duplicate-removal-map.json` в `scripts/check_test_architecture.py`.
- [ ] T008 Обновить schema-2, fingerprint, duration, LOC и no-node-floor tests в `tests/unit/test_quality_baseline_tools.py`.
- [ ] T009 Создать positive/negative tests для manifest/map parsing и stage CLI в `tests/unit/test_test_architecture.py`.

**Foundation exit gate:** T001–T009 проходят; tooling готово принять repaired baseline, но baseline ещё не зафиксирован.

## Phase 3: User Story 1 — Reliable Gate and Safe Deduplication (P1, stage pr1)

**Goal:** исправить process signal, заменить weak network smoke и зафиксировать immutable quality/behavior baseline.

**Independent test:** удалить один duplicate mapping после его регистрации и убедиться, что architecture gate падает; вернуть mapping и убедиться, что gate проходит при неизменных coverage/mutation/behavior metrics.

- [ ] T010 [US1] Создать `ProcessState`, Linux `/proc` adapter, macOS `ps` adapter и bounded wait helpers в `tests/fixtures/process_state.py` с deadline 2.0 seconds и interval 0.02 seconds.
- [ ] T011 [US1] Добавить running/zombie/absent parsing и wait deadline tests в `tests/unit/test_process_state.py`.
- [ ] T012 [US1] Расширить `tests/fixtures/child_process.py` ready/release, ignore-SIGTERM, descendant, parent-PID и descendant-PID modes; удалить fixed 30/60-second sleeps.
- [ ] T013 [US1] Переписать `tests/component/test_process_contract.py` как единственную функцию `test_process_contract`, параметризованную ровно четырьмя IDs `cancellation`, `timeout`, `sigterm-escalation`, `descendant-cleanup`; применить module markers `process`, `serial` и timeout 20 seconds; реализовать bounded finalizer по `contracts/process-harness.md` (закрытие pipes, завершение process group, повторная проверка отсутствия потомков).
- [ ] T014 [US1] Удалить `tests/component/test_cancellation.py` после T013 и записать все removed/retained contracts в `tests/duplicate-removal-map.json`.
- [ ] T015 [US1] Заменить `test_check_offline_does_not_touch_network` hard socket/httpx prohibition test-ом (invariant `network.offline-hard-fail`) в `tests/unit/test_upstream_contract_security.py`, удалить старый test из `tests/contract/test_upstream_contract_check.py` и записать mapping в `tests/duplicate-removal-map.json`.
- [ ] T016 [US1] Запустить repaired offline suite и branch coverage; сохранить JUnit и coverage outputs в `.artifacts/test-suite-consolidation/offline-junit.xml` и `coverage.json`.
- [ ] T017 [US1] Запустить полный configured mutmut scope и сохранить `mutmut results --all` в `.artifacts/mutation/results.txt`; unknown status должен считаться failure.
- [ ] T018 [US1] Создать reviewed `tests/behavioral-coverage.json` с ровно 111 operation keys, closed dimensions и обязательными named invariants из `data-model.md`.
- [ ] T019 [US1] Сгенерировать и commit immutable schema-2 `tests/quality-baseline.json` из T016–T018; `git_sha` должен указывать на green repaired stage-`pr1` commit.
- [ ] T020 [US1] Реализовать stage `pr1` согласно stage-activation table в `contracts/quality-gates.md`: process markers (проверка №8), default live/packaging exclusion (№12), manifest invariants и baseline self-check в `scripts/check_test_architecture.py`; фактическое отсутствие running descendants обеспечивается process-тестами T013 и в architecture gate не дублируется.
- [ ] T021 [US1] Добавить unit/contract/component run, process run, hard-network test, architecture `pr1`, coverage, mutation artifact и baseline compare в quality job `.github/workflows/ci.yml`; добавить `tools` в scope types job (`mypy tests scripts tools --ignore-missing-imports --follow-imports=silent --check-untyped-defs`).
- [ ] T022 [US1] Выполнить весь stage-`pr1` quickstart и сохранить combined output в `.artifacts/test-suite-consolidation/pr1-gate.txt`.

**US1 exit gate:** offline suite green; zombie false failures отсутствуют; raw node count не является gate; baseline/manifest committed; coverage, mutation и required contracts защищены.

## Phase 4: User Story 2 — One OperationCase Catalog (P1, stage pr2)

**Goal:** заменить unit/component catalogs одним `OperationCase` source и одним real fake-CLI round trip.

**Independent test:** временно добавить case variant в `OPERATION_CASES`; unit и component executors собирают его без второй записи; после проверки временный case удаляется.

- [ ] T023 [US2] Определить только `BehaviorDimension`, `ExpectedTransportCall`, `FakeCliResponse`, `LivePolicy`, `OperationCase`, `ErrorCase` и validation rules в `tests/cases/models.py`.
- [ ] T024 [US2] Реализовать `invoke_client_operation`, `invoke_resource_operation`, `configure_mock_transport` и единственный root-resource class map в `tests/cases/execution.py`.
- [ ] T025 [P] [US2] Перенести typed result/exception assertions и payload helpers в `tests/cases/assertions.py` и `tests/cases/payloads.py`; реализовать `load_golden(name: str) -> bytes`, читающий `tests/fixtures/golden/<name>.json`, если он существует, иначе `<name>.bin` (отсутствие обоих — `FileNotFoundError`); порог 4096 применяется только при авторинге case data и проверяется architecture gate (один payload не хранится в двух местах).
- [ ] T026 [US2] Мигрировать все `ARGV_CASES`, `DECODE_CASES` и success `CommandCase` variants в единственный immutable `OPERATION_CASES` в `tests/cases/operations.py`.
- [ ] T027 [US2] Назначить byte-identical `LivePolicy` всем variants каждого из 111 operation IDs в `tests/cases/operations.py` по таблице деривации в `data-model.md` §4 (`mode=smoke` не присваивается ни одной операции); unrunnable reasons использовать только из closed enum.
- [ ] T028 [US2] Создать компактный `ERROR_CASES` с public exception assertions в `tests/cases/errors.py`; private helper assertions не переносить.
- [ ] T029 [US2] Экспортировать только canonical models/helpers/registries и выполнять import-time uniqueness/reference validation в `tests/cases/__init__.py`.
- [ ] T030 [US2] Переписать `tests/unit/resources/test_operations.py` как exhaustive executor `OPERATION_CASES`, проверяющий exact method/argv/stdin/timeout и `assert_result`.
- [ ] T031 [US2] Переписать `tests/fixtures/fake_multica.py` на explicit response/record schema 1, absolute paths, base64 output, env allowlist и exit 64 validation; argv-based fixture selection удалить.
- [ ] T032 [US2] Переписать `tests/component/conftest.py` на создание client с programmable fake executable; удалить recursive private transport mutation и string check DSL.
- [ ] T033 [US2] Создать единственный success executor `test_cli_round_trip` в `tests/component/test_cli_roundtrip.py` для всех non-spawn `OperationCase`.
- [ ] T034 [US2] Создать единственный failure executor `test_cli_error_round_trip` в `tests/component/test_cli_errors.py` для всех `ErrorCase`.
- [ ] T035 [US2] Добавить direct protocol tests response/stderr/exit/record/invalid-path/invalid-base64 в `tests/component/test_fake_cli.py`.
- [ ] T036 [US2] Удалить `tests/unit/resources/cases/`, `tests/component/command_cases.py`, `tests/component/resource_payloads.py`, `tests/component/resource_support.py` и `tests/component/resources/`; в `tests/unit/test_project_resource_models.py` переименовать локальный класс `DecodeCase` в `ProjectResourceDecodeCase` и `_DECODE_CASES` в `_PROJECT_RESOURCE_DECODE_CASES` (содержимое cases и assertions не меняется, node IDs сохраняются, запись в duplicate map не добавляется); записать removed node mappings в `tests/duplicate-removal-map.json`.
- [ ] T037 [P] [US2] Удалить canonical-operation duplicates из `tests/component/test_issue_project_assignment.py` и `tests/component/test_project_resources.py`, сохранив только multi-operation/stateful scenarios; обновить `tests/duplicate-removal-map.json`.
- [ ] T038 [US2] Реализовать stage `pr2` согласно stage-activation table в `contracts/quality-gates.md`; обновить manifest consumers `tests/contract/test_full_cli_coverage.py` и `tests/_manifest_support.py` на `OPERATION_CASES`/`ERROR_CASES` и добавить проверку соответствия `LivePolicy` в `OPERATION_CASES` текущим ID-наборам `tests/live/resources.py`; `tests/live/test_live_command_coverage.py` на stage `pr2` НЕ изменяется (полная замена guard и удаление ID-наборов — T064/T065); выполнить stage-`pr2` quickstart и сохранить `.artifacts/test-suite-consolidation/pr2-gate.txt`.

**US2 exit gate:** ровно 111 operation IDs; stale case types/registries отсутствуют; unit/component используют один catalog; coverage/mutation/behavior не ниже `pr1` baseline; tests LOC не выше `pr1` baseline.

## Phase 5: User Story 3 — Offline Contracts, Tooling and Packaging (P2, stage pr3)

**Goal:** удалить fixture/low-signal шум, оставить шесть upstream boundary modules и один package build contour.

**Independent test:** package job строит один artifact set; удаление `dist/` перед artifact test приводит к failure, не к skip.

- [ ] T039 [US3] Удалить весь `tests/fixtures/json/`, удалить payload constants, дублирующие migrated response bytes, и перенести только payloads `>4096` bytes в `tests/fixtures/golden/`.
- [ ] T040 [P] [US3] Удалить wall-clock `test_check_runs_under_30_seconds` из `tests/contract/test_upstream_contract_check.py`, redundant `hasattr` из `tests/contract/test_issue_models.py` и trivial constructor duplicates из `tests/unit/resources/test_issues.py`; обновить `tests/duplicate-removal-map.json`.
- [ ] T041 [P] [US3] Создать `repo_factory(tmp_path)` и direct subprocess invocation helpers без mutation checked-in files в `tests/contract/conftest.py`.
- [ ] T042 [US3] Создать ровно шесть boundary modules `test_check_cli.py`, `test_collect_cli.py`, `test_diff_cli.py`, `test_upgrade_cli.py`, `test_promotion_cli.py`, `test_observer_cli.py` в `tests/contract/upstream/`.
- [ ] T043 [US3] Сохранить exhaustive schema/severity/diff/output/argv/security combinations только в `tests/unit/test_upstream_contract_*.py`; перенести `MutationSeverityCase`/`MUTATION_SEVERITY_CASES` в `tests/unit/mutation_severity_cases.py` и обновить импорт в `tests/unit/test_upstream_contract_diff.py`; перенести retained workflow/action assertions в `tests/contract/test_ci_profiles.py`, inventory assertions в `tests/contract/test_cli_manifest.py`, а contract modules T042 оставить representative boundary cases.
- [ ] T044 [US3] Удалить `tests/contract/test_upstream_contract_actions.py`, `test_upstream_contract_apply_suggestions.py`, `test_upstream_contract_argv.py`, `test_upstream_contract_check.py`, `test_upstream_contract_collect.py`, `test_upstream_contract_diff.py`, `test_upstream_contract_output.py`, `test_upstream_contract_prepare_upgrade.py`, `test_upstream_contract_promotion.py`, `test_upstream_contract_quickstart.py`, `test_upstream_contract_workflows.py`, `tests/contract/test_upstream_inventory.py` и `tests/contract/mutation_severity_cases.py`; обновить duplicate map.
- [ ] T045 [US3] Удалить `preserved_generated_state`, `fcntl.flock` и writes в checked-in generated paths из `tests/contract/`; все write scenarios направить в `repo_factory`.
- [ ] T046 [P] [US3] Создать единственный no-skip artifact test `test_dist_contains_one_wheel_and_one_sdist` в `tests/packaging/test_artifacts.py`, проверяющий ровно один wheel и один sdist и contents из package contract.
- [ ] T047 [US3] Добавить `tools/live_support` в sdist include и оставить его вне wheel в `pyproject.toml`; удалить старые packaging modules `tests/packaging/test_artifact_contents.py`, `test_build.py`, `test_import_smoke.py`, `test_installation.py`, `test_wheel_install.py` и обновить duplicate map.
- [ ] T048 [US3] Переписать `.github/workflows/package-test.yml` на jobs `build-and-validate` и `install`, один `uv build`, один uploaded artifact set и ровно шесть install paths; сохранить триггеры `on: pull_request` и `push` на `main`.
- [ ] T049 [US3] Удалить distribution `build` job и `uv build` compatibility steps из `.github/workflows/ci.yml`; package workflow сделать единственным build gate.
- [ ] T050 [US3] Обновить `tests/contract/test_ci_profiles.py` assertions: one build, six paths, zero packaging skips, no CI compatibility build. `test_package_workflow_builds_wheel_once` — guard-узел invariant `packaging.single-build` (используется в manifest-расширении T053).
- [ ] T051 [P] [US3] Создать canonical shared environment/target models and parsers в `tools/live_support/environment.py` с limit `<=450` logical lines и exports в `tools/live_support/__init__.py`.
- [ ] T052 [P] [US3] Создать canonical shared scan/redaction functions и `VERIFICATION_CODE` в `tools/live_support/diagnostics.py`.
- [ ] T053 [US3] Перевести `scripts/resolve_multica_target.py`, `scripts/run_live_tests.py`, `scripts/scan_live_artifacts.py` на imports только из `tools.live_support`; imports `tests.*` удалить; создать pytest guard `tests/unit/test_test_architecture.py::test_no_tests_import`, вызывающий `check_test_architecture.py --stage pr3` (проверка №6); добавить stage-gated keys `packaging.artifact-required`, `packaging.single-build`, `tooling.no-tests-import` в `tests/behavioral-coverage.json` последним коммитом stage `pr3` (после готовности guard-узлов T046/T050 и данного guard) с отображением на guard-узлы `tests/packaging/test_artifacts.py::test_dist_contains_one_wheel_and_one_sdist`, `tests/contract/test_ci_profiles.py::test_package_workflow_builds_wheel_once` и `tests/unit/test_test_architecture.py::test_no_tests_import` соответственно (формат по data-model §7 правило 6) — sanctioned fingerprint migration по data-model §7 правило 5. Зависит от T046 и T050.
- [ ] T054 [US3] Создать consolidated tests shared tools в `tests/unit/test_live_support_tools.py`, удалить superseded `tests/unit/test_resolve_multica_target.py` и `tests/unit/test_scan_live_artifacts.py`, перенести `tests/unit/test_live_mutation_cases.py` в `tests/unit/test_live_support_tools.py`, обновить duplicate map.
- [ ] T055 [US3] Реализовать stage `pr3` согласно stage-activation table в `contracts/quality-gates.md`, выполнить offline/contract/package quickstart и сохранить `.artifacts/test-suite-consolidation/pr3-gate.txt`.

**US3 exit gate:** fixture tree отсутствует; шесть contract modules; packaging skip zero; one build/six install paths; no scripts/src imports from tests; tests LOC `<=11000`.

## Phase 6: User Story 4 — Declarative Live Core (P2, stage pr4)

**Goal:** один HTTP boundary, четыре contexts, fully declarative CRUD и immediate LIFO cleanup.

**Independent test:** временный третий descriptor выполняется generic CRUD test без изменения `tests/live/test_crud.py`; затем временный descriptor удаляется.

- [ ] T056 [P] [US4] Создать один `LiveApiClient` и typed bootstrap/oracle helper functions в `tests/live/api.py` с limit `<=350` logical lines; `BootstrapApiClient` и `DirectApiOracle` не создавать.
- [ ] T057 [US4] Добавить request/status/shape/redaction/delete-idempotency tests `LiveApiClient` в `tests/unit/test_live_api.py`.
- [ ] T058 [P] [US4] Определить `LiveEnvironment`, `LiveSession`, `LiveCase`, `SandboxSession`, context managers и one-ExitStack cleanup в `tests/live/session.py` с limit `<=450` logical lines.
- [ ] T059 [US4] Переписать `tests/live/conftest.py` с limit `<=300` logical lines на ровно `live_environment`, `live_session`, `live_case`, `sandbox_session` плюс pytest hooks; удалить one-field fixtures и `getfixturevalue`.
- [ ] T060 [US4] Перевести все `tests/live/test_*.py` и `tests/live/extended/test_*.py` на explicit context fields из T059; string fixture selectors удалить.
- [ ] T061 [P] [US4] Реализовать fully declarative generic `CrudDescriptor[T]` с обязательным `profile` и descriptors labels/projects в `tests/live/crud_descriptors.py`; единственный registry называется `CRUD_CASES` (старое имя `CRUD_DESCRIPTORS` удаляется); `delete` сделать idempotent.
- [ ] T062 [US4] Переписать `tests/live/test_crud.py` на exact 11-step algorithm из `contracts/live-core.md` без resource-specific branch/cast/lookup; unicode name variants удаляются — имя всегда `live_case.unique_name`; удалённые node IDs записать в `tests/duplicate-removal-map.json` с retained `test_crud_round_trip[<id>]`.
- [ ] T063 [US4] Создать registry/source-AST tests unique IDs, all callables, no descriptor references и no identity branch в `tests/unit/test_live_crud_descriptors.py`.
- [ ] T064 [US4] Перенести direct live executor callables в `tests/live/operations.py` с limit `<=350` logical lines и связать их только через `OperationCase.live.owner`; удалить manual operation-ID sets из `tests/live/resources.py`; переписать `tests/live/extended/test_live_operations.py`: параметризовать по `OPERATION_CASES`, отобранным по `case.live.mode == "extended"` и `case.live.owner.startswith("direct:")`, с id=`case.sdk_method`; тело теста — `DIRECT_EXECUTORS[case.sdk_method](live_session, live_case)`; module `pytestmark` (`live`, `live_extended`, `serial`) не меняется.
- [ ] T064a [US4] Переименовать `tests/live/test_errors.py::ERROR_CASES` в `LIVE_ERROR_CASES` (имя `ERROR_CASES` зарезервировано за каноническим registry по FR-012 и проверкой №2); содержимое cases, assertions и node IDs сохраняется; запись в `tests/duplicate-removal-map.json` не добавляется.
- [ ] T065 [US4] Переписать `tests/live/test_live_command_coverage.py` на проверку 111 `LivePolicy`, direct executor targets, CRUD descriptor targets, sandbox ownership и closed unrunnable reasons.
- [ ] T066 [US4] Заменить `ResourceRegistry`, `CleanupRegistry` и late registration одним `LiveCase.defer_cleanup`/`ExitStack`; обычные live operation helpers оставить в `tests/live/operations.py`.
- [ ] T067 [US4] Сократить compose/daemon/bootstrap lifecycle до `<=650` logical lines в `tests/live/backend.py`; session construction держать только в `tests/live/session.py`.
- [ ] T068 [US4] Удалить `tests/live/environment.py` и `tests/live/oracle.py`; переписать `tests/live/diagnostics.py` как test-only diagnostics hooks/assertions поверх `tools.live_support.diagnostics`; сократить `tests/live/resources.py` до sandbox-only temporary module `<=800` lines; консолидировать retained harness tests и обновить duplicate map:
  - `test_live_oracle.py` + `test_live_bootstrap.py` → `tests/unit/test_live_api.py`;
  - `test_live_compose.py` → `tests/unit/test_live_backend.py`;
  - `test_live_settings.py` + `test_canary_environment.py` + `test_live_profile.py` + `test_live_compatibility_report.py` → `tests/unit/test_live_environment.py`;
  - unit `test_live_diagnostics.py` остаётся единственным diagnostics test module;
  - `test_live_mutation_cases.py` → `tests/unit/test_live_support_tools.py` (миграция в T054);
  - `test_live_sandbox_support.py` — superseded, удаляется в T074.
- [ ] T069 [US4] Обновить live commands/architecture в `tests/live/README.md`, реализовать stage `pr4` согласно stage-activation table в `contracts/quality-gates.md`, выполнить smoke/extended runs и stage `pr4`, сохранить `.artifacts/test-suite-consolidation/pr4-gate.txt`.

**US4 exit gate:** one HTTP client; four fixtures; branch-free CRUD; immediate LIFO cleanup; live support `<=3000`; smoke/extended contracts green.

## Phase 7: User Story 5 — Isolated Sandbox and Final Gates (P3, stage pr5)

**Goal:** изолировать sandbox domain и достигнуть финальных LOC/file budgets без потери deterministic/canary behavior.

**Independent test:** deterministic fake-OpenCode workflow и real-provider canary проходят через новые three-phase functions; ordinary live session не создаёт sandbox resources.

- [ ] T070 [US5] Создать immutable `PreparedSandbox`, `CompletedAssignment`, `SandboxVerification` в `tests/live/sandbox/models.py`, filesystem policy в `tests/live/sandbox/policy.py` и exports в `tests/live/sandbox/__init__.py`.
- [ ] T071 [US5] Реализовать ровно `prepare_sandbox`, `run_assignment`, `verify_sandbox` с immediate cleanup в `tests/live/sandbox/workflow.py`.
- [ ] T072 [US5] Перевести `tests/live/test_agent_sandbox.py`, `tests/live/extended/test_agent_sandbox_failures.py`, `tests/live/extended/test_opencode_canary.py` на `sandbox_session` и three-phase workflow.
- [ ] T073 [US5] Добавить phase-transition, cleanup-order, filesystem-policy, diagnostics и no-ordinary-session-side-effect tests в `tests/unit/test_live_sandbox.py`.
- [ ] T074 [US5] Удалить migrated sandbox code и final temporary `tests/live/resources.py`; удалить superseded sandbox helper tests и обновить `tests/duplicate-removal-map.json`.
- [ ] T075 [US5] Реализовать final architecture limits `tests_python<=10500`, `live_support_python<=2500`, max file `<=800`, no stale files/types/imports/skips согласно stage-activation table в `contracts/quality-gates.md` в `scripts/check_test_architecture.py`.
- [ ] T076 [US5] Обновить final test architecture, five-stage commands и deletion rules в `README.md`, `AGENTS.md`, `tests/live/README.md`.
- [ ] T077 [US5] Выполнить Ruff, strict mypy, full offline, architecture, coverage, mutation, package, live smoke, live extended и real-provider canary; сохранить `.artifacts/test-suite-consolidation/final-gate.txt`.
- [ ] T078 [US5] Записать final measured metrics и source/baseline SHAs в `.artifacts/test-suite-consolidation/final-metrics.json`; `tests/quality-baseline.json` не изменять.

**US5 exit gate:** final budgets выполнены; ordinary/live/sandbox/package boundaries прямые; all quality/live/canary contracts green.

## Dependencies

- Phase 1 blocks Phase 2.
- Phase 2 blocks every user story.
- US1 blocks US2–US5 because baseline and behavioral contracts must exist before deduplication.
- US2 blocks US3–US5 because live policy and component cases depend on canonical operation metadata.
- US3 blocks US4 because live scripts must already import `tools/live_support`.
- US4 blocks US5 because sandbox extraction depends on final live contexts and cleanup owner.
- Final completion requires every exit gate and T077.

## Parallel Execution Examples

- T025 can run after T023 while T024 is implemented in a separate file.
- T037 can run after T033–T035 while T036 deletes independent catalog files.
- T040, T041 and T046 can run in parallel after US2.
- T051 and T052 can run in parallel before T053.
- T053 depends on T046 and T050 (guard-узлы должны существовать до записи stage-gated keys в manifest).
- T056, T058 and T061 can run in parallel before T059/T062.

## MVP Scope

MVP = Phase 1 + Phase 2 + US1 + US2. Он даёт green process boundary, behavior-based gates, один `OperationCase` catalog и один component round trip. Feature нельзя считать завершённой до прохождения US3–US5 и final budgets.

## Implementation Strategy

1. Сначала исправить достоверность измерений.
2. Создать нового consumer до удаления старого source.
3. Удалять duplicate вместе с traceability record.
4. Не смешивать два stage в одном repair cycle.
5. После каждого task group выполнять ближайший targeted test; после phase — полный exit gate.
