# Спецификация 005: Надёжная тестовая система и live-сценарий работы агента в песочнице

**Feature ID:** `005-test-suite-agent-sandbox`  
**Статус:** Implementation-locked  
**Дата:** 19 июля 2026 года

## 1. Цель

Доработка обязана одновременно:

1. удалить тесты, не защищающие наблюдаемое поведение `multica-py`;
2. сократить повторяющийся тестовый код без уменьшения числа обязательных поведенческих случаев;
3. сделать offline, compatibility, live-smoke, mutation и real-provider проверки независимыми профилями;
4. добавить merge-blocking live-сценарий, который через реальный Multica backend, CLI и daemon изменяет файл в привязанной `local_directory`;
5. добавить отдельный scheduled/manual canary с настоящим OpenCode, не являющийся required check для merge.

Новый live-сценарий проверяет полный путь:

`daemon start → runtime registration → agent create → workspace/project/issue create → local_directory attach → issue dispatch → OpenCode-compatible execution → exact file mutation → run verification → cleanup`.

## 2. Зафиксированные решения

Следующие решения окончательны и не оставляются на выбор исполнителю:

1. Каталог `tests/integration` переименовывается в `tests/component`.
2. Повторяющиеся command/resource проверки реализуются через `dataclass` descriptors и `pytest.mark.parametrize`; `pytest-subtests` не используется.
3. Hypothesis, Polyfactory, Syrupy, Testcontainers и BDD/Screenplay/Page Object не добавляются.
4. Markdown traceability matrix и `capabilities.toml` не создаются.
5. `pytest-xdist` используется только для parallel-safe offline tests.
6. `mutmut` используется только в отдельном weekly/manual workflow для ограниченного набора чистой логики; он не запускается в каждом PR и не запускает live-тесты.
7. Merge-blocking agent workflow использует реальный Multica backend/CLI/daemon и детерминированный OpenCode-compatible executable.
8. Настоящий OpenCode используется только в отдельном scheduled/manual canary.
9. Runtime не создаётся server-side API-вызовом. Он появляется после запуска изолированного daemon и удаляется после остановки daemon.
10. Workspace создаётся и удаляется существующим live bootstrap API helper. Публичный `workspaces` SDK не расширяется CRUD-операциями в рамках этой спецификации.
11. Multica live target фиксируется на release tag `v0.3.10`; использование `main`, `latest` или другого tag запрещено.
12. Для project resources добавляется typed public SDK surface `client.projects.resources`.
13. Агент не удаляется физически: cleanup выполняет `agents.archive`, после чего агент обязан стать non-routable.
14. Runtime не удаляется SDK-методом: cleanup останавливает daemon и ждёт deregistration runtime.
15. Единственный merge-blocking файловый сценарий изменяет `target.txt`; `control.txt` обязан остаться неизменным.
16. Multica-generated файлы `AGENTS.md`, `.multica/**`, `.opencode/**` и `.agent_context/**` разрешены и не считаются неожиданными пользовательскими изменениями.

## 3. Границы

### 3.1. Входит в объём

- удаление пяти известных low-signal тестов;
- содержательный lifecycle-тест context manager;
- единый детерминированный subprocess harness;
- четыре слоя `unit`, `contract`, `component`, `live`;
- typed table-driven command cases;
- canonical live CRUD descriptors;
- сокращение live support layer до семи модулей;
- statement и branch coverage gate с существующими зональными порогами;
- один полный offline quality job;
- узкая OS/Python compatibility matrix;
- повторное использование одного wheel artifact;
- отдельный weekly/manual targeted mutation workflow;
- typed SDK support project resources;
- поддержка `project_id` при create/update issue;
- детерминированный live agent sandbox workflow;
- отдельный real OpenCode canary;
- независимый от pytest teardown final cleanup в CI.

### 3.2. Не входит в объём

- изменение Multica server или daemon protocol;
- создание нового runtime API;
- добавление workspace create/delete в публичный SDK;
- UI/browser tests;
- параллельный запуск live profile;
- использование реального облачного LLM в required PR checks;
- автоматический выбор provider/model;
- гарантирование бесплатного DeepSeek endpoint;
- Markdown traceability;
- новые общие test frameworks помимо `pytest-xdist` и отдельного `mutmut` tool group.

