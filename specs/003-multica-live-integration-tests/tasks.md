# Задачи реализации: Live-интеграционное тестирование `multica-py`

**Feature ID:** `003-multica-live-integration-tests`  
**Основание:** `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/live-test-interface.md`, `contracts/bootstrap-http.md`, `contracts/presence-and-exceptions.md`  
**Статус:** Ready for implementation

## Формат и правила выполнения

- Все команды live-набора выполняют проверяемые действия только через публичный Python API и настоящий Multica CLI.
- Прямой HTTP-клиент используется только для bootstrap, arrange, независимого assert и cleanup; routes from `contracts/bootstrap-http.md`.
- Каждый тестовый ресурс получает уникальный run/test prefix и регистрируется для cleanup.
- Live smoke не должен требовать frontend, browser, daemon, email provider, AI provider или внешние credentials.
- Blocking target: `v0.3.35` / commit `4416313f8f7f801df8b7f5072087da8a6502a89c`; `latest` and placeholders forbidden.
- Every live test MUST carry `@pytest.mark.live` plus `live_smoke` or `live_extended`.
- Тесты сначала добавляются в падающем или неполном состоянии, затем реализуется минимальный harness/behavior, необходимый для их прохождения.

## Phase 1 — Setup

**Цель:** создать отдельный, явно управляемый слой live-тестов и зафиксировать его внешний контракт.

- [X] T001 Создать пакет live-тестов и базовую структуру каталогов в `tests/live/__init__.py`
- [X] T002 В `pyproject.toml`: добавить `httpx` в dependency-group `test` only; register strict markers `live`, `live_smoke`, `live_extended`, `destructive`, `serial`; set `addopts` to include `-m "not live"`; add mypy override module `tests.live.*`
- [X] T003 Verify committed `contracts/multica-live-target.toml` matches pin (`v0.3.35`, index digest `sha256:656dd76e866f636863a6fc034f04165227e35f427e526914ea2c9848f8f55e30`, amd64 digest present) and wire loader validation rejecting placeholders/`latest`
- [X] T004 [P] Описать prerequisites, переменные окружения, команды smoke/extended и правила безопасной отладки в `tests/live/README.md`
- [X] T005 [P] Добавить шаблон локальных non-secret переменных окружения в `tests/live/.env.example`
- [X] T006 [P] Добавить каталог live diagnostics и временные profile/home артефакты в `.gitignore`
- [X] T007 Реализовать CLI-обёртку `scripts/run_live_tests.py` with `--resolve-cli` / env `MULTICA_LIVE_RESOLVE_CLI=1`, fail-closed input validation, and CI forbid of `MULTICA_LIVE_KEEP_ENV`
- [X] T008 [P] Создать resolver exact Multica target (release CLI path + digest) и проверку фактической версии CLI в `scripts/resolve_multica_target.py`

**Gate Phase 1:** `uv run pytest -m "not live"` не запускает Docker, а `scripts/run_live_tests.py --help` документирует обязательные inputs.

## Phase 2 — Foundational prerequisites

**Цель:** построить session-scoped harness, без которого нельзя независимо реализовать ни один пользовательский сценарий.

