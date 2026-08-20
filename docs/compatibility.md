# Compatibility Policy

The generated runtime constants in
`src/multica_py/_generated/approved_sdk.py` define the reviewed CLI interval:

- `MIN_CLI_VERSION` equals `TARGET_VERSION`;
- `MAX_CLI_VERSION` is the exclusive next patch version.

The current reviewed interval is `[0.4.28, 0.4.29)`.

`multica_py._internal.compat` imports these constants. Client configuration
may override the bounds explicitly, while `strict`, `warn`, and `ignore`
retain their documented runtime behaviour.

For an upstream release, use the reviewed flow:

```text
collect → validate --source-checkout → render → check
```

The current v0.4.28 review uses these exact stages, in this order; collection
requires the verified release binary and writes only to ignored evidence:

```bash
uv run python scripts/upstream_contract.py collect \
  --source-checkout /absolute/pinned/v0.4.28/source \
  --binary /absolute/verified/multica-cli-0.4.28 \
  --tag v0.4.28 --version 0.4.28 \
  --commit 38c992ad0a757434fb51584fa34e3bc57d1b78e1 \
  --release-id 371790559 --asset-name multica-cli-0.4.28-darwin-arm64.tar.gz \
  --sha256 e42c1c6df05201d2d0feff1a9d8032a9ea11c6644721fd465496826124007acf \
  --os darwin --arch arm64 \
  --version-output /absolute/evidence/version-output.json \
  --output-dir /absolute/ignored/upstream-contract-evidence
uv run python scripts/upstream_contract.py validate \
  --approved contracts/sdk-contract.json \
  --source-checkout /absolute/pinned/v0.4.28/source
uv run python scripts/upstream_contract.py render \
  --approved contracts/sdk-contract.json \
  --runtime-output src/multica_py/_generated/approved_sdk.py \
  --transient-output /absolute/ignored/upstream-contract-render
uv run python scripts/upstream_contract.py check \
  --approved contracts/sdk-contract.json
```

The prior `v0.4.20` interval `[0.4.20, 0.4.21)` remains documented only as
historical context in archived OpenSpec material and earlier migration notes.

Evidence and transient reports are not runtime inputs. Only a reviewed Git
change to `contracts/sdk-contract.json` and the single generated runtime
projection can promote a new compatibility interval.

At v0.4.28, `client.auth.login()` maps to the root `login` Cobra command.
`configuration.get()` is retained only as a no-argument compatibility alias of
`configuration.show()` / `config show`; the removed `config get <key>` path is
not part of the tagged CLI. The SDK also removes the former
`issues.deprioritize` and `workspaces.watch/unwatch` methods because the pinned
command tree contains no equivalent leaves.
