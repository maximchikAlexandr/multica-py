# Data Model: Test Suite Consolidation

## 1. BehaviorDimension

Closed string enum:

- `argv`
- `decode`
- `component-roundtrip`
- `error-mapping`
- `secret-redaction`
- `malformed-output`
- `presence-omitted`
- `presence-null`
- `presence-empty`
- `live-smoke`
- `live-extended`
- `live-sandbox`

Новые значения добавляются только через отдельное изменение спецификации.

## 2. ExpectedTransportCall

| Field | Type | Rule |
|---|---|---|
| `method` | `Literal["run_bytes", "run_text", "spawn"]` | Обязателен. |
| `argv` | `tuple[str, ...]` | Не содержит executable. |
| `stdin` | `bytes | None` | Точное ожидаемое значение. |
| `timeout` | `datetime.timedelta | None` | Точное ожидаемое значение, совпадающее со значением, передаваемым в transport. |

## 3. FakeCliResponse

| Field | Type | Rule |
|---|---|---|
| `stdout` | `bytes` | Default `b""`. |
| `stderr` | `bytes` | Default `b""`. |
| `exit_code` | `int` | Default `0`. |

Serialized schema 1:

```json
{
  "schema": 1,
  "stdout_b64": "",
  "stderr_b64": "",
  "exit_code": 0
}
```

## 4. LivePolicy

| Field | Type | Rule |
|---|---|---|
| `mode` | `smoke | extended | sandbox | unrunnable` | Ровно одно значение. |
| `owner` | `str` | Формат определён ниже. |
| `reason` | closed reason code or `null` | Не-null только для `unrunnable`. |

Validation:

- `smoke`/`extended`: owner равен `direct:<executor-id>` или `crud:<descriptor-id>`, reason `null`.
- `sandbox`: owner равен `sandbox`, reason `null`.
- `unrunnable`: owner равен `none`, reason обязателен.

Closed reason codes:

- `destructive-irrecoverable`
- `interactive-or-foreground`
- `process-or-daemon-control`
- `requires-external-infra`

Все variants одного `sdk_method` имеют byte-identical `LivePolicy`.

Источник назначения policy для 111 operation IDs (снимок текущего live-разбиения; `mode=smoke` не присваивается ни одной операции):

| Текущий источник | mode | owner | Количество |
|---|---|---|---|
| `LIVE_OPERATIONS` в `tests/live/resources.py` | `extended` | `direct:<sdk_method>` | 27 |
| `crud_sdk_methods()` (labels/projects × 4 verb) | `extended` | `crud:labels` / `crud:projects` | 8 |
| `AGENT_SANDBOX_LIVE_METHODS` | `sandbox` | `sandbox` | 3 |
| `LIVE_EXEC_EXCEPTIONS` | `unrunnable` | `none`, reason = тот же closed code | 73 |

Разбиение не содержит пересечений и пропусков: 27 + 8 + 3 + 73 = 111.

## 5. OperationCase

| Field | Type | Rule |
|---|---|---|
| `sdk_method` | `str` | Public attribute path и manifest operation ID. |
| `variant_id` | `str` | Regex `[a-z0-9][a-z0-9.-]*`; base variant `default`. |
| `args` | `tuple[object, ...]` | Public method positional args. |
| `kwargs` | `tuple[tuple[str, object], ...]` | Sorted unique keys; executor converts to dict. |
| `expected_call` | `ExpectedTransportCall` | Unit oracle. |
| `response` | `FakeCliResponse | None` | `None` только при `expected_call.method == "spawn"`. |
| `assert_result` | `Callable[[object], None]` | Всегда задан. |
| `dimensions` | `frozenset[BehaviorDimension]` | Всегда содержит `argv`. |
| `live` | `LivePolicy` | Operation-owned live classification. |

Computed ID: `sdk_method` для variant `default`; иначе `<sdk_method>.<variant_id>`.

Registry validation:

1. `(sdk_method, variant_id)` уникален.
2. Ровно 111 unique `sdk_method` и каждый находится в guard-eligible manifest.
3. `spawn` case имеет `response=None`; остальные имеют response.
4. Все non-spawn cases содержат `component-roundtrip`.
5. Variants одного operation ID имеют одну live policy.
6. `invoke_client_operation` проходит attributes `sdk_method.split(".")` от `MulticaClient`.
7. `invoke_resource_operation` создаёт root resource class по первому segment и проходит оставшиеся attributes тем же алгоритмом.