- [X] T009 Реализовать immutable модели `CompatibilityTarget`, `LiveSettings`, `LiveTestRun` и загрузку target/environment с bounded validation в `tests/live/settings.py`
- [X] T010 [P] Добавить unit-тесты target parsing, запрета `latest`, отсутствующего CLI, loopback existing URL и timeout bounds в `tests/unit/test_live_settings.py`
- [X] T011 Реализовать lifecycle `docker compose` per `contracts/bootstrap-http.md` (env allowlist, services `postgres`/`backend`, `/readyz` JSON success body, timeout/poll bounds, `down -v --remove-orphans`) в `tests/live/compose.py`
- [X] T012 [P] Добавить unit-тесты построения subprocess argv, readiness timeout и teardown без shell invocation в `tests/unit/test_live_compose.py`
- [X] T013 Реализовать bootstrap sequence exactly as `contracts/bootstrap-http.md` §2 (`/auth/send-code` → `/auth/verify-code` code `888888` → `/api/tokens` `expires_in_days=1` → two `/api/workspaces`) в `tests/live/bootstrap.py`
- [X] T014 Реализовать secret wrapper, `TestIdentity`, `WorkspaceContext` и redacted `repr` для credentials в `tests/live/bootstrap.py`
- [X] T015 [P] Добавить unit-тесты bootstrap request sequence, status handling и отсутствия secrets в repr/error excerpts в `tests/unit/test_live_bootstrap.py`
- [X] T016 Реализовать writer временного CLI profile with exact keys `server_url`/`app_url`/`workspace_id`/`token` and mode `0600` в `tests/live/profile.py`
- [X] T017 [P] Добавить unit-тесты profile path, exact JSON keys, mode `0600`, и запрета записи в реальный HOME в `tests/unit/test_live_profile.py`
- [X] T018 Реализовать минимальный direct HTTP oracle с raw JSON, allowlisted headers и explicit timeouts в `tests/live/oracle.py`
- [X] T019 [P] Добавить unit-тесты oracle response, отсутствующего/null/empty поля и исключения Authorization из diagnostics в `tests/unit/test_live_oracle.py`
- [X] T020 Реализовать dependency-aware `ResourceRegistry` с reverse-topological cleanup и сохранением primary failure в `tests/live/resource_registry.py`
- [X] T021 [P] Добавить unit-тесты cleanup order, already-absent, partial failure и cyclic dependency rejection в `tests/unit/test_live_resource_registry.py`
- [X] T022 Реализовать allowlist-based `DiagnosticCollector`, bounded logs, atomic writes и exact-secret redaction в `tests/live/diagnostics.py`
- [X] T023 [P] Добавить positive/negative unit-тесты redaction, log truncation и разделения primary/cleanup failures в `tests/unit/test_live_diagnostics.py`
- [X] T024 Собрать session fixtures `live_settings`, `compatibility_target`, `live_environment`, `test_identity`, два workspace, два SDK-клиента, oracle, registry и diagnostics в `tests/live/conftest.py`
- [X] T025 Добавить pytest hooks для классификации setup/test/teardown failure и формирования diagnostic bundle в `tests/live/conftest.py`
- [X] T026 Добавить session teardown postcondition audit контейнеров, volumes, временного HOME и profile в `tests/live/conftest.py`
- [X] T027 [P] Добавить тест resolver/version report и fail-closed несовпадения CLI target в `tests/unit/test_resolve_multica_target.py`

**Gate Phase 2:** пустой live session способен поднять минимальный stack, bootstrap-нуть identity/workspaces, создать SDK clients и гарантированно удалить environment после pass и setup failure.

## Phase 3 — US1: Быстрая проверка интеграции в pull request (P1)

**Цель:** дать компактный блокирующий сигнал, что реальная цепочка SDK → CLI → backend работает.

**Independent test criterion:** один запуск `pytest -m live_smoke tests/live/test_bootstrap.py` подтверждает readiness, exact target, SDK workspace read, profile isolation и полный cleanup без frontend/daemon.

- [X] T028 [US1] Добавить smoke-тест `/readyz`, verified compatibility target и фактической версии CLI в `tests/live/test_bootstrap.py`
- [X] T029 [US1] Добавить smoke-тест `MulticaClient.workspaces.list()` asserting primary bootstrap workspace id is present in typed decode в `tests/live/test_bootstrap.py`
- [X] T030 [US1] Добавить smoke-тест, подтверждающий временный HOME/profile и отсутствие чтения либо изменения пользовательского `~/.multica` в `tests/live/test_bootstrap.py`
- [X] T031 [US1] Добавить negative setup-тест неготового backend: canonical injection = start compose then `docker compose stop backend`, set `MULTICA_LIVE_READY_TIMEOUT=10`, assert `LiveSetupError` stage `readyz` plus last readiness diagnostics в `tests/live/test_bootstrap.py`

