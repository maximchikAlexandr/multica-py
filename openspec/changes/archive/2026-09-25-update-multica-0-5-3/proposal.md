## Why

`origin/main` now contains the approved Multica `0.5.2` SDK delivery, while the
reviewed maximum remains `0.5.2`. Stable Multica `0.5.3` leaves the public CLI and
supported response shapes unchanged but corrects the meaning of usage reported
for resumed Claude sessions, so the SDK needs a narrow, source-pinned contract,
verification, and documentation upgrade from `0.5.2` to `0.5.3`.

## What Changes

- Promote the approved target from Multica `0.5.2` release `394535503`, commit
  `d45aba1cd7582bef9210b921bbb7dc198b48e1ee`, to `0.5.3` release `395523214`,
  commit `ff8b285497809e084915016c40c2bc5e5991ffbc`, and derive the next-patch
  compatibility ceiling from that target.
- Rebuild release, source, binary, command, gap, and response evidence for the
  exact `0.5.2...0.5.3` interval. Record that all 201 public command nodes and
  all 167 approved response entrypoints retain their existing public shape.
- Preserve target-provided per-run usage for resumed Claude sessions through the
  existing task, issue, and runtime usage models without adding SDK-side baseline
  subtraction, aggregation, fields, types, operations, or dependencies.
- Add focused regression fixtures for the corrected target semantics and retain
  legacy, reset/fallback, multi-model, cache, rejected-resume, and aggregate
  compatibility behavior.
- Update direct-migration, compatibility, changelog, live-target, release, and
  packaging claims for `0.5.2 -> 0.5.3`.
- Keep PR automation, cache-hit UI calculation, daemon attribution, Telegram,
  mobile, Grok, Antigravity, attachment-viewer, localization, and other target
  changes outside the public SDK unless a separate reviewed contract authorizes
  them.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: Move the pinned target and complete command/response
  reconciliation from `0.5.2` to `0.5.3` without reintroducing `0.5.2` work.
- `sdk-surface`: Preserve corrected target-provided usage values through the
  existing public models without changing their surface.
- `verification-and-release`: Verify and publish the narrow direct patch upgrade
  atomically with reproducible offline and packaging gates.

## Impact

Implementation is limited to `contracts/sdk-contract.json`, its deterministic
generated projection, existing contract/provenance/usage fixtures, compatibility
and release documentation, and package assertions. The already merged duplicate,
supplement, property-create, and issue-list work is baseline behavior and is not
implementation scope. No new public symbol, request input, response field,
operation, dependency, migration, or backend provisioning is introduced.
