# Модель данных тестового harness

**Feature:** `003-multica-live-integration-tests`

Модель ниже описывает test-only сущности. Она не изменяет доменную модель `multica-py` или Multica backend.

## 1. `CompatibilityTarget`

Однозначно определяет проверяемую комбинацию компонентов.

| Поле | Тип | Обязательное | Валидация |
|---|---|---:|---|
| `name` | string | да | стабильный slug |
| `upstream_ref` | string | да | exact tag или full commit SHA |
| `backend_image` | string | да для image mode | без `latest` |
| `backend_digest` | string | да when `cli_source=release` (blocking) | concrete `sha256:<64 hex>`; placeholders forbidden |
| `backend_digest_linux_amd64` | string/null | да for CI linux/amd64 release pulls | concrete digest or null for local-only |
| `cli_source` | enum | да | `release`, `source-build`, `local` |
| `cli_version_expected` | string | да | сравнивается с фактической версией |
| `compose_file` | path | да | существующий файл |
| `verified_at` | date | да | ISO date |
| `notes` | string/null | нет | без секретов |

### Состояния

`declared → resolved → verified → active`

Переход в `active` запрещён, если фактическая CLI version не соответствует target или backend source невозможно определить.

## 2. `LiveTestRun`

Идентифицирует один запуск.

| Поле | Тип | Обязательное | Валидация |
|---|---|---:|---|
| `run_id` | string | да | URL/filesystem-safe, уникален |
| `suite_profile` | enum | да | `smoke`, `extended` |
| `started_at` | datetime | да | timezone-aware |
| `target` | CompatibilityTarget | да | verified |
| `compose_project` | string | да | начинается с `multica-py-live-` |
| `artifact_dir` | path | да | внутри временного/CI каталога |
| `status` | enum | да | см. state transitions |

### Состояния

```text
created
  → environment_starting
  → environment_ready
  → bootstrapped
  → tests_running
  → cleaning
  → passed | failed | cleanup_failed
```

Любая ошибка до `tests_running` классифицируется как setup failure. Ошибка cleanup не перезаписывает исходный test failure, но повышает итоговый status до `cleanup_failed` с preserved primary cause.

## 3. `LiveTestEnvironment`

| Поле | Тип | Обязательное |
|---|---|---:|
| `server_url` | URL | да |
| `backend_port` | int | да |
| `compose_project` | string | да |
| `compose_files` | list[path] | да |
| `env_file` | path | да |
| `home_dir` | path | да |
| `profile_name` | string | да |
| `cli_executable` | path | да |
| `readiness_endpoint` | URL | да |
| `readiness_timeout_seconds` | float | да |

### Инварианты

- server URL использует loopback HTTP;
- опубликованный backend port уникален для run;
- home dir не равен реальному HOME;
- profile path находится внутри home dir;
- environment не считается ready до успешного `/readyz`.

## 4. `TestIdentity`

| Поле | Тип | Обязательное | Хранение в diagnostics |
|---|---|---:|---|
| `email` | string | да | допустимо |
| `user_id` | string | да | допустимо |
| `jwt` | secret string | временно | запрещено |
| `pat` | secret string | да | запрещено |
| `pat_id` | string/null | нет | допустимо |

JWT удаляется из объекта после создания PAT, если больше не нужен. Secret values должны быть зарегистрированы в redactor до первого диагностического вызова.

## 5. `WorkspaceContext`

| Поле | Тип | Обязательное |
|---|---|---:|
| `id` | string | да |
| `name` | string | да |
| `slug` | string | да |
| `role` | string/null | нет |
| `profile_name` | string | да |

Run содержит минимум два context: `primary` и `secondary`.

## 6. `CliProfileConfig`

Pinned to Multica `CLIConfig` @ `v0.3.35` (`server/internal/cli/config.go`). Exact JSON keys:

| Поле | Тип | Обязательное |
|---|---|---:|
| `server_url` | URL | да |
| `app_url` | URL | да |
| `token` | secret string | да |
| `workspace_id` | string | да |

Do not write `backends`, `profile_command_overrides`, or invented `watched_workspaces` in MVP.

### Валидация

- file mode `0600` when OS supports it;
- path only under temporary HOME: `.multica/profiles/live-<run-id>/config.json`;
- contents never attached to CI artifacts.

## 7. `RegisteredResource`

| Поле | Тип | Обязательное |
|---|---|---:|
| `resource_type` | string | да |
| `resource_id` | string | да |
| `workspace_id` | string | да |
| `display_name` | string/null | нет |
| `created_by` | enum | да (`sdk`, `oracle`) |
| `cleanup_strategy` | string | да |
| `depends_on` | list[resource key] | нет |
| `cleanup_status` | enum | да |

### Cleanup states

`registered → deleting → deleted | already_absent | delete_failed`

Cleanup order — reverse topological order по `depends_on`.

## 8. `DiagnosticBundle`

| Поле/файл | Содержание | Secret policy |
|---|---|---|
| `target.json` | SDK/CLI/backend target | allowlist only |
| `run.json` | run id, profile, timestamps, stage | allowlist only |
| `failure.json` | exception class, operation, exit code | redacted strings |
| `compose-ps.txt` | status containers | redacted |
| `backend.log` | bounded relevant logs | redacted |
| `postgres.log` | bounded relevant logs | redacted |
| `cleanup.json` | registered resources и cleanup outcomes | no token |
| `junit.xml` | pytest report | test names без secrets |

### Инварианты

- bundle не содержит точное значение PAT/JWT/JWT secret/database password;
- each log file capped at 262144 bytes (256 KiB) with start/end truncation markers;
- canonical files: `target.json`, `run.json`, `failure.json`, `cleanup.json`, `compose-ps.txt`, `backend.log`, `postgres.log`, `junit.xml` (no `environment.json`);
- primary failure и cleanup failure хранятся раздельно.

## 9. `OracleResponse`

Минимальное test-only представление HTTP результата.

| Поле | Тип |
|---|---|
| `status_code` | int |
| `headers` | allowlisted mapping |
| `json_body` | JSON value/null |
| `text_excerpt` | string/null |

Authorization headers никогда не сохраняются. DTO не преобразует доменные значения SDK и не нормализует отсутствующие/null/empty fields.

## 10. Связи

```text
CompatibilityTarget 1 ── 1 LiveTestRun
LiveTestRun         1 ── 1 LiveTestEnvironment
LiveTestRun         1 ── 1 TestIdentity
LiveTestRun         1 ── 2+ WorkspaceContext
WorkspaceContext    1 ── * RegisteredResource
LiveTestRun         1 ── 0..1 DiagnosticBundle
```
