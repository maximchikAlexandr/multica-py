# CLI Coverage

Pinned target upstream: `multica-ai/multica@2ea01ae4ef55de4310b99af192d2dbd367832883` (tag `v0.6.1`)

The reviewed compatibility interval is `[0.6.0, 0.6.2)`: baseline `v0.6.0`
is the direct comparison and `v0.6.1` is the maximum tested target. The
approved inventory covers all 205 target command nodes, including wakeup v2
lifecycle actions, task pagination, issue attachments, and retained public
parity families from PR #95.
Inherited global flags, interactive login inputs, output modes, and action
result shapes are reconciled in typed command plans and canonical vectors.
The 205-node reconciliation is 203 unchanged and two adapted nodes, with
zero added or removed nodes; hidden, test-only, and dynamic-Cobra
classifications remain explicit. The SDK promotes 193 operations and 196
response entrypoints, with nine changed and 187 unchanged. No public domain leaf
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
