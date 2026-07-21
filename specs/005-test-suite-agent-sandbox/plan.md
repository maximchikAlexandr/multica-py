# Implementation Plan — Spec 005

## 1. Summary

План реализует четыре независимых результата в фиксированной последовательности:

1. восстановление достоверности offline test signal;
2. сокращение дублирования test/live infrastructure;
3. добавление typed project-resource SDK и deterministic agent sandbox workflow;
4. оптимизация CI, package validation, mutation audit и real OpenCode canary.

Исполнитель реализует ровно восемь PR: `PR-01` соответствует Phase 0, `PR-02` — Phase 1, …, `PR-08` — Phase 7. Фазы не объединяются и не переставляются. Каждый PR обязан проходить свой exit gate и быть самостоятельно откатываемым.

## 2. Technical context

| Area | Fixed decision |
|---|---|
| Language | Python 3.12/3.13 |
| Package/build | `uv`, Hatchling |
| Models | existing `msgspec.Struct` conventions |
| Test runner | pytest 8+ |
| Parallel offline tests | `pytest-xdist>=3,<4` |
| Coverage | `pytest-cov`, branch enabled |
| Mutation | `mutmut>=3,<4`, separate group/workflow |
| Live backend | existing Docker Compose lifecycle and pinned Multica target |
| Agent runtime | real Multica daemon registration |
| Blocking agent executable | `tests/fixtures/fake_opencode.py` |
| Real provider | OpenCode path/model from environment |
| Test data factories | explicit deterministic builders; no Polyfactory/Hypothesis |
| Snapshots | ordinary JSON/TOML fixtures; no Syrupy |
| Cleanup | existing registry + exact compensation order + CI `if: always()` cleanup |

## 3. Constitution check

Source: `.specify/memory/constitution.md` (v1.0.0).

| Principle | Spec 005 alignment | Gate |
|---|---|---|
| I. Source-Driven CLI Contract | Project-resource and issue `--project` argv pinned with upstream tag `v0.3.10` source refs in `contracts/project-resources-sdk.md` | PASS after contract refs complete |
| II. Thin Synchronous Wrapper | No server API bypass; daemon/subprocess and public SDK only | PASS |
| III. Typed Public Surface | New msgspec models; optional `IssueUsage.cost_usd`; no `Any` | PASS |
| IV. Offline Testability | Default excludes `live`; fake CLI/fixtures; `tests/component` satisfies the constitution integration/fake-executable gate by behavior | PASS |
| V. Secure Packaging | Diagnostic redaction SC-013 | PASS |

Re-check required after PR-04 (public SDK) and PR-06 (live workflow).

Repository `AGENTS.md` Writing Tests section MUST be updated in PR-03 to document `CommandCase`, `tests/component/`, and marker rules.

## 4. Implementation lock

Запрещено во время реализации:

- добавлять альтернативный runtime create API;
- создавать workspace через public SDK;
- использовать real LLM в blocking live-smoke;
- заменять fake executable моками transport/backend;
- вводить generic test framework;
- использовать subtests, snapshots, random factories or property-based generators;
- сохранять generated traceability Markdown;
- расширять canary до нескольких models/providers;
- использовать Multica target, отличный от release tag `v0.3.10`;
- параллелить live tests.

## 5. Target file map

### Production SDK

Create:

- `src/multica_py/models/project_resources.py`
- `src/multica_py/resources/project_resources.py`

Modify:

- `src/multica_py/resources/projects.py`
- `src/multica_py/models/issues.py`
- `src/multica_py/resources/issues.py`
- `src/multica_py/models/__init__.py`
- `src/multica_py/__init__.py`
- `tests/contract/test_cli_manifest.py`
- `tests/contract/test_full_cli_coverage.py`
- `tests/contract/test_issue_models.py`
- `tests/contract/test_public_invariants.py`
- `tests/_manifest_support.py`
- `docs/api.md`
- `docs/cli-coverage.md`

### Offline tests

