# Контракт live-test interface

**Версия:** 2  
**Назначение:** единственный SSOT для inputs, markers, readiness bounds, diagnostics и CI между harness и workflows.  
**Связанные контракты:** [bootstrap-http.md](bootstrap-http.md), [presence-and-exceptions.md](presence-and-exceptions.md)

## 1. Входные переменные окружения

| Переменная | Обязательность | Значение |
|---|---|---|
| `MULTICA_LIVE_TARGET_FILE` | optional | путь к target TOML; default `contracts/multica-live-target.toml` |
| `MULTICA_LIVE_CLI` | required unless resolver mode | абсолютный путь к реальному `multica` |
| `MULTICA_LIVE_RESOLVE_CLI` | optional | `1` включает resolver mode (`scripts/resolve_multica_target.py`); тогда `MULTICA_LIVE_CLI` optional and filled by resolver |
| `MULTICA_LIVE_UPSTREAM_DIR` | required for compose/source mode | checkout Multica с `docker-compose.selfhost.yml` |
| `MULTICA_LIVE_ARTIFACT_DIR` | optional | каталог diagnostics; default temp dir |
| `MULTICA_LIVE_MODE` | optional | `smoke` или `extended` (documentation hint only; pytest `-m` is authoritative) |
| `MULTICA_LIVE_EXISTING_URL` | optional | reuse already running private backend; **loopback only** (`127.0.0.1` / `localhost`); non-loopback → setup error |
| `MULTICA_LIVE_KEEP_ENV` | optional local debug only | only value `1` is accepted; any other non-empty value → setup error; when `1`, skip compose `down` and HOME/profile audit after session end (pass or fail) |
| `MULTICA_LIVE_READY_TIMEOUT` | optional | seconds; default `120`; allowed `10`–`600` |

### Правила

- CI detection: env `CI` is non-empty (GitHub Actions sets `CI=true`). In CI, any non-empty `MULTICA_LIVE_KEEP_ENV` → setup error. Locally only `1` is allowed.
- `MULTICA_LIVE_EXISTING_URL` always loopback-only; no unsafe override flag in v1.
- Resolver mode is enabled only when `MULTICA_LIVE_RESOLVE_CLI=1` or `scripts/run_live_tests.py --resolve-cli` is passed. CI smoke always uses resolver mode then exports absolute `MULTICA_LIVE_CLI`.
- Missing required input → setup error, never silent skip.
- Secret values are not passed through these variables except runtime-generated values inside the harness process.

## 2. Target manifest TOML

Committed blocking manifest MUST contain concrete non-placeholder values. The example below uses the chosen first pin; `backend_digest` MUST be the real ghcr digest resolved before merge (empty/`sha256:...` placeholder forbidden in committed file).

```toml
schema_version = 1
name = "supported-v0.3.35"
upstream_ref = "v0.3.35"
upstream_commit = "4416313f8f7f801df8b7f5072087da8a6502a89c"
compose_file = "docker-compose.selfhost.yml"
backend_image = "ghcr.io/multica-ai/multica-backend"
backend_tag = "v0.3.35"
backend_digest = "sha256:656dd76e866f636863a6fc034f04165227e35f427e526914ea2c9848f8f55e30"
backend_digest_linux_amd64 = "sha256:d8a50acac1eb674093b0e9de4afc656328ac6b37fc641f1fb4b256547f1ffe3b"
cli_source = "release"
cli_version_expected = "0.3.35"
verified_at = "2026-07-18"
```

`backend_digest` is the OCI index digest. CI on `ubuntu-latest` MAY pull by `backend_digest_linux_amd64` for the platform manifest; both values are concrete and committed.

### Validation contract

- `schema_version` must equal `1`;
- `upstream_ref`, `upstream_commit`, backend tag/digest и CLI expected version не пусты и не содержат placeholders (`X.Y.Z`, `sha256:...`, `latest`);
- blocking mode rejects `latest`, branch-only refs and unresolved placeholders;
- resolved CLI executable must be executable;
- actual CLI version mismatch is fatal before resource tests;
- CI smoke mode: `cli_source=release` + digest-pinned backend image;
- local quickstart may use `cli_source=local` with `MULTICA_LIVE_CLI` + compose from `MULTICA_LIVE_UPSTREAM_DIR` checked out at `upstream_commit`.

## 3. Pytest marker contract

| Marker | Meaning |
|---|---|
| `live` | requires real CLI + backend; **mandatory parent on every live test** |
| `live_smoke` | blocking compact suite; implies `live` |
| `live_extended` | scheduled/manual extended suite; implies `live` |
| `destructive` | stops backend or mutates process state |
| `serial` | must not run concurrently with other live tests in the same environment |

Rules:

- Every test under `tests/live/` MUST be marked `@pytest.mark.live` and exactly one of `live_smoke` or `live_extended` (plus optional `destructive`/`serial`).
- `pyproject.toml` MUST set `addopts` to include `-m "not live"` so bare `uv run pytest` stays offline (Constitution IV).
- mypy overrides MUST include `tests.live.*`.
- `httpx` is test-only dependency-group; MUST NOT appear in `[project] dependencies`.
- pytest-xdist / parallel workers unsupported in v1.

