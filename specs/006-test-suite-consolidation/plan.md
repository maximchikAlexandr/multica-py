# План реализации: Test Suite Consolidation

**Feature:** `006-test-suite-consolidation`  
**Дата:** 2026-07-21  
**Spec:** `spec.md`

## Summary

Рефакторинг выполняется пятью последовательными PR. PR 1 восстанавливает process signal и quality baseline. PR 2 создаёт единственный `OperationCase` catalog. PR 3 удаляет fixture/contract/packaging/tooling duplication. PR 4 упрощает live core и делает CRUD полностью декларативным. PR 5 изолирует agent sandbox и включает финальные budgets. PR нельзя объединять или менять местами.

## Technical Context

- **Python:** 3.12 и 3.13.
- **Platforms:** Linux и macOS.
- **Existing test stack:** pytest, pytest-cov, pytest-xdist, httpx, mutmut.
- **New dependency:** только `pytest-timeout>=2.4,<3` в test group.
- **Storage:** checked-in JSON manifests; temporary response/record JSON; golden payloads только при размере `>4096` bytes.
- **Unchanged:** `src/multica_py`, public API, runtime dependencies, supported operation manifest.
- **Final budgets:** tests logical LOC `<=10500`; live support LOC `<=2500`; каждый Python file under `tests/` и `tools/live_support/` `<=800` logical lines.

## Constitution Check

| Principle | Result | Enforcement |
|---|---|---|
| Source-driven CLI contract | PASS | 111 operation IDs сверяются с pinned manifest. |
| Thin synchronous wrapper | PASS | Production transport не меняется; component boundary остаётся executable. |
| Typed public surface | PASS | Test data использует typed immutable models; string check DSL удаляется. |
| Offline testability/provenance | PASS | Default execution исключает live и packaging; fake CLI deterministic. |
| Secure packaging/release | PASS | Redaction, artifact content и single-build checks сохраняются. |
| Runtime dependency limit | PASS | Runtime dependencies не меняются. |

Post-design check: **PASS**, unresolved violations: **0**.

## Fixed Architecture

### 1. Canonical cases

```text
tests/cases/
├── __init__.py
├── models.py
├── execution.py
├── assertions.py
├── payloads.py
├── operations.py
└── errors.py
```

- `models.py` определяет только `BehaviorDimension`, `ExpectedTransportCall`, `FakeCliResponse`, `LivePolicy`, `OperationCase`, `ErrorCase`.
- `execution.py` содержит `invoke_client_operation`, `invoke_resource_operation`, `configure_mock_transport`.
- `operations.py` содержит единственный `OPERATION_CASES`.
- `errors.py` содержит единственный `ERROR_CASES`.
- `assertions.py` содержит typed result/exception assertions.
- `payloads.py` содержит payloads `<=4096` bytes и `load_golden()`.
- `ArgvCase`, `DecodeCase`, `CommandCase`, `OperationDefinition`, `COMMAND_CHECKS` отсутствуют.

`OperationCase.sdk_method` является public attribute path. Unit executor создаёт root resource class по первому path segment и проходит оставшиеся attributes. Component executor проходит тот же path от `MulticaClient`.

### 2. Behavioral and quality artifacts

- `tests/behavioral-coverage.json`: immutable required operation dimensions и named invariants после PR 1.
- `tests/duplicate-removal-map.json`: machine-validated migration каждой удалённой проверки.
- `tests/quality-baseline.json`: immutable schema 2 baseline после PR 1.
- `scripts/check_test_architecture.py`: structural/behavior checks.
- `scripts/check_test_baseline.py`: coverage, mutation, duration, LOC и package-path comparisons.

Raw collected counts остаются informational.

### 3. Process boundary

- `tests/fixtures/process_state.py`: `ProcessState`, Linux/macOS adapters, bounded wait.
- `tests/fixtures/child_process.py`: ready/release files, ignore-SIGTERM, descendant and PID modes.
- `tests/component/test_process_contract.py`: ровно четыре IDs: `cancellation`, `timeout`, `sigterm-escalation`, `descendant-cleanup`.
- `tests/component/test_cancellation.py` удаляется.
- Global per-test timeout: 30 seconds, method `signal`.
- Default pytest marker selection: `not live and not packaging`.
- Process contract timeout marker: 20 seconds.
- Live invocation: `--timeout=0`.

### 4. Programmable fake CLI

`tests/fixtures/fake_multica.py`:

1. требует absolute `MULTICA_FAKE_RESPONSE` и `MULTICA_FAKE_RECORD`;
2. читает response schema 1 (`stdout_b64`, `stderr_b64`, `exit_code`);
3. записывает `sys.argv[1:]`, cwd и только env keys из `MULTICA_FAKE_ENV_KEYS` (comma-separated, без пробелов);
4. пишет record до stdout/stderr;
5. на invalid schema/base64/path возвращает exit 64 и stderr prefix `fake-multica:`;
6. не импортирует SDK и не выбирает response по argv.

### 5. Upstream contract boundary

Final directory:

```text
tests/contract/upstream/
├── test_check_cli.py
├── test_collect_cli.py
├── test_diff_cli.py
├── test_upgrade_cli.py
├── test_promotion_cli.py
└── test_observer_cli.py
```

`test_upgrade_cli.py` покрывает `prepare-upgrade`, `apply-manifest-suggestions`, `upgrade`. `test_promotion_cli.py` покрывает `promote`, `reject`, `compat`. Exhaustive schema/severity/diff/output logic остаётся в unit. `test_upstream_contract_quickstart.py` удаляется.

