## Why

The approved SDK contract and maximum-tested compatibility claim stop at Multica
`0.5.0`, while stable `0.5.1` adds optional run correlation fields and seven
new `issue wakeup` CLI nodes. A direct, source-pinned `0.5.0` to `0.5.1`
upgrade is required to preserve supported response data without automatically
promoting the new wakeup family into the public SDK.

## What Changes

- Promote the approved target to Multica `0.5.1`, tag commit
  `f41fae6b08fb734afcbd13205c0b3203dd0bc9c6`, release ID `392880229`, and a
  reviewed compatibility interval `[0.4.42,0.5.2)`; preserve existing
  operation-level gates and require `0.5.1` for the two newly decoded fields.
- Add `TaskRun.wakeup_id` and `RunMessage.call_id` as optional open strings,
  preserving omission for ordinary and legacy rows and preserving all existing
  envelopes, ordering, pagination, timestamps, numeric values, errors, and
  enum openness.
- Reconcile the complete CLI inventory from 194 to 201 public help nodes: seven
  added, none removed, renamed, or moved, and only `issue` plus
  `runtime profile create` changed among existing nodes.
- Explicitly defer every `issue wakeup` leaf (`events`, `list`, `get`,
  `disable`, `create`, and `update`) from the public SDK. Their reviewed source
  mappings, replacement/re-enable behavior, retry boundary, schedule and filter
  constraints, and loop-protection guidance remain candidate evidence for a
  separately approved change; they create no operation ID, method, model, enum,
  retry, or compatibility promise here.
- Keep `runtime profile create --runtime-type` outside the SDK surface; retain
  configurable updater release sources and stricter workdir diagnostics without
  changing public signatures or response models.
- Update the human-reviewed contract first, render deterministically only from
  it, extend existing frozen table-driven fixtures, document the direct
  migration, and require strict offline, typing, lint, source-link, packaging,
  and clean-tree gates. Review evidence and transient renders remain untracked.
- Record official Darwin ARM64 archive SHA-256
  `85c5e6d8f9af4c3cfef9a6632a94b682ca09afb1e62900a8565eab5bb26a12ec`,
  extracted executable SHA-256
  `a7223c87c3da4b77afa8b0941504678c30a2770dd1d03df5f2325301360ed588`,
  and checksum-manifest SHA-256
  `cf71aab5b40ed16e89c5f826109deace7b4b92198ef1147dd1608e4aea396800`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `upstream-contract`: Pin exact `0.5.1` authority, compatibility bounds,
  complete command/response reconciliation, reviewed optional-field mappings,
  and explicit deferred or non-SDK dispositions.
- `sdk-surface`: Add optional `TaskRun.wakeup_id` and `RunMessage.call_id`
  fields without adding wakeup operations or changing legacy decoding.
- `verification-and-release`: Require provenance, 201-node and 167-entrypoint
  audits, deterministic generation, table-driven presence matrices, offline
  quality, packaging, migration, and clean-tree evidence.

## Impact

Implementation will update `contracts/sdk-contract.json`, generated runtime
metadata, task-run and run-message wire/public models, existing operation and
response fixture tables, public API and migration documentation, compatibility
claims, and package assertions. It adds no dependency and does not add an
`issue wakeup` resource, expose runtime profiles, or change production code,
tests, docs, the approved contract, or main specs until a human explicitly
approves implementation.
