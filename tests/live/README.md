# Live integration tests

Live tests exercise the public `multica-py` SDK against a real Multica CLI and an
isolated Multica backend with PostgreSQL. They are excluded from the default pytest
run via `-m "not live"`.

## Prerequisites

- Docker Engine or Docker Desktop with working `docker compose`
- Python 3.12+
- `uv`
- Checkout of [multica-ai/multica](https://github.com/multica-ai/multica) at the
  pinned target commit, or release artifacts resolved by the target manifest
- Real `multica` executable matching `contracts/multica-live-target.toml`

Verify tools:

```bash
docker version
docker compose version
/path/to/multica version --output json
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `MULTICA_LIVE_TARGET_FILE` | optional | Path to target TOML; default `contracts/multica-live-target.toml` |
| `MULTICA_LIVE_CLI` | required unless resolver mode | Absolute path to real `multica` |
| `MULTICA_LIVE_RESOLVE_CLI` | optional | Set to `1` to resolve CLI from the pinned release |
| `MULTICA_LIVE_UPSTREAM_DIR` | required for compose mode | Checkout containing `docker-compose.selfhost.yml` |
| `MULTICA_LIVE_ARTIFACT_DIR` | optional | Diagnostics output directory |
| `MULTICA_LIVE_MODE` | optional | `smoke` or `extended`; pytest markers remain authoritative |
| `MULTICA_LIVE_EXISTING_URL` | optional | Reuse a loopback-only backend (`127.0.0.1` / `localhost`) |
| `MULTICA_LIVE_KEEP_ENV` | optional local only | Must be exactly `1`; forbidden in CI |
| `MULTICA_LIVE_READY_TIMEOUT` | optional | Seconds between `10` and `600`; default `120` |

See `.env.example` for a local template.

## Agent sandbox workflow

Deterministic agent sandbox tests live in `tests/live/test_agent_sandbox.py`.

Prerequisites:

- All standard live prerequisites above
- Executable fake OpenCode at `tests/fixtures/fake_opencode.py` (default)
- Optional `MULTICA_TEST_OPENCODE_PATH` override (must be absolute)

Environment variables for sandbox control:

| Variable | Values | Purpose |
|---|---|---|
| `MULTICA_TEST_AGENT_MODE` | `success`, `error`, `timeout`, `wrong-edit` | Fake agent behavior |
| `MULTICA_TEST_INJECT_CLEANUP_FAILURE` | `remove-resource` | Inject cleanup failure |
| `MULTICA_LIVE_RUN_ID` | 32-char hex | Repeat-run prefix isolation |

One smoke run:

```bash
export MULTICA_LIVE_UPSTREAM_DIR=/absolute/path/to/multica
export MULTICA_LIVE_CLI=/absolute/path/to/multica/server/bin/multica
export MULTICA_LIVE_ARTIFACT_DIR="$PWD/.artifacts/live"
uv run pytest -o addopts="" -v --strict-markers \
  -m live_smoke tests/live/test_agent_sandbox.py::test_agent_executes_issue_in_local_directory
```

Twenty-repeat stability (per-run prefix isolation):

```bash
uv run python scripts/run_live_tests.py --resolve-cli --repeat 20 \
  --pytest-args "-v --strict-markers"
```

Extended negative cases (120-second assignment deadline applies to timeout case):

```bash
uv run pytest -o addopts="" -v --strict-markers \
  -m live_extended tests/live/test_agent_sandbox.py -k "failure"
```

Failure bundles are written under `<artifact-dir>/<run-id>/` using the filenames in
`specs/005-test-suite-agent-sandbox/contracts/live-diagnostics-bundle.md`, including
`run-context.json`, `filesystem-before.json`, `filesystem-after.json`, `filesystem.diff`,
`daemon-status.json`, `daemon.log.tail`, and `failure.json`.

## Commands

Default offline tests:

```bash
uv run pytest
```

Explicit offline selector:

```bash
uv run pytest -m "not live"
```

Blocking live smoke (default CI selection):

```bash
export MULTICA_LIVE_UPSTREAM_DIR=/absolute/path/to/multica
export MULTICA_LIVE_CLI=/absolute/path/to/multica/server/bin/multica
uv run pytest -m live_smoke tests/live -v
```

Extended live suite (smoke plus extended markers):

```bash
uv run pytest -m "live_smoke or live_extended" tests/live -v
```

Serial live execution (required — never use xdist for live tests):

```bash
uv run pytest -m live tests/live -v
```

## Safe local debugging

To keep compose resources after a run for inspection:

```bash
MULTICA_LIVE_KEEP_ENV=1 uv run pytest -m live_smoke tests/live -x
```

This mode is rejected when `CI` is set. Remove the compose project manually after
debugging using the printed `multica-py-live-<run-id>` project name.

## Diagnostics

When `MULTICA_LIVE_ARTIFACT_DIR` is set, failure bundles are written under
`<artifact-dir>/<run-id>/` with canonical filenames:

- `target.json`
- `run.json`
- `failure.json`
- `cleanup.json`
- `compose-ps.txt`
- `backend.log`
- `postgres.log`

Secrets are redacted before write. PAT, JWT, database password, and JWT secret
values must never appear in artifacts.

## Cleanup verification

After a normal run:

```bash
docker ps -a --filter name=multica-py-live-
docker volume ls --filter name=multica-py-live-
```

Expected result: no resources from the completed run remain.

## Helper script modes

`scripts/run_live_tests.py` wraps validated live smoke execution:

```bash
export MULTICA_LIVE_UPSTREAM_DIR=/absolute/path/to/multica
uv run python scripts/run_live_tests.py --resolve-cli
uv run python scripts/run_live_tests.py --resolve-cli --mutation-check
uv run python scripts/run_live_tests.py --resolve-cli --repeat 10
```

Live support modules (US4 stage pr4 layout, B-4a/b foundation):

- `conftest.py` — public fixture surface (`live_environment`, `live_session`, `live_case`, `sandbox_session`) plus pytest hooks; no `getfixturevalue` calls.
- `session.py` — `LiveEnvironment`, `LiveSession` (one `ExitStack` for LIFO cleanup), `LiveCase`, `SandboxSession`. `register_resource` is a thin facade over `defer_cleanup`.
- `api.py` — single `LiveApiClient` (idempotent delete, redaction, typed request helpers).
- `compose.py` — `ImagePolicy`, `ComposeLifecycle`, `ReadinessResult`, `compose_argv`, `probe_readiness`. Re-exported through `backend.py` for backward compatibility.
- `backend.py` — `BootstrapApiClient`, `setup_sandbox_session`, `SandboxSession`, `DaemonLifecycle`, runtime poll helpers. ≤650 logical lines.
- `_bootstrap.py` — `bootstrap_live_environment` (composes compose + sandbox session into a `LiveEnvironment`).
- `crud_descriptors.py` — `CRUD_CASES: tuple[CrudDescriptor[object], ...]` (the only CRUD registry).
- `operations.py` — `DIRECT_EXECUTORS: Mapping[str, Callable]` built from `OPERATION_CASES` with `mode == "extended"` and `owner.startswith("direct:")`.
- `sandbox/` — three-phase agent sandbox (`prepare_sandbox` / `run_assignment` / `verify_sandbox`) plus `PreparedSandbox`, `CompletedAssignment`, `SandboxVerification`, filesystem policy, and exports. Replaces the temporary `tests/live/resources.py` module.
- `diagnostics.py` — test-only diagnostics hooks (`DiagnosticCollector`, `truncate_log`, `assert_text_excludes_secrets`, `VERIFICATION_CODE`); the failure-bundle writer is sandbox-only and lives in `tests/live/sandbox/workflow.py`.
- `environment.py` / `oracle.py` — settings, target, run-context, and HTTP oracle. Final deletion + replacement with `tools.live_support` helpers lands in US5 (`tests_python ≤ 10500`, `live_support_python ≤ 2500`).
- `tests/cases/live_policy.json` — canonical source for the 111-`OperationCase` `LivePolicy` (mode / owner / `unrunnable_reason`); `test_live_command_coverage.py` enforces closed enum and owner resolution.

Live ownership routing:

- `direct:<sdk_method>` → callable in `DIRECT_EXECUTORS`; one executor per operation, signature `(LiveSession, LiveCase) -> None`.
- `crud:<resource_id>` → descriptor in `CRUD_CASES`; one descriptor per resource, branch-free 11-step round trip in `test_crud.py`.
- `sandbox` → `sandbox_session` fixture and the `execute_agent_sandbox_workflow` runtime.
- `unrunnable` (closed enum: `destructive-irrecoverable`, `interactive-or-foreground`, `process-or-daemon-control`, `requires-external-infra`) → expected to skip with `LiveSetupError` or `pytest.skip`.

Cleanup contract (per `contracts/live-core.md`):

- `LiveSession` owns one `ExitStack`; `defer_cleanup` registers a callback that runs LIFO at session exit.
- `test_crud.py` registers cleanup immediately after each successful side effect and re-runs `delete` explicitly; the explicit delete is idempotent so the registered cleanup is safe.
- The sandbox workflow keeps its `CleanupRegistry` for fixed-order teardown (cancel-run → remove-resource → archive-agent → delete-project → stop-daemon → wait-runtime-deregister → delete-workspace → remove-temp-paths → postcondition-audit). Extracted in US5.

Extended-only requirements (`FR-025`–`FR-027`) map to `tests/live/extended/*` with marker
`live_extended` (post-MVP).

## Real OpenCode canary

The canary is a separate non-required workflow (`live-opencode-canary.yml`) that runs one
real-provider attempt with a 15-minute timeout and a USD 0.10 cost ceiling.

Required environment:

| Variable | Description |
|---|---|
| `MULTICA_CANARY_OPENCODE_PATH` | Absolute path to real OpenCode executable |
| `MULTICA_CANARY_MODEL` | Provider/model identifier passed to the daemon |
| `MULTICA_CANARY_SECRET_NAMES` | Comma-separated env var names for provider credentials |
| each named secret | Non-empty value for every name in `MULTICA_CANARY_SECRET_NAMES` |

Skip behavior: if any required variable or named secret is missing or empty, the single
canary test skips before Docker, daemon, or backend startup and reports every missing name.

Standard live prerequisites (`MULTICA_LIVE_UPSTREAM_DIR`, `MULTICA_LIVE_CLI` or resolver
mode, artifact directory) still apply when the canary runs.

One local attempt:

```bash
export MULTICA_LIVE_UPSTREAM_DIR=/absolute/path/to/multica
export MULTICA_LIVE_CLI=/absolute/path/to/multica/server/bin/multica
export MULTICA_LIVE_ARTIFACT_DIR="$PWD/.artifacts/live"
export MULTICA_CANARY_OPENCODE_PATH=/absolute/path/to/opencode
export MULTICA_CANARY_MODEL=provider/model
export MULTICA_CANARY_SECRET_NAMES=PROVIDER_API_KEY
export PROVIDER_API_KEY=your-provider-key
uv run pytest -o addopts="" -v --strict-markers \
  -m live_opencode_canary tests/live/extended/test_opencode_canary.py
```

Policy:

- exactly one assignment attempt;
- workflow timeout 15 minutes;
- fail (not skip) when `issues.usage()` is unavailable or `cost_usd` is missing;
- fail when `cost_usd > 0.10`;
- publish sanitized diagnostics and `canary-usage.json` on success;
- external cleanup runs with `if: always()` via `scripts/cleanup_live_resources.py`.

The canary workflow is not a required branch-protection check.

## Target update procedure

When bumping the pinned Multica compatibility target:

1. Choose an exact upstream release tag (never `latest`) and record `upstream_ref` + full `upstream_commit`.
2. Resolve OCI digests for `ghcr.io/multica-ai/multica-backend:<tag>` (index + `linux/amd64`) and set `backend_digest` / `backend_digest_linux_amd64` in `contracts/multica-live-target.toml`.
3. Set `cli_version_expected` to the CLI version string from that same release; `cli_source` remains `release` for blocking CI.
4. Run offline contract/coverage checks for the SDK against the new pin (existing upstream contract tooling in this repo).
5. Run live smoke against the new pin:
   ```bash
   uv run python scripts/run_live_tests.py --resolve-cli
   ```
6. Run extended suite and write a pinned-vs-previous compatibility report:
   ```bash
   MULTICA_LIVE_MODE=extended \
   uv run python scripts/run_live_tests.py --resolve-cli --mode extended
   ```
7. Open a PR that updates only the target manifest (+ any intentional SDK contract changes) together with smoke/extended evidence. Do not merge a placeholder digest.

## Cleanup and security audit notes

Audit performed against `contracts/live-test-interface.md` §8–§9 on pinned target `v0.3.35`:

| Scenario | Registry cleanup | Compose teardown | Temp HOME/profile audit | Secret scan |
|---|---|---|---|---|
| Normal pass | yes (`conftest.py` session teardown) | yes (`ComposeLifecycle.teardown`) | yes unless `MULTICA_LIVE_KEEP_ENV=1` | redaction in `diagnostics.py`; leak test in `test_errors.py` |
| Test failure | yes; primary failure preserved | yes | yes unless keep-env | bundle scan before CI upload |
| Setup failure | best-effort registry | yes when compose started | yes unless keep-env | `LiveSetupError` stage recorded |
| Forced failed run | n/a (setup abort) | yes | yes | covered by `test_failed_run_leaves_no_compose_or_profile_artifacts` |

Manual verification after a local smoke run:

```bash
docker ps -a --filter name=multica-py-live-
docker volume ls --filter name=multica-py-live-
```

Expected: no project containers or volumes; temp profile under `tests/live/.live-home/` removed
unless `MULTICA_LIVE_KEEP_ENV=1`.
