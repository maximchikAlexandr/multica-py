## Why

`multica-py` is approved and tested through Multica CLI `0.7.1`, while the
latest verified stable CLI is `0.8.0`. The SDK must move directly to the
verified `0.8.0` contract without treating release evidence as an automatic
public-API decision or inheriting the planning-only `0.7.2` branch as a base.

## What Changes

- Advance the reviewed upstream contract, provenance, compatibility ceiling,
  generated projection, and CI source pin from CLI `0.7.1` to `0.8.0`.
- Reconcile the complete `0.7.1..0.8.0` public command and response inventories,
  retaining unchanged operations and recording an explicit supported,
  adapted, removed, deferred, or non-SDK disposition for every delta.
- Add typed SDK support for project workflow get/set, runtime concurrency,
  task-targeted issue reruns, comment steering, and forced daemon stop through
  the existing CLI transport and eager/lazy command pattern.
- **BREAKING**: replace the removed public `issue rerun` mapping and its
  `ActionResult[None]` contract with `issue rerun-task` returning a typed task;
  remove the obsolete `issues.rerun`/`rerun_command` methods rather than
  silently routing them to behavior with different identity and output.
- Adapt issue workflow-aware status validation, literal attachment paths,
  property and skill limits, skill-source diagnostics, repository stale-cache
  warnings, and privacy/error behavior while preserving existing result
  envelopes and fail-closed decoding.
- Add nullable task-usage credits and runtime concurrency fields with explicit
  omission, null, boundary, precision, and malformed-payload behavior; keep
  provider-, model-, runtime-, and workflow-owned vocabularies open strings.
- Keep task-environment-only quick-create `--assignee-picker`, hidden commands,
  UI/provider-only changes, and unreviewed HTTP behavior outside the SDK
  surface.
- Extend table-driven unit, component, contract, packaging, documentation, and
  exact-source CI checks; keep transient collectors, binaries, audits, logs,
  screenshots, and generated evidence out of Git.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `upstream-contract`: move the only approved generation input and reproducible
  source/release provenance from `0.7.1` to `0.8.0`.
- `public-cli-parity`: classify every added, removed, hidden, changed, and
  retained CLI node and bind reviewed operations to exact CLI behavior.
- `sdk-surface`: expose the approved workflow, runtime-concurrency,
  rerun-task, steering, force-stop, usage, and diagnostic contracts through
  typed Python models and resources.
- `subprocess-transport`: preserve literal filesystem arguments and surface
  reviewed warnings/errors without shell reinterpretation, retries, or unsafe
  process termination.
- `verification-and-release`: require deterministic generation, source-link
  closure, focused regression coverage, packaging/docs checks, and independent
  exact-revision evidence for the `0.8.0` compatibility claim.

## Impact

- Affected tracked areas include `contracts/sdk-contract.json`, its schema and
  generator, generated SDK inventory, client resources/models/entities,
  table-driven fixtures and tests, compatibility/API/CLI/migration/release
  documentation, and GitHub contract/live-smoke pins.
- Existing CLI transport, `Command` abstraction, presence-aware `Unset` policy,
  msgspec decoding, sanitized exception boundary, shared case tables, and
  standard repository verification remain the implementation foundation.
- No direct HTTP client, alternate transport, new dependency, database change,
  background service, UI automation framework, or generated evidence store is
  introduced.
