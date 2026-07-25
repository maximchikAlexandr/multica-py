# CLI Coverage

Pinned upstream: `multica-ai/multica@ecbdbda09e7b2be56cd9ccc55cee1ee360222d18`

## Coverage authority

The approved contract is `contracts/sdk-contract.json`. It records reviewed
operation IDs, source references, mappings, presence semantics, validators,
and test vectors. `tests/cases/operations.py::OPERATION_CASES` is the sole
success-operation executor and retains the complete public SDK table.

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
