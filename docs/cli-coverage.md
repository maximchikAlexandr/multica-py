# CLI Coverage

Pinned target upstream: `multica-ai/multica@ff8b285497809e084915016c40c2bc5e5991ffbc` (tag `v0.5.3`)

The reviewed compatibility interval is `[0.4.42, 0.5.4)`: baseline `v0.5.2`
remains the direct comparison and `v0.5.3` is the maximum tested target. The
approved inventory now covers the complete public command surface, including
chat history/thread, issue wakeups, repository checkout, and runtime profiles.
Inherited global flags, interactive login inputs, output modes, and action
result shapes are reconciled in typed command plans and canonical vectors.
The 166 reviewed command rows contain 165 typed public leaves and one hidden
`daemon probe-runtimes` exclusion; no public domain leaf is certified only by a
generic `cli:<command>` transport placeholder. Process-oriented leaves retain
their typed managed-process methods, while mapping and text results keep their
native result contracts.

## Coverage authority

The approved contract is `contracts/sdk-contract.json`. It records reviewed
operation IDs, source references, mappings, presence semantics, validators,
and test vectors. `tests/cases/operations.py::OPERATION_CASES` is the sole
success-operation executor and retains the complete public SDK table: 193
approved operations, 98 response models, 113 contract vectors, and 38
relation IDs. The frozen operation table contains 379 cases (219 canonical),
including 113 generated contract vectors (99 canonical and 14 variants); current
payload fingerprints guard retained response behavior.

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
