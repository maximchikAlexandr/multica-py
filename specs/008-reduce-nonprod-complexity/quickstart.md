# Quickstart: Validate the Reduction

Run from the repository root on branch `008-reduce-nonprod-complexity`.

## 1. Historical baseline

```bash
for path in \
  openspec/specs/sdk-surface/spec.md \
  openspec/specs/subprocess-transport/spec.md \
  openspec/specs/upstream-contract/spec.md \
  openspec/specs/verification-and-release/spec.md
do
  test -f "$path"
done
git grep -nE 'specs/00[1-6]' -- ':!specs/008-reduce-nonprod-complexity/**'
```

Expected: all four files exist; the final search prints nothing.

Check requirement/scenario grammar:

```bash
uv run pytest -q tests/contract/test_baseline_specs.py
```

Expected: every requirement has normative text, a scenario, `WHEN`, `THEN`,
and a historical source category.

## 2. Generator authority and determinism

```bash
uv run python scripts/upstream_contract.py validate \
  --approved contracts/sdk-contract.json
uv run python scripts/upstream_contract.py validate \
  --approved contracts/sdk-contract.json \
  --source-checkout /absolute/pinned/multica
uv run python scripts/upstream_contract.py check \
  --approved contracts/sdk-contract.json
uv run pytest -q \
  tests/unit/test_upstream_contract.py \
  tests/contract/test_sdk_contract.py
```

Expected: offline and pinned-source validation and check exit zero; the committed
`src/multica_py/_generated/approved_sdk.py` matches a clean render; two
transient renders are byte-identical.

Confirm removed state/goldens and the Group-D retired-reference guard:

```bash
test ! -e src/multica_py/_generated/upstream_state.json
test ! -e src/multica_py/_generated/upstream_supported_contract.json
test ! -e src/multica_py/_generated/upstream_coverage.json
test ! -e tests/fixtures/upstream_contract/v2
git grep -nE 'prepare-upgrade|stage-reviewed-candidate|upstream_contract\.py (upgrade|observe|diff|promote|reject)|upstream_upgrade\.sh|approved_sdk_cases\.py' -- ':!specs/008-reduce-nonprod-complexity/**'
```

Expected: path checks succeed and the search has no active code/docs match.

## 3. Canonical offline coverage

```bash
uv run pytest -q tests/unit/resources/test_operations.py
uv run pytest -q tests/component/test_process_contract.py
uv run pytest -q -m "not live" --collect-only
```

Expected: `discovered_public_methods == {case.sdk_method for case in
OPERATION_CASES if case.is_canonical}`, with 116 unique canonical methods, 135
unique case IDs, and 21 noncanonical variants;
the process module collects exactly `bytes-env`, `text-stdin`, and
`timeout-tree-cleanup`; no `tests/live` node appears in offline collection.

## 4. Full offline and package gates

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy --namespace-packages --explicit-package-bases -p multica_py
uv run mypy tests scripts tools --ignore-missing-imports \
  --follow-imports=silent --check-untyped-defs
uv run pytest -m "not live and not serial" -n auto --dist loadscope \
  --cov=multica_py --cov-branch --cov-report=json
uv run pytest -m "serial and not live" \
  --cov=multica_py --cov-branch --cov-append --cov-report=json
uv run python scripts/check_coverage.py --coverage-json coverage.json
uv run pytest -m packaging
uv build
TMP=$(mktemp -d)
mkdir "$TMP/empty"
uv venv --seed "$TMP/venv"
uv pip install --python "$TMP/venv/bin/python" msgspec
env -u PYTHONPATH "$TMP/venv/bin/python" -m pip install --no-deps "$PWD"/dist/multica_py-*.whl
cd "$TMP/empty" && env -u PYTHONPATH "$TMP/venv/bin/python" -c 'import multica_py, multica_py.enums, multica_py._generated.approved_sdk'
uv run pytest -o addopts="" -q tests/packaging/test_generated_runtime.py
```

Expected: every command exits zero without network, account, backend,
container, or agent sandbox.

## 5. Removed dependency and workflow-text tests

```bash
uv lock --check
git grep -nE 'DirectApiOracle|tools/live_support|live-extended|live-opencode-canary|httpx' -- ':!specs/008-reduce-nonprod-complexity/**'
git grep -nE 'test_ci_profiles\.py|test_live_target_workflows\.py|_job_block|WORKFLOWS.*glob' -- ':!specs/008-reduce-nonprod-complexity/**'
```

Expected: both searches print nothing.

## 6. Live collection

```bash
uv run pytest -o addopts="" -q \
  -m live_smoke tests/live/test_smoke.py --collect-only
```

Expected: exactly five tests named in
[verification.md](./contracts/verification.md).

To run them, use the prepared self-hosted environment or set all five
non-secret prepared-profile variables:

```bash
uv run pytest -o addopts="" -q \
  -m live_smoke tests/live/test_smoke.py
```

Expected: identity, CRUD, comment-list decoding, not-found, and presence semantics pass.
