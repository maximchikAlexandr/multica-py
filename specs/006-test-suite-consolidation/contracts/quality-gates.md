# Contract: Quality and Architecture Gates

## Stage pr1 capture order

1. Исправить process tests.
2. Заменить offline network smoke hard prohibition test-ом.
3. Запустить весь offline suite с JUnit и branch coverage.
4. Запустить полный configured mutmut scope.
5. Записать `tests/behavioral-coverage.json`.
6. Записать `tests/quality-baseline.json` schema 2.
7. Commit baseline; после этого файл immutable.

Массовое удаление дубликатов до шага 7 запрещено.

## Baseline comparison

Stage fails, если выполняется любое условие:

- statement percent ниже baseline;
- branch percent ниже baseline;
- zone ниже baseline или configured threshold;
- coverage config fingerprint изменён;
- mutation score ниже baseline;
- mutation config fingerprint изменён;
- required operation dimension отсутствует;
- required для данного stage invariant key отсутствует или mapped node отсутствует в full collection;
- duplicate map retained node не существует;
- duplicate map protected contract отсутствует;
- offline duration больше `max(45.0, baseline * 1.5)`;
- stage LOC/package/file limit нарушен.

Baseline behavior fingerprint содержит operation dimension pairs и invariant keys, но не invariant node paths. Traced rename обновляет node path и duplicate map без изменения required contract fingerprint. Collected count печатается и не сравнивается как minimum. Добавление stage-gated invariant keys на stage `pr3` (data-model §7 правило 5) — единственное разрешённое изменение behavior fingerprint после stage `pr1`; оно выполняется последним коммитом stage `pr3` после готовности guard-тестов T046/T050/T053.

## Stage limits

- `pr1`: фиксирует baseline; без нового LOC target.
- `pr2`: tests LOC не выше stage `pr1` baseline.
- `pr3`: tests LOC `<=11000`; fixture tree отсутствует; package paths `=6`.
- `pr4`: live support LOC `<=3000`.
- `final`: tests LOC `<=10500`; live support LOC `<=2500`; max file LOC `<=800`.

## Architecture checks

`scripts/check_test_architecture.py` fails при:

1. Registry-имена `ArgvCase`, `DecodeCase`, `CommandCase`, `OperationDefinition` или `COMMAND_CHECKS` как публичные/модуль-уровневые case-registry типы или константы. Локальные dataclass-контейнеры case-таблиц внутри одного test-модуля, не экспортируемые через `__init__.py` (например, `ProjectResourceDecodeCase` в `tests/unit/test_project_resource_models.py`), разрешены и registry не считаются.
2. Более одного module-level `OPERATION_CASES` или `ERROR_CASES` assignment в `tests/cases/` и публичных registry-модулях; имя `OPERATION_CASES`/`ERROR_CASES` зарезервировано за каноническим registry по FR-012, локальные одноимённые контейнеры вне этих областей должны быть переименованы.
3. Duplicate `(sdk_method, variant_id)`.
4. Не 111 unique operation IDs.
5. Inconsistent live policy variants.
6. `from tests`/`import tests` в `scripts/` или `src/`.
7. `pytest.skip` в `tests/packaging/`.
8. Real-process module без `process` и `serial`.
9. `getfixturevalue` в `tests/live/`.
10. Resource-identity branch/cast/lookup в `tests/live/test_crud.py`.
11. Missing/multiple live owner для operation.
12. Default execution с selected live или packaging node.
13. Stage LOC/file/package violation.
14. `tests/fixtures/json/` после stage `pr3`.
15. Payload размером `>4096` bytes в `tests/cases/payloads.py` или один payload, хранящийся одновременно в Python и `tests/fixtures/golden/`.

## Detection mechanism

Проверки №1–5 используют AST-анализ: class definitions и assignment statements на module level в `tests/cases/` и публичных registry-модулях. Локальные dataclass-контейнеры внутри одного test-модуля, не экспортируемые через `__init__.py` и не используемые другими модулями, разрешены (см. исключение в проверке №1). Поиск по подстроке в исходниках не применяется.

## Real-process module

Проверка №8 применяется только к модулям, параметризованным process-contract IDs и использующим `tests/fixtures/child_process.py`; на текущий snapshot это только `tests/component/test_process_contract.py`. Модули, запускающие короткоживущие fake/subprocess (например, `tests/component/test_fake_opencode_process.py`, contract CLI modules, `tests/unit/test_transport.py`), real-process modules не являются и `serial` не получают.

## Stage activation

Проверка активируется на stage своей задачи; активированные проверки остаются активными на всех последующих stages.

| Stage | Активируемые проверки |
|---|---|
| `pr1` | №8, №12 + baseline self-check |
| `pr2` | №1–5, №11, №15 + tests LOC не выше `pr1` baseline |
| `pr3` | №6, №7, №14 + tests LOC `<=11000` + package paths `=6` |
| `pr4` | №9, №10 + live support LOC `<=3000` |
| `final` | №13 (все финальные лимиты) |
