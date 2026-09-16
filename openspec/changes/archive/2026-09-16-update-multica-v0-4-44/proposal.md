## Why

The approved SDK contract and generated compatibility ceiling stop at Multica
`0.4.43`, while stable `0.4.44` changes comment deletion and adds
presence-sensitive comment and issue lifecycle behavior. A direct,
source-pinned `0.4.43` to `0.4.44` update is required so the SDK preserves
comment replies, exposes tombstones safely, and documents the target's issue
semantics without promoting extractor output into public policy.

## What Changes

- Promote the approved source target to Multica `0.4.44`, tag `v0.4.44`, exact
  commit `c7f259c70a60bff30011c403fada79ab382f608a`, release ID `389061637`,
  and compatibility interval `[0.4.42,0.4.45)`.
- Add public `Comment.deleted_at: datetime.datetime | None`; an omitted wire
  field maps to `None`, a present RFC 3339 timestamp is preserved, and explicit
  null, malformed timestamps, or wrong types fail closed.
- Retain the public comment-delete signature while adopting the target CLI's
  keep-replies route, proving descendants remain available as tombstones and a
  pre-support plain-text 404 fails without any destructive fallback.
- Retain `IssueStatus` and raw custom status keys while documenting and testing
  the target's legacy `status_category` projection: custom unstarted/started/
  done/closed phases map to `todo`/`in_progress`/`done`/`closed`, and built-in
  status keys retain their established projection and omission semantics.
- Pin `issues.update` and bound update behavior for Triage entries: any present
  `parent_issue_id`, including same-value and explicit null, returns standard
  SDK error code `issue_in_triage` with no partial mutation; ordinary issues
  retain set, clear, and omit behavior.
- Reconcile all 189 public CLI nodes and all 163 supported response entrypoints
  against exact old/target sources: no command or flag topology changes, one
  transport/error adaptation, 30 changed response rows, and 133 retained rows.
- Update the human-reviewed contract first, render only from that contract,
  extend existing frozen table-driven fixtures, document direct migration, and
  require strict OpenSpec, source-link, offline quality, packaging, and
  tracked-artifact gates. Evidence and transient renders remain untracked.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `upstream-contract`: Pin exact `0.4.44` authority, compatibility bounds,
  complete command/response reconciliation, reviewed comment and issue
  decisions, and non-SDK dispositions.
- `sdk-surface`: Add presence-correct comment tombstones while preserving the
  existing issue status type and defining lifecycle and Triage behavior.
- `subprocess-transport`: Require keep-replies comment deletion and fail-closed
  classification of the pre-support plain-text 404 without fallback.
- `verification-and-release`: Require provenance, 189-node and 163-entrypoint
  audits, deterministic generation, table-driven behavior matrices, offline
  quality, packaging, and clean-tree gates.

## Impact

Implementation will update `contracts/sdk-contract.json`, the generated
runtime, comment wire/entity adapters, existing issue/comment operation and
response case tables, compatibility/API/migration/release documentation, and
packaging/source-link assertions. It adds no dependency, command, public enum,
or SDK operation. Production code, the approved contract, generated files,
tests, docs, and main specs remain unchanged until human implementation
approval.