## 6. ErrorCase

| Field | Type | Rule |
|---|---|---|
| `id` | `str` | Уникален. |
| `operation` | `OperationCase` | Ссылка на существующий ordinary case. |
| `response` | `FakeCliResponse` | Nonzero exit или malformed stdout. |
| `exception_type` | `type[BaseException]` | Public SDK exception. |
| `assert_exception` | `Callable[[BaseException], None]` | Проверяет fields, argv и redaction. |
| `dimensions` | `frozenset[BehaviorDimension]` | Содержит `error-mapping` и дополнительные failure dimensions. |

## 7. Behavioral coverage schema 1

Path: `tests/behavioral-coverage.json`.

```json
{
  "schema": 1,
  "source_snapshot": "<40-char-sha>",
  "operations": {
    "agents.create": ["argv", "decode", "component-roundtrip", "live-extended"]
  },
  "invariants": {
    "process.timeout": "tests/component/test_process_contract.py::test_process_contract[timeout]"
  }
}
```

Rules:

1. `operations` содержит ровно 111 guard-eligible keys.
2. Dimension arrays non-empty, sorted, unique и используют closed enum.
3. Actual operation dimensions генерируются из `OPERATION_CASES`, `ERROR_CASES` и `LivePolicy`.
4. Required set MUST быть subset actual set; stale actual operation ID запрещён.
5. `invariants` содержит на stage `pr1` минимум:
   - `network.offline-hard-fail`
   - `process.cancellation`
   - `process.timeout`
   - `process.sigterm-escalation`
   - `process.descendant-cleanup`
   - `live.cleanup-lifo`
   - `live.workspace-isolation`
   - `live.oracle-consistency`
   - `live.secret-scan`
   - `sandbox.deterministic`
   - `sandbox.provider-canary`

   Stage-gated keys `packaging.artifact-required`, `packaging.single-build` и `tooling.no-tests-import` обязательны начиная со stage `pr3` и добавляются в manifest последним коммитом stage `pr3` после готовности guard-тестов (T046, T050, T053): до `pr3` их guard-узлы не существуют (scripts сегодня импортируют `tests.*`, packaging-тесты содержат skips). Отдельные коммиты задач разрешены, при условии что ключи добавляются последним коммитом stage `pr3`, когда T046/T050/T053 guard-узлы уже присутствуют в дереве; промежуточные коммиты stage `pr3`, где manifest уже содержит ключи, но guard-узлы отсутствуют, запрещены.
6. Каждый invariant value является существующим node ID из full collection с `-o addopts=""`.
7. Operation dimension arrays и invariant keys immutable после stage `pr1`; invariant node value меняется только вместе с duplicate-removal record. Единственное исключение — добавление stage-gated keys по правилу 5.

## 8. Duplicate removal map schema 1

Path: `tests/duplicate-removal-map.json`.

```json
{
  "schema": 1,
  "records": [
    {
      "removed_node_id": "tests/...::test_old",
      "retained_node_id": "tests/...::test_new[case]",
      "protected_contract": "operation:agents.create:component-roundtrip"
    }
  ]
}
```

`protected_contract` имеет только два формата:

- `operation:<sdk_method>:<dimension>`
- `invariant:<invariant-id>`

Rules: removed IDs unique; retained ID существует в final collection; protected contract существует в behavioral manifest.

## 9. Quality baseline schema 2

Path: `tests/quality-baseline.json`.

Required shape:

```json
{
  "schema": 2,
  "git_sha": "<green-pr1-sha>",
  "source_snapshot": "b3a299b36d1ad5bc386b5e4517d2a348d53db31c",
  "coverage": {
    "statement_percent": 0.0,
    "branch_percent": 0.0,
    "zones": {},
    "config_sha256": "sha256:..."
  },
  "mutation": {
    "killed": 0,
    "survived": 0,
    "timeout": 0,
    "suspicious": 0,
    "no_tests": 0,
    "skipped": 0,
    "score_percent": 0.0,
    "config_sha256": "sha256:..."
  },
  "behavior": {
    "requirements_sha256": "sha256:...",
    "operation_pairs": 0,
    "invariants": 0
  },
  "loc": {
    "tests_python": 0,
    "live_support_python": 0,
    "scripts_python": 0,
    "max_test_support_file": 0
  },
  "offline": {
    "duration_seconds": 0.0,
    "collected": {}
  },
  "package_install_paths": 6
}
```

