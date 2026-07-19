# Tasks - Spec 005: Reliable Test System and Agent Sandbox Live Workflow

## Execution rules

- Execute tasks in numeric order unless a task is marked `[P]` and the dependency section explicitly allows parallel work.
- Preserve the fixed PR boundaries: PR-01 through PR-08. Do not merge or reorder PRs.
- Do not introduce Hypothesis, Polyfactory, Syrupy, Testcontainers, pytest-subtests, BDD, Screenplay, Page Object, a runtime create API, or public workspace CRUD.
- Run live tests serially. Never run `tests/live` through xdist.
- Treat every exit gate as blocking. Do not add allowlists for a failing baseline or failing live cleanup.

## Phase mapping

Each plan phase maps to exactly one PR. Task phases use the same PR labels.

| Plan phase | PR | Task range | Exit gate task |
|---|---|---|---|
| Phase 0 | PR-01 | T001–T011 | T011 |
| Phase 1 | PR-02 | T012–T027 | T027 |
| Phase 2 | PR-03 | T028–T043 | T043 |
| Phase 3 | PR-04 | T044–T055 | T055 + contract tests green |
| Phase 4 | PR-05 | T056–T061 | T061 |
| Phase 5 | PR-06 | T062–T082 | T082 |
| Phase 6 | PR-07 | T083–T093 | T091 |
| Phase 7 | PR-08 | T094–T104 | T104 |
| — | completion | T105–T111 | T110 |

## PR-01 commit boundary

The first committed feature files in PR-01 MUST be only:

- `scripts/check_coverage.py`
- `scripts/capture_test_baseline.py`
- `scripts/check_test_baseline.py`
- `contracts/multica-live-target.toml` (digest update only)
- `tests/quality-baseline.json`

Unit tests for baseline scripts (`tests/unit/test_quality_baseline_tools.py`) are created in PR-02 (T012–T013) after the PR-01 commit.

## Phase 1: PR-01 preparation (T001–T003)

- [ ] T001 Confirm the repository working tree is clean, export the pre-change `BASELINE_SHA=$(git rev-parse HEAD)`, and preserve that value for `tests/quality-baseline.json`.
- [ ] T002 Create transient baseline output directories `.artifacts/baseline/` and `.artifacts/target-resolution/` without modifying production, test, workflow, dependency, or marker files.
- [ ] T003 Run the prerequisite commands from `specs/005-test-suite-agent-sandbox/quickstart.md` and save their output to `.artifacts/baseline/prerequisites.txt`.

## Phase 2: PR-01 baseline capture (T004–T011)

- [ ] T004 Create `scripts/check_coverage.py` with the exact CLI, sorted zone output, regex loading, threshold loading, missing-zone failure, and exit codes defined in `specs/005-test-suite-agent-sandbox/contracts/quality-baseline.md`.
- [ ] T005 Create `scripts/capture_test_baseline.py` with the exact allowed-diff check, layer collection, five-node exclusion, LOC rule, JUnit parsing, coverage copying, deterministic JSON serialization, and immutable-output behavior defined in `specs/005-test-suite-agent-sandbox/contracts/quality-baseline.md`.
- [ ] T006 Create `scripts/check_test_baseline.py` with `self-check` and fixed `PR-02`, `PR-03`, `PR-07`, and `final` comparison stages defined in `specs/005-test-suite-agent-sandbox/contracts/quality-baseline.md`.
- [ ] T007 Run the pre-change offline suite with JUnit and statement/branch coverage and create `.artifacts/baseline/offline.xml` and `.artifacts/baseline/coverage.json`.
- [ ] T008 Run `scripts/check_coverage.py` against `.artifacts/baseline/coverage.json` and fix only the script if its implementation violates `specs/005-test-suite-agent-sandbox/contracts/quality-baseline.md`; do not alter existing tests to make the baseline pass.
- [ ] T009 Generate `tests/quality-baseline.json` with `scripts/capture_test_baseline.py --source-sha "$BASELINE_SHA"` and verify all five excluded low-signal node IDs were collected exactly once.
- [ ] T010 Resolve Multica release tag `v0.3.10` through the existing resolver and update only the pinned ref, full upstream commit, and immutable image digests in `contracts/multica-live-target.toml`.
- [ ] T011 Commit PR-01 with only the five allowed files listed in `plan.md` PR-01 commit boundary, then re-run capture/self-check and verify `git diff --exit-code`.

