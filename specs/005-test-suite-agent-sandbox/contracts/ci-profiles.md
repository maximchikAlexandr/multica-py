# Contract: CI Profiles

## quality

- runner: Ubuntu
- Python: 3.12
- required check: yes
- selection pass 1: `not live and not serial`
- execution: xdist `-n auto --dist loadscope`
- selection pass 2: `serial and not live`
- execution: single process, `--cov-append`
- outputs: `coverage.xml`, `coverage.json`, terminal missing branches
- gate: zonal 80/90/70/95 and baseline behavioral counts

## compatibility

- required check: yes
- matrix: Ubuntu/macOS × Python 3.12/3.13
- selection: `-m compat`
- minimum collected items: 4 (see `contracts/compat-tests.md`)
- no full suite and no live

## live-smoke

- required check: yes
- runner: Ubuntu
- selection: `-m live_smoke tests/live`
- job timeout budget: 300 seconds (assert in workflow; maps to SC-009)
- includes exactly one new deterministic agent sandbox case
- final cleanup: `if: always()`

## live-extended

- required check: no
- schedule/manual according to existing workflow
- selection: `live_smoke or live_extended`, excluding `live_opencode_canary`
- includes four deterministic sandbox failure cases

## mutation

- required check: no
- schedule: weekly Tuesday 03:00 UTC and manual
- dependency group: mutation
- source scope: closed list in `contracts/mutation-scope.md`
- tests: unit+component only
- no Docker/live
- artifact: complete textual `mutmut results`
- no mutation-score or survivor-count gate

## live-opencode-canary

- required check: no
- schedule: weekly Sunday 03:00 UTC and manual
- marker: `live_opencode_canary`
- required env: `MULTICA_CANARY_OPENCODE_PATH`, `MULTICA_CANARY_MODEL`, `MULTICA_CANARY_SECRET_NAMES`, plus every named secret
- one scenario/one model/one attempt
- timeout: 15 minutes
- usage ceiling: 0.10 USD
- final cleanup and diagnostics always run

## package-test

- build wheel once
- pip install: 4 matrix cells
- uv pip install: Ubuntu/Python 3.12 only
- uv add: Ubuntu/Python 3.12 only
- total install paths: 6