### 6. Packaging

`tests/packaging/test_artifacts.py` — единственный packaging test module и никогда не вызывает skip.

`.github/workflows/package-test.yml`:

1. job `build-and-validate`: `uv build` ровно один раз, artifact test, upload wheel+sdist;
2. job `install`: один wheel устанавливается pip в 4 matrix cells, `uv pip` один раз и `uv add` один раз.

Триггеры workflow (`on: pull_request` и `push` на `main`) сохраняются.

`.github/workflows/ci.yml` не содержит distribution build и `uv build` в compatibility cells.

Wheel содержит только runtime package и `py.typed`. Sdist включает `src`, `tests`, `scripts`, `tools/live_support`, docs и build metadata. `tools` не входит в wheel.

### 7. Shared operational tooling

```text
tools/live_support/
├── __init__.py
├── environment.py
└── diagnostics.py
```

`environment.py` владеет `LiveSetupError`, `CompatibilityTarget`, shared settings/target parsing. `diagnostics.py` владеет shared artifact scanning/redaction. Test-only hooks/assertions остаются в `tests/`.

### 8. Live core

```text
tests/live/
├── api.py
├── session.py
├── backend.py
├── operations.py
├── crud_descriptors.py
├── diagnostics.py
├── conftest.py
├── test_*.py
└── sandbox/
    ├── __init__.py
    ├── models.py
    ├── policy.py
    └── workflow.py
```

- `api.py` `<=350` lines: один `LiveApiClient`; oracle — typed functions над ним.
- `session.py` `<=450` lines: `LiveEnvironment`, `LiveSession`, `LiveCase`, `SandboxSession` context managers.
- `backend.py` `<=650` lines: compose/daemon/bootstrap lifecycle.
- `operations.py` `<=350` lines: direct live executor callables keyed by executor ID, не operation registry.
- `crud_descriptors.py`: fully declarative descriptors.
- `conftest.py` `<=300` lines: pytest hooks и ровно четыре public fixtures.
- `diagnostics.py` — test-only diagnostics hooks/assertions поверх `tools.live_support.diagnostics` (миграция в T068).
- `tests/live/environment.py`, `oracle.py`, `resources.py` удаляются после миграции.

### 9. Live policy

Каждый `OperationCase` содержит `LivePolicy`:

- `mode`: `smoke`, `extended`, `sandbox`, `unrunnable`;
- `owner`: `direct:<executor-id>`, `crud:<descriptor-id>`, `sandbox`, `none`;
- `reason`: `null` кроме `unrunnable`.

Separate operation-ID lists (`LIVE_OPERATIONS`, `LIVE_EXEC_EXCEPTIONS`, CRUD/sandbox ID sets) удаляются. Gate проверяет ровно одну policy на каждый из 111 operation IDs.

### 10. Declarative CRUD

`CrudDescriptor[T]` содержит profile/create/get/update/delete/identity/assert_created/assert_fetched/assert_updated/assert_oracle/assert_deleted. Все fields обязательны. `CRUD_CASES` применяет marker из profile. `delete` идемпотентен.

`tests/live/test_crud.py` выполняет один фиксированный algorithm и использует только fields descriptor. Source-AST test запрещает branch/lookup/cast по descriptor identity.

### 11. Sandbox

- `models.py`: immutable `PreparedSandbox`, `CompletedAssignment`, `SandboxVerification`.
- `workflow.py`: ровно `prepare_sandbox`, `run_assignment`, `verify_sandbox`.
- `policy.py`: filesystem manifest policy.
- Cleanup регистрируется внутри `prepare`/`run` сразу после create.
- Обычные live fixtures не импортируют sandbox workflow.

## Progressive Gates

| Stage | Обязательный результат |
|---|---|
| `pr1` | Green process/offline suite; behavior manifest и schema-2 baseline зафиксированы. |
| `pr2` | Один `OperationCase` registry; все 111 IDs и required dimensions сохранены; tests LOC не выше PR-1 baseline. |
| `pr3` | `tests_python<=11000`; fixture tree отсутствует; packaging без skip; scripts/src не импортируют tests. |
| `pr4` | Declarative CRUD; 4 contexts; 1 HTTP boundary; live support `<=3000`. |
| `final` | `tests_python<=10500`; live support `<=2500`; каждый file `<=800`; live/canary gates green. |

Offline duration на всех compare stages: `current <= max(45.0, baseline * 1.5)` seconds.

## Последовательность delivery

1. **PR 1 — `baseline-process`**: timeout dependency, process harness/state, hard network prohibition, behavioral manifest, schema-2 baseline, architecture/quality gates.
2. **PR 2 — `operation-catalog`**: `OperationCase`, unit executor, programmable fake CLI, component round trip, `ERROR_CASES`, удаление старых catalogs.
3. **PR 3 — `offline-cleanup`**: fixture deletion, dead/duplicate cleanup, six contract modules, package single-build, `tools/live_support`.
4. **PR 4 — `live-core`**: `LiveApiClient`, four contexts, declarative CRUD, live policy ownership, ExitStack cleanup.
5. **PR 5 — `sandbox-final`**: isolated sandbox phases, final LOC/file gates, complete offline/live/package/canary evidence.

Каждый PR MUST пройти свой gate до начала следующего. Изменение порядка запрещено.
