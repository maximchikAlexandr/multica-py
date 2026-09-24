## 1. Freeze the approved Multica 0.5.2 contract

- [ ] 1.1 Record the implementation base and independently reverify `v0.5.2`, release `394535503`, peeled commit `d45aba1cd7582bef9210b921bbb7dc198b48e1ee`, comparison from `f41fae6b08fb734afcbd13205c0b3203dd0bc9c6`, both official Darwin ARM64 archive/executable/version JSON identities, checksum material, and unsigned-tag agreement in ignored storage.
- [ ] 1.2 Reproduce the `201→201` command audit with zero additions/removals/renames/moves, exactly three changed help nodes, all five source-only names classified, and reviewed arity, flags, aliases, defaults, values, presence, conflicts, destinations, compatibility, and source data for every node.
- [ ] 1.3 Reproduce the 167-entrypoint response audit with `response_review_complete=true`, unique work-item coverage, exact old/target source URLs, approved duplicate and supplement adaptations, and exact-equality evidence for unchanged responses.
- [ ] 1.4 Encode atomic ordered `issues.create` property mapping and explicit retain/defer/not-SDK dispositions for duplicate timeline/mutations, task-supplement handlers and receipts, attachment paths, and unrelated target fixes.
- [ ] 1.5 Update `contracts/sdk-contract.json` and only strictly required schema/validator fixtures for target `0.5.2`, interval `[0.4.42,0.5.3)`, field/operation provenance, mappings, dispositions, and negative inventories; run strict pinned-source validation before public edits.

## 2. Render and implement approved response projections

- [ ] 2.1 Render the approved contract twice to isolated destinations, require identical relative paths and bytes, commit only the deterministic generated runtime projection, and verify target/max-tested/exclusive-ceiling metadata.
- [ ] 2.2 Add absence-aware `duplicate_of` wire decoding and immutable `DuplicateIssueReference` projection to canonical `Issue`, preserve omission/null/object/malformed semantics, and thread the snapshot through list/get/create/update/children/search and bound-operation adapters without hydration.
- [ ] 2.3 Add optional open `supplement_capability`, ordered `supplement_comment_ids`, and optional `can_supplement` to `_AgentTaskWire`/`AgentTask` and `_TaskRunWire`/`TaskRun`, preserving omission, empty, false, malformed, serialization, and all existing task fields.
- [ ] 2.4 Add `duplicate_of` to the validated issue-list field allow-list and confirm direct/filter forms emit the same governed comma-separated projection without changing pagination or other list mappings.
- [ ] 2.5 Confirm public operations, resource inventories, relations, retries, enums, dependencies, and transport behavior remain unchanged except for the explicitly approved response and create mappings, with no supplement, duplicate mutation, timeline, receipt, or attachment API.

## 3. Implement atomic typed create properties

- [ ] 3.1 Add immutable public `IssuePropertyAssignment(reference, value)` with stable local validation for tuple/item/reference/value/reserved/comparison shapes and export it through the repository's established issue-model surface.
- [ ] 3.2 Add matching `properties` parameters to issue resource eager/command methods and project-bound delegates; emit repeatable `--property <reference>=<value>` pairs in caller order on the single create step with no catalog lookup or post-create property fallback.
- [ ] 3.3 Preserve existing description, project, parent, assignee, priority, label plan, options, decoding, and client binding behavior; document that create properties are atomic while legacy label attachment remains composite.
- [ ] 3.4 Surface pinned CLI capability, catalog, canonicalization, duplicate, archived, type, atomicity, and post-create mismatch failures through existing command error handling without reimplementing server-owned property rules.

## 4. Extend table-driven verification and documentation

- [ ] 4.1 Extend existing frozen issue response cases for omitted/null/valid/malformed duplicate snapshots, missing-original and status-snapshot semantics, every supported issue response path, and unchanged pagination/labels/metadata/properties/binding behavior.
- [ ] 4.2 Extend existing task cases for omitted/open capability, omitted/empty/ordered comment IDs, omitted/true/false permission, malformed values, both operations, presence evidence, and unchanged usage/result/error/failure/cancellation/delta fields.
- [ ] 4.3 Extend existing operation/component cases for property names and UUIDs, all property types, repeat order, eager/command/project-bound parity, local invalid shapes, CLI-owned duplicate/malformed/empty/archived/`__none__`/comparison/capability/canonicalization/atomicity/mismatch failures, exact argv, and zero fallback calls.
- [ ] 4.4 Update provenance, command, response, compatibility, source-link, generated-runtime, negative inventory, and package fixtures for exact `0.5.2` identities, 201 nodes, 167 response work items, and excluded REST/local-file surfaces.
- [ ] 4.5 Update README, API, compatibility, migration, changelog, prepared-live, and release guidance for direct `0.5.1→0.5.2`, new read fields, atomic properties, omission behavior, version gates, deferred surfaces, and rollback without an intermediate SDK delivery.

## 5. Verify and deliver atomically

- [ ] 5.1 Run strict OpenSpec validation; approved-contract validate/render/check against pinned target source; deterministic-render comparison; source-link audit; focused unit, contract, and component suites; and `git diff --check`.
- [ ] 5.2 Run Ruff check/format check, `mypy src`, `mypy tests`, complete `pytest -m "not live"`, and collect-only verification proving no `tests/live/*` node is selected.
- [ ] 5.3 Build wheel and source distribution, run isolated package validation, and prove generated compatibility, public exports, documentation, and included files match the approved contract.
- [ ] 5.4 Report prepared live-smoke status separately, audit tracked/package contents for archives, binaries, `.devlocal`, collector/audit evidence, and transient renders, and deliver one clean exact implementation commit with atomic rollback to the prior `0.5.1` state on gate failure.
