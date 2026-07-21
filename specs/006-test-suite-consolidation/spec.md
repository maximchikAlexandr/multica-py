# Спецификация: консолидация тестовой базы

**Feature ID:** `006-test-suite-consolidation`  
**Исходный снимок:** `b3a299b36d1ad5bc386b5e4517d2a348d53db31c`  
**Статус:** готово к реализации  
**Область:** тесты, тестовая инфраструктура, CI и packaging; публичное поведение SDK не меняется.

## Обзор

Тестовая база защищает SDK, но повторяет одни и те же контракты операций в unit, component и live-слоях, содержит argv-зависимые fixtures и поддерживает слишком крупный live-framework. Рефакторинг должен удалить повторение и сократить код без снижения фактического тестового покрытия.

Количество pytest-функций и node IDs разрешено уменьшать. Нельзя снижать обязательные поведенческие проверки, statement/branch/zonal coverage, mutation score критического ядра и live-контракты.

## Пользовательские сценарии

### US1 — достоверный quality gate и безопасное удаление дубликатов (P1)

Maintainer исправляет process-тесты, фиксирует зелёный baseline и удаляет дубли только при наличии эквивалентной оставшейся проверки.

**Независимая проверка:** удаление точного дубликата с корректной записью migration map проходит; удаление единственной проверки обязательного поведения блокируется.

**Критерии приёмки:**

1. Zombie-процесс не считается выполняющимся, но тест ждёт его фактического reap.
2. После process-теста не остаётся выполняющихся потомков.
3. Raw test count может уменьшиться и не используется как нижняя граница.
4. Снижение coverage, mutation score или обязательного behavior dimension блокирует приёмку PR.
5. Любая попытка socket/HTTP-вызова под monkeypatch-запретом invariant `network.offline-hard-fail` немедленно падает (см. FR-018).

### US2 — единый каталог `OperationCase` (P1)

Maintainer описывает каждый вариант SDK-операции один раз. Unit и component executors используют один и тот же каталог, но проверяют разные границы.

**Независимая проверка:** временно добавленный `OperationCase` автоматически собирается unit и component executors без второй записи; после проверки временная запись удаляется.

**Критерии приёмки:**

1. Все 111 guard-eligible операций присутствуют в одном registry.
2. Unit executor проверяет точный transport call и decoded result.
3. Component executor одним round trip проверяет argv, fake process boundary и decoded result.
4. Ошибочные сценарии находятся только в `ERROR_CASES`: один `ErrorCase` на failure-режим операции, private-helper assertions не переносятся.
5. Fake CLI получает ответ явно и никогда не выбирает fixture по фактическому argv.

### US3 — компактные offline contracts, tooling и packaging (P2)

Maintainer получает небольшой contract-suite, один реальный package build и прямое направление зависимостей.

**Независимая проверка:** package workflow строит один wheel и один sdist, валидирует их без skip и устанавливает один и тот же wheel шестью зафиксированными путями.

**Критерии приёмки:**

1. Per-command JSON fixture tree и дублирующие payload constants отсутствуют.
2. `test_upstream_contract_quickstart.py` отсутствует.
3. Exhaustive upstream semantics проверяются в unit; subprocess contract содержит только boundary cases.
4. Отсутствующий `dist/` является failure в artifact job, а не skip.
5. `scripts/` и `src/` не импортируют `tests.*`.
6. Общий operational код scripts/tests расположен в `tools/live_support/`.

### US4 — прямой и декларативный live core (P2)

Maintainer читает live-сценарий сверху вниз. Стандартный CRUD полностью задаётся descriptor-ом, а общий executor не знает конкретных ресурсов.

**Независимая проверка:** временный третий CRUD descriptor собирается и выполняется без изменения `tests/live/test_crud.py`; после проверки временный descriptor удаляется.

**Критерии приёмки:**

1. `CrudDescriptor` содержит все resource-specific callables.
2. CRUD executor не содержит branch (`if`/`match`), `cast`, строкового или mapping lookup, ключом которых является identity ресурса или descriptor ID.
3. Cleanup регистрируется сразу после успешного side effect и выполняется LIFO.
4. Bootstrap и oracle используют один `LiveApiClient`.
5. `tests/live/conftest.py` публикует ровно четыре fixture-контекста.
6. Live policy каждой операции хранится рядом с соответствующим `OperationCase`.