## Phase 3: PR-02 baseline script tests and offline signal part 1 (T012–T027)

- [ ] T012 [P] Add deterministic unit coverage for all success and failure branches of `scripts/check_coverage.py` in `tests/unit/test_quality_baseline_tools.py`.
- [ ] T013 [P] Add deterministic unit coverage for baseline schema validation, five-node exclusion, immutable bytes, ancestor SHA validation, and unknown stage rejection in `tests/unit/test_quality_baseline_tools.py`.
- [ ] T014 [US1] Register `unit`, `contract`, `component`, `packaging`, `process`, `compat`, `serial`, `live`, `live_smoke`, `live_extended`, and `live_opencode_canary` markers and set default `-m "not live"` in `pyproject.toml`.
- [ ] T015 [US1] Add path-based layer marker assignment and one-profile-per-live-case validation per `specs/005-test-suite-agent-sandbox/contracts/marker-profiles.md` in `tests/conftest.py`.
- [ ] T016 [US1] Rename `tests/_coverage_guard.py` to `tests/_manifest_coverage.py`, preserve `assert_manifest_coverage`, and update every import under `tests/`.
- [ ] T017 [P] [US1] Delete `tests/integration/test_issue_workflows.py` in full.
- [ ] T018 [P] [US1] Delete `test_managed_process_argv`, `test_managed_process_stdout_lines`, and `test_managed_process_consumes_partial_output` from `tests/integration/test_streaming_commands.py`; retain `test_managed_process_poll` unchanged for migration to `tests/component/`.
- [ ] T019 [US1] Create `tests/unit/test_client_lifecycle.py` with exactly `normal-exit` and `exception-exit` parameter IDs, one canonical close call per case, and propagation of the body exception.
- [ ] T020 [US1] Create deterministic executable harness `tests/fixtures/child_process.py` supporting stdout, stderr, exit code, ready file, release file, PID file, and child-process mode.
- [ ] T021 [US1] Create `tests/component/test_process_contract.py` with one parameterized lifecycle function containing IDs `success`, `non-zero-exit`, `stdout`, `stderr`, and `timeout`.
- [ ] T022 [US1] Add parent/child termination, exception field, argv redaction, and unconditional process-group finalizer assertions to the `timeout` case in `tests/component/test_process_contract.py`.
- [ ] T023 [US1] Move every retained module and fixture from `tests/integration/` to the matching path under `tests/component/`, preserving test behavior and node IDs except for the layer path; delete `tests/integration/test_process_lifecycle.py` after its cases are represented in `tests/component/test_process_contract.py`.
- [ ] T024 [US1] Update test paths, mypy overrides, pytest settings, and package include/exclude references from `tests/integration` to `tests/component` in `pyproject.toml`.
- [ ] T025 [P] [US1] Update repository scripts and workflow selections from `tests/integration` to `tests/component` in `.github/workflows/ci.yml`, `.github/workflows/package-test.yml`, and `scripts/run_live_tests.py`.
- [ ] T026 [P] [US1] Update user-facing path references from `tests/integration` to `tests/component` in `README.md`, `tests/live/README.md`, and `docs/` Markdown files that contain the old path; update `AGENTS.md` Writing Tests section to document `CommandCase`, `tests/component/`, marker rules, and remove stale `FakeCliCase` guidance.
- [ ] T027 [US1] Run `scripts/check_test_baseline.py --baseline tests/quality-baseline.json --mode compare --stage PR-02` and store the command output in `.artifacts/baseline/pr-02.txt`.

## Phase 4: PR-03 offline signal part 2 — CommandCase and live helpers (T028–T043)

