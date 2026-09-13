# Contributing

## Setup and quality gates

```bash
uv sync --frozen --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy --namespace-packages --explicit-package-bases -p multica_py
uv run mypy tests scripts tools --ignore-missing-imports --follow-imports=silent --check-untyped-defs
uv run pytest -m "not live"
uv build
```

## Approved upstream contract workflow

`contracts/sdk-contract.json` is the only reviewed input that may change
generated public SDK behaviour. The maintainer sequence is:

```bash
uv run python scripts/upstream_contract.py collect \
  --source-checkout /absolute/pinned/source \
  --binary /absolute/verified/multica \
  --tag vX.Y.Z --version X.Y.Z --commit <40-hex> --release-id <id> \
  --asset-name <name> --sha256 <extracted-executable-sha256> --os <os> --arch <arch> \
  --version-output /absolute/version.json --output-dir /absolute/evidence
uv run python scripts/upstream_contract.py validate \
  --approved contracts/sdk-contract.json \
  --source-checkout /absolute/pinned/source
uv run python scripts/upstream_contract.py render \
  --approved contracts/sdk-contract.json \
  --runtime-output src/multica_py/_generated/approved_sdk.py \
  --transient-output /absolute/ignored/output
uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json
```

`collect` records only declarative source facts and fail-closed review items.
It never edits the approved contract or repository runtime code. Review and Git
merge are the sole promotion decision; candidate state, journals, upgrade
bundles, and golden generated copies are not used.

For the current direct `0.4.42` → `0.4.43` review, the target source is pinned
to `2ae2dbbb8f9ed9ffe1739ecf5abfe31a940ee50c` and the compatibility interval
is `[0.4.42, 0.4.44)`. Verify the `0.4.42` and `0.4.43` release archives
against the official manifests before hashing their extracted executables;
pass only the executable digest to `collect --sha256`. Run the source-link
audit after validation:

```bash
uv run python scripts/audit_source_links.py \
  --source-checkout .devlocal/upstream-contract/v0.4.42..v0.4.43/source-repo/.devlocal/upstream-contract/v0.4.42..v0.4.43/source-0.4.43
```

The generated runtime projection is
`src/multica_py/_generated/approved_sdk.py`. Documentation, compatibility, and
provenance projections are transient and must remain outside tracked paths.
