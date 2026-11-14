## 1. Approved Upstream Contract Foundation

- [ ] 1.1 Update `contracts/sdk-contract.json` from exact Multica `0.7.1` commit `aec9b0b1699939a6d993da9ca2ebd2c62900a8e0` to stable `0.9.0` release `444052572` at commit `8cd8a2db978d532d8627c78cd29f05deab6c6f17`, including verified archive/executable identities and reviewed compatibility interval.
- [ ] 1.2 Encode exactly 236 target command nodes with 28 additions, one removal, 18 changed nodes, every source-only name, one reviewed disposition per node, and complete positional/flag/default/alias/deprecation/constraint/presence/destination/source/test metadata for every retained or adapted mapping.
- [ ] 1.3 Encode 196 unique baseline response-entrypoint verdicts (88 changed, 108 unchanged), their model/error/fixture/doc actions and pinned sources, and make validation reject missing, duplicate, unresolved, or pending rows.
- [ ] 1.4 Extend existing contract schema/check/render/source-link tooling only as required by the reviewed `0.9.0` facts, render `src/multica_py/_generated/approved_sdk.py`, and prove repeated rendering is byte-stable with evidence and transient output outside Git.
- [ ] 1.5 Exclusively update the shared `tests/cases/operations.py` canonical operation table and central decoder-vector metadata for every changed domain so approved operations have one canonical case, changed mappings have positive and negative vectors, and no downstream work package rewrites these shared tables.

## 2. Issue, Project, Task, Attachment, and Comment Models

- [ ] 2.1 Add typed issue requester and issue-list creator identity decoding with present, older-server omitted, allowed-null, malformed, and private-project redaction/omission fixtures.
- [ ] 2.2 Add project visibility and creator identity decoding with open-value compatibility and proven private-project 404/omission behavior; keep project create/update visibility inputs outside this change and test that the public signatures do not expand.
- [ ] 2.3 Add task credit and redaction projections across issue-run and agent-task paths, preserving open future values and rejecting malformed wire types.
- [ ] 2.4 Add attachment dimension and comment-resolution projections using the existing models/resources, including omitted/null/malformed compatibility and exact response-envelope coverage.
- [ ] 2.5 Extend issue/project/task decoder, relation, and fake-CLI component cases outside `tests/cases/operations.py` for presence, validation timing, standard errors, and eager/preview equivalence without creating a parallel operation table.
- [ ] 2.6 Extend attachment/comment decoder, resource, transport, and fake-CLI cases outside `tests/cases/operations.py`, including the existing `tests/unit/resources/test_attachments.py` and `test_issue_comments.py`, for response presence, literal input, standard errors, and eager/preview equivalence.

## 3. Rerun Migration and Relationship Safety

- [ ] 3.1 Remove the obsolete `issue rerun <issue-id>` approved mapping and public operation, then add explicit typed eager and preview operations for `issue rerun-task <run-id>` with reviewed resume and fresh inputs and result decoding.
- [ ] 3.2 Add positive resume/fresh, invalid identifier, conflicting/unsupported input, malformed response, and nonzero command-error cases; prove no compatibility alias reinterprets an issue identifier as a run identifier.
- [ ] 3.3 Update issue create/update relationship prevalidation so required-together, exactly-one, conflicts, identifiers, properties, parent/project/assignee, and attachment inputs fail before transport or mutation.
- [ ] 3.4 Preserve literal inline/file attachment binding and failure cleanup in the existing `IssueResource.create/update` methods and issue-mutation tests, with table-driven special-character, option-like, upload failure, mutation failure, and atomic-success cases owned with task 3.3.
- [ ] 3.5 Update public exports, API examples, migration documentation, type-check fixtures, and compatibility notes with a compiling old-to-new rerun path based on an actual run identifier.

## 4. Runtime, User, Workspace, and Subscriber Adaptations

- [ ] 4.1 Add runtime capacity and exact usage-window projections and tests, including open provider/model values, boundary days, omitted/null/malformed fields, and source-pinned date/window assertions.
- [ ] 4.2 Make runtime update nonzero exit fail through the shared command-error path even when progress text exists, while preserving typed zero-exit result and passive command preview.
- [ ] 4.3 Add user-profile `whats_new_seen_version` and workspace-list `pinned_at` decoding with present/null/omitted/malformed fixtures and list-order assertions.
- [ ] 4.4 Add project-inherited issue subscriber reason `project` through the existing typed subscriber relation, preserving older direct rows, open reason values, page order, and bounded cursor behavior.
- [ ] 4.5 Add authorization-safe relation cases proving omitted/redacted private identifiers create no loader or permalink while present identifiers use only governed typed resource services.

