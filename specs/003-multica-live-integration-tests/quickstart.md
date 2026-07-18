# Quickstart: live-интеграционные тесты

Документ описывает ожидаемый пользовательский workflow после реализации feature.

## 1. Предварительные требования

- Linux или macOS для локального запуска;
- Docker Engine/Desktop с рабочим `docker compose`;
- Python 3.12+;
- `uv`;
- checkout `multica-py`;
- checkout Multica либо заранее полученные exact release artifacts согласно target manifest;
- реальный executable `multica`, совпадающий с target.

## 2. Установка зависимостей

```bash
uv sync --frozen --all-groups
```

Проверка обязательных инструментов:

```bash
docker version
docker compose version
/path/to/multica --version
```

## 3. Обычные тесты без Docker

```bash
uv run pytest
# equivalent: uv run pytest -m "not live"  (addopts already excludes live)
```

Ожидаемый результат: live environment не запускается, существующие unit/component/contract tests работают как раньше.

## 4. Локальный smoke-запуск

```bash
export MULTICA_LIVE_UPSTREAM_DIR=/absolute/path/to/multica
export MULTICA_LIVE_CLI=/absolute/path/to/multica/server/bin/multica
export MULTICA_LIVE_TARGET_FILE=$PWD/contracts/multica-live-target.toml

uv run pytest -m live_smoke tests/live -v
```

Ожидаемый lifecycle:

1. валидируется target и CLI version;
2. создаётся уникальный Compose project;
3. запускаются PostgreSQL и backend;
4. harness ждёт `/readyz`;
5. создаются test identity, PAT и два workspace;
6. записывается профиль во временный HOME;
7. выполняются SDK smoke tests;
8. удаляются ресурсы, контейнеры и volumes.

## 5. Расширенный запуск

```bash
MULTICA_LIVE_MODE=extended \
uv run pytest -m "live_smoke or live_extended" tests/live -v
```

Ожидаемый результат: дополнительно выполняются pagination, filters, optional fields, timestamps и attachments.

## 6. Запуск одного сценария

```bash
uv run pytest tests/live/test_projects.py::test_project_partial_update_preserves_omitted_fields -v
```

Environment всё равно создаётся на session scope и удаляется после завершения процесса pytest.

## 7. Диагностика падения

По умолчанию bundle создаётся во временном каталоге. Для стабильного пути:

```bash
export MULTICA_LIVE_ARTIFACT_DIR=$PWD/.artifacts/live
uv run pytest -m live_smoke tests/live -v
```

Проверить:

```text
.artifacts/live/<run-id>/failure.json
.artifacts/live/<run-id>/compose-ps.txt
.artifacts/live/<run-id>/backend.log
.artifacts/live/<run-id>/cleanup.json
```

Токены и secrets не должны присутствовать в этих файлах.

## 8. Локальная отладка с сохранением environment

Только на private workstation:

```bash
MULTICA_LIVE_KEEP_ENV=1 \
uv run pytest tests/live/test_issue_workflow.py -v -x
```

Harness печатает безопасные команды просмотра status/logs. После отладки environment удаляется вручную через сгенерированный Compose project name. В CI этот режим запрещён.

## 9. Проверка cleanup

После обычного запуска:

```bash
docker ps -a --filter name=multica-py-live-
docker volume ls --filter name=multica-py-live-
```

Ожидаемый результат: ресурсов завершившегося run нет.

## 10. Ожидаемые smoke-сценарии

- workspace list через SDK;
- labels CRUD;
- project partial update с oracle assertion;
- issue + labels + comment workflow;
- auth/not-found/validation/transport errors;
- isolation двух workspace;
- diagnostic redaction.

## 11. Типовые причины setup failure

| Симптом | Проверка |
|---|---|
| CLI version mismatch | target manifest и `/path/to/multica --version` |
| backend не ready | backend/postgres logs в bundle |
| auth bootstrap rejected | development env и фиксированный verification code |
| port collision | убедиться, что используется dynamic loopback port |
| profile schema rejected | target CLI и profile writer version |
| Docker permission denied | доступ пользователя к Docker daemon |