- [ ] T028 [US1] Define immutable `CommandCase` and its success/error invariant in `tests/component/resources/cases.py` exactly as specified in `specs/005-test-suite-agent-sandbox/data-model.md`.
- [ ] T029 [US1] Migrate each former `FakeCliCase.id` to one `CommandCase.id` with the same stable ID, inlining literal stdout/stderr/expected values from JSON fixtures into `tests/component/resources/cases.py`.
- [ ] T030 [P] [US1] Create `tests/component/resources/test_commands.py` to assert literal argv, environment, cwd, and timeout for command cases.
- [ ] T031 [P] [US1] Create `tests/component/resources/test_decoding.py` to assert stdout decoding into the exact typed result for success cases.
- [ ] T032 [P] [US1] Create `tests/component/resources/test_errors.py` to assert non-zero exit, malformed output, mapped exception fields, and secret redaction.
- [ ] T033 [P] [US1] Create `tests/component/resources/test_presence_semantics.py` to assert omitted, null, empty, and optional flag behavior.
- [ ] T034 [US1] Delete the superseded one-resource test modules under `tests/component/resources/` only after every former behavior is represented by a stable case ID in `tests/component/resources/cases.py`; remove matching stale `KNOWN_FIXTURE_GAPS` entries when each ID lands.
- [ ] T035 [US1] Expand the immutable `CrudDescriptor` schema and invariants in `tests/live/crud_descriptors.py` exactly as specified in `specs/005-test-suite-agent-sandbox/data-model.md`.
- [ ] T036 [US1] Migrate standard live create/get/list/update/delete behavior into the registry in `tests/live/crud_descriptors.py` and the canonical parameterized runner in `tests/live/test_crud.py`.
- [ ] T037 [P] [US1] Merge settings, profile, context, and live-specific exceptions into `tests/live/environment.py` without orchestration logic.
- [ ] T038 [P] [US1] Merge bootstrap and Compose lifecycle behavior into `tests/live/backend.py` while preserving the current backend start, health, and stop contract.
- [ ] T039 [P] [US1] Merge live operations and cleanup registry behavior into `tests/live/resources.py` without importing or invoking another descriptor.
- [ ] T040 [US1] Reduce `tests/live/conftest.py` to fixture composition using only `environment.py`, `backend.py`, `resources.py`, `crud_descriptors.py`, `oracle.py`, and `diagnostics.py`.
- [ ] T041 [US1] Delete superseded live support modules only after imports are migrated and enforce the exact seven-file support structure in `tests/live/`.
- [ ] T042 [US1] Remove the stale manual traceability table and document exact default, smoke, and extended commands in `tests/live/README.md`.
- [ ] T043 [US1] Run `scripts/check_test_baseline.py --baseline tests/quality-baseline.json --mode compare --stage PR-03` and store the passing output in `.artifacts/baseline/pr-03.txt`.

## Phase 5: PR-04 public project-resource and issue-project SDK (T044–T055)
- [ ] T045 [US2] Export the new project-resource models from `src/multica_py/models/__init__.py` and `src/multica_py/__init__.py`.
- [ ] T046 [P] [US2] Create `ProjectResourceCollection` with exact `list`, `add_local_directory`, `update_local_directory`, and `remove` argv order and existing transport/error behavior in `src/multica_py/resources/project_resources.py`.
- [ ] T047 [US2] Construct one nested `.resources` collection on the existing project collection in `src/multica_py/resources/projects.py`.
- [ ] T048 [US2] Add model validation and decoding tests for project-resource records, discriminator handling, canonical absolute paths, empty IDs, and optional labels in `tests/unit/test_project_resource_models.py`.
- [ ] T049 [US2] Add exact argv, optional label, decoding, malformed response, and non-zero exit tests for all four project-resource methods in `tests/component/test_project_resources.py`.
- [ ] T050 [P] [US2] Add optional non-empty `project_id` fields to issue create and update request models in `src/multica_py/models/issues.py`.
- [ ] T051 [US2] Emit exactly one `--project <project_id>` flag for issue create and update in `src/multica_py/resources/issues.py`.
- [ ] T052 [US2] Add optional `cost_usd: float | None` to `IssueUsage` with decoding tests and add omitted, present, empty, create, and update project-association cases in `tests/component/test_issue_project_assignment.py`.
- [ ] T053 [US2] Add the project-resource command inventory and issue `--project` paths to `tests/contract/test_cli_manifest.py`, `tests/contract/test_full_cli_coverage.py`, and `tests/_manifest_support.py` without changing the pinned target SHA.
- [ ] T054 [US2] Add public exports and issue model invariants to `tests/contract/test_public_invariants.py` and `tests/contract/test_issue_models.py`.
- [ ] T055 [US2] Document `client.projects.resources` and issue `project_id` in `docs/api.md` and `docs/cli-coverage.md`.

