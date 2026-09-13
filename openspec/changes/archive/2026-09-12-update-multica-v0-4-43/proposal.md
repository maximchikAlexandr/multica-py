## Why

The approved SDK contract and generated compatibility ceiling stop at Multica
`0.4.42`, while stable `0.4.43` adds one reviewed agent request input and
presence-sensitive fields to task-run, run-message, and issue-usage responses.
A direct, source-pinned `0.4.42` to `0.4.43` update is needed so callers can use
the additive target behavior without treating extractor evidence as approval or
collapsing unknown values into misleading defaults.

## What Changes

- Promote the approved source target to Multica `0.4.43`, tag `v0.4.43`, exact
  commit `2ae2dbbb8f9ed9ffe1739ecf5abfe31a940ee50c`, release ID `387217464`,
  and compatibility interval `[0.4.42,0.4.44)`.
- Add `conversation_starters` to agent create/update and command forms as
  `tuple[AgentConversationStarter, ...] | UnsetType = Unset`; omission does not
  emit the flag, `()` emits `[]` to set or clear, and `None`, malformed values,
  blank fields, more than three entries, labels over 80 code points, and prompts
  over 4000 code points fail before transport.
- Add immutable `TaskCancellationActor(type: str, id: str | None,
  name: str | None)` and optional `TaskRun.cancelled_by`, preserving an open
  actor type and rejecting malformed/null actor payloads rather than inventing
  an enum or actor.
- Add tri-state `RunMessage.output_truncated: bool | None`, where an omitted
  wire field becomes unknown (`None`) and present `false` remains distinct from
  unknown; preserve target event timestamps and the reviewed 404-versus-500
  error boundary.
- Add optional exact-integer `terminal_task_count`, `metered_task_count`, and
  `unreported_task_count` to `IssueUsage` without redefining legacy
  `task_count`.
- Retain the existing issue-list sort API while pinning fixtures and docs to
  target canonical/custom status-category ordering; retain all other reviewed
  operations and record `repo checkout --fresh` as outside the SDK surface.
- Update the human-reviewed contract first, render only from that contract,
  extend existing frozen table-driven fixtures, document direct migration, and
  require strict OpenSpec, source-link, quality, packaging, and clean-tree
  gates. Evidence, downloads, audits, and transient renders remain untracked.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `upstream-contract`: Pin exact `0.4.43` authority, the reviewed additive
  mappings, direct compatibility interval, complete command/response review,
  and explicit non-SDK dispositions.
- `sdk-surface`: Add validated conversation-starter request input and
  presence-correct cancellation, truncation, and usage projections.
- `run-event-streaming`: Preserve `output_truncated` through complete immutable
  raw messages without changing semantic event classification.
- `bound-resource-relations`: Preserve the new task-run cancellation and raw
  message fields through existing Issue/Agent/TaskRun relation paths.
- `subprocess-transport`: Pin run-message not-found and internal-failure
  classification to the target 404/500 behavior.
- `verification-and-release`: Require target provenance, compatibility,
  request/response/status-sort matrices, deterministic generation, offline
  quality, packaging, and tracked-artifact gates.

## Impact

Implementation will update `contracts/sdk-contract.json`, the generated runtime,
agent resources, issue activity models and private wires/adapters, existing
operation/response case tables, compatibility/API/migration/release docs, and
packaging/source-link assertions. No runtime dependency, command removal, or
breaking public change is introduced. Production code, the approved contract,
generated files, tests, and main specs remain unchanged until a human explicitly
approves implementation.