## 4. Пользовательские сценарии

### US-001 — Достоверный offline signal (P1)

Разработчик запускает обычный тестовый набор и получает только детерминированные unit, contract и component проверки.

**Acceptance:**

1. `uv run pytest` не собирает live tests.
2. Каждый table-driven case отображается отдельным pytest item с ID `<resource>.<operation>.<variant>`.
3. Regression в argv, decoding, error mapping, presence semantics или redaction даёт целевое падение.
4. Process tests не используют длительный `sleep` и доказывают отсутствие orphan process tree.
5. После удаления low-signal тестов число обязательных behavioral cases не меньше baseline.

### US-002 — Детерминированное выполнение issue агентом (P1)

Разработчик запускает `live_agent_sandbox` и получает доказательство, что task прошёл через реальный Multica orchestration и изменил только разрешённый файл.

**Acceptance:**

1. Созданы `target.txt` со строкой `before:<run_id>\n` и `control.txt` со строкой `control:<run_id>\n`.
2. Запущен отдельный daemon profile с `MULTICA_OPENCODE_PATH`, указывающим на test executable.
3. Обнаружен ровно один online OpenCode runtime данного daemon.
4. Через SDK создан OpenCode agent по имени; runtime association обеспечивается daemon registration и issue assignment, без runtime flags в create.
5. Через bootstrap helper создан отдельный workspace; через SDK созданы project и issue.
6. Через `client.projects.resources.add_local_directory()` директория прикреплена к project для daemon данного запуска.
7. Issue description содержит одну machine-readable инструкцию `MULTICA_TEST_ACTION` и назначается созданному agent.
8. Test executable меняет `target.txt` с exact-before на exact-after, пишет валидный OpenCode JSONL stream и завершается с code 0.
9. Latest run достигает `completed` не более чем за 120 секунд.
10. `target.txt` равен `after:<run_id>\n`; `control.txt` не изменён; вне allowlist не создано и не изменено файлов.
11. Cleanup выполняется в зафиксированном порядке и postcondition audit не находит ресурсов данного запуска.

### US-003 — Real OpenCode canary (P2)

Maintainer запускает тот же минимальный workflow с настоящим OpenCode и заранее настроенной моделью.

**Acceptance:**

1. Canary запускается только из отдельного workflow по weekly schedule или `workflow_dispatch`.
2. При отсутствии любого обязательного параметра test item имеет статус `skipped` с перечнем отсутствующих имён переменных.
3. Canary использует путь и model identifier только из environment/secrets.
4. Canary выполняет ровно одну issue execution попытку.
5. Timeout равен 15 минутам, cost ceiling равен `0.10 USD` по `issues.usage()`.
6. Canary failure MUST завершать canary workflow со статусом `failure`; имя canary workflow MUST отсутствовать в branch-protection required checks.
7. Файловые и cleanup assertions совпадают с deterministic workflow.

### US-004 — Измеримая оптимизация тестовой базы (P2)

Maintainer сравнивает baseline и итоговые метрики и видит, что сокращение кода не уменьшило способность находить дефекты.

**Acceptance:**

1. Baseline привязан к `git rev-parse HEAD` до первого изменения.
2. Statement и branch reports созданы в одном canonical quality job.
3. Зональные пороги: transport 80%, models 90%, resources 70%, errors 95%.
4. Compatibility matrix выполняет только marker `compat`.
5. Mutation workflow обрабатывает только утверждённые source paths и unit/component tests.
6. Один wheel устанавливается через pip во всех четырёх compatibility cells; `uv pip install` и `uv add` выполняются только на Ubuntu/Python 3.12.

## 5. Функциональные требования

### 5.1. Test architecture

