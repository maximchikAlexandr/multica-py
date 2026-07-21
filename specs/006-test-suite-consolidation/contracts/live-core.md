# Contract: Live Core

## Public fixture surface

`tests/live/conftest.py` публикует ровно:

- `live_environment` — session scope;
- `live_session` — session scope;
- `live_case` — function scope;
- `sandbox_session` — function scope, запрашивается только sandbox tests.

Pytest hooks остаются в `conftest.py`. Однополевые fixtures и `request.getfixturevalue` отсутствуют.

## LiveApiClient

`tests/live/api.py` содержит один HTTP client class `LiveApiClient`:

- `request_json(method, path, body, auth, expected_statuses)`;
- `get_object`;
- `get_list`;
- `delete_if_exists`;
- один redaction/excerpt contract.

Bootstrap и oracle являются functions поверх этого class. `BootstrapApiClient` и `DirectApiOracle` отсутствуют.

## Cleanup

`LiveCase` владеет одним `ExitStack`.

1. Audit callback регистрируется первым.
2. Каждый successful side effect немедленно вызывает `defer_cleanup`.
3. LIFO callbacks выполняются при exit.
4. Cleanup failures собираются все.
5. Audit выполняется последним.
6. Primary failure остаётся primary; cleanup failures записываются в diagnostics.

## CRUD algorithm

`tests/live/test_crud.py` выполняет ровно:

1. `created = descriptor.create(live_session, live_case.unique_name)`
2. `identity = descriptor.identity(created)`
3. `live_case.defer_cleanup(f"{descriptor.id}:{identity}", descriptor.delete, live_session, created)`
4. `descriptor.assert_created(created)`
5. `fetched = descriptor.get(live_session, created)`
6. `descriptor.assert_fetched(created, fetched)`
7. `updated = descriptor.update(live_session, fetched)`
8. `descriptor.assert_updated(fetched, updated)`
9. `descriptor.assert_oracle(live_session.api, updated)`
10. `descriptor.delete(live_session, updated)`
11. `descriptor.assert_deleted(live_session.api, updated)`

`delete` idempotent, поэтому registered cleanup безопасен после explicit delete. Executor не содержит resource-specific code.

## Live ownership

- `direct:<id>` resolves to callable в `tests/live/operations.py`: executor callable имеет тип `Callable[[LiveSession, LiveCase], None]`, `<id>` равен `sdk_method` соответствующей операции (один executor на операцию); `operations.py` экспортирует `DIRECT_EXECUTORS: Mapping[str, Callable[[LiveSession, LiveCase], None]]`.
- `crud:<id>` resolves to descriptor in `tests/live/crud_descriptors.py`.
- `sandbox` resolves to sandbox workflow.
- `none` разрешён только для `unrunnable` с closed reason.

Separate operation-ID sets запрещены.
