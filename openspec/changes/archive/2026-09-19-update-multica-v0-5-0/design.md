## Context

Planning starts from clean `origin/main` SHA
`bc1c1609963b219ffcb2f9466f33aa3434f570a6`, which contains the approved
Multica `0.4.44` delivery. The approved replacement is stable `0.5.0`, exact tag
commit `2df765a3c8f39789c9fb76316378bcffc20d22d9`, release ID `391379076`. The
baseline and target Darwin ARM64 archives have SHA-256
`f300cf8036b1f596466acde35f67d986f1f75a657f77e6e0e9de1134563a76aa` and
`b4bae1001c30a870c784b19123437df9f09308f750a699ce3693877ba6ffc5d1`;
their executables have SHA-256
`ac26860e3f60ab6eafd4e7066d43d0fad2b0691adfefac339c4921e1dd68f774` and
`e8305b68e13d7cceeaaf382723d465552a9555b6540f1899527eccb36847e094`.

Verified command evidence moves from 189 to 194 public help nodes: comment
update and four skill-label nodes are added, none are removed, renamed, or
moved, and three existing label commands change inputs. Response review covers
163 SDK entrypoints: six changed and 157 unchanged. Current code already has
centralized command/error handling, `Unset` for patch presence, typed label and
skill entities, bound skill-file relations, open task failure strings, and
table-driven operation fixtures. Repository policy keeps
`contracts/sdk-contract.json` as the only production generator input.

## Goals / Non-Goals

**Goals:**

- Publish one implementation-ready contract for direct `0.4.44` to `0.5.0`.
- Approve public naming, typing, presence, error, and compatibility decisions
  for every changed SDK-relevant surface.
- Reconcile all 194 command nodes and 163 response entrypoints with exact source
  evidence and deterministic generated output.
- Preserve offline verification and atomic contract/runtime/API/docs/package
  delivery.

**Non-Goals:**

- Changing production code, approved contract, tests, docs, or main specs
  before human approval.
- Exposing CLI stdin/file content channels, server-only phase objects, internal
  UI/daemon/IM changes, or generated evidence as public SDK behavior.
- Automatically retrying stale comment edits or cascading runtime deletion.
- Publishing separate SDK deliveries for intermediate versions.

## Decisions

### Use one reviewed compatibility interval with operation gates

The generated default interval becomes `[0.4.42,0.5.1)`: the retained `0.4.42`
floor remains valid, `0.5.0` is maximum tested, and `0.5.1` is the exclusive
next-patch ceiling. Comment update, skill-label operations, label resource-type
and description inputs, and newly decoded target fields require `0.5.0` where
operation-level gating applies. Raising the global floor was rejected because
retained operations remain compatible. Treating the semver-major transition as
an unbounded claim was rejected because only the pinned target was reviewed.

### Expose comment editing as a text-only optimistic mutation

The public surface is
`issues.comments.update(comment_id, body, *, expected_revision, options=None)`
and its lazy `_command` twin. `expected_revision` is an exact positive,
non-boolean integer validated before transport. The SDK always emits
`--content <body> --expected-revision <n>`; it does not expose stdin or file
channels, so channel exclusivity and external-file hazards are eliminated at
the public boundary. The target `Comment` is decoded on success. A stale
revision remains the centralized conflict error; there is no hidden read/merge,
retry, attachment mutation, or suppression of upstream mention retriggering.
Mirroring every CLI content channel was rejected because it adds no SDK
capability and would duplicate file-safety policy.

The approved canonical invocation vector SHALL bind only `comment_id` and
`body` positionally and SHALL pass `expected_revision=3` through the vector's
keyword arguments. Its expected argv remains `issue comment update cmt_1
--content revised --expected-revision 3 --output json`. A vector that expects
that argv while omitting the keyword argument is invalid and SHALL fail contract
validation before any public implementation is accepted.

### Reuse Label and add one typed skill-label resource

Every bound `Skill` exposes one public `labels` shape:
`LazyCollection[Label]`. A `skills.list` response SHALL seed that collection
from its required `labels` array, including `[]`, so the first and subsequent
reads reuse the preloaded empty or populated tuple without another CLI call.
Skill detail retains its established wire contract: when `skills.get` omits
`labels`, the same collection starts unloaded and its first read executes only
the approved `skills.labels.list` operation. This keeps list and detail objects
substitutable while preserving operation-specific payload semantics; a
list-only public tuple and a differently typed bound relation were rejected.
Each nested row uses the reviewed Label shape.

`client.skills.labels.list/add/remove` returns `Page[Label]` for list/add and
for the successful remove refresh; when upstream remove succeeds but refresh
fails, remove returns `ActionResult[None]` with the approved detached fallback
instead of fabricating a label page. Successful add/remove invalidates the
bound collection cache. A separate `SkillLabel` type was rejected because
upstream returns the same label identity, name, color, description, and
resource type.

