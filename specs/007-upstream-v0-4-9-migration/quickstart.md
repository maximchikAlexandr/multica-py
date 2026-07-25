# Quickstart: Validate the v0.4.9 Migration

Run from repository root. Commands below are implementation acceptance targets;
live commands require the exact approved environment and run only after all
offline/coherence gates pass.

## 1. Contract and Generated Outputs

```bash
test "$(git -C .devlocal/upstream/multica-v0.4.9 rev-parse HEAD)" = \
  ecbdbda09e7b2be56cd9ccc55cee1ee360222d18
uv run python scripts/upstream_contract.py validate-source \
  --approved specs/007-upstream-v0-4-9-migration/contracts/sdk-contract-v2.seed.json \
  --source-root .devlocal/upstream/multica-v0.4.9
cmp --silent \
  specs/007-upstream-v0-4-9-migration/contracts/sdk-contract-v2.seed.json \
  contracts/sdk-contract.json

uv run python scripts/upstream_contract.py generate \
  --approved contracts/sdk-contract.json \
  --check

uv run python scripts/upstream_contract.py validate --source-checkout /absolute/pinned/source \
  --evidence .devlocal/artifacts/upstream-upgrades/v0.3.10..v0.4.9/candidate-contract.json \
  --approved contracts/sdk-contract.json \
  --release-provenance .devlocal/artifacts/upstream-upgrades/v0.3.10..v0.4.9/release-provenance.json \
  --expected-evidence-trust help-degraded \
  --output src/multica_py/_generated/upstream_candidate_contract.json

uv run python scripts/upstream_contract.py check --with-candidate
uv run python scripts/upstream_contract.py check \
  --decision contracts/upstream-v0.4.9-promotion-decision.json \
  --check
```

Expected: seven outputs present and byte-identical; staged candidate trust is
`approved-contract-bound`, never `verified`; check mode writes nothing;
canonical candidate/supported refs exist and match their semantic hashes;
promotion binds candidate, approved contract, exact target, provenance, and
previous supported identity without writing.

## 2. Focused Offline Validation

```bash
uv run pytest \
  tests/unit/test_upstream_contract_generator.py \
  tests/unit/test_upstream_contract_state.py \
  tests/unit/test_upstream_contract_promotion.py \
  tests/unit/test_upstream_contract_provenance.py \
  tests/unit/resources/test_operations.py \
  tests/unit/resources/test_issues.py \
  tests/unit/test_project_resource_models.py \
  tests/unit/test_transport.py \
  tests/component/test_cli_roundtrip.py \
  tests/component/test_process_contract.py \
  tests/contract/upstream \
  tests/contract/test_cli_manifest.py \
  tests/contract/test_full_cli_coverage.py \
  tests/live/test_smoke.py
```

Expected: schema, generator, state, promotion, provenance, argv, response,
presence, timeout/error, and coherence tests pass. Case tables contain complete
argv and positive/negative constraint cases.

## 3. Full Offline Quality

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run mypy tests scripts tools
uv run pytest -m "not live" \
  --junitxml=.test-artifacts/upstream-v0.4.9/offline/offline-junit.xml
uv run coverage erase
uv run pytest -o addopts="" -q --strict-markers \
  -m "not live and not serial" -n auto --dist loadscope \
  --cov=multica_py --cov-branch --cov-report=
uv run pytest -o addopts="" -q --strict-markers \
  -m "serial and not live" \
  --cov=multica_py --cov-branch --cov-append \
  --cov-report=json:.test-artifacts/upstream-v0.4.9/offline/coverage.json
uv run python scripts/check_coverage.py \
  --coverage-json .test-artifacts/upstream-v0.4.9/offline/coverage.json
uv run pytest -m "not live" --collect-only

```

Expected: all checks pass; non-live collection contains no `tests/live/*` node.
The implementation workflow must create the mutation result artifact before the
final baseline stage.

## 4. Five-Stage Architecture and Baseline Gates

```bash
uv run python scripts/check_coverage.py \
  --coverage-json .test-artifacts/upstream-v0.4.9/offline/coverage.json
```

The final baseline CLI flags are exactly `--coverage-json`, `--junit-xml`, and
`--mutation-results`. Keep those names while changing all three from optional
final-stage inputs to required final-stage inputs. Expected: a missing or
unreadable input is invalid; all five stages pass without weakening baselines
or allowlists.

## 5. Prepared-target Live Smoke

```bash
uv run pytest -o addopts="" -q \
  -m live_smoke tests/live/test_smoke.py
```

The runner supplies the five prepared-target variables documented in
`tests/live/README.md`; no backend or CLI resolver is owned by this repository.

## 6. Stability

Stability and extended live orchestration are outside the prepared-target SDK
scope. Use repeated manual smoke runs when the environment owner requires
additional confidence.

## Stop Conditions

Stop on any red phase gate. Do not update active supported/live metadata before
contract generation, promotion dry-check, and coherence pass. Environment,
authentication, or invalid-run live outcomes are inconclusive and cannot count
as migration acceptance.
