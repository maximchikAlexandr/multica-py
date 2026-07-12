# Tasks: Complete Python SDK for the Multica CLI

**Feature:** `001-full-cli-sdk`  
**Pinned upstream:** `multica-ai/multica@48b8dbf43971e5ea974bf827220cd212a1240c72`  
**Package:** `multica-py` / import package `multica_py`  
**Primary install/use:** `uv tool install multica-py`, `uvx multica-py`

## Phase 1: Setup

- [X] T001 Initialize the `src/` package layout, test directories, scripts directory, and GitHub workflow directories in `pyproject.toml`, `src/multica_py/__init__.py`, `tests/__init__.py`, `scripts/.gitkeep`, and `.github/workflows/.gitkeep`
- [X] T002 Configure Hatchling build metadata, Python 3.12/3.13 support, `msgspec` runtime dependency, `multica-py` console script, wheel package inclusion, and `py.typed` packaging in `pyproject.toml`
- [X] T003 Configure uv dependency groups for test, lint, type-check, build, and release tooling in `pyproject.toml` and generate `uv.lock`
- [X] T004 Port the supplied Ruff policy, remove Odoo-only sections/rules, disable `COM812`, and set project-specific file exclusions in `ruff.toml`
- [X] T005 Configure strict mypy with no `Any`, strict optional handling, namespace package settings, and `msgspec` compatibility in `pyproject.toml`
- [X] T006 Add baseline pytest settings, segmented coverage thresholds for transport/resources/models/error mapping, deterministic temporary-directory handling, and warning escalation in `pyproject.toml`
- [X] T007 Add package metadata, MIT license declaration, README links, repository URLs, classifiers, and PyPI project fields in `pyproject.toml` and `LICENSE`
- [X] T008 Add a contributor command reference using only uv commands in `README.md`

## Phase 2: Foundational prerequisites

- [X] T009 Create frozen shared scalar and JSON type aliases without `Any` in `src/multica_py/types.py`
- [X] T010 Create exact enums for issue status, project status, output mode, and all source-confirmed closed value sets in `src/multica_py/enums.py`
- [X] T011 Create the unset sentinel and typed patch-field aliases based on `msgspec.UNSET` in `src/multica_py/sentinels.py`
- [X] T012 Create the immutable `ClientConfig`, compatibility policy, timeout, environment, and executable configuration models in `src/multica_py/config.py`
- [X] T013 Create the exception hierarchy for executable, timeout, cancellation, output shape, compatibility, and command failures in `src/multica_py/exceptions.py`
- [X] T014 Create redaction primitives for token flags, environment secrets, stdin secrets, and exception rendering in `src/multica_py/_internal/redaction.py`
- [X] T015 Create generic command, raw result, text result, and decoder protocol types without `Any` in `src/multica_py/_internal/specs.py`
- [X] T016 Implement exact global-argument construction for executable, server URL, workspace, profile, debug, and output flags in `src/multica_py/_internal/argv.py`
- [X] T017 Implement JSON, text, empty-output, and line-stream decoders using `msgspec` in `src/multica_py/_internal/decoders.py`
- [X] T018 Implement synchronous finite-command execution without shell invocation in `src/multica_py/_internal/transport.py`
- [X] T019 Implement POSIX process-group creation, timeout termination, cancellation termination, and escalation from terminate to kill in `src/multica_py/_internal/processes.py`
- [X] T020 Implement `ManagedProcess` with polling, waiting, termination, killing, stdout/stderr line iterators, and context-manager cleanup in `src/multica_py/process.py`
- [X] T021 Implement executable discovery, permission checks, and lazy first-call validation in `src/multica_py/_internal/executable.py`
- [X] T022 Implement CLI version detection and pinned-baseline compatibility comparison in `src/multica_py/compatibility.py`
- [X] T023 Add transport unit tests covering argv ordering, environment isolation, cwd, stdin, stdout/stderr capture, exit status, and secret redaction in `tests/unit/test_transport.py`
- [X] T024 Add process lifecycle tests proving timeout and cancellation terminate the full spawned process tree in `tests/integration/test_process_lifecycle.py`
- [X] T025 Add decoder tests for additive unknown fields, missing required fields, malformed JSON, empty output, and UTF-8 errors in `tests/unit/test_decoders.py`
- [X] T026 Build a deterministic fake `multica` executable that records argv/stdin/environment and emits fixture-selected outputs in `tests/fixtures/fake_multica.py`
- [X] T027 Create source-provenance metadata models and fixture headers containing upstream SHA, Go file, function, and JSON branch in `src/multica_py/provenance.py` and `tests/fixtures/provenance/README.md`
- [X] T028 Create a machine-readable pinned CLI manifest containing every root command, alias, subcommand, flag, default, and output mode in `src/multica_py/_generated/cli_manifest.json`
- [X] T029 Implement a manifest loader and coverage validator that fails on missing SDK mappings or duplicate command ownership in `src/multica_py/_internal/manifest.py`
- [X] T030 Add manifest contract tests against the pinned snapshot in `tests/contract/test_cli_manifest.py`

