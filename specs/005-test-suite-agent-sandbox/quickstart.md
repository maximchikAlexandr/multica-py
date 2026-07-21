# Quickstart and Validation — Spec 005

Run commands from repository root.

Set the active feature before running speckit scripts:

```bash
export SPECIFY_FEATURE=005-test-suite-agent-sandbox
```

## 1. Prerequisites

```bash
python --version
uv --version
docker version
docker compose version
git rev-parse HEAD
```

Expected: Python 3.12 or 3.13; working uv and Docker; one full SHA.

## 2. Bootstrap baseline tooling and capture baseline (`PR-01`)

Before these commands, create the three scripts defined by `contracts/quality-baseline.md`. Do not modify production code, tests, markers or workflows first. Commit PR-01 with only the five files listed in `plan.md` PR-01 commit boundary before adding baseline script unit tests in PR-02.

```bash
export BASELINE_SHA="$(git rev-parse HEAD)"
uv sync --all-groups
mkdir -p .artifacts/baseline
uv run pytest -o addopts="" -q -m "not live" \
  --junitxml=.artifacts/baseline/offline.xml \
  --cov=multica_py --cov-branch \
  --cov-report=json:.artifacts/baseline/coverage.json
uv run python scripts/check_coverage.py \
  --coverage-json .artifacts/baseline/coverage.json
uv run python scripts/capture_test_baseline.py \
  --source-sha "$BASELINE_SHA" \
  --coverage-json .artifacts/baseline/coverage.json \
  --junit-xml .artifacts/baseline/offline.xml \
  --output tests/quality-baseline.json
uv run python scripts/check_test_baseline.py \
  --baseline tests/quality-baseline.json \
  --mode self-check
```

Resolve `v0.3.10` through the existing `scripts/resolve_multica_target.py` write path, verify `contracts/multica-live-target.toml`, then commit `PR-01`. After the commit, restore the immutable source SHA from the baseline and run the capture/self-check commands a second time:

```bash
export BASELINE_SHA="$(python -c 'import json; print(json.load(open("tests/quality-baseline.json"))["git_sha"])')"
uv run python scripts/capture_test_baseline.py \
  --source-sha "$BASELINE_SHA" \
  --coverage-json .artifacts/baseline/coverage.json \
  --junit-xml .artifacts/baseline/offline.xml \
  --output tests/quality-baseline.json
uv run python scripts/check_test_baseline.py \
  --baseline tests/quality-baseline.json \
  --mode self-check
git diff --exit-code
```

Expected: every command passes; baseline JSON records the pre-change `BASELINE_SHA`; the second capture leaves byte-identical JSON; no pre-existing failure or threshold violation is allowlisted.

## 3. Offline quality after implementation

```bash
uv run pytest -o addopts="" -v --tb=short --strict-markers \
  -m "not live and not serial" -n auto --dist loadscope \
  --cov=multica_py --cov-branch --cov-report=

uv run pytest -o addopts="" -v --tb=short --strict-markers \
  -m "serial and not live" \
  --cov=multica_py --cov-branch --cov-append \
  --cov-report=term-missing --cov-report=xml --cov-report=json

uv run python scripts/check_coverage.py --coverage-json coverage.json
uv run python scripts/check_test_baseline.py --baseline tests/quality-baseline.json --mode compare --stage final
```

Expected: all pass; reports exist; no mandatory behavioral count regression.

## 4. Verify default excludes live

```bash
uv run pytest --collect-only -q > /tmp/collected.txt
! grep -q "tests/live" /tmp/collected.txt
```

Expected: grep returns no live path.

## 5. Component project-resource contract

```bash
uv run pytest -q \
  tests/unit/test_project_resource_models.py \
  tests/component/test_project_resources.py \
  tests/component/test_issue_project_assignment.py
```

Expected: exact list/add/update/remove and issue `--project` argv tests pass.

## 6. Fake OpenCode contract

```bash
uv run pytest -q \
  tests/unit/test_fake_opencode.py \
  tests/component/test_fake_opencode_process.py
```

Expected: success and all parser/path/failure cases pass.

## 7. Deterministic live agent sandbox

```bash
export MULTICA_LIVE_UPSTREAM_DIR=/absolute/path/to/multica
export MULTICA_LIVE_CLI=/absolute/path/to/multica/server/bin/multica
export MULTICA_LIVE_ARTIFACT_DIR="$PWD/.artifacts/live"

uv run pytest -o addopts="" -v --strict-markers \
  -m live_smoke tests/live/test_agent_sandbox.py
```

Expected: one test passes in ≤120 seconds and final cleanup reports no leftovers.

## 8. Stability run

```bash
export MULTICA_LIVE_UPSTREAM_DIR=/absolute/path/to/multica
export MULTICA_LIVE_ARTIFACT_DIR="$PWD/.artifacts/live-repeat"
uv run python scripts/run_live_tests.py --resolve-cli --repeat 20 \
  --pytest-args "tests/live/test_agent_sandbox.py"
```

Expected: 20/20 pass; no Docker/process/backend entities with any completed run prefix.

## 9. Extended negative cases

```bash
uv run pytest -o addopts="" -v --strict-markers \
  -m live_extended tests/live/extended/test_agent_sandbox_failures.py
```

Expected: four test cases pass by observing expected failure behavior and cleanup; each creates sanitized diagnostic bundle.

## 10. Mutation audit

```bash
uv sync --group mutation
mkdir -p .artifacts/mutation
uv run mutmut run
uv run mutmut results | tee .artifacts/mutation/results.txt
```

Expected: only configured pure source modules are mutated; no live test executes; `.artifacts/mutation/results.txt` is uploaded by the weekly/manual workflow for maintainer triage. Survivor count is informational and does not gate a PR.

## 11. Real OpenCode canary

```bash
export MULTICA_CANARY_OPENCODE_PATH=/absolute/path/to/opencode
export MULTICA_CANARY_MODEL=provider/model
export MULTICA_CANARY_SECRET_NAMES=PROVIDER_API_KEY
export PROVIDER_API_KEY=secret-value

uv run pytest -o addopts="" -v --strict-markers \
  -m live_opencode_canary tests/live/extended/test_opencode_canary.py
```

Expected: passed or failed within 15 minutes with usage ≤0.10 USD and cleanup complete. Without required env, result is skipped before Docker starts.

## 12. Final repository checks

```bash
uv run ruff check .
uv run mypy src tests
uv run pytest
uv build
```

Expected: all pass; wheel and sdist are created; default pytest remains offline-only.
