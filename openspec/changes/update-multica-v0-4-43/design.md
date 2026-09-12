## Context

Planning starts from clean `origin/main` SHA
`cc467b2b4a68b57c2e66c9cff2f8176e3dd31eac`, which already contains the
approved Multica `0.4.42` delivery. Its contract targets tag `v0.4.42`, commit
`76f59f5f1cd9b6e779d0d34c603407d5d4001bf7`, release ID `385445715`, and
maximum-tested CLI `0.4.42`. The approved replacement is stable `0.4.43`, tag
commit `2ae2dbbb8f9ed9ffe1739ecf5abfe31a940ee50c`, release ID `387217464`.
The official [approved release](https://github.com/multica-ai/multica/releases/tag/v0.4.42)
was published `2026-09-09T14:00:46Z`; its Darwin ARM64 archive SHA-256 is
`a3bb48baeeb757361686978210e6195aaf50bc69edf83bf3b9c52ca3efc12e41`
and extracted executable SHA-256 is
`22abcd910562e8800c0e9db561229731e19486ec94b4815d6b1a075dc92ef36c`.
The official [target release](https://github.com/multica-ai/multica/releases/tag/v0.4.43)
was published `2026-09-11T17:23:17Z`; its archive SHA-256 is
`7d31b12d2ae94eab780cfcfdcfb7a9f43c6327c4ae54813d886410305cd26261`
and executable SHA-256 is
`b67ad1196dd62c6f59c29837db392a55a0e78a8ae2ac514ef861805eb2e19885`.
Both version JSON records identify Darwin ARM64, Go `1.26.8`, and their
respective exact commit prefixes. Release notes contain no explicit breaking,
migration, or compatibility section (`Нет данных`).

Both verified command trees have 189 nodes. No command is added, removed,
renamed, or moved; help changes on agent create/update and repo checkout.
Response review covers 160 approved operations through 163 entrypoints, with
four changed rows and 159 unchanged. The product delta is additive, but three
fields are presence-sensitive and the new starter flag is unavailable on
`0.4.42`. Repository policy makes the human-reviewed contract the sole
production generator input and requires ignored evidence, deterministic
rendering, source tracing, frozen table-driven tests, and offline release gates.

## Goals / Non-Goals

**Goals:**

- Publish one implementation-ready contract for direct `0.4.42` to `0.4.43`.
- Preserve `0.4.42` compatibility for the retained surface and expose the
  additive target data without collapsing absence, false, zero, or unknown.
- Fix public names, types, validation, failure behavior, compatibility bounds,
  and work-package dependencies before implementation begins.
- Keep generation, docs, global inventories, and package assertions atomic with
  the approved contract.

**Non-Goals:**

- Implementing production, contract, generated, test, documentation, or main
  spec changes before human approval.
- Adding a typed SDK surface for `repo checkout --fresh`.
- Adding operations from release notes or evidence that are absent from the
  approved 160-operation contract.
- Publishing a separate intermediate SDK release or promising compatibility
  with CLI `0.4.44` and later.

## Decisions

### Retain a two-patch interval with operation-level availability

The generated default interval is `[0.4.42,0.4.44)`: current main remains the
minimum and `0.4.43` becomes maximum tested. All response additions are optional
when reading `0.4.42`. Explicit starter mutations are documented as requiring
`0.4.43`; omission produces the existing `0.4.42` argv. Raising the global
minimum to `0.4.43` was rejected because the retained API remains compatible
and the change is additive. Pretending the new flag works on `0.4.42` was
rejected; capability availability is explicit in contract and docs.

### Reuse typed starter values and the repository's Unset convention

All four agent mutation forms receive
`conversation_starters: tuple[AgentConversationStarter, ...] | UnsetType =
Unset`. A tuple matches existing immutable collection inputs; one type avoids a
second builder model. `Unset` means omit, while `()` emits `[]` and therefore
sets/clears. `None` is rejected. Accepting arbitrary sequences was rejected
because it widens validation and mutation semantics without repository benefit;
using `None` for omission was rejected because upstream raw null is invalid.

Validation occurs during command construction: tuple/item shape, maximum three,
trim-nonblank label/prompt, and Unicode-code-point limits 80/4000. JSON encoding
uses `msgspec` once and preserves tuple order. Invalid input never reaches the
transport.

### Model cancellation as an immutable open actor

`TaskCancellationActor` lives beside task activity models with required open
string `type` and optional `id`/`name`; `TaskRun.cancelled_by` is optional.
Private wire state accepts omission or object, rejects null/malformed shapes,
and adapts through both `agents.tasks` and `issues.runs`. A closed enum was
rejected because upstream gives no future-value promise. A raw mapping was
rejected because it weakens typing and immutability.

### Preserve truncation as tri-state on the raw message

The private run-message wire stores `bool | UnsetType`; the public model exposes
`bool | None`, mapping only omission to `None`. Explicit null and wrong types
fail closed. Existing semantic events do not gain parallel truncation fields:
their complete `raw_message` already carries the value and participates in
duplicate equality. Defaulting absence to false was rejected because old data
cannot prove completeness.

### Add usage coverage without redefining legacy counts

The three target counters are optional nonnegative exact integers on
`IssueUsage`. Legacy `task_count` retains its established meaning; docs explain
that metered/unreported partition terminal coverage and no equality with
`task_count` is inferred. A replacement aggregate model was rejected because it
would break current callers and obscure wire provenance.

### Treat sort and error changes as semantic compatibility fixtures

`issue list --sort status` remains server-side pass-through. Target-backed
fixtures cover canonical/custom effective-category order and direction without
adding client sorting. The centralized transport classifier remains the single
error boundary; 404 task absence/workspace mismatch maps to `NotFoundError`,
while target 500 lookup failures remain internal command failures. Resource-
local diagnostic parsing was rejected because it would duplicate transport
policy.

### Freeze the approved contract before serialized domain implementation

Provenance and all reviewed mappings, presence rules, source URLs, constraints,
test references, response dispositions, compatibility bounds, and non-SDK
decisions enter `contracts/sdk-contract.json` first and pass pinned-source
validation. The agent-input, response-model, and semantic-compatibility
packages then proceed as a direct dependency chain because their established
fixtures converge on `tests/cases/operations.py` and
`tests/unit/resources/test_issues.py`. Serialization preserves repository test
organization without simultaneous writers. Generated output, global tables,
docs, and packaging have one later integration owner. Any material contract or
dependency change returns to planning revision.

## Risks / Trade-offs

- [A caller uses starters with CLI `0.4.42`] -> Contract, API, migration, and
  compatibility docs state the `0.4.43` requirement and exact omission behavior.
- [Unknown truncation is reported as complete] -> Use `Unset` at the wire,
  public `None`, and absent/false/true tests through raw and streamed paths.
- [Future actor types break decoding] -> Keep `type` as a validated open string.
- [Usage counts are conflated] -> Keep four separately named fields and assert
  differing values in fixtures/docs.
- [Shared test or generated tables cause parallel conflicts] -> Serialize all
  domain packages that write the two shared fixture files, then assign global
  inventories, generated output, docs, and packaging to one final integrator.
- [Evidence leaks into the release] -> Keep downloads, binaries, collectors,
  audits, and transient renders under ignored `.devlocal` or unique temp paths
  and audit tracked files before delivery.

## Migration Plan

1. After explicit human approval, refresh `origin/main` and record the exact
   implementation base; stop for planning revision if the contract surface or
   package topology changed.
2. Reproduce ignored target evidence and verify release/tag/archive/executable
   identities, 189/189 commands, and 163 response rows.
3. Human-review and atomically update `contracts/sdk-contract.json`; run strict
   pinned-source validation before any committed render or public edit.
4. Implement the three domain packages serially from the frozen contract.
5. Render the committed runtime only from the approved contract, reconcile
   global tables/docs/package metadata, and pass all offline/source gates.
6. Roll back by reverting contract, generated runtime, public behavior, tests,
   and docs together; never publish a mixed `0.4.43` claim.

## Open Questions

None. Public naming, input container, presence rules, open-string policy,
compatibility interval, operation-level availability, non-SDK disposition, and
delivery topology are fixed; changing one requires a planning revision.
