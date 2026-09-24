## Context

Planning starts from clean `origin/main` SHA
`53f06c24264bffe770df440a492e4acabe6835a2`, which contains the approved
Multica `0.5.1` delivery. The replacement is stable `0.5.2`, release
`394535503`, exact peeled tag commit
`d45aba1cd7582bef9210b921bbb7dc198b48e1ee`; the direct source comparison is
`f41fae6b08fb734afcbd13205c0b3203dd0bc9c6...d45aba1cd7582bef9210b921bbb7dc198b48e1ee`.
The official Darwin ARM64 archives have SHA-256
`85c5e6d8f9af4c3cfef9a6632a94b682ca09afb1e62900a8565eab5bb26a12ec`
and `7893b31e23cb58ef897b8d44c01b736acc33786aae70aa5d167f7a674b713cc3`;
the extracted executables have SHA-256
`a7223c87c3da4b77afa8b0941504678c30a2770dd1d03df5f2325301360ed588`
and `9f735a52685a958b739a616ec77d3003b3665e5686609d8e050bcd6dcb279984`;
the version JSON records have SHA-256
`587cb1df67fdada00aa1da960ac869acefaaafaacd5071faa8266675ef17d133`
and `4f3bd93112beb2c90090e9a8bef396d4c72db97e1e7f377a2bf7b00bc32c03cd`.
The unsigned target tag is accepted only because the official release, asset
digest, checksum file, peeled commit, executable identity, and binary-reported
commit agree.

Both public help trees contain 201 nodes. No node is added, removed, renamed,
or moved; `issue create`, `issue list`, and `issue timeline` are the three
changed nodes. The five source-only names are stable and classified as root
normalization (`multica`), hidden (`probe-runtimes`), test-only (`repo-test`,
`test`), or parser false-positive (`x`). Response review covers all 167
supported entrypoints. Existing code already centralizes issue wire decoding,
immutable public entities, task-run adapters, exact command plans, table-driven
cases, and deterministic generation from `contracts/sdk-contract.json`.

## Goals / Non-Goals

**Goals:**

- Publish one implementation-ready contract for direct `0.5.1` to `0.5.2`.
- Preserve duplicate issue references and task supplement metadata through
  existing typed response boundaries with explicit absence semantics.
- Add one natural, ordered Python input for atomic create-time properties while
  leaving server-aware parsing and atomicity in the pinned CLI.
- Reconcile every command and supported response entrypoint with pinned source,
  deterministic generation, negative inventory protection, and offline evidence.
- Deliver contract, generated metadata, models, fixtures, documentation, and
  package claims atomically after human approval.

**Non-Goals:**

- Changing production code, the approved contract, tests, docs, or main specs on
  this planning branch.
- Adding duplicate mark/unmark methods, issue timeline support, task-supplement
  create/retry/claim/ack methods, or supplement receipt fields to existing
  comment operations.
- Adding an attachment input to issue creation or changing existing label
  post-create behavior.
- Tracking release archives, binaries, `.devlocal`, collector output, audits, or
  transient renders.

## Decisions

### Use one reviewed compatibility interval with field and operation gates

The generated default interval becomes `[0.4.42,0.5.3)`: the retained floor
remains valid, `0.5.2` is maximum tested, and `0.5.3` is the exclusive
next-patch ceiling. Existing operation minimums remain unchanged. The new
response fields and atomic property assignment carry `0.5.2` provenance; using
`properties` against an older CLI fails compatibility preflight before process
execution. Raising the global floor was rejected because retained operations and
legacy response shapes remain valid. Leaving the ceiling at `0.5.2` was rejected
because that would classify the reviewed target as out of range.

### Represent duplicate targets with a narrow immutable projection

Add `DuplicateIssueReference` to the existing issue model module with exactly
`id`, `identifier`, `title`, and open-string `status`. Add
`duplicate_of: DuplicateIssueReference | None = None` to `Issue`, backed by an
absence-aware `_IssueWire` member and the existing `_wire_presence` mechanism.
The model is a snapshot, not a lazy `Issue` relation: it has no client binding,
refresh, mutations, or implied availability of the original issue. Legacy
omission and explicit null both expose `None`, while presence provenance retains
their distinction for contract tests. Reusing the existing `IssueReference`
input alias was rejected because it represents caller input (`str | Issue`), not
a four-field wire projection. Binding a partial `Issue` was rejected because it
would imply unsupported relation and action semantics.

The list field allow-list gains `duplicate_of`, and list/get/create/update/
children/search plus bound operations all use the same decoder. Status remains
an open string so custom workflow statuses survive. A missing or inaccessible
original is represented only by the server-provided nullable snapshot; the SDK
does not hydrate or infer it.

### Extend the two existing task projections without a supplement resource