- **FR-001:** Test suite MUST иметь каталоги `tests/unit`, `tests/contract`, `tests/component`, `tests/live`; каталог `tests/integration` MUST отсутствовать после миграции.
- **FR-002:** Корневой pytest configuration MUST исключать marker `live` по умолчанию.
- **FR-002a:** Каждый модуль под `tests/live/` MUST объявлять marker `live` и ровно один profile marker из `live_smoke`, `live_extended`, `live_opencode_canary`; правила path-based assignment заданы в `contracts/marker-profiles.md`.
- **FR-003:** Файл `tests/integration/test_issue_workflows.py` MUST быть удалён; три tests, проверяющие tuple/Popen вместо SDK в `test_streaming_commands.py`, MUST быть удалены; `test_managed_process_poll` MUST быть сохранён и перенесён в `tests/component/` без изменения поведения; `tests/integration/test_process_lifecycle.py` MUST быть удалён после миграции его coverage в `tests/component/test_process_contract.py`.
- **FR-004:** Context manager MUST иметь два параметризованных cases `normal-exit` и `exception-exit`, каждый проверяющий ровно один canonical close и отсутствие поглощения body exception.
- **FR-005:** Process harness MUST поддерживать stdout, stderr, exit code, ready signal, release signal, pid file и child-process mode.
- **FR-006:** Process lifecycle MUST выполняться одной parameterized test function с IDs `success`, `non-zero-exit`, `stdout`, `stderr`, `timeout`; case `timeout` MUST доказывать parent+child termination без long sleep.
- **FR-007:** Resource command cases MUST храниться как immutable typed descriptors, а tests MUST быть разделены на `commands`, `decoding`, `errors`, `presence_semantics`.
- **FR-008:** Expected argv/output/error MUST быть literal fixture data и MUST NOT вычисляться production builder/decoder.
- **FR-009:** Live CRUD MUST использовать один `CrudDescriptor` registry; отдельные live tests разрешены только для issue workflow, project presence semantics, error mapping, workspace isolation, bootstrap, oracle consistency и agent sandbox.
- **FR-010:** Live support layer MUST состоять ровно из `conftest.py`, `environment.py`, `backend.py`, `resources.py`, `crud_descriptors.py`, `oracle.py`, `diagnostics.py`.

### 5.2. Quality, CI and package validation

- **FR-011:** Canonical `quality` job MUST запускаться на Ubuntu/Python 3.12, собирать statement+branch coverage и применять zonal thresholds 80/90/70/95.
- **FR-012:** Parallel-safe offline tests MUST запускаться через `pytest-xdist --dist loadscope`; marker `serial` MUST запускаться отдельным non-xdist pass с coverage append.
- **FR-013:** Compatibility matrix MUST состоять из Ubuntu/macOS × Python 3.12/3.13 и запускать только marker `compat`.
- **FR-013a:** Минимальный набор compat tests и CI gate MUST соответствовать `contracts/compat-tests.md`; `pytest --collect-only -q -m compat` MUST сообщать не менее четырёх items.
- **FR-014:** Package workflow MUST собирать wheel один раз; pip install MUST выполняться в четырёх cells; `uv pip install` и `uv add` MUST выполняться один раз на Ubuntu/Python 3.12.
- **FR-015:** `mutmut` MUST находиться в отдельной dependency group `mutation` и MUST запускаться weekly во вторник 03:00 UTC и через manual dispatch.
- **FR-016:** Mutation scope MUST соответствовать closed list в `contracts/mutation-scope.md`; live, generated models и test helpers MUST быть исключены.
- **FR-017:** Mutation workflow MUST использовать только unit+component tests, MUST сохранять полный textual `mutmut results` как CI artifact и MUST NOT быть required PR check. Mutation score и survivor count не являются merge gate в этой спецификации.
- **FR-018:** `tests/quality-baseline.json` MUST хранить только pre-change commit SHA, collected counts по слоям, mandatory offline case count, test/support LOC, полный offline duration, coverage metrics и package install path count; mutation data в этот файл не записывается.

### 5.3. Public SDK additions required by sandbox workflow

