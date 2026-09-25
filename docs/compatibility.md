# Compatibility Policy

The generated runtime constants in
`src/multica_py/_generated/approved_sdk.py` define the reviewed CLI interval:

- `TARGET_VERSION` remains the exact source checkout pinned by every source reference;
- `MIN_CLI_VERSION` and exclusive `MAX_CLI_VERSION` come from the approved compatibility block.

The current reviewed interval is `[0.4.42, 0.5.4)`. This direct `0.5.2` →
`0.5.3` migration compares baseline `0.5.2` at source commit
`d45aba1cd7582bef9210b921bbb7dc198b48e1ee` with target `0.5.3` at source
commit `ff8b285497809e084915016c40c2bc5e5991ffbc`; it does not publish an
intermediate SDK release. The target is release `395523214`. Existing
operation-level gates remain unchanged; the global `0.4.42` floor applies where
already approved. The public command and response shapes are unchanged, while
resumed Claude usage values are corrected by the target and passed through the
existing models without SDK arithmetic. Unrelated PR automation, UI, daemon,
messaging/media, mobile, localization, runtime, documentation-site, and pricing
changes remain outside the SDK.
Historical note: the superseded `0.5.0` → `0.5.1` review is retained only as
historical comparison evidence, not as the current compatibility claim.

The baseline comparison release is GitHub release `394535503`, asset
`multica-cli-0.5.2-darwin-arm64.tar.gz`: archive digest
`7893b31e23cb58ef897b8d44c01b736acc33786aae70aa5d167f7a674b713cc3`,
executable digest
`9f735a52685a958b739a616ec77d3003b3665e5686609d8e050bcd6dcb279984`, and
version-output digest
`4f3bd93112beb2c90090e9a8bef396d4c72db97e1e7f377a2bf7b00bc32c03cd`.
The target release is GitHub release `395523214`, asset
`multica-cli-0.5.3-darwin-arm64.tar.gz`. Its official archive digest is
`c41428158b87a8dba409542d55c869d5d86ca738a01ba6e0b4698b49cc94d718`, its
extracted executable digest is
`576fe10229b95a624bbdf12ae54054c5d7a58156ea4cffa41ccae6d161729565`, and its
version-output digest
`67194f3de511d86a206d7656894705352f9c555794eb6c40166247a213163d9b`.
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

The current v0.5.3 review uses these exact stages, in this order; collection
requires the verified release binary and writes only to ignored evidence:

```bash
uv run python scripts/upstream_contract.py collect \
  --source-checkout /absolute/pinned/v0.5.2..v0.5.3/source/multica \
  --binary /absolute/verified/multica-cli-0.5.3 \
  --tag v0.5.3 --version 0.5.3 \
  --commit ff8b285497809e084915016c40c2bc5e5991ffbc \
  --release-id 395523214 --asset-name multica-cli-0.5.3-darwin-arm64.tar.gz \
  --sha256 576fe10229b95a624bbdf12ae54054c5d7a58156ea4cffa41ccae6d161729565 \
  --os darwin --arch arm64 \
  --version-output /absolute/evidence/version-output.json \
  --output-dir /absolute/ignored/upstream-contract-evidence
uv run python scripts/upstream_contract.py validate \
  --approved contracts/sdk-contract.json \
  --source-checkout /absolute/pinned/v0.5.2..v0.5.3/source/multica
uv run python scripts/upstream_contract.py render \
  --approved contracts/sdk-contract.json \
  --runtime-output src/multica_py/_generated/approved_sdk.py \
  --transient-output /absolute/ignored/upstream-contract-render
uv run python scripts/upstream_contract.py check \
  --approved contracts/sdk-contract.json
uv run python scripts/audit_source_links.py \
  --source-checkout /absolute/pinned/v0.5.2..v0.5.3/source/multica
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
