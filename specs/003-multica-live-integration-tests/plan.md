# План реализации: Live-интеграционное тестирование `multica-py`

**Feature ID:** `003-multica-live-integration-tests`  
**Дата:** 2026-07-18  
**Статус:** Ready for implementation  
**Основание:** `spec.md`, `contracts/live-test-interface.md`, `contracts/bootstrap-http.md`, `contracts/presence-and-exceptions.md`

## 1. Краткое техническое решение

В `multica-py` добавляется отдельный набор `tests/live`, запускающий публичный Python SDK против настоящего исполняемого файла Multica CLI и изолированного экземпляра Multica backend с PostgreSQL.

Тестовая сессия управляет окружением через официальный Docker Compose Multica. Frontend и daemon не входят в базовое окружение. Тестовый пользователь, PAT и два workspace создаются неинтерактивно через HTTP API development-инстанса. Для проверяемых действий используется только публичный `MulticaClient`; прямой HTTP-клиент применяется исключительно для подготовки данных, независимой проверки состояния и контролируемой генерации ошибок.

Основные профили запуска:

- `live_smoke` — блокирующий PR-набор;
- `live_extended` — периодический или ручной расширенный набор;
- обычный `pytest` по умолчанию не поднимает Docker-окружение и исключает live-тесты.

## 2. Технический контекст

| Область | Решение |
|---|---|
| Язык | Python 3.12 и 3.13 для SDK; live CI первоначально на Python 3.12 |
| Тестовый раннер | `pytest >= 8` |
| Управление окружением | `docker compose` через небольшой Python lifecycle-адаптер |
| HTTP bootstrap/oracle | `httpx` как test-only dependency |
| Backend | Multica backend целевого release/revision |
| Хранилище | PostgreSQL из официального self-host Compose Multica |
| CLI | реальный Multica CLI, собранный или загруженный из того же compatibility target, что и backend |
| SDK | текущий checkout `multica-py` |
| Формат данных SDK | существующие строгие `msgspec`-модели |
| CI | отдельный Linux job для smoke; отдельный scheduled/manual workflow для extended |
| Диагностика | pytest output + redacted metadata + compose logs + compatibility manifest |
| Изоляция | уникальный Compose project, временный HOME, отдельный CLI profile, уникальные workspace/resource prefixes |

## 3. Архитектурная схема

```text
pytest session
  ├─ CompatibilityTarget
  │    ├─ backend image/ref
  │    └─ real multica executable
  ├─ ComposeLifecycle
  │    ├─ postgres
  │    └─ backend
  ├─ BootstrapApiClient
  │    ├─ test identity
  │    ├─ PAT
  │    └─ workspace A + workspace B
  ├─ isolated HOME/.multica/profiles/<run-id>/config.json
  ├─ MulticaClient(workspace A/B)
  ├─ DirectApiOracle
  └─ DiagnosticCollector
```

Проверяемая цепочка:

```text
public Python resource method
  → SDK command construction
  → real multica subprocess
  → real backend HTTP API
  → PostgreSQL
  → CLI JSON/error output
  → SDK model or public exception
```

## 4. Структура изменений в репозитории

```text
multica-py/
├── pyproject.toml                    # addopts -m "not live"; markers; httpx test-only; mypy tests.live.*
├── tests/
│   ├── integration/                  # existing fake-CLI component tests; no rename in MVP
│   └── live/
│       ├── __init__.py
│       ├── conftest.py
│       ├── bootstrap.py
│       ├── compose.py
│       ├── diagnostics.py
│       ├── oracle.py
│       ├── profile.py
│       ├── settings.py
│       ├── resource_registry.py
│       ├── test_bootstrap.py
│       ├── test_labels.py
│       ├── test_projects.py
│       ├── test_issue_workflow.py
│       ├── test_errors.py
│       ├── test_oracle_consistency.py
│       ├── test_workspace_isolation.py
│       └── extended/
│           ├── test_pagination.py
│           ├── test_optional_fields.py
│           ├── test_timestamps.py
│           ├── test_attachments.py
│           └── test_read_only_resources.py
├── scripts/
│   ├── resolve_multica_target.py
│   └── run_live_tests.py
├── contracts/
│   └── multica-live-target.toml      # pinned v0.3.35 + digest
└── .github/workflows/
    ├── ci.yml                        # live-smoke after US1–US5 exist
    └── live-extended.yml             # schedule + workflow_dispatch
```

`tests/integration` остаётся существующим слоем component/process-интеграции с fake CLI. Переименование этой директории не входит в минимальный релиз, чтобы не смешивать функциональную работу с миграцией тестовой классификации.