## Phase 3: US-001 — Typed Python client and core resource API

**Independent test criterion:** A Python application can construct `MulticaClient`, invoke representative read/write commands through resources, receive frozen typed models, and receive typed exceptions without constructing subprocess commands.

- [X] T031 [US1] Implement `MulticaClient` construction, immutable configuration, resource caching, transport injection, and context-manager cleanup in `src/multica_py/client.py`
- [X] T032 [P] [US1] Create the base resource class and nested-resource construction helpers in `src/multica_py/resources/_base.py`
- [X] T033 [P] [US1] Create shared action, page, identifier, timestamp, and diagnostic models in `src/multica_py/models/common.py`
- [X] T034 [P] [US1] Create exact issue, assignee, linked pull request, child-stage, create/update/filter/reorder/assignment models from pinned Go JSON structs in `src/multica_py/models/issues.py`
- [X] T035 [P] [US1] Create exact comment, thread, subscriber, metadata, task run, run message, and usage models from pinned Go JSON structs in `src/multica_py/models/issue_activity.py`
- [X] T036 [US1] Implement `IssueResource.list`, `get`, `pull_requests`, `children`, `create`, `update`, `assign`, `set_status`, `reorder`, and `search` with exact pinned flags in `src/multica_py/resources/issues.py`
- [X] T037 [US1] Implement mutually exclusive issue description variants for inline, file, stdin, and omitted input in `src/multica_py/models/issues.py`
- [X] T038 [US1] Implement `IssueCommentResource.list`, `add`, `reply`, `delete`, `resolve`, and `unresolve`, including flat/thread/recent/cursor/since incremental polling request variants in `src/multica_py/resources/issue_comments.py`
- [X] T039 [US1] Implement `IssueMetadataResource.list`, `get`, `set`, and `delete`, including explicit and inferred primitive value typing in `src/multica_py/resources/issue_metadata.py`
- [X] T040 [US1] Implement `IssueSubscriberResource.list`, `add`, and `remove` with caller and explicit-user variants in `src/multica_py/resources/issue_subscribers.py`
- [X] T041 [US1] Implement issue label list/add/remove operations with exact source names and repeated-flag order in `src/multica_py/resources/issue_labels.py`
- [X] T042 [US1] Implement `IssueResource.runs`, `run_messages`, `usage`, `rerun`, and `cancel_task` in `src/multica_py/resources/issues.py`
- [X] T043 [US1] Export only stable client, config, exceptions, enums, sentinels, and public models from `src/multica_py/__init__.py`
- [X] T044 [US1] Add issue command-construction tests for every command, alias-equivalent path, flag default, repeated flag, and mutually exclusive request variant in `tests/unit/resources/test_issues.py`
- [X] T045 [US1] Add exact issue/comment/metadata/run JSON fixtures with provenance headers in `tests/fixtures/json/issues/`
- [X] T046 [US1] Add typed decoder contract tests for all issue-family fixtures in `tests/contract/test_issue_models.py`
- [X] T047 [US1] Add fake-binary integration tests covering issue create, list, status, assignment, comments, metadata, runs, and cancellation in `tests/integration/test_issue_workflows.py`
- [X] T048 [US1] Add public API typing tests that run mypy against valid and intentionally invalid consumer snippets in `tests/typing/test_client_api.py` and `tests/typing/cases/`

