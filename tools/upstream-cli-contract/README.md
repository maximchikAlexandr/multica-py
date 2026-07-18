# Verified upstream CLI contract export

Maintainers need machine-readable CLI contracts with verified provenance.
Use the Python collector (never a shell wrapper):

```bash
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
```

The collector tries verified paths in fixed order:

1. Release asset `multica-cli-contract.json` bundled with the pinned CLI release.
2. Hidden exporter command: `multica __contract --format json`.
3. Help-parser fallback (degraded trust; requires checksum unless `--local-manual`).

Neither verified interface exists in upstream `multica-ai/multica` v0.4.x today.

## Upstream contribution target

Contribute to `multica-ai/multica` (preferred options):

- Add `__contract --format json` that walks the Cobra command tree and emits
  JSON matching `RawExporterPayload` in
  `src/multica_py/_internal/upstream_contract/collectors/_raw_payloads.py`.
- Or attach `multica-cli-contract.json` to GoReleaser release assets.

When working against a pinned multica checkout, implement the exporter in the
upstream repository and wire it to Cobra registration code. Do not add parallel
collect logic in this Python SDK repository.
