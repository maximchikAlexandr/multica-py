# CLI Coverage

Pinned target upstream: `multica-ai/multica@ff8b285497809e084915016c40c2bc5e5991ffbc` (tag `v0.5.3`)

The reviewed compatibility interval is `[0.4.42, 0.5.4)`: baseline `v0.5.2`
remains the direct comparison and `v0.5.3` is the maximum tested target. The
direct `v0.5.2` → `v0.5.3` reconciliation covers 201 baseline and 201 target
nodes: all 201 retained, with no additions, removals, renames, moves, or help
changes. All 167 response entrypoints retain their wire contract; resumed
Claude usage is a target semantic correction behind existing fields.
`runtime profile --runtime-type` remains outside the typed SDK surface.

## Coverage authority

The approved contract is `contracts/sdk-contract.json`. It records reviewed
operation IDs, source references, mappings, presence semantics, validators,
and test vectors. `tests/cases/operations.py::OPERATION_CASES` is the sole
success-operation executor and retains the complete public SDK table: 164
approved operations, 81 response models, 167 response-entrypoint inventory
rows (all unchanged), 37 relation IDs, and 84 contract vectors
(70 canonical and 14 variants). The frozen operation table contains 350 cases
(190 canonical and 160 non-canonical), while 143 current payload fingerprints
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