## Phase 4: US-002 — Complete pinned Multica CLI coverage

**Independent test criterion:** Every command in the pinned manifest maps to exactly one typed SDK method or one explicit process-oriented method, and the coverage audit passes with no undocumented omissions.

- [X] T049 [P] [US2] Create workspace and workspace-member models from pinned source in `src/multica_py/models/workspaces.py`
- [X] T050 [P] [US2] Create project and project mutation models from pinned source in `src/multica_py/models/projects.py`
- [X] T051 [P] [US2] Create label models from pinned source in `src/multica_py/models/labels.py`
- [X] T052 [P] [US2] Create agent, agent task, avatar, and agent-skill models from pinned source in `src/multica_py/models/agents.py`
- [X] T053 [P] [US2] Create skill and skill-file models from pinned source in `src/multica_py/models/skills.py`
- [X] T054 [P] [US2] Create autopilot, run, schedule, and trigger models from pinned source in `src/multica_py/models/autopilots.py`
- [X] T055 [P] [US2] Create repository, runtime, attachment, squad, user, auth, daemon, setup, config, update, and version models from pinned source in `src/multica_py/models/system.py`
- [X] T056 [US2] Implement workspace list/switch/get/members/watch/unwatch operations in `src/multica_py/resources/workspaces.py`
- [X] T057 [US2] Implement project list/get/create/update/delete/set_status operations in `src/multica_py/resources/projects.py`
- [X] T058 [US2] Implement label list/get/create/update/delete operations in `src/multica_py/resources/labels.py`
- [X] T059 [US2] Implement agent list/get/create/update/archive/restore/tasks/upload_avatar operations in `src/multica_py/resources/agents.py`
- [X] T060 [US2] Implement agent skill list/set operations in `src/multica_py/resources/agent_skills.py`
- [X] T061 [US2] Implement skill list/get/create/update/delete/import_from_url operations in `src/multica_py/resources/skills.py`
- [X] T062 [US2] Implement skill file list/upsert/delete operations in `src/multica_py/resources/skill_files.py`
- [X] T063 [US2] Implement every pinned autopilot CRUD, manual-run, run-history, and trigger operation in `src/multica_py/resources/autopilots.py` and `src/multica_py/resources/autopilot_triggers.py`
- [X] T064 [US2] Implement every pinned repository operation, including checkout semantics and file-system result handling, in `src/multica_py/resources/repositories.py`
- [X] T065 [US2] Implement every pinned runtime operation in `src/multica_py/resources/runtimes.py`
- [X] T066 [US2] Implement every pinned attachment upload/download/list operation, including binary/file output handling, in `src/multica_py/resources/attachments.py`
- [X] T067 [US2] Implement squad and user commands exactly as registered in the pinned root command tree in `src/multica_py/resources/squads.py` and `src/multica_py/resources/users.py`
- [X] T068 [US2] Implement configuration show/get/set operations with exact key/value handling in `src/multica_py/resources/configuration.py`
- [X] T069 [US2] Implement auth status/logout and token-based login as finite typed operations in `src/multica_py/resources/auth.py`
- [X] T070 [US2] Implement browser-based login and interactive setup variants as `ManagedProcess` operations in `src/multica_py/resources/auth.py` and `src/multica_py/resources/setup.py`
- [X] T071 [US2] Implement daemon stop/restart/status/disk_usage as finite operations and start foreground/logs follow as process-oriented operations in `src/multica_py/resources/daemon.py`
- [X] T072 [US2] Implement maintenance version as a typed finite operation and update as an explicit process-oriented operation in `src/multica_py/resources/maintenance.py`
- [X] T073 [US2] Register every completed resource on `MulticaClient` with stable attribute names from the public contract in `src/multica_py/client.py`
- [X] T074 [US2] Add one command-construction test module per resource family under `tests/unit/resources/`
- [X] T075 [US2] Add exact JSON/text/binary fixture sets with source provenance for every resource family under `tests/fixtures/json/`, `tests/fixtures/text/`, and `tests/fixtures/binary/`
- [X] T076 [US2] Add one model decoder contract test module per resource family under `tests/contract/models/`
- [X] T077 [US2] Add fake-binary integration tests for all finite command families under `tests/integration/resources/`
- [X] T078 [US2] Add managed-process integration tests for browser login, setup, daemon foreground/log follow, and update under `tests/integration/test_streaming_commands.py`
- [X] T079 [US2] Complete every row in `contracts/cli-coverage.md` with exact method signature, command flags, output mode, command source function, and model source function in `specs/001-full-cli-sdk/contracts/cli-coverage.md`
- [X] T080 [US2] Complete every model entry with exact Go struct, JSON tags, optionality, and fixture path in `specs/001-full-cli-sdk/contracts/model-source-map.md`
- [X] T081 [US2] Add a coverage audit test proving every manifest command and alias has one SDK mapping and every public SDK operation points to a manifest entry in `tests/contract/test_full_cli_coverage.py`

