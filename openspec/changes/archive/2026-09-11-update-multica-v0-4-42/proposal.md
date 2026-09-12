## Why

The approved SDK contract still targets Multica `0.4.28` and certifies binary
compatibility only through `0.4.38`, while stable `0.4.42` removes an entire
public CLI family and changes command, projection, pagination, and response
contracts used by the SDK. A single source-traced review of `0.4.28` through
`0.4.42` is required so generated behavior remains governed by the approved
contract rather than by extractor output or stale fixtures.

## What Changes

- Promote the reviewed source target to Multica `0.4.42`, exact commit
  `76f59f5f1cd9b6e779d0d34c603407d5d4001bf7`, and set the minimum and
  maximum-tested CLI version to `0.4.42`, while retaining separate release,
  archive, and extracted-binary provenance.
- Reconcile all `199` baseline and `189` target Cobra nodes and all `173`
  SDK response work items against exact old and target source references.
- Adapt Issue, Comment, Agent, TaskRun, skill-content, issue-list, service-tier,
  update-presence, pagination, and failure mappings without promoting
  unreviewed extractor suggestions.
- Add opt-in issue property filtering, projection, resolved-property output,
  and property sorting to the existing issue list/get surface while preserving
  existing defaults.
- **BREAKING** Remove the SDK Plugin resource, bound plugin relation, models,
  contract operations, exports, and documentation because Multica `0.4.42`
  has no public `plugin` command tree and no compatible replacement.
- **BREAKING** Remove the unsupported `priority` inputs from autopilot create
  and update operations; preserve safe redacted autopilot reads.
- Preserve full skill-get behavior by explicitly requesting content; make
  skill-file content retrieval an explicit opt-in projection and keep skill
  lists metadata-only.
- Keep `issue runs` default history compatible and defer `--active` /
  `--siblings`, `issue timeline`, and `autopilot trigger-list` to separately
  approved response-model changes.
- Correct compatibility documentation so release-archive SHA-256 and extracted
  executable SHA-256 are distinct inputs, and keep evidence, downloads, audit
  reports, and transient renders untracked.
- Add table-driven positive and negative coverage, migration guidance,
  packaging/release checks, exact source-link audit, and deterministic
  `validate -> render -> check` gates.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `upstream-contract`: Promote the exact `0.4.42` authority, reconcile the
  complete CLI/response inventories, separate archive and binary identities,
  and keep approval as the sole generation gate.
- `sdk-surface`: Adapt reviewed response models and projections, add explicit
  issue property query options, and remove unsupported Plugin symbols.
- `plugin-resource`: Remove the public Plugin capability because its complete
  upstream command hierarchy is absent at the target.
- `property-resource`: Extend issue list/get with reviewed property filters,
  resolution, projection, and sorting semantics.
- `autopilot-resource`: Remove unsupported priority inputs while retaining
  redacted reads and existing trigger behavior.
- `bound-resource-relations`: Remove `Workspace.plugins` and preserve default
  issue-run relation semantics without adopting the compact active-run envelope.
- `subprocess-transport`: Re-pin validation, conflict, authentication,
  not-found, rate, transport, and local-process failure classification to the
  target CLI without weakening redaction.
- `verification-and-release`: Require full inventory, projection, presence,
  pagination, error, documentation, packaging, and clean-tree verification for
  the direct `0.4.28` to `0.4.42` migration.

## Impact

Implementation will update the approved contract and its generated runtime,
public resources/models/entities and exports, typed decoders, operation tables,
contract/component/live-negative fixtures, compatibility/API/migration docs,
and release checks. Plugin consumers and callers passing autopilot priority
must migrate; no replacement Plugin API is claimed. There is no new runtime
dependency, no intermediate SDK release for `0.4.29` through `0.4.41`, and no
production change is authorized by this planning set before human approval.
