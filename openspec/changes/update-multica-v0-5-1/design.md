## Context

Planning starts from clean `origin/main` SHA
`f3d69a0d4871e70d96a87ccfeadd34e0c97d88dc`, which contains the approved
Multica `0.5.0` delivery. The approved replacement is stable `0.5.1`, exact
peeled tag commit `f41fae6b08fb734afcbd13205c0b3203dd0bc9c6`, release ID `392880229`.
The baseline and target Darwin ARM64 archives have SHA-256
`b4bae1001c30a870c784b19123437df9f09308f750a699ce3693877ba6ffc5d1` and
`85c5e6d8f9af4c3cfef9a6632a94b682ca09afb1e62900a8565eab5bb26a12ec`;
their executables have SHA-256
`e8305b68e13d7cceeaaf382723d465552a9555b6540f1899527eccb36847e094`
and `a7223c87c3da4b77afa8b0941504678c30a2770dd1d03df5f2325301360ed588`.
The official target checksum manifest has SHA-256
`cf71aab5b40ed16e89c5f826109deace7b4b92198ef1147dd1608e4aea396800`.

Verified command evidence moves from 194 to 201 public help nodes: the
`issue wakeup` parent plus six leaves are added; none are removed, renamed, or
moved. Existing `issue` changes only by the new child, while
`runtime profile create` adds `--runtime-type` beside the legacy
`--protocol-family`. Response review covers all 167 supported entrypoints:
`agents.tasks` and `issues.runs` add optional `TaskRun.wakeup_id`,
`issues.run_messages` adds optional `RunMessage.call_id`, and 164 remain exact.
Current code already centralizes typed wire decoding, exposes both public
models, keeps table-driven operation/model fixtures, and generates compatibility
metadata only from `contracts/sdk-contract.json`.

## Goals / Non-Goals

**Goals:**

- Publish one implementation-ready contract for direct `0.5.0` to `0.5.1`.
- Preserve both optional correlation identifiers through existing typed model
  boundaries while remaining compatible with omitted legacy fields.
- Reconcile every target command and response entrypoint with pinned sources,
  explicit coverage decisions, deterministic output, and offline evidence.
- Keep the public operation inventory stable and package the contract, model,
  fixture, documentation, and compatibility updates atomically.

**Non-Goals:**

- Changing production code, approved contract, tests, docs, or main specs
  before human approval.
- Adding any `issue wakeup` SDK method, model, enum, relation, retry, or lifecycle
  abstraction in this change.
- Adding runtime-profile SDK operations, exposing updater environment controls,
  or changing existing file-channel APIs.
- Tracking release archives, binaries, collector evidence, gap/response audits,
  transient renders, or `.devlocal` content.

## Decisions

### Use one reviewed compatibility interval with field-level target provenance

The generated default interval becomes `[0.4.42,0.5.2)`: the retained `0.4.42`
floor remains valid, `0.5.1` is maximum tested, and `0.5.2` is the exclusive
next-patch ceiling. Existing operation gates remain unchanged because no
supported command signature changed. The new response fields carry `0.5.1`
provenance while omission remains valid for older compatible CLIs. Raising the
global floor was rejected because retained operations and legacy response shapes
remain supported; leaving `0.5.1` outside the tested interval was rejected
because its exact binary and source were reviewed.

### Model correlation identifiers as optional open strings

Add `wakeup_id: str | None = None` to `_TaskRunWire` and `TaskRun`, thread it
through `_task_run_from_wire`, and add `call_id: str | None = None` to the
run-message wire and public `RunMessage` path. Present strings round-trip;
omitted ordinary/legacy fields decode to `None`; invalid non-string values fail
at the existing protocol boundary. No enum or identifier wrapper is introduced
because both values are opaque server identities. A lazy wakeup relation was
rejected because it would silently promote the deferred CRUD family. Collapsing
these fields into generic metadata was rejected because upstream now provides
stable named response fields on already supported operations.

### Defer every issue wakeup command as one inseparable policy boundary