## Phase 5: US-003 — Safe use in FastAPI, Temporal, and automation services

**Independent test criterion:** Multiple configured clients can run concurrently without shared-state interference; subprocesses are bounded and cancellable; errors preserve diagnostics but redact secrets.

- [X] T082 [P] [US3] Add explicit immutable client cloning helpers for profile, workspace, timeout, cwd, and environment overrides in `src/multica_py/client.py`
- [X] T083 [P] [US3] Add a configurable bounded process semaphore owned by each client instance in `src/multica_py/_internal/concurrency.py`
- [X] T084 [US3] Integrate per-client concurrency limits into finite and managed process execution without global locks in `src/multica_py/_internal/transport.py` and `src/multica_py/process.py`
- [X] T085 [US3] Add tests proving two clients with different profiles, workspaces, environments, and concurrency limits never leak state in `tests/integration/test_client_isolation.py`
- [X] T086 [US3] Add tests proving command timeout, caller cancellation, and context-manager exit release process slots and child processes in `tests/integration/test_service_safety.py`
- [X] T087 [US3] Add a documented FastAPI usage pattern using sync endpoints or thread offloading and a Temporal Activity usage pattern in `docs/service-usage.md`
- [X] T088 [US3] Add a non-network example service adapter with explicit timeout and concurrency configuration in `examples/fastapi_adapter.py`
- [X] T089 [US3] Add a non-network Temporal Activity example showing idempotency ownership remains in the caller in `examples/temporal_activity.py`
- [X] T090 [US3] Add compatibility-policy tests for exact baseline, allowed newer version, older version rejection, and unparsable version output in `tests/unit/test_compatibility.py`

## Phase 6: US-004 — PyPI package and uv tool experience

**Independent test criterion:** A locally built wheel installs through `uv tool install`, runs through `uvx`, imports through `uv add`/pip-compatible environments, includes `py.typed`, and exposes only the specified utility commands.

- [X] T091 [P] [US4] Implement the `multica-py doctor` command to check Python version, executable discovery, executable version, compatibility, and configuration in `src/multica_py/cli/doctor.py`
- [X] T092 [P] [US4] Implement the `multica-py version` command for package and detected upstream CLI versions in `src/multica_py/cli/version.py`
- [X] T093 [P] [US4] Implement the `multica-py coverage` command using the pinned manifest and SDK mapping audit in `src/multica_py/cli/coverage.py`
- [X] T094 [P] [US4] Implement `multica-py exec -- <args>` as an explicitly untyped diagnostic passthrough returning the upstream exit code in `src/multica_py/cli/exec.py`
- [X] T095 [US4] Implement argument parsing and command dispatch without duplicating Multica resource semantics in `src/multica_py/cli/main.py`
- [X] T096 [US4] Add CLI tests for help, exit codes, redaction, missing executable, doctor, version, coverage, and passthrough in `tests/unit/test_console_cli.py`
- [X] T097 [US4] Add `src/multica_py/py.typed` and verify it is present in wheel and sdist in `tests/packaging/test_artifact_contents.py`
- [X] T098 [US4] Add local wheel installation tests using `uv tool install`, `uvx --from`, `uv add`, `uv pip install`, and standard pip in `tests/packaging/test_installation.py`
- [X] T099 [US4] Add build validation for wheel metadata, source distribution completeness, importability, and console entry point in `tests/packaging/test_build.py`
- [X] T100 [US4] Add the CI quality workflow triggered on pull requests and the default branch, running Ruff format/check, strict mypy, pytest with segmented coverage reporting for transport/resources/models/error mapping, coverage audit, and build on Python 3.12 and 3.13 in `.github/workflows/ci.yml`
- [X] T101 [US4] Add a dedicated packaging workflow that builds once and tests the artifact through uv tool, uvx, uv add, uv pip, and pip in `.github/workflows/package-test.yml`
- [X] T102 [US4] Add PyPI Trusted Publishing release workflow with environment protection, tag validation, artifact reuse, and no long-lived token in `.github/workflows/release.yml`
- [X] T103 [US4] Document uv tool installation, uvx execution, library installation, pip compatibility, upstream CLI prerequisite, and supported platforms in `README.md`
- [X] T104 [US4] Add release, versioning, and pinned-upstream compatibility policy in `docs/releasing.md` and `docs/compatibility.md`

