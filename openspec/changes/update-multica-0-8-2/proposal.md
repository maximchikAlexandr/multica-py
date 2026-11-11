## Why

`multica-py` is currently reviewed only through Multica CLI `0.7.1`, while
stable `0.8.2` changes the public command tree, presence-sensitive inputs,
response fields, and private-project authorization behavior. The SDK needs one
reviewed `0.7.1` to `0.8.2` contract upgrade so consumers do not receive stale
argv mappings, silently dropped fields, or an automatically expanded public
surface.

## What Changes

- Reconcile all 235 target help nodes and all 196 baseline response entrypoints
  against pinned upstream source `b7f8efcaae6c5f3273c0038252b5d10c81b41068`,
  including dispositions for 27 added, 1 removed-from-help, and 18 changed
  command nodes.
- Make mandatory compatibility repairs for `issue rerun` to run-targeted
  `issue rerun-task`, issue search bounds/project filtering, pull-request
  auto-complete presence semantics, attachment/comment binding, additive model
  fields, open enums, numeric precision, and private-project fail-closed errors.
- Add reviewed typed SDK resources for the CLI-backed issue-status catalog,
  project members, workflows/project workflows, saved views, and runtime
  concurrency. These are approved additions, distinct from mandatory repairs,
  and reuse the existing client/resource/model/transport architecture.
- Keep `environment`, daemon force/watchdog controls, hidden
  `probe-runtimes`, and hidden/deprecated issue rerun outside the new public SDK
  surface until upstream help exposure or a separate process-safety design is
  approved.
- Update only the approved `contracts/sdk-contract.json` as generator input;
  regenerate deterministic runtime bindings and extend table-driven contract,
  unit, component, compatibility, documentation, and package checks.
- **BREAKING**: remove the false issue-targeted rerun mapping and replace it
  with a run-targeted typed operation; retain an explicit migration path rather
  than fabricating backward-compatible argv.
- Advance the tested compatibility envelope and release/source/checksum pins to
  `0.8.2` only after all source-link, regeneration, offline, package, and
  release gates pass.

## Capabilities

### New Capabilities

None. The additions are new typed resources inside the existing SDK surface and
do not create a parallel subsystem or transport.

### Modified Capabilities

- `upstream-contract`: require complete `0.7.1` to `0.8.2` command/response
  reconciliation, reviewed promotion, and deterministic generation from the
  approved contract alone.
- `public-cli-parity`: define the supported, adapted, retained, deferred, and
  non-SDK dispositions for every target command node and changed response.
- `sdk-surface`: add the approved typed resources/models and compatibility
  repairs while preserving explicit command methods and open-enum behavior.
- `subprocess-transport`: preserve exact argv, file/stdin channels,
  presence-sensitive flags, local-path secrecy, and sanitized error behavior
  for the expanded CLI contract.
- `verification-and-release`: require table-driven positive/negative coverage,
  source-link and byte-stability gates, independent E2E evidence, package
  checks, and exact-SHA publication.

## Impact

- Affected production areas: `contracts/sdk-contract.json`, generated approved
  bindings, client resource registration, typed models/enums, existing resource
  modules, transport error decoding, compatibility defaults, exports, and
  migration/compatibility documentation.
- Affected verification: contract/source audits, canonical operation vectors,
  unit resource case tables, fake-CLI component cases, malformed payload/error
  fixtures, live smoke and local independent walkthrough scripts, package tests,
  and existing CI jobs.
- No new dependency, transport, runtime registry, evidence store, or public
  process-control abstraction is introduced. Downloaded binaries, source
  checkouts, collected evidence, diagnostic output, and rendered visuals remain
  untracked.
