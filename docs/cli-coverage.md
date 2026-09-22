# CLI Coverage

Pinned target upstream: `multica-ai/multica@f41fae6b08fb734afcbd13205c0b3203dd0bc9c6` (tag `v0.5.1`)

The reviewed compatibility interval is `[0.4.42, 0.5.2)`: baseline `v0.5.0`
remains the direct comparison and `v0.5.1` is the maximum tested target. The
direct `v0.5.0` → `v0.5.1` reconciliation covers 194 baseline and 201 target
nodes: 192 unchanged, two changed existing nodes (`issue` and `runtime profile
create`), and seven deferred `issue wakeup` additions, with no removals,
renames, or moves.
`runtime profile --runtime-type` remains outside the typed SDK surface.

## Coverage authority

The approved contract is `contracts/sdk-contract.json`. It records reviewed
operation IDs, source references, mappings, presence semantics, validators,
and test vectors. `tests/cases/operations.py::OPERATION_CASES` is the sole
success-operation executor and retains the complete public SDK table: 164
approved operations, 81 response models, 167 response-entrypoint inventory
rows (164 unchanged and 3 changed), 37 relation IDs, and 84 contract vectors
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