### US5 — изолированный agent sandbox (P3)

Maintainer изменяет sandbox workflow, не затрагивая обычные live CRUD/operation tests.

**Независимая проверка:** deterministic fake-OpenCode workflow и real-provider canary сохраняют filesystem policy, diagnostics и cleanup audit после переноса в изолированный package.

**Критерии приёмки:**

1. Sandbox workflow состоит ровно из фаз `prepare_sandbox`, `run_assignment`, `verify_sandbox`.
2. Каждая фаза получает полностью инициализированный immutable phase record.
3. Sandbox cleanup регистрируется немедленно.
4. Обычный live session не создаёт sandbox resources.

## Функциональные требования

- **FR-001:** Источником является только snapshot `b3a299b36d1ad5bc386b5e4517d2a348d53db31c` и актуальный аудит этого snapshot.
- **FR-002:** Новый baseline MUST быть снят после исправления process-тестов и до массового удаления дубликатов.
- **FR-003:** Количество тестов MAY уменьшаться; minimum node-count gate MUST быть удалён.
- **FR-004:** Coverage MUST защищаться checked-in operation dimensions и named invariants.
- **FR-005:** Каждый удалённый test node MUST ссылаться на существующий retained node и защищаемый contract.
- **FR-006:** Statement, branch, zonal coverage и mutation score MUST быть не ниже baseline.
- **FR-007:** Coverage и mutation configuration fingerprints MUST совпадать с baseline.
- **FR-008:** Один deterministic child-process harness MUST покрывать cancellation, timeout, SIGTERM escalation и descendant cleanup.
- **FR-009:** Real-process tests — тесты, параметризованные process-contract IDs и использующие `tests/fixtures/child_process.py` (на текущий snapshot это только `tests/component/test_process_contract.py`) — MUST иметь markers `process` и `serial`, bounded finalizer и per-test timeout 20 секунд.
- **FR-010:** Global offline emergency timeout MUST быть 30 секунд с method `signal`; default pytest selection MUST исключать markers `live` и `packaging`; live runs MUST передавать `--timeout=0`.
- **FR-011:** Единственный тип обычного operation case MUST называться `OperationCase`.
- **FR-012:** Единственные ordinary/error registries MUST называться `OPERATION_CASES` и `ERROR_CASES`.
- **FR-013:** Все 111 guard-eligible operation IDs MUST присутствовать в `OPERATION_CASES`.
- **FR-014:** `ArgvCase`, `DecodeCase`, `CommandCase`, `COMMAND_CHECKS` и recursive private transport patch MUST быть удалены.
- **FR-015:** Fake CLI MUST читать explicit response file, писать explicit invocation record и записывать только allowlisted environment keys.
- **FR-016:** Payload до 4096 bytes MUST храниться в Python case data; payload больше 4096 bytes MUST храниться в `tests/fixtures/golden/`.
- **FR-017:** `tests/fixtures/json/` MUST быть удалён целиком.
- **FR-018:** Offline network contract является named invariant `network.offline-hard-fail` и реализуется одним prohibition test-ом, который через monkeypatch запрещает socket creation/connect и `httpx` transport calls так, что любая попытка network call немедленно падает.
- **FR-019:** Upstream contract boundary MUST состоять ровно из шести модулей, перечисленных в `plan.md`.
- **FR-020:** Package workflow MUST построить wheel и sdist ровно один раз и использовать один wheel в четырёх pip cells, одном `uv pip` и одном `uv add` path.
- **FR-021:** Wheel MUST исключать `tests`, `scripts`, `tools` и repository state; sdist MUST включать `tools/live_support/`, потому что scripts импортируют его.
- **FR-022:** `tools/live_support/` MUST быть единственным местом shared settings/target/scanner кода и MUST не входить в wheel.
- **FR-023:** `CrudDescriptor` MUST быть полностью декларативным; добавление стандартного CRUD-ресурса MUST менять только descriptor registry и local typed callables.
- **FR-024:** Live cleanup MUST использовать один `contextlib.ExitStack`; audit callback MUST регистрироваться первым и выполняться последним.
- **FR-025:** Единственный HTTP boundary MUST называться `LiveApiClient`; отдельный HTTP client/oracle class запрещён.
- **FR-026:** Public live fixtures MUST быть ровно `live_environment`, `live_session`, `live_case`, `sandbox_session`.
- **FR-027:** Каждая operation MUST иметь ровно одну live policy: direct smoke, direct extended, CRUD smoke/extended, sandbox или unrunnable с closed reason; variants одного operation ID MUST иметь одну и ту же policy.
- **FR-028:** Final architecture gate MUST запрещать imports `tests.*` из `scripts/` и `src/`, stale case types, packaging skips, missing process markers, live policy gaps и files выше 800 logical lines.
- **FR-029:** Final logical Python LOC under `tests/` MUST быть `<= 10500`; live support LOC MUST быть `<= 2500`.
- **FR-030:** Публичный SDK API, production runtime dependencies, supported platforms, upstream semantics и live observable behavior MUST не изменяться.
- **FR-031:** Offline suite duration MUST быть `<= max(45.0, baseline * 1.5)` seconds на каждом compare stage.
- **FR-032:** Если stage gate падает после commit-а дедупликации, дедупликация MUST останавливаться до revert этого commit-а или восстановления retained coverage; `tests/duplicate-removal-map.json` MUST служить источником восстановления.