## 5. Компоненты плана

### 5.1 `LiveSettings`

Единая типизированная загрузка настроек из переменных окружения и target manifest. Компонент обязан завершать подготовку понятной ошибкой при отсутствии обязательного CLI или некорректном target, а не пропускать тесты незаметно в CI.

Ключевые параметры:

- путь к Multica checkout или Compose-файлу;
- путь к реальному CLI;
- exact backend image tag или source revision;
- режим `smoke` / `extended`;
- таймаут готовности;
- каталог диагностических артефактов;
- опциональный режим использования уже запущенного backend для локальной отладки.

### 5.2 `CompatibilityTarget`

Manifest определяет согласованный набор:

- upstream repository;
- exact git tag/SHA;
- backend image repository и exact tag/digest либо режим source build;
- способ получения CLI из того же tag/SHA;
- ожидаемую строку версии CLI;
- дату последней верификации target.

PR smoke использует закреплённый поддерживаемый target. Extended workflow дополнительно умеет подставлять upstream tag/SHA через `workflow_dispatch` или scheduled resolver.

### 5.3 `ComposeLifecycle`

Session-scoped lifecycle (exact contract: `contracts/bootstrap-http.md`):

1. создаёт уникальный Compose project name;
2. выбирает свободный loopback-порт backend;
3. формирует временный env-файл с allowlisted keys (`APP_ENV=development`, `MULTICA_DEV_VERIFICATION_CODE=888888`, generated `JWT_SECRET`/`POSTGRES_PASSWORD`, image pins);
4. запускает только services `postgres` и `backend` from `docker-compose.selfhost.yml`;
5. polls `GET /readyz` per readiness contract (default 120s, interval 0.5→1→2s, exact JSON success body);
6. при ошибке сохраняет compose status и логи;
7. в `finally` выполняет `down -v --remove-orphans` unless local `MULTICA_LIVE_KEEP_ENV=1`;
8. postcondition audit: containers/volumes проекта отсутствуют.

Запуск через shell не используется: аргументы передаются списком в `subprocess`.

### 5.4 `BootstrapApiClient`

Exact HTTP sequence in `contracts/bootstrap-http.md` §2:

1. `POST /auth/send-code`;
2. `POST /auth/verify-code` with code `888888` → JWT;
3. `POST /api/tokens` with `expires_in_days=1` → PAT;
4. `POST /api/workspaces` twice → workspace A/B;
5. возвращает `TestIdentity` и `WorkspaceContext`.

Клиент применяется только в `tests/live/` и не должен быть импортирован production-кодом SDK. `httpx` — test-only dependency.

### 5.5 Изолированный CLI profile

Для каждой test session создаётся временный `HOME`. В нём формируется профиль:

```text
$HOME/.multica/profiles/live-<run-id>/config.json
```

Profile JSON keys exactly: `server_url`, `app_url`, `workspace_id`, `token` per `contracts/bootstrap-http.md` §5. `ClientConfig.environment` передаёт временный `HOME`; `ClientConfig.executable`, `server_url`, `workspace_id` и `profile` задаются явно.

Тесты не должны полагаться только на default workspace: workspace-scoped сценарии создают производные клиенты через публичный API конфигурации.

### 5.6 `DirectApiOracle`

Независимый HTTP-интерфейс; routes pinned in `contracts/bootstrap-http.md` §4. Used for arrange/assert/cleanup only. Returns raw JSON / minimal test-only DTO. Never calls SDK resource methods for independence asserts.

### 5.7 `ResourceRegistry`

Каждый созданный ресурс регистрируется с типом, workspace и cleanup callback. Cleanup order and hierarchy: `contracts/live-test-interface.md` §9 (registry → compose down -v → audit). Ошибка cleanup не скрывает primary failure.

### 5.8 `DiagnosticCollector`

Canonical filenames only (`contracts/live-test-interface.md` §8): `target.json`, `run.json`, `failure.json`, `cleanup.json`, `compose-ps.txt`, `backend.log`, `postgres.log`, `junit.xml`. Log cap 256 KiB each. Secret scan before CI upload. Leak coverage lives in `tests/live/test_errors.py`.

## 6. Pytest-контракт

SSOT: `contracts/live-test-interface.md` §3.

### Маркеры

- `live` — mandatory parent on every live test; requires real CLI and backend;
- `live_smoke` — blocking compact suite (implies `live`);
- `live_extended` — periodic extended suite (implies `live`);
- `destructive` — stops backend or mutates process state;
- `serial` — cannot run concurrently in one environment.