All seven nodes remain explicit `defer`: parent `issue wakeup` and leaves
`events`, `list`, `get`, `disable`, `create`, and `update`. The pinned CLI
mapping is preserved as evidence:
`agent-id→agent_id`, `instruction|instruction-file→instruction`, `kind→kind`,
`mode→mode`, `event→event_types`, `filter-agent-id→filter_agent_id`,
`filter-actor-type→filter_actor_type`, `filter-actor-id→filter_actor_id`,
`task-id→filter_task_id`, `parent→parent_comment_id`, `at→at`,
`after→after_seconds`, `every→interval_seconds`, `cron→cron_expression`, and
`timezone→timezone`. Authoritative sources are target
`server/cmd/multica/cmd_issue_wakeup.go` lines 18–175,
`server/internal/service/issue_wakeup.go` lines 30–155, and
`server/internal/handler/issue_wakeup.go` lines 105–250.

Deferral keeps unresolved public-policy decisions together: instruction
trim/size and inline/file channels; open or closed kind/event/mode enums;
actor/task/filter exclusivity; event versus schedule constraints; positive
whole-second duration ranges; absolute, interval, and cron scheduling;
timezone validation; `get` list-then-local-select behavior; update as complete
replacement plus re-enable; the create-only 250 ms retry for HTTP 409
`wakeup_source_busy`; ambiguous transport failure handling; and event
loop-protection guidance. Supporting only read leaves was rejected because it
would create models and lifecycle promises before write/update semantics are
approved. Supporting the whole family now was rejected because the issue asks
for a compatibility upgrade and evidence alone cannot approve new SDK surface.

### Keep runtime profile and source-only hardening outside public changes

`runtime profile create --runtime-type` remains `not_sdk_surface` because the
approved contract contains no runtime-profile operations. The environment-
configurable release source used by `update` and stricter workdir
canonicalization/diagnostics remain `retain`: existing SDK signatures and
outputs do not change. Adding profile operations or surfacing environment
variables was rejected as unrelated scope expansion.

### Freeze the reviewed contract before model, fixture, and documentation edits

The approved contract first records exact target identity, compatibility,
194-to-201 command reconciliation, all retained/deferred/non-SDK dispositions,
and the 167-entrypoint response audit. Strict pinned-source validation must pass
before deterministic rendering or handwritten public changes. Existing frozen
case types and shared fixtures receive present, omitted/legacy, and malformed
rows; no parallel fixture framework is added. The same commit updates generated
metadata, models/adapters, tests, docs, migration, live-target guidance, and
package assertions. Generating from collector evidence or implementing first
was rejected because it bypasses the repository's approval boundary.

## Risks / Trade-offs

- [A caller sees `wakeup_id` and assumes wakeup CRUD exists] -> Document the
  identifier as opaque correlation only and assert wakeup methods are absent.
- [Omission is collapsed into an invalid required field] -> Keep defaults at
  `None` and cover present plus omitted legacy payloads on both task-run paths.
- [`call_id` disturbs stream ordering or truncation semantics] -> Add the field
  only to row decoding and assert sequence plus tri-state `output_truncated`
  behavior unchanged.
- [Deferred candidates leak into generation] -> Require explicit deferred rows,
  negative public-inventory guards, and contract-only deterministic rendering.
- [Compatibility is overstated beyond reviewed source] -> Cap the interval at
  exclusive `0.5.2` and preserve exact operation minimums.
- [Unsigned annotated tag weakens provenance] -> Record it explicitly and
  require agreement among peeled commit, official release assets, checksums,
  executable identity, and version output.
- [Evidence leaks into Git or packages] -> Audit tracked/package paths and keep
  binaries, collectors, audits, and transient renders ignored or external.

## Migration Plan

1. After explicit human approval, refresh `origin/main`, record the exact
   implementation base, and return to planning if source scope or contract
   dependencies changed.
2. Reproduce release, binary, source, command, gap, and response identities in
   ignored storage; update and strictly validate `contracts/sdk-contract.json`
   before public implementation.
3. Render the generated runtime twice and require byte equality; then extend the
   two wire/public model paths and existing table-driven fixtures.
4. Update compatibility, README/API/migration/changelog/live-target guidance,
   and package assertions as one direct `0.5.0` to `0.5.1` migration.
5. Run focused and complete offline gates, report gated-live status separately,
   audit the clean tracked/package contents, and deliver one exact commit.
6. Roll back atomically to the prior approved contract/generated/model/docs
   commit if provenance, deterministic generation, decoding, or packaging fails;
   do not leave a partially raised compatibility claim.

## Open Questions

None. Public support for `issue wakeup` requires a separate planning change and
explicit human approval; it is not an implementation-time choice in this plan.
