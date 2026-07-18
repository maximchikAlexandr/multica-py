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

## Commands

Default offline tests:

```bash
uv run pytest
```

Explicit offline selector:

```bash
uv run pytest -m "not live"
```

Blocking live smoke:

```bash
export MULTICA_LIVE_UPSTREAM_DIR=/absolute/path/to/multica
export MULTICA_LIVE_CLI=/absolute/path/to/multica/server/bin/multica
uv run pytest -m live_smoke tests/live -v
```

Using the helper script:

```bash
export MULTICA_LIVE_UPSTREAM_DIR=/absolute/path/to/multica
uv run python scripts/run_live_tests.py --resolve-cli
```

Extended suite:

```bash
uv run pytest -m "live_smoke or live_extended" tests/live -v
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

## FR / SC traceability (MVP smoke)

| ID | Requirement | Live tests / markers |
|---|---|---|
| FR-001 | Separate live suite | `tests/live/*` with `@pytest.mark.live` |
| FR-002 | Real Multica CLI | session fixtures in `conftest.py` |
| FR-003 | Real backend with session storage | `test_bootstrap.py` (`live`, `live_smoke`) |
| FR-004 | Non-interactive bootstrap | `test_bootstrap.py` |
| FR-005 | Readiness before tests | `test_bootstrap.py::test_readyz_reports_backend_ready`, `test_bootstrap.py::test_not_ready_backend_raises_live_setup_error_with_diagnostics` |
| FR-006 | Isolated profiles/tokens/workspaces | `test_bootstrap.py`, `test_workspace_isolation.py` |
| FR-007 | Pinned CLI/backend target | `test_bootstrap.py::test_readyz_reports_backend_ready`, `scripts/resolve_multica_target.py` |
| FR-008 | `workspaces.list()` smoke | `test_bootstrap.py::test_workspaces_list_includes_primary_bootstrap_workspace` |
| FR-009 | Labels CRUD | `test_labels.py` (`live_smoke`) |
| FR-010 | Issue workflow | `test_issue_workflow.py` (`live_smoke`) |
| FR-011 | Unicode/special strings | `test_labels.py`, `test_issue_workflow.py` |
| FR-012 | Presence matrix | `test_projects.py`, `test_issue_workflow.py` (`C-EMPTY`) |
| FR-013 | Unrelated fields unchanged | `test_projects.py::test_p_set_*`, `test_p_omit_*` |
| FR-014 | Exception mapping | `test_errors.py` (`live_smoke`) |
| FR-015 | Network vs command execution errors | `test_errors.py` |
| FR-016 | No secret leakage | `test_errors.py` diagnostic bundle scan |
| FR-017 | Workspace isolation | `test_workspace_isolation.py` |
| FR-018 | No user profile mutation | `test_bootstrap.py::test_cli_profile_is_isolated_from_user_home` |
| FR-019 | Layered cleanup | `conftest.py`, `test_workspace_isolation.py::test_failed_run_*` |
| FR-020 | Cleanup on pass and fail | `conftest.py`, `test_workspace_isolation.py::test_failed_run_*` |
| FR-021 | Failure diagnostics | `conftest.py`, `test_errors.py` |
| FR-022 | Separate live invocation | `pyproject.toml` `-m "not live"`, this README |
| FR-023 | PR smoke vs extended split | markers `live_smoke` / `live_extended` |
| FR-024 | No frontend/daemon deps | smoke scope in `spec.md` |
| FR-028 | Independent oracle verification | `test_oracle_consistency.py`, oracle asserts in `test_labels.py` / `test_projects.py` |
| FR-029 | Unique run/resource naming | `settings.py`, `test_live_naming.py` (unit) |
| FR-030 | Repeatable runs | `test_workspace_isolation.py`, `--repeat` mode |
| SC-001 | End-to-end chain | `test_bootstrap.py`, `test_labels.py`, `test_issue_workflow.py` |
| SC-002 | Mutation gate | `scripts/run_live_tests.py --mutation-check` |
| SC-003 | PR smoke budgets | `.github/workflows/ci.yml` live-smoke job |
| SC-004 | Ten-run stability | `scripts/run_live_tests.py --repeat 10` |
| SC-005 | Post-run cleanup | `test_workspace_isolation.py::test_failed_run_*`, manual `docker ps` checks above |
| SC-006 | Failure localization | `test_errors.py` bundle metadata |
| SC-007 | Two-workspace isolation | `test_workspace_isolation.py` |
| SC-008 | Presence case IDs | `test_projects.py`, `test_issue_workflow.py` |
| SC-009 | Byte-identical special strings | `test_labels.py`, `test_issue_workflow.py` |
| SC-010 | No token in logs/exceptions | `test_errors.py` |

Extended-only requirements (`FR-025`–`FR-027`) map to `tests/live/extended/*` with marker
`live_extended` (post-MVP).

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