- **FR-019:** `client.projects.resources` MUST быть public nested resource.
- **FR-020:** Public models MUST включать `ProjectResourceRecord`, `LocalDirectoryResourceRef`, `ProjectResourceAddLocalDirectoryRequest`, `ProjectResourceUpdateLocalDirectoryRequest`.
- **FR-021:** `client.projects.resources.list(project_id)` MUST вернуть typed tuple ресурсов.
- **FR-022:** `add_local_directory(project_id, request)` MUST построить CLI command `project resource add` с `--type local_directory`, `--local-path`, `--daemon-id` и optional `--ref-label`.
- **FR-023:** `update_local_directory(project_id, resource_id, request)` MUST передать новый `--local-path`.
- **FR-024:** `remove(project_id, resource_id)` MUST выполнить `project resource remove`.
- **FR-025:** `IssueCreateRequest` и `IssueUpdateRequest` MUST поддерживать `project_id`; transport MUST передавать `--project <project_id>`.
- **FR-026:** Новые public models/resources MUST быть отражены в public-surface contract, CLI coverage contract, unit/component tests и docs; `IssueUsage` MUST получить optional field `cost_usd: float | None` для canary cost gate.

### 5.4. Deterministic daemon/runtime setup

- **FR-027:** Run ID MUST быть lowercase UUID hex; все имена MUST начинаться с `multica-py-live-<run_id>`.
- **FR-028:** Workspace MUST создаваться существующим `BootstrapApiClient`; public workspaces SDK MUST NOT использоваться для create/delete.
- **FR-029:** Test MUST создать isolated HOME, daemon profile name, daemon ID и workspaces root внутри test temp root.
- **FR-030:** Daemon process MUST запускаться через subprocess `multica daemon start --foreground` с exact environment из `contracts/agent-runtime-live-helpers.md`.
- **FR-031:** Runtime MUST считаться ready только после появления ровно одного online runtime; oracle helper MUST подтвердить `provider == "opencode"` и `daemon_id == <daemon_id>` по backend JSON.
- **FR-032:** Runtime ready timeout MUST быть 60 секунд; poll interval MUST быть 1 секунда.
- **FR-033:** Agent MUST создаваться через `client.agents.create(AgentCreateRequest(name=f"{prefix}-agent"))` без новых public agent fields; routing обеспечивается assignment на созданного agent.

### 5.5. Deterministic file workflow

- **FR-034:** Sandbox directory MUST находиться внутри test temp root и MUST использовать canonical absolute path.
- **FR-035:** Initial files MUST быть `target.txt=before:<run_id>\n` и `control.txt=control:<run_id>\n` encoded UTF-8.
- **FR-036:** Project MUST создаваться в bootstrap workspace; issue MUST создаваться с `project_id` и без assignee, затем project resource MUST быть attached и прочитан через `client.projects.resources.list()` до assignment.
- **FR-037:** Issue description MUST содержать строку `MULTICA_TEST_ACTION=<compact-json>` со schema `1`, path `target.txt`, exact before и exact after.
- **FR-038:** Dispatch MUST выполняться единственным вызовом `issues.assign(IssueAssignmentRequest(issue_id=..., agent_id=...))` после успешной resource verification; argv MUST быть `issue assign <issue_id> --to-id <agent_id>`.
- **FR-039:** Fake OpenCode executable MUST принять canonical OpenCode argv, извлечь `MULTICA_TEST_ACTION`, проверить path containment и exact-before, атомарно заменить файл и вывести валидный JSONL success stream.
- **FR-040:** Fake executable MUST отклонять unknown schema, absolute path, `..`, missing file, before mismatch и malformed instruction с non-zero exit и JSONL error event.
- **FR-041:** Test MUST poll `issues.runs(issue_id)` раз в 1 секунду не более 120 секунд и выбрать post-assignment run с greatest `started_at` по правилам `contracts/agent-runtime-live-helpers.md`.
- **FR-042:** Success MUST требовать terminal task status `completed`; `failed`, `cancelled` и timeout MUST падать.
- **FR-043:** File assertion MUST сравнить exact bytes target/control и filesystem manifest.
- **FR-044:** Filesystem manifest MUST разрешать изменения `target.txt`, `AGENTS.md`, `.multica/**`, `.opencode/**` и `.agent_context/**` (OpenCode provider context written by Multica into the local directory); `control.txt` MUST быть byte-identical; другие created/removed/modified paths MUST падать.
- **FR-045:** Routing assertion MUST подтвердить issue.project_id, issue.assignee_id, run ID, agent runtime ID и daemon runtime ID через SDK плюс existing bootstrap/oracle helper.
- **FR-046:** Failure bundle MUST соответствовать `contracts/live-diagnostics-bundle.md`.

