# Compatibility Policy

The generated runtime constants in
`src/multica_py/_generated/approved_sdk.py` define the reviewed CLI interval:

- `MIN_CLI_VERSION` equals `TARGET_VERSION`;
- `MAX_CLI_VERSION` is the exclusive next patch version.

The current reviewed interval is `[0.4.20, 0.4.21)`.

`multica_py._internal.compat` imports these constants. Client configuration
may override the bounds explicitly, while `strict`, `warn`, and `ignore`
retain their documented runtime behaviour.

For an upstream release, use the reviewed flow:

```text
collect → validate --source-checkout → render → check
```

The current v0.4.20 review uses these exact stages, in this order; collection
requires the verified release binary and writes only to ignored evidence:

```bash
uv run python scripts/upstream_contract.py collect \
  --source-checkout /absolute/pinned/v0.4.20/source \
  --binary /absolute/verified/multica-cli-0.4.20 \
  --tag v0.4.20 --version 0.4.20 \
  --commit 93342d04a7a9f788fec921e5aa736f86c7f22d8f \
  --release-id 366120041 --asset-name multica-cli-0.4.20-darwin-arm64.tar.gz \
  --sha256 2ff226b0d8c086736ad3e7ab223bf53d6cbce7e6961deadf6922e13dce4f6f08 \
  --os darwin --arch arm64 \
  --version-output /absolute/evidence/version-output.json \
  --output-dir /absolute/ignored/upstream-contract-evidence
uv run python scripts/upstream_contract.py validate \
  --approved contracts/sdk-contract.json \
  --source-checkout /absolute/pinned/v0.4.20/source
uv run python scripts/upstream_contract.py render \
  --approved contracts/sdk-contract.json \
  --runtime-output src/multica_py/_generated/approved_sdk.py \
  --transient-output /absolute/ignored/upstream-contract-render
uv run python scripts/upstream_contract.py check \
  --approved contracts/sdk-contract.json
```

Evidence and transient reports are not runtime inputs. Only a reviewed Git
change to `contracts/sdk-contract.json` and the single generated runtime
projection can promote a new compatibility interval.
