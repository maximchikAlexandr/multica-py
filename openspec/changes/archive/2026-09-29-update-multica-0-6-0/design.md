## Context

Effective baseline — `origin/main` SHA
`c1842ae2dfcd0cc5e739b7785d3209d5e72d01ed` after merge PR #95. Its approved
contract targets Multica `0.5.3`, contains 193 operations and reviews 196
entrypoints. It already provides `IssueWakeupResource` with create/update/list/get/
disable/events, `IssueResource.wakeups`, wakeup models, timeline, and 23 other
operations absent from the older planning baseline. These existing surfaces SHALL
be adapted, not rebuilt.

Target Multica `0.6.0` is pinned to
`ea94c7cd5bbce9c8e1f28c5fa049c47ee7651d02`: 205 CLI nodes and 196 approved SDK
response entrypoints, of which 18 change and 178 remain unchanged. Approved JSON
remains the only production input to generation; collector manifests, binaries,
source checkouts and the source-augmented dynamic `checkin` fact remain evidence.

## Goals / Non-Goals

**Goals:**

- Deliver one direct `0.5.3` → `0.6.0` contract with generated interval
  `[0.5.3,0.6.1)` and exact operation/field gates.
- Reconcile all 205 CLI nodes and all 196 response entrypoints from refreshed main.
- Evolve the existing wakeup family in place, add four target-only lifecycle leaves,
  and preserve existing public names and eager/command conventions.
- Add agent-task header pagination, issue attachments and all changed response
  projections without leaking entrypoint-specific semantics.
- Reuse current validators, models, command plans and table-driven verification.

**Non-Goals:**

- Reimplementation of the six existing wakeup operations or the other 23 operations
  already merged by PR #95.
- API-only `steer_task_ids`, extractor hardening or excluded upstream UI/mobile/
  desktop/search/channel/WeCom/internal scheduler work.
- Runtime reads of evidence, tracked release assets, backend provisioning or an
  offline gate that silently requires live access.
- Updating or starting parked MYL-343 before READY, AF-SPEC-PUBLISH and human gate.

## Decisions

### 1. Refreshed approved contract is the only promotion boundary

`contracts/sdk-contract.json` SHALL move from its 193-operation/196-entrypoint
`0.5.3` baseline to exact `0.6.0` provenance. It SHALL reconcile 205 target nodes,
four added/zero removed/six changed commands, 18 changed/178 unchanged response
entrypoints, mappings, vectors and source/test references. Generation SHALL still
write only `src/multica_py/_generated/approved_sdk.py`.

Alternative — layer a delta registry over the merged contract — is rejected because
it would create two promotion authorities and could duplicate PR #95 operations.

### 2. Wakeup v2 evolves the existing resource in place

The existing `IssueWakeupResource` and `IssueWakeup` model SHALL retain create,
update, list, get, disable and events. Their decoders/models SHALL gain approved
deadline/timeout, condition, max-fire/count, pause and provenance semantics; events
SHALL gain target conditions and loop-protection mapping. Create/update SHALL extend
their current shared validator/argv builder with `expires_in_seconds`, `expires_at`,
`on_timeout`, `max_fires` and exactly one approved condition family while update
continues complete replacement and re-enables the rule.

The same resource SHALL add eager/command pairs trigger, delete, checkin and runs.
Trigger/delete use typed acknowledgement models, checkin returns
`ActionResult[None]`, and runs returns `Page[IssueWakeupRun]` from the bare array.
No parallel wakeup module or second attachment seam is introduced.

Alternative — create a new wakeup family as in graph revision 2 — is rejected
because it duplicates modules, exports and tests already present at the baseline.

### 3. Validation stops at the source-approved ownership boundary

Local validation SHALL enforce input type, nonblank, range, conflict and
required-together rules available before I/O. Workspace existence/ownership,
future-time authority, the 500-code-point checkin limit and checkin applicability
only to every/cron runs SHALL remain server-authoritative typed errors without SDK
retry. Omitted `max_fires` SHALL omit the flag and preserve the target continuous-
event default cap of `20`.