## 4. Pytest fixture contract

Session fixtures:

- `live_settings` — validated immutable settings;
- `compatibility_target` — resolved and verified target;
- `live_environment` — started/ready environment;
- `test_identity` — authenticated identity without exposed secrets in repr;
- `primary_workspace`, `secondary_workspace`;
- `live_client`, `secondary_live_client`;
- `api_oracle` — direct API helper;
- `resource_registry`;
- `diagnostic_collector`.

Function fixtures:

- `resource_name` — unique safe prefix based on run/test;
- `register_resource` — convenience registration;
- `assert_no_secret_leak`.

No fixture may return raw PAT as a normal string fixture. Token access is encapsulated in objects with redacted `repr`.

## 5. Exit behavior

| Condition | Result |
|---|---|
| Docker unavailable locally | explicit setup failure with prerequisite message |
| CLI missing | explicit setup failure |
| target version mismatch | explicit compatibility setup failure |
| backend not ready | setup failure + compose diagnostics |
| bootstrap rejected | setup failure + redacted HTTP status/body excerpt |
| test assertion failed | normal pytest failure + diagnostic metadata |
| cleanup failed after pass | test session failure |
| cleanup failed after test failure | preserve primary failure and report cleanup failure |

Setup failures use a dedicated exception type name in harness: `LiveSetupError` (test-only), message must name the failed stage (`target`, `compose`, `readyz`, `bootstrap`, `profile`).

## 6. Naming contract

- Compose project: `multica-py-live-<run-id>`;
- CLI profile: `live-<run-id>`;
- email: `multica-py-live+<run-id>@localhost`;
- workspace slug: `mpy-<run-id>-a|b` truncated to **48** chars with 8-char hash suffix when needed;
- resource prefix: `mpy-live-<run-id>-<test-fragment>` truncated to **64** chars with 8-char hash suffix when needed.

## 7. Readiness contract

See [bootstrap-http.md §3](bootstrap-http.md). Summary: `GET /readyz` must return status `200` and body with `status=ok` and `checks.db=ok` and `checks.migrations=ok`; default timeout 120s; poll 0.5→1.0→2.0s.

## 8. Diagnostic bundle contract (SSOT)

Artifact root:

```text
<artifact-dir>/<run-id>/
  target.json
  run.json
  failure.json
  cleanup.json
  compose-ps.txt
  backend.log
  postgres.log
  junit.xml
```

Requirements:

- atomic file writes where practical;
- UTF-8 text;
- each `*.log` truncated to **262144** bytes (256 KiB) with start/end truncation markers;
- secret scanner before artifact publication: harness function scanning exact values of PAT, JWT, verification code `888888` only when it appears as a credential field echo, JWT secret, database password; job fails on match;
- bundle creation must not raise over primary test failure; collector errors are reported separately;
- plan/docs MUST NOT invent alternate filenames (`environment.json` is forbidden; use `run.json`).

## 9. Cleanup hierarchy (mandatory, layered — not XOR)

Always, in order:

1. `ResourceRegistry` reverse-topological delete for registered resources;
2. if Compose-managed: `docker compose -p <project> down -v --remove-orphans`;
3. postcondition audit: no compose containers/volumes for project; temp HOME/profile removed unless `MULTICA_LIVE_KEEP_ENV=1` locally.

For `MULTICA_LIVE_EXISTING_URL` mode: step 1 is mandatory; step 2 is skipped; step 3 audits only temp HOME/profile and registry leftovers.

If resource cleanup fails: continue to environment destroy (when applicable), record `cleanup.json`, and apply exit behavior from §5.

## 10. CI contract

Default offline job (existing `test`):

```text
uv run pytest
# relies on addopts -m "not live" — must not start Docker
```

Blocking job (added only after US1–US5 smoke tests exist):

```text
job name: live-smoke
platform: ubuntu-latest
python: 3.12
timeout: 10 minutes
hard fail: job `timeout-minutes: 10`
SC-003 budgets (env startup ≤ 180s; tests ≤ 120s; total wall ≤ 300s): recorded in job summary; exceedance fails the job via explicit timing assert step (not warn-only)
pytest selector: -m live_smoke tests/live
artifacts: upload if: failure()
retention-days: 7
secret scan: required before upload
```

Extended job:

```text
workflow: scheduled + workflow_dispatch
pytest selector: -m "live_smoke or live_extended" tests/live
compatibility target: required input or scheduled resolver
pinned-target failure: job failure (SDK regression)
upstream-main failure: workflow conclusion success with notice annotation (compatibility signal only)
```

Third-party GitHub Actions remain pinned by full commit SHA.

## 11. Extended suite numeric pins

| Item | Value |
|---|---|
| Pagination resource | issues |
| `page_size` | `10` |
| Created objects | `12` |
| Filter pair | `status` + one attached `label` id |
| Attachment payload | exactly `1024` bytes, content `b"\x00\xff" * 512` |
| Attachment filenames | `empty.bin` (0 bytes), `file name.bin`, `файл.bin` |
| Attachments policy | required on pinned target `v0.3.35`; missing capability → fail (not skip) |
| Read-only decode smoke resources | `agents.list`, `skills.list`, `autopilots.list` |
