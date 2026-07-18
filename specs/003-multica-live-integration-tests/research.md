# Исследование технических решений

**Feature:** `003-multica-live-integration-tests`  
**Дата:** 2026-07-18

## R-001 — Orchestration framework

**Decision:** использовать официальный Docker Compose Multica через собственный небольшой lifecycle-адаптер, вызывающий `docker compose` посредством `subprocess`.

**Rationale:** upstream уже поставляет self-host Compose с backend, PostgreSQL, health/readiness behavior и version pinning. Дополнительный orchestration framework не устранит необходимость bootstrap пользователя, создания workspace, профиля CLI, независимого oracle и redaction. Прямая интеграция уменьшает число зависимостей и оставляет lifecycle прозрачным.

**Alternatives considered:**

- Testcontainers Python — удобно для программного управления отдельными контейнерами, но дублирует существующий Compose и добавляет abstraction/version surface.
- `pytest-docker` — rejected for MVP; custom lifecycle adapter is mandatory.
- Testcontainers — rejected for MVP; duplicates official Compose.
- Docker services in GitHub Actions only — rejected; must work locally with the same Compose file.

## R-002 — Минимальный запущенный stack

**Decision:** PR smoke поднимает только PostgreSQL и backend.

**Rationale:** проверяемые SDK-команды обращаются через CLI к backend; frontend и daemon не участвуют в CRUD, workspace, error mapping и большинстве schema compatibility scenarios. Исключение этих компонентов сокращает startup time и число причин flaky failure.

**Alternatives considered:**

- Полный self-host stack — полезен для browser/daemon E2E, но повторяет upstream E2E и не нужен основной цепочке SDK.
- Backend как локальный Go process — быстрее при тёплой сборке, но требует Go toolchain и усложняет matching release images в PR CI.

## R-003 — Readiness

**Decision:** ждать dependency-aware `/readyz` с ограниченным polling и общим timeout.

**Rationale:** состояние container `running` не подтверждает завершение migrations и готовность БД. Фиксированный sleep создаёт либо задержку, либо flaky failures.

**Alternatives considered:**

- Compose health status — можно использовать как дополнительный сигнал, но test harness всё равно должен подтвердить HTTP readiness фактического endpoint.
- `/health` — годится для liveness, но `/readyz` лучше отражает зависимости.

## R-004 — Automated authentication

**Decision:** запускать backend в private development mode с фиксированным verification code, затем получить JWT, создать PAT и workspace через HTTP API.

**Rationale:** этот flow документирован самим Multica для изолированной автоматизации и не требует браузера, email provider или frontend. PAT подходит CLI и direct API oracle.

**Alternatives considered:**

- `multica login` — открывает браузер или передаёт token через argv; хуже для CI и security.
- Seed БД напрямую — слишком тесно связывает SDK tests со схемой backend и обходит публичные auth/workspace contracts.
- Извлечение случайного кода из logs — менее детерминированно и усложняет redaction.

## R-005 — CLI profile isolation

**Decision:** временный HOME и отдельный profile config на test session; executable/server/workspace также задаются явно в `ClientConfig`.

**Rationale:** Multica profiles изолируют token, workspace и daemon state. Временный HOME гарантирует отсутствие чтения или записи пользовательского `~/.multica`. `ClientConfig.environment` уже поддерживает передачу окружения subprocess.

**Alternatives considered:**

- Только `--workspace-id`/environment — не решает хранение PAT/profile и риск доступа к default config.
- Изменение реального profile с teardown — недопустимый риск для локального разработчика.

## R-006 — HTTP client для bootstrap и oracle

**Decision:** добавить `httpx` только в test dependency group.

**Rationale:** нужен небольшой надёжный клиент с timeouts, JSON, headers и понятными ошибками. Stdlib `urllib` не добавляет dependency, но делает test harness существенно более многословным. Production package dependency не меняется.

**Alternatives considered:**

- `urllib.request` — rejected for this feature; harness standardizes on `httpx`.
- `requests` — rejected for this feature.
- Использовать SDK как oracle — rejected; violates independence.

## R-007 — Независимый oracle

**Decision:** критичные partial-update и round-trip сценарии проверять прямым HTTP чтением backend.