`pyproject.toml` `addopts` MUST include `-m "not live"`. pytest-xdist unsupported in v1.

### Команды

```bash
# Обычные быстрые тесты
uv run pytest -m "not live"

# Блокирующий live smoke
uv run pytest -m live_smoke tests/live

# Расширенный набор
uv run pytest -m "live_smoke or live_extended" tests/live
```

В первом релизе live-набор выполняется без `pytest-xdist`. Параллельные операции проверяются внутри отдельных тестов, но сами тесты используют один session environment последовательно.

## 7. Набор тестов минимального релиза

### 7.1 Bootstrap smoke

- backend достигает `/readyz`;
- CLI version доступна и записана в target report;
- `workspaces.list()` через SDK декодирует реальный ответ;
- временный профиль не совпадает с пользовательским default profile.

### 7.2 Labels CRUD

- create/get/list/update/delete;
- точный round-trip Unicode, emoji, пробелов и цвета;
- независимый HTTP assert после create/update/delete;
- delete в `finally` плюс registry fallback.

### 7.3 Project partial update

Prerequisite SDK work (before live asserts): wire `Unset` on `ProjectUpdateRequest`, map Python `name`→CLI `--title`, reject `description=None` with `ValidationError`.

Then execute case IDs from `contracts/presence-and-exceptions.md`: `P-OMIT`, `P-EMPTY`, `P-SET`, `C-EMPTY`, plus oracle-only `P-NULL-HTTP`.

### 7.4 Issue workflow

- project + две labels;
- issue с Unicode и многострочным description;
- get/list/filter;
- изменение status/priority/title;
- attach/detach label;
- comment round-trip;
- cleanup в dependency-safe порядке.

### 7.5 Error mapping

Prerequisite: T046a maps CLI exits `2/3/4/5` → `NetworkError` / `AuthenticationError` / `NotFoundError` / `ValidationError`.

Exact class matrix: `contracts/presence-and-exceptions.md` §3 (no OR forks).

Synthetic exits: temp wrapper on `ClientConfig.executable` — exit `2` and exit `99` cases in T051.

### 7.6 Workspace isolation

- два клиента на workspace A/B;
- сущность A отсутствует в list/get B;
- параллельные read-only команды двух клиентов не смешивают context;
- закрытие одного клиента не ломает второй.

## 8. Расширенный набор

Numeric pins: `contracts/live-test-interface.md` §11.

- pagination: 12 issues, `page_size=10`;
- filters: `status` + label id;
- unknown/optional/null/empty JSON cases on pinned target;
- timezone-aware timestamps and `created_at <= updated_at`;
- attachments required (1024-byte + edge filenames); fail if unsupported;
- read-only decode smoke: `agents.list`, `skills.list`, `autopilots.list`;
- controlled concurrency (two clients, no xdist);
- upstream main/SHA as non-blocking compatibility observer.

Daemon, runtime execution, repositories и внешние AI/git интеграции — out of v1.

## 9. CI-план

SSOT: `contracts/live-test-interface.md` §10.

### Blocking PR job `live-smoke`

- add only after US1–US5 resource suites land (bootstrap-only green CI is forbidden as the full smoke gate);
- `ubuntu-latest`, Python 3.12 only (local still supports 3.12+3.13);
- `uv sync --frozen --all-groups`;
- resolver mode → absolute CLI path; pull digest-pinned backend image;
- `pytest -m live_smoke tests/live`;
- artifacts: `if: failure()`, retention 7 days, after secret scan;
- timeout 10 minutes; SC-003 budgets enforced;
- concurrency per PR cancels outdated runs.

Existing default `test` job stays offline via `addopts -m "not live"`.

### Scheduled/manual `live-extended`

- weekly + `workflow_dispatch`;
- selector `-m "live_smoke or live_extended" tests/live`;
- pinned-target failure → job failure;
- upstream-main failure → notice only, workflow success.

## 10. Стратегия версий

1. В репозитории хранится один pinned supported target.
2. CLI и backend одного запуска обязаны происходить из одного release tag или одного source SHA.
3. `latest` запрещён в blocking CI.
4. Image digest предпочтительнее mutable tag, когда digest доступен.
5. Target resolver должен fail closed при несовпадении фактической версии CLI с manifest.
6. Обновление target выполняется отдельным PR вместе с результатом contract check и extended suite.

## 11. Безопасность

