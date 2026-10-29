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

For the current direct `0.6.2` → `0.7.1` review, the baseline source is pinned
to `7ab92d7622ecd81d179a8d83ae2dea74835a5069`; the target source is pinned to
`aec9b0b1699939a6d993da9ca2ebd2c62900a8e0` (release `425269384`) and the
compatibility interval is `[0.6.2, 0.7.2)`. Verify both release archives against
their official manifests before hashing their extracted executables. Pass only
the target executable digest to `collect --sha256`. Run the source-link audit
after validation:

The earlier `0.5.0` → `0.5.1` instructions are historical and no longer
describe the current release workflow.

```bash
uv run python scripts/audit_source_links.py \
  --source-checkout .devlocal/upstream-contract/v0.7.1/source/multica
```

The release gate also keeps the immutable composition's original planning
parent separate from the verified planning revision used for final OpenSpec
equality. Preserve accepted implementation commits and run the composition
gate with both SHA inputs; never rewrite composition or accepted history.

The generated runtime projection is
`src/multica_py/_generated/approved_sdk.py`. Documentation, compatibility, and
provenance projections are transient and must remain outside tracked paths. The
0.7.1 release provenance is kept under
`.devlocal/upstream-contract/v0.7.1/evidence/`.