### Make label scope an open-safe reviewed enum and description presence-aware

Add public `LabelResourceType` values `ISSUE="issue"` and `SKILL="skill"` and
retain decoding of future response strings as open values where the project
already follows open-enum policy. `Label` gains nullable `description` and
`resource_type`. Create accepts `resource_type=ISSUE` by default and optional
non-empty description. List accepts an optional resource-type filter while
omission preserves the server's issue default. Update accepts
`description: str | None | UnsetType`: `Unset` omits the flag, `None` and `""`
both emit an explicit empty `--description` to clear, and a non-empty string
sets it. A plain optional argument was rejected because it cannot distinguish
omit from clear.

### Decode task state deltas by presence and keep failure reasons open

Task-run wire models preserve omission independently for current issue title,
description, status, and assignee and for known/delta markers. Absent delta
means unavailable; `known=true` with an empty array means a known empty delta.
Changed strings and current status/assignee decode without collapsing omission
to null. `failure_reason` remains an open string and explicitly accepts
`runtime_access_denied` and future values; no closed SDK enum is introduced.
Collapsing all absent/null/empty forms was rejected because it loses target
meaning.

### Validate OMP model/thinking combinations before transport

Agent create/update shares one validation rule: a supplied thinking level
requires an effective model. Create has no prior state, so the model must be
supplied. Update may use an explicitly supplied model or a retained effective
model only when the resource has authoritative model state; explicit clear plus
thinking fails. Runtime changes do not bypass the rule. Every invalid
combination fails before CLI execution, and component cases prove no partial
mutation. Deferring wholly to the server was rejected because this SDK already
validates deterministic input constraints before transport.

### Preserve structured runtime-delete guidance without automation

The centralized error decoder retains status/code/message and optional blocker
counts, timestamps, profile identity, and cleanup guidance from target 409 JSON.
Legacy proxy/plain bodies remain ordinary `ConflictError` messages. The SDK
never adds `--cascade`, retries deletion, or performs cleanup automatically;
online, offline, and profile-backed blockers are data for the caller. A
runtime-specific exception hierarchy was rejected because the established
error boundary can preserve the structured context without changing catch
behavior.

### Freeze the reviewed contract before all public edits

Exact command arity, aliases, local/persistent flags, defaults, required and
conflict rules, presence semantics, destinations, response shapes, source URLs,
compatibility gates, and non-SDK dispositions enter the approved contract
first. Strict pinned-source validation must pass before deterministic rendering
or handwritten public changes. The six changed responses receive targeted
fixtures; the remaining 157 retain exact equality evidence. Any material public
or dependency correction returns to planning revision.

## Risks / Trade-offs

- [A caller assumes comment update merges automatically] -> Require the
  revision, preserve the stale conflict, and document explicit read/merge.
- [Skill list and detail accidentally converge] -> Keep one public
  `LazyCollection[Label]` while operation-specific wire fixtures prove that
  list preloads required labels and detail leaves the relation unloaded.
- [Description clear is collapsed into omission] -> Keep `Unset` distinct from
  `None`/empty and assert complete argv.
- [Unknown failure reasons break decoding] -> Keep failure reason open and test
  both `runtime_access_denied` and an unknown future value.
- [OMP validation uses stale state] -> Only treat bound authoritative state as
  effective; otherwise require explicit model and retain server atomicity tests.
- [Structured runtime guidance causes destructive automation] -> Preserve data
  only; prohibit cascade/retry in requirements and tests.
- [Evidence leaks into release] -> Keep binaries, collectors, audits, and
  transient renders under ignored `.devlocal` or unique temporary paths and
  audit tracked files before delivery.

## Migration Plan

1. After explicit human approval, refresh `origin/main`, record the exact
   implementation base, and stop for planning revision if scope changed.
2. Reproduce ignored `0.4.44`/`0.5.0` evidence and verify releases, tags,
   archives, executables, version JSON, 189-to-194 nodes, and 163 responses.
3. Human-review and atomically update `contracts/sdk-contract.json`; pass strict
   pinned-source validation before rendering or public edits.
4. Implement the reviewed models/resources/relations and extend existing frozen
   operation, decoder, component, and contract tables.
5. Render twice, reconcile exact inventories, update docs/package claims, and
   pass strict OpenSpec, source-link, Ruff, mypy, non-live pytest, and build
   gates at one clean SHA.
6. Roll back contract, generated runtime, public behavior, tests, docs, and
   package claims together; never publish a mixed `0.5.0` claim.

## Open Questions

None. Public naming, typing, content channel, optimistic concurrency,
skill-label relation behavior, label clear semantics, task presence policy,
OMP validation, runtime conflict handling, compatibility interval, and
verification scope are fixed; changing any requires a planning revision.