Create or final names after move:

- `tests/fixtures/child_process.py`
- `tests/unit/test_client_lifecycle.py`
- `tests/component/test_process_contract.py`
- `tests/component/resources/cases.py`
- `tests/component/resources/test_commands.py`
- `tests/component/resources/test_decoding.py`
- `tests/component/resources/test_errors.py`
- `tests/component/resources/test_presence_semantics.py`
- `tests/unit/test_project_resource_models.py`
- `tests/component/test_project_resources.py`
- `tests/component/test_issue_project_assignment.py`
- `tests/unit/test_fake_opencode.py`
- `tests/component/test_fake_opencode_process.py`
- `tests/unit/test_quality_baseline_tools.py`
- `tests/unit/test_live_sandbox_support.py`
- `tests/unit/test_canary_environment.py`
- `tests/unit/test_live_diagnostics.py`
- `tests/contract/test_ci_profiles.py`

Delete/move:

- delete `tests/integration/test_issue_workflows.py`;
- delete three low-signal Popen/tuple tests from `test_streaming_commands.py`;
- move all retained integration tests under `tests/component`;
- delete `tests/integration` after `pytest --collect-only` count reconciliation.

### Live support final structure

Keep exactly:

- `tests/live/conftest.py`
- `tests/live/environment.py`
- `tests/live/backend.py`
- `tests/live/resources.py`
- `tests/live/crud_descriptors.py`
- `tests/live/oracle.py`
- `tests/live/diagnostics.py`

Move contents:

- `settings.py`, `profile.py`, `context.py`, `exceptions.py` → `environment.py`;
- `bootstrap.py`, `compose.py`, new daemon lifecycle → `backend.py`;
- `live_operations.py`, `resource_registry.py`, sandbox workflow operations → `resources.py`.

Create:

- `tests/fixtures/fake_opencode.py`
- `tests/live/test_agent_sandbox.py`
- `tests/live/extended/test_agent_sandbox_failures.py`
- `tests/live/extended/test_opencode_canary.py`

### Scripts and CI

Create:

- `scripts/check_coverage.py`
- `scripts/capture_test_baseline.py`
- `scripts/check_test_baseline.py`
- `scripts/cleanup_live_resources.py`
- `tests/quality-baseline.json`
- `.github/workflows/mutation.yml`
- `.github/workflows/live-opencode-canary.yml`

Modify:

- `pyproject.toml`
- `.github/workflows/ci.yml`
- `.github/workflows/package-test.yml`
- `.github/workflows/live-extended.yml`
- `tests/live/README.md`
- `scripts/run_live_tests.py`

Rename:

- `tests/_coverage_guard.py` → `tests/_manifest_coverage.py`; preserve `assert_manifest_coverage` behavior and update imports. This helper checks CLI-manifest operation coverage and is not the code-coverage gate.

Keep:

- `contracts/multica-live-target.toml`; update only its pinned target fields through the existing resolver.

## 6. Phase sequence

### Phase 0 — Baseline tooling and capture (`PR-01`)

1. Checkout the implementation branch and export `BASELINE_SHA=$(git rev-parse HEAD)` before creating or modifying any file.
2. Create `scripts/check_coverage.py`, `scripts/capture_test_baseline.py` and `scripts/check_test_baseline.py` exactly to `contracts/quality-baseline.md`. Do not change production code, tests, markers or workflows in this PR before baseline capture.
3. Run exact commands from `quickstart.md` section 2; all commands MUST pass. A failing baseline blocks the feature and is not converted into an allowlist.
4. Resolve release tag `v0.3.10` using existing `scripts/resolve_multica_target.py` through the repository's current target-resolution entry point and update `contracts/multica-live-target.toml` with full commit and immutable image digests.
5. Generate `tests/quality-baseline.json` only through `scripts/capture_test_baseline.py --source-sha "$BASELINE_SHA"`; the stored SHA is the pre-change source commit and is never rewritten.
6. Commit the three scripts, target manifest and generated baseline together.
7. After `PR-01`, `tests/quality-baseline.json` is immutable except for an explicit follow-up spec; later PRs only read it.

