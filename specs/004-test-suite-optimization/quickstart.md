# Quickstart & Validation: Test Suite Optimization

Runnable validation for the refactor. See [contracts/test-harness.md](./contracts/test-harness.md)
for the harness API and [data-model.md](./data-model.md) for the case shapes.

## Prerequisites

- `uv` installed; dependencies synced: `uv sync --all-groups`
- Repo root: `/Users/alexandr/local_dev/repositories/my_projects/multica-py`
- No live backend needed for US1–US5, US7 (offline default suite). US6 requires
  the live stack and `-m live` markers.

## Baseline (before changes)

```bash
uv run pytest --collect-only -q -m "not live" > /tmp/004-baseline-nodeids.txt  # SC-002 baseline
uv run pytest -m "not live" -q          # record collected count (expect ~449)
uv run ruff format --check . && uv run ruff check .
uv run mypy src                         # strict, src only (CI gate)
uv run mypy tests                       # uses the relaxed tests.* override (helper typing)
```

Keep `/tmp/004-baseline-nodeids.txt`; after the refactor the MUST-retain
guard/invariant node IDs from SC-002 must still be present and passing.

## Per-user-story validation

Each story must leave the non-live suite green (FR-017). Run after each.

### US1 — dead/duplicate removals

```bash
# after deleting tests/contract/models/, tests/typing/, tautological tests
uv run pytest -m "not live" -q
uv run mypy src            # mypy overrides for tests.typing.* / tests.contract.models.* removed
```

Expected: suite passes; the frozen-msgspec invariant still runs via
`tests/contract/test_public_invariants.py`; relocated mutually-exclusive
assertions run in `tests/unit/resources/test_issues.py`.

### US2 — unit resource table + argv guard

```bash
uv run pytest tests/unit/resources/test_operations.py -q
uv run pytest tests/unit/resources/test_operations.py::test_every_guard_eligible_operation_has_argv_case -q
```

Expected: `test_command_argv` / `test_decode` cover all migrated operations; the
guard passes (green) because every guard-eligible `sdk_method` is either in the
argv table or in `KNOWN_ARGV_GAPS`, and FAILS (naming the operation) if an
eligible op is missing from both, or if a `KNOWN_ARGV_GAPS` entry is stale. Old
per-file resource tests are deleted except `test_issues.py`.

### US3 — integration fixture + fixture-usage guard

```bash
uv run pytest tests/integration/resources/test_fake_cli_operations.py -q
uv run pytest tests/integration/resources/test_fake_cli_operations.py::test_every_json_fixture_is_referenced -q
uv run pytest tests/integration/resources/test_fake_cli_operations.py::test_every_guard_eligible_operation_has_fixture_or_gap -q
grep -rn "os.environ\[" tests/integration/resources/ || echo "no direct os.environ mutation (expected)"
```

Expected: no `os.environ[...]` mutation remains; the fixture-usage guard FAILS if
any `tests/fixtures/json/**/*.json` is unreferenced; the operation-coverage guard
FAILS if a guard-eligible operation is neither covered by a `FakeCliCase` nor in
`KNOWN_FIXTURE_GAPS` (stale allowlist entries also fail).

### US4 — maintainer contract harness

```bash
uv run pytest tests/contract/test_upstream_contract_collect.py \
             tests/contract/test_upstream_contract_check.py \
             tests/contract/test_upstream_contract_prepare_upgrade.py \
             tests/contract/test_upstream_contract_promotion.py \
             tests/contract/test_upstream_contract_quickstart.py \
             tests/contract/test_upstream_contract_apply_suggestions.py -q
git status --porcelain src/multica_py/_generated/upstream_state.json
```

Expected: tests pass; `upstream_state.json` is unchanged after the run
(`preserved_generated_state` restored it); no leftover generated candidate
contract.

### US5 — contract-diff severity table

```bash
uv run pytest tests/unit/test_upstream_contract_diff.py tests/contract/test_upstream_contract_diff.py -q
```

Expected: one parametrized `test_mutation_severity` covers the five file-mutation
rows; the `command-renamed` rename-heuristic test and other distinct-logic tests
stay separate.

### US6 — live suite (requires backend)

```bash
uv run pytest -m live_smoke tests/live -q   # compact live suite incl. FR-021 guard (guard itself needs no backend)
uv run pytest -m live_extended tests/live -q  # executes every op (test_crud + test_live_command_coverage)
```

Expected: `test_crud_round_trip` runs for labels and projects (plus the
Unicode/emoji `name_builder`); `test_error_mapping` covers the five error cases;
presence cases P-OMIT/P-EMPTY/P-SET parametrized; destructive / diagnostic-bundle
/ P-NULL-HTTP tests still separate and green. The FR-021 guard
(`test_every_guard_eligible_operation_runs_live`, `live_smoke`) FAILS if
`E - T_live - set(LIVE_EXEC_EXCEPTIONS) - KNOWN_LIVE_GAPS` is non-empty, on a stale
allowlist entry, or on an invalid reason code — `KNOWN_LIVE_GAPS` keeps it green
while gaps are closed. Under `-m live_extended`, `test_live_operation_executes`
runs every non-CRUD op and CRUD round-trips execute against the real backend
(SC-008). The whole layer is `-m live`-gated and never runs in the offline suite.

### US7 — infra consolidation

```bash
uv run pytest tests/unit/test_live_settings.py tests/unit/test_live_bootstrap.py tests/unit/test_transport.py -q
grep -rn "def _target\|def _settings" tests/unit/ || echo "local factories removed (expected)"
```

Expected: shared `make_target`/`make_settings` used; merged modules pass; all
feature-002 security-invariant tests still run.

## Final acceptance

```bash
uv run pytest -m "not live" -q          # green, no coverage loss (SC-002)
uv run ruff format --check . && uv run ruff check .
uv run mypy src && uv run mypy tests
# SC-002: MUST-retain node IDs still present
uv run pytest tests/contract/test_public_invariants.py::test_models_are_frozen \
             tests/contract/test_full_cli_coverage.py -q
# SC-008: live command-execution guard green (needs no backend)
uv run pytest -m live_smoke tests/live/test_live_command_coverage.py::test_every_guard_eligible_operation_runs_live -q
# SC-008 full execution (requires backend, scheduled/manual): CRUD + non-CRUD ops
uv run pytest -m live_extended tests/live -q
# offline suite must collect NO live nodes (FR-017 / Constitution IV)
uv run pytest -m "not live" --collect-only -q tests/live | grep -c "::" # expect 0
# line-count sanity across the 8 targeted areas trends toward ~3,410 (SC-001, secondary)
```

Success = all four guards enforced (three offline + one live-gated, SC-003),
non-live suite green (SC-002), every guard-eligible operation executed live or
allowlisted (SC-008), no new dependency (SC-006), CI gates pass (SC-007), and
adding an operation/fixture/resource is a one-row/one-descriptor change
(SC-004a/b/c/d).
