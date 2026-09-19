## 1. Provenance and approved contract foundation

- [x] 1.1 Refresh `origin/main`, record the exact implementation base, reproduce ignored `0.4.44`/`0.5.0` evidence, and independently verify tag commits, release IDs, official archive manifests/digests, executable SHA-256 values, and version JSON
- [x] 1.2 Reconcile the 189 baseline and 194 target public command nodes, proving five additions, zero removals/renames/moves, all changed label flags, exact arity/aliases/defaults/constraints/presence/secret channels/destinations, and positive/negative references
- [x] 1.3 Reconcile all 163 unique response work items to six changed and 157 unchanged rows with exact old/target source URLs and no duplicate or missing work-item IDs
- [x] 1.4 Human-review and atomically update `contracts/sdk-contract.json` for target `0.5.0`, interval `[0.4.42,0.5.1)`, operation gates, public naming/types, retained operations, and non-SDK dispositions
- [x] 1.5 Pass strict pinned-source contract validation and tracked-evidence audit before rendering or changing public behavior

## 2. Comment update and label operations

- [x] 2.1 Add eager/lazy `issues.comments.update` with nonblank ID, text-only content, required positive non-boolean keyword-only revision, a canonical vector that supplies `expected_revision=3` via kwargs, exact argv, typed response, and operation-level `0.5.0` compatibility
- [x] 2.2 Preserve stale-revision conflict, unchanged attachments, mention retriggering, and one-call no-read/merge/retry behavior through unit, component, and transport cases
- [x] 2.3 Extend Label output and `labels.create/list/update` for reviewed resource type, description, default/filter mapping, and `Unset` versus explicit-clear semantics
- [x] 2.4 Add label enum/open-response policy and frozen exact-argv/decoder cases for issue/skill, omitted/set/clear, malformed values, and pre-transport failures

## 3. Skill labels and skill-list projection

- [x] 3.1 Add `skills.labels.list/add/remove` resource methods with nonblank IDs, exact argv, skill-only resolver fence, typed Label results, and reviewed remove-refresh fallback
- [x] 3.2 Add one public `Skill.labels: LazyCollection[Label]`, preload it from list-only empty/populated payloads without extra transport, enforce strict nested field validation, and leave it unloaded when unchanged skill-detail payloads omit labels
- [x] 3.3 Back unloaded/invalidated skill-label collections only with `skills.labels.list`; add eager/lazy bound mutations, success/fallback cache invalidation, one-load cache reuse, and unbound pre-transport failures
- [x] 3.4 Extend shared operation, relation, decoder, command, and component case tables for all skill-label success/failure paths without duplicate tests

## 4. Task, agent, and runtime adaptations

- [x] 4.1 Extend task-run and agent-task wires/models for presence-correct issue title/description, current status/assignee, known/empty/value deltas, `runtime_access_denied`, and future failure strings
- [x] 4.2 Add table-driven task fixtures for absent delta, known empty delta, changed fields, malformed nested values, open failure reasons, and both affected response entrypoints
- [x] 4.3 Implement shared OMP effective-model validation for agent create/update across model omitted/set/clear, thinking omitted/set, runtime swaps, exact argv, and pre-transport no-partial-mutation behavior
- [x] 4.4 Preserve runtime-delete empty success and structured optional 409 guidance for online/offline/profile blockers while retaining legacy/plain conflicts and prohibiting cascade or retry
- [x] 4.5 Extend centralized error, resource, component, and contract tables for structured/missing/malformed/plain runtime guidance and OMP positive/negative combinations

## 5. Generation, inventories, documentation, and packaging

- [x] 5.1 Render the committed runtime only from the approved contract and prove a second ignored render has identical relative paths and bytes
- [x] 5.2 Reconcile generated/manual bindings, public signatures/exports, all 163 response dispositions, canonical/variant/legacy operation cases, source links, compatibility constants, and relation inventory by exact equality without allowlists
- [x] 5.3 Update API, compatibility, migration, maintainer, release, README, examples, and changelog for direct `0.4.44 -> 0.5.0`, new surface, presence/error semantics, checksum roles, non-SDK changes, and atomic rollback
- [x] 5.4 Update packaging/release assertions for maximum tested `0.5.0` and exclusive `0.5.1`, then prove Git tracks no `.devlocal`, archives, binaries, downloads, collector evidence, audits, or transient renders

## 6. Acceptance gates and delivery proof

- [x] 6.1 Run strict OpenSpec validation, pinned-source contract validate, two-render byte equality, contract check, and exact source-link audit
- [x] 6.2 Run focused comment, label, skill, relation, task, agent, runtime, compatibility, and transport suites, then Ruff format/check and mypy for source, tests, scripts, and tools
- [x] 6.3 Run full non-live pytest with coverage, prove offline collection excludes every live node, and pass build plus package validation
- [x] 6.4 Run authorized prepared-target `0.5.0` live-negative coverage when configured and report unavailable authorization separately without weakening offline acceptance
- [x] 6.5 Audit the final diff and clean tree for exact target/bounds, no unapproved API, no retry/cascade, no transient artifacts, and atomic contract/generated/public/docs agreement; record every command exit code and exact delivery SHA