## Phase 4 — US2: Round-trip основных ресурсов (P1)

**Цель:** проверить реальное сохранение и чтение основных сущностей, специальных строк и составных связей.

**Independent test criterion:** labels CRUD и issue workflow проходят через SDK/CLI, а oracle независимо подтверждает create/update/delete и связанные project/labels/comment.

- [X] T034 [P] [US2] Добавить label CRUD методы direct oracle и cleanup callbacks в `tests/live/oracle.py`
- [X] T035 [US2] Добавить полный create/get/list/update/delete label round-trip через SDK с oracle assertions в `tests/live/test_labels.py`
- [X] T036 [US2] Добавить label round-trip для Unicode, emoji, пробелов и точного значения color в `tests/live/test_labels.py`
- [X] T037 [P] [US2] Добавить project/issue/comment arrange, read и cleanup методы direct oracle в `tests/live/oracle.py`
- [X] T038 [US2] Добавить issue workflow: project, две labels, Unicode/multiline description, create/get/list/filter в `tests/live/test_issue_workflow.py`
- [X] T039 [US2] Добавить issue update status/priority/title, attach/detach label и comment round-trip в `tests/live/test_issue_workflow.py`
- [X] T040 [US2] Добавить проверку dependency-safe cleanup issue → comment/links → labels/project и oracle-confirmed absence в `tests/live/test_issue_workflow.py`

## Phase 5 — US3: Семантика частичных обновлений (P1)

**Цель:** зафиксировать матрицу `Unset` / empty string / set value / empty label collection без изменения несвязанных полей.

**Independent test criterion:** cases `P-OMIT`, `P-EMPTY`, `P-SET`, `C-EMPTY` from `contracts/presence-and-exceptions.md` pass with oracle confirmation.

- [X] T041a [US3] Align `projects.create` / `projects.update` CLI argv with upstream `--title` (map public `name`→`--title`) and add unit coverage in `tests/unit/resources/test_projects.py`
- [X] T041b [US3] Wire `Unset` defaults into `ProjectUpdateRequest` and argv omission rules in `src/multica_py/models/projects.py` and `src/multica_py/resources/projects.py`
- [X] T041c [US3] Make `description=None` raise public `ValidationError` (CLI cannot emit JSON null); cover in `tests/unit/resources/test_projects.py`
- [X] T041 [P] [US3] Добавить oracle helpers создания и raw чтения project без SDK normalization в `tests/live/oracle.py`
- [X] T042 [US3] Добавить тест case `P-OMIT` (update title only, description unchanged) в `tests/live/test_projects.py`
- [X] T043 [US3] Добавить тест case `P-EMPTY` vs `P-OMIT` и oracle-only `P-NULL-HTTP` в `tests/live/test_projects.py`
- [X] T044 [US3] Добавить тест case `C-EMPTY` (issue labels detach-all → oracle `[]`) в `tests/live/test_projects.py` или `tests/live/test_issue_workflow.py`
- [X] T045 [US3] Добавить assertions case `P-SET`, неизменности unrelated fields и `updated_at` после update в `tests/live/test_projects.py`

## Phase 6 — US4: Ошибки и безопасность диагностики (P1)

**Цель:** проверить публичные Python exceptions на реальных backend/CLI ошибках и исключить утечку credentials.

**Independent test criterion:** mapping from `contracts/presence-and-exceptions.md` §3; generated bundle не содержит точные PAT/JWT/secrets.

