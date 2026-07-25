# Contract: Exact Reduction Map

The paths below are binding. A task may update an extra referencing file found
by `rg`, but it may not retain a listed subsystem under a new name.

## Group A — Historical Spec Kit Records

Delete entire directories:

- `specs/001-full-cli-sdk/`;
- `specs/002-upstream-coverage-checks/`;
- `specs/003-multica-live-integration-tests/`;
- `specs/004-test-suite-optimization/`;
- `specs/005-test-suite-agent-sandbox/`;
- `specs/006-test-suite-consolidation/`.

Replacement:
[historical-baseline.md](./historical-baseline.md). Retain `specs/007-*` and
`specs/008-*` until the later OpenSpec migration.

## Group B — Test Meta-Governance

Delete:

- `scripts/_loc_metrics.py`;
- `scripts/check_test_architecture.py`;
- `scripts/check_test_baseline.py`;
- `scripts/capture_test_baseline.py`;
- `tests/behavioral-coverage.json`;
- `tests/duplicate-removal-map.json`;
- `tests/quality-baseline.json`;
- `tests/unit/test_test_architecture.py`;
- `tests/unit/test_quality_baseline_tools.py`.

Remove associated five-stage calls and artifact wiring from
`.github/workflows/ci.yml`. Remove their rules from `AGENTS.md` and `README.md`.

Replacement:

- `discovered_public_methods == {case.sdk_method for case in OPERATION_CASES if case.is_canonical}`, with 116 unique canonical methods, 137 unique IDs, and 21 noncanonical variants;
- existing coverage thresholds enforced by `scripts/check_coverage.py`;
- Ruff, mypy, offline pytest, package tests, marker selection;

## Group C — Duplicate Operation Harnesses

Delete after migration:

- `tests/cases/argv_data.py`;
- `tests/cases/models.py`;
- `tests/cases/assertions.py`;
- `tests/cases/execution.py`;
- current live-policy content of `tests/cases/operations.py`;
- `tests/component/test_cli_roundtrip.py`;
- `tests/_manifest_support.py`;
- `tests/_manifest_coverage.py`;
- `src/multica_py/_internal/manifest.py`;
- `src/multica_py/_generated/cli_manifest.json`;
- `tests/contract/test_cli_manifest.py`;
- `tests/contract/test_full_cli_coverage.py`.

Replacement:

- rewritten `tests/cases/operations.py`;
- retained `tests/cases/errors.py` only for distinct negative rows;
- rewritten `tests/unit/resources/test_operations.py`;
- three rows in `tests/component/test_process_contract.py`.

Delete fake-OpenCode fixtures and tests:

- `tests/fixtures/fake_opencode.py`;
- `tests/fixtures/fake_opencode_helpers.py`;
- `tests/component/test_fake_opencode_process.py`;
- `tests/unit/test_fake_opencode.py`.

Do not add compatibility aliases for `ArgvSpec`, `OperationCase` old fields,
`LivePolicy`, behavior dimensions, or old registries.

## Group D — Upstream State Machine and Goldens

Delete the entire
`src/multica_py/_internal/upstream_contract/` directory after the four-command
replacement is active. The replacement package is fixed by
[generation.md](./generation.md).

Delete:

- `scripts/upstream_upgrade.sh`;
- `scripts/check_upstream_drift.py`;
- `.github/workflows/upstream-contract-observer.yml`;
- `.github/workflows/upstream-drift.yml`;
- `contracts/schema/upstream-report-v1.schema.json`;
- old generated state/support/coverage/manifest files listed in
  [generation.md](./generation.md);
- `tests/fixtures/upstream_contract/v2/`;
- state/candidate/supported/exporter/help-parser/coverage/release goldens under
  `tests/fixtures/upstream_contract/golden/`;
- mutation fixtures used only by semantic diff/rename classification under
  `tests/fixtures/upstream_contract/mutations/`.

Delete all `tests/unit/test_upstream_contract_*.py` and
`tests/contract/upstream/*.py`, then add only:

- `tests/unit/test_upstream_contract.py`;
- `tests/contract/test_sdk_contract.py`.

`tests/unit/test_upstream_contract_security.py` behavior is folded into the
focused unit module using stdlib socket prohibition; it must not retain
`httpx`.

