# Contract: Reduced Verification

## Offline Operation Coverage

`tests/cases/operations.py` owns:

- frozen `OperationCase`;
- `OPERATION_CASES`;
- resource-path resolution used by its executor.

For every public operation, the table has exactly one `is_canonical=True` row.
Only the closed governed vector catalog adds `is_canonical=False` rows for a
different argv, presence, stdin, timeout, or result shape.
Each row has the stable ID prescribed by `generation.md`'s closed legacy-row
mapping.  An empty legacy `ArgvSpec.id` is not a final ID.

`tests/unit/resources/test_operations.py::test_operation`:

1. selects `run_bytes`, `run_text`, or `spawn` solely from
   `case.transport_method` and configures that mock response;
2. constructs the actual resource;
3. invokes the public method with row inputs;
4. asserts exact result shape when supplied;
5. asserts exactly one call to the exact transport method;
6. compares complete argv, stdin, and timeout.

There is no skip for complex request models. Every row must be invocable. A row
that cannot be invoked is invalid test data and fails collection/setup.

The completeness test introspects the resource attributes exposed by
`MulticaClient`, collects callable public methods declared on each resource
class, excludes only dunder/private names and overload-only stubs, builds their
dotted SDK names with the same fixed nested-resource map as the executor, and
asserts `discovered_public_methods == {case.sdk_method for case in
OPERATION_CASES if case.is_canonical}`. It also asserts 116 unique canonical
methods, 137 unique case IDs, and 21 noncanonical variants. No allowlist is
accepted.

## Distinct Offline Tests

Retain separate focused tests for:

- decoder shapes and malformed output;
- positive/negative validation constraints;
- omission/null/empty/zero/false semantics;
- reliable exit-code error mapping and generic fallback;
- secret redaction;
- client/environment isolation;
- package build/install/import;
- compatibility policy;
- managed-process public behavior.

These tests do not create a second all-operation success registry.

## Process Contract

`tests/component/test_process_contract.py` has one parametrized function and
exactly these IDs:

| ID | Fixture action | Required assertions |
| --- | --- | --- |
| `bytes-env` | child writes JSON bytes, stderr, argv, and selected env | exact bytes/stderr/argv; only allowlisted env reaches child |
| `text-stdin` | child reads stdin and emits UTF-8 text | exact stdin bytes; decoded text; exit zero |
| `timeout-tree-cleanup` | child starts descendant and ignores first termination | timeout exception; escalation occurs; parent and descendant are gone |

`tests/fixtures/child_process.py` is the sole fake process implementation.
Delete `tests/fixtures/fake_opencode.py`,
`tests/fixtures/fake_opencode_helpers.py`, and their component/unit tests.
Delete the all-operation component round-trip. Keep other focused component
tests only when they do not duplicate these three boundaries or the unit
operation executor.

## Default CI

`.github/workflows/ci.yml` runs:

1. Ruff check and format check;
2. `uv run mypy --namespace-packages --explicit-package-bases -p multica_py`;
3. `uv run mypy tests scripts tools --ignore-missing-imports
   --follow-imports=silent --check-untyped-defs`;
4. parallel `pytest -m "not live and not serial"` with coverage;
5. serial `pytest -m "serial and not live"` with coverage append;
6. `scripts/check_coverage.py`;
7. `scripts/upstream_contract.py check`;
8. the existing PR mutation command and artifact upload unchanged.

Remove five-stage loops and architecture/baseline scripts. Package, mutation,
and release workflows remain separate and their policy is unchanged.

No pytest test opens or reads `.github/workflows/*.yml`. Workflow success is an
external required-check outcome.

## Prepared Live Environment

`.github/workflows/live-smoke.yml` has only `workflow_dispatch`, runner labels
`[self-hosted, multica-live]`, read-only contents permission, and a 10-minute
timeout. It checks out this repository, installs locked development
dependencies with the runner's existing Python 3.12/`uv`, and runs:

```bash
uv run pytest -o addopts="" -q \
  -m live_smoke tests/live/test_smoke.py
```

The workflow maps repository environment values to:

- variable `MULTICA_LIVE_CLI`;
- variable `MULTICA_LIVE_EXPECTED_VERSION`;
- variable `MULTICA_LIVE_SERVER_URL`;
- variable `MULTICA_LIVE_WORKSPACE_ID`;
- variable `MULTICA_LIVE_PROFILE`.