Exit gate:

- live target manifest names `v0.3.10` and contains resolved full commit/image digests;
- baseline conforms to `contracts/quality-baseline.md` and contains the pre-change source SHA, layer counts, LOC, duration, coverage and package path count;
- current offline tests and zonal coverage gates pass on the recorded SHA;
- after committing `PR-01`, a repeated capture with the same `BASELINE_SHA` produces byte-identical JSON and `git diff --exit-code` is clean.

### Phase 1 — Offline test signal (`PR-02`)

1. Add root markers: `unit`, `contract`, `component`, `process`, `compat`, `serial`, `live`, `live_smoke`, `live_extended`, `live_opencode_canary`.
2. Set root `addopts` to include `-m "not live"`.
3. Add path-based marker assignment in root `tests/conftest.py`.
4. Rename `tests/_coverage_guard.py` to `tests/_manifest_coverage.py`, update every import, and leave the helper behavior unchanged.
5. Delete exact five low-signal functions from the audit.
6. Add `test_client_lifecycle.py` with `normal-exit` and `exception-exit` cases.
7. Create deterministic `child_process.py` fixture and migrate all process tests.
8. Consolidate four process lifecycle tests into one parameterized function.
9. Rename `tests/integration` to `tests/component` and update mypy overrides/imports/workflows/docs.
10. Run `scripts/check_test_baseline.py --baseline tests/quality-baseline.json --mode compare --stage PR-02`.

Exit gate:

- no `tests/integration` path remains;
- default collection includes zero live items;
- process timeout proves parent+child termination;
- mandatory offline case count is not lower than baseline.

### Phase 2 — Table-driven resource tests and live infrastructure (`PR-03`)

1. Introduce `CommandCase` exactly as defined in `data-model.md`.
2. Migrate resource test behavior into four modules and one data catalog.
3. Preserve literal expected argv and fixture output.
4. Expand existing `CrudDescriptor` to the exact schema in `data-model.md`.
5. Move live helper code into the seven fixed support modules.
6. Remove pass-through wrappers and old helper modules only after all imports are migrated.
7. Update live README commands; remove stale manual traceability table entirely.
8. Run `scripts/check_test_baseline.py --baseline tests/quality-baseline.json --mode compare --stage PR-03`; it MUST enforce the 25% resource test/support LOC reduction.

Exit gate:

- all standard resource operations are descriptor cases;
- no standard CRUD one-resource test file remains;
- live support module count equals seven;
- collected behavioral case count is preserved.

### Phase 3 — Public project-resource and issue-project SDK (`PR-04`)

1. Implement models from `contracts/project-resources-sdk.md` using current `msgspec.Struct` style.
2. Implement `ProjectResourceCollection` nested under existing `ProjectResource` instance as `.resources`.
3. Implement `list`, `add_local_directory`, `update_local_directory`, `remove` with exact argv contract.
4. Add `project_id` to issue create/update request models.
5. Add `--project` argv handling to issue create/update.
6. Add public-surface, model, command, decoding and error tests.
7. Update `tests/contract/test_cli_manifest.py`, `tests/contract/test_full_cli_coverage.py`, `tests/contract/test_issue_models.py`, `tests/contract/test_public_invariants.py`, and `tests/_manifest_support.py` for the new public/CLI surface without changing target SHA.
8. Update `docs/api.md` and `docs/cli-coverage.md`.

Exit gate:

- public contract tests include new types and methods;
- component tests prove exact argv;
- live test can attach/list/remove `local_directory` exclusively through public SDK.

### Phase 4 — Deterministic OpenCode contract (`PR-05`)

