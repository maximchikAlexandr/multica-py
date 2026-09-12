## 1. Provenance and approved contract foundation

- [x] 1.1 Refresh `origin/main`, record the exact implementation base, confirm it contains the approved `0.4.42` contract, and stop for a planning revision if public scope, contract dependencies, or delivery topology changed
- [x] 1.2 Reproduce ignored `0.4.42`/`0.4.43` provenance and independently verify tag commits, release IDs, official archive manifests/digests, extracted executable SHA-256 values, and version JSON
- [x] 1.3 Reconcile the 189/189 command trees with three changed help nodes and no additions/removals/renames/moves, then reconcile all 160 approved operations and 163 unique response entrypoints to four changed and 159 unchanged rows with exact old/target source URLs
- [x] 1.4 Human-review and atomically update `contracts/sdk-contract.json` for exact target `0.4.43`, interval `[0.4.42,0.4.44)`, starter mappings/constraints/presence, changed response schemas, status/error semantics, retained operations, and non-SDK fresh checkout; pass strict pinned-source validation before rendering

## 2. Agent conversation-starter input

- [x] 2.1 Add the exact `conversation_starters: tuple[AgentConversationStarter, ...] | UnsetType = Unset` keyword to agent create/update eager and command forms without changing other signatures or omission argv
- [x] 2.2 Validate tuple/item shape, maximum three entries, trim-nonblank label/prompt, and 80/4000 Unicode-code-point limits during command construction; encode an explicit ordered tuple once as deterministic JSON and preserve `()` as `[]`
- [x] 2.3 Extend existing frozen argv/command/component/type tables for omitted, empty, valid multi-entry, malformed/non-tuple, `None`, greater-than-three, blank, and 80/81 plus 4000/4001 cases, asserting complete argv and zero executor calls on failure

## 3. Presence-aware task and usage responses

- [x] 3.1 Add immutable open-string `TaskCancellationActor`, optional `TaskRun.cancelled_by`, and private omission/object wire adaptation shared by `agents.tasks` and `issues.runs`; reject null and malformed actor shapes
- [x] 3.2 Add `RunMessage.output_truncated` through an unset-aware private wire and public tri-state model, preserve received timestamps, and prove semantic events retain the value through complete `raw_message` and duplicate comparison
- [x] 3.3 Add optional nonnegative exact-integer terminal/metered/unreported counts to `IssueUsage` while retaining independent legacy `task_count`, token, cost, and uncosted fields
- [x] 3.4 Extend existing frozen decoder, relation, streaming, contract, component, and type tables for legacy/current/malformed actor, truncation, timestamp, exact-integer, immutable-input, and divergent-count cases without changing the 37-relation topology or call counts

## 4. Retained semantic compatibility

- [x] 4.1 Add target-backed status-sort fixtures for canonical/custom effective-category ordering and direction while proving exact existing status/property/manual sort argv and no client-side reordering
- [x] 4.2 Add run-message target fixtures that distinguish task/workspace 404 from non-not-found lookup 500 through the centralized redacted classifier and distinguish malformed successful payloads from HTTP failures
- [x] 4.3 Prove all unchanged operations, envelopes, relation IDs, and public symbols remain exact, and add negative contract/discovery coverage that `repo checkout --fresh` creates no typed SDK surface

## 5. Generation, documentation, and integration

- [ ] 5.1 Render the committed runtime only from the reviewed contract and prove a second ignored render has identical relative paths and bytes
- [ ] 5.2 Reconcile generated/manual operation bindings, public signatures/exports, response adapters, canonical/variant/legacy case counts, source links, compatibility constants, and relation inventory by exact equality without allowlists
- [ ] 5.3 Update API, compatibility, migration, maintainer, release, README, example, and changelog material for direct `0.4.42 -> 0.4.43`, explicit-starter CLI availability, actor/truncation/usage semantics, status/error behavior, checksum roles, non-SDK checkout, and atomic rollback
- [ ] 5.4 Update packaging/release assertions for target `0.4.43` and exclusive `0.4.44`, then confirm Git tracks no `.devlocal`, archives, binaries, downloads, collector evidence, gap/response audits, or transient renders

## 6. Acceptance gates and delivery proof

- [ ] 6.1 Run strict OpenSpec validation, pinned-source contract validate, two-render byte equality, contract check, and exact source-link audit
- [ ] 6.2 Run focused starter/model/relation/streaming/usage/status/error/compatibility suites, then Ruff format/check and mypy for source, tests, scripts, and tools
- [ ] 6.3 Run full non-live pytest with coverage, confirm offline collection excludes every live node, and pass build plus package validation
- [ ] 6.4 Run authorized prepared-target `0.4.43` live-negative coverage when configured and report missing authorization separately without weakening offline acceptance
- [ ] 6.5 Audit the final diff and clean tree for exact target/bounds, no unapproved or non-SDK API, no transient artifacts, and atomic contract/generated/public/docs agreement; record every command exit code and exact delivery SHA
