## 1. Provenance and approved contract foundation

- [x] 1.1 Refresh `origin/main`, record the exact implementation base, reproduce ignored `0.4.43`/`0.4.44` evidence, and independently verify tag commits, release IDs, official archive manifests/digests, executable SHA-256 values, and version JSON
- [x] 1.2 Reconcile both 189-node public command trees with zero topology/argument/flag deltas and one delete transport adaptation, then reconcile all 163 unique response work items to 30 changed and 133 unchanged rows with exact old/target source URLs
- [x] 1.3 Human-review and atomically update `contracts/sdk-contract.json` for target `0.4.44`, interval `[0.4.42,0.4.45)`, comment-delete `0.4.44` availability, tombstone presence, lifecycle projection, Triage parent presence, retained operations, and non-SDK changes
- [x] 1.4 Pass strict pinned-source contract validation and tracked-evidence audit before rendering or changing public behavior

## 2. Comment tombstones and safe deletion

- [x] 2.1 Add `Comment.deleted_at: datetime | None` through the existing immutable entity and `_CommentWire`, mapping only omission to `None` and rejecting explicit null, malformed timestamps, and wrong types
- [x] 2.2 Preserve the comment-delete signature/argv while enforcing the approved `0.4.44` operation availability, centralized pre-support plain-text 404 failure, and zero destructive fallback behavior
- [x] 2.3 Extend focused frozen decoder, resource, command, component, and relation fixtures for live omission, empty live content, tombstones, retained replies, all add/reply/list paths, malformed values, exact delete argv, target success, and old-server failure

## 3. Issue lifecycle and Triage semantics

- [x] 3.1 Extend focused issue fixtures for all custom unstarted/started/done/closed projections, every built-in status key, partial-row omission, `status_name`, open status strings, and malformed category/name failures without adding a public lifecycle enum
- [x] 3.2 Pin unbound and bound issue update mappings for omitted/same/null/foreign parent values, standard `issue_in_triage` errors, ordinary issue set/clear controls, and complete exact argv
- [x] 3.3 Add combined-field Triage cases that refetch authoritative state and prove title, description, priority, assignee, project, and parent receive no partial write

## 4. Generation, inventories, documentation, and packaging

- [x] 4.1 Render the committed runtime only from the approved contract and prove a second ignored render has identical relative paths and bytes
- [x] 4.2 Reconcile generated/manual bindings, public signatures/exports, all 163 response dispositions, canonical/variant/legacy case tables, source links, compatibility constants, and relation inventory by exact equality without allowlists
- [x] 4.3 Update API, compatibility, migration, maintainer, release, README, example, and changelog material for direct `0.4.43 -> 0.4.44`, strict tombstones, safe-delete availability, lifecycle/Triage semantics, checksum roles, non-SDK changes, and atomic rollback
- [x] 4.4 Update packaging/release assertions for maximum tested `0.4.44` and exclusive `0.4.45`, then confirm Git tracks no `.devlocal`, archives, binaries, downloads, collector evidence, audits, or transient renders

## 5. Acceptance gates and delivery proof

- [x] 5.1 Run strict OpenSpec validation, pinned-source contract validate, two-render byte equality, contract check, and exact source-link audit
- [x] 5.2 Run focused comment, delete, lifecycle, Triage, compatibility, relation, and transport suites, then Ruff format/check and mypy for source, tests, scripts, and tools
- [x] 5.3 Run full non-live pytest with coverage, confirm offline collection excludes every live node, and pass build plus package validation
- [x] 5.4 Run authorized prepared-target `0.4.44` live-negative coverage when configured and report missing authorization separately without weakening offline acceptance
- [x] 5.5 Audit the final diff and clean tree for exact target/bounds, no unapproved API or fallback, no transient artifacts, and atomic contract/generated/public/docs agreement; record every command exit code and exact delivery SHA