- Development verification code включается только для loopback-only test instance.
- Compose ports публикуются только на `127.0.0.1`.
- Токены имеют минимально необходимый срок жизни и уничтожаются вместе с БД.
- Secrets не передаются через pytest parameters, test IDs или report names.
- Команда login с token не используется для bootstrap, чтобы не размещать PAT в argv; профиль создаётся напрямую в временном HOME.
- Diagnostic redactor имеет positive и negative tests.
- Никакие GitHub Actions secrets не требуются для базового smoke при использовании публичных release artifacts/images.

## 12. Проверка конституции

Checked against `.specify/memory/constitution.md` v1.0.0.

| Principle | Verdict | Evidence in this plan |
|---|---|---|
| I. Source-Driven CLI Contract | PASS | Pinned `upstream_ref=v0.3.35` / commit; bootstrap/oracle routes and project CLI flags cited from upstream sources in contracts |
| II. Thin Synchronous Wrapper | PASS | Production SDK stays subprocess-only; HTTP clients exist only under `tests/live/` |
| III. Typed Public Surface | PASS (with prerequisite) | US-003 requires `Unset` wiring on `ProjectUpdateRequest` before live presence asserts |
| IV. Offline Testability and Provenance | PASS | `addopts` includes `-m "not live"`; every live test carries parent marker `live`; default CI job must not start Docker |
| V. Secure Packaging and Release | PASS | Redaction + secret scan before artifact upload; no runtime secret deps |
| SDK Constraints / Quality Gates | PASS | Python 3.12/3.13 SDK; live CI on 3.12; `httpx` test-only; ruff/mypy/uv gates unchanged; live-smoke additive |

**Результат:** PASS with mandatory marker/`Unset` prerequisites recorded in tasks T002 / T041a–T041c.

## 13. Этапы реализации

### Этап A — Harness foundation

- manifest и settings;
- compose lifecycle;
- readiness;
- bootstrap и profile;
- diagnostic collector;
- один workspace smoke.

**Gate:** один локальный запуск поднимает окружение, выполняет SDK read и гарантированно удаляет окружение.

### Этап B — Blocking smoke coverage

- labels CRUD;
- project partial update;
- issue/comment workflow;
- error mapping;
- workspace isolation.

**Gate:** все P1 сценарии спецификации покрыты, intentional mutation SDK/CLI contract ломает соответствующий тест.

### Этап C — CI integration

- отдельный `live-smoke` job after US1–US5 suites exist;
- exact target acquisition;
- JUnit и redacted diagnostics (`if: failure()`, 7-day retention);
- timeout/concurrency settings;
- T071 mutation check + T075 ten-run repeat mode.

**Gate:** десять последовательных запусков pinned target без flaky failure; runtime не превышает SC-003.

### Этап D — Extended compatibility suite

- pagination/filter/optional/timestamp/attachments;
- scheduled/manual workflow;
- pinned-vs-upstream reporting.

**Gate:** weekly workflow формирует однозначный compatibility report и не влияет на blocking status pinned PR target.

## 14. Quality gates

Перед завершением реализации должны пройти:

- `uv run ruff format --check .`;
- `uv run ruff check .`;
- `uv run mypy src tests scripts`;
- `uv run pytest -m "not live"`;
- `uv run pytest -m live_smoke tests/live`;
- `uv build`;
- secret scan diagnostic bundle;
- повторный live smoke после принудительного падения предыдущего запуска;
- проверка отсутствия Compose containers/volumes и временных CLI profiles.

## 15. Основные риски и меры

| Риск | Мера |
|---|---|
| Compose upstream меняет service names или env contract | resolver/validation до запуска; target update PR |
| Development auth меняется | bootstrap adapter отделён от тестов ресурсов; contract test bootstrap endpoint |
| CLI profile schema меняется | profile writer versioned по compatibility target; smoke auth-status/workspace list |
| Backend image и CLI расходятся | one-target rule и version assertion |
| Flaky readiness | dependency-aware `/readyz`, bounded polling, логирование последнего ответа |
| Тесты подтверждают собственную ошибку SDK | direct HTTP oracle для критичных операций |
| Cleanup падает | layered cleanup: resource registry → compose down -v → postcondition check |
| Секрет попадает в artifacts | allowlist metadata + mandatory redaction + leak test |
| PR job становится медленным | один Linux/Python job, session reuse, минимальный stack, no frontend/daemon |
| Upstream main нестабилен | отдельный non-blocking compatibility signal |

## 16. Выходные артефакты реализации

- live test harness;
- pinned compatibility target manifest;
- smoke и extended suites;
- CI workflows;
- diagnostic bundle format;
- документация локального запуска;
- таблица трассировки `FR → tests` only in `tests/live/README.md` (T072).