## Phase 6: PR-05 deterministic OpenCode executable (T056–T061)

- [ ] T056 [P] [US2] Implement strict canonical argv parsing for the single supported `run --format json --dangerously-skip-permissions --dir ... --model multica-test/fake <prompt>` command in `tests/fixtures/fake_opencode.py`.
- [ ] T057 [US2] Implement exact `MULTICA_TEST_ACTION` extraction and schema, key, relative path, containment, regular-file, UTF-8, and exact-before validation in `tests/fixtures/fake_opencode.py`.
- [ ] T058 [US2] Implement sibling temporary write, flush, `os.replace`, and the exact three-line success JSONL stream in `tests/fixtures/fake_opencode.py`.
- [ ] T059 [US2] Implement `success`, `error`, `timeout`, `wrong-edit`, and unknown-mode behavior with fixed exit codes and no unintended file mutation in `tests/fixtures/fake_opencode.py`.
- [ ] T060 [US2] Add all required parser, path, file, before mismatch, atomic write, JSONL, and failure-mode tests in `tests/unit/test_fake_opencode.py`.
- [ ] T061 [US2] Add a real subprocess contract test for canonical argv, stdout flushing, timeout termination, exit codes, and file results in `tests/component/test_fake_opencode_process.py`.

## Phase 7: PR-06 daemon/runtime and agent sandbox workflow (T062–T082)