Metric definitions:

- Logical line: non-empty line whose first non-space character is not `#`.
- `tests_python`: all `tests/**/*.py`.
- `live_support_python`: all non-`test_*.py` Python files under `tests/live/` plus all `tools/live_support/**/*.py`.
- `max_test_support_file`: maximum over `tests/**/*.py` and `tools/live_support/**/*.py`.
- `requirements_sha256`: canonical hash of operation dimension pairs and invariant keys; invariant node-path values are excluded so a traced test rename does not change required behavior.
- `zones`: per-zone coverage percent, где zone — группа из `[tool.coverage.regexs]`/`[tool.coverage.thresholds]` в `pyproject.toml` (текущие: `transport`, `models`, `resources`, `errors`); compare падает, если zone ниже baseline или configured threshold.
- Coverage fingerprint: canonical JSON of `[tool.coverage.run|report|regexs|thresholds]` after `tomllib` parsing.
- Mutation fingerprint: canonical JSON of `[tool.mutmut]` after `tomllib` parsing.
- Serialization: UTF-8, `indent=2`, `sort_keys=True`, one trailing newline.

State transition: source snapshot → process-fixed green stage `pr1` → immutable schema-2 baseline → stage comparisons.

## 10. CrudDescriptor[T]

| Field | Type | Use |
|---|---|---|
| `id` | `str` | Registry ID and live owner target. |
| `profile` | `Literal["live_smoke", "live_extended"]` | Pytest marker profile for descriptor case. |
| `create` | `Callable[[LiveSession, str], T]` | Create resource. |
| `get` | `Callable[[LiveSession, T], T]` | Fetch using resource-owned identity. |
| `update` | `Callable[[LiveSession, T], T]` | Update resource. |
| `delete` | `Callable[[LiveSession, T], None]` | Idempotent delete; ignores already absent. |
| `identity` | `Callable[[T], str]` | Cleanup label and diagnostics identity. |
| `assert_created` | `Callable[[T], None]` | Create assertions. |
| `assert_fetched` | `Callable[[T, T], None]` | Fetch assertions. |
| `assert_updated` | `Callable[[T, T], None]` | Update assertions. |
| `assert_oracle` | `Callable[[LiveApiClient, T], None]` | Backend oracle. |
| `assert_deleted` | `Callable[[LiveApiClient, T], None]` | Absence oracle. |

Все fields обязательны. `CRUD_CASES` создаёт `pytest.param` с marker, имя которого точно равно `profile`. Соответствие `LivePolicy.mode` и `profile`: `smoke` ↔ `live_smoke`, `extended` ↔ `live_extended`; operations с owner `crud:<id>` обязаны иметь mode, соответствующий descriptor profile. Оба descriptor (`labels`, `projects`) получают `profile="live_extended"` — состав live-сьютов не меняется. Запрещены `resource_id`, optional callables, capabilities flags, string helper names и descriptor-to-descriptor references.

## 11. Live contexts

- `LiveEnvironment`: resolved target/settings, backend lifecycle, diagnostics root.
- `LiveSession`: primary/secondary SDK clients, workspaces, identity, `LiveApiClient`.
- `LiveCase`: unique name, one `ExitStack`, cleanup failures, `defer_cleanup(name, callback, *args)`.
- `SandboxSession`: `LiveCase` plus OpenCode configuration; создаётся только sandbox tests.

`defer_cleanup` регистрирует wrapped callback немедленно. Primary test failure остаётся primary; cleanup failures прикладываются к diagnostics.

## 12. Sandbox phase records

- `PreparedSandbox`: project, project resource, agent, issue, filesystem paths.
- `CompletedAssignment`: `prepared`, run/task identity, captured execution result.
- `SandboxVerification`: `completed`, filesystem manifest, diagnostics and assertion summary.

Все records immutable; nullable partial fields запрещены.
