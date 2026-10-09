# Compatibility Policy

The generated runtime constants in
`src/multica_py/_generated/approved_sdk.py` define the reviewed CLI interval:

- `TARGET_VERSION` remains the exact source checkout pinned by every source reference;
- `MIN_CLI_VERSION` and exclusive `MAX_CLI_VERSION` come from the approved compatibility block.

The current reviewed interval is `[0.6.0, 0.6.2)`. This direct `0.6.0` →
`0.6.1` migration compares baseline `0.6.0` at source commit
`48745d2fe9e80ee9c027293ef22971ff5723f5f5` with target `0.6.1` at source
commit `2ea01ae4ef55de4310b99af192d2dbd367832883`; it does not publish an
intermediate SDK release. The target is release `400860726`. The typed SDK
maintains a closed 205-node inventory, 193-operation registry, and 196-entrypoint
response registry, with nine changed and 187 unchanged responses. Unrelated UI,
mobile, desktop, search, channel, WeCom, scheduler, and other internal changes
remain outside the SDK.
Historical note: the superseded `0.5.0` → `0.5.1` review is retained only as
historical comparison evidence, not as the current compatibility claim.

The baseline comparison is the approved `0.6.0` release asset
`multica-cli-0.6.0-darwin-arm64.tar.gz`: archive digest
`b0d90f9eda1080b924520fc1fa0b72912e27134e856b0ce6f4a04231d126651a`, executable
digest `c8b1c13590b28fcc591268658d139a1eb426f3cc54d5c9abbd50558d65fed2c4`,
and version-output digest
`8116e8c0c49f74127fc72dd90baf4dae0b27f0ad94a21905e0d153b7dd1bffdb`.
The target release is GitHub release `400860726`, asset
`multica-cli-0.6.1-darwin-arm64.tar.gz`; archive digest
`f2cc3ef1a142bbf5f419d625cd98323602ca96007b4b29f2e0068439be32a2e9`, executable
digest `a6a73b6c13a8da4fe9591b0884ee24aaac8a8f0913f1dfb3d8d34eda6a23371e`,
and version-output digest
`c6f360978000921093c3232e866003ac0038a80cfcb801707c52021981eec086`.
These identities are checked independently; the collector receives only the
executable digest. The preceding `0.4.44` archive and executable digests remain
historical comparison evidence; both baseline and target retain separate
checksum roles.

`multica_py._internal.compat` imports these constants. Client configuration
may override the bounds explicitly, while `strict`, `warn`, and `ignore`
retain their documented runtime behaviour.

For an upstream release, use the reviewed flow:

```text
collect → validate --source-checkout → render → check
```

The current v0.6.1 review uses these exact stages, in this order; collection
requires the verified release binary and writes only to ignored evidence:

```bash
uv run python scripts/upstream_contract.py collect \
  --source-checkout /absolute/pinned/v0.6.0..v0.6.1/source/multica \
  --binary /absolute/verified/multica-cli-0.6.1 \
  --tag v0.6.1 --version 0.6.1 \
  --commit 2ea01ae4ef55de4310b99af192d2dbd367832883 \
  --release-id 400860726 --asset-name multica-cli-0.6.1-darwin-arm64.tar.gz \
  --sha256 a6a73b6c13a8da4fe9591b0884ee24aaac8a8f0913f1dfb3d8d34eda6a23371e \
  --os darwin --arch arm64 \
  --version-output /absolute/evidence/version-output.json \
  --output-dir /absolute/ignored/upstream-contract-evidence
uv run python scripts/upstream_contract.py validate \
  --approved contracts/sdk-contract.json \
  --source-checkout /absolute/pinned/v0.6.0..v0.6.1/source/multica
uv run python scripts/upstream_contract.py render \
  --approved contracts/sdk-contract.json \
  --runtime-output src/multica_py/_generated/approved_sdk.py \
  --transient-output /absolute/ignored/upstream-contract-render
uv run python scripts/upstream_contract.py check \
  --approved contracts/sdk-contract.json
uv run python scripts/audit_source_links.py \
  --source-checkout /absolute/pinned/v0.6.0..v0.6.1/source/multica
```

The release archive hashes are verified separately from the extracted binary:
the 0.4.28 archive/binary are
`e42c1c6df05201d2d0feff1a9d8032a9ea11c6644721fd465496826124007acf` /
`26a722384d8ef39a30cb83fec4e76f3185768369536d1f13a546b03e6c7fbeb9`, and the
0.4.42 archive/binary are
`a3bb48baeeb757361686978210e6195aaf50bc69edf83bf3b9c52ca3efc12e41` /
`22abcd910562e8800c0e9db561229731e19486ec94b4815d6b1a075dc92ef36c`, and
0.4.43 archive/binary are
`7d31b12d2ae94eab780cfcfdcfb7a9f43c6327c4ae54813d886410305cd26261` /
`b67ad1196dd62c6f59c29837db392a55a0e78a8ae2ac514ef861805eb2e19885`, and
0.4.44 archive/binary are
`f300cf8036b1f596466acde35f67d986f1f75a657f77e6e0e9de1134563a76aa` /
`ac26860e3f60ab6eafd4e7066d43d0fad2b0691adfefac339c4921e1dd68f774`.
The collector's `--sha256` receives the extracted executable digest, never the
archive digest; version JSON and archive identities are checked independently.

Evidence and transient reports are not runtime inputs. Only a reviewed Git
change to `contracts/sdk-contract.json` and the single generated runtime
projection can promote a new compatibility interval.

The 0.4.32 compatibility extension reviews the issue get/usage/runs response
fields against the exact release source. It preserves scalar issue assignees,
token/cost/uncosted categories, and bounded task-run worktree/runtime context.
Unreviewed response additions remain ignored until a later contract review.

At v0.4.28, `client.auth.login()` maps to the root `login` Cobra command.
`configuration.get()` is retained only as a no-argument compatibility alias of
`configuration.show()` / `config show`; the removed `config get <key>` path is
not part of the tagged CLI. The SDK also removes the former
`issues.deprioritize` and `workspaces.watch/unwatch` methods because the pinned
command tree contains no equivalent leaves.
