# CLI Coverage

Pinned target upstream: `multica-ai/multica@dbdbb299164347586e2650bb67684a490726a798` (tag `v0.7.0`)

The reviewed compatibility interval is `[0.6.2, 0.7.1)`: baseline `v0.6.2`
at source commit `7ab92d7622ecd81d179a8d83ae2dea74835a5069` is the direct
comparison and `v0.7.0` is the maximum tested target. The approved inventory
covers all 209 target command nodes and all 196 supported response work items.
Inherited global flags, interactive login inputs, output modes, and action
result shapes are reconciled in typed command plans and canonical vectors.
The 209-node reconciliation has 205 unchanged and four changed nodes, with
zero added or removed nodes; hidden, test-only, and dynamic-Cobra
classifications remain explicit. The SDK promotes 193 operations and 196
response entrypoints, with eight changed and 188 unchanged. Runtime list and
rename decode visibility and ordered sharing identities; update remains typed
as `RuntimeUpdateResult`. No public domain leaf
is certified only by a generic `cli:<command>` transport placeholder.

## Coverage authority

The approved contract is `contracts/sdk-contract.json`. It records reviewed
operation IDs, source references, mappings, presence semantics, validators,
and test vectors. `tests/cases/operations.py::OPERATION_CASES` is the sole
success-operation executor and retains the complete public SDK table: 193
approved operations, 98 response models, and 117 contract vectors. Target-only
wakeup lifecycle leaves are validated through the lifecycle catalog and
focused resource tests, not a second operation registry.

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