- [ ] T062 [US2] Add every `LiveRunContext` field, adopt 32-character lowercase hex `run_id` per FR-027, exact run prefix, canonical path construction, and immutable setting validation to `tests/live/environment.py`.
- [ ] T063 [P] [US2] Implement deterministic `FileManifest` creation and the fixed target/control/AGENTS/.multica comparison policy in `tests/live/resources.py`.
- [ ] T064 [P] [US2] Implement `CleanupAction`, fixed cleanup ordering, idempotent already-absent handling, error accumulation, and primary-failure preservation in `tests/live/resources.py`.
- [ ] T065 [US2] Add focused unit tests for file manifest policy, cleanup ordering, idempotence, and primary-failure preservation in `tests/unit/test_live_sandbox_support.py`.
- [ ] T066 [US2] Implement `DaemonLifecycle.start()` with isolated HOME/profile/workspaces root and exact daemon environment, foreground process handling, graceful stop, terminate, and kill escalation in `tests/live/backend.py`.
- [ ] T067 [US2] Implement runtime readiness polling, exact one-runtime matching, 60-second readiness deadline, 1-second polling, 30-second deregistration deadline, and non-routable terminal handling in `tests/live/backend.py`.
- [ ] T068 [US2] Implement bootstrap identity/token/workspace creation and isolated CLI profile writing through the existing `BootstrapApiClient` in `tests/live/backend.py`.
- [ ] T069 [P] [US2] Implement the exact failure bundle file set, daemon/Compose capture, hashes, unified diffs, and value-based secret redaction in `tests/live/diagnostics.py`.
- [ ] T070 [P] [US2] Extend independent backend/API verification for workspace, project, issue, agent, runtime, and project resource state in `tests/live/oracle.py`.
- [ ] T071 [US2] Implement sandbox directory creation, exact initial target/control bytes, agent creation, project creation, issue creation without assignee, and immediate cleanup registration in `tests/live/resources.py`.
- [ ] T072 [US2] Implement `add_local_directory`, list verification of canonical path and daemon ID, resource cleanup registration, and pre-dispatch manifest capture in `tests/live/resources.py`.
- [ ] T073 [US2] Implement the exact issue title/description, one `issues.assign(IssueAssignmentRequest(issue_id=..., agent_id=...))` call, 1-second run polling, post-assignment run selection per `contracts/agent-runtime-live-helpers.md`, 120-second deadline, and active-run cancellation in `tests/live/resources.py`.
- [ ] T074 [US2] Implement completed-status, routing identity, exact target/control bytes, filesystem allowlist, and oracle assertions in `tests/live/resources.py`.
- [ ] T075 [US2] Implement the fixed cleanup sequence and postcondition audit for run, resource, agent, project, daemon, runtime, workspace, temp paths, and Docker objects in `tests/live/resources.py`.
- [ ] T076 [US2] Compose the backend, daemon, SDK client, run context, diagnostics, and sandbox workflow fixtures without domain branching in `tests/live/conftest.py`.
- [ ] T077 [US2] Create exactly one `live_smoke` test named `test_agent_executes_issue_in_local_directory` in `tests/live/test_agent_sandbox.py`.
- [ ] T078 [US2] Create exactly four `live_extended` cases with IDs `agent-error`, `agent-timeout`, `wrong-edit`, and `cleanup-failure`; each MUST pass by observing expected failure behavior per `contracts/agent-sandbox-workflow.md` extended outcomes table.
- [ ] T079 [US2] Add `--repeat 20`, exact pytest argument forwarding, per-run prefix isolation, and final leftover aggregation to `scripts/run_live_tests.py`.
- [ ] T080 [US2] Document deterministic sandbox prerequisites, one-run command, repeat command, negative command, deadlines, and artifact locations in `tests/live/README.md`.
- [ ] T081 [US2] Run the project-resource, issue-project, and fake OpenCode unit/component commands from `specs/005-test-suite-agent-sandbox/quickstart.md` and save results under `.artifacts/validation/us2-offline/`.
- [ ] T082 [US2] Run the live smoke once, then 20 repeats, then all four negative variants; save sanitized artifacts under `.artifacts/validation/us2-live/` and require zero managed leftovers.

## Phase 8: PR-07 CI, package, and mutation (T083–T093)

**Goal:** One canonical quality job enforces coverage and behavioral counts, compatibility runs only the boundary subset, package validation uses six paths, and mutation testing remains a targeted non-blocking diagnostic.

**Independent test:** Quality, all four compatibility cells, and all six package install paths pass; `scripts/check_test_baseline.py --stage PR-07` passes; mutation output proves no live/backend/Docker execution.