The deleted `tests/contract/conftest.py` and `tests/unit/conftest.py` supplied
only removed upstream-state fixtures and local helper aliases. Their retained
coverage is bound to the repository-level marker fixture in `tests/conftest.py`
and the focused contract/unit modules above; no fixture consumer remains.

Replace contributing/coverage/compatibility docs with the four-command flow.
Do not retain deprecated command aliases.

Update `AGENTS.md`, `docs/contributing.md`, `docs/cli-coverage.md`,
`docs/releasing.md`, `docs/compatibility.md`, and every active
`specs/007-upstream-v0-4-9-migration/*.md` occurrence in the same Group-D
change. The exact replacement text is `collect → validate --source-checkout →
render → check`; the retired-name guard in `generation.md` must be empty before
this group is accepted.

## Group E — SDK-Owned Live Control Plane

Delete the exact live ownership list in
[verification.md](./verification.md), including `tools/live_support`,
backend/sandbox/extended trees, live runner/resolver/cleanup/report/scanner
scripts, extended/canary workflows, and their unit/contract tests.

Replacement:

- `tests/live/conftest.py`;
- `tests/live/test_smoke.py`;
- concise `tests/live/README.md`;
- manual `.github/workflows/live-smoke.yml`.

Remove `httpx` from `pyproject.toml`; refresh `uv.lock` mechanically with
`uv lock`.

Delete `tests/live/.env.example`: it described the retired SDK-owned backend
bootstrap. The required externally prepared target inputs are documented and
validated by `tests/live/README.md`, `tests/live/conftest.py`, and the manual
`live-smoke.yml` workflow.

## Group F — Workflow Text Tests

Delete:

- `tests/contract/test_ci_profiles.py`;
- `tests/contract/test_live_target_workflows.py`;
- observer/drift workflow tests already covered by group D;
- any function elsewhere that reads `.github/workflows/*.yml` to assert
  literal jobs, matrices, commands, names, schedules, timeouts, action strings,
  or YAML text.

Do not replace these with a YAML parser test. Actual CI job outcomes and
external branch protection are the replacement.

## Out of Scope: Must Remain

Do not change policy or remove:

- `.github/workflows/mutation.yml` and `[tool.mutmut]`;
- package install modes or `.github/workflows/package-test.yml`;
- strict mypy scopes;
- local cache/artifact cleanup policy;
- production resource/model behavior except imports needed for the one runtime
  generated module;
- `specs/007-upstream-v0-4-9-migration/`;
- Spec Kit installation and `.specify/` (removed only by the next migration).

## Reference Guard

Run this one exact retired-reference guard after each named group. Every command
excludes feature 008 itself, because this reduction specification intentionally
names retired artefacts. Each command must print no output.

| Group | Exact command |
| --- | --- |
| A | `git grep -nE 'specs/00[1-6]' -- ':!specs/008-reduce-nonprod-complexity/**'` |
| B | `git grep -nE 'check_test_architecture\.py|check_test_baseline\.py|quality-baseline\.json|duplicate-removal-map\.json' -- ':!specs/008-reduce-nonprod-complexity/**'` |
| C | `git grep -nE 'ArgvSpec|LivePolicy|KNOWN_ARGV_GAPS|KNOWN_FIXTURE_GAPS|KNOWN_LIVE_GAPS|LIVE_EXEC_EXCEPTIONS' -- ':!specs/008-reduce-nonprod-complexity/**'` |
| D | `git grep -nE 'prepare-upgrade|stage-reviewed-candidate|upstream_contract\.py (upgrade|observe|diff|promote|reject)|upstream_upgrade\.sh|approved_sdk_cases\.py' -- ':!specs/008-reduce-nonprod-complexity/**'` |
| E | `git grep -nE 'DirectApiOracle|tools/live_support|live-extended|live-opencode-canary|httpx' -- ':!specs/008-reduce-nonprod-complexity/**'` |
| F | `git grep -nE 'test_ci_profiles\.py|test_live_target_workflows\.py|_job_block|WORKFLOWS.*glob' -- ':!specs/008-reduce-nonprod-complexity/**'` |

A stale reference is fixed at its actual owner; no shim, empty placeholder,
ignored golden, or allowlist entry is accepted.