Alternative — duplicate all server validation locally — is rejected because the
SDK lacks authoritative workspace/run state and would create divergent errors.

### 4. Cursor and attachment behavior use narrow existing extension points

`AgentResource.tasks[_command]` SHALL add `limit` and `before`, keep stdout as a
bare array and extract the opaque next cursor only from the exact successful-stderr
hint. The shared task model gains optional wakeup fields, but `IssueResource.runs`
SHALL not inherit cursor behavior.

`IssueResource.update[_command]` SHALL add ordered repeatable attachment paths,
external-path opt-in, attach-only execution and a 60-second minimum effective
timeout. It delegates upload/description/attachment-ID orchestration to target CLI;
post-upload failures retain redacted uploaded IDs and are not retried.

Alternatives — change the shared page decoder or reproduce upload orchestration in
Python — are rejected because each would leak semantics or create partial states.

### 5. All 18 changed responses remain presence-aware and entrypoint-scoped

Task wakeup fields are shared by agent tasks and issue runs, with cursor limited to
agent tasks. Seven comment entrypoints decode `supplements` without synthesizing or
overwriting legacy scalar fields. Pull requests expose typed auto-complete target
status while state remains open; workspace MCP list preserves `agent_count=0`
without adding it to agent-scoped/add/update projections. Existing issue timeline
keeps its generic envelope and accepts the new wakeup action/detail domain. Six
wakeup entrypoints use the v2 model policy from Decision 2.

The task and comment wire projections both live in
`src/multica_py/_internal/wire_models.py`. They SHALL therefore be implemented by
one focused work package that is the sole writer of that file and also owns the
agent/issue/comment/PR/MCP adapters that consume those projections. Wakeup work
remains an independent sibling because its models and decoders do not edit the
shared wire file.

Alternative — closed enums or shared permissive decoders — is rejected because it
would break forward-compatible states or leak fields across entrypoints.

### 6. Verification extends merged tables and joins shared seams once

Focused work SHALL use existing resource/model files and private focused tests.
The stage-2 frontier SHALL contain the wakeup-specific writer and one combined
shared-wire response writer; splitting task and comment response changes between
parallel packages is prohibited.
Shared operation tables, public inventories, aggregate exports, contract fixtures,
docs and package claims SHALL be integrated only after focused packages complete.
No parallel fixture framework is allowed. Full acceptance includes deterministic
double render, source-link audit, strict typing/lint, complete offline tests, build,
isolated package validation and forbidden-content audit; live status is separate.

## Risks / Trade-offs

- [Merged baseline makes old task assumptions unsafe] → exact base SHA and
  193/196 inventory are gates; already present operations are retain/adapt only.
- [Cursor exists only in successful stderr] → parse only the pinned hint and keep
  stdout as the sole payload.
- [Attachment update can fail after upload] → preserve redacted IDs, document the
  partial side effect and never retry automatically.
- [Wakeup v2 crosses validators and six existing decoders] → one shared builder,
  table-driven boundary cases and exact response presence tests.
- [Comment legacy and supplement views can disagree] → decode independently and do
  not invent precedence or cross-population.
- [Open upstream action/state vocabulary grows] → preserve strings and test unknown
  future values rather than close enums.

## Migration Plan

1. Update approved provenance, inventories, mappings, 196-entrypoint verdicts and
   vectors; validate before handwritten edits.
2. Render the generated projection twice and check byte identity.
3. Adapt existing wakeup, agent, issue, comment, PR, timeline and MCP code through
   their current extension points; add the four target-only wakeup leaves.
4. Extend focused and shared tables, then synchronize public exports and consumer/
   maintainer/release documentation.
5. Run all offline/package/content gates and publish only the coherent set. Any
   failure rolls contract, generated output, handwritten code, tests and claims back
   together to exact baseline `c1842ae2…`.

## Open Questions

Нет. Baseline, public names, validation ownership, response presence policy,
exclusions, verification and rollback are fixed by this revision.
