## 1. Freeze the approved Multica 0.5.1 contract

- [x] 1.1 Record the implementation base and independently reverify `v0.5.1`, peeled commit `f41fae6b08fb734afcbd13205c0b3203dd0bc9c6`, release `392880229`, Darwin ARM64 archive SHA-256 `85c5e6d8f9af4c3cfef9a6632a94b682ca09afb1e62900a8565eab5bb26a12ec`, extracted executable SHA-256 `a7223c87c3da4b77afa8b0941504678c30a2770dd1d03df5f2325301360ed588`, official checksum-manifest SHA-256 `cf71aab5b40ed16e89c5f826109deace7b4b92198ef1147dd1608e4aea396800`, and version JSON in ignored storage.
- [x] 1.2 Reproduce the 194-to-201 command audit with seven additions, zero removals/renames/moves, exact changed existing nodes, and reviewed positional, flag, default, alias, constraint, presence, destination, compatibility, and source data for every retained or changed node.
- [x] 1.3 Encode explicit `defer` dispositions for the `issue wakeup` parent and all six leaves, including reviewed candidate mappings and constraints but no public operation/model/enum/retry promise; encode runtime-profile `--runtime-type` as `not_sdk_surface` and updater/workdir deltas as `retain`.
- [x] 1.4 Reproduce the 167-entrypoint response audit with `response_review_complete=true`, exactly three changed entrypoints for `wakeup_id`/`call_id`, and exact-equality evidence for the 164 unchanged entrypoints.
- [x] 1.5 Update `contracts/sdk-contract.json` and only strictly required schema/validator fixtures for target `0.5.1`, interval `[0.4.42,0.5.2)`, optional-field provenance, source references, dispositions, and negative public-inventory rules; run strict pinned-source validation before public edits.

## 2. Render and implement optional correlation fields

- [x] 2.1 Render the approved contract twice to isolated destinations, require byte-identical results, commit only the deterministic generated runtime projection, and verify target/max-tested/exclusive-ceiling metadata.
- [x] 2.2 Add optional open-string `wakeup_id` to `_TaskRunWire`, `_task_run_from_wire`, and `TaskRun` so present values round-trip, omitted ordinary/legacy values remain `None`, and malformed non-string values fail through the existing protocol boundary.
- [x] 2.3 Add optional open-string `call_id` to the run-message wire/adapter and `RunMessage` so present values round-trip, omitted legacy values remain `None`, and ordering plus tri-state truncation semantics are unchanged.
- [x] 2.4 Confirm public resources, eager/command signatures, operation IDs, relations, enums, dependencies, and transport behavior are unchanged and that no `issue wakeup` or runtime-profile API is introduced.

## 3. Extend table-driven verification

- [x] 3.1 Extend existing frozen task-run decode/serialization cases for present, omitted/legacy, and malformed `wakeup_id` payloads through both `agents.tasks` and `issues.runs` without new duplicate helpers.
- [x] 3.2 Extend existing frozen run-message cases for present, omitted/legacy, and malformed `call_id` payloads while asserting sequence ordering, timestamps, input/output/content, and `output_truncated` behavior.
- [x] 3.3 Extend contract and component cases to prove exact argv/transport counts, unchanged legacy envelopes and errors, absence of wakeup public methods/generated symbols, and stable operation/resource inventories.
- [x] 3.4 Update provenance, command, response, compatibility, source-link, generated-runtime, and package fixtures so their exact totals and target identities match the approved `0.5.1` contract.

## 4. Publish direct migration and package documentation

- [x] 4.1 Update README, API reference, migration guide, changelog, examples, and typed documentation fixtures for the direct `0.5.0` to `0.5.1` migration, optional correlation fields, `[0.4.42,0.5.2)` interval, and maximum-tested `0.5.1`.
- [x] 4.2 Document `issue wakeup` as deferred correlation context rather than supported CRUD, keep runtime profiles outside the SDK, and preserve existing updater/file-channel public contracts.
- [x] 4.3 Update prepared-live guidance and packaging assertions for CLI `0.5.1` without adding backend provisioning, network requirements to offline tests, or an intermediate SDK release.

## 5. Verify and deliver atomically

- [x] 5.1 Run strict OpenSpec validation; approved-contract validate/render/check against pinned target source; deterministic-render comparison; source-link audit; focused unit, contract, and component suites; and `git diff --check`.
- [x] 5.2 Run Ruff check/format check, `mypy src`, `mypy tests`, complete `pytest -m "not live"`, and collect-only verification proving no `tests/live/*` node is selected.
- [x] 5.3 Build wheel and source distribution, run package validation in isolation, and prove generated compatibility, exports, docs, and included files match the approved contract.
- [x] 5.4 Report prepared live-smoke status separately, audit tracked/package contents for archives, binaries, `.devlocal`, collector/audit evidence, and transient renders, and deliver one clean exact commit with rollback to the prior atomic contract/model/docs state.