### 5.6. Cleanup

- **FR-047:** Cleanup MUST регистрироваться немедленно после каждого successful side effect.
- **FR-048:** Cleanup MUST всегда выполняться в порядке: cancel nonterminal run; remove project resource; archive agent; delete project; stop daemon; wait runtime deregistration; delete bootstrap workspace; remove isolated HOME/workspaces/sandbox directories.
- **FR-049:** Cleanup action MUST считать already-absent/already-archived состоянием success и MUST продолжать после ошибки следующей action.
- **FR-050:** Original test failure MUST оставаться primary; cleanup failures MUST добавляться в diagnostic bundle и summary.
- **FR-051:** Runtime deregistration timeout MUST быть 30 секунд с poll interval 1 секунда.
- **FR-052:** Postcondition audit MUST подтвердить отсутствие runtime/daemon process, routable agent, project resource, project, workspace и temp paths данного run ID.
- **FR-053:** CI final cleanup MUST выполняться с `if: always()` и удалять только Docker containers/networks/volumes и processes, маркированные exact run prefix.

### 5.7. Real OpenCode canary

- **FR-054:** Canary marker MUST называться `live_opencode_canary` и MUST отсутствовать в live-smoke selection.
- **FR-055:** Canary workflow MUST запускаться weekly в воскресенье 03:00 UTC и через `workflow_dispatch`.
- **FR-056:** Required variables MUST быть `MULTICA_CANARY_OPENCODE_PATH`, `MULTICA_CANARY_MODEL`, `MULTICA_CANARY_SECRET_NAMES`; последняя содержит comma-separated environment variable names, каждое из которых MUST иметь непустое значение.
- **FR-057:** Отсутствие path/model/secret-name list или любого перечисленного secret value MUST давать `pytest.skip` до запуска backend/daemon.
- **FR-058:** Canary MUST использовать тот же workflow helper и file assertions, заменяя только executable path и отсутствие `MULTICA_TEST_ACTION` parser dependency.
- **FR-059:** Canary issue instruction MUST соответствовать exact template в `contracts/opencode-canary-workflow.md`.
- **FR-060:** Canary MUST выполнять одну попытку, иметь 15-minute job timeout и падать при `issues.usage().cost_usd > 0.10`.
- **FR-061:** Canary workflow MUST публиковать provider/model/OpenCode version, duration, usage and sanitized failure bundle; secrets MUST быть redacted.
- **FR-062:** Canary workflow MUST NOT быть required branch check.
- **FR-063:** `contracts/multica-live-target.toml` MUST pin `upstream_ref = "v0.3.10"`; existing resolver MUST record full upstream commit and immutable image digests for this tag before live implementation begins.

## 6. Edge cases и обязательная реакция

1. Runtime не появился за 60 секунд → setup failure, daemon diagnostics, cleanup.
2. Появилось 0 или более 1 matching runtime → setup failure, список runtimes, cleanup.
3. Project resource response path не равен canonical path → failure до dispatch.
4. Fake executable получил malformed instruction → run `failed`, test failure, diagnostics.
5. Exact-before не совпал → fake executable не пишет файл и возвращает failure.
6. Run не появился за 120 секунд → timeout, active task cancellation, cleanup.
7. Run стал `failed` или `cancelled` → immediate failure, diagnostics, cleanup.
8. Target изменён неверно → file assertion failure, cleanup.
9. Control изменён → file assertion failure, cleanup.
10. Создан неожиданный user path → manifest failure, cleanup.
11. Project-resource removal failed → cleanup continues; workspace deletion remains final server-side containment.
12. Daemon killed before fixture teardown → CI final cleanup and postcondition audit identify leftovers.
13. Canary provider rejects credentials/quota/model → canary fails, but merge remains unaffected.
14. Canary environment incomplete → test is skipped before infrastructure startup.
15. `issues.usage()` unavailable or без `cost_usd` после terminal run → canary fails with diagnostic, not skip.

