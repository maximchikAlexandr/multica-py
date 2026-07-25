# Verified upstream CLI contract evidence

The approved SDK contract is maintained in `contracts/sdk-contract.json`.
Evidence collection is fail-closed and never changes public SDK behavior.

Validate the approved contract and, when reviewing a pinned checkout, verify
its source references:

```bash
uv run python scripts/upstream_contract.py validate \
  --approved contracts/sdk-contract.json \
  --source-checkout .devlocal/upstream/multica-v0.4.9
```

Collect declarative facts from a pinned source checkout and verified release
binary into a caller-supplied ignored directory:

```bash
uv run python scripts/upstream_contract.py collect \
  --source-checkout .devlocal/upstream/multica-v0.4.9 \
  --binary /path/to/multica \
  --tag v0.4.9 --version 0.4.9 --commit <full-commit> \
  --release-id <release-id> --asset-name <asset-name> \
  --sha256 <sha256> --os darwin --arch arm64 \
  --version-output /path/to/version-output.json \
  --output-dir /private/tmp/upstream-contract-evidence
```

The collector writes only `evidence.json` and `review-items.json`. Unknown
source patterns, unresolved helpers, imperative validation, and
presence-sensitive behavior become review items; they cannot generate or
modify the approved contract.

After a reviewed contract change, render the committed runtime projection and
transient documentation/reports, then check the repository:

```bash
uv run python scripts/upstream_contract.py render \
  --approved contracts/sdk-contract.json \
  --runtime-output src/multica_py/_generated/approved_sdk.py \
  --transient-output /private/tmp/upstream-contract-render
uv run python scripts/upstream_contract.py check \
  --approved contracts/sdk-contract.json
```

The pinned upstream CLI source and release binary are evidence sources only.
The approved contract is the sole production generator input.