`_TaskRunWire`/`TaskRun` and `_AgentTaskWire`/`AgentTask` gain the same three
read-only members: `supplement_capability: str | None`,
`supplement_comment_ids: tuple[str, ...]`, and `can_supplement: bool | None`.
The capability remains an open string. Omitted IDs normalize to `()` while an
explicit empty array is also `()` publicly; `_wire_presence` preserves omission
versus value. Omitted `can_supplement` remains `None`, and explicit `false`
remains `False`. Existing usage, result, error, failure, cancellation, issue
delta, ordering, and serialization behavior is unchanged.

No supplement operation, enum, retry policy, or comment receipt member is added.
Creating a new supplement resource was rejected because the target has no public
CLI node for the REST-only handlers. A closed capability enum was rejected
because the server owns future values.

### Add one typed ordered input for atomic create-time properties

Add immutable `IssuePropertyAssignment(reference: str, value: str)` beside
other issue inputs. `IssueResource.create` and `create_command`, including the
project-bound delegates, gain
`properties: tuple[IssuePropertyAssignment, ...] = ()`. Each validated item
emits one `--property <reference>=<value>` pair in caller order before
`--output json`. `reference` accepts a property name or UUID and must be
nonblank after trimming; `value` must be a string and is passed verbatim after
the separator so the CLI can apply the property definition's value grammar and
type rules. Non-tuples, wrong item types, non-string values, and non-string or
blank references fail locally before transport. Empty string values,
`__none__`, comparison spellings, duplicate references, archived definitions,
unresolved names/UUIDs, invalid select/actor/date/URL/number/checkbox/multi
values, and post-create snapshot mismatch are emitted unchanged and remain
pinned CLI errors because resolving them locally would require a race-prone
catalog request and duplicate server logic.

The CLI performs configuration/capability preflight, resolves definitions,
converts every supported property type to canonical JSON, rejects duplicates,
uploads no attachment for this SDK path, and sends all resolved values in the
create request. The SDK executes one create step for property-only creation;
existing `label_ids` may still add post-create steps and therefore retain their
documented partial-label risk. A raw `tuple[str, ...]` was rejected because it
would make delimiter validation and public documentation ambiguous. A mapping
was rejected because it obscures caller order and cannot represent duplicate
negative cases. Client-side catalog resolution was rejected because it adds I/O
and weakens atomicity.

### Freeze the reviewed contract before public edits

The approved contract first records exact target identity, `[0.4.42,0.5.3)`,
201-to-201 command reconciliation, all 167 response work items, atomic property
mapping, and explicit retain/defer/not-SDK dispositions. Strict pinned-source
validation must pass before deterministic rendering or handwritten changes.
Existing frozen case tables and shared fixtures receive the new positive,
legacy, malformed, and negative rows; no parallel fixture framework or new
dependency is introduced. Production generation remains solely from the
approved contract, never from collector or audit output.

## Risks / Trade-offs

- [Consumers mistake a duplicate snapshot for a live relation] → Use the narrow
  `DuplicateIssueReference` name, no binding, and explicit read-only docs.
- [Omission collapses into null, empty, or false] → Keep wire members
  absence-aware and assert `_wire_presence` matrices for issue and both task
  projections.
- [Property validation drifts from the server catalog] → Validate only stable
  local structure and delegate value grammar, type, catalog, and
  canonicalization rules to the pinned CLI.
- [Labels make an otherwise atomic create workflow composite] → Document that
  `properties` are atomic with issue creation while legacy label attachment
  remains a separate post-create workflow.
- [REST-only features leak through shared server models] → Require negative
  operation, symbol, receipt-field, timeline, and mutation inventory checks.
- [Compatibility is overstated] → Gate new fields and create properties at
  `0.5.2`, cap at exclusive `0.5.3`, and keep older operation minimums intact.
- [Unsigned tag or evidence leakage weakens release trust] → Require all official
  identities to agree and audit tracked/package paths for forbidden evidence.

## Migration Plan

1. After explicit human approval, refresh `origin/main`, record the exact
   implementation base, and return to planning if scope or contract dependencies
   changed.
2. Reproduce release, binary, source, command, gap, and response identities in
   ignored storage; update and strictly validate `contracts/sdk-contract.json`
   before public edits.
3. Render twice to isolated destinations and require byte equality; commit only
   the deterministic runtime projection.
4. Extend issue/task wires, immutable models, adapters, list/create mappings,
   exports, and existing table-driven fixtures.
5. Update compatibility, API, migration, changelog, prepared-live guidance, and
   package assertions for one direct `0.5.1` to `0.5.2` migration.
6. Run focused and complete offline gates, report gated-live status separately,
   audit tracked/package contents, and deliver one exact implementation commit.
7. Roll back atomically to the prior `0.5.1` contract/generated/model/docs state
   if provenance, generation, decoding, create mapping, or packaging fails.

## Open Questions

None. The public property input, duplicate projection, presence behavior,
compatibility gates, and deferred surfaces are fixed by this design and are not
implementation-time choices.
