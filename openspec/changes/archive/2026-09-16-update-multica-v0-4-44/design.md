## Context

Planning starts from clean `origin/main` SHA
`276ef5d0e83a42ad291f1ce5b699593f8f0377ca`, which contains the approved
Multica `0.4.43` delivery. The approved replacement is stable `0.4.44`, tag
commit `c7f259c70a60bff30011c403fada79ab382f608a`, release ID `389061637`.
The baseline and target Darwin ARM64 archives have SHA-256
`7d31b12d2ae94eab780cfcfdcfb7a9f43c6327c4ae54813d886410305cd26261`
and `f300cf8036b1f596466acde35f67d986f1f75a657f77e6e0e9de1134563a76aa`;
their extracted executables have SHA-256
`b67ad1196dd62c6f59c29837db392a55a0e78a8ae2ac514ef861805eb2e19885`
and `ac26860e3f60ab6eafd4e7066d43d0fad2b0691adfefac339c4921e1dd68f774`.
Release notes contain no explicit breaking, migration, or compatibility
statement, so exact source and verified-binary review is authoritative.

Both verified command trees contain 189 public help nodes with no additions,
removals, renames, moves, flags, or argument changes. The one command behavior
change is `issue comment delete`: target CLI uses
`DELETE /api/comments/<id>/keep-replies`; a server without that route returns a
plain-text 404 and target CLI does not retry the old destructive endpoint.
Response review covers all 163 entrypoints: 30 changed issue/comment rows and
133 unchanged rows. Comments gain tombstone deletion time; issue responses
project a four-phase custom lifecycle through the retained legacy category;
Triage rejects any present parent update.

Current code already centralizes comments in `_CommentWire`, `Comment`, and
`IssueCommentResource`; issue decoding already retains wire presence and open
status strings; issue updates already distinguish `Unset`, explicit `None`, and
values. Repository policy makes `contracts/sdk-contract.json` the sole
production generator input and requires ignored evidence, deterministic
rendering, frozen table-driven tests, and offline release gates.

## Goals / Non-Goals

**Goals:**

- Publish one implementation-ready contract for direct `0.4.43` to `0.4.44`.
- Preserve older retained calls from CLI `0.4.42` while marking safe comment
  deletion as requiring CLI `0.4.44` and setting `0.4.45` as exclusive ceiling.
- Fix tombstone type/presence, lifecycle projection, Triage failure semantics,
  compatibility bounds, and delivery dependencies before implementation.
- Keep contract, generated runtime, public behavior, tests, docs, and package
  claims atomic.

**Non-Goals:**

- Changing production code, approved contract, tests, docs, or main specs
  before human approval.
- Adding a lifecycle enum, exposing server-internal status phases, or adding a
  new command, resource, relation, or dependency.
- Falling back to the destructive pre-`0.4.44` comment-delete endpoint.
- Publishing a separate SDK delivery for an intermediate version.

## Decisions

### Retain the compatibility floor and gate the changed operation

The generated interval becomes `[0.4.42,0.4.45)`: `0.4.42` remains the floor
for retained operations, `0.4.44` is maximum tested, and `0.4.45` is exclusive.
Comment tombstone fields are optional when decoding older payloads. Comment
deletion is explicitly available only with CLI `0.4.44`; it is not represented
as safe on `0.4.42` or `0.4.43`. Raising the global floor was rejected because
unchanged operations remain compatible. Treating old deletion as equivalent
was rejected because it can remove replies.

### Add one nullable public timestamp with strict wire presence

`Comment.deleted_at` is `datetime.datetime | None = None`. `_CommentWire` stores
`datetime.datetime | msgspec.UnsetType`, so omission maps to public `None` and a
present RFC 3339 timestamp is preserved. Explicit JSON null, malformed strings,
numbers, booleans, arrays, and objects raise `OutputShapeError`. A separate
public tombstone class was rejected because live and deleted rows share identity
and relation behavior. Accepting null on the wire was rejected because target
source emits omission for live rows and a timestamp for tombstones; silently
accepting a third form would weaken the reviewed contract.

Tombstones retain `id`, thread/parent context, author and revision metadata,
and replies while exposing `body == ""`. Empty body alone does not imply
deletion; only `deleted_at` does. All add/reply/list/list-flat/list-thread/
list-recent adapters reuse the same wire and entity path.