## 7. Ключевые сущности

- **CommandCase:** immutable descriptor with ID, invocation, expected argv/result/error and markers.
- **CrudDescriptor:** immutable live CRUD descriptor with create/update payload builders, oracle and cleanup.
- **LiveRunContext:** run ID, prefix, target, workspace, isolated paths, diagnostics and cleanup registry.
- **DaemonRuntimeContext:** daemon process/profile/ID, registered runtime and lifecycle state.
- **AgentSandboxInstruction:** schema, relative path, exact before and exact after.
- **ProjectResourceRecord:** typed project resource returned by public SDK.
- **FileManifest:** relative paths, kinds, sizes and SHA-256 hashes before/after run.
- **CleanupRegistry:** ordered idempotent compensating actions.
- **DiagnosticBundle:** sanitized machine-readable evidence for one failed run.

## 8. Измеримые критерии успеха

- **SC-001:** Пять известных low-signal tests отсутствуют; context-manager replacement имеет два behavioral cases.
- **SC-002:** Resource command test/support LOC уменьшен минимум на 25%, collected mandatory cases не уменьшены.
- **SC-003:** Process lifecycle представлен пятью IDs одной parameterized function (`success`, `non-zero-exit`, `stdout`, `stderr`, `timeout`); case `timeout` доказывает process-tree cleanup.
- **SC-004:** `uv run pytest --collect-only` не собирает ни одного live item.
- **SC-005:** Quality job создаёт coverage JSON/XML и применяет transport 80%, models 90%, resources 70%, errors 95%.
- **SC-006:** Полный offline suite выполняется один раз; compatibility subset — четыре cells.
- **SC-007:** Package paths сокращены до 6: 4 pip + 1 uv-pip + 1 uv-add.
- **SC-008:** Deterministic agent sandbox проходит 20 последовательных запусков без failure.
- **SC-009:** Каждый deterministic workflow завершается ≤120 секунд; blocking live-smoke suite ≤300 секунд wall; CI asserts env startup ≤180s and test phase ≤240s as suite sub-budgets under that ceiling.
- **SC-010:** После каждого из 20 запусков postcondition audit не находит управляемых leftovers.
- **SC-011:** Negative cases `agent-error`, `agent-timeout`, `wrong-edit`, `cleanup-failure` создают diagnostic bundle и не оставляют управляемых ресурсов.
- **SC-012:** Real canary завершается passed/failed ≤15 минут или skipped до infrastructure startup.
- **SC-013:** Secret scan diagnostic artifacts возвращает 0 matches.
- **SC-014:** Public contract содержит typed project-resource methods и issue project assignment; command coverage содержит все новые argv paths.

## 9. Предпосылки

1. Реализация начинается с сохранения baseline на фактическом `git rev-parse HEAD`.
2. Multica compatibility target равен release tag `v0.3.10`; manifest хранит resolved full commit and image digests.
3. Target Multica поддерживает daemon registration, OpenCode provider, `local_directory` project resources и issue assignment.
4. Existing `BootstrapApiClient` является единственным механизмом create/delete test workspace в этой спецификации.
5. Existing agents SDK create/archive methods остаются без новых public fields; runtime matching и daemon start выполняются live helpers по `contracts/agent-runtime-live-helpers.md`; agent delete method не создаётся.
6. Multica пишет `AGENTS.md`, `.multica/project/resources.json`, `.opencode/**` и `.agent_context/**` в local directory; эти paths входят в allowlist.
7. GitHub branch protection configuration находится вне репозитория; условие non-required canary проверяется организационной настройкой после merge workflow file.

## 10. Готовность

Спецификация implementation-locked; все choices зафиксированы в `plan.md` и `contracts/`. Checklist re-validation обязателен после каждого spec revision cycle. Следующая фаза — implementation (`PR-01`…`PR-08` по `tasks.md`).