- [X] T046a [US4] Wire CLI exit-code → exception subclass mapping in `src/multica_py/_internal/transport.py` per `contracts/presence-and-exceptions.md` §1.2; unit-test in `tests/unit/test_transport_errors.py`
- [X] T046 [P] [US4] Добавить fixtures invalid PAT, inaccessible workspace (secondary client + primary resource id), missing ID и closed loopback port в `tests/live/conftest.py`
- [X] T047 [US4] Добавить тест invalid PAT → `AuthenticationError` с безопасным message в `tests/live/test_errors.py`
- [X] T048 [US4] Добавить тесты missing resource → `NotFoundError` и invalid status → `ValidationError` в `tests/live/test_errors.py`
- [X] T048b [US4] Добавить access-collapse тест: primary label via secondary client → `NotFoundError` в `tests/live/test_errors.py`
- [X] T049 [US4] Добавить closed port → `NetworkError` тест в `tests/live/test_errors.py`
- [X] T050 [US4] Добавить serial destructive тест остановки backend mid-operation → `NetworkError` и отсутствия оставшегося CLI process в `tests/live/test_errors.py`
- [X] T051 [US4] Добавить synthetic wrapper executable tests: exit `2` → `NetworkError`, exit `99` → `CommandExecutionError` via `ClientConfig.executable` в `tests/live/test_errors.py`
- [X] T052 [US4] Добавить generated diagnostic bundle test, сканирующий PAT, JWT, verification code, JWT secret и database password в `tests/live/test_errors.py`
- [X] T053 [US4] Добавить assertion, что diagnostic bundle содержит target, stage, resource, operation, exit code и redacted service logs в `tests/live/test_errors.py`

## Phase 7 — US5: Изоляция workspace и запусков (P1)

**Цель:** исключить утечку контекста между workspace, клиентами и последовательными тестовыми запусками.

**Independent test criterion:** объект workspace A недоступен из B, parallel read-only calls не смешивают context, закрытие клиента A не влияет на B, повторный запуск не видит старые данные/resources.

- [X] T054 [US5] Добавить тест невидимости label/project workspace A через list/get клиента workspace B в `tests/live/test_workspace_isolation.py`
- [X] T055 [US5] Добавить controlled concurrency read-only команд двух клиентов и проверку неизменности workspace context в `tests/live/test_workspace_isolation.py`
- [X] T056 [US5] Добавить тест закрытия primary client без нарушения работы secondary client в `tests/live/test_workspace_isolation.py`
- [X] T057 [P] [US5] Добавить unit-тест unique run/resource naming, truncation и hash suffix для upstream limits в `tests/unit/test_live_naming.py`
- [X] T058 [US5] Добавить serial тест postcondition отсутствия Compose containers, volumes и profile artifacts после принудительного failed run в `tests/live/test_workspace_isolation.py`
- [X] T032 [US5] Добавить blocking job `live-smoke` on Ubuntu/Python 3.12 with resolver mode, digest pull, 10-minute timeout, PR concurrency, and SC-003 budgets in `.github/workflows/ci.yml` (only after T028–T058 exist)
- [X] T033 [US5] Добавить JUnit + redacted diagnostic artifact upload `if: failure()`, retention-days 7, after secret scan in `.github/workflows/ci.yml`

## Phase 8 — US6: Периодическая расширенная совместимость (P2)

**Цель:** обнаруживать schema drift, pagination/filter regressions и расширенные проблемы данных вне PR critical path.

**Independent test criterion:** `pytest -m "live_smoke or live_extended" tests/live` на pinned target; scheduled workflow отдельно сообщает upstream-main as non-blocking notice.

- [X] T059 [US6] Добавить pagination тест: create 12 issues, `page_size=10`, no duplicates, cursor completes в `tests/live/extended/test_pagination.py`
- [X] T060 [US6] Добавить filter тест `status` + label id для issues в `tests/live/extended/test_pagination.py`
- [X] T061 [US6] Добавить raw-response тесты absent/null/empty/unknown fields без скрытой SDK normalization в `tests/live/extended/test_optional_fields.py`
- [X] T062 [US6] Добавить timezone-aware timestamp precision/offset и `created_at <= updated_at` проверки в `tests/live/extended/test_timestamps.py`
- [X] T063 [US6] Добавить attachment upload/metadata/download/SHA-256/delete for 1024-byte payload plus empty/Unicode/spaced filenames; fail if unsupported на pinned target в `tests/live/extended/test_attachments.py`
- [X] T064 [P] [US6] Добавить parametrized read-only decode smoke for `agents.list`, `skills.list`, `autopilots.list` в `tests/live/extended/test_read_only_resources.py`
- [X] T065 [US6] Реализовать versioned pinned-vs-upstream compatibility report в `scripts/run_live_tests.py`
- [X] T066 [US6] Создать weekly и `workflow_dispatch` extended workflow с inputs `multica_ref`, `image_tag`, `mode` в `.github/workflows/live-extended.yml`
- [X] T067 [US6] Добавить раздельную интерпретацию pinned regression и non-blocking upstream compatibility signal в `.github/workflows/live-extended.yml`