- [ ] T083 [US4] Add `pytest-xdist>=3,<4` to the test dependency group and `mutmut>=3,<4` to a separate mutation dependency group in `pyproject.toml`.
- [ ] T084 [US4] Configure mutmut exactly as defined in `specs/005-test-suite-agent-sandbox/contracts/mutation-scope.md` in `pyproject.toml`.
- [ ] T085 [US4] Refactor `.github/workflows/ci.yml` so `quality` runs Ubuntu/Python 3.12 with xdist for `not live and not serial`, a serial coverage-append pass, coverage XML/JSON artifacts, zonal checks, baseline checks, and live-smoke job timeout budget of 300 seconds.
- [ ] T086 [US4] Add the Ubuntu/macOS by Python 3.12/3.13 compatibility matrix running only `-m compat` and create/mark compat tests per `specs/005-test-suite-agent-sandbox/contracts/compat-tests.md` in `.github/workflows/ci.yml`.
- [ ] T087 [US4] Refactor `.github/workflows/package-test.yml` to build one wheel, run four pip-install matrix cells, and run exactly one `uv pip install` and one `uv add` path on Ubuntu/Python 3.12.
- [ ] T088 [US4] Create weekly Tuesday 03:00 UTC plus manual `.github/workflows/mutation.yml` using only the mutation dependency group and uploading complete textual `mutmut results`.
- [ ] T089 [P] [US4] Add contract checks for quality selection, compatibility matrix, live exclusion, package path count, mutation non-required status, and mutation source/test scope in `tests/contract/test_ci_profiles.py`.
- [ ] T090 [US4] Wire `scripts/check_coverage.py` and `scripts/check_test_baseline.py --stage PR-07` into `.github/workflows/ci.yml` without importing or invoking `tests/_manifest_coverage.py` as a code-coverage gate.
- [ ] T091 [US4] Run `scripts/check_test_baseline.py --baseline tests/quality-baseline.json --mode compare --stage PR-07` and save passing output in `.artifacts/baseline/pr-07.txt`.
- [ ] T092 [US4] Run one complete targeted mutation audit and save `mutmut results` to `.artifacts/mutation/results.txt`; do not create or enforce a mutation-score baseline.
- [ ] T093 [US4] Execute all six package install paths and save the job summaries under `.artifacts/validation/package/`.

## Phase 9: PR-08 real OpenCode canary (T094–T104)

**Goal:** A single scheduled/manual, non-required real-provider canary reuses the deterministic workflow structure, enforces environment and cost limits, and always performs external cleanup.

**Independent test:** With no canary environment, the test is skipped before backend startup and lists every missing variable; with complete environment, one attempt finishes passed or failed within 15 minutes, reports usage at or below USD 0.10, publishes sanitized diagnostics, and leaves no managed resources.

- [ ] T094 [P] [US3] Add strict parsing and validation for `MULTICA_CANARY_OPENCODE_PATH`, `MULTICA_CANARY_MODEL`, `MULTICA_CANARY_SECRET_NAMES`, and every named secret to `tests/live/environment.py`.
- [ ] T095 [US3] Add unit tests proving complete missing-variable reporting, empty secret rejection, comma trimming, duplicate secret-name normalization, and no infrastructure startup on invalid configuration in `tests/unit/test_canary_environment.py`.
- [ ] T096 [US3] Extend the shared sandbox orchestration in `tests/live/resources.py` to accept the validated real executable path/model, omit fake-action parsing dependency, use canary issue template from `contracts/opencode-canary-workflow.md`, enforce one assignment attempt, collect `issues.usage()`, and fail when `cost_usd` is missing or above USD 0.10.
- [ ] T097 [US3] Create exactly one `live_opencode_canary` test named `test_real_opencode_executes_issue_in_local_directory` in `tests/live/extended/test_opencode_canary.py`.
- [ ] T098 [P] [US3] Create `scripts/cleanup_live_resources.py` to remove only processes and Docker containers, networks, and volumes matching the exact run prefix and to emit a machine-readable cleanup audit.
- [ ] T099 [US3] Create `.github/workflows/live-opencode-canary.yml` with Sunday 03:00 UTC plus manual triggers, 15-minute timeout, one model, one attempt, sanitized artifacts, and `if: always()` external cleanup.
- [ ] T100 [P] [US3] Add `scripts/cleanup_live_resources.py` as an `if: always()` final step with audit upload in the live-smoke job in `.github/workflows/ci.yml`.
- [ ] T101 [P] [US3] Add `scripts/cleanup_live_resources.py` as an `if: always()` final step with audit upload in `.github/workflows/live-extended.yml`.
- [ ] T102 [US3] Add secret redaction and diagnostic artifact scanning tests for provider keys, configured canary secrets, JWTs, tokens, and database passwords in `tests/unit/test_live_diagnostics.py`.
- [ ] T103 [US3] Document required environment, skip behavior, one-attempt policy, 15-minute timeout, USD 0.10 ceiling, artifact contents, and non-required branch-check policy in `tests/live/README.md`.
- [ ] T104 [US3] Run the canary test once with an empty environment to verify pre-infrastructure skip, then run one configured manual canary when credentials are available and save the workflow result under `.artifacts/validation/canary/`.