## 5. Transport and Error Boundaries

- [ ] 5.1 Extend the shared transport/error decoder for reviewed status `499` with no body, preserving command context and avoiding false JSON output-shape errors.
- [ ] 5.2 Add cancellation cases for empty body, sanitized stderr, neighboring nonzero statuses, and eager/preview behavior without weakening existing command-error classification.
- [ ] 5.3 Extend retained comment/attachment/file/stdin command cases for literal argv and payload transport, local prevalidation, caller-file preservation, and failure-safe cleanup.
- [ ] 5.4 Add private-project 404, list omission, redaction, and relationship fail-closed component fixtures using existing standard error and fake-CLI infrastructure.

## 6. Documentation, CI, and Repository Verification

- [ ] 6.1 Update compatibility, API, service-usage, migration, CLI-coverage, changelog, contributing, packaging, and release documentation for the direct `0.7.1` to `0.9.0` upgrade, retained/deferred dispositions, typed additions, private behavior, cancellation, and rerun migration.
- [ ] 6.2 Update the existing CI/live-smoke configuration, `tests/live/conftest.py`, `tests/live/test_smoke.py`, and `scripts/e2e/verify_multica_test.py` to pin exact `0.9.0`, require the protected administrator/primary/denied profiles, rerun agent, runtime, project-subscription fixture, and cleanup registry defined in `delivery-plan.md`, provide the exact administrator fixture helper plus `if: always()` cleanup, fail readiness before dispatch when any input or setup/cleanup probe is absent, and add no new framework.
- [ ] 6.3 Run focused table-driven unit, contract, component, transport, relation, documentation, and packaging checks for every changed scenario and record exact commands and exit codes.
- [ ] 6.4 Run strict OpenSpec validation, contract validate/render/check, repeated-render comparison, source-link audit, operation completeness, non-live collection isolation, mypy for source/tests/scripts, Ruff check/format, documentation, packaging, and release gates.
- [ ] 6.5 Run the full non-live automated suite locally only if it is expected to complete within ten minutes; otherwise, or if it reaches ten minutes, stop only that run-owned process and run the unsplit suite in GitHub Actions on the published exact revision.

## 7. Independent Exact-Revision Verification and Delivery

- [ ] 7.1 Map every affected OpenSpec scenario to a sufficient lower-level assertion or one focused live case, and have an independent Tester inspect that mapping from a fresh exact-revision checkout without editing implementation tests or fixtures.
- [ ] 7.2 Have the `multica-live` environment administrator provision and attest the protected rerun-agent/runtime fixture, pre-subscribed project/issue fixture, distinct denied human profile, administrator profile, and external cleanup registry exactly as specified in `delivery-plan.md`; gate dispatch on exact revisions, CLI `0.9.0`, isolated bindings, differing identities, focused lower-level results, a destructive setup/cleanup probe, registered cleanup callbacks, and renderer availability.
- [ ] 7.3 Execute the exact live setup/action/assertion/cleanup sequences in `delivery-plan.md` for rerun-task resume/fresh, administrator-created private-project 404/list omission, project-inherited subscriber provenance, safe nonexistent-runtime update failure, and exact runtime-usage window; delete every run-created issue before its project, verify issue/runs/project absence through the pinned administrator CLI, prove the registry empty, and prove 499/no-body separately with the deterministic fake-CLI/process fixture.
- [ ] 7.4 For any changed visible terminal output, capture equivalent baseline and candidate text plus genuine macOS PNGs at identical locale/width/output mode; otherwise publish a case-specific no-image rationale and do not create decorative images.
- [ ] 7.5 Publish normal development and applicable test/result commits, push normally, prove remote branch SHA equals the verified local SHA, and preserve branch/PR/commits without force, merge, close, or deletion.
- [ ] 7.6 Publish sanitized commands, exit codes, assertions, CI/PR/commit/file links, exact SHAs, provenance, and required images as Multica evidence attachments; read back the final comment and attachments, then remove only run-owned stand data and local diagnostic output.