The profile is preauthenticated on the runner. No credential is copied into
the repository, pytest environment, artifact, or command line.

## Five Live Scenarios

`tests/live/test_smoke.py` has exactly:

1. `test_release_identity`: run `<cli> version --output json`; assert the
   decoded `version` equals `MULTICA_LIVE_EXPECTED_VERSION`.
2. `test_project_crud`: create a uniquely named project, immediately register
   its delete callback, get it, update its name, get again, call `stack.close()`,
   and assert a subsequent get raises `NotFoundError`; never call delete manually.
3. `test_comment_list`: create one project and issue, add three comments, call
   `comments.list(issue.id)`, and assert the returned IDs equal the three
   created IDs.
4. `test_not_found_mapping`: get the fixed absent project ID
   `00000000-0000-0000-0000-000000000000` and assert `NotFoundError`.
5. `test_project_update_presence`: create with description `"before"`, update
   name with description omitted and assert `"before"` remains, then update
   description to `""` and assert it is empty; also assert passing `None`
   raises the SDK validation exception before a subprocess call.

Names use `multica-py-live-<uuid4 hex>`. Cleanup uses public SDK delete methods
registered on one `ExitStack`; no direct HTTP assertion is allowed.

## Deleted Live Ownership

Delete:

- `tests/live/backend/`, `tests/live/sandbox/`, `tests/live/extended/`;
- every current `tests/live/*.py` except rewritten `conftest.py`,
  `test_smoke.py`, `README.md`, and package `__init__.py`;
- `tools/live_support/`;
- `scripts/run_live_tests.py`, `resolve_multica_target.py`,
  `cleanup_live_resources.py`, `live_compatibility_report.py`, and
  `scan_live_artifacts.py`;
- `.github/workflows/live-extended.yml` and
  `.github/workflows/live-opencode-canary.yml`;
- all `tests/unit/test_live_*`, `test_canary_environment.py`, and
  `tests/contract/test_live_target_workflows.py`;
- `httpx` from `pyproject.toml` and the lockfile.

The prepared environment owner is responsible for backend lifecycle, account,
workspace, profile, and CLI installation. The upstream Multica project owns
agent-sandbox, direct API, compose, runtime, and broad backend acceptance.

## Closed public-operation discovery and provenance

`tests/cases/operations.py` owns `RESOURCE_SPECS`, an ordered literal tuple: `agents:AgentResource`, `agent_skills:AgentSkillResource`, `attachments:AttachmentResource`, `auth:AuthResource`, `autopilot_triggers:AutopilotTriggerResource`, `autopilots:AutopilotResource`, `configuration:ConfigurationResource`, `daemon:DaemonResource`, `issue_comments:IssueCommentResource`, `issue_labels:IssueLabelResource`, `issue_metadata:IssueMetadataResource`, `issue_subscribers:IssueSubscriberResource`, `issues:IssueResource`, `labels:LabelResource`, `maintenance:MaintenanceResource`, `project_resources:ProjectResourceCollection`, `projects:ProjectResource`, `repositories:RepositoryResource`, `runtimes:RuntimeResource`, `setup:SetupResource`, `skill_files:SkillFileResource`, `skills:SkillResource`, `squads:SquadResource`, `users:UserResource`, `workspaces:WorkspaceResource`. Dotted prefixes are the tuple keys except nested prefixes `agents.skills`, `issues.comments`, `issues.labels`, `issues.metadata`, `issues.subscribers`, `autopilots.triggers`, `projects.resources`, and `skills.files`.

Discovery iterates each listed class `__dict__` in declaration order; includes only public `def`/`classmethod`/`staticmethod` values; excludes names beginning `_`, properties, nested-resource attributes, aliases, and overload stubs returned by `typing.get_overloads`. It creates one `prefix.method` per included implementation. The expected set is exactly 116 names. The completeness test asserts this set equals `{case.sdk_method for case in OPERATION_CASES if case.is_canonical}`, exactly 137 rows, 116 canonical rows with unique `sdk_method`, and 21 noncanonical rows. It also asserts 30 generated governed rows (19 entrypoint-base vectors and 11 entrypoint variants) and 107 manual ungoverned rows (97 canonical public-method rows and 10 variants).  Generated rows contain 16 canonical public-method rows and 14 noncanonical rows.  No allowlist, alias, exception, or coverage deletion exists.