## Phase 9 — US7: Независимая проверка результата (P2)

**Цель:** доказать, что критичные тесты не подтверждают одинаковую ошибку SDK при записи и чтении.

**Independent test criterion:** данные, созданные SDK, читаются raw HTTP oracle; данные для update создаются oracle; intentional mutation SDK flag/decoder ломает соответствующий тест.

- [X] T068 [US7] Добавить отдельный cross-interface тест SDK-create → oracle-read для точных label fields в `tests/live/test_oracle_consistency.py`
- [X] T069 [US7] Добавить отдельный cross-interface тест oracle-create → SDK-update → oracle-read для project omitted/null semantics в `tests/live/test_oracle_consistency.py`
- [X] T070 [US7] Добавить SDK-delete → oracle-404 проверку для простого ресурса в `tests/live/test_oracle_consistency.py`
- [X] T071 [US7] Automate SC-002 mutation gate in `scripts/run_live_tests.py --mutation-check`: (1) temporarily patch `projects.update` argv builder to emit `--name` instead of `--title` and expect live project update test fail; (2) temporarily strip a required field from label JSON decoder fixture path / force `OutputShapeError` on label get and expect fail; (3) temporarily map CLI exit `4` to `CommandExecutionError` instead of `NotFoundError` and expect not-found live test fail; restore sources after each case; exit nonzero if any mutation still passes

## Phase 10 — Polish and cross-cutting quality

**Цель:** завершить трассировку, документацию, стабильность и security gates для релизного использования.

- [X] T072 [P] Добавить таблицу трассировки FR/SC → конкретные live tests и markers в `tests/live/README.md`
- [X] T073 [P] Добавить пользовательский раздел о live smoke, extended suite и compatibility target update в `README.md`
- [X] T074 Добавить quality gate команды format/lint/mypy/non-live/live-smoke/build в `scripts/run_live_tests.py`
- [X] T075 Добавить repeat mode для десяти последовательных smoke runs и сводку flaky/runtime результатов в `scripts/run_live_tests.py`
- [X] T076 Добавить target update procedure с contract check, extended run и digest verification в `tests/live/README.md`
- [X] T077 Выполнить полный quality-gate прогон и исправить обнаруженные lint/type/test проблемы в `tests/live/`
- [X] T078 Выполнить cleanup/security audit после pass, test failure и setup failure и зафиксировать результат в `tests/live/README.md`

## Зависимости

### Порядок фаз

1. Phase 1 блокирует Phase 2.
2. Phase 2 блокирует все user-story phases.
3. US1 bootstrap tests (T028–T031) должны пройти до resource workflows; CI job T032–T033 waits until US1–US5 suites exist.
4. US2–US5 независимы после Phase 2 и могут разрабатываться параллельно, но общий MVP gate требует прохождения всех P1 stories.
5. US3 live asserts (T042+) depend on T041a–T041c SDK presence/`--title` work.
6. US6 зависит от стабильного smoke harness и CI artifact contract (post-MVP).
7. US7 T068–T071 входят в MVP after US2/US3 resources exist.
8. Phase 10 polish including T075 enters MVP after smoke suites are green.

### Зависимости пользовательских сценариев

