## Why

The SDK's approved contract and verified compatibility ceiling remain Multica
`0.7.1`, while the latest stable upstream release is `0.11.0`. A direct,
evidence-backed refresh is required so supported Python behavior matches the exact
`0.11.0` CLI and wire contracts without automatically publishing every new
upstream surface.

## What Changes

- Replace the approved upstream baseline with the exact Multica `0.11.0`
  release, commit, binary, command inventory, response review, and source links.
- Apply an explicit `retain`, `adapt`, `remove`, `defer`, or
  `not_sdk_surface` decision to every direct-range command and response item.
- Adapt approved models and operations for changed issue, project, autopilot,
  runtime, skill, text-input, cancellation, conflict, and pagination contracts.
- **BREAKING**: remove the public legacy issue-rerun mapping and expose the
  approved task-identity rerun operation instead.
- Preserve newly discovered command families as deferred unless this change
  explicitly approves them; extractor output remains evidence rather than a
  public-API generator input.
- Extend deterministic generation, table-driven offline coverage, exact-revision
  live verification, compatibility documentation, packaging, and release gates
  for the direct `0.7.1` to `0.11.0` migration.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: pin and reconcile the complete exact `0.11.0`
  upstream command and response contract.
- `sdk-surface`: define the approved typed Python adaptations, breaking rerun
  migration, presence semantics, validation, and deferred public surfaces.
- `public-cli-parity`: keep every public SDK operation traceable to an approved
  target CLI operation and disposition.
- `verification-and-release`: require deterministic generation, complete
  table-driven coverage, isolated exact-revision evidence, and safe publication.

## Impact

The implementation will update `contracts/sdk-contract.json`, its deterministic
generated projection, affected models/entities/resources/transport errors and
exports, existing test tables and fake-CLI fixtures, the existing isolated E2E
verifier and trusted live workflow, and compatibility/API/migration/release
documentation. No new runtime dependency, test framework, public chat/inbox/view/
workflow family, production deployment, or automatic release is introduced.