Each generated governed case has its exact `contract_operation_id` and no `source_ref`; each manual ungoverned case has `contract_operation_id=None` and exact `source_ref`. The loader enforces the data-model XOR rule. Thus 16 is the approved migration operation set, 19 its internal binding entrypoints, 116 the complete distinct public method set, 137 operation rows total, 21 additional noncanonical variants, and 135 preserved legacy payload rows. The four `issues.comments.list` entrypoints are internal binding variants of one canonical public `issues.comments.list` row.

## Contract test-reference rewrite

Before deleting tests, change `contracts/sdk-contract.json.test_refs` to exactly `T-OPERATION` (`tests/unit/resources/test_operations.py`, node `test_operation`) and `T-CONTRACT` (`tests/contract/test_sdk_contract.py`, node `test_sdk_contract`). Replace every current operation `T-ARGV`, `T-COMPONENT`, and `T-TRANSPORT` reference with `T-OPERATION`; replace every traceability `T-ARGV`, `T-COMPONENT`, `T-TRANSPORT`, and `T-CONTRACT` reference with `T-OPERATION` for operation authority and `T-CONTRACT` otherwise. Rewrite validator-evidence node IDs to `test_generated_constraint[<case-id>]` in `test_operations.py`. Contract validation and collect-only resolution are the gate before deleting old nodes.

## Exact live factory and scenarios

`tests/live/conftest.py` defines `prepared_client()` once. It requires all five variables, rejects missing/blank values with `pytest.UsageError`, resolves `MULTICA_LIVE_CLI`, checks executable, constructs `ClientConfig(executable=cli, server_url=url, workspace_id=workspace, profile=profile, compatibility=CompatibilityPolicy.strict)`, and creates `MulticaClient`. Locally, explicit `-m live_smoke` with missing input exits as usage error. `live-smoke.yml` maps repository variables, and missing variables make its first shell step fail before pytest.

`test_project_crud` creates the project, immediately registers `projects.delete(project.id)` as its only cleanup callback, updates and gets it, calls `stack.close()`, then asserts `projects.get(project.id)` raises `NotFoundError`; it never invokes delete elsewhere. `test_comment_list` creates a project, registers only project deletion, creates an issue with that project ID, adds three root comments, calls `comments.list(issue.id)` exactly once, and asserts the returned IDs equal the three created IDs. Cursor pagination is explicitly outside this feature. `test_project_update_presence` uses the same factory and a mocked transport subcase for the `None` pre-subprocess assertion; its live portion covers omitted and empty behavior. Every live module has exactly `pytestmark = [pytest.mark.live, pytest.mark.live_smoke, pytest.mark.serial]`; delete `live_extended` and `live_opencode_canary` markers and custom marker/path validators with the architecture gate.

## Workflow review and wheel gate

No automated YAML-content test replaces deleted workflow tests. `CI-008` is a mandatory reviewer step: open one `ci.yml` run and confirm green `lint`, `types`, `quality`, `compatibility`, and `contract-check`; manually dispatch `live-smoke.yml` and confirm green `live-smoke`; paste exactly `CI-008 ci=<URL> jobs=lint,types,quality,compatibility,contract-check:green; live=<URL> job=live-smoke:green` into the PR description. A missing URL, job, or `green` token fails review.

`tests/packaging/test_generated_runtime.py::test_wheel_exports_generated_runtime` owns wheel verification in CI workflow `package-test.yml`: run `uv build`; create `TMP=$(mktemp -d)`, `mkdir "$TMP/empty"`, and `uv venv --seed "$TMP/venv"`; run `env -u PYTHONPATH "$TMP/venv/bin/python" -m pip install --no-deps "$PWD"/dist/multica_py-*.whl`; run `cd "$TMP/empty" && env -u PYTHONPATH "$TMP/venv/bin/python" -c '<imports/assertions>'`. The assertion imports `multica_py`, `multica_py.enums`, and `multica_py._generated.approved_sdk`, asserts each resolved `__file__` is under the venv `site-packages` directory and outside the repository root, and asserts `IssueSort`, `SortDirection`, `TARGET_VERSION`, `MIN_CLI_VERSION`, `MAX_CLI_VERSION`, `OPERATION_BINDINGS`, and every `__all__` name exist. Run it with `uv run pytest -o addopts="" -q tests/packaging/test_generated_runtime.py`. This is separate from source-level `upstream_contract.py check`.
