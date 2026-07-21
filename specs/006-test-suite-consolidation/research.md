# Research: Test Suite Consolidation

Все решения ниже окончательные. Раздел `Rejected` фиксирует запрещённые варианты и не предоставляет implementer выбор.

## R1. Canonical operation data

**Decision:** использовать только `OperationCase` в `tests/cases/operations.py`; failure variants хранить только в `ERROR_CASES` из `tests/cases/errors.py`.

**Rationale:** unit и component catalogs описывают одни 111 operations. Один typed source удаляет drift.

**Rejected:** `ArgvCase`, `DecodeCase`, `CommandCase`, `OperationDefinition`, `pytest-cases`, string DSL.

## R2. Coverage protection

**Decision:** gate сравнивает checked-in operation dimensions, named invariants, statement/branch/zonal coverage и mutation score. Node count только печатается.

**Rationale:** один сильный round-trip test может заменить несколько дубликатов.

**Rejected:** minimum node count; только LOC; только line coverage.

## R3. Duplicate traceability

**Decision:** каждое удаление записывается в `tests/duplicate-removal-map.json` как removed node, существующий retained node и machine contract: operation records используют `operation:<id>:<dimension>`, invariant records используют `invariant:<id>`.

**Rationale:** review видит, какой observable contract остаётся защищённым.

**Rejected:** комментарии в PR; свободный текст без machine validation.

## R4. Mutation metric

**Decision:** `NO_COLOR=1 uv run mutmut results --all` сохраняется в artifact. Parser принимает только известные statuses. Score равен `killed / (killed + survived + timeout + suspicious + no_tests)`; `skipped` исключается. Unknown status и parse error блокируют gate.

**Rationale:** timeout, suspicious и no-tests не являются успешными mutants.

**Rejected:** ручной score; смена mutation framework; снижение mutate scope.

## R5. Timeout and process state

**Decision:** добавить `pytest-timeout>=2.4,<3`; global per-test timeout `30`, method `signal`; process contracts имеют marker timeout `20`; live commands передают `--timeout=0`. Linux status читается из `/proc/<pid>/stat`, macOS — `ps -o stat= -p <pid>`. Zombie считается stopped; ожидание `absent` длится максимум 2 секунды с interval 0.02.

**Rationale:** `os.kill(pid, 0)` не отличает zombie от running.

**Rejected:** `psutil`, fixed sleeps, собственный watchdog, timeout для live tests.

## R6. Fake CLI protocol

**Decision:** response и record передаются абсолютными JSON paths через `MULTICA_FAKE_RESPONSE` и `MULTICA_FAKE_RECORD`; allowlist env keys передаётся `MULTICA_FAKE_ENV_KEYS`; stdout/stderr кодируются base64.

**Rationale:** response selection не зависит от actual argv; secrets не попадают в record.

**Rejected:** fixture lookup по argv; запись всего environment; один fixture file на command.

## R7. Payload storage

**Decision:** serialized payload `<=4096` bytes хранится в `tests/cases/payloads.py`; payload `>4096` bytes хранится в `tests/fixtures/golden/<case-id>.json` для valid UTF-8 JSON и `.bin` для остальных bytes и загружается через один `load_golden()`.

**Rationale:** threshold исключает субъективное решение о “крупном” fixture.

**Rejected:** `tests/fixtures/json/<resource>/<command>.json`; дубли Python constant + JSON file.

## R8. Upstream contract boundary

**Decision:** contract subprocess layer содержит ровно `test_check_cli.py`, `test_collect_cli.py`, `test_diff_cli.py`, `test_upgrade_cli.py`, `test_promotion_cli.py`, `test_observer_cli.py`. Exhaustive semantics остаются в unit. Quickstart удаляется.

**Rationale:** contract layer проверяет parsing, exit codes, persistence и file boundary, а не повторяет pure logic.

**Rejected:** quickstart smoke; отдельный output-contract module; exhaustive matrices через subprocess.

## R9. Packaging

**Decision:** `package-test.yml` строит wheel и sdist один раз. Wheel устанавливается четырьмя pip matrix cells, одним `uv pip` и одним `uv add`. Wheel исключает tools; sdist включает `tools/live_support/`.

**Rationale:** scripts из sdist должны иметь импортируемую shared dependency, а runtime wheel не должен содержать test tooling.

**Rejected:** `ci.yml::build`; build в compatibility cells; packaging skips; source-tree import smoke.

## R10. Shared tooling boundary

**Decision:** shared target/settings/scanner code находится только в `tools/live_support/`; scripts и live tests импортируют его; `scripts/` и `src/` не импортируют `tests.*`.

**Rejected:** `src/multica_py/_internal/live_support`; duplicate script models; imports из `tests.live`.

## R11. Live core and CRUD

**Decision:** использовать один `LiveApiClient`, четыре fixture contexts, один `ExitStack` и fully declarative `CrudDescriptor`. Oracle является набором typed helper functions поверх `LiveApiClient`, а не вторым client class.

**Rejected:** `DirectApiOracle` class; `ResourceRegistry`; `CleanupRegistry`; `if resource_id`; string fixture selectors.

## R12. Sandbox

**Decision:** sandbox изолирован в `tests/live/sandbox/`; workflow экспортирует ровно `prepare_sandbox`, `run_assignment`, `verify_sandbox` и использует immutable phase records.

**Rejected:** один 200+ line orchestration function; nullable shared state; sandbox logic в generic live resources.

## R13. Dependencies

**Decision:** единственная новая dependency — `pytest-timeout`.

**Rejected:** Hypothesis, `pytest-cases`, snapshots, BDD, `pytest-subprocess`, Docker helpers, HTTP mocking libraries, `psutil`.
