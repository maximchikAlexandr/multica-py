# Quickstart: Versioned Upstream CLI Contract and SDK Upgrade Workflow

## Prerequisites

- Repository dependencies are installed with `uv sync --frozen --all-groups`.
- Supported contract artifacts and SDK coverage manifest are checked in.
- For manual collection only, a selected `multica` executable or verified release asset is available.

## Validate Offline Supported Coverage

Run the normal offline gate:

```sh
uv run python scripts/upstream_contract.py check --format human
```

Expected outcome:

- The command reads checked-in supported artifacts.
- It prints supported version, full commit, semantic hash, coverage counts, and failure count.
- It exits `0` when supported coverage is clean.
- It exits `2` for compatibility or coverage gaps.
- It does not require network, a live Multica account, or a local Multica executable.

## Validate Machine-Readable Report

Run:

```sh
uv run python scripts/upstream_contract.py check --format json --output /tmp/upstream-contract-report.json
```

Expected outcome:

- The JSON report contains supported, observed, candidate, upstream diff, coverage counts, and failures.
- The human output and JSON output describe the same result model.
- Automation can use the JSON report without parsing console text.

## Collect a Candidate Contract from a Local Binary

Run in manual refresh mode:

```sh
uv run python scripts/upstream_contract.py collect --binary "$(command -v multica)" --output /tmp/candidate-contract.json
```

Expected outcome:

- The collector records release version, full source commit, platform, collection method, generator identity, and semantic hash.
- The generated contract is canonical and deterministic for unchanged inputs.
- The SDK coverage manifest is not changed automatically.
- Missing full commit, timeout, or incomplete traversal exits with collector failure.

## Compare Supported and Candidate Contracts

Run:

```sh
uv run python scripts/upstream_contract.py diff --from tests/fixtures/provenance/supported-cli-contract.json --to /tmp/candidate-contract.json --format human
```

Expected outcome:

- Changes are grouped by semantic category and severity.
- Required argument/flag additions are breaking.
- Optional flag additions are additive.
- Help text-only changes are documentation-only.
- Possible renames are suggestions requiring maintainer confirmation.

## Validate Input and Output Contract Fixtures

Run focused contract tests for typed SDK operations:

```sh
uv run pytest tests/contract/test_full_cli_coverage.py tests/unit/test_upstream_contract_coverage.py -q
```

Expected outcome:

- Every typed row has an argv contract test comparing exact argument sequence.
- Every structured output row has a fixture or schema reference.
- Strict decoders reject removed or type-changed fields through negative fixtures.
- Optional output field additions are handled according to explicit decoder policy.

## Validate Runtime Compatibility Policy

Run compatibility-focused checks:

```sh
uv run pytest tests/unit/test_compatibility.py tests/unit/test_compat_policy.py -q
```

Expected outcome:

- Detected CLI version and supported range appear in diagnostics.
- CLI version/build metadata is read once per client instance.
- Newer untested CLI versions warn once unless an explicit override is configured.
- Documentation can be generated from the same compatibility matrix artifact.

## Prepare an Upgrade Bundle

Run:

```sh
uv run python scripts/upstream_contract.py prepare-upgrade --candidate /tmp/candidate-contract.json --output-dir artifacts/upstream-upgrades/v0.4.2..v0.4.3
```

Expected outcome:

- The bundle contains summary, upstream diff, impact map, candidate contract, manifest suggestions, implementation-task suggestions, changelog fragment, and test suggestions.
- Generated suggestions are incomplete and do not satisfy coverage.
- Re-running the command with unchanged inputs produces no diff.

## Validate Collector Security

For network-based observer mode, validate that official assets are checked before execution:

```sh
uv run python scripts/upstream_contract.py observe --dry-run
```

Expected outcome:

- The observer reports latest release identity without changing supported baseline.
- It plans checksum verification before any binary execution.
- It does not expose repository secrets to collection.
- Re-running for the same release is idempotent.

## Full Project Quality Gate

Run before marking implementation complete:

```sh
uv run ruff format --check .
uv run ruff check .
uv run mypy --namespace-packages --explicit-package-bases -p multica_py
uv run mypy tests scripts --ignore-missing-imports --follow-imports=silent --check-untyped-defs
uv run pytest
```

Expected outcome:

- All checks pass.
- Blocking checks remain offline.
- No generated artifact changes when inputs are unchanged.