### Preserve the public delete method and prohibit fallback

The Python method and argv remain `issues.comments.delete(comment_id)` and
`issue comment delete <id>`. The approved contract changes transport semantics,
source references, minimum operation version, fixtures, and docs, not the SDK
signature. Tests prove target CLI requests keep-replies, descendants decode as
tombstones, and plain-text 404 from a pre-support server is classified through
the existing centralized error boundary. No resource-local retry or direct HTTP
implementation is added.

### Keep the legacy issue model and make projection semantics explicit

`Issue.status` remains `IssueStatus | str` behavior: known built-ins normalize
to the existing enum and custom keys remain open strings. No new public phase
enum is introduced. For target custom statuses, `status_category` remains the
legacy projection: unstarted -> `todo`, started -> `in_progress`, done ->
`done`, closed -> `closed`. Built-in keys retain their established categories.
Wire omission remains distinguishable in projection rows, `status_name` remains
the reviewed non-null string when present, and malformed category/name values
fail closed. Exposing internal phase objects was rejected because the CLI does
not promise them as a public response contract.

### Treat Triage parent rejection as a presence rule

For both eager and command, unbound and bound update paths, omitted `parent_id`
emits no parent field. A present value, same value, foreign value, or explicit
`None` emits `parent_issue_id` and target Triage responds HTTP 400 with code
`issue_in_triage`. The standard SDK exception preserves safe code/message;
tests refetch and prove no title, priority, project, assignee, description, or
parent partial write. Ordinary issues retain omit/set/clear behavior. Client-
side Triage detection was rejected because it would be stale and duplicate the
server's atomic guard.

### Freeze one foundation, then use a parallel implementation front

Provenance and every mapping, presence rule, source URL, response disposition,
compatibility bound, and non-SDK decision enter the approved contract first.
After that foundation, comment tombstones/delete and issue lifecycle/Triage can
run in parallel: their production and focused test write-zones are disjoint.
One integration owner then renders global output and reconciles shared case
tables, docs, packaging, and inventories. Verification is terminal. Any
material contract or dependency change requires planning revision.

## Risks / Trade-offs

- [A caller uses comment deletion with CLI below `0.4.44`] -> Compatibility
  metadata, preflight, and docs identify the operation-level minimum and never
  claim old destructive behavior is safe.
- [A live comment is mistaken for a tombstone] -> Only a valid present
  `deleted_at` establishes deletion; empty content is insufficient.
- [Malformed target timestamps become silent absence] -> Wire omission is the
  sole path to `None`; null and malformed values fail closed.
- [Custom lifecycle becomes a second public enum] -> Retain `IssueStatus` plus
  open strings and expose only the existing legacy category projection.
- [Triage update partially mutates other fields] -> Combined-field negative
  cases refetch authoritative state after the standard 400 response.
- [Parallel workers conflict in global tables/docs] -> Domain siblings own
  disjoint focused files; a later sole integrator owns shared registries,
  generated output, documentation, and package assertions.
- [Evidence leaks into the release] -> Keep archives, binaries, collectors,
  audits, and transient renders under ignored `.devlocal` or unique temp paths
  and audit tracked files before delivery.

## Migration Plan

1. After explicit human approval, refresh `origin/main`, record the exact
   implementation base, and stop for planning revision if contract surface or
   delivery topology changed.
2. Reproduce ignored baseline/target evidence and verify release, tag, archive,
   executable, version JSON, 189-node command inventory, and 163 response rows.
3. Human-review and atomically update `contracts/sdk-contract.json`; pass strict
   pinned-source validation before rendering or public edits.
4. Implement comment and issue packages on the parallel Stage-2 front with
   disjoint write-zones, then integrate generated output, shared inventories,
   docs, and package metadata.
5. Pass all source, offline, typing, lint, package, and clean-tree gates at one
   exact SHA. Report gated live verification separately.
6. Roll back contract, generated runtime, public behavior, tests, docs, and
   package claims together; never publish a mixed `0.4.44` claim.

## Open Questions

None. Public naming, timestamp strictness, lifecycle projection, Triage
presence behavior, compatibility interval, operation-level availability, and
delivery topology are fixed; changing any of them requires planning revision.
