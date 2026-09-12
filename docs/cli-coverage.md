# CLI Coverage

Pinned target upstream: `multica-ai/multica@2ae2dbbb8f9ed9ffe1739ecf5abfe31a940ee50c` (tag `v0.4.43`)

The reviewed compatibility interval is `[0.4.42, 0.4.44)`: baseline
`v0.4.42` remains supported and `v0.4.43` is the maximum tested target. The
target command tree retains 189 nodes (186 unchanged, 3 changed, no additions,
removals, renames, or moves), and `repo checkout --fresh` remains outside the
typed SDK surface.

## Coverage authority

The approved contract is `contracts/sdk-contract.json`. It records reviewed
operation IDs, source references, mappings, presence semantics, validators,
and test vectors. `tests/cases/operations.py::OPERATION_CASES` is the sole
success-operation executor and retains the complete public SDK table: 160
approved operations, 81 response models, 163 response-entrypoint inventory
rows (159 unchanged and 4 changed), 37 relation IDs, and 79 contract vectors
(66 canonical and 13 variants). The frozen operation table contains 343 cases
(184 canonical and 159 non-canonical), while 143 current payload fingerprints
guard unchanged response behavior.

## Maintainer flow

Use `collect` for read-only source evidence, then review the approved contract
and run `validate --source-checkout`, `render`, and `check`:

```text
collect → validate --source-checkout → render → check
```

`src/multica_py/_generated/approved_sdk.py` is the only committed generated
runtime projection. `docs/approved-sdk.md`, `reports/compatibility.json`, and
`reports/provenance.json` are transient render outputs. Evidence and review
items are also transient and cannot change public SDK behaviour.
