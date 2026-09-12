## 1. Provenance and approved contract foundation

- [x] 1.1 Rebase onto the approved implementation base, verify exact old/target source commits and release IDs, and keep all checkouts, archives, binaries, evidence, gap audits, response reviews, and transient output ignored
- [x] 1.2 Verify baseline and target release archives against official manifests, verify extracted executable SHA-256 values separately, and correct the collector invocation to use each executable digest
- [x] 1.3 Reconcile all 199 baseline and 189 target Cobra nodes to the exact 166 unchanged, 21 changed, 2 added, and 12 removed classification, including every source-only/hidden/test-only name
- [x] 1.4 Reconcile all 173 response work items exactly once with old/target pinned URLs, 51 changed and 122 unchanged classifications, and reviewed model/fixture/doc actions
- [x] 1.5 Human-review and update `contracts/sdk-contract.json` atomically for target `0.4.42`, bounds `[0.4.42,0.4.43)`, complete mapping/presence/error dispositions, Plugin/autopilot removals, approved issue query options, and explicit deferred commands; run strict contract validation against the pinned target source

## 2. Core response models and adapters

- [x] 2.1 Add presence-aware private wire fields and immutable public projections for Issue `status_name`, `revision`, `last_activity_at`, and optional detail-only `source_context`
- [x] 2.2 Add Comment `revision` and omitted-versus-present `issue_revision` handling across direct, flat, recent, and thread envelopes
- [x] 2.3 Add the typed Agent conversation-starter value and optional runtime-availability projection without exposing mutable raw JSON or private runtime presence
- [x] 2.4 Reconcile TaskRun additive target context, path, status-catalog, quick-create, comment-delta, plugin-hook-tool, and per-run usage fields; remove obsolete manifest/sibling projections and preserve exact integers/immutable JSON
- [x] 2.5 Extend existing decoder/contract fixture tables for legacy, compact, null, empty, zero, malformed, and target model/envelope cases without new parallel case hierarchies

## 3. Skill and issue query surfaces

- [x] 3.1 Make `skills.get` and its command form emit `--with-content`, accept metadata-only `skills.list` rows, and preserve omission rather than fabricating empty bodies
- [x] 3.2 Add `with_content: bool = False` to skill-file list/command and bound Skill file loading, with reviewed content/size projection decoding
- [x] 3.3 Add opt-in `resolve_properties` to issue get and list while retaining the default raw UUID-keyed property map and using the separate resolved-property projection
- [x] 3.4 Add issue-list fields, repeatable property predicates, and property sort with exact target encoding, local allowlist/range/operator validation, same-name OR, cross-name AND, and `__none__`
- [x] 3.5 Repair issue list/search pagination so `has_more` is truthful, unavailable totals are not invented, and malformed/repeated/no-progress pages fail within bounded calls
- [x] 3.6 Extend shared argv, command-preview, decoder, relation, component, and type-check tables for all valid/default/invalid skill and issue query cases, including `--siblings` implying `--active` as a negative deferred-surface fact

## 4. Breaking surface removals

- [x] 4.1 Remove all `plugins.*` approved operations, bindings, generated descriptors, canonical cases, and response adapters so contract/public discovery contains no Plugin exception
- [x] 4.2 Remove Plugin resource/model/digest modules, `MulticaClient.plugins`, `Workspace.plugins` cache/loader/invalidation, and all root/submodule exports without remapping to another service
- [x] 4.3 Remove `priority` from autopilot create/update eager and command signatures, argv builders, bindings, docs fixtures, and type-check expectations; preserve all other target presence semantics
- [x] 4.4 Update the bound relation inventory to exactly 37 while preserving stable IDs R35-R38 and all property/MCP/run-history relation behavior
- [x] 4.5 Add negative import, signature, public discovery, exact argv, and migration-fixture coverage proving Plugin and autopilot priority compatibility shims are absent

## 5. Target failure and presence behavior

- [x] 5.1 Re-pin centralized validation, authentication, not-found, conflict/revision, rate-limit, unknown-command, transport, malformed-output, timeout, and local-process mappings to exact target sources and diagnostics
- [x] 5.2 Preserve actionable redacted stdout/stderr/argv detail and actual exit codes while keeping retained inline/file/stdin, agent config, custom-env, and MCP secrets out of previews and exceptions
- [x] 5.3 Add table-driven omission/null/empty/zero/false argv cases and mutually exclusive inline/file/stdin content/config/secret channel failures with zero-I/O construction proof
- [x] 5.4 Add table-driven success and failure fixtures for every semantic error class plus generic unknown diagnostics, executable absence, malformed JSON, timeout, and process-control failures

## 6. Generation, documentation, and global integration

- [x] 6.1 Deterministically render the committed approved runtime solely from the reviewed contract and compare a second ignored transient render byte-for-byte
- [x] 6.2 Reconcile operation IDs, public symbols/signatures, eager/command pairs, nested resources, relation IDs, canonical/variant counts, legacy payload counts, and generated/manual table partitions with exact equality and no allowlist
- [x] 6.3 Update compatibility and maintainer documentation with distinct archive/executable digests, correct collector arguments, exact source pins, ignored evidence locations, and `validate -> render -> check`
- [x] 6.4 Update API, migration, README, examples, and changelog for direct `0.4.28 -> 0.4.42`, Plugin/autopilot priority removals, skill projections, issue query options, deferred commands, and atomic rollback
- [x] 6.5 Update packaging/release assertions and source-link audit expectations for target `0.4.42`, exclusive upper bound `0.4.43`, removed files/exports, and pinned old/target URLs
- [x] 6.6 Confirm Git tracks no `.devlocal`, archives, binaries, collector evidence, gap/response audit output, downloads, or transient renders

## 7. Acceptance gates and delivery proof

- [x] 7.1 Run strict OpenSpec validation and approved contract validate/render/check against the exact pinned target checkout, including deterministic-render and source-link audits
- [x] 7.2 Run focused model, argv, projection, pagination, relation, removal, error, and compatibility tests, then Ruff check/format and mypy for source, tests, and scripts
- [x] 7.3 Run the complete non-live pytest/coverage gate, build and package validation, and confirm offline collection contains no live nodes
- [x] 7.4 Run authorized prepared-target `0.4.42` live-negative coverage when configured and report unavailable credentials separately without weakening offline acceptance
- [x] 7.5 Audit the final diff and clean tree for exact target/bounds, no deferred APIs, no transient artifacts, and atomic contract/generated/public/docs agreement; record command exit codes and delivery SHA

## Delivery evidence

- Integrated review-fix SHA: `3784669a5574d11efc9541dcb0ccbc53ab76a15e` (direct child of `854be7e0500f092f91e724f742d0393ef72167b4`; approved base `0442e9ad1269298a51611b87901ca86e7920c6b7` remains an ancestor).
- Contract gates: strict OpenSpec validation, pinned-source contract validation, deterministic render/check, and source-link audit completed with exit `0`; the audit covered `63` contract links and `173` response registry items.
- Quality gates: focused model/relation tests `264 passed`; Ruff format/check and mypy for source, tests/scripts, and tools completed with exit `0`.
- Delivery gates: non-live pytest `2764 passed, 2 skipped, 11 deselected`; packaging `3 passed`; build, coverage, offline live-node exclusion, `git diff --check`, and tracked-tree/transient audits completed successfully.
- Live-negative gate: `GATED / NOT RUN` because no authorized prepared Multica `0.4.42` target/profile credentials were supplied; this was reported separately and does not weaken the mandatory offline acceptance gates.
