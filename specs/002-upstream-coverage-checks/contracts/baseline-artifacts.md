# Contract: Baseline and State Artifacts

## Upstream State Artifact

The upstream state artifact separates supported, observed, and candidate
release state.

Required shape:

```json
{
  "schema_version": 1,
  "supported": {
    "version": "0.4.2",
    "tag": "v0.4.2",
    "commit": "fff23c1fc3528883ca232a475ee2aa14541d3a1c",
    "semantic_hash": "sha256:<hash>",
    "contract_ref": "tests/fixtures/provenance/supported-cli-contract.json"
  },
  "observed": {
    "version": "0.4.3",
    "tag": "v0.4.3",
    "release_id": "123456789",
    "status": "candidate-available"
  },
  "candidate": {
    "version": "0.4.3",
    "tag": "v0.4.3",
    "commit": "<40-char-sha>",
    "semantic_hash": "sha256:<hash>",
    "contract_ref": "artifacts/upstream-upgrades/v0.4.2..v0.4.3/candidate-contract.json",
    "trust_level": "verified"
  }
}
```

Validation contract:

- `supported` is the only state used by blocking offline coverage gates.
- `observed` is informational and cannot change supported coverage.
- `candidate` cannot become supported without an explicit promotion decision.
- Full 40-character commits are required for supported and candidate contracts.
- Re-observing the same release is idempotent.
- Allowed and forbidden transitions are defined in `implementation-oracles.md`;
  implementations must not invent additional transitions.

## Semantic Contract Metadata

Every semantic contract artifact carries reproducibility metadata.

Required shape:

```json
{
  "schema_version": 2,
  "baseline": {
    "state": "candidate",
    "version": "0.4.3",
    "tag": "v0.4.3",
    "commit": "<40-char-sha>"
  },
  "artifact": {
    "semantic_hash": "sha256:<hash>",
    "generator_name": "multica-py-upstream-contract",
    "generator_version": "0.1.0",
    "generator_commit": "<40-char-sha>",
    "collection_method": "binary+source"
  },
  "binary": {
    "asset_name": "multica-cli-0.4.3-linux-amd64.tar.gz",
    "sha256": "<asset-sha256>",
    "os": "linux",
    "arch": "amd64",
    "version_output": "multica 0.4.3 ..."
  },
  "observation": {
    "generated_at": "2026-07-17T00:00:00Z"
  }
}
```

Validation contract:

- Unknown schema versions are rejected.
- JSON Schema must be generated from the same typed models into
  `contracts/schema/upstream-contract-v2.schema.json`; CI validates checked-in
  contract artifacts against that schema.
- `contracts/schema/upstream-report-v1.schema.json` validates machine-readable
  reports written with `--format json --output`.
- Schema drift fails CI unless the model change and regenerated schema are part
  of the same review.
- Canonical JSON is deterministic: sorted keys where applicable, stable list
  ordering, fixed indentation, UTF-8 encoding, and trailing newline.
- Volatile observation fields do not affect semantic hash.
- Source URLs are generated from commit and source path, not duplicated as
  authoritative values in every row.
- Tag-to-commit relation is verified when release metadata is available.
- Checked-in artifacts store asset identity, basename, digest, platform, and
  normalized version output instead of absolute local executable paths.

## Promotion Decision

Promotion records why a candidate becomes supported.

Required fields:

- Candidate version, tag, full commit, semantic hash.
- Supported baseline being replaced.
- Clean offline gate reference.
- Maintainer identity or review reference.
- Explicit resolution for all breaking or potentially breaking changes.

Validation contract:

- Candidate with unresolved breaking changes cannot be promoted.
- Candidate without full provenance cannot be promoted.
- Candidate with `release-binary`, `source-only`, `local-manual`,
  `help-degraded`, or `mismatch` trust level cannot be promoted.
- Promotion is a normal reviewable repository change, not a scheduled workflow side effect.