1. Implement `tests/fixtures/fake_opencode.py` to the exact contract in `contracts/deterministic-opencode.md`.
2. Add unit tests for instruction parsing, containment, exact-before, atomic write and JSONL events.
3. Add component test spawning the executable with canonical OpenCode argv.
4. Implement failure modes selected only by `MULTICA_TEST_AGENT_MODE`: `success`, `error`, `timeout`, `wrong-edit`.
5. Ensure default mode is `success`; unknown mode exits 64 before touching files.

Exit gate:

- success modifies exactly one file and emits required events;
- each failure mode is deterministic;
- test executable has no network access and does not import production SDK internals.

### Phase 5 — Daemon/runtime and agent sandbox workflow (`PR-06`)

1. Extend live `backend.py` with `DaemonLifecycle` from `contracts/agent-sandbox-workflow.md`.
2. Create isolated HOME/profile/workspaces root under run temp root.
3. Start real daemon foreground with fake OpenCode path.
4. Poll runtimes until exactly one matching online OpenCode runtime exists.
5. Create agent by name only; runtime association is implicit via daemon registration and issue assignment.
6. Create workspace through `BootstrapApiClient`.
7. Create project and issue through public SDK.
8. Attach and list-verify local directory through `client.projects.resources`.
9. Snapshot filesystem manifest.
10. Assign issue to agent exactly once.
11. Poll run to terminal outcome.
12. Assert routing and exact filesystem result.
13. Always execute fixed cleanup order and postcondition audit.
14. Add `live_smoke` marker to success workflow only.
15. Add extended failure cases `agent-error`, `agent-timeout`, `wrong-edit`, `cleanup-failure`.

Exit gate:

- one `live_smoke` case passes under 120 seconds;
- 20-repeat run has 20/20 pass and no leftovers;
- all four extended negative cases generate diagnostics and no leftovers.

### Phase 6 — Coverage, compatibility, package and mutation (`PR-07`)

1. Wire the already-created `scripts/check_coverage.py` into `quality`; do not reuse or delete `tests/_manifest_coverage.py`.
2. Add `pytest-xdist>=3,<4` to `test` dependency group.
3. Add `mutmut` to separate `mutation` dependency group.
4. Split `ci.yml` into `quality`, `compatibility`, and existing `live-smoke` jobs.
5. Quality: parallel non-serial pass + serial coverage append + reports + zonal check.
6. Compatibility: four cells, marker `compat` only.
7. Package: build wheel once, 4 pip cells, 1 uv-pip and 1 uv-add path.
8. Add weekly/manual mutation workflow, targeted sources only.
9. Run `scripts/check_test_baseline.py --baseline tests/quality-baseline.json --mode compare --stage PR-07`.
10. Run one complete targeted mutation audit and upload `mutmut results` as a text artifact. Do not create a mutation-score baseline and do not block PRs on survivor count.

Exit gate:

- quality is the only full offline run;
- 4 compatibility cells pass;
- package path count equals six;
- mutation workflow does not invoke live/backend/Docker and publishes a readable result artifact.

### Phase 7 — Real OpenCode canary and external cleanup (`PR-08`)

1. Add `live_opencode_canary` test reusing sandbox workflow helper.
2. Validate required environment before backend startup.
3. Require `MULTICA_CANARY_SECRET_NAMES`, validate every named secret, then use real OpenCode path/model, one issue, 15-minute timeout and 0.10 USD ceiling.
4. Add Sunday 03:00 UTC + manual workflow.
5. Do not add workflow name to required branch checks.
6. Add `if: always()` external cleanup to live workflows.
7. Upload sanitized diagnostics and cleanup audit.

Exit gate:

- incomplete env produces skip before Docker startup;
- configured run yields passed or failed with artifacts;
- workflow is independent from PR required checks.

## 7. Architecture

### 7.1. Offline command testing

`CommandCase` replaces `FakeCliCase` for resource command coverage. Existing `ArgvCase` remains for unit argv tests. Migration rule:

