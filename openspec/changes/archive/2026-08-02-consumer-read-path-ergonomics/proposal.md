## Why

An SDK service consumer still needs list-plus-N follow-up reads to discover queue candidates, cannot reconcile workspace members to issue creators, and loses issue-level attachments already embedded by `issue get`. These gaps block adoption of the relation-based SDK even though pinned Multica CLI `0.4.9` already exposes the required server-backed read paths.

## What Changes

- Add typed metadata predicates to `IssueListFilter` using the existing repeatable upstream `--metadata key=value` flag.
- Preserve `label_names` and `metadata_snapshot` on `IssueSummary` so queue and external-key discovery do not require per-issue relation loads.
- **BREAKING** Make direct `issues.list()` return the existing immutable `IssueListPage` with `IssueSummary` items instead of `BoundIssueListPage` with compact `IssueEntity` wrappers.
- **BREAKING** Make workspace, project, agent, squad, and workspace-member issue relations expose `OffsetLazyCollection[IssueSummary]`; callers use `issues.get(summary.id)` only when full issue state or bound behavior is required.
- Preserve `WorkspaceMember.id` as the workspace membership ID used by issue assignee filtering, and add `user_id` plus `email` for registry and `Issue.creator_id` reconciliation.
- Decode issue-level attachments embedded by `issue get` into both immutable `Issue.attachments` and `IssueData.attachments`, then expose the latter through a passive read-only `IssueEntity.attachments` tuple using the existing attachment result type.
- Treat omitted or empty `attachments` from pinned CLI `0.4.9` as an empty tuple. Document that the upstream endpoint also omits the field when its best-effort attachment read fails, so polling consumers retry a missing result rather than treating the read as an atomic completion signal.
- Keep explicit offset pagination, existing `download_bytes()`, entity-local relation caches, and application-owned queue/result policies; add no query framework, attachment relation loader, selection helper, global cache, or upstream Multica change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `sdk-surface`: Change issue-list result types, extend summary/member/issue attachment data, and document migration from removed list APIs.
- `bound-resource-relations`: Change the five issue-list relation item types to summaries, preserve membership identity for assignee filtering, and distinguish passive embedded attachments from lazy relations.
- `upstream-contract`: Approve the metadata flag mapping and the three reviewed response projections from pinned CLI `0.4.9`.
- `verification-and-release`: Require exact argv, decoding, presence, migration, and consumer-shaped contract coverage for the new read paths.

## Impact

- Affected SDK areas: issue/workspace wire models, immutable models, resource adapters, five offset relation loaders, approved contract/generated runtime, exports, migration docs, and table-driven tests.
- Affected consumer areas: queue discovery, external-key lookup, workspace-member registry reconciliation, and result-attachment discovery.
- Direct list and five issue relation item types change before a stable release; full issue operations remain available through `client.issues.get(summary.id)`.
- No new dependency, transport, subprocess command, cache layer, async API, or upstream server change is introduced.
