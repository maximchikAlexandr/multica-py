# Contract: OperationCase and programmable fake CLI

## Единственный test-data API

`tests/cases/models.py` экспортирует только:

- `BehaviorDimension`
- `ExpectedTransportCall`
- `FakeCliResponse`
- `LivePolicy`
- `OperationCase`
- `ErrorCase`

`tests/cases/execution.py` экспортирует только:

- `invoke_client_operation(client, case)`
- `invoke_resource_operation(transport, config, case)`
- `configure_mock_transport(mock, case)`

`tests/cases/operations.py` экспортирует `OPERATION_CASES`.  
`tests/cases/errors.py` экспортирует `ERROR_CASES`.  
Другой operation registry запрещён.

## Unit executor

Для каждого `OperationCase`:

1. создать mock transport;
2. настроить его только через `configure_mock_transport`;
3. вызвать `invoke_resource_operation`;
4. проверить ровно один exact `ExpectedTransportCall`;
5. выполнить `assert_result`. Для `spawn` `configure_mock_transport` возвращает `MagicMock(spec=ManagedProcess)`, а case assertion проверяет non-null result.

## Component executor

Для каждого non-spawn `OperationCase`:

1. записать response schema 1 в `tmp_path/response.json`;
2. задать absolute `MULTICA_FAKE_RESPONSE` и `MULTICA_FAKE_RECORD`;
3. вызвать public SDK operation через `MulticaClient` ровно один раз;
4. прочитать `record.json` и проверить exact `argv`, `cwd`, allowlisted env;
5. выполнить тот же `assert_result`.

Success executor: `tests/component/test_cli_roundtrip.py::test_cli_round_trip`.  
Error executor: `tests/component/test_cli_errors.py::test_cli_error_round_trip`.

## Fake CLI

Response root содержит ровно `schema`, `stdout_b64`, `stderr_b64`, `exit_code`. Record root содержит ровно `argv`, `cwd`, `env`.

- Paths обязаны быть absolute.
- `argv` равен `sys.argv[1:]`.
- Record пишется до output.
- Unknown schema, invalid base64 или invalid path возвращает exit `64` и prefix `fake-multica:`.
- Fake CLI не импортирует `multica_py`.
- Fake CLI не анализирует argv для выбора response.
- `MULTICA_FAKE_ENV_KEYS` — comma-separated имена переменных без пробелов; record `env` содержит ровно эти ключи в порядке перечисления; отсутствующие переменные опускаются.

## Payload rule

- serialized size `<=4096` bytes: `tests/cases/payloads.py`;
- serialized size `>4096` bytes: `tests/fixtures/golden/<case-id>.json` для valid UTF-8 JSON, иначе `.bin`;
- `tests/fixtures/json/` отсутствует;
- один payload не хранится одновременно в Python и file fixture.
