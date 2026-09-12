## Context

Planning is pinned to `multica-py` base
`0442e9ad1269298a51611b87901ca86e7920c6b7`. Its approved contract targets
Multica `0.4.28` at `38c992ad0a757434fb51584fa34e3bc57d1b78e1`
and records binary compatibility through `0.4.38`. The approved replacement is
stable `0.4.42`, release ID `385445715`, source commit
`76f59f5f1cd9b6e779d0d34c603407d5d4001bf7`. A completed gap audit accounts
for 199 baseline and 189 target Cobra nodes and 173 SDK response work items.

The target removes the full Plugin tree and autopilot priority flags, changes
several core response models, makes skill bodies opt-in, adds issue projection
and property query flags, and adds commands with response envelopes that do not
fit current SDK methods. Repository rules require source tracing through
`RunE`, explicit five-state presence, one approved generation input,
table-driven coverage, and untracked evidence/transients. The active
`unify-sdk-operation-contracts` planning change does not alter this plan's base;
implementation must rebase and reconcile it before editing shared contract and
operation surfaces if it lands first.

## Goals / Non-Goals

**Goals:**

- Publish one coherent reviewed contract for direct `0.4.28` to `0.4.42` migration.
- Preserve existing defaults where the target remains compatible.
- Remove public promises for command paths absent at the target.
- Add only issue query options whose request and response contracts are fully reviewed.
- Make all response presence, pagination, and error behavior testable and deterministic.
- Keep contract, runtime generation, public surface, docs, and release proof atomic.

**Non-Goals:**

- Implementing this plan or editing the approved contract during planning.
- Adding `issue timeline`, `autopilot trigger-list`, or compact run-list modes.
- Inventing a Plugin replacement or deriving public API from evidence.
- Publishing intermediate SDK releases for `0.4.29` through `0.4.41`.
- Committing evidence, binaries, downloads, gap audits, or transient renders.

## Decisions

### Promote one exact target and compatibility interval

The approved contract will advance its catalog target and default compatibility
minimum/maximum-tested version to `0.4.42`; rendering produces exclusive upper
bound `0.4.43`. Old `0.4.28` source URLs remain only where needed as explicit
old-side comparison provenance, not as active operation authority. This avoids
claiming target behavior while permitting an older default CLI. Retaining
`0.4.28` as minimum was rejected because target removals make that interval
incapable of supporting one uniform public surface.

### Separate archive verification from executable identity

Release verification will check the downloaded archive against official
checksums and GitHub asset digest, then hash the extracted executable
separately. Collector `--sha256` will receive the executable digest because
`tools/upstream_contract/evidence.py` validates the executable. The docs will
name both values and stages. Reusing the archive hash for collector invocation
was rejected because it documents a command that cannot pass its identity gate.

### Reconcile inventories before changing the contract

Implementation first materializes ignored baseline/target evidence and the
reviewed 173-entry response registry, then checks the exact totals and pinned
source URLs. Only after that gate does a human-reviewed edit update
`contracts/sdk-contract.json`. Each retained/new mapping traces arity, flags,
defaults, aliases, constraints, `Flags().Changed`, destinations, response, and
errors. Cherry-picking changelog highlights was rejected because unchanged
entrypoints and removed subtrees would remain uncertified.

### Remove Plugin without replacement

All Plugin operations, models, resources, client accessors, Workspace relation,
exports, generated descriptors, tests, and docs will be removed together. The
change is explicitly breaking and the migration guide states that target
`0.4.42` offers no compatible CLI path. A deprecated method that fails at
runtime was rejected because the SDK's compatibility claim requires canonical
operations to exist. Mapping to apps or raw CLI was rejected as unapproved API.

### Remove autopilot priority at the signature boundary

`priority` is removed from create/update eager and command signatures,
generated mappings, type fixtures, docs, and cases. No ignored compatibility
parameter remains. Existing callers receive an ordinary Python signature/type
failure instead of silently dropping intent. A deprecation shim was rejected
because it would accept an option that the target cannot honor.

