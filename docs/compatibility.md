# Compatibility Policy

The generated runtime constants in
`src/multica_py/_generated/approved_sdk.py` define the reviewed CLI interval:

- `TARGET_VERSION` remains the exact source checkout pinned by every source reference;
- `MIN_CLI_VERSION` and exclusive `MAX_CLI_VERSION` come from the approved compatibility block.

The current reviewed interval is `[0.4.42, 0.5.1)`. This direct migration
compares baseline `0.4.44` at source commit
`c7f259c70a60bff30011c403fada79ab382f608a` with target `0.5.0` at source
commit `2df765a3c8f39789c9fb76316378bcffc20d22d9`; it does not publish an
intermediate SDK release. Retained operations support `0.4.42`; new comment,
skill-label, label-input, and target-only response behavior gates at `0.5.0`,
and `0.5.1` is exclusive.

The target release is GitHub release `391379076`, asset
`multica-cli-0.5.0-darwin-arm64.tar.gz`. Its official archive digest is
`b4bae1001c30a870c784b19123437df9f09308f750a699ce3693877ba6ffc5d1`, its
extracted executable digest is
`e8305b68e13d7cceeaaf382723d465552a9555b6540f1899527eccb36847e094`, and its
version-output digest is
`1f51c193e774cab80dfc93706de3081e9568ed261496d01c6dd1a1bc98b0eb5e`.
These identities are checked independently; the collector receives only the
executable digest. The preceding `0.4.44` archive and executable digests remain
comparison evidence and retain their separate checksum roles.

`multica_py._internal.compat` imports these constants. Client configuration
may override the bounds explicitly, while `strict`, `warn`, and `ignore`
retain their documented runtime behaviour.

For an upstream release, use the reviewed flow:

```text
collect → validate --source-checkout → render → check
```

The current v0.5.0 review uses these exact stages, in this order; collection
requires the verified release binary and writes only to ignored evidence:

```bash
uv run python scripts/upstream_contract.py collect \
  --source-checkout /absolute/pinned/v0.5.0/source \
  --binary /absolute/verified/multica-cli-0.5.0 \
  --tag v0.5.0 --version 0.5.0 \
  --commit 2df765a3c8f39789c9fb76316378bcffc20d22d9 \
  --release-id 391379076 --asset-name multica-cli-0.5.0-darwin-arm64.tar.gz \
  --sha256 e8305b68e13d7cceeaaf382723d465552a9555b6540f1899527eccb36847e094 \
  --os darwin --arch arm64 \
  --version-output /absolute/evidence/version-output.json \
  --output-dir /absolute/ignored/upstream-contract-evidence
uv run python scripts/upstream_contract.py validate \
  --approved contracts/sdk-contract.json \
  --source-checkout /absolute/pinned/v0.5.0/source
uv run python scripts/upstream_contract.py render \
  --approved contracts/sdk-contract.json \
  --runtime-output src/multica_py/_generated/approved_sdk.py \
  --transient-output /absolute/ignored/upstream-contract-render
uv run python scripts/upstream_contract.py check \
  --approved contracts/sdk-contract.json
uv run python scripts/audit_source_links.py \
  --source-checkout /absolute/pinned/v0.5.0/source
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