## Edge cases

- Одна SDK operation имеет несколько presence/payload variants.
- Operation использует `run_text`, `run_bytes` или `spawn`.
- Error case содержит malformed output, stderr-only output, secret argv или nonstandard exit code.
- Процесс завершён, но временно остаётся zombie.
- Cleanup падает после primary test failure; primary failure остаётся главным, cleanup failures прикладываются к diagnostics.
- Operation намеренно не запускается live; policy содержит закрытый reason code.
- Ресурс не соответствует стандартному CRUD contract; он остаётся отдельным scenario и не добавляет branch в generic executor.

## Основные сущности

- `OperationCase`: один вариант публичной SDK operation.
- `ErrorCase`: явный failure variant и public exception oracle.
- Behavioral coverage manifest: обязательные operation dimensions и named invariants.
- Guard-eligible operation IDs: IDs, возвращаемые `tests/_manifest_support.py::guard_eligible_operations()` — manifest entries с `sdk_method` и status, отличным от `unsupported`, из pinned upstream CLI manifest; на source snapshot их ровно 111.
- Duplicate removal map: removed node, retained node и protected contract.
- Quality baseline schema 2: coverage, mutation, behavior, LOC, duration и package-path metrics.
- `CrudDescriptor[T]`: все resource-specific CRUD callables.
- Live contexts: environment, session, case и sandbox session.
- Sandbox phase records: prepared, completed и verified states без nullable partial state.

## Предположения

- Поддерживаемая matrix остаётся Linux/macOS × Python 3.12/3.13.
- `pytest-timeout>=2.4,<3` является единственной новой test dependency.
- `psutil`, Hypothesis, BDD, snapshots, `pytest-cases` и другие test-DSL libraries не добавляются.
- Live acceptance выполняется на pinned Multica target репозитория.

## Вне scope

- Новые SDK methods и изменение public behavior.
- Изменение upstream Multica/backend contracts.
- Windows process-tree guarantees.
- Production refactoring внутри `src/multica_py`.

## Измеримые критерии успеха

- **SC-001:** Все 111 operation IDs и обязательные dimensions сохранены.
- **SC-002:** Statement, branch, zonal coverage и mutation score не ниже repaired baseline.
- **SC-003:** Default execution выбирает ноль live и packaging nodes; unit/contract/component offline suite проходит детерминированно.
- **SC-004:** Process tests не дают zombie false failures и не оставляют running descendants.
- **SC-005:** Unit, component, manifest coverage и live policy используют только `OPERATION_CASES`/`ERROR_CASES`.
- **SC-006:** `tests/fixtures/json/`, stale case types, string check DSL и recursive transport patch отсутствуют.
- **SC-007:** Generic CRUD executor branch-free; labels и projects проходят один algorithm.
- **SC-008:** Packaging содержит ноль conditional skips и один artifact build set.
- **SC-009:** `scripts/` и `src/` содержат ноль imports из `tests.*`.
- **SC-010:** Test LOC `<=10500`, live support LOC `<=2500`, каждый test/support Python file `<=800` logical lines.
- **SC-011:** Live smoke, extended, deterministic sandbox и provider canary сохраняют cleanup, isolation, oracle, diagnostics и secret-scan contracts.
