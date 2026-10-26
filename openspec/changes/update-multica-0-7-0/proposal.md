## Why

Draft PR #101 already contains the accepted Multica `0.6.2` SDK work, but it
conflicts with `main` and has not been merged. The `0.7.0` upgrade therefore
needs one consolidated remaining-delta plan that preserves exact PR #101 head
`b1c350ce22941a66871f11e0c5830a6ec542878c` as implementation evidence and
implements only behavior not already present there.

## What Changes

- Start implementation from exact PR #101 head, reconcile its conflicts with
  the eventual integration target without discarding reviewed `0.6.2` behavior,
  and advance the approved target from `0.6.2` to Multica `0.7.0`.
- Reconcile the closed 209-node CLI inventory and 196 supported response items
  against `0.7.0`, retaining the existing approved-contract-only generator and
  explicit exclusions for daemon autostart, workflow-management HTTP endpoints,
  and upstream-only internals.
- Implement only the remaining typed delta: property comparison filters,
  nullable project workflow identity and reviewed writes, PR-conflict wakeup
  conditions, runtime sharing/privacy/authorization behavior, and the new
  workspace allowlist/conflict shapes.
- Preserve PR #101 implementations of list-property values, daemon CLI commit,
  wakeup diagnostics, upload/network/server error handling, search, and project
  partial-update semantics; add regression checks rather than reimplementing them.
- Set `e2e_required=false`. Prove the remaining behavior through deterministic
  contract checks, frozen lower-level tables, component tests, package checks,
  and ordinary GitHub CI; do not require a stand, live credentials, images, or
  capture artifacts.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: make PR #101's exact `0.6.2` head the implementation
  baseline and advance provenance, inventory, mappings, compatibility, and
  deterministic projections only for the remaining `0.7.0` delta.
- `sdk-surface`: add only the reviewed property-filter, project-workflow,
  wakeup-conflict, runtime-sharing/privacy, and workspace-error behavior absent
  from PR #101.
- `public-cli-parity`: require an explicit retained/adapted/excluded decision for
  every target node and prevent already accepted `0.6.2` behavior from drifting.
- `verification-and-release`: replace live/capture gates with concrete offline,
  contract, component, package, and CI assertions at one exact candidate SHA.

## Impact

- Integration baseline: draft PR #101 / `feat/MYL-474-update-multica-0.6.2` at
  exact head `b1c350ce22941a66871f11e0c5830a6ec542878c`; the PR and branch remain
  preserved and are not modified by this planning change.
- Remaining writes: approved contract and projection, property-filter, project,
  wakeup, runtime/agent, workspace/error models and adapters, existing case
  tables, docs, package metadata, and CI verification.
- No new dependency, persistence layer, transport, workflow client, daemon
  autostart API, live-test harness, screenshot flow, or product implementation
  is part of this planning revision.