| Story | Зависит от | Может проверяться независимо |
|---|---|---|
| US1 | Phase 1–2 | Да, через bootstrap/workspace smoke |
| US2 | Phase 1–2, US1 environment gate | Да, через labels + issue workflow |
| US3 | Phase 1–2, oracle | Да, через project partial update |
| US4 | Phase 1–2, diagnostics | Да, через error matrix и leak scan |
| US5 | Phase 1–2, два workspace | Да, через isolation suite |
| US6 | Stable P1 harness | Да, через extended selector/workflow |
| US7 | Oracle + US2/US3 resources | Да, через cross-interface consistency tests |

## Возможности параллельной реализации

- После T009 могут параллельно выполняться пары T011/T012, T013–T015, T016/T017, T018/T019, T020/T021 и T022/T023, поскольку они затрагивают независимые модули.
- После T024 команды могут независимо реализовывать US2, US3, US4 и US5; синхронизация нужна только при изменении общих fixtures в `tests/live/conftest.py`.
- В US2 задачи T034 и T037 могут выполняться параллельно до объединения в issue workflow.
- В US6 задачи T059–T064 могут выполняться параллельно по отдельным test modules.
- Документация T072 и T073 может выполняться параллельно после стабилизации названий markers/commands.

### Пример параллельного выполнения

```text
Developer A: T011 → T012 → T024
Developer B: T013 → T014 → T015
Developer C: T018 → T019 → T034/T037
Developer D: T020 → T021 и T022 → T023

После foundation:
Developer A: US2
Developer B: US3
Developer C: US4
Developer D: US5
```

## MVP scope

Минимальный блокирующий релиз включает:

- Phase 1 и Phase 2 полностью;
- US1–US5 полностью including T032–T033 CI job after suites exist;
- US3 SDK prerequisites T041a–T041c;
- US4 SDK exit-code mapping T046a and access-collapse T048b;
- US7 MVP slice T068–T070 plus SC-002 automation T071;
- SC-004 repeat mode T075;
- Phase 10 задачи T072–T074, T077 и T078.

US6 (T059–T067) and extended target-update docs T076 are follow-up after PR smoke stabilizes.

## Стратегия реализации

1. **Foundation first:** сначала добиться одного воспроизводимого workspace read и безусловного teardown.
2. **Simple resource slice:** добавить label CRUD как вертикальный тест всей цепочки.
3. **State semantics:** добавить project partial update с oracle.
4. **Composite workflow:** добавить issue/project/labels/comment и dependency cleanup.
5. **Failure behavior:** только после стабильного happy path добавить destructive/error tests и diagnostics.
6. **Isolation and CI:** подтвердить два workspace, повторный запуск и blocking job.
7. **Extended compatibility:** вынести дорогие pagination/attachments/schema-drift сценарии в schedule/manual workflow.

## Phase 11: Convergence

Remaining gaps found by `/speckit-converge` against implemented code (all prior T001–T078 marked complete).

- [X] T079 Fix ruff `I001` unsorted imports in `tests/live/test_bootstrap.py` and re-run `uv run ruff check tests/live scripts` clean per T077 (`partial`)
- [X] T080 Enforce SC-003 sub-budgets in `.github/workflows/ci.yml` and/or `run.json`: env startup ≤180s and test phase ≤120s (not only total wall ≤300s) per Spec §NFR-006 / §SC-003 and `contracts/live-test-interface.md` §10 (`partial`)
- [X] T081 Align FR/SC traceability table test names in `tests/live/README.md` with actual functions in `tests/live/test_bootstrap.py` (and other drifted rows) per T072 (`partial`)
- [X] T082 Verify `scripts/run_live_tests.py --mutation-check` patch strings still match current `projects.py` / transport / decoder sources after Wave 2–4 edits; refresh MUTATION_CASES if needed per SC-002 / T071 (`partial`)

## Format validation

Все implementation tasks используют формат `- [ ] TNNN [P?] [US?] Description with file path`. Setup, foundation и polish задачи не имеют story labels; story tasks содержат ровно один label `[US1]`–`[US7]`.
