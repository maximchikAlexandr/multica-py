## Why

`multica-py` currently certifies Multica CLI `0.6.1`, while the latest stable
release is `0.7.0`. The verified upstream comparison contains additive and
changed request, response, validation, and error contracts that the SDK must
review explicitly before it can raise its compatibility ceiling. Shipping an
intermediate `0.6.2`–`0.6.5` baseline would not reduce the direct migration
risk because no intermediate SDK upgrade has been published.

## What Changes

- Replace the approved target provenance and compatibility ceiling with the
  verified Multica `0.7.0` release while retaining `0.6.1` as the effective
  migration baseline.
- Reconcile all 209 target CLI nodes and all 196 supported response work items
  in the approved contract. Four new `daemon autostart` nodes remain deferred;
  workflow-management HTTP endpoints and upstream-only internals remain outside
  the SDK surface.
- Add typed support for `multi_text` and `multi_url` property values, property
  comparison filters, nullable project workflow state, daemon CLI commit
  identity, wakeup PR-conflict conditions and diagnostics, runtime sharing and
  privacy conflicts, and the reviewed upload/network/server/workspace errors.
- Regenerate the committed approved runtime projection deterministically and
  update table-driven unit, contract, component, live, documentation, and
  packaging coverage without introducing a second registry or generator input.
- Verify the direct `0.6.1` to `0.7.0` migration through offline gates, package
  checks, and isolated live evidence on the exact candidate revision.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: approve the `0.7.0` provenance, complete command/response
  verdicts, compatibility interval, mappings, and deterministic projections.
- `sdk-surface`: expose only the reviewed property, project, daemon, wakeup,
  runtime, and error changes while retaining all unaffected operations.
- `public-cli-parity`: require a closed target inventory and explicit decisions
  for every new or changed CLI node.
- `verification-and-release`: require table-driven regression coverage, strict
  generation/source-link gates, package checks, and isolated live evidence.

## Impact

- Approved contract and generator: `contracts/sdk-contract.json`, its schema and
  `tools/upstream_contract/`, plus the generated
  `src/multica_py/_generated/approved_sdk.py` projection.
- Public types and adapters: property, issue, project, daemon, wakeup, runtime,
  workspace, agent, upload, and transport/error modules under `src/multica_py/`.
- Verification: existing case tables, fixtures, compatibility tests, live smoke,
  docs, changelog, and package/release checks.
- No new dependency, persistence layer, transport, workflow-management client,
  daemon-autostart API, or production implementation is part of this planning
  change.