### Preserve skill semantics with explicit projections

`skills.get` always adds `--with-content`, preserving the current full-object
expectation. `skills.list` accepts metadata-only target rows. Skill file list
adds `with_content=False`, and the bound relation uses that default; callers
request bodies explicitly. Always requesting content for all lists was rejected
because target defaults intentionally limit payload size. Treating omissions as
empty strings was rejected because it destroys projection information.

### Support reviewed issue query flags but defer new envelopes

Issue get/list gain opt-in property resolution; list also gains fields,
repeatable property predicates, and property sort with local table-driven
validation. Defaults stay unchanged. `issue timeline`, `autopilot trigger-list`,
and `issues.runs --active/--siblings` remain deferred: the first two require new
typed domain models, and active/sibling modes return a compact capped envelope
that must not be decoded as the existing full TaskRun page. Reusing the current
adapter was rejected because it would conflate response contracts.

### Use private presence-aware wires for response evolution

Issue, Comment, Agent, TaskRun, skill, and resolved-property payloads are first
decoded into private wire models that preserve field presence, then adapted to
immutable public values. Exact integers stay integers, timestamps retain string
or approved parsed types, and arbitrary JSON is frozen recursively. Adding
per-field ad hoc defaults in public constructors was rejected because missing,
null, empty, and zero have distinct compatibility meanings.

### Keep one error-classification boundary

Target error evidence updates the existing transport classifier and fixtures;
resources do not parse stderr independently. Reviewed status/HTTP/local markers
cover validation, auth, not-found, conflict/revision, and rate limits, while
unknown failures remain generic. Secret collection/redaction occurs before
diagnostic construction. Resource-local classification was rejected because it
would drift across 173 entrypoints and weaken redaction.

### Stage implementation through conflict-free responsibility scopes

The contract/provenance foundation precedes public model and API work. After
that predecessor lands, response-model work and request-surface/removal work can
run in parallel because their production/test write zones are separated. A
single integration predecessor then reconciles generated artifacts, docs, and
global operation counts before final verification. This topology is captured
in `delivery-plan.md`; operational assignees and live status are intentionally
not stored in OpenSpec.

## Risks / Trade-offs

- [Plugin removal breaks imports and callers] -> Ship explicit migration and exhaustive negative public-surface checks in the same release.
- [The active operation-contract change lands first] -> Rebase before implementation and revise planning if its contract topology changes, rather than merging assumptions silently.
- [Projection payloads omit fields older decoders defaulted] -> Preserve presence in private wires and test omitted/null/empty cases.
- [Property options create combinatorial validation] -> Use frozen table rows for valid/invalid grouping, operators, fields, sort, and limit boundaries.
- [Full inventory review is large] -> Gate contract edits on exact machine-checked counts and one reviewed registry entry per response work item.
- [Binary/archive digest confusion recurs] -> Name both artifacts and digest roles in contract metadata, docs, fixtures, and collector examples.
- [Live target is unavailable] -> Keep source-backed offline gates mandatory and report gated live proof separately.

## Migration Plan

1. Rebase the implementation branch onto the approved integration base and
   confirm no concurrent change owns the same contract/public-surface files.
2. Reproduce ignored old/target evidence, verify both archive and executable
   identities, and freeze the command/response reconciliation registry.
3. Human-review and atomically update the approved contract, then validate it
   against the pinned target source before generating runtime changes.
4. Implement response models/projections and request/removal surfaces in the
   dependency order defined by `delivery-plan.md`.
5. Reconcile generated output, canonical counts, docs, migration, changelog,
   packaging, and complete offline gates; run gated live-negative proof when an
   authorized prepared target exists.
6. Roll back by reverting the contract, generated runtime, public API, tests,
   and docs as one unit. Do not publish a mixed target claim.

## Open Questions

None. New command families and compact run modes are explicitly deferred to
separate planning changes rather than left for implementation-time choice.
