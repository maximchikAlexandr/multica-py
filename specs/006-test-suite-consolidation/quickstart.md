# Quickstart: validation by fixed PR stages

Все команды выполняются из repository root. Stages выполняются только последовательно.

## Prerequisites

```bash
uv sync --frozen --all-groups
mkdir -p .artifacts/test-suite-consolidation .artifacts/mutation
```

Перед каждым `check_test_baseline.py` обновить quality artifacts одним и тем же блоком:

```bash
rm -f .coverage coverage.json
uv run pytest -q tests/unit tests/contract tests/component \
  --junitxml=.artifacts/test-suite-consolidation/offline-junit.xml
uv run pytest -o addopts="" -q -m "not live and not packaging and not serial" \
  --cov=multica_py --cov-branch --cov-report=
uv run pytest -o addopts="" -q -m "serial and not live and not packaging" \
  --cov=multica_py --cov-branch --cov-append \
  --cov-report=term-missing --cov-report=json
NO_COLOR=1 uv run mutmut run
NO_COLOR=1 uv run mutmut results --all > .artifacts/mutation/results.txt
```

## Stage pr1 — baseline-process

```bash
uv run pytest -o addopts="" -q -m "process and serial" \
  tests/component/test_process_contract.py

# Выполнить quality-artifact block выше.
GREEN_SHA="$(git rev-parse HEAD)"
uv run python scripts/capture_test_baseline.py \
  --git-sha "$GREEN_SHA" \
  --source-snapshot b3a299b36d1ad5bc386b5e4517d2a348d53db31c \
  --coverage-json coverage.json \
  --junit-xml .artifacts/test-suite-consolidation/offline-junit.xml \
  --mutation-results .artifacts/mutation/results.txt \
  --behavior-manifest tests/behavioral-coverage.json \
  --output tests/quality-baseline.json

uv run python scripts/check_test_architecture.py --stage pr1
uv run python scripts/check_test_baseline.py \
  --baseline tests/quality-baseline.json --stage pr1 \
  --coverage-json coverage.json \
  --junit-xml .artifacts/test-suite-consolidation/offline-junit.xml \
  --mutation-results .artifacts/mutation/results.txt
```

Expected: process IDs `cancellation`, `timeout`, `sigterm-escalation`, `descendant-cleanup` pass; baseline schema 2 is committed and remains unchanged afterward.

## Stage pr2 — operation-catalog

```bash
uv run pytest -q tests/unit/resources/test_operations.py
uv run pytest -q \
  tests/component/test_cli_roundtrip.py \
  tests/component/test_cli_errors.py \
  tests/component/test_fake_cli.py
# Выполнить quality-artifact block выше.
uv run python scripts/check_test_architecture.py --stage pr2
uv run python scripts/check_test_baseline.py \
  --baseline tests/quality-baseline.json --stage pr2 \
  --coverage-json coverage.json \
  --junit-xml .artifacts/test-suite-consolidation/offline-junit.xml \
  --mutation-results .artifacts/mutation/results.txt
```

Expected: 111 unique operation IDs; only `OperationCase`; old case catalogs absent.

## Stage pr3 — offline-cleanup

```bash
uv build
uv run pytest -o addopts="" -q tests/packaging/test_artifacts.py
# Выполнить quality-artifact block выше.
uv run python scripts/check_test_architecture.py --stage pr3
uv run python scripts/check_test_baseline.py \
  --baseline tests/quality-baseline.json --stage pr3 \
  --coverage-json coverage.json \
  --junit-xml .artifacts/test-suite-consolidation/offline-junit.xml \
  --mutation-results .artifacts/mutation/results.txt
```

Expected: `tests/fixtures/json/` absent; six upstream contract modules; packaging skips zero; package install paths six; test LOC `<=11000`.

## Stage pr4 — live-core

```bash
uv run python scripts/run_live_tests.py --resolve-cli --mode smoke -- --timeout=0 -q
uv run python scripts/run_live_tests.py --resolve-cli --mode extended -- --timeout=0 -q
# Выполнить quality-artifact block выше.
uv run python scripts/check_test_architecture.py --stage pr4
uv run python scripts/check_test_baseline.py \
  --baseline tests/quality-baseline.json --stage pr4 \
  --coverage-json coverage.json \
  --junit-xml .artifacts/test-suite-consolidation/offline-junit.xml \
  --mutation-results .artifacts/mutation/results.txt
```

Expected: labels/projects use one branch-free CRUD algorithm; four public contexts; one HTTP client; live support LOC `<=3000`.

## Stage pr5 — sandbox-final

```bash
# deterministic sandbox + extended failure scenarios (через live runner, как в stage pr4).
uv run python scripts/run_live_tests.py --resolve-cli --mode extended -- \
  --timeout=0 -q -k agent_sandbox
uv run ruff format --check .
uv run ruff check .
uv run mypy --namespace-packages --explicit-package-bases -p multica_py
uv run mypy tests scripts tools --ignore-missing-imports --follow-imports=silent --check-untyped-defs
# Выполнить quality-artifact block выше.
uv run python scripts/check_test_architecture.py --stage final
uv run python scripts/check_test_baseline.py \
  --baseline tests/quality-baseline.json --stage final \
  --coverage-json coverage.json \
  --junit-xml .artifacts/test-suite-consolidation/offline-junit.xml \
  --mutation-results .artifacts/mutation/results.txt
```

Запустить real-provider canary на feature branch:

```bash
gh workflow run live-opencode-canary.yml --ref 006-test-suite-consolidation
gh run watch "$(gh run list --workflow live-opencode-canary.yml \
  --branch 006-test-suite-consolidation --limit 1 \
  --json databaseId --jq '.[0].databaseId')" --exit-status
```

Expected: test LOC `<=10500`; live support LOC `<=2500`; max file LOC `<=800`; all offline/package/live/canary gates green.
