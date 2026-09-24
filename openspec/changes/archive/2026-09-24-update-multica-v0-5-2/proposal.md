## Why

The approved SDK contract and maximum-tested compatibility claim stop at Multica
`0.5.1`, while stable `0.5.2` changes already-supported issue and task response
shapes and adds atomic typed property assignment to `issue create`. A direct,
source-pinned `0.5.1` to `0.5.2` upgrade is required so the SDK preserves those
fields and exposes the new create capability without promoting unrelated REST-only
mutations.

## What Changes

- Promote the approved target to Multica `0.5.2`, release `394535503`, exact
  peeled tag commit `d45aba1cd7582bef9210b921bbb7dc198b48e1ee`, with direct
  comparison from `f41fae6b08fb734afcbd13205c0b3203dd0bc9c6` and a reviewed
  compatibility interval `[0.4.42,0.5.3)`.
- Record the official Darwin ARM64 archive SHA-256 values for `0.5.1`
  (`85c5e6d8f9af4c3cfef9a6632a94b682ca09afb1e62900a8565eab5bb26a12ec`)
  and `0.5.2`
  (`7893b31e23cb58ef897b8d44c01b736acc33786aae70aa5d167f7a674b713cc3`),
  extracted executable identities, version JSON identities, and official
  checksum sources as review-only provenance.
- Add an immutable typed duplicate reference to supported `Issue` projections.
  Legacy omission and explicit `null` decode compatibly, valid objects preserve
  `id`, `identifier`, `title`, and `status`, malformed objects fail typed
  decoding, and list projections accept `duplicate_of` in `fields`.
- Add read-only task supplement metadata to existing `AgentTask` and `TaskRun`
  projections: optional open-string `supplement_capability`, ordered
  `supplement_comment_ids`, and optional `can_supplement`, while preserving
  omission separately from empty or false values.
- Support atomic typed issue properties on `IssueResource.create` and
  `create_command` through a small immutable `IssuePropertyAssignment` input
  and repeatable `properties` tuple. Each assignment maps in caller order to
  one `--property <name-or-UUID>=<value>` argument; the pinned CLI remains the
  authority for catalog preflight, type-specific canonical JSON, archived and
  duplicate rejection, atomic create binding, and post-create snapshot checks.
- Reconcile the complete public CLI tree at `201` nodes on both versions:
  zero added, removed, renamed, or moved nodes; three changed help nodes; and
  all five source-only names classified. Reconcile all 167 supported response
  entrypoints with `response_review_complete=true`.
- Keep task-supplement REST handlers, duplicate mutation REST/UI behavior,
  duplicate timeline actions, and create-time attachment paths outside the
  public SDK surface. Negative inventory checks prevent accidental promotion.
- Update the human-reviewed contract first, render only from it, extend existing
  table-driven fixtures, document direct migration and version gating, and run
  strict offline, typing, lint, source-link, packaging, and clean-tree gates.
  Review evidence, archives, binaries, `.devlocal`, audits, and transient renders
  remain untracked.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `upstream-contract`: Pin exact `0.5.2` provenance, compatibility bounds,
  complete command/response reconciliation, approved atomic-create mapping,
  and explicit deferred or non-SDK dispositions.
- `sdk-surface`: Add duplicate issue references, task supplement metadata, the
  `duplicate_of` list projection, and typed ordered create-time property
  assignments without adding mutation or supplement operations.
- `verification-and-release`: Require provenance, 201-node and 167-entrypoint
  audits, deterministic generation, compatibility matrices, negative inventory
  checks, direct migration documentation, and offline/package evidence.

## Impact

Implementation will update `contracts/sdk-contract.json`, generated runtime
metadata, issue/task wire and public models, issue create/list mappings, existing
operation and response fixture tables, public exports, compatibility and migration
documentation, and package assertions. It adds no dependency and does not expose
task-supplement endpoints, duplicate mutations, timeline operations, or local
attachment handling. This planning branch changes only OpenSpec artifacts until
human implementation approval.