## Phase 10: Polish and cross-cutting completion

- [ ] T105 Run `uv run ruff check .` and resolve all findings in the files changed by Spec 005.
- [ ] T106 Run `uv run mypy src tests` and resolve all typing findings in `src/multica_py/`, `tests/`, and `scripts/` changed by Spec 005.
- [ ] T107 Run the two-pass offline quality commands from `specs/005-test-suite-agent-sandbox/quickstart.md` and preserve final `coverage.xml` and `coverage.json` under `.artifacts/final/`.
- [ ] T108 Run `uv build`, install the produced wheel in a clean environment, and save package smoke output under `.artifacts/final/package-smoke.txt`.
- [ ] T109 Run final deterministic live smoke, 20-repeat stability, and extended negative validation and save the cleanup summaries under `.artifacts/final/live/`.
- [ ] T110 Run `scripts/check_test_baseline.py --baseline tests/quality-baseline.json --mode compare --stage final` and save the passing output in `.artifacts/baseline/final.txt`.
- [ ] T111 Verify `git diff --check`, confirm `tests/quality-baseline.json` is byte-identical to PR-01, confirm no `tests/integration/` path or forbidden dependency remains, update CI comments that referenced legacy SC-003 live timing to SC-009, and record completion evidence in the final PR description.

## Dependencies

1. T001–T003 (PR-01 preparation) MUST complete before any PR-01 commit.
2. T004–T011 (PR-01 baseline capture) blocks every user story because all later work reads the immutable baseline and pinned live target.
3. US1 blocks US2, US4, and US3 because it establishes the final test paths, markers, resource case registry, and seven-module live support layout.
4. PR-04 (T044–T055) MUST merge before PR-05 (T056–T061) starts; `[P]` tasks within one PR may run in parallel only before that PR merges.
5. PR-05 MUST merge before PR-06 (T062–T082) starts.
6. US4 follows US2 because the locked plan assigns CI/package/mutation changes to PR-07 after the deterministic live workflow exists.
7. US3 follows US2 and US4 because it reuses the sandbox workflow and adds final cleanup to the already-refactored workflows.
8. Phase 10 starts only after US1, US2, US4, and US3 are complete.

## Parallel execution examples

### US1

- T017 and T018 can run in parallel because they delete independent low-signal tests.
- T025 and T026 can run in parallel after T023 because workflow/script references and documentation references are independent.
- T030, T031, T032, and T033 can run in parallel after T028-T029 because each owns one behavior module.
- T037, T038, and T039 can run in parallel after T035-T036 because each owns a separate live support module.

### US2

- T044-T055 (PR-04 SDK branch) and T056-T061 (PR-05 fake OpenCode branch) are sequential PRs; do not start PR-05 until PR-04 merges.
- T063, T064, T069, and T070 can run in parallel after T062 because they touch independent support responsibilities.
- T077 and T078 must wait for T071-T076 but can then be implemented in parallel in separate files.

### US4 and US3

- T089 can run in parallel with T085-T088 after the intended workflow contracts are fixed.
- T094 and T098 can run in parallel because canary configuration and external cleanup are independent.
- T100 and T101 can run in parallel after T098 because they modify separate workflow files.

## Suggested MVP scope

The MVP is PR-01 through PR-06 (T001–T082): baseline tooling, offline signal, typed project-resource SDK, deterministic OpenCode executable, and merge-blocking live agent sandbox workflow.

## Implementation strategy

1. Complete and merge one PR at a time using the fixed PR-01 through PR-08 boundaries.
2. Run the phase exit gate before requesting review.
3. Never combine cleanup refactoring with an unverified behavior change in the same task.
4. Register each live cleanup action immediately after its side effect, but execute cleanup only in the fixed contract order.
5. Preserve literal expected data in tests; never generate expected argv or decoded fixtures with the production code under test.
6. Keep real-provider logic out of required checks and keep deterministic fake-agent logic out of production SDK modules.