**Rationale:** если SDK одинаково ошибается при записи и чтении, SDK-only round-trip может пройти. Oracle должен наблюдать серверное состояние через другой путь и минимальные raw JSON assertions.

**Alternatives considered:**

- SQL queries — слишком тесно связывают тесты с внутренней схемой и обходят API representation.
- CLI subprocess напрямую — использует тот же CLI serializer/decoder и недостаточно независим.

## R-008 — Version strategy

**Decision:** blocking tests pin Multica `v0.3.35` (`4416313f8f7f801df8b7f5072087da8a6502a89c`); CLI и backend берутся из этого release tag/SHA + resolved image digest. `latest` запрещён.

**Rationale:** иначе падение невозможно отнести к SDK, CLI или backend version drift. Репозиторий уже имеет offline contract check и weekly upstream observer; live suite дополняет их behavioral signal.

**Alternatives considered:**

- Всегда upstream main — ранний сигнал, но неподходящий blocking gate.
- Только latest stable tag resolver — mutable во времени и ухудшает reproducibility.
- Раздельное pinning CLI/backend — допускает неподдерживаемую комбинацию.

## R-009 — Pytest classification

**Decision:** markers `live`, `live_smoke`, `live_extended`, `destructive`, `serial`; live tests расположены отдельно в `tests/live`.

**Rationale:** текущий репозиторий использует strict markers, а `tests/integration` уже означает component/process tests с fake CLI. Отдельная директория предотвращает скрытое поднятие Docker при обычном `pytest`.

**Alternatives considered (rejected for MVP):**

- Rename `tests/integration` — out of scope.
- Directory selection without markers — rejected; markers + `addopts -m "not live"` are mandatory for Constitution IV.

## R-010 — Session reuse и parallelism

**Decision:** один environment на pytest session; тесты выполняются последовательно, ресурсы получают unique run/test prefixes.

**Rationale:** startup backend и migrations — самая дорогая часть. Параллельные pytest workers потребуют отдельных Compose projects или сложной синхронизации и не нужны для целевого runtime менее 5 минут.

**Alternatives considered (rejected for MVP):**

- Environment per test — too slow.
- `pytest-xdist` shared or per-worker environments — unsupported in v1; serial session only.

## R-011 — Cleanup strategy

**Decision:** layered cleanup: resource registry, session fixture `finally`, `docker compose down -v --remove-orphans`, postcondition audit.

**Rationale:** cleanup отдельных сущностей нужен для семантических assertions и reuse environment; удаление всего project/volume гарантирует отсутствие влияния на следующий запуск даже после частичного failure.

**Alternatives considered:**

- Только resource delete — не покрывает setup failures и orphaned data.
- Только volume removal — скрывает defects delete operations и усложняет локальный existing-backend mode.

## R-012 — CI placement

**Decision:** отдельный `live-smoke` job в CI только на Ubuntu/Python 3.12 и отдельный extended workflow.

**Rationale:** существующая test matrix уже покрывает Python 3.12/3.13 и Ubuntu/macOS на fake/component tests. Docker live stack во всей matrix увеличит стоимость без пропорциональной пользы.

**Alternatives considered:**

- Добавить live в существующий matrix test job — четыре startup и более сложная диагностика.
- Только scheduled live — не блокирует SDK regressions в PR.

## R-013 — Diagnostic artifact security

**Decision:** diagnostic bundle строится из allowlisted metadata и redacted logs; отдельный test сканирует bundle на точный token/JWT/secret.

**Rationale:** SDK уже обращает внимание на redaction subprocess errors, а live harness добавляет backend logs и profile material. Нужна проверяемая, а не декларативная гарантия.

**Alternatives considered:**

- Не сохранять logs — безопаснее, но резко ухудшает диагностику CI.
- Полагаться только на GitHub secret masking — test PAT динамический и не обязательно зарегистрирован как Actions secret.

## Источники исследования

- `multica-py`: README, `pyproject.toml`, `tests/conftest.py`, `.github/workflows/ci.yml`, upstream observer workflows, `ClientConfig`.
- Multica: `CONTRIBUTING.md`, `SELF_HOSTING.md`, `SELF_HOSTING_AI.md`, `CLI_AND_DAEMON.md`.
- Официальная документация pytest о fixture scopes/yield teardown.
- Официальная документация Docker Compose о startup order и health/readiness.