## Phase 7: Polish and cross-cutting verification

- [X] T105 [P] Add API reference documentation for client configuration, resources, models, exceptions, and process handles in `docs/api.md`
- [X] T106 [P] Add command-family documentation generated from the pinned manifest and verified against the coverage matrix in `docs/cli-coverage.md`
- [X] T107 Add docstring coverage for every public symbol and ensure each resource method names the equivalent Multica command and pinned source in `src/multica_py/`
- [X] T108 Add runtime tests that reject accidental public `Any`, `object`, mutable model fields, list returns, and dataclass/Pydantic dependencies in `tests/contract/test_public_invariants.py`
- [X] T109 Add a scheduled upstream drift workflow that fetches Multica, compares the current command tree to the pinned manifest, and opens a report artifact without modifying code in `.github/workflows/upstream-drift.yml` and `scripts/check_upstream_drift.py`
- [X] T110 Add an offline source-audit script that checks all coverage rows reference the pinned SHA and resolvable source paths in `scripts/audit_source_links.py`
- [X] T111 Run the complete quickstart validation matrix and record final verified commands and expected results in `specs/001-full-cli-sdk/quickstart.md`
- [X] T112 Update the decision log with all final implementation decisions and mark the feature ready for implementation in `.speckit-chat/decision-log.md` and `.speckit-chat/state.json`

## Dependencies

- Phase 1 must complete before all later phases.
- T009–T030 are foundational and block every user-story phase.
- US-001 is the MVP and must complete before broad CLI-family work begins.
- US-002 depends on the client, transport, model conventions, and fixture system from US-001.
- US-003 depends on stable finite and managed-process execution from US-001/US-002.
- US-004 may begin after T031 and T029, but final packaging validation depends on all public resources being registered.
- Phase 7 depends on completion of all selected user stories.

## Parallel execution examples

- T032–T035 can run in parallel after T009–T017.
- T049–T055 can run in parallel because they create independent model modules.
- Resource implementations T056–T072 can be split by resource family after their matching model task completes.
- T091–T094 can run in parallel after client and manifest APIs stabilize.
- Documentation tasks T105–T106 can run in parallel after the public API and manifest are final.

## MVP scope

The recommended MVP is Phases 1–3: installable project foundation, safe subprocess transport, pinned manifest, `MulticaClient`, and complete issue-family support. This MVP is independently useful for the planned FastAPI/Temporal orchestration service while preserving the architecture required to add the remaining CLI families without redesign.

## Implementation strategy

1. Never implement a command from prose documentation alone; inspect its pinned Cobra declaration, `run...` function, validation logic, JSON branch, and referenced `server/internal/cli` structs.
2. Add source provenance and fixtures before marking a model or command complete.
3. Implement one resource family vertically: models, argv builder, decoder, unit tests, fixture contract tests, fake-binary integration tests, then coverage-row completion.
4. Treat interactive and streaming commands as `ManagedProcess`; do not force them into finite JSON methods.
5. Keep subprocess idempotency outside the SDK. The SDK guarantees exact invocation and bounded lifecycle; FastAPI/Temporal callers own workflow-level deduplication.
