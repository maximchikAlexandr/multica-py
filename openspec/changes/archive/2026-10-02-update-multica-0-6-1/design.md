## Context

Effective SDK baseline is exact `origin/main` commit
`48745d2fe9e80ee9c027293ef22971ff5723f5f5`, tree
`3afc72c975052cfb92506e5d20df95a5b925da92`. It already targets Multica
`0.6.0`, exposes 193 approved operations and audits 196 response entrypoints.
`Issue.duplicate_of` is already an immutable optional projection; direct and
bound update/status methods already share the issue adapter and shell-free command
plan. Target `0.6.1` keeps 205 CLI nodes, changing only `issue status` and
`issue update`, and changes semantics for nine supported response entrypoints.

The approved JSON contract remains the only production generator input. Official
archives, binaries, upstream source checkout and `.devlocal` collector/audit files
are review-only. The planning issue requires a direct `0.6.0 → 0.6.1` migration,
strict offline gates and no implementation before independent review/human approval.

## Goals / Non-Goals

**Goals:**

- Deliver one exact-provenance contract with compatibility `[0.6.0,0.6.2)`.
- Add `duplicate_of` consistently to direct/bound update and status APIs while
  reusing the existing issue response projection.
- Enforce all SDK-owned conflicts before transport/upload and delegate
  reference resolution plus response verification to CLI `0.6.1`.
- Reconcile 205/205 CLI nodes and 196/196 response entrypoints, including
  compatible quota, usage and checkout semantics.
- Extend current tables, docs, generation and packaging gates without new
  dependencies or fixture architecture.

**Non-Goals:**

- New duplicate-management operation, duplicate model, price table or repository
  checkout implementation.
- Promoting GPT catalog labels, UI/chat changes, server performance or daemon
  internals into SDK surface.
- Fixing the dynamic-Cobra collector parser defect in this release plan.
- Tracking evidence, release assets, transient renders or the visual explanation.
- Starting implementation or creating implementation/WP issues before READY and
  human approval.

## Decisions

### 1. The existing issue mutation seam owns duplicate transitions

All four eager/command direct/bound pairs receive the same optional keyword
`duplicate_of: str | None = None`. `None` means omitted; nonblank strings map to
one `--duplicate-of`. Existing `Issue.duplicate_of` remains the only result model.
Only calls using the new flag require CLI `0.6.1`.

Alternative — introduce `mark_duplicate()` plus a second model — is rejected:
upstream exposes flags on existing mutations, and a parallel API would duplicate
validation, binding and response decoding.

### 2. Update/status validation mirrors observable CLI rules before I/O

`set_status` accepts the flag only with `cancelled`. `update` accepts omitted or
`cancelled` status and rejects other statuses. Any emitted description or
attachment conflicts before command execution; present inline description remains
present even for `None`/empty. Upstream file/stdin conflicts remain contract facts,
not new public parameters. Attachment paths may be normalized/validated, but no
conflicting plan may upload or mutate.

Alternative — let CLI reject every conflict — is rejected because attachment
workflows can create partial side effects and the SDK already owns pre-I/O input
validation. Alternative — broaden update with new file/stdin parameters — is
rejected because `0.6.1` does not require that public expansion.

### 3. CLI owns reference resolution and compatibility verification

The SDK emits the reviewed flag and decodes the returned existing Issue. CLI owns
reference resolution, request body construction and the fail-closed check that a
successful server response contains `duplicate_of`. The SDK uses the centralized
typed/redacted process-error boundary, with no retry, synthesis or secondary read.

Alternative — resolve references or verify through an extra SDK command — is
rejected because it duplicates CLI authority and can race or repeat mutation.

### 4. Compatible response semantics extend fixtures, not architecture

`TaskRun.failure_reason` stays open string; provider quota becomes another fixture.
Usage continues to preserve server integer ticks and uncosted buckets without local
pricing. Repository checkout keeps its path result and centralized error handling;
junction/containment behavior remains CLI-owned. The response registry records nine
changed semantics and 187 pinned unchanged entrypoints.

Alternative — closed failure enums, embedded price policy or platform-specific
path logic — is rejected as duplicative and less forward-compatible.

### 5. One contract foundation precedes one coherent implementation surface

Implementation first updates provenance, inventories, mappings, response audit and
generated projection. Handwritten changes then extend the existing issue resource,
bound entity and shared table-driven evidence, followed by docs and full release
gates. The package is small and shares aggregate fixtures/docs; estimate authority
will select the final delivery topology after the complete package is sized.

Alternative — predeclare parallel packages before estimating — is rejected because
the authoritative threshold and shared write zones decide whether a DAG is legal.

## Risks / Trade-offs

- [Presence-sensitive update values collapse accidentally] → use `Unset` for
  existing update fields, complete expected argv and cases for `None`/empty/omitted.
- [Attachment conflict creates partial upload] → reject before executor calls and
  assert zero transport/upload activity.
- [Older CLI sees an unknown flag] → set operation-level minimum `0.6.1` only when
  `duplicate_of` is present; omission keeps baseline behavior.
- [Server accepts mutation but omits duplicate snapshot] → surface one CLI
  compatibility error and never retry or synthesize.
- [Pricing fixtures become copied policy] → assert decoded server values and
  uncosted categories only; never encode upstream prices.
- [Windows-specific path behavior is overclaimed] → retain portable SDK success/
  error boundaries and use source-pinned compatibility evidence.

## Migration Plan

1. Update exact baseline/target provenance, 205-node inventory, four adapted
   operation mappings, full 196-entrypoint audit and compatibility interval.
2. Validate the approved contract, render the generated projection twice and
   require byte-identical output before handwritten edits.
3. Add `duplicate_of` to existing resource/bound signatures and validators; extend
   current operation/response fixtures and focused zero-I/O/error tests.
4. Synchronize README/docs and release/package claims, then run all offline gates
   and record live status separately.
5. Publish one coherent implementation commit/PR only after approval. On any gate
   failure, revert contract, projection, code, tests and docs together to exact
   baseline `48745d2fe9e80ee9c027293ef22971ff5723f5f5`.

## Open Questions

Нет. Public argument name, omission/conflict policy, validation ownership,
compatibility interval, exclusions and rollback are fixed by this design.
