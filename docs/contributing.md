# Contributing

## Setup

```bash
uv sync --frozen --all-groups
```

## Quality gates

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy --namespace-packages --explicit-package-bases -p multica_py
uv run mypy tests scripts --ignore-missing-imports --follow-imports=silent --check-untyped-defs
uv run pytest
uv build
```

## Upstream-contract workflow

The maintainer CLI lives at `scripts/upstream_contract.py`. Run the
offline gate, collect a candidate, diff supported vs. candidate, and
prepare an upgrade bundle:

```bash
uv run python scripts/upstream_contract.py check --format human
uv run python scripts/upstream_contract.py check --format json --output /tmp/report.json
uv run python scripts/upstream_contract.py collect \
  --binary "$(command -v multica)" \
  --version 0.4.2 \
  --tag v0.4.2 \
  --commit 48b8dbf43971e5ea974bf827220cd212a1240c72 \
  --asset-name multica-cli-0.4.2-linux-amd64.tar.gz \
  --sha256 "<release-sha256>" \
  --os linux \
  --arch amd64 \
  --version-output "multica 0.4.2" \
  --output /tmp/candidate.json
uv run python scripts/upstream_contract.py diff \
  --from src/multica_py/_generated/upstream_supported_contract.json \
  --to /tmp/candidate.json
uv run python scripts/upstream_contract.py prepare-upgrade \
  --candidate /tmp/candidate.json \
  --output-dir artifacts/upstream-upgrades/v0.4.2..v0.4.3
uv run python scripts/upstream_contract.py apply-manifest-suggestions \
  --bundle artifacts/upstream-upgrades/v0.4.2..v0.4.3
uv run python scripts/upstream_contract.py promote --decision promotion.json
uv run python scripts/upstream_contract.py observe \
  --release-id 123 --version 0.4.3 --tag v0.4.3 --dry-run
```

The observer workflow (`.github/workflows/upstream-contract-observer.yml`)
is non-blocking and only updates observed/candidate state.

One-shot maintainer entrypoint (requires full collect provenance):

```bash
TAG=v0.4.3 \
RELEASE_ID=123 \
COMMIT=abc1234567890abcdef1234567890abcdef12345 \
BINARY="$(command -v multica)" \
ASSET_NAME=multica-cli-0.4.3-linux-amd64.tar.gz \
SHA256="<release-sha256>" \
VERSION_OUTPUT="multica 0.4.3" \
./scripts/upstream_upgrade.sh
```

Or invoke the Python subcommand directly:

```bash
uv run python scripts/upstream_contract.py upgrade \
  --tag v0.4.3 \
  --version 0.4.3 \
  --commit abc1234567890abcdef1234567890abcdef12345 \
  --release-id 123 \
  --binary "$(command -v multica)" \
  --asset-name multica-cli-0.4.3-linux-amd64.tar.gz \
  --sha256 "<release-sha256>" \
  --os linux \
  --arch amd64 \
  --version-output "multica 0.4.3" \
  --output-dir artifacts/upstream-upgrades/v0.4.2..v0.4.3
```

Verified contract export paths for upstream contribution are documented in
`tools/upstream-cli-contract/README.md`.

## Adding a new command

1. Update `src/multica_py/_generated/upstream_state.json` with the
   new supported baseline.
2. Update `src/multica_py/_generated/upstream_coverage.json` with the
   new `CoverageDecision` (typed/raw/process/unsupported/legacy/incomplete).
3. Update the supported contract at
   `src/multica_py/_generated/upstream_supported_contract.json`.
4. Add tests under `tests/unit/`, `tests/contract/`, `tests/component/`.
5. Update `docs/cli-coverage.md` with the new state.

## Approved SDK contract

`contracts/sdk-contract.json` is the only valid production generator
input. Source evidence, candidate diffs, and generated upgrade bundles
are never generator input.