- unit layer: keep `ArgvCase` in `tests/unit/resources/cases/`;
- component layer: migrate each former `FakeCliCase.id` to one `CommandCase.id` with the same stable ID string;
- JSON fixtures under `tests/fixtures/json/` are inlined into `tests/component/resources/cases.py` as literal stdout/stderr/expected values and then deleted when no longer referenced;
- `KNOWN_FIXTURE_GAPS` entries MUST be removed when the corresponding `CommandCase.id` lands.

`CommandCase` is data only. Test modules own behavior. Production resources are never imported into case-generation helpers except for the public invocation callable. Expected values remain literals.

Flow:

`case catalog → pytest.param(id) → fake CLI process → SDK public call → literal assertion`.

### 7.2. Live workflow ownership

- `environment.py`: validated settings, run IDs, paths, immutable contexts and live errors.
- `backend.py`: compose backend, bootstrap API client, CLI profile and daemon process lifecycle.
- `resources.py`: cleanup registry, SDK operations, agent sandbox orchestration and postcondition audit.
- `crud_descriptors.py`: data only.
- `oracle.py`: independent backend/API verification.
- `diagnostics.py`: redaction and bundles.
- `conftest.py`: fixture composition only; no domain branching.

### 7.3. Runtime creation

There is no runtime create call. `DaemonLifecycle.start()` launches the daemon. The daemon detects `MULTICA_OPENCODE_PATH`, applies fixed `MULTICA_OPENCODE_MODEL=multica-test/fake`, registers a runtime, and sends heartbeats. `DaemonLifecycle.stop()` stops the daemon. The test then waits until the runtime is absent or non-routable.

### 7.4. Workspace ownership

`BootstrapApiClient` owns workspace create/delete because the public SDK is intentionally read-oriented for workspaces. All project/issue/agent/project-resource behavior uses public SDK.

## 8. Testing strategy

### Unit

- model validation and decoding;
- instruction parser and file mutation;
- cleanup ordering/idempotence;
- file manifest/diff;
- context manager lifecycle;
- coverage and test-baseline scripts.

### Contract

- public exports;
- project resource command inventory;
- issue `--project` support;
- marker/profile architecture;
- deterministic OpenCode event schema fixtures.

### Component

- exact argv and JSON decoding against fake CLI;
- process lifecycle;
- project resource list/add/update/remove;
- issue create/update project flag;
- fake OpenCode subprocess invocation.

### Live smoke

Exactly one new test:

`test_agent_executes_issue_in_local_directory`.

### Live extended

Exactly four deterministic negative variants:

- `agent-error`;
- `agent-timeout`;
- `wrong-edit`;
- `cleanup-failure`.

### Canary

Exactly one real-provider test:

`test_real_opencode_executes_issue_in_local_directory`.

## 9. Diagnostics contract

See `contracts/live-diagnostics-bundle.md`. Plan-level summary: every live failure bundle directory is `<artifact-root>/<run_id>/` with the thirteen filenames defined in that contract.

## 10. Rollback boundaries

- `PR-01` rollback removes baseline tooling/baseline and restores the previous live-target manifest.
- `PR-02` rollback restores only offline test layout, markers and the `_coverage_guard.py` filename.
- `PR-03` rollback restores resource-test and live-helper layout without production API changes.
- `PR-04` rollback removes public project-resource/issue-project SDK additions and their tests/docs.
- `PR-05` rollback removes the deterministic OpenCode executable and its unit/component tests.
- `PR-06` rollback removes the daemon sandbox workflow and its live tests without changing existing live scenarios.
- `PR-07` rollback restores previous CI/package workflows and removes xdist/mutation integration while retaining implemented product behavior.
- `PR-08` rollback removes only the real OpenCode canary and external cleanup additions introduced there.

No database migration or server change is introduced, so every rollback is repository-only.

## 11. Completion gate

Feature is complete only when all commands in `quickstart.md` pass, `scripts/check_test_baseline.py --baseline tests/quality-baseline.json --mode compare --stage final` passes, all contracts are implemented, checklist remains PASS, 20-repeat deterministic live run is clean, and no unresolved implementation choice remains in the artifacts.
